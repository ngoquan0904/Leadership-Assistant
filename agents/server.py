import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import UploadFile, File, Form, HTTPException
import asyncio
import subprocess
from fastapi.middleware.cors import CORSMiddleware
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

# Allow frontend (served on localhost:8000) to call API on localhost:8001
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/install-agent")
async def install_agent(
    profile: str = Form(...),
    service_name: str = Form(...),
    port: int = Form(...),
    file: UploadFile = File(...),
    sender_email: str | None = Form(None),
    sender_password: str | None = Form(None),
):
    """Upload a credential file and start the specified agent service using docker compose.

    Expects:
    - profile: docker compose profile (e.g. 'calendar' or 'gmail')
    - service_name: service key from docker-compose (e.g. 'calendar_agent')
    - port: internal port exposed by the agent (e.g. 10002)
    - file: uploaded client_secret json
    """
    try:
        global host_agent_instance
        if not host_agent_instance:
            raise RuntimeError("HostAgent not initialized")

        # save uploaded file to agent_cards/client_secret.json (mapped into agent containers)
        save_dir = os.path.join(os.getcwd(), "agent_cards")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, "client_secret.json")
        logger.info("Saving uploaded client secret to %s", save_path)
        try:
            content = await file.read()
            with open(save_path, "wb") as f:
                f.write(content)
        except Exception as e:
            logger.exception("Failed to save uploaded file")
            raise RuntimeError(f"Failed to save uploaded file: {e}")

        # if gmail creds provided, write an env file that will be mounted via docker-compose
        if service_name == "gmail_agent" and (sender_email or sender_password):
            env_path = os.path.join(save_dir, "gmail.env")
            logger.info("Writing gmail env to %s", env_path)
            try:
                with open(env_path, "w", encoding="utf-8") as ef:
                    if sender_email:
                        ef.write(f"sender_email={sender_email}\n")
                    if sender_password:
                        ef.write(f"sender_password={sender_password}\n")
            except Exception as e:
                logger.exception("Failed to save env file")
                raise RuntimeError(f"Failed to save env file: {e}")

        # start the agent via docker compose (capture output)
        cmd = ["docker", "compose", "--profile", profile, "up", "-d", service_name]
        logger.info("Running command: %s", " ".join(cmd))
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=os.getcwd(),
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            msg = (
                "Docker CLI not found inside orchestrator container. "
                "Can't run `docker compose` from inside the container.\n"
                "Options:\n"
                " 1) Run the orchestrator on the host (not in docker), so it can call docker compose.\n"
                " 2) Mount the Docker socket and provide docker CLI inside the orchestrator image (not recommended for prod).\n"
                " 3) Start the agent manually on the host: `docker compose --profile {profile} up -d {service}` and then call the orchestrator register API.`"
            )
            logger.error(msg)
            raise RuntimeError(msg)

        logger.info("docker compose returncode=%s stdout=%s stderr=%s", result.returncode, result.stdout, result.stderr)
        if result.returncode != 0:
            raise RuntimeError(f"docker compose failed: returncode={result.returncode} stderr={result.stderr}")

        # register new agent with HostAgent
        agent_url = f"http://{service_name}:{port}"
        logger.info("Registering agent at %s", agent_url)
        try:
            await host_agent_instance.add_remote_agent(agent_url)
        except Exception as e:
            logger.exception("Failed to register agent after starting service")
            return {"status": "started", "agent_url": agent_url, "warning": str(e)}

        return {"status": "started", "agent_url": agent_url}
    except Exception as e:
        logger.exception("install-agent failed")
        # Return a helpful error message without exposing uploaded file contents.
        raise HTTPException(status_code=500, detail=str(e))

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
