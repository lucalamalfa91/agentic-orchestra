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
from AI_agents.graph.state import OrchestraState, AgentStatus
from AI_agents.utils.llm_client import get_llm_client
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import json
import time
from json_repair import repair_json
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
    output_field = "backend_code"

    def get_llm_config(self) -> dict:
        return {"max_tokens": 8000}

    # ------------------------------------------------------------------
    # Per-file generation: overrides BaseAgent.run()
    # ------------------------------------------------------------------

    async def run(self, state: OrchestraState) -> OrchestraState:  # type: ignore[override]
        """
        Two-phase generation:
          1. Ask the LLM for a file plan (list of filenames + purpose).
          2. For each file, make a separate LLM call to generate its content.
        This avoids JSON-truncation when the entire codebase is generated in
        one shot (which easily exceeds 64K output tokens for non-trivial apps).
        """
        if self.output_field and state.get(self.output_field):
            logger.info("[backend_agent] output already present, skipping")
            state["completed_steps"].append(self.agent_name)
            state["agent_statuses"][self.agent_name] = AgentStatus.COMPLETED
            return state

        state["current_step"] = self.agent_name
        state["agent_statuses"][self.agent_name] = AgentStatus.RUNNING

        provider = state.get("ai_provider", "anthropic")
        llm = get_llm_client(provider, {"max_tokens": 2000})

        design = state.get("design_yaml") or {}
        stack = design.get("stack", {})
        framework = stack.get("backend_framework", "FastAPI")
        database = stack.get("database", "PostgreSQL")
        app_name = design.get("app_name", "app")
        description = design.get("description", "")
        api_endpoints = state.get("api_schema", [])
        db_entities = state.get("db_schema", [])

        # ── Phase 1: file plan ────────────────────────────────────────
        plan_prompt = f"""You are a {framework} architect.
List the files needed for a minimal working backend for: {app_name} — {description}
Framework: {framework}, Database: {database}
Entities: {', '.join(e.get('name','') for e in db_entities)}
Endpoints: {len(api_endpoints)} REST endpoints

Return ONLY a JSON array of objects with keys "path" and "purpose". Max 8 files.
Example: [{{"path":"backend/main.py","purpose":"entry point"}},...]"""

        try:
            plan_raw = await (
                RunnableLambda(lambda _: [HumanMessage(content=plan_prompt)])
                | llm
                | StrOutputParser()
            ).ainvoke({})
            cleaned = plan_raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(l for l in lines if not l.startswith("```"))
            try:
                file_plan = json.loads(cleaned)
            except json.JSONDecodeError:
                file_plan = json.loads(repair_json(cleaned))
            if not isinstance(file_plan, list):
                file_plan = file_plan.get("files", [])
        except Exception as e:
            logger.error("[backend_agent] file plan failed: %s", e)
            state["errors"][self.agent_name] = f"File plan failed: {e}"
            state["agent_statuses"][self.agent_name] = AgentStatus.FAILED
            return state

        logger.info("[backend_agent] file plan: %s", [f.get("path") for f in file_plan])

        # ── Phase 2: generate each file ──────────────────────────────
        llm_file = get_llm_client(provider, {"max_tokens": 4000})
        backend_code: dict = {}

        api_summary = "\n".join(
            f"  {ep.get('method','GET')} {ep.get('path','/')}: {ep.get('description','')}"
            for ep in api_endpoints
        )
        entity_summary = "\n".join(
            f"  {e.get('name','')}: {', '.join(f.get('name','') for f in e.get('fields',[]))}"
            for e in db_entities
        )

        for file_info in file_plan:
            file_path = file_info.get("path", "")
            purpose = file_info.get("purpose", "")
            if not file_path:
                continue

            file_prompt = f"""Generate the file `{file_path}` for a {framework} + {database} backend.
App: {app_name} — {description}

Purpose of this file: {purpose}

API endpoints (for context):
{api_summary or '  (standard CRUD)'}

Entities (for context):
{entity_summary or '  User'}

Rules:
- Output ONLY the raw source code for this single file (no JSON wrapping, no markdown fences).
- Max 150 lines. Complete and syntactically correct.
- Include all necessary imports."""

            for attempt in range(3):
                try:
                    t0 = time.monotonic()
                    code = await (
                        RunnableLambda(lambda _: [HumanMessage(content=file_prompt)])
                        | llm_file
                        | StrOutputParser()
                    ).ainvoke({})
                    logger.info("[backend_agent] %s generated in %.1fs", file_path, time.monotonic() - t0)
                    # Strip accidental markdown fences
                    if code.startswith("```"):
                        lines = code.split("\n")
                        code = "\n".join(l for l in lines if not l.startswith("```"))
                    backend_code[file_path] = code.strip()
                    break
                except Exception as e:
                    logger.warning("[backend_agent] file %s attempt %d failed: %s", file_path, attempt + 1, e)
                    if attempt == 2:
                        backend_code[file_path] = f"# Generation failed: {e}"

        state["backend_code"] = backend_code
        state["completed_steps"].append(self.agent_name)
        state["agent_statuses"][self.agent_name] = AgentStatus.COMPLETED
        logger.info("[backend_agent] completed — %d files", len(backend_code))
        return state

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

SCOPE CONSTRAINT (MANDATORY):
- Generate ONLY 6–8 files maximum. Quality over quantity.
- Prioritize: entry point, models, one routes/controllers file, database config, requirements/package file.
- Each file: max 150 lines. Keep code focused and correct.
- Do NOT generate separate files for every entity — consolidate models into one file.
- A working app with 7 focused files is better than an incomplete app with 20 truncated files.

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
Generate the backend codebase in {backend_framework} following the requirements in your system prompt.
Use the appropriate project structure, naming conventions, and patterns for {backend_framework}.
IMPORTANT: Generate exactly 6–8 files. Consolidate models in one file, routes in one file.
Each file must be complete and correct (max 150 lines each).
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

            # Parse JSON (with repair fallback)
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError as json_err:
                logger.warning(f"[backend_agent] JSON parse failed, attempting repair: {json_err}")
                try:
                    # Attempt to repair malformed JSON
                    repaired = repair_json(cleaned)
                    parsed = json.loads(repaired)
                    logger.info("[backend_agent] JSON repaired successfully")
                except Exception as repair_err:
                    logger.error(f"[backend_agent] JSON repair also failed: {repair_err}")
                    raise json_err  # Re-raise original error

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
            raise ValueError("Failed to parse JSON: " + str(e).replace("{", "{{").replace("}", "}}"))
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
