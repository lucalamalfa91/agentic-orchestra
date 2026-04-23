"""
LangGraph orchestration graph for Agentic Orchestra.
Replaces run_all_agents.py with declarative graph-based flow.

Graph structure:
START → knowledge_retrieval → design → INTERRUPT (human approval)
  → human_approval_gate
  → [backend, frontend, backlog in parallel]
  → integration_check → conditional(errors? error_handler : devops_agent)
  → publish_agent → END
"""

import logging
import os
from typing import Literal, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from .state import OrchestraState, AgentStatus
from .nodes.design_node import design_node
from .nodes.publish_node import publish_node
from .nodes.backend_node import backend_node
from .nodes.frontend_node import frontend_node
from .nodes.backlog_node import backlog_node
from .nodes.devops_node import devops_node

logger = logging.getLogger(__name__)

# ============================================================================
# Agents that are critical — their failure aborts the pipeline.
# Used by both graph routing AND orchestrator final-state check.
# ============================================================================
CRITICAL_AGENTS = frozenset({"design", "backend_agent", "frontend_agent"})

# Get DATABASE_URL from environment (same as main backend)
try:
    from orchestrator_ui.backend.database import DATABASE_URL
except ModuleNotFoundError:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/orchestrator.db")


# ============================================================================
# Agent nodes
# ============================================================================

async def knowledge_retrieval(state: OrchestraState) -> OrchestraState:
    """Retrieve relevant documentation/examples from knowledge base (RAG)."""
    logger.info("[knowledge_retrieval] running...")
    state["current_step"] = "knowledge_retrieval"
    state["completed_steps"].append("knowledge_retrieval")
    state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.COMPLETED
    logger.info("[knowledge_retrieval] completed (stub)")
    return state


async def human_approval_gate(state: OrchestraState) -> OrchestraState:
    """
    Pass-through node placed after design and before code generation.
    The graph is compiled with interrupt_before=["human_approval_gate"],
    so execution pauses here until the orchestrator resumes it after
    the user approves the design in the frontend.
    """
    logger.info("[human_approval_gate] resumed after human approval")
    state["current_step"] = "human_approval_gate"
    state["completed_steps"].append("human_approval_gate")
    state["agent_statuses"]["human_approval_gate"] = AgentStatus.COMPLETED
    return state


async def integration_check(state: OrchestraState) -> OrchestraState:
    """Verify that backend, frontend, and backlog are consistent."""
    logger.info("[integration_check] running...")
    state["current_step"] = "integration_check"
    state["completed_steps"].append("integration_check")
    state["agent_statuses"]["integration_check"] = AgentStatus.COMPLETED
    logger.info("[integration_check] completed (stub)")
    return state


async def error_handler(state: OrchestraState) -> OrchestraState:
    """Handle errors from any agent - log details and mark as FAILED."""
    logger.error("[error_handler] running - agent failures detected")
    for agent_name, error_msg in state["errors"].items():
        if error_msg:
            logger.error("  - %s: %s", agent_name, error_msg)
    state["current_step"] = "FAILED"
    state["completed_steps"].append("error_handler")
    state["agent_statuses"]["error_handler"] = AgentStatus.COMPLETED
    logger.error("[error_handler] pipeline marked as FAILED")
    return state


# ============================================================================
# Parallel fan-out control
# ============================================================================

def fan_out_to_parallel_agents(state: OrchestraState):
    """
    After human approval, send state to backend, frontend, and backlog
    agents in parallel using LangGraph Send API.
    """
    if state.get("errors", {}).get("design"):
        logger.error("[fan_out] Design agent failed - routing to error_handler")
        return [Send("error_handler", state)]
    logger.info("[fan_out] Routing to parallel code-generation agents")
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
    Route to error_handler only if a critical agent failed.
    Non-critical failures (backlog, publish) are logged but do not block devops.
    """
    critical_errors = {
        agent: msg
        for agent, msg in state["errors"].items()
        if msg and agent in CRITICAL_AGENTS
    }

    if critical_errors:
        logger.warning("Critical agent failures detected, routing to error_handler: %s", list(critical_errors.keys()))
        return "error_handler"

    non_critical = {a: m for a, m in state["errors"].items() if m and a not in CRITICAL_AGENTS}
    if non_critical:
        logger.warning("Non-critical failures (ignored): %s", list(non_critical.keys()))

    logger.info("Critical agents succeeded - routing to devops_agent")
    return "devops_agent"


# ============================================================================
# Graph construction
# ============================================================================

def create_graph() -> StateGraph:
    """Build and return the LangGraph StateGraph for orchestration."""
    graph = StateGraph(OrchestraState)

    graph.add_node("knowledge_retrieval", knowledge_retrieval)
    graph.add_node("design", design_node)
    graph.add_node("human_approval_gate", human_approval_gate)
    graph.add_node("backend_agent", backend_node)
    graph.add_node("frontend_agent", frontend_node)
    graph.add_node("backlog_agent", backlog_node)
    graph.add_node("integration_check", integration_check)
    graph.add_node("error_handler", error_handler)
    graph.add_node("devops_agent", devops_node)
    graph.add_node("publish_agent", publish_node)

    graph.add_edge(START, "knowledge_retrieval")
    graph.add_edge("knowledge_retrieval", "design")
    # Design → human_approval_gate (graph pauses here via interrupt_before)
    graph.add_edge("design", "human_approval_gate")
    # After approval → parallel code generation
    graph.add_conditional_edges(
        "human_approval_gate",
        fan_out_to_parallel_agents,
        ["backend_agent", "frontend_agent", "backlog_agent", "error_handler"]
    )

    graph.add_edge("backend_agent", "integration_check")
    graph.add_edge("frontend_agent", "integration_check")
    graph.add_edge("backlog_agent", "integration_check")

    graph.add_conditional_edges(
        "integration_check",
        route_after_integration_check,
        {"error_handler": "error_handler", "devops_agent": "devops_agent"},
    )

    graph.add_edge("error_handler", END)
    graph.add_edge("devops_agent", "publish_agent")
    graph.add_edge("publish_agent", END)

    return graph


# ============================================================================
# Graph compilation with checkpointer
# ============================================================================

_app: Optional[object] = None
_checkpointer = None


async def get_app():
    """
    Get compiled LangGraph app with checkpointer (lazy initialization).

    Uses PostgreSQL when DATABASE_URL points to postgres, falls back to
    in-memory MemorySaver for SQLite/dev environments.
    """
    global _app, _checkpointer

    if _app is None:
        logger.info("Initializing LangGraph app with checkpointer...")

        if DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres"):
            try:
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                _checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
                await _checkpointer.setup()
                logger.info("PostgreSQL checkpointer initialized")
            except Exception as e:
                logger.warning("PostgreSQL checkpointer failed (%s), falling back to MemorySaver", e)
                from langgraph.checkpoint.memory import MemorySaver
                _checkpointer = MemorySaver()
        else:
            logger.info("Non-postgres DATABASE_URL — using MemorySaver checkpointer")
            from langgraph.checkpoint.memory import MemorySaver
            _checkpointer = MemorySaver()

        graph_builder = create_graph()
        _app = graph_builder.compile(
            checkpointer=_checkpointer,
            interrupt_before=["human_approval_gate"],
        )
        logger.info("LangGraph app compiled with interrupt_before=['human_approval_gate']")

    return _app


# Backward-compatible synchronous proxy (no checkpointer, no interrupt)
class _AppProxy:
    def __getattr__(self, name):
        import asyncio
        graph_builder = create_graph()
        compiled = graph_builder.compile(checkpointer=None)
        return getattr(compiled, name)

app = _AppProxy()

__all__ = ["app", "get_app", "create_graph", "CRITICAL_AGENTS"]
