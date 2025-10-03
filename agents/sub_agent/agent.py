import random
import os
from collections.abc import AsyncIterable
from datetime import datetime, date
from typing import Any, List, Literal
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()
memory = MemorySaver()

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"]
    message: str

class BaseAgent:
    SUPPORT_CONTENT_TYPES = ["text", "text/plain"]
    SYSTEM_PROMPT: str = ""

    def __init__(self, tools=None):
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))
        self.tools = tools if tools is not None else self.get_tools()

        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_PROMPT,
            response_format=ResponseFormat,
        )
    def get_api_resource(self):
        raise NotImplementedError
    
    def get_tools(self):
        raise NotImplementedError
    
    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get("structured_response")
        if structured_response and isinstance(structured_response, ResponseFormat):
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            if structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message
                }
        return {
            "is_task_complete": False,
            "require_user_input": False,
            "content": (
                "We are unable to process your request at the moment. "
                "Please try again."
            ),
        }
    async def stream(self, query, context_id) -> AsyncIterable[dict[str, Any]]:
        config: RunnableConfig = {"configurable": {"thread_id": context_id}}
        today_str = f"Today's date is {date.today().strftime('%Y-%m-%d')}."
        augmented_query = f"{today_str}\n\nUser query: {query}"
        input = {"messages": [("user", augmented_query)]}

        async for item in self.graph.astream(input, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                tool_names = [call["name"] for call in message.tool_calls]
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": f"Calling tool(s): {', '.join(tool_names)}"
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": f"Tool message: {message.content}"
                }
        yield self.get_agent_response(config)