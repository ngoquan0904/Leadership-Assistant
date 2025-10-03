import os
import json
import asyncio
from typing import List
from pydantic import BaseModel
from pypdf import PdfReader
from tqdm.asyncio import tqdm as tqdm_async
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from model.person import Person, get_short_id
from config import *
def read_resume_from_directory(directory=RESUME_PATH):
    resumes = []

    if not os.path.exists(directory):
        print(f"Directory '{directory}' does not exist.")
        return resumes

    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"No PDF files found from '{directory}'.")
        return resumes

    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                person_id = get_short_id(pdf_path)
                text += f"PersonID: {person_id}\n"
                for page in pdf_reader.pages:
                    text += page.extract_text()
            resumes.append(text)
            print(f"Processed: {pdf_path} ({len(text)} characters)")
        except Exception as e:
            print(f"Error with {pdf_file}: {str(e)}")
    print(f"Total resumes loaded: {len(resumes)}")
    # print(resumes[0])
    return resumes

def chunks(xs, n=10):
    n = max(1, n)
    return [xs[i:i+n] for i in range(0, len(xs), n)]

class TextExtractor:
    def __init__(self, llm_with_structured_output,
                 prompt_template):
        self.llm = llm_with_structured_output
        self.prompt_template = prompt_template
    
    async def extract(self, texts: List[str], semaphore) -> BaseModel:
        # Đảm bảo số lượng tác vụ chạy đồng thời không vượt quá giới hạn
        async with semaphore:
            prompt = self.prompt_template.invoke({'texts': '\n\n'.join(texts)})
            entity: BaseModel = await self.llm.ainvoke(prompt)
        return entity
    async def extract_all(self, texts: List[str], chunk_size=1, max_workers=5) -> List[BaseModel]:
        # Tạo semaphore để giới hạn số lượng tác vụ đồng thời
        semaphore = asyncio.Semaphore(max_workers)
        text_chunks = chunks(texts, chunk_size)
        # Tạo danh sách tasks, chưa gọi await vì chỉ tạo couroutine chưa thực thi
        tasks = [self.extract(text_chunk, semaphore) for text_chunk in text_chunks]

        entities: List[BaseModel] = []
        # tạo progress bar
        with tqdm_async(total=len(tasks), desc="extracting texts") as pbar:
            # asyncio.as_completed(tasks) mới thực thi task đồng thời
            for future in asyncio.as_completed(tasks):
                result = await future
                entities.append(result)
                pbar.update(1)
        return entities
def main():
    resumes = read_resume_from_directory()
    prompt_template = PromptTemplate.from_template("""
    You are extracting information from resumes according to the people schema. Below is the resume.
    Only include information explicitly listed in the resume. 
    For example, do not add skills if they aren't explicitly mentioned in the resume. 
    
    # Resume
    {texts}
    """)
    llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=os.getenv("GEMINI_API"))
    llm_with_structured_output = llm.with_structured_output(Person)
    text_extractor = TextExtractor(llm_with_structured_output, prompt_template)
    people = asyncio.run(text_extractor.extract_all(resumes))
    people_list = [person.model_dump() for person in people]
    with open(EXTRACTED_JSON, 'w') as f:
        json.dump(people_list, f, indent=4)
                              
if __name__ == "__main__":
    main()