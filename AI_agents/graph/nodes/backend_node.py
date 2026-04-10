"""
Backend Agent Node — Generates C# + ASP.NET Core backend code from design.

This agent:
- Reads design_yaml, api_schema, db_schema from state
- Generates complete backend codebase (Models, Services, Controllers, Program.cs)
- Populates state["backend_code"] as dict {file_path: code_content}
- Uses BaseAgent abstraction for consistent error handling and retries

Created: Prompt 07d (2026-04-10)
"""

from AI_agents.base_agent import BaseAgent
from AI_agents.graph.state import OrchestraState
import json
import logging

logger = logging.getLogger(__name__)


class BackendAgent(BaseAgent):
    """
    Generates backend code (C# + ASP.NET Core) from architecture design.

    Input fields (from OrchestraState):
        - design_yaml: dict with app_name, description, stack config
        - api_schema: list of API endpoints (method, path, description)
        - db_schema: list of entities (name, fields)
        - rag_context: optional list of relevant docs/examples

    Output fields (updates OrchestraState):
        - backend_code: dict mapping file paths to code content
          Example: {"backend/Program.cs": "...", "backend/Models/User.cs": "..."}
    """

    agent_name = "backend_agent"

    def system_prompt(self) -> str:
        return """You are an expert backend architect specialized in C# and ASP.NET Core.

Your task is to generate a complete, production-ready backend codebase based on the provided design specification.

CRITICAL OUTPUT FORMAT:
You must output ONLY valid JSON with this exact structure (no markdown, no extra text):
{
  "files": {
    "backend/Program.cs": "... complete C# code ...",
    "backend/Models/User.cs": "... complete C# code ...",
    "backend/Services/UserService.cs": "... complete C# code ...",
    "backend/Controllers/UserController.cs": "... complete C# code ...",
    "backend/Data/AppDbContext.cs": "... complete C# code ...",
    "backend/appsettings.json": "... JSON config ..."
  }
}

REQUIREMENTS:
1. Generate ALL necessary files for a working ASP.NET Core application:
   - Program.cs (with dependency injection, Swagger, CORS)
   - Models/ (one file per entity from db_schema)
   - Services/ (business logic for each entity)
   - Controllers/ (API endpoints from api_schema)
   - Data/AppDbContext.cs (Entity Framework Core context)
   - appsettings.json (configuration with database connection string)

2. Code quality standards:
   - Use async/await for all I/O operations
   - Include XML documentation comments
   - Follow C# naming conventions (PascalCase for public members)
   - Add proper error handling (try-catch in controllers)
   - Use dependency injection for services
   - Include input validation (DataAnnotations)

3. Entity Framework Core:
   - Configure DbContext with all entities
   - Use proper relationships (one-to-many, many-to-many as per design)
   - Add navigation properties where appropriate

4. API Design:
   - RESTful conventions (GET, POST, PUT, DELETE)
   - Return appropriate HTTP status codes (200, 201, 404, 500)
   - Use DTOs for request/response models if complex entities
   - Enable Swagger/OpenAPI documentation

5. Security:
   - Use HTTPS
   - Add CORS configuration
   - Prepare for authentication (even if not fully implemented)
   - Sanitize user inputs

OUTPUT RULES:
- Output MUST be valid JSON only (no markdown fences, no explanations)
- All file paths use forward slashes: "backend/Models/User.cs"
- All code must compile without errors
- Include proper using statements in all C# files
- Escape special characters in JSON (quotes, newlines, backslashes)

If any design field is missing or unclear, make reasonable assumptions and document them in code comments.
"""

    def build_input(self, state: OrchestraState) -> str:
        """
        Build prompt from design specifications in state.

        Formats design_yaml, api_schema, db_schema into a clear specification
        for the LLM to generate backend code.
        """
        design = state.get("design_yaml", {})
        api_endpoints = state.get("api_schema", [])
        db_entities = state.get("db_schema", [])
        rag_docs = state.get("rag_context", [])

        # Build context section from RAG documents
        context_section = ""
        if rag_docs:
            context_section = "\n## Relevant Documentation\n"
            for doc in rag_docs[:3]:  # Limit to top 3 to avoid token overflow
                context_section += f"### {doc.get('source', 'Unknown')}\n{doc.get('content', '')}\n\n"

        # Format API endpoints
        api_section = "## API Endpoints\n"
        if api_endpoints:
            for endpoint in api_endpoints:
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "/")
                desc = endpoint.get("description", "")
                api_section += f"- {method} {path}: {desc}\n"
        else:
            api_section += "(No specific endpoints defined - generate standard CRUD)\n"

        # Format database entities
        db_section = "## Database Entities\n"
        if db_entities:
            for entity in db_entities:
                name = entity.get("name", "Unknown")
                fields = entity.get("fields", [])
                db_section += f"\n### {name}\n"
                for field in fields:
                    field_name = field.get("name", "")
                    field_type = field.get("type", "string")
                    required = field.get("required", False)
                    db_section += f"  - {field_name}: {field_type}{'*' if required else ''}\n"
        else:
            db_section += "(No entities defined - generate basic User entity)\n"

        # Build full prompt
        app_name = design.get("app_name", "MyApp")
        description = design.get("description", "No description provided")
        stack = design.get("stack", {})
        backend_framework = stack.get("backend_framework", "ASP.NET Core")
        database = stack.get("database", "PostgreSQL")

        return f"""# Backend Code Generation Request

## Application Overview
**Name**: {app_name}
**Description**: {description}
**Backend Framework**: {backend_framework}
**Database**: {database}

{api_section}

{db_section}

{context_section}

Generate the complete backend codebase following the requirements in your system prompt.
Output ONLY the JSON structure with all file paths and code content. No markdown, no explanations.
"""

    def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
        """
        Parse JSON response and extract backend code files.

        Expected format:
        {
          "files": {
            "backend/Program.cs": "...",
            "backend/Models/User.cs": "..."
          }
        }

        Populates state["backend_code"] with the files dict.
        """
        try:
            # Strip markdown fences if present (LLM sometimes ignores instructions)
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                # Remove first and last lines (markdown fences)
                lines = cleaned.split("\n")
                # Find first { and last }
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
            if "files" not in parsed:
                raise ValueError("Response missing 'files' key")

            backend_files = parsed["files"]

            # Validate that we have at least Program.cs
            if not any("Program.cs" in path for path in backend_files.keys()):
                logger.warning("[backend_agent] No Program.cs found in generated files")

            # Store in state
            state["backend_code"] = backend_files
            logger.info(f"[backend_agent] Generated {len(backend_files)} backend files")

            return state

        except json.JSONDecodeError as e:
            logger.error(f"[backend_agent] JSON parse error: {e}")
            logger.error(f"[backend_agent] Raw output (first 500 chars): {raw[:500]}")
            raise ValueError(f"Failed to parse backend code JSON: {e}")
        except Exception as e:
            logger.error(f"[backend_agent] Unexpected error parsing output: {e}")
            raise


# ============================================================================
# Node function
# ============================================================================

async def backend_node(state: OrchestraState) -> OrchestraState:
    """
    Backend agent node for LangGraph graph.

    Generates C# + ASP.NET Core backend code from design specifications.
    Uses BaseAgent for retry logic, error handling, and state management.

    Args:
        state: OrchestraState with design_yaml, api_schema, db_schema

    Returns:
        OrchestraState with backend_code populated (or error set on failure)
    """
    return await BackendAgent().run(state)
