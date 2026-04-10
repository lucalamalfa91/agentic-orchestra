"""
LangGraph orchestration graph for Agentic Orchestra.
Replaces run_all_agents.py with declarative graph-based flow.

Graph structure:
START → knowledge_retrieval → design → INTERRUPT (human approval)
  → [backend, frontend, backlog in parallel]
  → integration_check → conditional(errors? error_handler : devops_agent)
  → publish_agent → END
"""

import logging
import os
from typing import Literal, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from .state import OrchestraState, AgentStatus
from .nodes.design_node import design_node
from .nodes.publish_node import publish_node
from .nodes.backend_node import backend_node
from .nodes.frontend_node import frontend_node
from .nodes.backlog_node import backlog_node
from .nodes.devops_node import devops_node

logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment (same as main backend)
try:
    from orchestrator_ui.backend.database import DATABASE_URL
except ModuleNotFoundError:
    # Fallback for standalone execution
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/orchestrator.db")


# ============================================================================
# Agent nodes
# ============================================================================
# Real implementations:
#   - design_node (Prompt 07a + 07c): Uses Deep Agents with planning
#   - publish_node (Prompt 07c): Uses Deep Agents with filesystem + GitHub tools
#   - backend_node (Prompt 07d): Uses BaseAgent for backend generation (language-agnostic)
#   - frontend_node (Prompt 07d): Uses BaseAgent for frontend generation (framework-agnostic)
#   - backlog_node (Prompt 07d): Uses BaseAgent for product backlog generation
#   - devops_node (Prompt 07e): Uses BaseAgent for CI/CD and Docker configuration
# Stubs remaining:
#   - knowledge_retrieval, integration_check

async def knowledge_retrieval(state: OrchestraState) -> OrchestraState:
    """Retrieve relevant documentation/examples from knowledge base (RAG)."""
    logger.info("[knowledge_retrieval] running...")

    state["current_step"] = "knowledge_retrieval"
    state["completed_steps"].append("knowledge_retrieval")
    state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.COMPLETED

    # Stub: in Prompt 04 this will populate state["retrieved_docs"]
    logger.info("[knowledge_retrieval] completed (stub)")
    return state


# backend_agent, frontend_agent, backlog_agent now use real implementations
# Defined in AI_agents/graph/nodes/ (Prompt 07d)


async def integration_check(state: OrchestraState) -> OrchestraState:
    """Verify that backend, frontend, and backlog are consistent."""
    logger.info("[integration_check] running...")

    state["current_step"] = "integration_check"
    state["completed_steps"].append("integration_check")
    state["agent_statuses"]["integration_check"] = AgentStatus.COMPLETED

    # Stub: in Prompt 07 this will validate consistency across artifacts
    logger.info("[integration_check] completed (stub)")
    return state


async def error_handler(state: OrchestraState) -> OrchestraState:
    """Handle errors from any agent - log details and mark as FAILED."""
    logger.error("[error_handler] running - agent failures detected")

    # Log all errors from state["errors"]
    for agent_name, error_msg in state["errors"].items():
        if error_msg:
            logger.error(f"  - {agent_name}: {error_msg}")

    state["current_step"] = "FAILED"
    state["completed_steps"].append("error_handler")
    state["agent_statuses"]["error_handler"] = AgentStatus.COMPLETED

    logger.error("[error_handler] pipeline marked as FAILED")
    return state


# devops_agent now uses real implementation from devops_node (Prompt 07e)
# Defined in AI_agents/graph/nodes/devops_node.py

# publish_agent now uses real implementation from publish_node (Prompt 07c)
# Defined in AI_agents/graph/nodes/publish_node.py


# ============================================================================
# Parallel fan-out control
# ============================================================================

def fan_out_to_parallel_agents(state: OrchestraState):
    """
    After design completes, send state to backend, frontend, and backlog
    agents in parallel using LangGraph Send API.
    """
    return [
        Send("backend_agent", state),
        Send("frontend_agent", state),
        Send("backlog_agent", state),
    ]


# ============================================================================
# Conditional routing
# ============================================================================

def route_after_integration_check(
    state: OrchestraState,
) -> Literal["error_handler", "devops_agent"]:
    """
    Route to error_handler if any agent failed, otherwise continue to devops.
    """
    # Check if any error is non-empty
    has_errors = any(error_msg for error_msg in state["errors"].values())

    if has_errors:
        logger.warning("Errors detected - routing to error_handler")
        return "error_handler"
    else:
        logger.info("All agents succeeded - routing to devops_agent")
        return "devops_agent"


# ============================================================================
# Graph construction
# ============================================================================

def create_graph() -> StateGraph:
    """
    Build and return the LangGraph StateGraph for orchestration.

    Graph flow:
      START → knowledge_retrieval → design
        → [backend_agent, frontend_agent, backlog_agent] (parallel)
        → integration_check
        → conditional:
            - if errors → error_handler → END
            - else → devops_agent → publish_agent → END
    """
    graph = StateGraph(OrchestraState)

    # Add all nodes
    graph.add_node("knowledge_retrieval", knowledge_retrieval)
    graph.add_node("design", design_node)
    graph.add_node("backend_agent", backend_node)
    graph.add_node("frontend_agent", frontend_node)
    graph.add_node("backlog_agent", backlog_node)
    graph.add_node("integration_check", integration_check)
    graph.add_node("error_handler", error_handler)
    graph.add_node("devops_agent", devops_node)
    graph.add_node("publish_agent", publish_node)

    # Sequential: START → knowledge_retrieval → design
    graph.add_edge(START, "knowledge_retrieval")
    graph.add_edge("knowledge_retrieval", "design")

    # Parallel fan-out: design → [backend, frontend, backlog]
    graph.add_conditional_edges(
        "design",
        fan_out_to_parallel_agents,
        ["backend_agent", "frontend_agent", "backlog_agent"]
    )

    # Fan-in: all 3 agents → integration_check
    graph.add_edge("backend_agent", "integration_check")
    graph.add_edge("frontend_agent", "integration_check")
    graph.add_edge("backlog_agent", "integration_check")

    # Conditional routing after integration_check
    graph.add_conditional_edges(
        "integration_check",
        route_after_integration_check,
        {
            "error_handler": "error_handler",
            "devops_agent": "devops_agent",
        }
    )

    # Final steps
    graph.add_edge("error_handler", END)
    graph.add_edge("devops_agent", "publish_agent")
    graph.add_edge("publish_agent", END)

    return graph


# ============================================================================
# Graph compilation with checkpointer (Prompt 08)
# ============================================================================

# Lazy compilation - checkpointer initialized on first use
_app: Optional[StateGraph] = None
_checkpointer: Optional[AsyncPostgresSaver] = None


async def get_app():
    """
    Get compiled LangGraph app with PostgreSQL checkpointer.

    Initializes checkpointer on first call (lazy initialization).
    The checkpointer enables:
    - State persistence across sessions
    - Human-in-the-loop approval after design phase
    - Resume from checkpoints after interrupts

    Returns:
        Compiled LangGraph application
    """
    global _app, _checkpointer

    if _app is None:
        logger.info("Initializing LangGraph app with PostgreSQL checkpointer...")

        # Create checkpointer from DATABASE_URL
        _checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)

        # Setup checkpoint tables in database
        await _checkpointer.setup()
        logger.info("PostgreSQL checkpointer initialized successfully")

        # Build and compile graph
        graph_builder = create_graph()
        _app = graph_builder.compile(
            checkpointer=_checkpointer,
            interrupt_before=["backend_agent"]  # Pause after design for human approval
        )
        logger.info("LangGraph app compiled with interrupt_before=['backend_agent']")

    return _app


# For backward compatibility (synchronous access)
# WARNING: This will fail if checkpointer is not initialized
# Use get_app() instead for proper async initialization
graph_builder = create_graph()
app = graph_builder.compile(checkpointer=None)  # Legacy sync version


# ============================================================================
# Exports
# ============================================================================

__all__ = ["app", "get_app", "create_graph"]
