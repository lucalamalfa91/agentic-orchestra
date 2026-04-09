"""
LangGraph orchestration graph for Agentic Orchestra.
Replaces run_all_agents.py with declarative graph-based flow.

Graph structure:
START → knowledge_retrieval → design → [backend, frontend, backlog in parallel]
  → integration_check → conditional(errors? error_handler : devops_agent)
  → publish_agent → END
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from .state import OrchestraState, AgentStatus

logger = logging.getLogger(__name__)


# ============================================================================
# Agent nodes (stubs for now - real implementation in Prompt 07)
# ============================================================================

async def knowledge_retrieval(state: OrchestraState) -> OrchestraState:
    """Retrieve relevant documentation/examples from knowledge base (RAG)."""
    logger.info("[knowledge_retrieval] running...")

    state["current_step"] = "knowledge_retrieval"
    state["completed_steps"].append("knowledge_retrieval")
    state["agent_statuses"]["knowledge_retrieval"] = AgentStatus.COMPLETED

    # Stub: in Prompt 04 this will populate state["retrieved_docs"]
    logger.info("[knowledge_retrieval] completed (stub)")
    return state


async def design(state: OrchestraState) -> OrchestraState:
    """Generate architecture design (YAML) from user requirements."""
    logger.info("[design] running...")

    state["current_step"] = "design"
    state["completed_steps"].append("design")
    state["agent_statuses"]["design"] = AgentStatus.COMPLETED

    # Stub: in Prompt 07 this will populate state["design_yaml"]
    logger.info("[design] completed (stub)")
    return state


async def backend_agent(state: OrchestraState) -> OrchestraState:
    """Generate backend code (C# + ASP.NET Core) from design."""
    logger.info("[backend_agent] running...")

    state["current_step"] = "backend_agent"
    state["completed_steps"].append("backend_agent")
    state["agent_statuses"]["backend_agent"] = AgentStatus.COMPLETED

    # Stub: in Prompt 07 this will populate state["backend_code"]
    logger.info("[backend_agent] completed (stub)")
    return state


async def frontend_agent(state: OrchestraState) -> OrchestraState:
    """Generate frontend code (React + TypeScript) from design."""
    logger.info("[frontend_agent] running...")

    state["current_step"] = "frontend_agent"
    state["completed_steps"].append("frontend_agent")
    state["agent_statuses"]["frontend_agent"] = AgentStatus.COMPLETED

    # Stub: in Prompt 07 this will populate state["frontend_code"]
    logger.info("[frontend_agent] completed (stub)")
    return state


async def backlog_agent(state: OrchestraState) -> OrchestraState:
    """Generate product backlog (user stories, issues) from requirements."""
    logger.info("[backlog_agent] running...")

    state["current_step"] = "backlog_agent"
    state["completed_steps"].append("backlog_agent")
    state["agent_statuses"]["backlog_agent"] = AgentStatus.COMPLETED

    # Stub: in Prompt 07 this will populate state["github_issues"]
    logger.info("[backlog_agent] completed (stub)")
    return state


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


async def devops_agent(state: OrchestraState) -> OrchestraState:
    """Generate CI/CD pipeline (GitHub Actions) and Docker config."""
    logger.info("[devops_agent] running...")

    state["current_step"] = "devops_agent"
    state["completed_steps"].append("devops_agent")
    state["agent_statuses"]["devops_agent"] = AgentStatus.COMPLETED

    # Stub: in Prompt 07 this will populate state["ci_cd_config"]
    logger.info("[devops_agent] completed (stub)")
    return state


async def publish_agent(state: OrchestraState) -> OrchestraState:
    """Publish generated app to GitHub repository."""
    logger.info("[publish_agent] running...")

    state["current_step"] = "publish_agent"
    state["completed_steps"].append("publish_agent")
    state["agent_statuses"]["publish_agent"] = AgentStatus.COMPLETED

    # Stub: in Prompt 07 this will commit + push to state["github_repo_url"]
    logger.info("[publish_agent] completed (stub)")
    return state


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
    graph.add_node("design", design)
    graph.add_node("backend_agent", backend_agent)
    graph.add_node("frontend_agent", frontend_agent)
    graph.add_node("backlog_agent", backlog_agent)
    graph.add_node("integration_check", integration_check)
    graph.add_node("error_handler", error_handler)
    graph.add_node("devops_agent", devops_agent)
    graph.add_node("publish_agent", publish_agent)

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


# Compile the graph (checkpointer will be added in Prompt 08)
graph_builder = create_graph()
app = graph_builder.compile(checkpointer=None)


# ============================================================================
# Exports
# ============================================================================

__all__ = ["app", "create_graph"]
