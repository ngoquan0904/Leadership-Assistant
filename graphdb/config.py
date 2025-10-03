import os
from dotenv import load_dotenv
load_dotenv()

RESUME_PATH = r"D:\Document\Agent\CalendarAgent\graphdb\resume"
EXTRACTED_JSON = r"D:\Document\Agent\CalendarAgent\graphdb\resume\extracted_data.json"
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")