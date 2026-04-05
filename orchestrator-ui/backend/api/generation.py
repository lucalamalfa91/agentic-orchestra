"""
Generation API endpoints.
"""
import asyncio
import jwt
import os
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Header
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

# Global orchestrator instance
orchestrator = GenerationOrchestrator()


async def get_auth_user(authorization: str = Header(None)):
    """
    Verify JWT token and return authenticated user ID.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User ID from validated token

    Raises:
        HTTPException: If token is missing or invalid
    """
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
    db: Session
):
    """
    Background task to run generation.
    """
    try:
        project_id = await orchestrator.run_generation(generation_id, request, db)
        if project_id:
            print(f"[OK] Generation completed successfully! Project ID: {project_id}")
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

    This endpoint:
    1. Validates user authentication
    2. Checks GitHub connection
    3. Checks AI provider configuration
    4. Generates a unique generation ID
    5. Starts generation in background
    6. Returns WebSocket URL for progress tracking
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Check if GitHub is connected
    if not user.github_token:
        raise HTTPException(status_code=400, detail="GitHub account not connected")

    # Check if AI provider is configured
    config = db.query(Configuration).filter(
        Configuration.user_id == user_id,
        Configuration.is_active == True
    ).first()

    print(f"DEBUG: user_id={user_id}, config={config}")
    if config:
        print(f"DEBUG: config.is_active={config.is_active}, config.ai_base_url={config.ai_base_url}")

    if not config:
        # Check all configs for this user
        all_configs = db.query(Configuration).filter(Configuration.user_id == user_id).all()
        print(f"DEBUG: All configs for user {user_id}: {len(all_configs)}")
        for cfg in all_configs:
            print(f"  - id={cfg.id}, is_active={cfg.is_active}, base_url={cfg.ai_base_url}")
        raise HTTPException(status_code=400, detail="AI provider not configured")

    # Generate unique ID
    generation_id = generate_id()

    # Add background task
    background_tasks.add_task(
        run_generation_background,
        generation_id,
        request,
        db
    )

    return schemas.GenerationStartResponse(
        generation_id=generation_id,
        message="Generation started successfully",
        websocket_url=f"ws://localhost:9000/ws/generation/{generation_id}"
    )


@router.get("/status/{generation_id}", response_model=schemas.GenerationStatus)
def get_generation_status(generation_id: str):
    """
    Get current status of a generation (for polling fallback).
    """
    # This is a simple implementation - in production you'd track status in memory or DB
    # For now, just return a basic response
    return schemas.GenerationStatus(
        generation_id=generation_id,
        status="in_progress",
        message="Check WebSocket for real-time updates"
    )


@router.post("/{generation_id}/cancel")
def cancel_generation(generation_id: str, db: Session = Depends(get_db)):
    """
    Cancel an ongoing generation and mark associated project as failed.
    """
    try:
        # Find project with this generation ID in logs
        log = db.query(schemas if hasattr(schemas, 'GenerationLog') else type('obj', (object,), {})) \
            .filter_by(step_name=generation_id).first() if hasattr(schemas, 'GenerationLog') else None

        # Alternative: search by message containing generation_id
        from orchestrator_ui.backend.models import GenerationLog, Project

        logs = db.query(GenerationLog).filter(
            GenerationLog.project_id.isnot(None)
        ).all()

        # Find the most recent project that was being generated
        project = None
        for log in reversed(logs):
            if log.project_id:
                project = db.query(Project).filter(Project.id == log.project_id).first()
                if project and project.status == 'in_progress':
                    break

        if project:
            # Update project status to failed
            from orchestrator_ui.backend import crud
            crud.update_project_status(db, project.id, 'failed')

            return {
                "status": "cancelled",
                "generation_id": generation_id,
                "project_id": project.id,
                "message": "Generation cancelled and marked as failed"
            }

        return {
            "status": "cancel_requested",
            "generation_id": generation_id,
            "message": "Cancellation requested"
        }
    except Exception as e:
        print(f"[ERROR] Error cancelling generation: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
