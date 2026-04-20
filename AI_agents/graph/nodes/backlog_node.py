"""
Backlog Agent Node — Generates product backlog (user stories, issues) from requirements.

This agent:
- Reads requirements, design_yaml, api_schema, db_schema from state
- Generates comprehensive product backlog with user stories, tasks, and technical debt items
- Populates state["backlog_items"] as list of dicts with GitHub issue format
- Uses BaseAgent abstraction for consistent error handling and retries

Created: Prompt 07d (2026-04-10)
"""

from AI_agents.base_agent import BaseAgent
from AI_agents.graph.state import OrchestraState
import json
from json_repair import repair_json
import logging

logger = logging.getLogger(__name__)


class BacklogAgent(BaseAgent):
    """
    Generates product backlog (user stories, issues) from requirements and design.

    Input fields (from OrchestraState):
        - requirements: str with raw user requirements
        - design_yaml: dict with app_name, description, stack config, entities
        - api_schema: list of API endpoints
        - db_schema: list of entities
        - rag_context: optional list of relevant docs/examples

    Output fields (updates OrchestraState):
        - backlog_items: list of dicts with GitHub issue format
          Each item: {title, body, labels, priority}
    """

    agent_name = "backlog_agent"
    output_field = "backlog_items"

    def get_llm_config(self):
        return {"max_tokens": 3000}

    def system_prompt(self) -> str:
        return """You are a product owner. Generate a concise product backlog as JSON.

Output ONLY valid JSON (no markdown, no extra text):
{
  "items": [
    {
      "title": "As a user, I want to...",
      "body": "## Acceptance Criteria\n- [ ] criterion 1\n- [ ] criterion 2",
      "labels": ["feature", "backend"],
      "priority": "high"
    }
  ]
}

Rules:
- Generate exactly 8-10 items total
- Include: user stories, 2 technical setup tasks, 1 testing task
- Keep body SHORT: only 2-3 acceptance criteria per item
- priority: critical | high | medium | low
- labels: lowercase-with-hyphens
- Output MUST be valid JSON only
"""

    def build_input(self, state: OrchestraState) -> str:
        """
        Build prompt from requirements and design specifications.

        Formats requirements, design_yaml, api_schema, db_schema into a clear
        specification for the LLM to generate backlog items.
        """
        requirements = state.get("requirements", "")
        design = state.get("design_yaml")
        if design is None:
            raise ValueError(
                "design_yaml is None - design agent may have failed. "
                "Check state['errors']['design'] for details."
            )

        api_endpoints = state.get("api_schema", [])
        db_entities = state.get("db_schema", [])
        rag_docs = state.get("rag_context", [])

        # Build context section from RAG documents
        context_section = ""
        if rag_docs:
            context_section = "\n## Relevant Documentation\n"
            for doc in rag_docs[:3]:
                context_section += f"### {doc.get('source', 'Unknown')}\n{doc.get('content', '')}\n\n"

        # Format API endpoints
        api_section = "## API Endpoints (from design)\n"
        if api_endpoints:
            for endpoint in api_endpoints:
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "/")
                desc = endpoint.get("description", "")
                api_section += f"- {method} {path}: {desc}\n"

        # Format database entities
        db_section = "## Database Entities (from design)\n"
        if db_entities:
            for entity in db_entities:
                name = entity.get("name", "Unknown")
                fields = entity.get("fields", [])
                db_section += f"\n### {name}\n"
                for field in fields:
                    field_name = field.get("name", "")
                    field_type = field.get("type", "string")
                    db_section += f"  - {field_name}: {field_type}\n"

        # Build full prompt
        app_name = design.get("app_name", "MyApp")
        description = design.get("description", "No description provided")
        stack = design.get("stack", {})

        return f"""# Backlog Generation Request

## Application Overview
**Name**: {app_name}
**Description**: {description}
**Stack**: {stack.get('backend_framework', 'N/A')} + {stack.get('frontend_framework', 'N/A')} + {stack.get('database', 'N/A')}

## Original Requirements
{requirements}

{api_section}

{db_section}

{context_section}

## Instructions
Generate a comprehensive product backlog for this application. Include:
1. User stories for all core features
2. Technical tasks for infrastructure setup (DB, CI/CD, auth)
3. Testing tasks (unit tests, integration tests, E2E tests)
4. Documentation tasks (README, API docs, deployment guide)
5. Technical debt items (code quality, performance, security)

Prioritize items based on dependencies and business value.
Output ONLY the JSON structure with backlog items. No markdown, no explanations.
"""

    def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
        """
        Parse JSON response and extract backlog items.

        Expected format:
        {
          "items": [
            {
              "title": "...",
              "body": "...",
              "labels": ["feature", "backend"],
              "priority": "high"
            }
          ]
        }

        Populates state["backlog_items"] with the items array.
        """
        try:
            # Strip markdown fences if present
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                start_idx = None
                end_idx = None
                for i, line in enumerate(lines):
                    if "{" in line and start_idx is None:
                        start_idx = i
                    if "}" in line:
                        end_idx = i
                if start_idx is not None and end_idx is not None:
                    cleaned = "\n".join(lines[start_idx:end_idx+1])

            # Parse JSON (with repair fallback for truncated responses)
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as json_err:
                logger.warning(f"[backlog_agent] JSON parse error: {json_err}, attempting repair")
                try:
                    repaired = repair_json(cleaned)
                    parsed = json.loads(repaired)
                    logger.info("[backlog_agent] JSON repaired successfully")
                except Exception:
                    raise json_err

            # Validate structure
            if "items" not in parsed:
                raise ValueError("Response missing 'items' key")

            backlog_items = parsed["items"]

            # Validate items structure
            for i, item in enumerate(backlog_items):
                if "title" not in item:
                    logger.warning(f"[backlog_agent] Item {i} missing 'title'")
                if "body" not in item:
                    logger.warning(f"[backlog_agent] Item {i} missing 'body'")
                if "labels" not in item:
                    item["labels"] = []  # Default to empty array
                if "priority" not in item:
                    item["priority"] = "medium"  # Default priority

            # Store in state
            state["backlog_items"] = backlog_items
            logger.info(f"[backlog_agent] Generated {len(backlog_items)} backlog items")

            # Log priority breakdown
            priority_counts = {}
            for item in backlog_items:
                p = item.get("priority", "unknown")
                priority_counts[p] = priority_counts.get(p, 0) + 1
            logger.info(f"[backlog_agent] Priority breakdown: {priority_counts}")

            return state

        except json.JSONDecodeError as e:
            logger.error(f"[backlog_agent] JSON parse error: {e}")
            logger.error(f"[backlog_agent] Raw output (first 500 chars): {raw[:500]}")
            raise ValueError("Failed to parse JSON: " + str(e).replace("{", "{{").replace("}", "}}"))
        except Exception as e:
            logger.error(f"[backlog_agent] Unexpected error parsing output: {e}")
            raise


# ============================================================================
# Node function
# ============================================================================

async def backlog_node(state: OrchestraState) -> OrchestraState:
    """
    Backlog agent node for LangGraph graph.

    Generates product backlog (user stories, issues) from requirements and design.
    Uses BaseAgent for retry logic, error handling, and state management.

    Args:
        state: OrchestraState with requirements, design_yaml, api_schema, db_schema

    Returns:
        OrchestraState with backlog_items populated (or error set on failure)
    """
    return await BacklogAgent().run(state)
