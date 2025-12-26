import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from agents.host.agent import HostAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

host_agent_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global host_agent_instance
    raw_agent_urls = os.getenv("AGENT_URLS", '[]')
    logger.info(f"Initializing HostAgent with URLs: {raw_agent_urls}")
    try:
        agent_urls = json.loads(raw_agent_urls)
        host_agent_instance = await HostAgent.create(remote_agent_addresses=agent_urls)
        logger.info("HostAgent initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize HostAgent: {e}")
    yield
    # Clean up if necessary

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                query = message_data.get("query")
                session_id = message_data.get("session_id", "default_session")
            except json.JSONDecodeError:
                query = data
                session_id = "default_session"
            
            if not host_agent_instance:
                await websocket.send_json({
                    "is_task_complete": True, 
                    "content": "Host Agent is not initialized."
                })
                continue

            logger.info(f"Received query: {query} for session: {session_id}")
            
            try:
                async for event in host_agent_instance.stream(query, session_id):
                    await websocket.send_json(event)
            except Exception as e:
                logger.error(f"Error processing query: {e}")
                await websocket.send_json({
                    "is_task_complete": True,
                    "content": f"Error: {str(e)}"
                })

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
