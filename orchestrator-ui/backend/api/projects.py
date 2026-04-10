"""
Projects API endpoints.
"""
from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from orchestrator_ui.backend import crud, schemas
    from orchestrator_ui.backend.database import get_db
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    import crud
    import schemas
    from database import get_db

router = APIRouter(prefix="/api/projects", tags=["projects"])

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


class ProjectStatusUpdate(BaseModel):
    """Schema for updating project status."""
    status: Literal["pending", "in_progress", "completed", "failed"]


@router.options("/{project_id}/status")
async def options_project_status(project_id: int):
    """Explicit OPTIONS handler so CORS preflight always returns 200."""
    return JSONResponse(status_code=200, content={}, headers=CORS_HEADERS)


@router.get("/", response_model=schemas.PaginatedProjects)
def list_projects(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """
    List all projects with pagination.
    """
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

    skip = (page - 1) * page_size
    projects = crud.get_projects(db, skip=skip, limit=page_size)
    total = crud.get_projects_count(db)
    total_pages = (total + page_size - 1) // page_size

    return schemas.PaginatedProjects(
        items=projects,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{project_id}", response_model=schemas.ProjectWithRequirements)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Get project details by ID, including requirements if available.
    """
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    requirements = crud.get_project_requirements(db, project_id)

    return schemas.ProjectWithRequirements(
        id=project.id,
        name=project.name,
        description=project.description,
        github_repo_url=project.github_repo_url,
        status=project.status,
        created_at=project.created_at,
        requirements=requirements
    )


@router.get("/{project_id}/requirements", response_model=schemas.ProjectRequirementResponse)
def get_project_requirements(project_id: int, db: Session = Depends(get_db)):
    """
    Get original requirements for a project (for regeneration).
    """
    requirements = crud.get_project_requirements(db, project_id)
    if not requirements:
        raise HTTPException(status_code=404, detail="Requirements not found for this project")

    return requirements


@router.get("/{project_id}/logs", response_model=List[schemas.GenerationLogResponse])
def get_project_logs(project_id: int, db: Session = Depends(get_db)):
    """
    Get generation logs for a project.
    """
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = crud.get_project_logs(db, project_id)
    return logs


@router.patch("/{project_id}/status", response_model=schemas.ProjectResponse)
def update_project_status_endpoint(
    project_id: int,
    status_update: ProjectStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update project status.
    """
    project = crud.update_project_status(db, project_id, status_update.status)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Delete a project and its associated data.
    """
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        crud.delete_project_requirements(db, project_id)
        crud.delete_project_logs(db, project_id)
        crud.delete_project(db, project_id)
        return {"status": "deleted", "project_id": project_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


@router.post("/{project_id}/resume", response_model=schemas.GenerationStartResponse)
async def resume_generation(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    Resume a failed generation by restarting with same requirements.

    - Verifies project exists and status is 'failed'
    - Fetches original requirements from database
    - Increments generation_attempt counter
    - Starts new generation with same requirements
    - Returns new generation_id and WebSocket URL
    """
    # 1. Verify project exists and is failed
    project = crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Can only resume failed projects (current status: {project.status})"
        )

    # 2. Get original requirements
    requirements = crud.get_project_requirements(db, project_id)
    if not requirements:
        raise HTTPException(status_code=404, detail="Requirements not found")

    # 3. Reconstruct GenerationRequest
    import json
    from orchestrator_ui.backend.schemas import GenerationRequest, TechStack

    try:
        request = GenerationRequest(
            mvp_description=requirements.mvp_description,
            features=json.loads(requirements.features),
            user_stories=json.loads(requirements.user_stories) if requirements.user_stories else None,
            tech_stack=TechStack(
                frontend=requirements.frontend_framework or "react",
                backend=requirements.backend_framework or "python",
                database=requirements.database_type or "postgresql",
                deploy_platform=requirements.deploy_platform or "vercel"
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reconstruct requirements: {str(e)}")

    # 4. Increment generation attempt
    crud.increment_generation_attempt(db, project_id)

    # 5. Update status to in_progress
    crud.update_project_status(db, project_id, "in_progress")

    # 6. Log resume event
    crud.create_generation_log(
        db=db, project_id=project_id,
        step_name="resume", status="started",
        message=f"Resuming generation (attempt #{project.generation_attempt + 1})",
        generation_attempt=project.generation_attempt + 1
    )

    # 7. Start generation in background
    from orchestrator_ui.backend.orchestrator import GenerationOrchestrator, generate_id
    import asyncio

    generation_id = generate_id()
    orchestrator = GenerationOrchestrator()

    asyncio.create_task(
        orchestrator.run_generation(
            generation_id=generation_id,
            request=request,
            db=db,
            user_id=None,  # TODO: Get from auth context if available
            existing_project_id=project_id  # Pass existing project ID for resume mode
        )
    )

    return schemas.GenerationStartResponse(
        generation_id=generation_id,
        message=f"Resuming generation for project {project.name} (attempt #{project.generation_attempt + 1})",
        websocket_url=f"ws://localhost:8000/ws/generation/{generation_id}"
    )
