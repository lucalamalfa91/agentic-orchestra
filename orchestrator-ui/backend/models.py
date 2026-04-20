"""
SQLAlchemy ORM models for Orchestrator UI.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

try:
    from orchestrator_ui.backend.database import Base
except ModuleNotFoundError:
    from database import Base


class SourceType(str, enum.Enum):
    """Enum for knowledge source types."""
    WEB = "web"
    FILE = "file"
    API = "api"


class Project(Base):
    """
    Represents a generated application project.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    github_repo_url = Column(String(500))
    status = Column(String(50), default="completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_attempt = Column(Integer, default=1, nullable=False)

    # Relationships
    user = relationship("User", backref="projects")
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
    generation_attempt = Column(Integer, default=1, nullable=False)

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
    knowledge_sources = relationship("KnowledgeSourceConfig", back_populates="user", cascade="all, delete-orphan")

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
    ai_provider = Column(String(50), nullable=False, server_default="openai")  # "openai" or "anthropic"
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


class KnowledgeSourceConfig(Base):
    """
    Stores user-configured knowledge sources for RAG system.
    Each source (web, file, or API) is indexed into the vector store.
    """
    __tablename__ = "knowledge_source_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    config_json = Column(Text, nullable=False)  # Encrypted JSON configuration
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="knowledge_sources")

    def __repr__(self):
        return f"<KnowledgeSourceConfig(id='{self.id}', user_id={self.user_id}, name='{self.name}', type='{self.source_type.value}')>"


class ProjectArtifacts(Base):
    """
    Persists agent outputs per project/attempt so that Resume can skip
    steps whose output was already generated in a previous run.
    """
    __tablename__ = "project_artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    generation_attempt = Column(Integer, nullable=False, default=1)
    design_yaml   = Column(Text, nullable=True)   # JSON
    api_schema    = Column(Text, nullable=True)   # JSON
    db_schema     = Column(Text, nullable=True)   # JSON
    backend_code  = Column(Text, nullable=True)   # JSON
    frontend_code = Column(Text, nullable=True)   # JSON
    devops_config = Column(Text, nullable=True)   # JSON
    backlog_items = Column(Text, nullable=True)   # JSON
    updated_at    = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", backref="artifacts")

    def __repr__(self):
        return f"<ProjectArtifacts(project_id={self.project_id}, attempt={self.generation_attempt})>"
