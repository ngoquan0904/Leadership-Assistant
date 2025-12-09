import os
import shutil
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from pypdf import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

from utils.minio import MinioClientWrapper
from graphdb.extract_resume import TextExtractor
from graphdb.graph import KnowledgeGraph
from graphdb.person import Person, get_short_id

load_dotenv()

app = FastAPI()

# Initialize MinIO
minio_client = MinioClientWrapper(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    secure=os.getenv("MINIO_SECURE", "False").lower() == "true"
)

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
        minio_path = minio_client.upload_file_private(
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
            "minio_path": minio_path
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
