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
    project_id: str

    # Producer: Orchestrator → Consumer: Configuration lookup
    user_id: str

    # Producer: Orchestrator → Consumer: LLM client factory
    ai_provider: str  # "openai" | "anthropic"

    # ===== AGENT-PRODUCED DATA =====

    # Producer: Requirements Agent → Consumer: Architect Agent
    parsed_requirements: Optional[dict]

    # Producer: Architect Agent → Consumer: Backend, Frontend, DevOps Agents
    design_yaml: Optional[dict]

    # Producer: Architect Agent (extracts from design_yaml) → Consumer: Backend Agent
    api_schema: Optional[list]

    # Producer: Architect Agent (extracts from design_yaml) → Consumer: Backend Agent
    db_schema: Optional[list]

    # Producer: Backend Agent → Consumer: Publish Agent
    # Dict structure: {file_path: code_content}
    backend_code: Optional[dict]

    # Producer: Frontend Agent → Consumer: Publish Agent
    # Dict structure: {file_path: code_content}
    frontend_code: Optional[dict]

    # Producer: DevOps Agent → Consumer: Publish Agent
    # Dict structure: {workflow_name: workflow_yaml}
    devops_config: Optional[dict]

    # ===== SUPPORTING SYSTEMS =====

    # Producer: Backlog Agent → Consumer: Project Manager, Requirements Agent
    # List of user stories/tasks
    # Annotated with operator.add to merge lists from parallel agents
    backlog_items: Optional[Annotated[list, operator.add]]

    # Producer: Knowledge Agent (RAG) → Consumer: All agents
    # List of knowledge fragments injected into agent prompts
    # Annotated with operator.add to merge RAG docs from parallel agents
    rag_context: Optional[Annotated[list, operator.add]]

    # ===== ORCHESTRATION STATE =====

    # Producer: Orchestrator → Consumer: WebSocket handler
    # Name of currently executing agent
    current_step: str

    # Producer: Orchestrator → Consumer: Orchestrator (tracks progress)
    # List of successfully completed agent names
    completed_steps: list[str]

    # Producer: Orchestrator → Consumer: WebSocket handler
    # Dict mapping agent_name → AgentStatus value
    agent_statuses: dict[str, str]

    # Producer: Any agent (on error) → Consumer: Orchestrator
    # Dict mapping agent_name → error message string
    # Agents set errors[agent_name] and return state instead of raising
    errors: dict[str, str]
