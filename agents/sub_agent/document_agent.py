import os
import requests
from langchain_core.tools import tool
from agent import BaseAgent
from utils.prompts import DOCUMENT_AGENT_SYSTEM_PROMPT

class DocumentAgent(BaseAgent):
    SYSTEM_PROMPT = DOCUMENT_AGENT_SYSTEM_PROMPT

    def get_tools(self):
        @tool
        async def get_relevant_chunks(query: str) -> str:
            """
            Retrieve relevant information chunks from the internal business and company documentation repository based on the user's query.
            Uses semantic search over Vector Database Qdrant to find the most relevant context for business and company-related questions.
            Args:
                query (str): The user's search query.
            Returns:
                str: Relevant context or information extracted from the internal documentation repository.
            """
            doc_host = os.getenv("DOCUMENT_EXTRACTION_HOST", "localhost")
            doc_port = os.getenv("DOCUMENT_EXTRACTION_PORT", "8888")
            url = f"http://{doc_host}:{doc_port}/search"
            payload = {
                "query": query,
                "image_description": ""
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            response = response.json()
            return response["text"].replace("http://minio", "http://localhost")
        
        return [get_relevant_chunks]
import os

import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from utils.prompts import CALENDAR_AGENT_SYSTEM_PROMPT
from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service,
    get_google_credentials
)
from agent import BaseAgent

class CalendarAgent(BaseAgent):
    def __init__(self, tools=None):
        self.SYSTEM_PROMPT = CALENDAR_AGENT_SYSTEM_PROMPT
        super().__init__(tools)

    def get_api_resource(self):
        credentials = get_google_credentials(
            token_file="token.json",
            scopes=["https://www.googleapis.com/auth/calendar"],
            client_secrets_file=os.getenv("client_secrets_file")
        )
        api_resource = build_resource_service(credentials=credentials)
        return api_resource
    def get_tools(self):
        return CalendarToolkit(api_resource=self.get_api_resource()).get_tools()
