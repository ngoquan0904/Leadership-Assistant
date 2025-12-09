import os
from datetime import datetime
import sys
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from utils.prompts import CALENDAR_AGENT_SYSTEM_PROMPT
from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service,
    get_google_credentials
)
from agent import BaseAgent

class CalendarAgent(BaseAgent):
    SYSTEM_PROMPT = CALENDAR_AGENT_SYSTEM_PROMPT.format(current_time=datetime.now())

    def get_api_resource(self):
        credentials = get_google_credentials(
            token_file="token.json",
            scopes=["https://www.googleapis.com/auth/calendar"],
            client_secrets_file=os.getenv("client_secrets_file")
        )
        api_resource = build_resource_service(credentials=credentials)
        return api_resource
    def get_tools(self):
        return CalendarToolkit(api_resource=self.get_api_resource()).get_tools()