"""
FastAPI main application for Orchestrator UI.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

try:
    from orchestrator_ui.backend.database import init_db
    from orchestrator_ui.backend.websocket import manager
    from orchestrator_ui.backend.api import projects, generation, auth, config
except ModuleNotFoundError:
    import database
    import websocket as ws_module
    from api import projects, generation, auth, config
    init_db = database.init_db
    manager = ws_module.manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler - runs on startup and shutdown.
    """
    # Startup: Initialize database
    print("Starting Orchestrator UI Backend...")
    init_db()
    print("Database initialized")

    yield

    # Shutdown
    print("Shutting down Orchestrator UI Backend...")


# Create FastAPI application
app = FastAPI(
    title="Orchestrator UI API",
    description="API for managing AI app generation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - MUST be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers
app.include_router(projects.router)
app.include_router(generation.router)
app.include_router(auth.router)
app.include_router(config.router)


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
    """
    await manager.connect(websocket, generation_id)
    try:
        # Keep connection alive and listen for messages
        while True:
            # Wait for any message from client (heartbeat)
            data = await websocket.receive_text()

            # Echo back for heartbeat
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket, generation_id)
    except Exception as e:
        print(f"⚠️ WebSocket error: {e}")
        manager.disconnect(websocket, generation_id)


if __name__ == "__main__":
    import sys
    import uvicorn

    port = 8000
    # Check for port override from environment or command line
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])

    uvicorn.run(app, host="0.0.0.0", port=port)
