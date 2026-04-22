"""Shared pytest fixtures for agentic-orchestra tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from datetime import datetime
from typing import List, Dict, Any

from AI_agents.graph.state import OrchestraState, AgentStatus
from AI_agents.knowledge.sources.base_source import Document


@pytest.fixture
def mock_state() -> OrchestraState:
    """Minimal valid OrchestraState for testing."""
    return {
        # User inputs
        "requirements": "Build a simple todo app",
        "user_id": "test-user-123",
        "project_id": "test-project-456",
        "ai_provider": "anthropic",
        "features": ["task creation", "task completion"],

        # Agent data
        "rag_context": [],
        "design_yaml": {},
        "api_schema": {},
        "db_schema": {},
        "backend_code": {},
        "frontend_code": {},
        "backlog_items": [],
        "devops_config": {},
        "github_repo_url": "",

        # Supporting data
        "current_step": "START",
        "completed_steps": [],

        # Orchestration
        "agent_statuses": {
            "knowledge_retrieval": AgentStatus.PENDING,
            "design": AgentStatus.PENDING,
            "backend_agent": AgentStatus.PENDING,
            "frontend_agent": AgentStatus.PENDING,
            "backlog_agent": AgentStatus.PENDING,
            "integration_check": AgentStatus.PENDING,
            "error_handler": AgentStatus.PENDING,
            "devops_agent": AgentStatus.PENDING,
            "publish_agent": AgentStatus.PENDING,
        },
        "errors": {},
    }


@pytest.fixture
def mock_vector_store():
    """Mocked VectorStoreService with configurable responses."""
    mock = MagicMock()
    mock.search = AsyncMock(return_value=[])  # Default: empty results
    mock.upsert = AsyncMock(return_value=None)  # No-op
    mock.delete_by_source = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def mock_documents() -> List[Document]:
    """Sample Document objects for testing."""
    return [
        Document(
            content="FastAPI is a modern web framework for Python.",
            metadata={"source": "web", "url": "https://fastapi.tiangolo.com"},
            source_id="source-1",
        ),
        Document(
            content="React is a JavaScript library for building UIs.",
            metadata={"source": "web", "url": "https://react.dev"},
            source_id="source-2",
        ),
        Document(
            content="PostgreSQL is a powerful relational database.",
            metadata={"source": "web", "url": "https://postgresql.org"},
            source_id="source-3",
        ),
    ]


@pytest.fixture
def mock_llm():
    """Mocked LangChain LLM that returns fixed DesignSchema response."""
    mock = MagicMock()

    # Fixed design response matching DesignSchema structure
    fixed_response = {
        "app_name": "Test Todo App",
        "description": "A simple todo application for testing",
        "stack": {
            "backend": "Python/FastAPI",
            "frontend": "React/TypeScript",
            "database": "PostgreSQL",
            "deployment": "Docker",
        },
        "entities": [
            {
                "name": "Task",
                "fields": [
                    {"name": "id", "type": "UUID", "required": True},
                    {"name": "title", "type": "string", "required": True},
                    {"name": "completed", "type": "boolean", "required": True},
                ],
            }
        ],
        "api_endpoints": [
            {
                "method": "GET",
                "path": "/api/tasks",
                "description": "List all tasks",
            },
            {
                "method": "POST",
                "path": "/api/tasks",
                "description": "Create a new task",
            },
        ],
    }

    # Mock the ainvoke method to return the fixed response
    mock.ainvoke = AsyncMock(return_value=fixed_response)

    # Mock with_structured_output to return self
    mock.with_structured_output = MagicMock(return_value=mock)

    return mock


@pytest.fixture
def mock_mcp_client():
    """Mocked MCPClientManager for testing MCP integrations."""
    mock = MagicMock()

    # Mock get_tools to return a list of tool definitions
    mock.get_tools = AsyncMock(return_value=[
        {
            "name": "create_repository",
            "description": "Create a new GitHub repository",
            "parameters": {
                "name": {"type": "string", "required": True},
                "description": {"type": "string", "required": False},
                "private": {"type": "boolean", "required": False},
            },
        },
        {
            "name": "push_files",
            "description": "Push files to a GitHub repository",
            "parameters": {
                "repo_name": {"type": "string", "required": True},
                "files": {"type": "array", "required": True},
            },
        },
    ])

    # Mock call_tool to return success response
    mock.call_tool = AsyncMock(return_value={
        "success": True,
        "data": {"repo_url": "https://github.com/test/test-repo"},
    })

    # Mock start/stop methods
    mock.start = AsyncMock()
    mock.stop = AsyncMock()

    return mock


@pytest.fixture
def mock_knowledge_source():
    """Mocked KnowledgeSource for testing."""
    mock = MagicMock()
    mock.source_id = "test-source-1"
    mock.fetch = AsyncMock(return_value=[
        Document(
            content="Sample content from knowledge source",
            metadata={"source": "test", "test": True},
            source_id="test-source-1",
        )
    ])
    return mock


@pytest.fixture
def sample_design_yaml() -> Dict[str, Any]:
    """Sample design_yaml structure for testing."""
    return {
        "app_name": "Sample App",
        "description": "A sample application",
        "stack": {
            "backend": "Python/FastAPI",
            "frontend": "React/TypeScript",
            "database": "PostgreSQL",
        },
        "entities": [
            {
                "name": "User",
                "fields": [
                    {"name": "id", "type": "UUID", "required": True},
                    {"name": "email", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": True},
                ],
            }
        ],
        "api_endpoints": [
            {
                "method": "GET",
                "path": "/api/users",
                "description": "List users",
            },
            {
                "method": "POST",
                "path": "/api/users",
                "description": "Create user",
            },
        ],
    }


@pytest.fixture
def sample_api_schema() -> List[Dict[str, Any]]:
    """Sample API schema structure for testing."""
    return [
        {
            "method": "GET",
            "path": "/api/users",
            "description": "List users",
            "response": {"type": "array", "items": {"type": "User"}},
        },
        {
            "method": "POST",
            "path": "/api/users",
            "description": "Create user",
            "request": {"type": "User"},
            "response": {"type": "User"},
        },
    ]


@pytest.fixture
def sample_db_schema() -> List[Dict[str, Any]]:
    """Sample database schema for testing."""
    return [
        {
            "table": "users",
            "columns": [
                {"name": "id", "type": "UUID", "primary_key": True},
                {"name": "email", "type": "VARCHAR(255)", "unique": True},
                {"name": "name", "type": "VARCHAR(255)"},
                {"name": "created_at", "type": "TIMESTAMP"},
            ],
        }
    ]
