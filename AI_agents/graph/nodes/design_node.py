"""
Design Agent Node for Agentic Orchestra.

Generates structured application design (architecture, stack, entities, API endpoints)
from user requirements using LLM with structured output.

Input:
    - state["requirements"]: Raw user requirements text
    - state["rag_context"]: Optional list of knowledge documents

Output:
    - state["design_yaml"]: Full design dict
    - state["api_schema"]: Extracted API endpoints list
    - state["db_schema"]: Extracted database schema list

Error Handling:
    - Retries up to 2 times on parse failures
    - Sets state["errors"]["design"] on failure
    - Never raises exceptions (returns state with FAILED status)
"""

import logging
from typing import Optional
from pydantic import BaseModel, Field

from AI_agents.graph.state import OrchestraState, AgentStatus
from AI_agents.utils.llm_client import get_llm_client

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Schemas for Structured Output
# ============================================================================

class StackConfig(BaseModel):
    """Technology stack configuration."""
    backend_framework: str = Field(description="Backend framework (e.g., 'ASP.NET Core', 'FastAPI')")
    frontend_framework: str = Field(description="Frontend framework (e.g., 'React', 'Vue')")
    database: str = Field(description="Database technology (e.g., 'PostgreSQL', 'MongoDB')")
    auth_method: str = Field(description="Authentication method (e.g., 'JWT', 'OAuth2')")


class EntityField(BaseModel):
    """Database entity field definition."""
    name: str = Field(description="Field name")
    type: str = Field(description="Field type (e.g., 'string', 'int', 'datetime')")
    required: bool = Field(default=True, description="Whether field is required")


class Entity(BaseModel):
    """Database entity definition."""
    name: str = Field(description="Entity/table name")
    fields: list[EntityField] = Field(description="List of entity fields")


class APIEndpoint(BaseModel):
    """API endpoint definition."""
    method: str = Field(description="HTTP method (GET, POST, PUT, DELETE)")
    path: str = Field(description="API path (e.g., '/api/users/{id}')")
    description: str = Field(description="Endpoint purpose and behavior")


class DesignSchema(BaseModel):
    """
    Complete application design schema.

    This schema enforces structured output from the LLM, eliminating
    YAML/JSON parsing failures and validation issues.
    """
    app_name: str = Field(description="Application name (kebab-case, no spaces)")
    description: str = Field(description="Brief application description (1-2 sentences)")
    stack: StackConfig = Field(description="Technology stack configuration")
    entities: list[Entity] = Field(description="Database entities/tables")
    api_endpoints: list[APIEndpoint] = Field(description="REST API endpoints")
    deployment_target: str = Field(description="Deployment platform (e.g., 'Railway', 'Azure')")


# ============================================================================
# Design Node Implementation
# ============================================================================

async def design_node(state: OrchestraState) -> OrchestraState:
    """
    Generate application design from user requirements.

    Algorithm:
        1. Build prompt with requirements + RAG context
        2. Call LLM with structured output (Pydantic schema)
        3. Retry up to 2 times on failures
        4. Extract design_yaml, api_schema, db_schema from response
        5. Update orchestration state (current_step, completed_steps, statuses)

    Args:
        state: Current orchestration state

    Returns:
        Updated state with design data or error information
    """
    logger.info("[design_node] Starting design generation")

    # Update orchestration state
    state["current_step"] = "design"
    state["agent_statuses"]["design"] = AgentStatus.RUNNING

    # Extract input data
    requirements = state.get("requirements", "")
    rag_context = state.get("rag_context") or []

    if not requirements:
        logger.error("[design_node] No requirements provided")
        state["errors"]["design"] = "No requirements provided in state"
        state["agent_statuses"]["design"] = AgentStatus.FAILED
        return state

    # Build RAG context section
    rag_section = ""
    if rag_context:
        logger.info(f"[design_node] Including {len(rag_context)} RAG documents")
        rag_docs = "\n\n".join(
            f"## Relevant Context\n{doc.get('content', '')}"
            for doc in rag_context
        )
        rag_section = f"\n\n{rag_docs}"

    # Build prompt
    prompt = f"""You are an expert software architect specializing in .NET, React, and Azure.

Analyze the following requirements and produce a detailed application design.

Requirements:
{requirements}
{rag_section}

Generate a complete design covering:
1. Application name (kebab-case, no spaces)
2. Brief description
3. Technology stack (backend, frontend, database, auth)
4. Database entities with fields
5. API endpoints with HTTP methods and paths
6. Deployment target

Be specific and realistic. Use best practices for the chosen stack.
"""

    # Get LLM client
    provider = state.get("ai_provider", "anthropic")

    try:
        llm = get_llm_client(provider, {"temperature": 0.1, "max_tokens": 4000})
    except Exception as e:
        logger.error(f"[design_node] Failed to create LLM client: {e}")
        state["errors"]["design"] = f"LLM client error: {str(e)}"
        state["agent_statuses"]["design"] = AgentStatus.FAILED
        return state

    # Create structured output chain
    structured_llm = llm.with_structured_output(DesignSchema)

    # Retry loop (up to 2 retries = 3 total attempts)
    MAX_RETRIES = 2
    last_error = None

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            logger.info(f"[design_node] Attempt {attempt}/{MAX_RETRIES + 1}")

            # Call LLM with structured output
            design: DesignSchema = await structured_llm.ainvoke(prompt)

            # Convert Pydantic model to dict
            design_dict = design.model_dump()

            logger.info(f"[design_node] Design generated: {design_dict.get('app_name')}")

            # Populate state with design data
            state["design_yaml"] = design_dict

            # Extract API schema
            state["api_schema"] = [
                {
                    "method": ep.method,
                    "path": ep.path,
                    "description": ep.description
                }
                for ep in design.api_endpoints
            ]

            # Extract DB schema
            state["db_schema"] = [
                {
                    "table": entity.name,
                    "fields": [
                        {
                            "name": field.name,
                            "type": field.type,
                            "required": field.required
                        }
                        for field in entity.fields
                    ]
                }
                for entity in design.entities
            ]

            # Mark success
            state["completed_steps"].append("design")
            state["agent_statuses"]["design"] = AgentStatus.COMPLETED

            logger.info("[design_node] Design generation completed successfully")
            return state

        except Exception as e:
            last_error = e
            logger.warning(f"[design_node] Attempt {attempt} failed: {str(e)}")

            # Add error feedback to prompt for retry
            if attempt <= MAX_RETRIES:
                prompt += f"\n\nPrevious attempt failed with error: {str(e)}\nPlease try again with valid data."
            else:
                # Max retries exceeded
                logger.error(f"[design_node] All {MAX_RETRIES + 1} attempts failed")
                state["errors"]["design"] = f"Failed after {MAX_RETRIES + 1} attempts: {str(last_error)}"
                state["agent_statuses"]["design"] = AgentStatus.FAILED
                return state

    # Should never reach here, but satisfy type checker
    state["errors"]["design"] = f"Unexpected error: {str(last_error)}"
    state["agent_statuses"]["design"] = AgentStatus.FAILED
    return state
