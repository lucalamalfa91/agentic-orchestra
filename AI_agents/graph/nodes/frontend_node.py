"""
Frontend Agent Node — Generates frontend code from design (any framework).

This agent:
- Reads design_yaml, api_schema from state
- Generates complete frontend codebase in the framework specified in design_yaml["stack"]
- Supports: React, Vue, Angular, Svelte, Next.js, Nuxt, SolidJS, etc. (with TS or JS)
- Populates state["frontend_code"] as dict {file_path: code_content}
- Uses BaseAgent abstraction for consistent error handling and retries

Created: Prompt 07d (2026-04-10)
Modified: 2026-04-10 - Made framework-agnostic
"""

from AI_agents.base_agent import BaseAgent
from AI_agents.graph.state import OrchestraState
import json
from json_repair import repair_json
import logging

logger = logging.getLogger(__name__)


class FrontendAgent(BaseAgent):
    """
    Generates frontend code from architecture design (framework-agnostic).

    Input fields (from OrchestraState):
        - design_yaml: dict with app_name, description, stack config (specifies frontend_framework)
        - api_schema: list of API endpoints (method, path, description)
        - rag_context: optional list of relevant docs/examples

    Output fields (updates OrchestraState):
        - frontend_code: dict mapping file paths to code content
          Example: {"frontend/src/App.jsx": "...", "frontend/src/components/UserList.vue": "..."}

    Supported frameworks:
        - React (JavaScript or TypeScript, with Vite/CRA/Next.js)
        - Vue 3 (Composition API or Options API, with Vite/Nuxt)
        - Angular (TypeScript)
        - Svelte/SvelteKit
        - SolidJS
        - Qwik
        - Any other frontend framework specified by user
    """

    agent_name = "frontend_agent"
    output_field = "frontend_code"

    def get_llm_config(self) -> dict:
        return {"max_tokens": 8000}

    def system_prompt(self) -> str:
        return """You are an expert polyglot frontend architect with deep knowledge of modern web frameworks and UI development.

Your task is to generate a complete, production-ready frontend codebase in the EXACT framework specified by the user.

CRITICAL OUTPUT FORMAT:
You must output ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "files": {{
    "frontend/src/[main_file]": "... complete code ...",
    "frontend/src/[folder]/[file]": "... complete code ...",
    ...
  }}
}}

Example for React + TypeScript + Vite:
{{
  "files": {{
    "frontend/src/App.tsx": "...",
    "frontend/src/main.tsx": "...",
    "frontend/src/components/UserList.tsx": "...",
    "frontend/package.json": "...",
    "frontend/vite.config.ts": "..."
  }}
}}

Example for Vue 3 + Vite:
{{
  "files": {{
    "frontend/src/App.vue": "...",
    "frontend/src/main.js": "...",
    "frontend/src/components/UserList.vue": "...",
    "frontend/package.json": "...",
    "frontend/vite.config.js": "..."
  }}
}}

Example for Angular:
{{
  "files": {{
    "frontend/src/app/app.component.ts": "...",
    "frontend/src/app/components/user-list/user-list.component.ts": "...",
    "frontend/package.json": "...",
    "frontend/angular.json": "..."
  }}
}}

FRAMEWORK-SPECIFIC REQUIREMENTS:
You will receive the exact framework to use in the user prompt. Follow these principles for ANY framework:

1. Generate ALL necessary files for a working application:
   - Main entry point (main.tsx, main.js, main.ts, index.html, etc.)
   - Root component (App.tsx, App.vue, app.component.ts, etc.)
   - Components (reusable UI components for each entity)
   - Pages/Views (page components for each route)
   - API client (HTTP service with typed requests)
   - Styling (CSS, SCSS, Tailwind, CSS-in-JS as appropriate)
   - Configuration files (package.json, tsconfig.json, vite/webpack config, etc.)

2. Code quality standards (adapt to framework conventions):
   - Use TypeScript if specified, otherwise JavaScript
   - Follow framework's component patterns (functional/class, composition/options, etc.)
   - Proper type definitions for props and API responses (if TypeScript)
   - Error handling for API calls
   - Loading states for async operations
   - Accessible HTML (ARIA labels, semantic elements)

3. Routing:
   - Use framework's recommended router (React Router, Vue Router, Angular Router, etc.)
   - Create routes for: home, entity lists, entity detail pages
   - Include 404 not found page

4. State Management:
   - Use framework's built-in state (hooks, reactive, signals, etc.)
   - Add global state if needed (Context, Pinia, NgRx, stores, etc.)

5. Styling:
   - Use Tailwind CSS, framework's scoped styles, or CSS modules as appropriate
   - Responsive design (mobile-first)
   - Modern UI patterns (cards, modals, forms)
   - Consistent spacing and typography

6. API Integration:
   - Create API client/service layer
   - Use environment variables for API base URL
   - CRUD operations for each entity (GET, POST, PUT, DELETE)
   - Handle API errors gracefully

7. Dependencies:
   - Include all necessary dependencies in package.json
   - Use appropriate versions for the framework
   - Add dev dependencies for tooling

OUTPUT RULES:
- Output MUST be valid JSON only (no markdown fences, no explanations)
- All file paths use forward slashes: "frontend/src/App.tsx"
- Follow the framework's standard project structure
- All code must run without errors (syntax correct, imports valid)
- Include proper import statements in all files
- Escape special characters in JSON (quotes, newlines, backslashes)
- Use the EXACT framework specified - do not substitute or change it

SCOPE CONSTRAINT (MANDATORY):
- Generate ONLY 6–8 files maximum. Quality over quantity.
- Prioritize: entry point (index.html/main.tsx), root component (App.tsx/App.vue), one main page component, API client file, package.json, config file.
- Each file: max 150 lines. Keep code focused and correct.
- Do NOT generate a separate component for every entity — one main component is enough for an MVP.
- A working app with 7 focused files is better than an incomplete app with 20 truncated files.

IMPORTANT: Read the user prompt carefully to understand which framework to use. Generate code ONLY in that framework.
"""

    def build_input(self, state: OrchestraState) -> str:
        """
        Build prompt from design specifications in state.

        Formats design_yaml, api_schema into a clear specification
        for the LLM to generate frontend code.
        """
        design = state.get("design_yaml")
        if design is None:
            raise ValueError(
                "design_yaml is None - design agent may have failed. "
                "Check state['errors']['design'] for details."
            )

        api_endpoints = state.get("api_schema", [])
        rag_docs = state.get("rag_context", [])

        # Build context section from RAG documents
        context_section = ""
        if rag_docs:
            context_section = "\n## Relevant Documentation\n"
            for doc in rag_docs[:3]:  # Limit to top 3 to avoid token overflow
                context_section += f"### {doc.get('source', 'Unknown')}\n{doc.get('content', '')}\n\n"

        # Format API endpoints
        api_section = "## API Endpoints to Integrate\n"
        if api_endpoints:
            for endpoint in api_endpoints:
                method = endpoint.get("method", "GET")
                path = endpoint.get("path", "/")
                desc = endpoint.get("description", "")
                api_section += f"- {method} {path}: {desc}\n"
        else:
            api_section += "(No specific endpoints defined - create placeholder API client)\n"

        # Build full prompt
        app_name = design.get("app_name", "MyApp")
        description = design.get("description", "No description provided")
        stack = design.get("stack", {})
        frontend_framework = stack.get("frontend_framework", "React")

        return f"""# Frontend Code Generation Request

## Application Overview
**Name**: {app_name}
**Description**: {description}

## REQUIRED TECHNOLOGY STACK
**Frontend Framework**: {frontend_framework}

CRITICAL: You MUST use {frontend_framework} as the frontend framework. Do not substitute with another framework.
Generate code following {frontend_framework} conventions and best practices.

{api_section}

{context_section}

## UI Requirements
- Modern, responsive design (mobile-first)
- Clean, professional appearance
- Smooth user experience with loading states
- Error handling with user-friendly messages
- Accessible (WCAG 2.1 AA compliant)

## Instructions
Generate the frontend codebase in {frontend_framework} following the requirements in your system prompt.
Use the appropriate project structure, component patterns, and tooling for {frontend_framework}.
If TypeScript is specified in the framework name, use TypeScript. Otherwise, use JavaScript unless the framework requires TypeScript (like Angular).
IMPORTANT: Generate exactly 6–8 files. One main App component, one page/view component, one API client, package.json, config, index.html.
Each file must be complete and correct (max 150 lines each).
Output ONLY the JSON structure with all file paths and code content. No markdown, no explanations.
"""

    def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
        """
        Parse JSON response and extract frontend code files.

        Expected format:
        {
          "files": {
            "frontend/src/App.tsx": "...",
            "frontend/package.json": "..."
          }
        }

        Populates state["frontend_code"] with the files dict.
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
                logger.warning(f"[frontend_agent] JSON parse failed, attempting repair: {json_err}")
                try:
                    # Attempt to repair malformed JSON
                    repaired = repair_json(cleaned)
                    parsed = json.loads(repaired)
                    logger.info("[frontend_agent] JSON repaired successfully")
                except Exception as repair_err:
                    logger.error(f"[frontend_agent] JSON repair also failed: {repair_err}")
                    raise json_err  # Re-raise original error

            # Validate structure
            if "files" not in parsed:
                raise ValueError("Response missing 'files' key")

            frontend_files = parsed["files"]

            # Validate essential files (framework-agnostic)
            has_package = any("package.json" in path for path in frontend_files.keys())

            if not has_package:
                logger.warning("[frontend_agent] No package.json found - might cause issues")

            # Log file count
            logger.debug(f"[frontend_agent] Files generated: {list(frontend_files.keys())}")

            # Store in state
            state["frontend_code"] = frontend_files
            logger.info(f"[frontend_agent] Generated {len(frontend_files)} frontend files")

            return state

        except json.JSONDecodeError as e:
            logger.error(f"[frontend_agent] JSON parse error: {e}")
            logger.error(f"[frontend_agent] Raw output (first 500 chars): {raw[:500]}")
            raise ValueError("Failed to parse JSON: " + str(e).replace("{", "{{").replace("}", "}}"))
        except Exception as e:
            logger.error(f"[frontend_agent] Unexpected error parsing output: {e}")
            raise


# ============================================================================
# Node function
# ============================================================================

async def frontend_node(state: OrchestraState) -> OrchestraState:
    """
    Frontend agent node for LangGraph graph.

    Generates frontend code in any framework specified in design_yaml["stack"]["frontend_framework"].
    Supports: React, Vue, Angular, Svelte, Next.js, Nuxt, SolidJS, etc.
    Uses BaseAgent for retry logic, error handling, and state management.

    Args:
        state: OrchestraState with design_yaml, api_schema

    Returns:
        OrchestraState with frontend_code populated (or error set on failure)
    """
    return await FrontendAgent().run(state)
