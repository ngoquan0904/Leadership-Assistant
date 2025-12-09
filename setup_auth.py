import os
import sys

# Add the current directory to sys.path to ensure imports work if needed
sys.path.append(os.getcwd())

try:
    from langchain_google_community.calendar.utils import get_google_credentials
    from langchain_google_community.gmail.utils import get_gmail_credentials
except ImportError:
    print("Please install the required packages first: pip install langchain-google-community google-auth-oauthlib")
    sys.exit(1)

def setup_calendar_auth():
    print("\n--- Setting up Calendar Agent authentication ---")
    if not os.path.exists("client_secret.json"):
        print("Error: client_secret.json not found in the current directory.")
        return

    print("This will open a browser to authenticate for Google Calendar access.")
    try:
        get_google_credentials(
            token_file="token_calendar.json",
            scopes=["https://www.googleapis.com/auth/calendar"],
            client_secrets_file="client_secret.json"
        )
        print("Successfully generated token_calendar.json")
    except Exception as e:
        print(f"Error generating token: {e}")

def setup_gmail_auth():
    print("\n--- Setting up Gmail Agent authentication ---")
    if not os.path.exists("client_secret.json"):
        print("Error: client_secret.json not found.")
        return

    print("This will open a browser to authenticate for Gmail access.")
    try:
        get_gmail_credentials(
            token_file="token_gmail.json",
            scopes=["https://mail.google.com/"],
            client_secrets_file="client_secret.json"
        )
        print("Successfully generated token_gmail.json")
    except Exception as e:
        print(f"Error generating token: {e}")

if __name__ == "__main__":
    print("Starting authentication setup...")
    setup_calendar_auth()
    # setup_gmail_auth() # Uncomment if you need to regenerate gmail token
    print("\nSetup complete. You can now restart your docker containers.")
