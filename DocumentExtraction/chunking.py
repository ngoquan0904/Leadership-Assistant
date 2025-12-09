import os
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from tqdm import tqdm
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
load_dotenv()
import re
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)
CHUNK_PROMPT = """
Bạn là một trợ lý xử lý văn bản. Hãy chia nhỏ văn bản đầu vào thành các đoạn (chunk) theo cấu trúc sau:
- heading: là tiêu đề chính của đoạn nội dung (lấy đúng nội dung tiêu đề xuất hiện trong văn bản, không tự tạo mới)
- content: là nội dung thuộc về các tiêu đề trên, CÓ THỂ chứa URL hình ảnh  nếu có trong văn bản gốc, không được bỏ đi bất cứ image URL nào.

Yêu cầu:
- Không bỏ đi bất kỳ thông tin nào trong văn bản.
- Sinh ra 1 heading ngắn gọn làm tiêu đề cho nội dung của chunk
- Những câu mô tả, giải thích, hoặc đoạn văn bản thông thường phải để trong content.
- Mỗi chunk không được dài quá 400 tokens. Nếu nội dung vượt quá 400 tokens thì cắt thành nhiều chunk, giữ nguyên heading
- Chuẩn hóa các từ bị tách (ví dụ "ho ạ t động" thành "hoat động") và bỏ đi các ký tự không cần thiết.
- Trả về kết quả theo định dạng JSON phù hợp với schema đã cho.
"""
def split_sections(text, max_length=20000):
    # Cho phép các ký tự trắng trước số La Mã
    roman_pattern = r'(?:^|\n)[ \t]*([IVXLCDM]{1,5})[.、:：]'
    roman_matches = list(re.finditer(roman_pattern, text, flags=re.IGNORECASE))
    if len(roman_matches) > 1:
        sections = []
        # Lấy phần header trước mục I
        header = text[:roman_matches[0].start(1)].strip()
        for i in range(len(roman_matches)):
            start = roman_matches[i].start(1)
            end = roman_matches[i+1].start(1) if i+1 < len(roman_matches) else len(text)
            sections.append(text[start:end].strip())
        return header, sections
    # Nếu không có mục La Mã, chia theo dòng, không vượt quá max_length
    lines = text.splitlines(keepends=True)
    sections = []
    buffer = ""
    for line in lines:
        if len(buffer) + len(line) <= max_length:
            buffer += line
        else:
            if buffer:
                sections.append(buffer.strip())
            buffer = line
    if buffer:
        sections.append(buffer.strip())
    return "", sections

def merge_short_sections(sections, max_total_length=20000):
    merged = []
    buffer = ""
    for sec in sections:
        if len(buffer) + len(sec) <= max_total_length:
            if buffer:
                buffer += " " + sec
            else:
                buffer = sec
        else:
            if buffer:
                merged.append(buffer)
            buffer = sec
    if buffer:
        merged.append(buffer)
    return merged

class Chunk(BaseModel):
    heading: str = Field(..., description="Tiêu đề chính của đoạn chunk")
    content: str = Field(..., description="Nội dung đoạn chunk")
    
class Chunks(BaseModel):
    chunks: List[Chunk] = Field(..., description="Danh sách các chunk đã tách")

def chunk_section(model, section_content):
    structured_model = model.with_structured_output(Chunks)
    system =  CHUNK_PROMPT
    chunk_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("human", "Toàn bộ đoạn văn bản gốc: {text}")
        ]
    )
    chunk_chain = chunk_prompt | structured_model
    chunks = chunk_chain.invoke({"text": section_content})
    return chunks

class ChunkModule:
    def __init__(self, output_dir=None, storage_client=None, mode="prod", max_workers: int = 4):
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-pro", api_key=os.getenv("LLM_API"))
        self.max_workers = max_workers
        self.output_dir = output_dir
        self.mode = mode
        if self.mode == "prod":
            self.storage_client = storage_client
            self.storage_bucket = os.getenv("STORAGE_BUCKET")
            self.storage_folder = os.getenv("STORAGE_FOLDER", "").strip("/")
        
    def chunks_all_text(self, file_name):
        if self.mode == "dev":
            md_path = Path(self.output_dir) / file_name / f"{file_name}_posted.md"
            try:
                md_content = md_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.error(f"❌ Lỗi khi đọc file markdown: {e}")
                return
        elif self.mode == "prod":
            # Đọc file md từ storage về memory
            folder_name = f"{self.storage_folder}/{file_name}" if self.storage_folder else file_name
            object_name = f"{folder_name}/{file_name}_posted.md"
            try:
                response = self.storage_client.get_object(self.storage_bucket, object_name)
                md_content = response.read().decode("utf-8")
                # print(md_content)
                response.close()
                # response.release_conn()
            except Exception as e:
                logger.error(f"❌ Lỗi khi đọc file markdown từ storage: {e}")
                return
        # tách thành các section <= 50.000 ký tự
        header, sections = split_sections(md_content)
        if header and sections and len(header) + len(sections[0]) <= 20000:
            sections[0] = header + "\n" + sections[0]
            header = ""
        elif header:
            # nếu không ghép được, sections[0] là header, các phần còn lại là nội dung
            sections = [header] + sections
            header = ""

        sections = merge_short_sections(sections, max_total_length=20000)
        # chunk cho từng section song song và lưu lại, giữ đúng thứ tự
        all_chunks = []
        if sections:
            # partial để truyền model vào hàm chunk_section
            func = partial(chunk_section, self.model)
            # executor.map bảo toàn thứ tự tương ứng với input sequence
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = list(tqdm(executor.map(func, sections), total=len(sections), desc="Chunking sections"))
            for section_chunks in results:
                # mỗi section_chunks là đối tượng Chunks
                all_chunks.extend(section_chunks.chunks)

        # Chuyển sang dict trước khi tóm tắt
        all_chunks_dict = [chunk.model_dump() for chunk in all_chunks]
        if self.mode == "dev":
            try:
                save_path = md_path.with_suffix(".json")
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "chunks": all_chunks_dict
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"📄 Đã lưu nội dung trích xuất vào: {md_path}")
            except Exception as e:
                logger.error(f"❌ Lỗi khi ghi file json: {e}")

        elif self.mode == "prod":
            from io import BytesIO
            folder_name = f"{self.storage_folder}/{file_name}" if self.storage_folder else file_name
            json_bytes = BytesIO(json.dumps({
                "chunks": all_chunks_dict
            }, ensure_ascii=False, indent=2).encode("utf-8"))
            save_path = f"{folder_name}/{file_name}.json"
            try:
                self.storage_client.upload_fileobj(
                    fileobj=json_bytes,
                    bucket_type=self.storage_bucket,
                    folder_name=folder_name,
                    file_name=f"{file_name}.json",
                    content_type="application/json"
                )
                logger.info(f"📄 Đã upload file chunks JSON lên storage: {save_path}")
            except Exception as e:
                logger.error(f"❌ Lỗi khi upload file chunks JSON lên storage: {e}")
                
if __name__ == "__main__":
    # dir_path = r"D:\Dowloads\md1-3\md1-3"
    dir = os.getenv("DOCUMENT_FOLDER")
    input_dir = Path(dir) / "input"
    output_dir = Path(dir) / "output"
    output_dir.mkdir(exist_ok=True)
    chunk_module = ChunkModule(output_dir=output_dir, max_workers=6)
    # for filename in tqdm(os.listdir(dir_path)):
        # file_path = os.path.join(dir_path, filename)
    file_name = "scribe_test"
    chunk_module.chunks_all_text(file_name)
    # add_prev_next_sentences(r'D:\Document\Viettel\Agent for SE\chunking\data\PL02_Huong dan LTAT Android_iOS.json')