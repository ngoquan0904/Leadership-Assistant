import logging
from agent import BaseAgent
from pydantic import BaseModel, Field
from langchain_mcp_adapters.client import MultiServerMCPClient
from datetime import datetime
from typing import Literal
import sys
import os
import traceback
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from utils.prompts import PROJECT_MANAGER_AGENT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)
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

class ProjectManagerAgent(BaseAgent):
    def __init__(self, tools=None):
        self.SYSTEM_PROMPT = PROJECT_MANAGER_AGENT_SYSTEM_PROMPT
        super().__init__(tools)

    @classmethod
    async def create(cls):
        try:
            notion_tools = await get_notion_tools()
        except Exception:
            logger.error("Failed to get notion tools during agent creation")
            raise
        tools = notion_tools
        agent = cls(tools=tools)
        return agent
