"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_serializer


# Tech Stack Configuration
class TechStack(BaseModel):
    """Technology stack configuration for app generation."""
    frontend: str = Field(..., description="Frontend framework (react, vue, angular)")
    backend: str = Field(..., description="Backend framework (dotnet, node, python, none)")
    database: str = Field(..., description="Database type (postgresql, mysql, mongodb, none)")
    deploy_platform: str = Field(..., description="Deployment platform (vercel, railway, render, github-pages, azure-free)")


# Generation Request
class GenerationRequest(BaseModel):
    """Request to start a new app generation."""
    mvp_description: str = Field(..., min_length=10, description="High-level description of the application")
    features: List[str] = Field(..., min_items=1, description="List of features to implement")
    user_stories: Optional[List[str]] = Field(default=None, description="Optional user stories")
    tech_stack: TechStack


# Project Requirement Response
class ProjectRequirementResponse(BaseModel):
    """Project requirements data."""
    id: int
    project_id: int
    mvp_description: str
    features: str  # JSON string
    user_stories: Optional[str] = None  # JSON string
    frontend_framework: Optional[str] = None
    backend_framework: Optional[str] = None
    database_type: Optional[str] = None
    deploy_platform: Optional[str] = None
    requirements_text: str

    class Config:
        from_attributes = True


# Project Response
class ProjectResponse(BaseModel):
    """Project data for API responses."""
    id: int
    name: str
    description: Optional[str] = None
    github_repo_url: Optional[str] = None
    status: str
    created_at: datetime
    generation_attempt: int = 1

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat() if value else None


# Project with Requirements
class ProjectWithRequirements(ProjectResponse):
    """Project data including requirements."""
    requirements: Optional[ProjectRequirementResponse] = None


# Generation Log Response
class GenerationLogResponse(BaseModel):
    """Generation log entry."""
    id: int
    project_id: Optional[int] = None
    step_name: Optional[str] = None
    status: str
    message: Optional[str] = None
    created_at: datetime
    generation_attempt: int = 1

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return value.isoformat() if value else None


# Generation Status
class GenerationStatus(BaseModel):
    """Current status of a generation process."""
    generation_id: str
    project_id: Optional[int] = None
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    current_step: Optional[str] = None
    percentage: int = 0
    message: Optional[str] = None


# Generation Start Response
class GenerationStartResponse(BaseModel):
    """Response when starting a new generation."""
    generation_id: str
    message: str
    websocket_url: str


# WebSocket Progress Message
class ProgressMessage(BaseModel):
    """WebSocket message for progress updates."""
    type: str = "progress"
    step: str
    step_number: int
    percentage: int
    message: str


# Paginated Projects Response
class PaginatedProjects(BaseModel):
    """Paginated list of projects."""
    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# User Response
class UserResponse(BaseModel):
    """User data for API responses."""
    id: int
    github_username: str


# AI Provider Configuration
class AIProviderConfig(BaseModel):
    """AI provider configuration."""
    base_url: str
    api_key_set: bool = True


# Simplified Generation Request (auto-decide mode)
class GenerationRequestSimple(BaseModel):
    """Simplified request for auto-decide mode."""
    mvp_description: str = Field(..., min_length=10, description="High-level description of the application")
    tech_stack: Optional[Dict] = Field(default=None, description="Optional tech stack override")
    auto_decide: bool = Field(default=True, description="Auto-decide features and tech stack")


# ===== Knowledge Sources =====

# Knowledge Source Create Request
class KnowledgeSourceCreate(BaseModel):
    """Request to create a new knowledge source."""
    name: str = Field(..., min_length=1, max_length=255, description="Display name for the source")
    source_type: str = Field(..., description="Type of source: web, file, or api")
    config: Dict = Field(..., description="Configuration dictionary (will be encrypted)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Company Documentation",
                "source_type": "web",
                "config": {
                    "url": "https://docs.example.com",
                    "selectors": ["article", ".content"],
                    "max_depth": 2
                }
            }
        }


# Knowledge Source Response
class KnowledgeSourceResponse(BaseModel):
    """Knowledge source data for API responses."""
    id: str
    user_id: int
    name: str
    source_type: str
    last_indexed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at', 'last_indexed_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return value.isoformat() if value else None


# Indexing Status Response
class IndexingStatusResponse(BaseModel):
    """Response for indexing status check."""
    source_id: str
    status: str  # "idle", "indexing", "completed", "failed"
    last_indexed_at: Optional[datetime] = None
    message: Optional[str] = None

    @field_serializer('last_indexed_at')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format string."""
        return value.isoformat() if value else None
