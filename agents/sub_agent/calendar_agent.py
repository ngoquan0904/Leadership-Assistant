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
from datetime import datetime, date
from zoneinfo import ZoneInfo

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
        tools = CalendarToolkit(api_resource=self.get_api_resource()).get_tools()
        selected_tool = [
            t for t in tools if t.name != "get_current_datetime"
        ]
        return selected_tool

if __name__ == "__main__":
    # agent = CalendarAgent()
    # tools = agent.get_tools()
    # # for t in tools:
    # #     print(t.name)

    # create_event_tool = next(
    #     t for t in tools if t.name == "create_calendar_event"
    # )

    create_event_tool.invoke(
        {
            "summary": "Calculus exam",
            "start_datetime": "2026-01-09 11:00:00",
            "end_datetime": "2026-01-09 13:00:00",
            "timezone": "Asia/Ho_Chi_Minh",
            "location": "UAM Cuajimalpa",
            "description": "Event created from the LangChain toolkit",
            "reminders": [{"method": "popup", "minutes": 60}],
            "conference_data": True,
            "color_id": "5",
        }
    )
    now_vn = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    today_str = f"Today's date is {now_vn.strftime('%Y-%m-%d')}."
    print(today_str)
