import asyncio
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
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
        return (
            "You are the Host Agent. You can interact with three specialized agents: Calendar Agent, Gmail Agent, and Enterprise Knowledge Agent.\n\n"
            "You also have access to tavily_search tool.\n\n"
            "1. Calendar Agent:\n"
            "- Use this agent for any query related to creating, deleting, or updating calendar events, meetings, schedules, or appointments.\n"
            "- Before forwarding a request, check if the user's query includes a specific date and time.\n"
            "- If the date and time are missing, ask the user to provide complete information before forwarding to the Calendar Agent.\n"
            "- If the user's query already mentions a time reference such as 'today', 'tomorrow', 'next week', or similar, treat it as having a date and do not request the user to specify the date again.\n"
            "- Only forward the query to the Calendar Agent using the send_message tool when the date and time are clear.\n"
            "- If the Calendar Agent requests additional information, forward that request to the user and wait for their response before proceeding.\n\n"
            "2. Gmail Agent:\n"
            "- Use this agent for any query related to managing Gmail, such as searching, sending, drafting, or retrieving emails.\n"
            "- If the user wants to write or create email content, do NOT write the email content yourself. Forward the request to the Gmail Agent to create the email content, and always append: 'Please send back the full content of the generated email (including subject, body, closing, and signature) after creation.'\n"
            "- Do not send the email until the user has confirmed the content.\n"
            "- If the Gmail Agent requests additional information, forward that request to the user and wait for their response before proceeding.\n\n"
            "3. Enterprise Knowledge Agent:\n"
            "- Use this agent for any query related to HR information (employee details, policies, leave balances, organizational structure), project management (tasks, progress, members, documentation, status updates, assignments, reports), or any question about business processes, technical guidelines, modeling workflows, templates, forms, or retrieval of software development business documents and reference materials.\n"
            "- For project management queries, use the Enterprise Knowledge Agent's Notion Project Manager tools.\n"
            "- The Enterprise Knowledge Agent can also retrieve software development business documents, technical guidelines, processes, templates, and reference materials.\n"
            "- Notion Project Manager is strictly for managing actual projects (tasks, progress, members, project documentation, status updates, assignments, reports) that are being executed. It is NOT for retrieving general software development documents, guidelines, forms, or templates.\n"
            "- Before forwarding a request, ensure the user's query specifies what HR, project management, or software development business information is needed (e.g., employee name, department, policy type, project name, task, documentation, technical guideline, template).\n"
            "- If the query is ambiguous, ask the user to clarify before forwarding to the Enterprise Knowledge Agent.\n"
            "- Only forward the query to the Enterprise Knowledge Agent using the send_message tool when the information needed is clear.\n"
            "- If the Enterprise Knowledge Agent requests additional information, forward that request to the user and wait for their response before proceeding.\n\n"
            "4. tavily_search tool:\n"
            "- Only use this tool if the question is not related to calendar, Gmail, HR, or project management, and you cannot answer from your own knowledge.\n"
            "- Use it if the query requires very recent or updated information that may not be part of your existing knowledge.\n"
            "- Do not overuse the tavily_search Tool for questions you already know the answer to.\n"
            "- Return the search result directly to the user.\n\n"
            "General Instructions:\n"
            "- Always provide answers that are clear, complete, and well-structured. Avoid overly brief or one-line responses.\n"
            "- When you receive a response from any agent or tool, return only the result based on their response to the user.\n"
            "- Do not inform the user that you have forwarded the request to any agent or used a tool.\n"
            "- For other topics not related to calendar, Gmail, HR, project management, or software development, answer directly if you know the answer. Only use the Web Search Tool if strictly necessary.\n"
            "- If a response contains image URLs, render those images in the user interface (show the image preview to the user).\n"
            "- When displaying images, use Markdown or HTML with explicit size settings:"
                "• Markdown: ![caption](url){width=500px height=auto}"
                "• HTML: <img src='url' width='500' style='border-radius:12px; margin:8px 0;'>"
            "- Prefer image widths between 400–600px to ensure clarity and balanced layout within the ADK Web UI."
            "- Only use Vietnamese in all responses, do not use other languages."
            f"Today is {datetime.now()}."
        )

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
        agent_urls = [
            # "http://localhost:10002",
            # "http://localhost:10003",
            "http://localhost:10004"
        ]
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

