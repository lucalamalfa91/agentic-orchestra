"""
SQLAlchemy ORM models for Orchestrator UI.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from orchestrator_ui.backend.database import Base
except ModuleNotFoundError:
    from database import Base


class Project(Base):
    """
    Represents a generated application project.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    github_repo_url = Column(String(500))
    status = Column(String(50), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    requirements = relationship("ProjectRequirement", back_populates="project", cascade="all, delete-orphan")
    logs = relationship("GenerationLog", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class ProjectRequirement(Base):
    """
    Stores original requirements for each project to enable regeneration.
    """
    __tablename__ = "project_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    mvp_description = Column(Text, nullable=False)
    features = Column(Text, nullable=False)  # JSON string of features list
    user_stories = Column(Text)  # JSON string of user stories list (optional)
    frontend_framework = Column(String(50))
    backend_framework = Column(String(50))
    database_type = Column(String(50))
    deploy_platform = Column(String(50))
    requirements_text = Column(Text, nullable=False)  # Full original requirements.txt content

    # Relationships
    project = relationship("Project", back_populates="requirements")

    def __repr__(self):
        return f"<ProjectRequirement(id={self.id}, project_id={self.project_id})>"


class GenerationLog(Base):
    """
    Execution logs for debugging and audit trail.
    """
    __tablename__ = "generation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    step_name = Column(String(100))
    status = Column(String(50))  # 'started', 'in_progress', 'completed', 'failed'
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    project = relationship("Project", back_populates="logs")

    def __repr__(self):
        return f"<GenerationLog(id={self.id}, step='{self.step_name}', status='{self.status}')>"


class User(Base):
    """
    Represents authenticated users with GitHub OAuth.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(String(255), unique=True, nullable=False)
    github_username = Column(String(255), nullable=False)
    github_token = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    configurations = relationship("Configuration", back_populates="user", cascade="all, delete-orphan")
    deploy_providers = relationship("DeployProviderAuth", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, github_username='{self.github_username}')>"


class Configuration(Base):
    """
    Stores AI provider configuration for each user.
    """
    __tablename__ = "configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ai_base_url = Column(String(500), nullable=False)
    ai_api_key_encrypted = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="configurations")

    def __repr__(self):
        return f"<Configuration(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


class DeployProviderAuth(Base):
    """
    Stores deployment provider authentication tokens.
    """
    __tablename__ = "deploy_provider_auth"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider_name = Column(String(50), nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="deploy_providers")

    def __repr__(self):
        return f"<DeployProviderAuth(id={self.id}, user_id={self.user_id}, provider='{self.provider_name}')>"
