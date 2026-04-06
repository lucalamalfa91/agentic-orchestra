"""
Generation API endpoints.
"""
import asyncio
import jwt
import os
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

try:
    from orchestrator_ui.backend import schemas
    from orchestrator_ui.backend.database import get_db
    from orchestrator_ui.backend.orchestrator import GenerationOrchestrator, generate_id
    from orchestrator_ui.backend.models import User, Configuration
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import schemas
    from database import get_db
    from orchestrator import GenerationOrchestrator, generate_id
    from models import User, Configuration

router = APIRouter(prefix="/api/generation", tags=["generation"])
orchestrator = GenerationOrchestrator()

WS_BASE_URL = os.getenv("WS_BASE_URL", "ws://localhost:8000")


async def get_auth_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.replace("Bearer ", "")
    try:
        jwt_secret = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def run_generation_background(
    generation_id: str,
    request: schemas.GenerationRequest,
    db: Session,
    user_id: int
):
    """
    Background task to run generation.
    Waits 1.5s so the frontend WebSocket has time to connect.
    """
    try:
        await asyncio.sleep(1.5)
        project_id = await orchestrator.run_generation(generation_id, request, db, user_id)
        if project_id:
            print(f"[OK] Generation completed! Project ID: {project_id}")
        else:
            print(f"[ERROR] Generation failed for {generation_id}")
    except Exception as e:
        print(f"[ERROR] Background task error: {e}")
    finally:
        db.close()


@router.post("/start", response_model=schemas.GenerationStartResponse)
async def start_generation(
    request: schemas.GenerationRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_auth_user),
    db: Session = Depends(get_db)
):
    """
    Start a new app generation process.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.github_token:
        raise HTTPException(status_code=400, detail="GitHub account not connected")

    config = db.query(Configuration).filter(
        Configuration.user_id == user_id,
        Configuration.is_active == True
    ).first()

    print(f"DEBUG: user_id={user_id}, config={config}")
    if config:
        print(f"DEBUG: config.is_active={config.is_active}, config.ai_base_url={config.ai_base_url}")

    if not config:
        all_configs = db.query(Configuration).filter(Configuration.user_id == user_id).all()
        print(f"DEBUG: All configs for user {user_id}: {len(all_configs)}")
        for cfg in all_configs:
            print(f"  - id={cfg.id}, is_active={cfg.is_active}, base_url={cfg.ai_base_url}")
        raise HTTPException(status_code=400, detail="AI provider not configured")

    generation_id = generate_id()

    background_tasks.add_task(
        run_generation_background,
        generation_id,
        request,
        db,
        user_id
    )

    return schemas.GenerationStartResponse(
        generation_id=generation_id,
        message="Generation started successfully",
        websocket_url=f"{WS_BASE_URL}/ws/generation/{generation_id}"
    )


@router.get("/status/{generation_id}", response_model=schemas.GenerationStatus)
def get_generation_status(generation_id: str):
    return schemas.GenerationStatus(
        generation_id=generation_id,
        status="in_progress",
        message="Check WebSocket for real-time updates"
    )


def _cancel_project_by_id(project_id: int, db: Session):
    """Shared cancel logic: marks an in_progress project as failed."""
    try:
        from orchestrator_ui.backend.models import Project
        from orchestrator_ui.backend import crud
    except ModuleNotFoundError:
        from models import Project
        import crud

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"status": "not_found", "project_id": project_id,
                "message": f"Project {project_id} not found"}

    if project.status == "in_progress":
        crud.update_project_status(db, project_id, "failed")
        print(f"[CANCEL] project_id={project_id} marked as failed")
        return {"status": "cancelled", "project_id": project_id,
                "message": "Generation cancelled"}

    return {"status": "noop", "project_id": project_id,
            "message": f"Project status is '{project.status}', nothing to cancel"}


@router.post("/project/{project_id}/cancel")
def cancel_generation_by_project(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Cancel generation using numeric project_id.
    The frontend uses this because it does not have the generation UUID
    after the WS session ends.
    """
    return _cancel_project_by_id(project_id, db)


@router.post("/{generation_id}/cancel")
def cancel_generation(generation_id: str, db: Session = Depends(get_db)):
    """
    Cancel generation using the generation UUID.
    Kept for backwards compatibility; tries to find the matching project.
    """
    try:
        from orchestrator_ui.backend.models import GenerationLog, Project
        from orchestrator_ui.backend import crud
    except ModuleNotFoundError:
        from models import GenerationLog, Project
        import crud

    # Try to find the project linked to this generation via logs
    logs = db.query(GenerationLog).all()
    project = None
    for log in reversed(logs):
        if log.project_id:
            p = db.query(Project).filter(Project.id == log.project_id).first()
            if p and p.status == "in_progress":
                project = p
                break

    if project:
        crud.update_project_status(db, project.id, "failed")
        print(f"[CANCEL] generation_id={generation_id} -> project_id={project.id} marked as failed")
        return {"status": "cancelled", "generation_id": generation_id,
                "project_id": project.id, "message": "Generation cancelled"}

    return {"status": "cancel_requested", "generation_id": generation_id,
            "message": "Cancellation requested (no in-progress project found)"}
