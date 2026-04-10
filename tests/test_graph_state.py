"""Tests for OrchestraState and AgentStatus."""

import pytest
from AI_agents.graph.state import OrchestraState, AgentStatus


@pytest.mark.unit
def test_orchestrastate_instantiation(mock_state):
    """Test that OrchestraState can be instantiated with required fields."""
    # Verify all required fields are present
    assert mock_state["requirements"] == "Build a simple todo app"
    assert mock_state["user_id"] == "test-user-123"
    assert mock_state["project_id"] == "test-project-456"
    assert isinstance(mock_state["features"], list)

    # Verify agent data fields
    assert isinstance(mock_state["rag_context"], list)
    assert isinstance(mock_state["design_yaml"], dict)
    assert isinstance(mock_state["api_schema"], dict)
    assert isinstance(mock_state["db_schema"], dict)
    assert isinstance(mock_state["backend_code"], dict)
    assert isinstance(mock_state["frontend_code"], dict)
    assert isinstance(mock_state["backlog_items"], list)
    assert isinstance(mock_state["devops_config"], dict)
    assert isinstance(mock_state["github_repo_url"], str)

    # Verify orchestration fields
    assert mock_state["current_step"] == "START"
    assert isinstance(mock_state["completed_steps"], list)
    assert isinstance(mock_state["agent_statuses"], dict)
    assert isinstance(mock_state["errors"], dict)


@pytest.mark.unit
def test_agent_status_transitions():
    """Test that all AgentStatus enum values are valid."""
    # Verify all expected status values exist
    assert AgentStatus.PENDING == "pending"
    assert AgentStatus.RUNNING == "running"
    assert AgentStatus.COMPLETED == "completed"
    assert AgentStatus.FAILED == "failed"
    assert AgentStatus.SKIPPED == "skipped"

    # Verify they are string subclass (JSON serializable)
    assert isinstance(AgentStatus.PENDING, str)
    assert isinstance(AgentStatus.RUNNING, str)
    assert isinstance(AgentStatus.COMPLETED, str)
    assert isinstance(AgentStatus.FAILED, str)
    assert isinstance(AgentStatus.SKIPPED, str)

    # Test typical status progression
    statuses = [
        AgentStatus.PENDING,
        AgentStatus.RUNNING,
        AgentStatus.COMPLETED,
    ]
    assert all(isinstance(s, str) for s in statuses)


@pytest.mark.unit
def test_errors_dict_update(mock_state):
    """Test that errors field can be set per agent key."""
    # Initially empty
    assert len(mock_state["errors"]) == 0

    # Add error for design agent
    mock_state["errors"]["design"] = "Design validation failed"
    assert mock_state["errors"]["design"] == "Design validation failed"

    # Add error for backend agent
    mock_state["errors"]["backend_agent"] = "Code generation timeout"
    assert mock_state["errors"]["backend_agent"] == "Code generation timeout"

    # Verify both errors are present
    assert len(mock_state["errors"]) == 2
    assert "design" in mock_state["errors"]
    assert "backend_agent" in mock_state["errors"]

    # Verify other agents have no errors
    assert "frontend_agent" not in mock_state["errors"]
    assert "publish_agent" not in mock_state["errors"]


@pytest.mark.unit
def test_completed_steps_append(mock_state):
    """Test that completed_steps can be extended."""
    # Initially empty
    assert len(mock_state["completed_steps"]) == 0

    # Add steps sequentially
    mock_state["completed_steps"].append("knowledge_retrieval")
    assert mock_state["completed_steps"] == ["knowledge_retrieval"]

    mock_state["completed_steps"].append("design")
    assert mock_state["completed_steps"] == ["knowledge_retrieval", "design"]

    mock_state["completed_steps"].append("backend_agent")
    assert len(mock_state["completed_steps"]) == 3

    # Verify order is preserved
    assert mock_state["completed_steps"][0] == "knowledge_retrieval"
    assert mock_state["completed_steps"][1] == "design"
    assert mock_state["completed_steps"][2] == "backend_agent"


@pytest.mark.unit
def test_agent_statuses_update(mock_state):
    """Test that agent_statuses can be updated."""
    # All agents start as PENDING
    assert mock_state["agent_statuses"]["design"] == AgentStatus.PENDING

    # Update to RUNNING
    mock_state["agent_statuses"]["design"] = AgentStatus.RUNNING
    assert mock_state["agent_statuses"]["design"] == AgentStatus.RUNNING

    # Update to COMPLETED
    mock_state["agent_statuses"]["design"] = AgentStatus.COMPLETED
    assert mock_state["agent_statuses"]["design"] == AgentStatus.COMPLETED

    # Test FAILED status
    mock_state["agent_statuses"]["backend_agent"] = AgentStatus.FAILED
    assert mock_state["agent_statuses"]["backend_agent"] == AgentStatus.FAILED

    # Test SKIPPED status
    mock_state["agent_statuses"]["publish_agent"] = AgentStatus.SKIPPED
    assert mock_state["agent_statuses"]["publish_agent"] == AgentStatus.SKIPPED


@pytest.mark.unit
def test_current_step_update(mock_state):
    """Test that current_step can be updated."""
    assert mock_state["current_step"] == "START"

    mock_state["current_step"] = "knowledge_retrieval"
    assert mock_state["current_step"] == "knowledge_retrieval"

    mock_state["current_step"] = "design"
    assert mock_state["current_step"] == "design"

    mock_state["current_step"] = "END"
    assert mock_state["current_step"] == "END"


@pytest.mark.unit
def test_state_with_all_fields_populated():
    """Test state with all fields fully populated."""
    state: OrchestraState = {
        "requirements": "Full featured app",
        "user_id": "user-001",
        "project_id": "project-001",
        "features": ["auth", "dashboard", "api"],
        "rag_context": [
            {"content": "Context 1", "metadata": {}, "source_id": "s1"}
        ],
        "design_yaml": {"app_name": "Test App"},
        "api_schema": {"endpoints": []},
        "db_schema": {"tables": []},
        "backend_code": {"main.py": "print('hello')"},
        "frontend_code": {"App.tsx": "export {}"},
        "backlog_items": [{"title": "Task 1", "body": "Description"}],
        "devops_config": {"docker-compose.yml": "version: '3'"},
        "github_repo_url": "https://github.com/test/repo",
        "current_step": "devops_agent",
        "completed_steps": ["knowledge_retrieval", "design", "backend_agent"],
        "agent_statuses": {
            "knowledge_retrieval": AgentStatus.COMPLETED,
            "design": AgentStatus.COMPLETED,
            "backend_agent": AgentStatus.COMPLETED,
            "frontend_agent": AgentStatus.RUNNING,
            "backlog_agent": AgentStatus.PENDING,
            "integration_check": AgentStatus.PENDING,
            "error_handler": AgentStatus.SKIPPED,
            "devops_agent": AgentStatus.PENDING,
            "publish_agent": AgentStatus.PENDING,
        },
        "errors": {"frontend_agent": "Temporary error"},
    }

    # Verify all fields are accessible and correct type
    assert state["requirements"] == "Full featured app"
    assert len(state["rag_context"]) == 1
    assert state["design_yaml"]["app_name"] == "Test App"
    assert "main.py" in state["backend_code"]
    assert state["github_repo_url"].startswith("https://")
    assert len(state["completed_steps"]) == 3
    assert state["agent_statuses"]["frontend_agent"] == AgentStatus.RUNNING
    assert "frontend_agent" in state["errors"]
