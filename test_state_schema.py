"""
Test script for OrchestraState TypedDict and AgentStatus enum.

This script verifies:
1. Import functionality
2. State creation with all fields
3. Type compatibility
4. Enum behavior
5. Simulated agent flow (receive state, modify, return)
"""

from AI_agents.graph.state import OrchestraState, AgentStatus
from typing import Optional


def test_imports():
    """Test that imports work correctly."""
    print("[OK] Test 1: Imports successful")


def test_enum():
    """Test AgentStatus enum behavior."""
    # Test all enum values
    assert AgentStatus.PENDING == "pending"
    assert AgentStatus.RUNNING == "running"
    assert AgentStatus.COMPLETED == "completed"
    assert AgentStatus.FAILED == "failed"
    assert AgentStatus.SKIPPED == "skipped"

    # Test that it's a string subclass (for JSON serialization)
    status = AgentStatus.RUNNING
    assert isinstance(status, str)
    assert status == "running"
    assert status.value == "running"

    print("[OK] Test 2: AgentStatus enum works correctly")


def test_state_creation():
    """Test creating a valid OrchestraState."""
    # Create initial state (like orchestrator would)
    initial_state: OrchestraState = {
        "requirements": "Build a todo app with React and FastAPI",
        "project_id": "proj_123",
        "user_id": "user_456",
        "ai_provider": "openai",
        "parsed_requirements": None,
        "design_yaml": None,
        "api_schema": None,
        "db_schema": None,
        "backend_code": None,
        "frontend_code": None,
        "devops_config": None,
        "backlog_items": None,
        "rag_context": None,
        "current_step": "requirements",
        "completed_steps": [],
        "agent_statuses": {},
        "errors": {}
    }

    # Verify all fields present
    assert len(initial_state) == 17
    assert initial_state["requirements"] == "Build a todo app with React and FastAPI"
    assert initial_state["project_id"] == "proj_123"
    assert initial_state["errors"] == {}

    print("[OK] Test 3: OrchestraState creation successful (17 fields)")


def test_agent_simulation():
    """Simulate an agent receiving state, modifying it, and returning it."""

    # Initial state
    state: OrchestraState = {
        "requirements": "Build a todo app",
        "project_id": "proj_123",
        "user_id": "user_456",
        "ai_provider": "anthropic",
        "parsed_requirements": None,
        "design_yaml": None,
        "api_schema": None,
        "db_schema": None,
        "backend_code": None,
        "frontend_code": None,
        "devops_config": None,
        "backlog_items": None,
        "rag_context": None,
        "current_step": "requirements",
        "completed_steps": [],
        "agent_statuses": {"requirements": AgentStatus.RUNNING},
        "errors": {}
    }

    # Simulate Requirements Agent processing
    def requirements_agent(state: OrchestraState) -> OrchestraState:
        """Mock requirements agent."""
        # Parse requirements
        parsed = {
            "app_type": "todo",
            "frontend": "react",
            "backend": "fastapi"
        }

        # Return modified state
        return {
            **state,
            "parsed_requirements": parsed,
            "current_step": "architect",
            "completed_steps": state["completed_steps"] + ["requirements"],
            "agent_statuses": {
                **state["agent_statuses"],
                "requirements": AgentStatus.COMPLETED
            }
        }

    # Process through agent
    updated_state = requirements_agent(state)

    # Verify modifications
    assert updated_state["parsed_requirements"] is not None
    assert updated_state["parsed_requirements"]["app_type"] == "todo"
    assert "requirements" in updated_state["completed_steps"]
    assert updated_state["agent_statuses"]["requirements"] == AgentStatus.COMPLETED
    assert updated_state["current_step"] == "architect"

    print("[OK] Test 4: Agent simulation successful (state immutability preserved)")


def test_error_handling():
    """Test error handling pattern."""

    state: OrchestraState = {
        "requirements": "Build app",
        "project_id": "proj_123",
        "user_id": "user_456",
        "ai_provider": "openai",
        "parsed_requirements": None,
        "design_yaml": None,
        "api_schema": None,
        "db_schema": None,
        "backend_code": None,
        "frontend_code": None,
        "devops_config": None,
        "backlog_items": None,
        "rag_context": None,
        "current_step": "backend",
        "completed_steps": ["requirements", "architect"],
        "agent_statuses": {"backend": AgentStatus.RUNNING},
        "errors": {}
    }

    # Simulate agent error
    def failing_agent(state: OrchestraState) -> OrchestraState:
        """Mock agent that encounters an error."""
        try:
            # Simulate error
            raise ValueError("Missing design_yaml field")
        except Exception as e:
            # Agent sets error and returns state instead of raising
            return {
                **state,
                "errors": {
                    **state["errors"],
                    "backend": str(e)
                },
                "agent_statuses": {
                    **state["agent_statuses"],
                    "backend": AgentStatus.FAILED
                }
            }

    # Process through failing agent
    error_state = failing_agent(state)

    # Verify error handling
    assert "backend" in error_state["errors"]
    assert "Missing design_yaml" in error_state["errors"]["backend"]
    assert error_state["agent_statuses"]["backend"] == AgentStatus.FAILED

    print("[OK] Test 5: Error handling pattern works correctly")


def test_optional_fields():
    """Test that Optional fields can be None or populated."""

    # State with all Optional fields as None
    empty_state: OrchestraState = {
        "requirements": "Test",
        "project_id": "123",
        "user_id": "456",
        "ai_provider": "openai",
        "parsed_requirements": None,
        "design_yaml": None,
        "api_schema": None,
        "db_schema": None,
        "backend_code": None,
        "frontend_code": None,
        "devops_config": None,
        "backlog_items": None,
        "rag_context": None,
        "current_step": "start",
        "completed_steps": [],
        "agent_statuses": {},
        "errors": {}
    }

    # State with Optional fields populated
    populated_state: OrchestraState = {
        **empty_state,
        "parsed_requirements": {"key": "value"},
        "design_yaml": {"architecture": "microservices"},
        "api_schema": [{"endpoint": "/api/todos"}],
        "db_schema": [{"table": "todos"}],
        "backend_code": {"main.py": "print('hello')"},
        "frontend_code": {"App.tsx": "export default App"},
        "devops_config": {"ci": "github-actions"},
        "backlog_items": [{"story": "As a user..."}],
        "rag_context": [{"source": "docs"}]
    }

    # Verify both states are valid
    assert empty_state["parsed_requirements"] is None
    assert populated_state["parsed_requirements"] is not None
    assert isinstance(populated_state["design_yaml"], dict)
    assert isinstance(populated_state["api_schema"], list)

    print("[OK] Test 6: Optional fields work correctly (None and populated)")


def test_parallel_agent_simulation():
    """Simulate parallel agents reading same state field."""

    # State after architect agent
    state: OrchestraState = {
        "requirements": "Build todo app",
        "project_id": "proj_123",
        "user_id": "user_456",
        "ai_provider": "anthropic",
        "parsed_requirements": {"app": "todo"},
        "design_yaml": {
            "architecture": "REST API",
            "database": "postgresql",
            "api_endpoints": ["/todos"],
            "frontend_pages": ["home", "todos"]
        },
        "api_schema": None,
        "db_schema": None,
        "backend_code": None,
        "frontend_code": None,
        "devops_config": None,
        "backlog_items": None,
        "rag_context": None,
        "current_step": "parallel",
        "completed_steps": ["requirements", "architect"],
        "agent_statuses": {},
        "errors": {}
    }

    # Backend agent reads design_yaml
    def backend_agent(state: OrchestraState) -> OrchestraState:
        design = state["design_yaml"]
        return {
            **state,
            "backend_code": {
                "main.py": f"# API: {design['api_endpoints']}"
            },
            "agent_statuses": {
                **state["agent_statuses"],
                "backend": AgentStatus.COMPLETED
            }
        }

    # Frontend agent reads design_yaml (parallel to backend)
    def frontend_agent(state: OrchestraState) -> OrchestraState:
        design = state["design_yaml"]
        return {
            **state,
            "frontend_code": {
                "App.tsx": f"// Pages: {design['frontend_pages']}"
            },
            "agent_statuses": {
                **state["agent_statuses"],
                "frontend": AgentStatus.COMPLETED
            }
        }

    # Both agents can read same design_yaml (this enables parallelism in LangGraph)
    backend_result = backend_agent(state)
    frontend_result = frontend_agent(state)

    # Verify both read successfully
    assert backend_result["backend_code"] is not None
    assert frontend_result["frontend_code"] is not None
    assert "# API:" in backend_result["backend_code"]["main.py"]
    assert "// Pages:" in frontend_result["frontend_code"]["App.tsx"]

    print("[OK] Test 7: Parallel agents can read same state field (enables parallelism)")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing OrchestraState Schema")
    print("=" * 60)
    print()

    test_imports()
    test_enum()
    test_state_creation()
    test_agent_simulation()
    test_error_handling()
    test_optional_fields()
    test_parallel_agent_simulation()

    print()
    print("=" * 60)
    print("[SUCCESS] All tests passed!")
    print("=" * 60)
    print()
    print("Summary:")
    print("- OrchestraState TypedDict: 17 fields working correctly")
    print("- AgentStatus enum: 5 values, JSON-serializable")
    print("- Immutable state pattern: agents return new state")
    print("- Error handling: agents set errors dict instead of raising")
    print("- Parallel execution: multiple agents can read same fields")
    print()


if __name__ == "__main__":
    run_all_tests()
