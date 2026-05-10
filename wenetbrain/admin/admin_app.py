"""FastAPI admin application for WenetBrain."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from admin.admin_routes import router as admin_router
from app.tools import migrate_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncIterator[None]:
    migrate_db()
    logger.info("Admin app starting up...")
    yield
    logger.info("Admin app shutting down...")


app = FastAPI(
    title="wenetbrain-admin",
    description="Admin panel for WenetBrain — users, spaces, ACL",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)


@app.get("/login.html")
def login_page(api: str | None = None):
    """Serve admin login page. Injects correct API URL if not already set."""
    from fastapi.responses import HTMLResponse
    with open("app/frontend/static/login.html", encoding="utf-8") as f:
        html = f.read()
    if not api:
        html = html.replace(
            "const API = params.get('api') || 'http://localhost:8000';",
            "const API = params.get('api') || 'http://localhost:8001';",
        ).replace(
            "const tokenKey = params.get('key') || 'wenetbrain_token';",
            "const tokenKey = params.get('key') || 'wenetbrain_admin_token';",
        ).replace(
            "const appName = params.get('app') || 'Aplikacja';",
            "const appName = params.get('app') || 'Panel admina';",
        )
    return HTMLResponse(content=html)


@app.get("/api/status")
def api_status() -> dict:
    """Admin API status."""
    return {
        "app": "WenetBrain Admin",
        "version": "0.1.0",
        "status": "running",
    }


# Serve React admin frontend built files
app.mount("/", StaticFiles(directory="admin/frontend/dist", html=True), name="static")


# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
