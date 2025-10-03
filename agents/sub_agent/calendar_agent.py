import os
from datetime import datetime
from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service,
    get_google_credentials
)
from agent import BaseAgent

class CalendarAgent(BaseAgent):
    SYSTEM_PROMPT = f"""You are an agent that can help manage a user's calendar.

    Users will request information about the state of their calendar or to make changes to
    their calendar. Use the provided tools for interacting with the calendar API.

    If not specified, assume the calendar the user wants is the 'primary' calendar.

    Before creating a new event, always check if there is already an event scheduled at the requested time slot.
    If there is a conflict, inform the user about the existing event and do not create a new one unless the user confirms to overwrite or reschedule.
    Only create events with details explicitly provided by the user. Do not invent or assume event details.
    
    When using the Calendar API tools, use well-formed RFC3339 timestamps.
    If the user does not specify a timezone, default to 'Asia/Ho_Chi_Minh'.
    Today is {datetime.now()}."""

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