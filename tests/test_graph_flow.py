"""Integration tests for LangGraph orchestration flow."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langgraph.graph import StateGraph

from AI_agents.graph.graph import create_graph, fan_out_to_parallel_agents, route_after_integration_check
from AI_agents.graph.state import OrchestraState, AgentStatus


@pytest.fixture
def simple_graph():
    """Create a simplified graph for testing (without checkpointer)."""
    return create_graph()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_graph_runs_end_to_end(mock_state):
    """Test that graph runs from START to END with mocked agents."""
    # Create graph without checkpointer for testing
    graph_builder = create_graph()
    app = graph_builder.compile(checkpointer=None)

    # Mock all agent nodes to be no-ops (just update statuses)
    with patch("AI_agents.graph.graph.design_node", new=AsyncMock(side_effect=lambda s: {
        **s,
        "design_yaml": {"app_name": "Test App"},
        "api_schema": {},
        "db_schema": {},
        "agent_statuses": {**s["agent_statuses"], "design": AgentStatus.COMPLETED},
        "completed_steps": s["completed_steps"] + ["design"],
    })):
        with patch("AI_agents.graph.nodes.backend_node.backend_node", new=AsyncMock(side_effect=lambda s: {
            **s,
            "backend_code": {"main.py": "print('test')"},
            "agent_statuses": {**s["agent_statuses"], "backend_agent": AgentStatus.COMPLETED},
            "completed_steps": s["completed_steps"] + ["backend_agent"],
        })):
            with patch("AI_agents.graph.nodes.frontend_node.frontend_node", new=AsyncMock(side_effect=lambda s: {
                **s,
                "frontend_code": {"App.tsx": "export {}"},
                "agent_statuses": {**s["agent_statuses"], "frontend_agent": AgentStatus.COMPLETED},
                "completed_steps": s["completed_steps"] + ["frontend_agent"],
            })):
                with patch("AI_agents.graph.nodes.backlog_node.backlog_node", new=AsyncMock(side_effect=lambda s: {
                    **s,
                    "backlog_items": [{"title": "Task 1"}],
                    "agent_statuses": {**s["agent_statuses"], "backlog_agent": AgentStatus.COMPLETED},
                    "completed_steps": s["completed_steps"] + ["backlog_agent"],
                })):
                    with patch("AI_agents.graph.nodes.devops_node.devops_node", new=AsyncMock(side_effect=lambda s: {
                        **s,
                        "devops_config": {"docker-compose.yml": "version: '3'"},
                        "agent_statuses": {**s["agent_statuses"], "devops_agent": AgentStatus.COMPLETED},
                        "completed_steps": s["completed_steps"] + ["devops_agent"],
                    })):
                        with patch("AI_agents.graph.nodes.publish_node.publish_node", new=AsyncMock(side_effect=lambda s: {
                            **s,
                            "github_repo_url": "https://github.com/test/repo",
                            "agent_statuses": {**s["agent_statuses"], "publish_agent": AgentStatus.COMPLETED},
                            "completed_steps": s["completed_steps"] + ["publish_agent"],
                        })):
                            # Run graph
                            config = {"configurable": {"thread_id": "test-thread-1"}}
                            final_state = None

                            async for event in app.astream(mock_state, config):
                                # Extract final state
                                if "__end__" in event:
                                    final_state = event["__end__"]

                            # Verify all steps completed
                            assert final_state is not None
                            assert "knowledge_retrieval" in final_state["completed_steps"]
                            assert "design" in final_state["completed_steps"]
                            assert "backend_agent" in final_state["completed_steps"]
                            assert "frontend_agent" in final_state["completed_steps"]
                            assert "backlog_agent" in final_state["completed_steps"]
                            assert "integration_check" in final_state["completed_steps"]
                            assert "devops_agent" in final_state["completed_steps"]
                            assert "publish_agent" in final_state["completed_steps"]

                            # Verify no errors
                            assert len(final_state["errors"]) == 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_backend_agent_failure_routes_to_error_handler(mock_state):
    """Test that backend_agent failure triggers error_handler."""
    graph_builder = create_graph()
    app = graph_builder.compile(checkpointer=None)

    # Mock backend_agent to fail
    async def failing_backend_node(state):
        state["errors"]["backend_agent"] = "Code generation failed"
        state["agent_statuses"]["backend_agent"] = AgentStatus.FAILED
        state["completed_steps"].append("backend_agent")
        return state

    with patch("AI_agents.graph.graph.design_node", new=AsyncMock(side_effect=lambda s: {
        **s,
        "design_yaml": {"app_name": "Test"},
        "agent_statuses": {**s["agent_statuses"], "design": AgentStatus.COMPLETED},
        "completed_steps": s["completed_steps"] + ["design"],
    })):
        with patch("AI_agents.graph.nodes.backend_node.backend_node", new=failing_backend_node):
            with patch("AI_agents.graph.nodes.frontend_node.frontend_node", new=AsyncMock(side_effect=lambda s: {
                **s,
                "frontend_code": {},
                "agent_statuses": {**s["agent_statuses"], "frontend_agent": AgentStatus.COMPLETED},
                "completed_steps": s["completed_steps"] + ["frontend_agent"],
            })):
                with patch("AI_agents.graph.nodes.backlog_node.backlog_node", new=AsyncMock(side_effect=lambda s: {
                    **s,
                    "backlog_items": [],
                    "agent_statuses": {**s["agent_statuses"], "backlog_agent": AgentStatus.COMPLETED},
                    "completed_steps": s["completed_steps"] + ["backlog_agent"],
                })):
                    # Run graph
                    config = {"configurable": {"thread_id": "test-thread-2"}}
                    final_state = None

                    async for event in app.astream(mock_state, config):
                        if "__end__" in event:
                            final_state = event["__end__"]

                    # Verify error_handler was invoked
                    assert final_state is not None
                    assert "error_handler" in final_state["completed_steps"]

                    # Verify backend error is recorded
                    assert "backend_agent" in final_state["errors"]
                    assert final_state["errors"]["backend_agent"] == "Code generation failed"

                    # Verify devops and publish were NOT executed
                    assert "devops_agent" not in final_state["completed_steps"]
                    assert "publish_agent" not in final_state["completed_steps"]

                    # Verify final step is FAILED
                    assert final_state["current_step"] == "FAILED"


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
    """Test that data set in design node is accessible in backend and frontend nodes."""
    graph_builder = create_graph()
    app = graph_builder.compile(checkpointer=None)

    design_output = {
        "app_name": "Todo App",
        "stack": {"backend": "Python/FastAPI"},
        "entities": [{"name": "Task"}],
    }

    # Mock design_node to set design_yaml
    async def mock_design_node(state):
        state["design_yaml"] = design_output
        state["api_schema"] = {"endpoints": []}
        state["db_schema"] = {"tables": []}
        state["agent_statuses"]["design"] = AgentStatus.COMPLETED
        state["completed_steps"].append("design")
        return state

    # Track what data backend/frontend receive
    backend_received_data = {}
    frontend_received_data = {}

    async def track_backend_node(state):
        backend_received_data["design_yaml"] = state["design_yaml"]
        state["backend_code"] = {"main.py": "# code"}
        state["agent_statuses"]["backend_agent"] = AgentStatus.COMPLETED
        state["completed_steps"].append("backend_agent")
        return state

    async def track_frontend_node(state):
        frontend_received_data["design_yaml"] = state["design_yaml"]
        state["frontend_code"] = {"App.tsx": "// code"}
        state["agent_statuses"]["frontend_agent"] = AgentStatus.COMPLETED
        state["completed_steps"].append("frontend_agent")
        return state

    with patch("AI_agents.graph.graph.design_node", new=mock_design_node):
        with patch("AI_agents.graph.nodes.backend_node.backend_node", new=track_backend_node):
            with patch("AI_agents.graph.nodes.frontend_node.frontend_node", new=track_frontend_node):
                with patch("AI_agents.graph.nodes.backlog_node.backlog_node", new=AsyncMock(side_effect=lambda s: {
                    **s,
                    "backlog_items": [],
                    "agent_statuses": {**s["agent_statuses"], "backlog_agent": AgentStatus.COMPLETED},
                    "completed_steps": s["completed_steps"] + ["backlog_agent"],
                })):
                    with patch("AI_agents.graph.nodes.devops_node.devops_node", new=AsyncMock(side_effect=lambda s: {
                        **s,
                        "devops_config": {},
                        "agent_statuses": {**s["agent_statuses"], "devops_agent": AgentStatus.COMPLETED},
                        "completed_steps": s["completed_steps"] + ["devops_agent"],
                    })):
                        with patch("AI_agents.graph.nodes.publish_node.publish_node", new=AsyncMock(side_effect=lambda s: {
                            **s,
                            "github_repo_url": "https://github.com/test/repo",
                            "agent_statuses": {**s["agent_statuses"], "publish_agent": AgentStatus.COMPLETED},
                            "completed_steps": s["completed_steps"] + ["publish_agent"],
                        })):
                            state = {
                                "requirements": "Todo app",
                                "user_id": "u1",
                                "project_id": "p1",
                                "features": [],
                                "rag_context": [],
                                "design_yaml": {},
                                "api_schema": {},
                                "db_schema": {},
                                "backend_code": {},
                                "frontend_code": {},
                                "backlog_items": [],
                                "devops_config": {},
                                "github_repo_url": "",
                                "current_step": "START",
                                "completed_steps": [],
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

                            config = {"configurable": {"thread_id": "test-thread-3"}}

                            async for event in app.astream(state, config):
                                pass  # Let graph run to completion

                            # Verify backend received design data
                            assert "design_yaml" in backend_received_data
                            assert backend_received_data["design_yaml"]["app_name"] == "Todo App"

                            # Verify frontend received design data
                            assert "design_yaml" in frontend_received_data
                            assert frontend_received_data["design_yaml"]["app_name"] == "Todo App"


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
