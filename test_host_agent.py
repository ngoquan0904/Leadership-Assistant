import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure the project root is in sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from agents.host.agent import HostAgent

async def main():
    print("Initializing HostAgent...")
    # Initialize with empty remote agents for now
    # If you have actual remote agents running, you can add their URLs here
    # e.g. ["http://localhost:8001", "http://localhost:8002"]
    agent_urls = [] 
    
    try:
        host_agent = await HostAgent.create(remote_agent_addresses=agent_urls)
        print("HostAgent initialized successfully.")
        
        query = "giải thích về NLP"
        print(f"\nSending query: '{query}'")
        
        session_id = "test_session_001"
        
        print("\nStreaming response:")
        async for response in host_agent.stream(query, session_id):
            print(response)
            if response.get("is_task_complete"):
                print(f"\nFinal Response:\n{response.get('content')}")
            else:
                # Print updates on the same line or new lines
                print(f"Update: {response.get('updates')}")
                
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
