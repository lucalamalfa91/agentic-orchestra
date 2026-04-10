"""
Backend Agent Node — Generates backend code from design (any language/framework).

This agent:
- Reads design_yaml, api_schema, db_schema from state
- Generates complete backend codebase in the framework specified in design_yaml["stack"]
- Supports: C#/ASP.NET Core, Python/FastAPI, Node.js/Express, Java/Spring Boot, Go/Gin, etc.
- Populates state["backend_code"] as dict {file_path: code_content}
- Uses BaseAgent abstraction for consistent error handling and retries

Created: Prompt 07d (2026-04-10)
Modified: 2026-04-10 - Made language-agnostic
"""

from AI_agents.base_agent import BaseAgent
from AI_agents.graph.state import OrchestraState
import json
import logging

logger = logging.getLogger(__name__)


class BackendAgent(BaseAgent):
    """
    Generates backend code from architecture design (language-agnostic).

    Input fields (from OrchestraState):
        - design_yaml: dict with app_name, description, stack config (specifies backend_framework)
        - api_schema: list of API endpoints (method, path, description)
        - db_schema: list of entities (name, fields)
        - rag_context: optional list of relevant docs/examples

    Output fields (updates OrchestraState):
        - backend_code: dict mapping file paths to code content
          Example: {"backend/main.py": "...", "backend/models/user.py": "..."}

    Supported frameworks:
        - C# / ASP.NET Core
        - Python / FastAPI, Django, Flask
        - Node.js / Express, NestJS, Fastify
        - Java / Spring Boot
        - Go / Gin, Echo, Fiber
        - Ruby / Rails
        - PHP / Laravel
        - Any other backend framework specified by user
    """

    agent_name = "backend_agent"

    def system_prompt(self) -> str:
        return """You are an expert polyglot backend architect with deep knowledge of modern web frameworks across all major programming languages.

Your task is to generate a complete, production-ready backend codebase in the EXACT framework specified by the user.

CRITICAL OUTPUT FORMAT:
You must output ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "files": {{
    "backend/[main_file]": "... complete code ...",
    "backend/[folder]/[file]": "... complete code ...",
    ...
  }}
}}

Example for Python/FastAPI:
{{
  "files": {{
    "backend/main.py": "...",
    "backend/models/user.py": "...",
    "backend/routers/users.py": "...",
    "backend/requirements.txt": "..."
  }}
}}

Example for Node.js/Express:
{{
  "files": {{
    "backend/server.js": "...",
    "backend/models/User.js": "...",
    "backend/routes/users.js": "...",
    "backend/package.json": "..."
  }}
}}

FRAMEWORK-SPECIFIC REQUIREMENTS:
You will receive the exact framework to use in the user prompt. Follow these principles for ANY framework:

1. Generate ALL necessary files for a working application:
   - Main entry point (main.py, server.js, Program.cs, etc.)
   - Models/Entities (one file/class per entity from db_schema)
   - Services/Business logic (business logic for each entity)
   - Routes/Controllers/Endpoints (API endpoints from api_schema)
   - Database configuration (ORM/connection setup)
   - Configuration files (requirements.txt, package.json, appsettings.json, go.mod, etc.)

2. Code quality standards (adapt to language conventions):
   - Use async/await for all I/O operations (if language supports it)
   - Include documentation comments (docstrings, JSDoc, XML docs, etc.)
   - Follow language naming conventions (PascalCase, camelCase, snake_case, etc.)
   - Add proper error handling (try-catch, error middleware, etc.)
   - Use dependency injection / proper architecture patterns
   - Include input validation (Pydantic, Joi, DataAnnotations, etc.)

3. Database/ORM:
   - Use appropriate ORM for the framework (SQLAlchemy, Prisma, EF Core, GORM, etc.)
   - Configure all entities from db_schema
   - Use proper relationships (one-to-many, many-to-many as per design)
   - Add migrations/schema management if applicable

4. API Design:
   - RESTful conventions (GET, POST, PUT, DELETE)
   - Return appropriate HTTP status codes (200, 201, 404, 500)
   - Use DTOs/schemas for request/response validation
   - Enable API documentation (Swagger/OpenAPI, auto-docs, etc.)

5. Security:
   - Use HTTPS
   - Add CORS configuration
   - Prepare for authentication (JWT, OAuth, sessions as appropriate)
   - Sanitize user inputs
   - Use environment variables for secrets

OUTPUT RULES:
- Output MUST be valid JSON only (no markdown fences, no explanations)
- All file paths use forward slashes: "backend/models/user.py"
- Follow the framework's standard project structure
- All code must run without errors (syntax correct, imports valid)
- Include proper import statements in all files
- Escape special characters in JSON (quotes, newlines, backslashes)
- Use the EXACT framework specified - do not substitute or change it

IMPORTANT: Read the user prompt carefully to understand which framework to use. Generate code ONLY in that framework.
"""

    def build_input(self, state: OrchestraState) -> str:
        """
        Build prompt from design specifications in state.

        Formats design_yaml, api_schema, db_schema into a clear specification
        for the LLM to generate backend code.
        """
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

## REQUIRED TECHNOLOGY STACK
**Backend Framework**: {backend_framework}
**Database**: {database}

CRITICAL: You MUST use {backend_framework} as the backend framework. Do not substitute with another framework.
Generate code following {backend_framework} conventions and best practices.

{api_section}

{db_section}

{context_section}

## Instructions
Generate the complete backend codebase in {backend_framework} following the requirements in your system prompt.
Use the appropriate project structure, naming conventions, and patterns for {backend_framework}.
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

            # Log file count (no validation on specific files since framework varies)
            logger.debug(f"[backend_agent] Files generated: {list(backend_files.keys())}")

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

    Generates backend code in any framework specified in design_yaml["stack"]["backend_framework"].
    Supports: C#/ASP.NET Core, Python/FastAPI, Node.js/Express, Java/Spring Boot, Go/Gin, etc.
    Uses BaseAgent for retry logic, error handling, and state management.

    Args:
        state: OrchestraState with design_yaml, api_schema, db_schema

    Returns:
        OrchestraState with backend_code populated (or error set on failure)
    """
    return await BackendAgent().run(state)
