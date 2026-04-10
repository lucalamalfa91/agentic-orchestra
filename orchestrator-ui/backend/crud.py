"""
CRUD operations for database access.
"""
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime

try:
    from orchestrator_ui.backend import models, schemas
except ModuleNotFoundError:
    import models
    import schemas


def create_project(
    db: Session,
    name: str,
    description: Optional[str] = None,
    github_repo_url: Optional[str] = None,
    status: str = "pending"
) -> models.Project:
    """Create a new project."""
    project = models.Project(
        name=name,
        description=description,
        github_repo_url=github_repo_url,
        status=status
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_project_by_id(db: Session, project_id: int) -> Optional[models.Project]:
    """Get project by ID."""
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_projects(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[models.Project]:
    """Get all projects with pagination."""
    return db.query(models.Project).order_by(models.Project.created_at.desc()).offset(skip).limit(limit).all()


def get_projects_count(db: Session) -> int:
    """Get total count of projects."""
    return db.query(models.Project).count()


def update_project_status(
    db: Session,
    project_id: int,
    status: str,
    github_repo_url: Optional[str] = None
) -> Optional[models.Project]:
    """Update project status and optionally GitHub URL."""
    project = get_project_by_id(db, project_id)
    if project:
        project.status = status
        if github_repo_url:
            project.github_repo_url = github_repo_url
        db.commit()
        db.refresh(project)
    return project


def create_project_requirement(
    db: Session,
    project_id: int,
    mvp_description: str,
    features: List[str],
    user_stories: Optional[List[str]],
    tech_stack: schemas.TechStack,
    requirements_text: str
) -> models.ProjectRequirement:
    """Create project requirements."""
    requirement = models.ProjectRequirement(
        project_id=project_id,
        mvp_description=mvp_description,
        features=json.dumps(features),
        user_stories=json.dumps(user_stories) if user_stories else None,
        frontend_framework=tech_stack.frontend,
        backend_framework=tech_stack.backend,
        database_type=tech_stack.database,
        deploy_platform=tech_stack.deploy_platform,
        requirements_text=requirements_text
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement


def get_project_requirements(db: Session, project_id: int) -> Optional[models.ProjectRequirement]:
    """Get requirements for a project."""
    return db.query(models.ProjectRequirement).filter(
        models.ProjectRequirement.project_id == project_id
    ).first()


def delete_project(db: Session, project_id: int) -> bool:
    """Delete a project."""
    project = get_project_by_id(db, project_id)
    if project:
        db.delete(project)
        db.commit()
        return True
    return False


def delete_project_requirements(db: Session, project_id: int) -> None:
    """Delete all requirements for a project."""
    db.query(models.ProjectRequirement).filter(
        models.ProjectRequirement.project_id == project_id
    ).delete()
    db.commit()


def delete_project_logs(db: Session, project_id: int) -> None:
    """Delete all logs for a project."""
    db.query(models.GenerationLog).filter(
        models.GenerationLog.project_id == project_id
    ).delete()
    db.commit()


def create_generation_log(
    db: Session,
    project_id: Optional[int],
    step_name: str,
    status: str,
    message: Optional[str] = None,
    generation_attempt: int = 1
) -> models.GenerationLog:
    """Create a generation log entry."""
    log = models.GenerationLog(
        project_id=project_id,
        step_name=step_name,
        status=status,
        message=message,
        generation_attempt=generation_attempt
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def increment_generation_attempt(db: Session, project_id: int) -> Optional[models.Project]:
    """
    Increment generation attempt counter for a project.
    Called when resuming a failed generation.
    """
    project = get_project_by_id(db, project_id)
    if project:
        project.generation_attempt += 1
        db.commit()
        db.refresh(project)
    return project


def get_project_logs(db: Session, project_id: int) -> List[models.GenerationLog]:
    """Get all logs for a project."""
    return db.query(models.GenerationLog).filter(
        models.GenerationLog.project_id == project_id
    ).order_by(models.GenerationLog.created_at.asc()).all()


def save_project_metadata(
    app_name: str,
    github_repo_url: str,
    requirements_path: Path,
    design_yaml_path: Path
) -> None:
    """
    Save project metadata to database after successful GitHub repo creation.
    Called from publish_agent.py.
    """
    try:
        from orchestrator_ui.backend.database import SessionLocal
    except ModuleNotFoundError:
        from database import SessionLocal

    db = SessionLocal()
    try:
        # Read requirements file
        requirements_text = ""
        if requirements_path.exists():
            requirements_text = requirements_path.read_text()

        # Parse description from requirements (first non-comment line)
        description = ""
        for line in requirements_text.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                description = line
                break

        # Create project
        project = create_project(
            db=db,
            name=app_name,
            description=description,
            github_repo_url=github_repo_url,
            status="completed"
        )

        # Create log entry
        create_generation_log(
            db=db,
            project_id=project.id,
            step_name="publish",
            status="completed",
            message=f"Successfully published to GitHub: {github_repo_url}"
        )

        print(f"[OK] Saved project metadata to database: {app_name} (ID: {project.id})")

    except Exception as e:
        print(f"[WARN] Warning: Failed to save project metadata to database: {e}")
    finally:
        db.close()


def get_or_create_user(github_id: str, github_username: str, github_token: str):
    """Get existing user or create new one."""
    try:
        from orchestrator_ui.backend.database import SessionLocal
    except ModuleNotFoundError:
        from database import SessionLocal

    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.github_id == github_id).first()
        if not user:
            user = models.User(
                github_id=github_id,
                github_username=github_username,
                github_token=github_token
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


def get_user_config(user_id: int):
    """Get user configuration."""
    try:
        from orchestrator_ui.backend.database import SessionLocal
    except ModuleNotFoundError:
        from database import SessionLocal

    db = SessionLocal()
    try:
        return db.query(models.Configuration).filter(
            models.Configuration.user_id == user_id
        ).first()
    finally:
        db.close()


def save_user_config(user_id: int, base_url: str, api_key_encrypted: str):
    """Save or update user configuration."""
    try:
        from orchestrator_ui.backend.database import SessionLocal
    except ModuleNotFoundError:
        from database import SessionLocal

    db = SessionLocal()
    try:
        config = db.query(models.Configuration).filter(
            models.Configuration.user_id == user_id
        ).first()

        if not config:
            config = models.Configuration(
                user_id=user_id,
                ai_base_url=base_url,
                ai_api_key_encrypted=api_key_encrypted
            )
        else:
            config.ai_base_url = base_url
            config.ai_api_key_encrypted = api_key_encrypted

        db.add(config)
        db.commit()
        db.refresh(config)
        return config
    finally:
        db.close()


def get_deploy_auth(user_id: int, provider: str):
    """Get deployment provider authentication."""
    try:
        from orchestrator_ui.backend.database import SessionLocal
    except ModuleNotFoundError:
        from database import SessionLocal

    db = SessionLocal()
    try:
        return db.query(models.DeployProviderAuth).filter(
            models.DeployProviderAuth.user_id == user_id,
            models.DeployProviderAuth.provider_name == provider
        ).first()
    finally:
        db.close()


def save_deploy_auth(user_id: int, provider: str, access_token: str, refresh_token: str = None):
    """Save or update deployment provider authentication."""
    try:
        from orchestrator_ui.backend.database import SessionLocal
    except ModuleNotFoundError:
        from database import SessionLocal

    db = SessionLocal()
    try:
        auth = db.query(models.DeployProviderAuth).filter(
            models.DeployProviderAuth.user_id == user_id,
            models.DeployProviderAuth.provider_name == provider
        ).first()

        if not auth:
            auth = models.DeployProviderAuth(
                user_id=user_id,
                provider_name=provider,
                access_token=access_token
            )
        else:
            auth.access_token = access_token

        if refresh_token:
            auth.refresh_token = refresh_token

        db.add(auth)
        db.commit()
        db.refresh(auth)
        return auth
    finally:
        db.close()


# ===== Knowledge Source CRUD =====

def create_knowledge_source(
    db: Session,
    user_id: int,
    name: str,
    source_type: str,
    config_json_encrypted: str
) -> models.KnowledgeSourceConfig:
    """
    Create a new knowledge source configuration.

    Args:
        db: Database session
        user_id: User ID who owns this source
        name: Display name for the source
        source_type: Type of source ("web", "file", "api")
        config_json_encrypted: Encrypted JSON configuration string

    Returns:
        Created KnowledgeSourceConfig instance
    """
    source = models.KnowledgeSourceConfig(
        user_id=user_id,
        name=name,
        source_type=source_type,
        config_json=config_json_encrypted,
        last_indexed_at=None
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_knowledge_sources(db: Session, user_id: int) -> List[models.KnowledgeSourceConfig]:
    """
    Get all knowledge sources for a user.

    Args:
        db: Database session
        user_id: User ID to filter by

    Returns:
        List of KnowledgeSourceConfig instances
    """
    return db.query(models.KnowledgeSourceConfig).filter(
        models.KnowledgeSourceConfig.user_id == user_id
    ).order_by(models.KnowledgeSourceConfig.created_at.desc()).all()


def get_knowledge_source(
    db: Session,
    source_id: str,
    user_id: int
) -> Optional[models.KnowledgeSourceConfig]:
    """
    Get a specific knowledge source by ID, ensuring it belongs to the user.

    Args:
        db: Database session
        source_id: Source ID (UUID string)
        user_id: User ID to verify ownership

    Returns:
        KnowledgeSourceConfig instance or None if not found
    """
    return db.query(models.KnowledgeSourceConfig).filter(
        models.KnowledgeSourceConfig.id == source_id,
        models.KnowledgeSourceConfig.user_id == user_id
    ).first()


def delete_knowledge_source(db: Session, source_id: str, user_id: int) -> bool:
    """
    Delete a knowledge source, ensuring it belongs to the user.

    Args:
        db: Database session
        source_id: Source ID (UUID string)
        user_id: User ID to verify ownership

    Returns:
        True if deleted, False if not found
    """
    source = get_knowledge_source(db, source_id, user_id)
    if source:
        db.delete(source)
        db.commit()
        return True
    return False


def update_last_indexed(db: Session, source_id: str, timestamp: datetime) -> Optional[models.KnowledgeSourceConfig]:
    """
    Update the last_indexed_at timestamp for a knowledge source.

    Args:
        db: Database session
        source_id: Source ID (UUID string)
        timestamp: Datetime to set as last_indexed_at

    Returns:
        Updated KnowledgeSourceConfig instance or None if not found
    """
    source = db.query(models.KnowledgeSourceConfig).filter(
        models.KnowledgeSourceConfig.id == source_id
    ).first()

    if source:
        source.last_indexed_at = timestamp
        db.commit()
        db.refresh(source)

    return source
