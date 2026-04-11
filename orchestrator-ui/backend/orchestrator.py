"""
Orchestrator for running LangGraph-based agent pipeline with progress tracking.

Replaced subprocess approach (run_all_agents.py) with direct LangGraph execution.
The WebSocket message format is preserved for frontend compatibility.
"""
import asyncio
import json
import logging
import os
import traceback
import uuid
from pathlib import Path
from typing import Optional, AsyncIterator
from sqlalchemy.orm import Session
from pydantic import ValidationError

logger = logging.getLogger(__name__)

try:
    from orchestrator_ui.backend import crud, schemas
    from orchestrator_ui.backend.websocket import manager
    from orchestrator_ui.backend.encryption_service import decrypt
    from orchestrator_ui.backend.models import Configuration, User
    from AI_agents.graph.graph import app as langgraph_app
    from AI_agents.graph.state import OrchestraState, AgentStatus
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    import crud
    import schemas
    from websocket import manager
    from encryption_service import decrypt
    from models import Configuration, User
    from AI_agents.graph.graph import app as langgraph_app
    from AI_agents.graph.state import OrchestraState, AgentStatus


class GenerationOrchestrator:
    """
    Orchestrates LangGraph-based MVP generation pipeline.

    Maps LangGraph agent node events to WebSocket progress messages
    using the same format as the legacy subprocess approach.
    """

    # Map agent node names to step information (preserves legacy format)
    AGENT_TO_STEP = {
        "knowledge_retrieval": {"step": "readme",   "step_number": 1, "percentage": 16},
        "design":              {"step": "design",   "step_number": 2, "percentage": 33},
        "backend_agent":       {"step": "backend",  "step_number": 3, "percentage": 50},
        "frontend_agent":      {"step": "frontend", "step_number": 4, "percentage": 67},
        "devops_agent":        {"step": "devops",   "step_number": 5, "percentage": 83},
        "publish_agent":       {"step": "publish",  "step_number": 6, "percentage": 100},
    }

    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.pipeline_data_dir = project_root / "pipeline_data"
        self.requirements_file = self.pipeline_data_dir / "requirements.txt"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _inject_env_vars(self, db: Session, user_id: int) -> str:
        """
        Inject user configuration and tokens as environment variables.

        These env vars are read by MCP servers and LLM client factories.
        Must be called BEFORE starting LangGraph execution.

        Args:
            db: Database session
            user_id: User ID to fetch config for

        Returns:
            AI provider name configured by user ("openai" or "anthropic")

        Raises:
            ValueError: If user_id is None or configuration is missing/invalid
        """
        # Validate user_id
        if not user_id:
            raise ValueError(
                "❌ Cannot start generation: No user ID provided. "
                "Please ensure you're logged in with GitHub."
            )

        ai_provider = "openai"  # Default fallback

        try:
            # Inject AI provider configuration
            config = db.query(Configuration).filter(
                Configuration.user_id == user_id,
                Configuration.is_active == True
            ).first()

            if not config:
                raise ValueError(
                    f"❌ No AI configuration found for user_id={user_id}. "
                    "Please configure your AI provider in Settings before starting generation."
                )

            # Decrypt and validate API key
            try:
                api_key = decrypt(config.ai_api_key_encrypted)
                if not api_key or len(api_key) < 10:
                    raise ValueError("Invalid or empty API key")
            except Exception as e:
                raise ValueError(
                    f"❌ Failed to decrypt API key: {e}. "
                    "Please re-configure your API key in Settings."
                )

            # Read provider from user configuration (graceful fallback for existing DBs)
            ai_provider = getattr(config, 'ai_provider', 'openai')

            # Validate base_url
            if not config.ai_base_url:
                raise ValueError(
                    f"❌ Missing base URL for AI provider '{ai_provider}'. "
                    "Please configure your base URL in Settings."
                )

            # Inject API key with correct env var name based on provider
            if ai_provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = api_key
                print(f"[DEBUG] Set ANTHROPIC_API_KEY = {api_key[:10]}...{api_key[-4:]}")

                # Validate Anthropic API key format
                if "anthropic.com" in config.ai_base_url.lower() and not api_key.startswith("sk-ant-"):
                    print(f"[WARN] Using official Anthropic API but key doesn't start with 'sk-ant-'. "
                          f"This may cause authentication errors. "
                          f"Expected: sk-ant-api-xxx, Got: {api_key[:10]}...")

                # Set base_url if it's not default Anthropic
                if "anthropic.com" not in config.ai_base_url.lower():
                    os.environ["ANTHROPIC_BASE_URL"] = config.ai_base_url
                    print(f"[DEBUG] Set ANTHROPIC_BASE_URL = {config.ai_base_url}")
                else:
                    print(f"[DEBUG] Using official Anthropic API (api.anthropic.com)")

            elif ai_provider == "openai":
                # OpenAI or OpenAI-compatible (like Adesso AI Hub)
                os.environ["OPENAI_API_KEY"] = api_key
                print(f"[DEBUG] Set OPENAI_API_KEY = {api_key[:10]}...{api_key[-4:]}")
                # Set base_url for OpenAI-compatible providers
                if "openai.com" not in config.ai_base_url.lower():
                    os.environ["OPENAI_BASE_URL"] = config.ai_base_url
                    print(f"[DEBUG] Set OPENAI_BASE_URL = {config.ai_base_url}")

            # Legacy support: also set ADESSO_* env vars for backwards compatibility
            os.environ["ADESSO_BASE_URL"] = config.ai_base_url
            os.environ["ADESSO_AI_HUB_KEY"] = api_key

            print(f"[OK] Injected AI config: provider={ai_provider}, base_url={config.ai_base_url}, user_id={user_id}")

            # Inject GitHub token for MCP GitHub server
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.github_token:
                os.environ["GITHUB_TOKEN"] = user.github_token
                print(f"[OK] Injected GITHUB_TOKEN for user {user.github_username}")
            else:
                print(f"[WARN] No GitHub token found for user_id={user_id}")

            # TODO: Inject other MCP server tokens (Azure DevOps, Railway, etc.)
            # from models.DeployProviderAuth table

        except ValueError:
            # Re-raise ValueError with user-friendly message
            raise
        except Exception as e:
            # Wrap other exceptions in ValueError with context
            raise ValueError(
                f"❌ Failed to inject environment variables: {type(e).__name__}: {e}. "
                "Please check your Settings configuration."
            )

        return ai_provider

    def _build_initial_state(
        self,
        request: schemas.GenerationRequest,
        project_id: str,
        user_id: int,
        ai_provider: str
    ) -> OrchestraState:
        """
        Build initial OrchestraState from user request.

        Args:
            request: Generation request from API
            project_id: Unique project identifier
            user_id: User ID
            ai_provider: AI provider name configured by user

        Returns:
            Initial state dict for LangGraph execution
        """
        requirements_text = self.generate_requirements_txt(request)

        state: OrchestraState = {
            # User input & metadata
            "requirements": requirements_text,
            "project_id": project_id,
            "user_id": str(user_id),
            "ai_provider": ai_provider,

            # Agent-produced data (will be populated during execution)
            "parsed_requirements": None,
            "design_yaml": None,
            "api_schema": None,
            "db_schema": None,
            "backend_code": None,
            "frontend_code": None,
            "devops_config": None,

            # Supporting systems
            "backlog_items": None,
            "rag_context": None,

            # Orchestration state
            "current_step": "start",
            "completed_steps": [],
            "agent_statuses": {},
            "errors": {},
        }

        return state

    def _load_knowledge_sources(self, db: Session, user_id: int) -> list:
        """
        Load user's configured knowledge sources from DB.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            List of instantiated KnowledgeSource objects
        """
        # TODO: Implement in Prompt 07 when knowledge agent is implemented
        # For now, return empty list
        return []

    def generate_requirements_txt(self, request: schemas.GenerationRequest) -> str:
        """
        Generate requirements text from user request.

        Args:
            request: Generation request

        Returns:
            Formatted requirements text
        """
        lines = [request.mvp_description, "", "Features:"]
        for feature in request.features:
            lines.append(f"- {feature}")
        lines.append("")
        if request.user_stories:
            lines.append("User stories:")
            for story in request.user_stories:
                lines.append(f"- {story}")
            lines.append("")
        lines += [
            "Technical:",
            f"- Frontend: {request.tech_stack.frontend}",
            f"- Backend: {request.tech_stack.backend}",
            f"- Database: {request.tech_stack.database}",
            f"- Deploy to: {request.tech_stack.deploy_platform}",
        ]
        return "\n".join(lines)

    def write_requirements_file(self, content: str) -> None:
        """Write requirements to file (for legacy compatibility)."""
        self.pipeline_data_dir.mkdir(parents=True, exist_ok=True)
        self.requirements_file.write_text(content, encoding="utf-8")
        print(f"[OK] Written requirements to: {self.requirements_file}")

    async def broadcast_progress(self, generation_id, step, step_number, percentage, message):
        """Broadcast progress update via WebSocket."""
        await manager.broadcast(generation_id, {
            "type": "progress",
            "step": step,
            "step_number": step_number,
            "percentage": percentage,
            "message": message,
        })

    def _map_event_to_step_info(self, event: dict) -> Optional[dict]:
        """
        Map LangGraph event to step info for WebSocket broadcast.

        Args:
            event: LangGraph stream event

        Returns:
            Step info dict or None if event should be ignored
        """
        # LangGraph events have structure: {node_name: {data}}
        # We care about when nodes complete (have output data)

        for node_name, node_data in event.items():
            if node_name in self.AGENT_TO_STEP and node_data:
                # Check if this node just completed (has updated state)
                if "completed_steps" in node_data and node_name in node_data["completed_steps"]:
                    return self.AGENT_TO_STEP[node_name]

        return None

    # ------------------------------------------------------------------
    # Main generation coroutine (LangGraph-based)
    # ------------------------------------------------------------------

    async def run_generation(
        self,
        generation_id: str,
        request: schemas.GenerationRequest,
        db: Session,
        user_id: int = None,
        existing_project_id: Optional[int] = None,  # NEW: for resume mode
        timeout_seconds: int = 1800  # 30 minutes default timeout
    ) -> Optional[int]:
        """
        Run LangGraph-based generation pipeline with WebSocket progress streaming.

        Args:
            generation_id: Unique generation session ID
            request: User's generation request
            db: Database session
            user_id: User ID (optional, for token injection)
            existing_project_id: Existing project ID for resume mode (optional)
            timeout_seconds: Maximum generation time in seconds (default 30 min)

        Returns:
            Project ID if successful, None if failed
        """
        project = None
        generation_attempt = 1

        try:
            # Wrap entire generation in timeout
            return await asyncio.wait_for(
                self._run_generation_internal(
                    generation_id, request, db, user_id, existing_project_id, generation_attempt
                ),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"Generation {generation_id} timed out after {timeout_seconds}s")
            if project:
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db, project_id=project.id,
                    step_name="error", status="failed",
                    message=f"Generation timed out after {timeout_seconds} seconds",
                    generation_attempt=generation_attempt
                )
            await self._close_websocket_gracefully(generation_id, 1011, "Generation timed out")
            return None
        except ValidationError as e:
            logger.error(f"Validation error in generation {generation_id}: {e}")
            if project:
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db, project_id=project.id,
                    step_name="error", status="failed",
                    message=f"Validation error: {str(e)[:500]}",
                    generation_attempt=generation_attempt
                )
            await self._close_websocket_gracefully(generation_id, 1011, "Validation error")
            return None
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception during generation {generation_id}:\n{tb}")
            if project:
                try:
                    crud.update_project_status(db, project.id, "failed")
                    crud.create_generation_log(
                        db=db, project_id=project.id,
                        step_name="error", status="failed",
                        message=tb[:500],
                        generation_attempt=generation_attempt
                    )
                    db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to save error state to DB: {db_error}")
                    db.rollback()
            await self._close_websocket_gracefully(generation_id, 1011, f"Internal error: {str(e)[:100]}")
            return None

    async def _run_generation_internal(
        self,
        generation_id: str,
        request: schemas.GenerationRequest,
        db: Session,
        user_id: Optional[int],
        existing_project_id: Optional[int],
        generation_attempt: int
    ) -> Optional[int]:
        """Internal generation logic without timeout wrapper."""
        project = None

        try:
            if existing_project_id:
                # Resume mode: use existing project
                project = crud.get_project_by_id(db, existing_project_id)
                if not project:
                    raise ValueError(f"Project {existing_project_id} not found")
                generation_attempt = project.generation_attempt
                # Don't recreate requirements, already exist
                # But still write requirements file for agents
                requirements = crud.get_project_requirements(db, existing_project_id)
                if requirements:
                    self.write_requirements_file(requirements.requirements_text)
            else:
                # New generation mode
                # Create project record
                project = crud.create_project(
                    db=db,
                    name=f"Generated App - {generation_id[:8]}",
                    description=request.mvp_description,
                    status="in_progress",
                    user_id=user_id
                )

                # Save requirements
                requirements_text = self.generate_requirements_txt(request)
                crud.create_project_requirement(
                    db=db,
                    project_id=project.id,
                    mvp_description=request.mvp_description,
                    features=request.features,
                    user_stories=request.user_stories,
                    tech_stack=request.tech_stack,
                    requirements_text=requirements_text,
                )
                self.write_requirements_file(requirements_text)

            # Log start
            crud.create_generation_log(
                db=db, project_id=project.id,
                step_name="start", status="started",
                message="Starting app generation with LangGraph",
                generation_attempt=generation_attempt
            )
            await self.broadcast_progress(generation_id, "start", 0, 0, "Starting app generation...")

            # Inject environment variables (tokens, config) and get user's AI provider
            ai_provider = "openai"  # Default
            try:
                if user_id:
                    ai_provider = self._inject_env_vars(db, user_id)
                else:
                    raise ValueError(
                        "❌ No user_id provided. Please log in with GitHub before starting generation."
                    )
            except ValueError as ve:
                # User-friendly configuration errors
                error_msg = str(ve)
                print(f"[ERROR] Configuration error: {error_msg}")
                await self.broadcast_progress(generation_id, "error", 0, 0, error_msg)
                raise

            # Build initial state
            initial_state = self._build_initial_state(request, str(project.id), user_id or 1, ai_provider)

            # Load knowledge sources
            # knowledge_sources = self._load_knowledge_sources(db, user_id or 1)
            # TODO: Pass knowledge_sources to knowledge_retrieval node in Prompt 07

            # Stream LangGraph execution
            current_step = "start"
            final_state = None

            print(f"[OK] Starting LangGraph execution for project {project.id}")

            async for event in langgraph_app.astream(
                initial_state,
                config={"configurable": {"thread_id": generation_id}}
            ):
                print(f"[LangGraph Event] {event.keys()}")

                # Map event to step info
                step_info = self._map_event_to_step_info(event)

                if step_info:
                    current_step = step_info["step"]
                    crud.create_generation_log(
                        db=db, project_id=project.id,
                        step_name=current_step, status="completed",
                        message=f"{current_step.capitalize()} step completed",
                        generation_attempt=generation_attempt
                    )
                    await self.broadcast_progress(
                        generation_id,
                        current_step,
                        step_info["step_number"],
                        step_info["percentage"],
                        f"{current_step.capitalize()} generation completed",
                    )

                # Store final state for error checking
                for node_name, node_data in event.items():
                    if isinstance(node_data, dict) and "errors" in node_data:
                        final_state = node_data

            print(f"[OK] LangGraph execution completed for project {project.id}")

            # Check for errors in final state
            if final_state and final_state.get("errors"):
                error_summary = ", ".join(
                    f"{agent}: {msg}" for agent, msg in final_state["errors"].items()
                )
                print(f"[ERROR] Generation failed with errors: {error_summary}")
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db, project_id=project.id,
                    step_name=current_step, status="failed",
                    message=error_summary[:500],
                    generation_attempt=generation_attempt
                )
                await self.broadcast_progress(
                    generation_id, "error", 0, 0,
                    f"Generation failed: {error_summary[:400]}"
                )
                return None

            # Success!
            crud.update_project_status(db, project.id, "completed")
            await self.broadcast_progress(
                generation_id, "complete", 7, 100,
                "App generation completed successfully!"
            )
            return project.id

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[ERROR] Exception during generation:\n{tb}")
            if project:
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db, project_id=project.id,
                    step_name="error", status="failed",
                    message=tb[:500],
                    generation_attempt=generation_attempt
                )
            await self.broadcast_progress(
                generation_id, "error", 0, 0, f"Exception: {str(e)}"
            )
            return None


def generate_id() -> str:
    """Generate unique generation session ID."""
    return str(uuid.uuid4())
