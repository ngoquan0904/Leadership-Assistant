import logging
from agent import BaseAgent
from pydantic import BaseModel, Field
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Literal
import sys
import os
import traceback
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from utils.person import *
from utils.prompts import EK_AGENT_SYSTEM_PROMPT
logger = logging.getLogger(__name__)
import requests
from dotenv import load_dotenv
load_dotenv()
class ServerConfig(BaseModel):
    host: str
    port: int
    transport: str
    url: str     

def get_mcp_server_config(port, transport, host_env="SERVER_URL", path="/mcp/") -> ServerConfig:
    host = os.getenv(host_env, os.getenv("SERVER_URL", "127.0.0.1"))
    return ServerConfig(
        host=host,
        port=port,
        transport=transport,
        url=f'http://{host}:{port}{path}'
    )
async def get_notion_tools():
    config = get_mcp_server_config(port=3000, transport='streamable_http', host_env="NOTION_MCP_HOST")
    logger.info(f"MCP Server url={config.url}")
    client = MultiServerMCPClient(
            {
                "all_tools": {
                    "url": config.url,
                    "transport": config.transport,
                    # Use AUTH_TOKEN from environment (set in docker-compose or host env)
                    "headers": {"Authorization": f"Bearer {os.getenv('AUTH_TOKEN', 'my_auth_token')}"}
                },
            }
        )
    try:
        tools = await client.get_tools()
        return tools
    except Exception as e:
        logger.error(f"Error fetching Notion MCP tools from {config.url}: {e}")
        logger.error(traceback.format_exc())
        raise
async def get_neo4j_tools():
    # For SSE transport, the MCP endpoint path should be '/sse'
    config = get_mcp_server_config(port=8001, transport='sse', host_env="NEO4J_MCP_HOST", path='/sse')
    logger.info(f"MCP Server url={config.url}")
    client = MultiServerMCPClient(
            {
                "all_tools": {
                    "url": config.url,
                    "transport": config.transport,
                },
            }
        )
    try:
        tools = await client.get_tools()
    except Exception as e:
        logger.error(f"Error fetching Neo4j MCP tools from {config.url}: {e}")
        logger.error(traceback.format_exc())
        raise
    selected_tools = []
    for tool in tools:
        if tool.name in ['get_neo4j_schema', 'read_neo4j_cypher']:
            selected_tools.append(tool)
    logger.debug(f"Selected Neo4j tools: {[t.name for t in selected_tools]}")
    return selected_tools

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal["input_required", "completed", "error"]
    message: str


class EnterpriseKnowledgeAgent(BaseAgent):
    @staticmethod
    async def get_relevant_chunks(query) -> str:
        """
        Retrieve relevant information chunks from the software documentation repository based on the user's query.
        Uses semantic search over Vector Database Qdrant to find the most relevant context for software development business questions.
        Args:
            query (str): The user's search query.
        Returns:
            str: Relevant context or information extracted from the documentation repository.
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
    SYSTEM_PROMPT = EK_AGENT_SYSTEM_PROMPT

    @classmethod
    async def create(cls):
        try:
            neo4j_tools = await get_neo4j_tools()
        except Exception:
            logger.error("Failed to get neo4j tools during agent creation")
            raise
        try:
            notion_tools = await get_notion_tools()
        except Exception:
            logger.error("Failed to get notion tools during agent creation")
            raise
        tools = neo4j_tools + notion_tools + [cls.get_relevant_chunks]
        agent = cls(tools=tools)
        return agent