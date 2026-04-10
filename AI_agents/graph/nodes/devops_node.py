"""
DevOps Agent Node — Generates CI/CD workflows and Docker configuration.

This agent:
- Reads design_yaml, backend_code, frontend_code from state
- Generates CI/CD pipelines (GitHub Actions, Azure Pipelines, GitLab CI)
- Generates Docker configuration (Dockerfiles, docker-compose.yml)
- Generates deployment manifests (Kubernetes, Railway, Vercel config)
- Populates state["devops_config"] as dict {file_path: config_content}
- Uses BaseAgent abstraction for consistent error handling and retries

Created: Prompt 07e (2026-04-10)
"""

from AI_agents.base_agent import BaseAgent
from AI_agents.graph.state import OrchestraState
import json
import logging

logger = logging.getLogger(__name__)


class DevopsAgent(BaseAgent):
    """
    Generates DevOps configuration from application design.

    Input fields (from OrchestraState):
        - design_yaml: dict with app_name, description, stack config
        - backend_code: dict with backend file paths (to detect framework)
        - frontend_code: dict with frontend file paths (to detect framework)
        - rag_context: optional list of relevant docs/examples

    Output fields (updates OrchestraState):
        - devops_config: dict mapping file paths to configuration content
          Example: {
              ".github/workflows/ci-cd.yml": "...",
              "backend/Dockerfile": "...",
              "frontend/Dockerfile": "...",
              "docker-compose.yml": "..."
          }

    Supported platforms:
        - CI/CD: GitHub Actions, Azure Pipelines, GitLab CI, CircleCI
        - Containers: Docker, docker-compose
        - Deployment: Kubernetes, Railway, Vercel, Azure App Service, AWS ECS
        - IaC: Terraform, CloudFormation (optional)
    """

    agent_name = "devops_agent"

    def system_prompt(self) -> str:
        return """You are an expert DevOps engineer and infrastructure architect with deep knowledge of CI/CD, containerization, and cloud deployment.

Your task is to generate complete DevOps configuration files for deploying the application.

CRITICAL OUTPUT FORMAT:
You must output ONLY valid JSON with this exact structure (no markdown, no extra text):
{
  "files": {
    ".github/workflows/ci-cd.yml": "... complete workflow ...",
    "backend/Dockerfile": "... complete Dockerfile ...",
    "frontend/Dockerfile": "... complete Dockerfile ...",
    "docker-compose.yml": "... complete compose config ...",
    ...
  }
}

REQUIRED FILES TO GENERATE:

1. CI/CD Workflow (choose based on Git platform in requirements):
   - GitHub Actions: .github/workflows/ci-cd.yml
   - Azure Pipelines: azure-pipelines.yml
   - GitLab CI: .gitlab-ci.yml
   - Default to GitHub Actions if not specified

2. Docker Configuration:
   - backend/Dockerfile (multi-stage build for backend framework)
   - frontend/Dockerfile (multi-stage build for frontend framework)
   - docker-compose.yml (orchestrate backend + frontend + database)
   - .dockerignore (exclude node_modules, .git, etc.)

3. Deployment Configuration (optional, based on target platform):
   - Kubernetes: k8s/deployment.yaml, k8s/service.yaml, k8s/ingress.yaml
   - Railway: railway.json or railway.toml
   - Vercel: vercel.json (for frontend)
   - Azure: azure-app-service.yml
   - AWS: task-definition.json (ECS)

4. Environment Configuration:
   - .env.example (template for all required env vars)
   - README-DEPLOYMENT.md (deployment instructions)

CI/CD WORKFLOW REQUIREMENTS:

1. Pipeline Stages (adapt to platform):
   - Checkout code
   - Install dependencies (backend + frontend)
   - Run linters (eslint, pylint, etc.)
   - Run tests (unit + integration)
   - Build Docker images
   - Push images to registry (Docker Hub, GitHub Container Registry, Azure ACR)
   - Deploy to target environment (staging/production)

2. Environment Variables:
   - Use secrets for API keys, database passwords
   - Document all required secrets in README-DEPLOYMENT.md
   - Use appropriate secret management (GitHub Secrets, Azure Key Vault, etc.)

3. Triggers:
   - Push to main/master → deploy to production
   - Push to develop → deploy to staging
   - Pull requests → run tests only (no deployment)

DOCKERFILE REQUIREMENTS:

1. Multi-stage builds (builder + runtime):
   - Builder stage: install all dependencies, compile/build
   - Runtime stage: minimal base image, copy artifacts only
   - Example for Node.js: node:20-alpine builder → node:20-alpine runtime
   - Example for Python: python:3.11-slim builder → python:3.11-slim runtime
   - Example for .NET: mcr.microsoft.com/dotnet/sdk:8.0 → mcr.microsoft.com/dotnet/aspnet:8.0

2. Best Practices:
   - Non-root user (adduser, USER directive)
   - Layer caching optimization (COPY package.json FIRST, then npm install)
   - Minimal final image size (alpine variants, distroless)
   - Health checks (HEALTHCHECK directive)
   - Proper signal handling (ENTRYPOINT with exec form)

3. Framework-Specific:
   - Python/FastAPI: Use gunicorn or uvicorn with workers
   - Node.js/Express: Use PM2 or node in production mode
   - .NET: Use dotnet publish with Release configuration
   - Java/Spring Boot: Use JRE (not JDK) in runtime stage
   - Go: Static binary compilation, use scratch or alpine

DOCKER COMPOSE REQUIREMENTS:

1. Services:
   - backend: build from backend/Dockerfile, expose port
   - frontend: build from frontend/Dockerfile, expose port
   - database: use official image (postgres, mysql, mongo, etc.)
   - redis: optional, for caching/sessions
   - nginx: optional, for reverse proxy

2. Networking:
   - Create custom network for inter-service communication
   - Frontend calls backend via service name (http://backend:PORT)

3. Volumes:
   - Persistent volumes for database data
   - Bind mounts for development (hot reload)

4. Environment Variables:
   - env_file: .env (load from file)
   - Default values in compose file for development

5. Health Checks:
   - Ensure services start in correct order (depends_on + healthcheck)

SECURITY & BEST PRACTICES:

1. Never hardcode secrets in configuration files
2. Use .env files (excluded from git via .gitignore)
3. Minimal base images (alpine, distroless)
4. Scan images for vulnerabilities (Trivy, Snyk in CI)
5. Use specific image tags (not :latest in production)
6. Implement proper logging (stdout/stderr for containers)
7. Resource limits (memory, CPU in docker-compose and k8s)

OUTPUT RULES:
- Output MUST be valid JSON only (no markdown fences, no explanations)
- All file paths use forward slashes
- All YAML must be valid (correct indentation, no tabs)
- All Dockerfiles must be valid (correct syntax, valid base images)
- Escape special characters in JSON (quotes, newlines, backslashes)
- Generate production-ready configuration (not dev-only)

IMPORTANT: Adapt all configuration to the EXACT tech stack specified in the user prompt.
"""

    def build_input(self, state: OrchestraState) -> str:
        """
        Build prompt from design specifications and generated code.

        Formats design_yaml, stack info, and code structure into a clear specification
        for the LLM to generate DevOps configuration.
        """
        design = state.get("design_yaml", {})
        backend_files = state.get("backend_code", {})
        frontend_files = state.get("frontend_code", {})
        rag_docs = state.get("rag_context", [])

        # Build context section from RAG documents
        context_section = ""
        if rag_docs:
            context_section = "\n## Relevant Documentation\n"
            for doc in rag_docs[:3]:  # Limit to top 3 to avoid token overflow
                context_section += f"### {doc.get('source', 'Unknown')}\n{doc.get('content', '')}\n\n"

        # Detect backend framework from file structure
        backend_framework = design.get("stack", {}).get("backend_framework", "ASP.NET Core")
        if backend_files:
            if "backend/main.py" in backend_files or "backend/requirements.txt" in backend_files:
                backend_framework = "Python/FastAPI"
            elif "backend/server.js" in backend_files or "backend/package.json" in backend_files:
                backend_framework = "Node.js/Express"
            elif "backend/Program.cs" in backend_files:
                backend_framework = "C#/ASP.NET Core"
            elif "backend/main.go" in backend_files:
                backend_framework = "Go/Gin"

        # Detect frontend framework from file structure
        frontend_framework = design.get("stack", {}).get("frontend_framework", "React")
        if frontend_files:
            if "frontend/package.json" in frontend_files:
                # Could be React, Vue, Angular, etc. - use design spec
                frontend_framework = design.get("stack", {}).get("frontend_framework", "React")

        # Get database from stack
        database = design.get("stack", {}).get("database", "PostgreSQL")

        # Determine CI/CD platform (default to GitHub Actions)
        ci_platform = design.get("stack", {}).get("ci_platform", "GitHub Actions")

        # Determine deployment target
        deployment_target = design.get("stack", {}).get("deployment_target", "Docker Compose")

        # Build full prompt
        app_name = design.get("app_name", "MyApp")
        description = design.get("description", "No description provided")

        return f"""# DevOps Configuration Generation Request

## Application Overview
**Name**: {app_name}
**Description**: {description}

## Technology Stack
**Backend Framework**: {backend_framework}
**Frontend Framework**: {frontend_framework}
**Database**: {database}
**CI/CD Platform**: {ci_platform}
**Deployment Target**: {deployment_target}

## Generated Code Structure
**Backend Files**: {len(backend_files)} files
Sample paths: {', '.join(list(backend_files.keys())[:5])}

**Frontend Files**: {len(frontend_files)} files
Sample paths: {', '.join(list(frontend_files.keys())[:5])}

{context_section}

## Instructions
Generate complete DevOps configuration following the requirements in your system prompt.

REQUIRED:
1. CI/CD workflow for {ci_platform}
2. Dockerfiles for {backend_framework} backend and {frontend_framework} frontend
3. docker-compose.yml with backend + frontend + {database}
4. .dockerignore files
5. .env.example template
6. README-DEPLOYMENT.md with setup instructions

OPTIONAL (if deployment target specified):
- Kubernetes manifests (if deployment_target = "Kubernetes")
- Railway config (if deployment_target = "Railway")
- Vercel config (if deployment_target = "Vercel")

Output ONLY the JSON structure with all file paths and configuration content.
No markdown, no explanations.
"""

    def parse_output(self, raw: str, state: OrchestraState) -> OrchestraState:
        """
        Parse JSON response and extract DevOps configuration files.

        Expected format:
        {
          "files": {
            ".github/workflows/ci-cd.yml": "...",
            "backend/Dockerfile": "...",
            "docker-compose.yml": "..."
          }
        }

        Populates state["devops_config"] with the files dict.
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

            devops_files = parsed["files"]

            # Basic validation: check for at least one Dockerfile
            has_dockerfile = any("Dockerfile" in path for path in devops_files.keys())
            if not has_dockerfile:
                logger.warning("[devops_agent] No Dockerfile found in generated config")

            # Log file count
            logger.debug(f"[devops_agent] Files generated: {list(devops_files.keys())}")

            # Store in state
            state["devops_config"] = devops_files
            logger.info(f"[devops_agent] Generated {len(devops_files)} DevOps config files")

            return state

        except json.JSONDecodeError as e:
            logger.error(f"[devops_agent] JSON parse error: {e}")
            logger.error(f"[devops_agent] Raw output (first 500 chars): {raw[:500]}")
            raise ValueError(f"Failed to parse DevOps config JSON: {e}")
        except Exception as e:
            logger.error(f"[devops_agent] Unexpected error parsing output: {e}")
            raise


# ============================================================================
# Node function
# ============================================================================

async def devops_node(state: OrchestraState) -> OrchestraState:
    """
    DevOps agent node for LangGraph graph.

    Generates CI/CD workflows, Docker configuration, and deployment manifests.
    Supports: GitHub Actions, Azure Pipelines, GitLab CI, Docker, Kubernetes, Railway, Vercel.
    Uses BaseAgent for retry logic, error handling, and state management.

    Args:
        state: OrchestraState with design_yaml, backend_code, frontend_code

    Returns:
        OrchestraState with devops_config populated (or error set on failure)
    """
    return await DevopsAgent().run(state)
