"""
Frontend Agent Node — Generates React + TypeScript frontend code from design.

This agent:
- Reads design_yaml, api_schema from state
- Generates complete frontend codebase (components, pages, API client, routing)
- Populates state["frontend_code"] as dict {file_path: code_content}
- Uses BaseAgent abstraction for consistent error handling and retries

Created: Prompt 07d (2026-04-10)
"""

from AI_agents.base_agent import BaseAgent
from AI_agents.graph.state import OrchestraState
import json
import logging

logger = logging.getLogger(__name__)


class FrontendAgent(BaseAgent):
    """
    Generates frontend code (React + TypeScript + Vite) from architecture design.

    Input fields (from OrchestraState):
        - design_yaml: dict with app_name, description, stack config
        - api_schema: list of API endpoints (method, path, description)
        - rag_context: optional list of relevant docs/examples

    Output fields (updates OrchestraState):
        - frontend_code: dict mapping file paths to code content
          Example: {"frontend/src/App.tsx": "...", "frontend/src/components/UserList.tsx": "..."}
    """

    agent_name = "frontend_agent"

    def system_prompt(self) -> str:
        return """You are an expert frontend architect specialized in React, TypeScript, and modern web development.

Your task is to generate a complete, production-ready frontend codebase based on the provided design specification.

CRITICAL OUTPUT FORMAT:
You must output ONLY valid JSON with this exact structure (no markdown, no extra text):
{
  "files": {
    "frontend/src/App.tsx": "... complete TSX code ...",
    "frontend/src/main.tsx": "... complete TSX code ...",
    "frontend/src/components/UserList.tsx": "... complete TSX code ...",
    "frontend/src/api/client.ts": "... complete TS code ...",
    "frontend/src/index.css": "... CSS code ...",
    "frontend/package.json": "... JSON config ...",
    "frontend/tsconfig.json": "... JSON config ...",
    "frontend/vite.config.ts": "... TS config ..."
  }
}

REQUIREMENTS:
1. Generate ALL necessary files for a working React + Vite application:
   - main.tsx (entry point with React.StrictMode)
   - App.tsx (main app component with routing)
   - components/ (reusable UI components for each entity)
   - pages/ (page components for each route)
   - api/client.ts (type-safe API client with fetch wrappers)
   - index.css (Tailwind CSS or modern styling)
   - package.json (with all dependencies)
   - tsconfig.json (TypeScript configuration)
   - vite.config.ts (Vite bundler configuration)

2. Code quality standards:
   - Use TypeScript with strict mode
   - Functional components with hooks (useState, useEffect, etc.)
   - Proper type definitions for all props and API responses
   - Error handling for API calls (try-catch)
   - Loading states for async operations
   - Accessible HTML (ARIA labels, semantic elements)

3. Routing:
   - Use React Router v6 for client-side routing
   - Create routes for: home, entity lists, entity detail pages
   - Include 404 not found page

4. State Management:
   - Use React hooks (useState, useContext) for local state
   - For global state (if needed), use Context API or simple store

5. Styling:
   - Use Tailwind CSS utility classes
   - Responsive design (mobile-first)
   - Modern UI patterns (cards, modals, forms)
   - Consistent spacing and typography

6. API Integration:
   - Create typed API client in api/client.ts
   - Environment variable for API base URL (import.meta.env.VITE_API_URL)
   - CRUD operations for each entity (GET, POST, PUT, DELETE)
   - Handle API errors gracefully (display user-friendly messages)

7. Dependencies (package.json):
   - react: ^18.3.0
   - react-dom: ^18.3.0
   - react-router-dom: ^6.20.0
   - typescript: ^5.3.0
   - vite: ^5.0.0
   - tailwindcss: ^3.4.0
   - @vitejs/plugin-react: ^4.2.0

OUTPUT RULES:
- Output MUST be valid JSON only (no markdown fences, no explanations)
- All file paths use forward slashes: "frontend/src/App.tsx"
- All code must compile without TypeScript errors
- Include proper import statements in all files
- Escape special characters in JSON (quotes, newlines, backslashes)
- Use // for single-line comments, /* */ for multi-line (not JSDoc /** */)

If any design field is missing or unclear, make reasonable assumptions and document them in code comments.
"""

    def build_input(self, state: OrchestraState) -> str:
        """
        Build prompt from design specifications in state.

        Formats design_yaml, api_schema into a clear specification
        for the LLM to generate frontend code.
        """
        design = state.get("design_yaml", {})
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
**Frontend Framework**: {frontend_framework} + TypeScript + Vite

{api_section}

{context_section}

## UI Requirements
- Modern, responsive design (mobile-first)
- Clean, professional appearance
- Smooth user experience with loading states
- Error handling with user-friendly messages
- Accessible (WCAG 2.1 AA compliant)

## Technical Stack
- React 18+ with functional components and hooks
- TypeScript with strict mode
- Vite for build tooling
- React Router v6 for routing
- Tailwind CSS for styling
- Fetch API for HTTP requests

Generate the complete frontend codebase following the requirements in your system prompt.
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

            # Parse JSON
            parsed = json.loads(cleaned)

            # Validate structure
            if "files" not in parsed:
                raise ValueError("Response missing 'files' key")

            frontend_files = parsed["files"]

            # Validate that we have essential files
            has_app = any("App.tsx" in path for path in frontend_files.keys())
            has_package = any("package.json" in path for path in frontend_files.keys())

            if not has_app:
                logger.warning("[frontend_agent] No App.tsx found in generated files")
            if not has_package:
                logger.warning("[frontend_agent] No package.json found in generated files")

            # Store in state
            state["frontend_code"] = frontend_files
            logger.info(f"[frontend_agent] Generated {len(frontend_files)} frontend files")

            return state

        except json.JSONDecodeError as e:
            logger.error(f"[frontend_agent] JSON parse error: {e}")
            logger.error(f"[frontend_agent] Raw output (first 500 chars): {raw[:500]}")
            raise ValueError(f"Failed to parse frontend code JSON: {e}")
        except Exception as e:
            logger.error(f"[frontend_agent] Unexpected error parsing output: {e}")
            raise


# ============================================================================
# Node function
# ============================================================================

async def frontend_node(state: OrchestraState) -> OrchestraState:
    """
    Frontend agent node for LangGraph graph.

    Generates React + TypeScript + Vite frontend code from design specifications.
    Uses BaseAgent for retry logic, error handling, and state management.

    Args:
        state: OrchestraState with design_yaml, api_schema

    Returns:
        OrchestraState with frontend_code populated (or error set on failure)
    """
    return await FrontendAgent().run(state)
