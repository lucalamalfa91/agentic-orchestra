"""
FastAPI main application for Orchestrator UI.
"""
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

try:
    from orchestrator_ui.backend.database import init_db
    from orchestrator_ui.backend.encryption_init import ensure_encryption_key
    from orchestrator_ui.backend.websocket import manager
    from orchestrator_ui.backend.api import projects, generation, auth, config, knowledge, generation_control
except ModuleNotFoundError:
    import database
    import encryption_init
    import websocket as ws_module
    from api import projects, generation, auth, config, knowledge, generation_control
    init_db = database.init_db
    ensure_encryption_key = encryption_init.ensure_encryption_key
    manager = ws_module.manager


def run_migrations():
    """Run Alembic migrations to ensure DB schema is up to date."""
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg_path = Path(__file__).parent / "alembic.ini"
        alembic_cfg = Config(str(alembic_cfg_path))
        # Override script_location to absolute path so it works regardless of cwd
        alembic_cfg.set_main_option("script_location", str(Path(__file__).parent / "alembic"))
        command.upgrade(alembic_cfg, "head")
        print("Alembic migrations applied successfully")
    except Exception as e:
        print(f"[WARN] Alembic migration failed (non-fatal): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler - runs on startup and shutdown.
    """
    print("Starting Orchestrator UI Backend...")
    ensure_encryption_key()
    run_migrations()
    init_db()
    print("Database initialized")
    yield
    print("Shutting down Orchestrator UI Backend...")


# Create FastAPI application
app = FastAPI(
    title="Orchestrator UI API",
    description="API for managing AI app generation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS — set ALLOWED_ORIGINS env var in production (comma-separated URLs)
_origins_raw = os.getenv("ALLOWED_ORIGINS", "")
_allowed_origins = [o.strip() for o in _origins_raw.split(",") if o.strip()] or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(projects.router)
app.include_router(generation.router)
app.include_router(generation_control.router)
app.include_router(auth.router)
app.include_router(config.router)
app.include_router(knowledge.router)


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Orchestrator UI API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/generation/{generation_id}")
async def websocket_endpoint(websocket: WebSocket, generation_id: str):
    """
    WebSocket endpoint for real-time generation progress updates.
    Args are passed positionally — generation_id first, websocket second,
    matching ConnectionManager.connect(self, generation_id, websocket).
    """
    await manager.connect(generation_id, websocket)  # order matters!
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(generation_id, websocket)
    except Exception as e:
        print(f"[WARN] WebSocket error: {e}")
        manager.disconnect(generation_id, websocket)


if __name__ == "__main__":
    import sys
    import uvicorn

    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])

    uvicorn.run(app, host="0.0.0.0", port=port)
