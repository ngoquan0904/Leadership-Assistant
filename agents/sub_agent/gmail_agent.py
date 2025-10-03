import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from langchain_google_community import GmailToolkit
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_community.gmail.utils import (
    build_resource_service,
    get_gmail_credentials,
)
from agent import BaseAgent
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()
@tool
def convert_to_html(body: str) -> str:
    """
    Convert plain text email body to HTML using Gemini LLM.

    Args:
        body (str): The plain text body of the email.

    Returns:
        str: HTML formatted email body only.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))
    prompt = (
        f"Convert the following email body to HTML. Use <p> for paragraphs. "
        f"For closing lines like 'Sincerely,' and the name, use <br> to keep them together. "
        f"Place the horizontal line (<hr>) directly above the signature, with no extra space. "
        f"Only output the HTML content, do not include any explanation, instructions, or extra text.\n\n{body}"
    )
    response = llm.invoke(prompt)
    return response.content
@tool
def send_email(recipient_email, subject, body):
    """
    Send an email using Gmail's SMTP server.

    Args:
        recipient_email (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The body content of the email.

    Returns:
        str: Success or failure message.
    """
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")

    if not sender_email or not sender_password:
        return "Sender email or password is not set in environment variables."

    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        body = convert_to_html(body)
        message.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        return f"Email sent successfully to {recipient_email}."
    except Exception as e:
        return f"Failed to send email: {e}"
@tool
def create_content_email(request: str) -> str:
    """
    Generate email content using Gemini LLM based on user's request, with a signature and confirmation question.

    Args:
        request (str): Description of the email the user wants to write.

    Returns:
        str: Generated email content with signature and confirmation question.
    """
    signature = (
        "——————————————————————————————————————————\n"
        "Ngo Minh Quan\n"
        "Student | School of Information and Communications Technology\n"
        "Hanoi University of Science and Technology\n"
        "ngoquan.0904@gmail.com | 0966938727"
    )
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))
    prompt = (
        f"Write a professional, clear, and polite email based on the following request:\n"
        f"{request}\n"
        f"Format the email with a subject and body. At the end, use a suitable closing (such as 'Sincerely,' or 'Regards,') followed by 'Ngo Minh Quan', then add this signature:\n{signature}\n"
        f"Do not add student ID, course name, or any other optional fields."
    )
    response = llm.invoke(prompt)
    email_content = response.content
    return f"{email_content}\nDo you want any edits to this email?"
    
class GmailAgent(BaseAgent):
    SYSTEM_PROMPT = f"""
    You are an agent that can help manage a user's Gmail.

    Users will request information about their emails or ask you to create the email content, send, draft, or organize emails. Use the provided tools for interacting with the Gmail API.
    Only create a draft email when the user explicitly requests to create a draft.
    When the user requests to send an email, use the 'send_email' tool to send the email.
    If the user wants to write or send an email, first create the email content using 'create_content_email' tool and **always send the generated email content from tool back to the user for review**. Do not send the email until the user has confirmed the content.

    If not specified, assume the user wants to use their primary Gmail account.

    Always be clear and concise in your responses.
    Today is {datetime.now()}.
    """

    def get_api_resource(self):
        credential = get_gmail_credentials(
            token_file="token_gmail.json",
            scopes=["https://mail.google.com/"],
            client_secrets_file=os.getenv("client_secrets_file"),
        )
        api_resource = build_resource_service(credentials=credential)
        return api_resource
    
    def get_tools(self):
        tools = GmailToolkit(api_resource=self.get_api_resource()).get_tools()
        tools.append(create_content_email)
        tools.append(send_email)
        tools.append(convert_to_html)
        selected_tools = [t for t in tools if "send_gmail_message" not in t.name]
        return selected_tools
