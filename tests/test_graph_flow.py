"""Integration tests for LangGraph orchestration flow."""

import pytest
from contextlib import AsyncExitStack, ExitStack
from unittest.mock import AsyncMock, MagicMock, patch
from langgraph.graph import StateGraph

from AI_agents.graph.graph import create_graph, fan_out_to_parallel_agents, route_after_integration_check
from AI_agents.graph.state import OrchestraState, AgentStatus

# Patch targets: all node names as bound in graph.py's namespace.
# graph.add_node() captures the name from graph.py scope, so patches
# must target "AI_agents.graph.graph.<node_name>" and be active BEFORE
# create_graph() is called so the mock is registered in the graph.
_DESIGN_TARGET    = "AI_agents.graph.graph.design_node"
_BACKEND_TARGET   = "AI_agents.graph.graph.backend_node"
_FRONTEND_TARGET  = "AI_agents.graph.graph.frontend_node"
_BACKLOG_TARGET   = "AI_agents.graph.graph.backlog_node"
_DEVOPS_TARGET    = "AI_agents.graph.graph.devops_node"
_PUBLISH_TARGET   = "AI_agents.graph.graph.publish_node"


@pytest.fixture
def simple_graph():
    """Create a simplified graph for testing (without checkpointer)."""
    return create_graph()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_graph_runs_end_to_end(mock_state):
    """Test that graph runs from START to END with mocked agents."""
    mocks = {
        _DESIGN_TARGET:   AsyncMock(side_effect=lambda s: {**s, "design_yaml": {"app_name": "Test App"}, "api_schema": {}, "db_schema": {}, "agent_statuses": {**s["agent_statuses"], "design": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["design"]}),
        _BACKEND_TARGET:  AsyncMock(side_effect=lambda s: {**s, "backend_code": {"main.py": "print('test')"}, "agent_statuses": {**s["agent_statuses"], "backend_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["backend_agent"]}),
        _FRONTEND_TARGET: AsyncMock(side_effect=lambda s: {**s, "frontend_code": {"App.tsx": "export {}"}, "agent_statuses": {**s["agent_statuses"], "frontend_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["frontend_agent"]}),
        _BACKLOG_TARGET:  AsyncMock(side_effect=lambda s: {**s, "backlog_items": [{"title": "Task 1"}], "agent_statuses": {**s["agent_statuses"], "backlog_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["backlog_agent"]}),
        _DEVOPS_TARGET:   AsyncMock(side_effect=lambda s: {**s, "devops_config": {"docker-compose.yml": "version: '3'"}, "agent_statuses": {**s["agent_statuses"], "devops_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["devops_agent"]}),
        _PUBLISH_TARGET:  AsyncMock(side_effect=lambda s: {**s, "github_repo_url": "https://github.com/test/repo", "agent_statuses": {**s["agent_statuses"], "publish_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["publish_agent"]}),
    }

    # Patches must be active BEFORE create_graph() so graph.add_node() captures the mocks
    with ExitStack() as stack:
        for target, mock_fn in mocks.items():
            stack.enter_context(patch(target, new=mock_fn))

        app = create_graph().compile(checkpointer=None)
        config = {"configurable": {"thread_id": "test-e2e"}}
        # ainvoke returns the final accumulated state directly
        final_state = await app.ainvoke(mock_state, config)

    assert final_state is not None
    completed = final_state.get("completed_steps", [])
    assert "knowledge_retrieval" in completed
    assert "design" in completed
    assert "backend_agent" in completed
    assert "frontend_agent" in completed
    assert "backlog_agent" in completed
    assert "integration_check" in completed
    assert "devops_agent" in completed
    assert "publish_agent" in completed
    assert not any(v for v in final_state.get("errors", {}).values())


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backend_agent_failure_routes_to_error_handler(mock_state):
    """Test that backend_agent (critical) failure routes to error_handler, skipping devops/publish."""
    async def failing_backend(state):
        state["errors"]["backend_agent"] = "Code generation failed"
        state["agent_statuses"]["backend_agent"] = AgentStatus.FAILED
        state["completed_steps"].append("backend_agent")
        return state

    mocks = {
        _DESIGN_TARGET:   AsyncMock(side_effect=lambda s: {**s, "design_yaml": {"app_name": "Test"}, "agent_statuses": {**s["agent_statuses"], "design": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["design"]}),
        _BACKEND_TARGET:  failing_backend,
        _FRONTEND_TARGET: AsyncMock(side_effect=lambda s: {**s, "frontend_code": {}, "agent_statuses": {**s["agent_statuses"], "frontend_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["frontend_agent"]}),
        _BACKLOG_TARGET:  AsyncMock(side_effect=lambda s: {**s, "backlog_items": [], "agent_statuses": {**s["agent_statuses"], "backlog_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["backlog_agent"]}),
    }

    with ExitStack() as stack:
        for target, mock_fn in mocks.items():
            stack.enter_context(patch(target, new=mock_fn))

        app = create_graph().compile(checkpointer=None)
        config = {"configurable": {"thread_id": "test-backend-fail"}}
        final_state = await app.ainvoke(mock_state, config)

    assert final_state is not None
    completed = final_state.get("completed_steps", [])
    assert "error_handler" in completed
    assert "backend_agent" in final_state.get("errors", {})
    assert final_state["errors"]["backend_agent"] == "Code generation failed"
    assert "devops_agent" not in completed
    assert "publish_agent" not in completed


@pytest.mark.asyncio
@pytest.mark.integration
async def test_non_critical_failure_does_not_block_devops(mock_state):
    """Test that backlog_agent (non-critical) failure still allows devops+publish to run."""
    async def failing_backlog(state):
        state["errors"]["backlog_agent"] = "Backlog generation failed"
        state["agent_statuses"]["backlog_agent"] = AgentStatus.FAILED
        state["completed_steps"].append("backlog_agent")
        return state

    mocks = {
        _DESIGN_TARGET:   AsyncMock(side_effect=lambda s: {**s, "design_yaml": {"app_name": "Test"}, "api_schema": {}, "db_schema": {}, "agent_statuses": {**s["agent_statuses"], "design": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["design"]}),
        _BACKEND_TARGET:  AsyncMock(side_effect=lambda s: {**s, "backend_code": {"main.py": ""}, "agent_statuses": {**s["agent_statuses"], "backend_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["backend_agent"]}),
        _FRONTEND_TARGET: AsyncMock(side_effect=lambda s: {**s, "frontend_code": {"App.tsx": ""}, "agent_statuses": {**s["agent_statuses"], "frontend_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["frontend_agent"]}),
        _BACKLOG_TARGET:  failing_backlog,
        _DEVOPS_TARGET:   AsyncMock(side_effect=lambda s: {**s, "devops_config": {}, "agent_statuses": {**s["agent_statuses"], "devops_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["devops_agent"]}),
        _PUBLISH_TARGET:  AsyncMock(side_effect=lambda s: {**s, "github_repo_url": "https://github.com/test/repo", "agent_statuses": {**s["agent_statuses"], "publish_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["publish_agent"]}),
    }

    with ExitStack() as stack:
        for target, mock_fn in mocks.items():
            stack.enter_context(patch(target, new=mock_fn))

        app = create_graph().compile(checkpointer=None)
        config = {"configurable": {"thread_id": "test-backlog-fail"}}
        final_state = await app.ainvoke(mock_state, config)

    assert final_state is not None
    completed = final_state.get("completed_steps", [])
    assert "devops_agent" in completed
    assert "publish_agent" in completed
    assert "error_handler" not in completed
    assert final_state.get("errors", {}).get("backlog_agent") == "Backlog generation failed"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_parallel_nodes_all_update_state():
    """Test that backend, frontend, and backlog nodes all update state correctly."""
    # Create minimal state
    state = {
        "requirements": "Test app",
        "user_id": "u1",
        "project_id": "p1",
        "features": [],
        "rag_context": [],
        "design_yaml": {"app_name": "Test"},
        "api_schema": {},
        "db_schema": {},
        "backend_code": {},
        "frontend_code": {},
        "backlog_items": [],
        "devops_config": {},
        "github_repo_url": "",
        "current_step": "design",
        "completed_steps": ["knowledge_retrieval", "design"],
        "agent_statuses": {
            "knowledge_retrieval": AgentStatus.COMPLETED,
            "design": AgentStatus.COMPLETED,
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

    # Test fan-out function
    sends = fan_out_to_parallel_agents(state)

    # Verify Send API creates 3 parallel sends
    assert len(sends) == 3

    # Verify all three agents are targeted
    agent_names = [send.node for send in sends]
    assert "backend_agent" in agent_names
    assert "frontend_agent" in agent_names
    assert "backlog_agent" in agent_names

    # Verify all sends have the same state
    for send in sends:
        assert send.arg["requirements"] == "Test app"
        assert send.arg["design_yaml"]["app_name"] == "Test"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_state_preserved_across_nodes():
    """Test that design output is passed correctly to backend and frontend nodes."""
    design_output = {"app_name": "Todo App", "stack": {"backend": "Python/FastAPI"}, "entities": [{"name": "Task"}]}
    backend_received: dict = {}
    frontend_received: dict = {}

    async def mock_design(state):
        state["design_yaml"] = design_output
        state["api_schema"] = {"endpoints": []}
        state["db_schema"] = {"tables": []}
        state["agent_statuses"]["design"] = AgentStatus.COMPLETED
        state["completed_steps"].append("design")
        return state

    async def track_backend(state):
        backend_received["design_yaml"] = state["design_yaml"]
        state["backend_code"] = {"main.py": "# code"}
        state["agent_statuses"]["backend_agent"] = AgentStatus.COMPLETED
        state["completed_steps"].append("backend_agent")
        return state

    async def track_frontend(state):
        frontend_received["design_yaml"] = state["design_yaml"]
        state["frontend_code"] = {"App.tsx": "// code"}
        state["agent_statuses"]["frontend_agent"] = AgentStatus.COMPLETED
        state["completed_steps"].append("frontend_agent")
        return state

    init_state = {
        "requirements": "Todo app", "user_id": "u1", "project_id": "p1", "ai_provider": "anthropic",
        "features": [], "rag_context": [], "design_yaml": {}, "api_schema": {}, "db_schema": {},
        "backend_code": {}, "frontend_code": {}, "backlog_items": [], "devops_config": {},
        "github_repo_url": "", "current_step": "START", "completed_steps": [], "errors": {},
        "agent_statuses": {a: AgentStatus.PENDING for a in ["knowledge_retrieval", "design", "backend_agent", "frontend_agent", "backlog_agent", "integration_check", "error_handler", "devops_agent", "publish_agent"]},
    }

    mocks = {
        _DESIGN_TARGET:   mock_design,
        _BACKEND_TARGET:  track_backend,
        _FRONTEND_TARGET: track_frontend,
        _BACKLOG_TARGET:  AsyncMock(side_effect=lambda s: {**s, "backlog_items": [], "agent_statuses": {**s["agent_statuses"], "backlog_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["backlog_agent"]}),
        _DEVOPS_TARGET:   AsyncMock(side_effect=lambda s: {**s, "devops_config": {}, "agent_statuses": {**s["agent_statuses"], "devops_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["devops_agent"]}),
        _PUBLISH_TARGET:  AsyncMock(side_effect=lambda s: {**s, "github_repo_url": "https://github.com/test/repo", "agent_statuses": {**s["agent_statuses"], "publish_agent": AgentStatus.COMPLETED}, "completed_steps": s["completed_steps"] + ["publish_agent"]}),
    }

    with ExitStack() as stack:
        for target, mock_fn in mocks.items():
            stack.enter_context(patch(target, new=mock_fn))

        app = create_graph().compile(checkpointer=None)
        config = {"configurable": {"thread_id": "test-state-preserved"}}

        async for _ in app.astream(init_state, config):
            pass

    assert "design_yaml" in backend_received
    assert backend_received["design_yaml"]["app_name"] == "Todo App"
    assert "design_yaml" in frontend_received
    assert frontend_received["design_yaml"]["app_name"] == "Todo App"


@pytest.mark.unit
def test_route_after_integration_check_with_no_errors(mock_state):
    """Test routing logic when no errors exist."""
    # State with no errors
    mock_state["errors"] = {}

    result = route_after_integration_check(mock_state)

    assert result == "devops_agent"


@pytest.mark.unit
def test_route_after_integration_check_with_errors(mock_state):
    """Test routing logic when errors exist."""
    # State with errors
    mock_state["errors"] = {
        "backend_agent": "Code generation failed",
    }

    result = route_after_integration_check(mock_state)

    assert result == "error_handler"


@pytest.mark.unit
def test_fan_out_creates_correct_sends(mock_state):
    """Test that fan_out_to_parallel_agents creates correct Send objects."""
    sends = fan_out_to_parallel_agents(mock_state)

    # Should create 3 Send objects
    assert len(sends) == 3

    # Extract node names
    node_names = {send.node for send in sends}

    # Verify all three agents are targeted
    assert node_names == {"backend_agent", "frontend_agent", "backlog_agent"}

    # Verify each Send has the state
    for send in sends:
        assert send.arg == mock_state
