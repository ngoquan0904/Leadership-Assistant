import httpx
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    SendMessageRequest,
    SendMessageResponse
)
import logging
logger = logging.getLogger(__name__)

class RemoteAgentConnections:
    def __init__(self, agent_card: AgentCard, agent_url: str):
        logger.info(f"Connected to {agent_card.name} in {agent_url}")
        self._httpx_client = httpx.AsyncClient(timeout=120)
        self.agent_client = A2AClient(self._httpx_client, agent_card, url=agent_url)
        self.card = agent_card

    def get_agent(self) -> AgentCard:
        return self.card
    async def send_message(self, message_request: SendMessageRequest) -> SendMessageResponse:
        return await self.agent_client.send_message(message_request)
