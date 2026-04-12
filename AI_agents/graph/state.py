"""
LangGraph State Schema for Agentic Orchestra.

This module defines the central state contract (OrchestraState TypedDict) that
flows through all agent nodes in the LangGraph pipeline.

Design Principles:
- TypedDict for maximum LangGraph compatibility
- Optional[] for fields not present at all pipeline stages
- Each field documents producer → consumer relationships
- No runtime validation (agents validate their own inputs)
- Immutable data flow (agents return new state, don't mutate)
"""

from typing import TypedDict, Optional, Annotated
import operator
from enum import Enum


class AgentStatus(str, Enum):
    """
    Status values for agent execution tracking.

    Using str subclass for easy JSON serialization and database storage.
    """
    PENDING = "pending"       # Not yet started
    RUNNING = "running"       # Currently executing
    COMPLETED = "completed"   # Finished successfully
    FAILED = "failed"         # Encountered error
    SKIPPED = "skipped"       # Intentionally skipped (e.g., user opted out)


class OrchestraState(TypedDict):
    """
    Central state schema for LangGraph-based agent orchestration.

    This TypedDict flows through all agent nodes, enabling:
    - Parallel agent execution (multiple agents can read same fields)
    - Structured error handling (failed agents set errors dict)
    - Progress tracking (current_step, agent_statuses)
    - Knowledge injection (RAG context, MCP data)
    - Human-in-the-loop (LangGraph checkpoints can pause/inspect state)

    Field Naming Convention:
    - Singular for atomic values (requirements, current_step)
    - Plural for collections (completed_steps, errors)
    - Suffix "_code" for code outputs (backend_code, frontend_code)
    - Suffix "_config" for configuration (devops_config)
    - Suffix "_schema" for data models (api_schema, db_schema)

    All Optional[] fields can be None at early pipeline stages.
    Non-optional fields (requirements, project_id, etc.) must be set
    by the orchestrator before graph execution begins.
    """

    # ===== USER INPUT & METADATA =====

    # Producer: User input → Consumer: Requirements Agent
    # Annotated to handle parallel agents returning full state dict
    requirements: Annotated[str, lambda x, y: x or y]

    # Producer: Orchestrator → Consumer: All agents (for logging)
    # Annotated to handle parallel agents (backend/frontend/backlog) returning full state
    project_id: Annotated[str, lambda x, y: x or y]

    # Producer: Orchestrator → Consumer: Configuration lookup
    # Annotated to handle parallel agents returning full state
    user_id: Annotated[str, lambda x, y: x or y]

    # Producer: Orchestrator → Consumer: LLM client factory
    # Annotated to handle parallel agents returning full state
    ai_provider: Annotated[str, lambda x, y: x or y]  # "openai" | "anthropic"

    # ===== AGENT-PRODUCED DATA =====

    # Producer: Requirements Agent → Consumer: Architect Agent
    # Annotated to handle parallel agents returning full state
    parsed_requirements: Annotated[dict | None, lambda x, y: x or y]

    # Producer: Architect Agent → Consumer: Backend, Frontend, DevOps Agents
    # Annotated to handle parallel agents returning full state
    design_yaml: Annotated[dict | None, lambda x, y: x or y]

    # Producer: Architect Agent (extracts from design_yaml) → Consumer: Backend Agent
    # Annotated to handle parallel agents returning full state
    api_schema: Annotated[list | None, lambda x, y: x or y]

    # Producer: Architect Agent (extracts from design_yaml) → Consumer: Backend Agent
    # Annotated to handle parallel agents returning full state
    db_schema: Annotated[list | None, lambda x, y: x or y]

    # Producer: Backend Agent → Consumer: Publish Agent
    # Dict structure: {file_path: code_content}
    # Annotated to handle parallel agents returning full state
    backend_code: Annotated[dict | None, lambda x, y: x or y]

    # Producer: Frontend Agent → Consumer: Publish Agent
    # Dict structure: {file_path: code_content}
    # Annotated to handle parallel agents returning full state
    frontend_code: Annotated[dict | None, lambda x, y: x or y]

    # Producer: DevOps Agent → Consumer: Publish Agent
    # Dict structure: {workflow_name: workflow_yaml}
    # Annotated to handle parallel agents returning full state
    devops_config: Annotated[dict | None, lambda x, y: x or y]

    # ===== SUPPORTING SYSTEMS =====

    # Producer: Backlog Agent → Consumer: Project Manager, Requirements Agent
    # List of user stories/tasks
    # Annotated to merge lists from parallel agents (handles None)
    backlog_items: Annotated[list | None, lambda x, y: (x or []) + (y or [])]

    # Producer: Knowledge Agent (RAG) → Consumer: All agents
    # List of knowledge fragments injected into agent prompts
    # Annotated to merge RAG docs from parallel agents (handles None)
    rag_context: Annotated[list | None, lambda x, y: (x or []) + (y or [])]

    # ===== ORCHESTRATION STATE =====

    # Producer: Orchestrator → Consumer: WebSocket handler
    # Name of currently executing agent
    # Annotated to handle parallel agents returning full state
    current_step: Annotated[str, lambda x, y: x or y]

    # Producer: Orchestrator → Consumer: Orchestrator (tracks progress)
    # List of successfully completed agent names
    # Annotated to merge lists from parallel agents (handles None/empty)
    completed_steps: Annotated[list[str], lambda x, y: (x or []) + (y or [])]

    # Producer: Orchestrator → Consumer: WebSocket handler
    # Dict mapping agent_name → AgentStatus value
    # Annotated to merge dicts from parallel agents (handles None)
    agent_statuses: Annotated[dict[str, str], lambda x, y: {**(x or {}), **(y or {})}]

    # Producer: Any agent (on error) → Consumer: Orchestrator
    # Dict mapping agent_name → error message string
    # Agents set errors[agent_name] and return state instead of raising
    # Annotated to merge error dicts from parallel agents (handles None)
    errors: Annotated[dict[str, str], lambda x, y: {**(x or {}), **(y or {})}]
