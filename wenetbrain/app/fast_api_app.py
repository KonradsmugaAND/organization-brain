"""FastAPI app with A2A protocol support for WenetBrain."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.a2a.executor.a2a_agent_executor import A2aAgentExecutor
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Load .env and set defaults BEFORE any env-dependent imports
load_dotenv()
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "wenetbrain-local")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
if "GOOGLE_GENAI_USE_VERTEXAI" not in os.environ:
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")

from app.agent import app as adk_app  # noqa: E402
from app.api_routes import router as api_router  # noqa: E402
from app.app_utils.typing import Feedback  # noqa: E402
from app.tools import migrate_db  # noqa: E402

# Logging setup (fallback to standard logging if GCP is unavailable)
try:
    import google.auth
    from google.cloud import logging as google_cloud_logging

    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "wenetbrain-local")

artifact_service = InMemoryArtifactService()

runner = Runner(
    app=adk_app,
    artifact_service=artifact_service,
    session_service=InMemorySessionService(),
)

request_handler = DefaultRequestHandler(
    agent_executor=A2aAgentExecutor(runner=runner), task_store=InMemoryTaskStore()
)

A2A_RPC_PATH = f"/a2a/{adk_app.name}"


async def build_dynamic_agent_card() -> AgentCard:
    """Builds the Agent Card dynamically from the root_agent."""
    agent_card_builder = AgentCardBuilder(
        agent=adk_app.root_agent,
        capabilities=AgentCapabilities(streaming=True),
        rpc_url=f"{os.getenv('APP_URL', 'http://0.0.0.0:8000')}{A2A_RPC_PATH}",
        agent_version=os.getenv("AGENT_VERSION", "0.1.0"),
    )
    agent_card = await agent_card_builder.build()
    return agent_card


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
    migrate_db()
    agent_card = await build_dynamic_agent_card()
    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
    a2a_app.add_routes_to_app(
        app_instance,
        agent_card_url=f"{A2A_RPC_PATH}{AGENT_CARD_WELL_KNOWN_PATH}",
        rpc_url=A2A_RPC_PATH,
        extended_agent_card_url=f"{A2A_RPC_PATH}{EXTENDED_AGENT_CARD_PATH}",
    )
    yield


app = FastAPI(
    title="wenet-brain",
    description="API for interacting with the Agent WenetBrain",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/login.html")
def login_page():
    """Serve the shared login page."""
    return FileResponse("app/frontend/static/login.html")


# Serve React frontend built files
app.mount("/", StaticFiles(directory="app/frontend/dist", html=True), name="static")


@app.get("/api/status")
def api_status() -> dict:
    """WenetBrain API status and links."""
    return {
        "app": "WenetBrain",
        "version": "0.1.0",
        "status": "running",
        "mode": "local_poc",
        "links": {
            "docs": "http://localhost:8000/docs",
            "a2a_agent_card": "http://localhost:8000/a2a/wenetbrain/.well-known/agent.json",
            "a2a_rpc": "http://localhost:8000/a2a/wenetbrain",
            "qdrant_dashboard": "http://localhost:6333/dashboard",
        },
        "agents": [
            "meeting_agent",
            "extraction_agent",
            "routing_agent",
            "knowledge_agent",
            "chat_agent",
            "clickup_agent",
            "calendar_agent",
            "inbox_agent",
        ],
    }


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    if hasattr(logger, "log_struct"):
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        logger.info("Feedback: %s", feedback.model_dump())
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
