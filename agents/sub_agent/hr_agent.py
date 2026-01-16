import logging
import os
import sys
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv

# Add parent directories to sys.path for internal imports
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from agent import BaseAgent
from utils.prompts import HR_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)
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

async def get_neo4j_tools():
    config = get_mcp_server_config(port=5001, transport='sse', host_env="NEO4J_MCP_HOST")
    logger.info(f"Connecting to Neo4j MCP Server at {config.url}")
    
    client = MultiServerMCPClient(
        {
            "neo4j": {
                "url": config.url,
                "transport": config.transport,
            },
        }
    )
    
    try:
        tools = await client.get_tools()
        selected_tools = []
        for tool in tools:
            if tool.name in ['get_neo4j_schema', 'read_neo4j_cypher']:
                selected_tools.append(tool)
        logger.info(f"Successfully retrieved {len(selected_tools)} Neo4j tools")
        return selected_tools
    except Exception as e:
        logger.error(f"Error fetching Neo4j MCP tools from {config.url}: {e}")
        return []

class HRAgent(BaseAgent):
    def __init__(self, tools=None):
        self.SYSTEM_PROMPT = HR_AGENT_SYSTEM_PROMPT
        super().__init__(tools)

    @classmethod
    async def create(cls):
        try:
            neo4j_tools = await get_neo4j_tools()
        except Exception:
            logger.error("Failed to get neo4j tools during agent creation")
            raise
        tools = neo4j_tools
        agent = cls(tools=tools)
        print(tools)
        return agent
