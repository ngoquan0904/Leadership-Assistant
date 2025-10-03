import json
import logging 
import asyncio
import httpx
import click
import uvicorn
from pathlib import Path
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryPushNotifier, InMemoryTaskStore
from a2a.types import AgentCard
from agent_executor import AgentExecutor
from calendar_agent import CalendarAgent
from gmail_agent import GmailAgent
from ek_agent import EnterpriseKnowledgeAgent
logger = logging.getLogger(__name__)

async def get_agent_executor(agent_card: AgentCard):
    try:
        if agent_card.name == "Calendar Agent":
            logger.info(f"Initialize {agent_card.name}")
            agent = CalendarAgent()
            return AgentExecutor(agent)
        elif agent_card.name == "Gmail Agent":
            logger.info(f"Initialize {agent_card.name}")
            agent = GmailAgent()
            return AgentExecutor(agent)
        elif agent_card.name == "Enterprise Knowledge Agent":
            logger.info(f"Initialize {agent_card.name}")
            agent = await EnterpriseKnowledgeAgent.create()
            return AgentExecutor(agent)
    except Exception as e:
        raise e
    
@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10001)
@click.option("--agent-card", "agent_card")

def main(host, port, agent_card):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    try:
        if not agent_card:
            raise ValueError('Agent card is required')
        with Path.open(agent_card) as file:
            data = json.load(file)
        agent_card = AgentCard(**data)
        print(agent_card.name)
        client = httpx.AsyncClient()
        agent_executor = asyncio.run(get_agent_executor(agent_card))
        print(agent_card.name)
        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(client)
        )
        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        uvicorn.run(server.build(), host=host, port=port)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"An error occurred during server startup: {e}")


if __name__ == "__main__":
    main()