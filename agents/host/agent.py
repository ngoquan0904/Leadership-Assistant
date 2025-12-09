import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from utils.prompts import HOST_AGENT_ROOT_INSTRUCTION
import json
import uuid
from datetime import datetime
from typing import Any, AsyncIterable, List

import httpx
import nest_asyncio
from a2a.client import A2ACardResolver
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task
)
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from langchain_community.tools.tavily_search.tool import TavilySearchResults
from .remote_agent_connection import RemoteAgentConnections
from dotenv import load_dotenv
load_dotenv()
nest_asyncio.apply()

class HostAgent:
    def __init__(self):
        self.remote_agent_connections: dict[str, RemoteAgentConnections] = {}
        self.cards: dict[str, AgentCard] = {}
        self.agents: str = ""
        self.web_search_tool = TavilySearchResults(
            k=5,
            tavily_api_key=os.getenv("TAVILY_API_KEY")
        )
        self._agent = self.create_agent()
        self._user_id = "host_agent"
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service = InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService()
        )
        
    async def _async_init_components(self, remote_agent_addresses: List[str]):
        """Tạo connections instance đến các remote agent"""
        async with httpx.AsyncClient(timeout=120) as client:
            for address in remote_agent_addresses:
                card_resolver = A2ACardResolver(client, address)
                try:
                    card = await card_resolver.get_agent_card()
                    remote_connection = RemoteAgentConnections(
                        agent_card=card, agent_url=address
                    )
                    self.remote_agent_connections[card.name] = remote_connection
                    self.cards[card.name] = card
                except httpx.ConnectError as e:
                    print(f"ERROR: Failed to initialize connection for {address}: {e}")
        agent_info = [
            json.dumps({"name": card.name, "description": card.description})
            for card in self.cards.values()
        ]
        print("agent_infor:", agent_info)
        self.agents = "\n".join(agent_info) if agent_info else "No agent found."
    @classmethod
    async def create(cls, remote_agent_addresses: List[str]):
        instance = cls()
        await instance._async_init_components(remote_agent_addresses)
        return instance

    def create_agent(self) -> Agent:
        return Agent(
            model="gemini-2.5-flash",
            name="Host_Agent",
            instruction=self.root_instruction,
            description="",
            tools=[
                self.send_message,
                self.tavily_search,
            ]
        )

    def root_instruction(self, context: ReadonlyContext) -> str:
        return HOST_AGENT_ROOT_INSTRUCTION.format(current_time=datetime.now())

    async def tavily_search(self, query: str) -> str:
        search_result = self.web_search_tool.run(query)
        # print(search_result)  
        return search_result

    
    async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
        if "_" in agent_name:
            agent_name = " ".join(agent_name.split("_"))
        if agent_name not in self.remote_agent_connections:
            raise ValueError(f"Agent {agent_name} not found.")
        client = self.remote_agent_connections[agent_name]

        if not client:
            raise ValueError(f"Client not available got {agent_name}")
        
        state = tool_context.state
        task_id = state.get("task_id", str(uuid.uuid4()))
        context_id = state.get("context_id", str(uuid.uuid4()))
        message_id = str(uuid.uuid4())

        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
                "taskId": task_id,
                "contextId": context_id,
            },
        }
        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )
        send_response: SendMessageResponse = await client.send_message(message_request)
        print("Send response:", send_response)

        if not isinstance(
            send_response.root, SendMessageSuccessResponse
        ) or not isinstance(send_response.root.result, Task):
            """
            - send_response.root: kiến tra gửi message success hay error,
            - send_response.root.result: kiếm trả remote agent trả lại 1 Task - tức là agent đã thực hiện trả về Task chứa tool đã dùng, artifact thu được...
            """
            print(f"Received a non-success or non-task response. Cannot proceed.")
        
        response_content = send_response.root.model_dump_json(exclude_none=True)
        # sau khi chuyển root.model_dump_json sẽ thành
        # {
        #     "result": {
        #         "tool_name": "check_availability",
        #         "status": "completed",
        #         "artifacts": [
        #         {
        #             "parts": [
        #                     {"type": "text", "text": "I am free after 4pm"},
        #                     {"type": "text", "text": "Also free Saturday morning"}
        #              ]
        #         }
        #         ],
        #         "state": {
        #         "context_id": "abc",
        #         "task_id": "xyz"
        #         }
        #     }
        # }
        json_content = json.loads(response_content)
        print(json.dumps(json_content, indent=2, ensure_ascii=False))
        state = json_content.get("result", {}).get("status").get("state")
        # Nếu CalendarAgent yêu cầu thêm thông tin từ user
        if ("required" in state or "working" in state):
            # Forward lại yêu cầu này cho user
            message = ""
            artifacts = json_content["result"].get("artifacts", [])
            if artifacts:
                for artifact in artifacts:
                    for part in artifact.get("parts", []):
                        if part.get("kind") == "text":
                            message += part.get("text", "") + "\n"
            else:
                status_message = json_content["result"].get("status", {}).get("message", {})
                parts = status_message.get("parts", [])
                for part in parts:
                    if part.get("kind") == "text":
                        message += part.get("text", "") + "\n"
            print("Response message: ", message)
            return [{
                "is_task_complete": False,
                "require_user_input": True,
                "content": message.strip()
            }]
        resp = []
        if json_content.get("result", {}).get("artifacts"):
            for artifact in json_content["result"]["artifacts"]:
                if artifact.get("parts"):
                    resp.extend(artifact["parts"])
        print("Response: ", resp)
        return resp
    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        session = await self._runner.session_service.get_session(
            app_name=self._agent_name,
            user_id=self._user_id,
            state={},
            session_id=session_id
        )
        # tạo message từ query cuar user
        content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id
            )
        
        async for event in self._runner.run_async(
            user_id=self._user_id, session_id=session_id, new_message=content
        ):
            """
            - nếu là final response thì lấy text từ các parts trong event ra
            - chưa thì là đang thinking
            """
            if event.is_final_response():
                response = ""
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    response = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )
                yield {
                    "is_task_complete": True,
                    "content": response,
                }
            else:
                yield {
                    "is_task_complete": False,
                    "updates": "The host agent is thinking...."
                }
def _get_initialize_host_agent_sync():
    async def _async_main():
        raw_agent_urls = os.getenv("AGENT_URLS", '[]')
        print(f"DEBUG: AGENT_URLS from env: {raw_agent_urls}")
        agent_urls = json.loads(raw_agent_urls)
        print("Initializing host agent")
        hosting_agent_instance = await HostAgent.create(
            remote_agent_addresses=agent_urls
        )
        print("HostAgent initialized.")
        return hosting_agent_instance.create_agent()
    try:
        return asyncio.run(_async_main())
    except RuntimeError as e:
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            print(
                f"Warning: Could not initialize HostAgent with asyncio.run(): {e}. "
                "This can happen if an event loop is already running (e.g., in Jupyter). "
                "Consider initializing HostAgent within an async function in your application."
            )
        else:
            raise
    
root_agent = _get_initialize_host_agent_sync()

