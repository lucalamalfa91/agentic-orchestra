"""
Design Agent Node for Agentic Orchestra (Deep Agents Integration).

Generates structured application design (architecture, stack, entities, API endpoints)
from user requirements using Deep Agents framework with built-in planning.

This node uses Deep Agents (Prompt 07c) because the design process benefits from
multi-step planning: parse requirements → analyze context → produce YAML structure →
validate completeness. The enable_todos flag forces the agent to plan before executing.

Input:
    - state["requirements"]: Raw user requirements text
    - state["rag_context"]: Optional list of knowledge documents

Output:
    - state["design_yaml"]: Full design dict
    - state["api_schema"]: Extracted API endpoints list
    - state["db_schema"]: Extracted database schema list

Error Handling:
    - Sets state["errors"]["design"] on failure
    - Never raises exceptions (returns state with FAILED status)
"""

import logging
import json
import re
from deepagents import create_deep_agent
from AI_agents.utils.llm_client import get_llm_client
from AI_agents.graph.state import OrchestraState, AgentStatus

logger = logging.getLogger(__name__)


async def design_node(state: OrchestraState) -> OrchestraState:
    """
    Generate application design from user requirements using Deep Agents.

    Algorithm:
        1. Initialize Deep Agent with planning enabled (enable_todos=True)
        2. Build prompt with requirements + RAG context
        3. Agent plans the design process step-by-step
        4. Agent generates structured JSON design
        5. Extract design_yaml, api_schema, db_schema from response
        6. Update orchestration state

    Args:
        state: Current orchestration state

    Returns:
        Updated state with design data or error information
    """
    logger.info("[design_node] Starting design generation with Deep Agents")

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

    # Get LLM client
    provider = state.get("ai_provider", "anthropic")
    try:
        llm = get_llm_client(provider, {"temperature": 0.1, "max_tokens": 4000})
    except Exception as e:
        logger.error(f"[design_node] Failed to create LLM client: {e}")
        state["errors"]["design"] = f"LLM client error: {str(e)}"
        state["agent_statuses"]["design"] = AgentStatus.FAILED
        return state

    # Create Deep Agent (write_todos tool is built-in for planning)
    agent = create_deep_agent(
        model=llm,
        tools=[],  # No external tools needed — pure LLM generation
        system_prompt=(
            "You are a .NET/React/Azure architect. "
            "Your job is to analyze software requirements and produce "
            "a structured design covering: app_name, stack, entities, "
            "api_endpoints, and deployment_target. "
            "Think step by step before writing the final design."
        ),
    )

    # Build RAG context section
    rag_section = ""
    if rag_context:
        logger.info(f"[design_node] Including {len(rag_context)} RAG documents")
        rag_docs = "\n".join(
            f"## Relevant Context\n{d.get('content', '')}" for d in rag_context
        )
        rag_section = f"\n\n{rag_docs}"

    # Build user message
    message = f"""
Requirements:
{requirements}

{rag_section}

Produce a JSON object with keys:
- app_name (string, kebab-case, no spaces)
- description (string, 1-2 sentences)
- stack (object with: backend_framework, frontend_framework, database, auth_method)
- entities (array of objects with: name, fields as array of {{name, type, required}})
- api_endpoints (array of objects with: method, path, description)
- deployment_target (string, e.g., "Railway", "Azure")

Be specific and realistic. Use best practices for the chosen stack.
Return ONLY the JSON object, optionally wrapped in ```json markdown fences.
    """.strip()

    try:
        # Invoke Deep Agent
        logger.info("[design_node] Invoking Deep Agent with planning")
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})

        # Extract last assistant message
        raw = result["messages"][-1].content
        logger.debug(f"[design_node] Raw LLM response: {raw[:200]}...")

        # Parse JSON (strip markdown fences if present)
        match = re.search(r"```(?:json)?\s*\n(.*?)```", raw, re.DOTALL)
        json_str = match.group(1).strip() if match else raw.strip()
        parsed = json.loads(json_str)

        logger.info(f"[design_node] Design generated: {parsed.get('app_name')}")

        # Populate state with design data
        state["design_yaml"] = parsed

        # Extract API schema
        state["api_schema"] = parsed.get("api_endpoints", [])

        # Extract DB schema
        state["db_schema"] = [
            {"table": e["name"], "fields": e.get("fields", [])}
            for e in parsed.get("entities", [])
        ]

        # Mark success
        state["completed_steps"].append("design")
        state["agent_statuses"]["design"] = AgentStatus.COMPLETED

        logger.info("[design_node] Design generation completed successfully")

    except json.JSONDecodeError as e:
        logger.error(f"[design_node] JSON parsing failed: {e}")
        state["errors"]["design"] = f"Failed to parse JSON design: {str(e)}"
        state["agent_statuses"]["design"] = AgentStatus.FAILED

    except Exception as e:
        logger.error(f"[design_node] Unexpected error: {e}")
        state["errors"]["design"] = str(e)
        state["agent_statuses"]["design"] = AgentStatus.FAILED

    return state
