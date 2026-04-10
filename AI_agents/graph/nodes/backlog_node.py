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

    def system_prompt(self) -> str:
        return """You are an expert product owner and agile coach specialized in breaking down requirements into actionable backlog items.

Your task is to generate a comprehensive product backlog based on the provided requirements and design specification.

CRITICAL OUTPUT FORMAT:
You must output ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "items": [
    {{
      "title": "As a user, I want to...",
      "body": "## Description\\n...\\n\\n## Acceptance Criteria\\n- [ ] ...\\n- [ ] ...\\n\\n## Technical Notes\\n...",
      "labels": ["feature", "backend"],
      "priority": "high"
    }}
  ]
}}

REQUIREMENTS:
1. Generate backlog items in these categories:
   - **User Stories**: Features from end-user perspective (As a <role>, I want <goal>, so that <benefit>)
   - **Technical Tasks**: Implementation tasks (Set up database, Configure CI/CD, etc.)
   - **Testing Tasks**: QA and testing requirements (Write unit tests, E2E testing, etc.)
   - **Documentation Tasks**: Docs that need to be written (API docs, user guide, README)
   - **Technical Debt**: Known improvements (Refactor X, Optimize Y, etc.)

2. Each backlog item must have:
   - **title**: Clear, concise summary (50-80 chars)
     - User stories: "As a [role], I want to [action]"
     - Technical tasks: "[Action] [component]" (e.g., "Set up PostgreSQL database")
   - **body**: Detailed description with:
     - Description section (what and why)
     - Acceptance Criteria (checklist with - [ ] format)
     - Technical Notes (implementation hints, dependencies)
   - **labels**: Array of relevant labels
     - Type: feature, bug, enhancement, documentation, technical-debt, testing
     - Component: frontend, backend, database, devops, api
     - Priority level: P0, P1, P2, P3
   - **priority**: "critical" | "high" | "medium" | "low"

3. Backlog structure:
   - Prioritize items (critical/high priority items first)
   - Include 15-25 items total (comprehensive but manageable)
   - Break large features into smaller stories (1-5 days each)
   - Add dependencies in Technical Notes if needed

4. User Story format:
   - Title: "As a [user/admin/developer], I want to [action]"
   - Body:
     ```markdown
     ## Description
     [What the user wants to achieve and why it's valuable]

     ## Acceptance Criteria
     - [ ] [Specific, testable criterion]
     - [ ] [Another criterion]

     ## Technical Notes
     - [Implementation hints]
     - [Dependencies: "Requires #X to be completed"]
     ```

5. Technical Task format:
   - Title: "[Action] [component]" (e.g., "Set up Entity Framework migrations")
   - Body: Similar structure but focus on implementation details

6. Label guidelines:
   - Every item has at least 2 labels: [type] + [component]
   - Add priority label: P0 (critical), P1 (high), P2 (medium), P3 (low)
   - Optional: good-first-issue, help-wanted, security

7. Priority assignment:
   - **critical**: Core MVP features, blocking dependencies, security issues
   - **high**: Important features, foundational infrastructure
   - **medium**: Nice-to-have features, optimizations
   - **low**: Polish, minor enhancements, future improvements

OUTPUT RULES:
- Output MUST be valid JSON only (no markdown fences, no explanations)
- All backlog items in "items" array
- Use \\n for newlines in body field (JSON escape)
- Priority must be one of: critical, high, medium, low
- Labels must be lowercase-with-hyphens

If any requirement is unclear, make reasonable assumptions based on common product development practices.
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

            # Parse JSON
            parsed = json.loads(cleaned)

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
            raise ValueError(f"Failed to parse backlog JSON: {e}")
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
