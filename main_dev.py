import os
import re
import shutil
import logging
import tempfile
from pydantic import BaseModel
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
if not logger.hasHandlers():
    logger.addHandler(handler)
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pypdf import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from DocumentExtraction.extract_document import DocumentExtraction
from DocumentExtraction.chunking import ChunkModule
from DocumentExtraction.minio_client import MinioClientWrapper
from DocumentExtraction.s3 import S3ClientWrapper
from DocumentExtraction.db import QdrantVectorstore
from DocumentExtraction.utils import _folder_name_from_filename, parse_image_path
from utils.minio import MinioClientWrapper
from graphdb.extract_resume import TextExtractor
from graphdb.graph import KnowledgeGraph
from graphdb.person import Person, get_short_id

mode = os.getenv("MODE")
app = FastAPI()
storage_client = MinioClientWrapper(
    endpoint=f"{os.getenv('MINIO_HOST', '127.0.0.1')}:{os.getenv('MINIO_PORT', '9000')}",
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=False,
)
stopwords_path = os.getenv("STOPWORD_PATH")

# storage_client = S3ClientWrapper(
#     endpoint="s3.amazonaws.com",
#     access_key=os.getenv("S3_ACESS_KEY"),
#     secret_key=os.getenv("S3_SECRET_KEY"),
#     secure=True,
#     region_name=os.getenv("S3_REGION_NAME")
# )

extractor = DocumentExtraction(storage_client=storage_client)
chunk_module = ChunkModule(storage_client=storage_client)
vectorstore = QdrantVectorstore(host=os.getenv("QDRANT_HOST", "127.0.0.1"), port=os.getenv("QDRANT_PORT", "6333"), storage_client=storage_client)

def process_document(file_path):
    file_name = extractor.extract_all_infor(file_path)
    chunk_module.chunks_all_text(file_name)
    vectorstore.ingest_to_qdrant(collection_name=os.getenv("COLLECTION_NAME"), file_name=file_name)

def process_bytes_upload_and_process(file_bytes: bytes, filename: str):
    """
    Write uploaded bytes to a temp file (using the original filename inside a temp dir),
    upload to MinIO, run processing, then remove temp file and temp dir.
    This keeps the temp file named as the original file.
    """
    tmp_dir = None
    tmp_path = None
    try:
        # ensure we only use the base filename (no path components)
        base_name = os.path.basename(filename)
        # create a temporary directory and write the file with the original filename inside it
        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, base_name)
        with open(tmp_path, "wb") as f:
            f.write(file_bytes)

        # determine bucket and folder
        bucket = os.getenv("STORAGE_BUCKET")
        folder = f"{os.getenv('STORAGE_FOLDER')}/{_folder_name_from_filename(filename)}"

        # use _folder_name_from_filename as base and append original extension
        ext = Path(filename).suffix or ""
        safe_name = f"{_folder_name_from_filename(filename)}{ext}"

        # upload (public upload used here to match existing helper; change to upload_file if you prefer private)
        storage_client.upload_file(
            file_path=tmp_path,
            bucket_type=bucket,
            folder_name=folder,
            file_name=safe_name
        )

        # process the local temp file
        process_document(tmp_path)

    except Exception as e:
        logger.error("Failed upload/process for %s: %s", filename, e)
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir)
        except Exception:
            pass

@app.post("/upload-file")
async def create_upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Receive uploaded file, upload it to MinIO immediately (no persistent save to D:),
    and trigger processing (background if available). Returns file name and processing status.
    """
    # read bytes into memory right away so BackgroundTasks can use them after request ends
    content = await file.read()
    if background_tasks is not None:
        background_tasks.add_task(process_bytes_upload_and_process, content, file.filename)
        return {"filename": file.filename, "status": "processing"}
    else:
        process_bytes_upload_and_process(content, file.filename)
        return {"filename": file.filename, "status": "done"}
    
def get_presigned_url(text):
    image_urls = re.findall(r'http[s]?://\S+\.(?:png|jpg|jpeg|gif|pdf|docx)', text)
    for path in set(image_urls):
        parts = parse_image_path(path)
        bucket = parts[0]
        object_name = parts[1]
        presigned = storage_client.get_presigned_url(
            bucket, object_name
        )
        text = text.replace(path, presigned)
    return text

class Request(BaseModel):
    query: str
    image_description: str

@app.post("/search")
def search(request: Request):
    query = request.query
    image_description = request.image_description
    result = vectorstore.search(collection_name=os.getenv("COLLECTION_NAME"), query=query, image_description=image_description)
    text = result["text"]
    if not isinstance(storage_client, S3ClientWrapper):
        return {
            "text": text
        }
    return {
        "text": get_presigned_url(text)
    }

@app.post("/delete-file-object")
def delete_file(file_name: str):
    vectorstore.delete_points_by_filename(collection_name=os.getenv("COLLECTION_NAME"), filename=file_name)
    storage_client.delete_folder(bucket_type=os.getenv("STORAGE_BUCKET"), folder=f"{os.getenv('STORAGE_FOLDER')}/{file_name}")

#============== GraphDB ======
# Initialize Neo4j
knowledge_graph = KnowledgeGraph()

# Initialize Gemini
llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', api_key=os.getenv("GOOGLE_API_KEY"))
llm_with_structured_output = llm.with_structured_output(Person)

prompt_template = PromptTemplate.from_template("""
You are extracting information from resumes according to the people schema. Below is the resume.
Only include information explicitly listed in the resume. 
For example, do not add skills if they aren't explicitly mentioned in the resume. 

# Resume
{texts}
""")

text_extractor = TextExtractor(llm_with_structured_output, prompt_template)

@app.post("/upload_cv")
async def upload_cv(file: UploadFile = File(...)):
    temp_file_path = f"temp_{file.filename}"
    try:
        # 1. Save file temporarily
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Upload to MinIO
        bucket_name = os.getenv("STORAGE_BUCKET", "leadership-assistant")
        
        # Upload to STORAGE_BUCKET/human_resource
        storage_path = storage_client.upload_file_private(
            file_path=temp_file_path,
            bucket_type=bucket_name,
            folder_name="human_resource",
            file_name=file.filename
        )
        
        # 3. Extract text from PDF
        text = ""
        with open(temp_file_path, 'rb') as f:
            pdf_reader = PdfReader(f)
            person_id = get_short_id(file.filename) 
            text += f"PersonID: {person_id}\n"
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        # 4. Extract structured data
        people = await text_extractor.extract_all([text])
        if not people:
            raise HTTPException(status_code=500, detail="Failed to extract information from CV")
        
        person = people[0]
        
        # 5. Push to Neo4j
        knowledge_graph.initialize_graph([person.model_dump()])
        
        return {
            "message": "CV uploaded and processed successfully", 
            "person_id": person.id, 
            "storage_path": storage_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    file_path = r"D:\Document\Code\Projects\Tool-use_Agent\DocumentExtraction\input\scribe_test.pdf"
    process_document(file_path)
    # remove_object(r"D:\Document\Code\Projects\Tool-use_Agent\DocumentExtraction\input\scribe_test.pdf")

