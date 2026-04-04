"""
Projects API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
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
    total_pages = (total + page_size - 1) // page_size  # Ceiling division

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

    # Get requirements if they exist
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
