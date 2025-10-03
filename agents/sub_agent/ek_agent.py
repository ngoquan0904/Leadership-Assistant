import logging
from agent import BaseAgent
from pydantic import BaseModel, Field
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Literal
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from utils.person import *
logger = logging.getLogger(__name__)

class ServerConfig(BaseModel):
    host: str
    port: int
    transport: str
    url: str     

def get_mcp_server_config(port, transport) -> ServerConfig:
    return ServerConfig(
        host='127.0.0.1',
        port=port,
        transport=transport,
        url=f'http://127.0.0.1:{port}/mcp/'
    )

async def get_neo4j_tools():
    config = get_mcp_server_config(port=8001, transport='sse')
    logger.info(f"MCP Server url={config.url}")
    client = MultiServerMCPClient(
            {
                "all_tools": {
                    "url": config.url,
                    "transport": config.transport,
                },
            }
        )
    tools = await client.get_tools()
    selected_tools = []
    for tool in tools:
        if tool.name in ['get_neo4j_schema', 'read_neo4j_cypher']:
            selected_tools.append(tool)
    print(selected_tools)
    return selected_tools
async def get_notion_tools():
    config = get_mcp_server_config(port=3000, transport='streamable_http')
    logger.info(f"MCP Server url={config.url}")
    client = MultiServerMCPClient(
            {
                "all_tools": {
                    "url": config.url,
                    "transport": config.transport,
                    "headers": {"Authorization": "Bearer my_auth_token"}
                },
            }
        )
    tools = await client.get_tools()
    return tools

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal["input_required", "completed", "error"]
    message: str


class EnterpriseKnowledgeAgent(BaseAgent):
    @staticmethod
    async def get_relevant_chunks(query) -> str:
        """
        Retrieve relevant information chunks from the software documentation repository based on the user's query.
        Uses Solr search over pre-indexed document chunks to find the most relevant context for software development business questions.
        Args:
            query (str): The user's search query.
        Returns:
            str: Relevant context or information extracted from the documentation repository.
        """
        from utils.search import SolrSearch
        solr_search = SolrSearch(core="se_documents")
        context = solr_search.get_relevant_context(query)
        return context
    SYSTEM_PROMPT = f"""
        You are a human resources and project management assistant for Cyberdyne Systems.

        - If the question is related to HR management, skill analysis, talent search, or team building, use the knowledge in the graph database (Neo4j) and generate Cypher queries with the `read_neo4j_cypher` tool. ALWAYS get the schema first with `get_schema` and keep it in memory. Only use node labels, relationship types, property names, and patterns from that schema to generate valid Cypher queries using proper parameter syntax ($parameter). If you get errors or empty results, check the schema and try again up to 3 times.
        - If the question is related to project management, project information, project tasks, or project documentation (e.g., questions about projects, progress, tasks, project documents, project management), ALWAYS use Notion tools to query project data, documentation, or task tracking. DO NOT use get_relevant_chunks for these questions.
        - If the question is related to software development business (e.g., processes, forms, guidelines, technical documents, regulations, templates, references...), use `get_relevant_chunks` to retrieve information from the software documentation repository. Always ensure the query sent to `get_relevant_chunks` is in Vietnamese.

        For employee knowledge, use these standard values:
        - Domains: {[i.value for i in Domain]}
        - Work Types: {[i.value for i in WorkType]}
        - Skills: {[i.value for i in SkillName]}
        Never return embedding properties in Cypher queries, as this will cause delays and errors.

        When responding to the user:
        - Always provide a clear, structured, and detailed answer that directly addresses the question.
        - If the result is related to HR, always return both name and ID, never just the ID.
        - Avoid mentioning or describing the tools, databases, or internal processes used to get the result. The answer should read naturally, as if you already know the information.
        - If the user's query is about forms, templates, or sample documents, and the retrieved chunks contain relevant links, present those links directly to the user as references.
        - If the retrieved chunks include content that contains images (for example, image URLs), render those images directly in your answer along with any explanatory text.
        - Always enrich your answer with additional useful context, insights, or explanations whenever possible, so the response is comprehensive and actionable for the user.

        Always use information from previous queries when possible instead of asking the user again.
    """

    @classmethod
    async def create(cls):
        neo4j_tools = await get_neo4j_tools()
        notion_tools = await get_notion_tools()
        tools = neo4j_tools + notion_tools + [cls.get_relevant_chunks]
        agent = cls(tools=tools)
        return agent