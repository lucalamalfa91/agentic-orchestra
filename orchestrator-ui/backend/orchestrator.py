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
            # Use raw SQL to bypass SQLAlchemy metadata cache issue
            from sqlalchemy import text
            config_result = db.execute(
                text("SELECT ai_base_url, ai_api_key_encrypted, ai_provider, ai_model FROM configurations WHERE user_id = :user_id AND is_active = true LIMIT 1"),
                {"user_id": user_id}
            ).fetchone()

            if not config_result:
                raise ValueError(
                    f"❌ No AI configuration found for user_id={user_id}. "
                    "Please configure your AI provider in Settings before starting generation."
                )

            base_url, api_key_encrypted, ai_provider, ai_model = config_result
            ai_provider = ai_provider or "openai"  # Graceful fallback

            # Decrypt and validate API key
            try:
                api_key = decrypt(api_key_encrypted)
                if not api_key or len(api_key) < 10:
                    raise ValueError("Invalid or empty API key")
            except Exception as e:
                raise ValueError(
                    f"❌ Failed to decrypt API key: {e}. "
                    "Please re-configure your API key in Settings."
                )

            # Validate base_url
            if not base_url:
                raise ValueError(
                    f"❌ Missing base URL for AI provider '{ai_provider}'. "
                    "Please configure your base URL in Settings."
                )

            # Inject API key with correct env var name based on provider
            if ai_provider == "anthropic":
                os.environ["ANTHROPIC_API_KEY"] = api_key
                print(f"[DEBUG] Set ANTHROPIC_API_KEY = {api_key[:10]}...{api_key[-4:]}")

                # Validate Anthropic API key format
                if "anthropic.com" in base_url.lower() and not api_key.startswith("sk-ant-"):
                    print(f"[WARN] Using official Anthropic API but key doesn't start with 'sk-ant-'. "
                          f"This may cause authentication errors. "
                          f"Expected: sk-ant-api-xxx, Got: {api_key[:10]}...")

                # Set base_url if it's not default Anthropic
                if "anthropic.com" not in base_url.lower():
                    os.environ["ANTHROPIC_BASE_URL"] = base_url
                    print(f"[DEBUG] Set ANTHROPIC_BASE_URL = {base_url}")
                else:
                    print(f"[DEBUG] Using official Anthropic API (api.anthropic.com)")

            elif ai_provider == "openai" or ai_provider == "custom":
                # OpenAI, OpenAI-compatible, or Custom AI Hub (like LiteLLM, Adesso)
                os.environ["OPENAI_API_KEY"] = api_key
                print(f"[DEBUG] Set OPENAI_API_KEY = {api_key[:10]}...{api_key[-4:]}")

                # For custom providers, always set base URL
                # For OpenAI, only set if not official API
                if ai_provider == "custom" or "openai.com" not in base_url.lower():
                    os.environ["OPENAI_BASE_URL"] = base_url
                    print(f"[DEBUG] Set OPENAI_BASE_URL = {base_url}")
                    if ai_provider == "custom":
                        print(f"[INFO] Using custom AI hub/proxy: {base_url}")

            # Legacy support: also set ADESSO_* env vars for backwards compatibility
            os.environ["ADESSO_BASE_URL"] = base_url
            os.environ["ADESSO_AI_HUB_KEY"] = api_key

            # Inject user-selected model so llm_client.py picks it up via env var
            if ai_model:
                if ai_provider == "anthropic":
                    os.environ["ANTHROPIC_MODEL"] = ai_model
                else:
                    os.environ["OPENAI_MODEL"] = ai_model
                print(f"[OK] Injected AI_MODEL={ai_model} for provider={ai_provider}")
            else:
                # Clear any stale value from a previous generation
                os.environ.pop("ANTHROPIC_MODEL", None)
                os.environ.pop("OPENAI_MODEL", None)

            print(f"[OK] Injected AI config: provider={ai_provider}, model={ai_model or 'default'}, base_url={base_url}, user_id={user_id}")

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

    # Maps LangGraph node names → OrchestraState fields to persist after completion
    ARTIFACT_MAP = {
        "design":         ["design_yaml", "api_schema", "db_schema"],
        "backend_agent":  ["backend_code"],
        "frontend_agent": ["frontend_code"],
        "devops_agent":   ["devops_config"],
        "backlog_agent":  ["backlog_items"],
    }

    def _build_initial_state(
        self,
        request: schemas.GenerationRequest,
        project_id: str,
        user_id: int,
        ai_provider: str,
        saved_artifacts: dict = None,
    ) -> OrchestraState:
        """
        Build initial OrchestraState from user request.
        On resume, pre-populate state with saved artifact outputs so nodes
        that already completed can skip their LLM calls.
        """
        requirements_text = self.generate_requirements_txt(request)

        state: OrchestraState = {
            # User input & metadata
            "requirements": requirements_text,
            "project_id": project_id,
            "user_id": str(user_id),
            "ai_provider": ai_provider,

            # Agent-produced data — pre-loaded from DB when resuming
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

        # Restore previously-generated outputs so nodes can skip them
        if saved_artifacts:
            for key, value in saved_artifacts.items():
                if value is not None:
                    state[key] = value  # type: ignore[literal-required]
            logger.info(f"[orchestrator] Loaded saved artifacts: {list(saved_artifacts.keys())}")

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

    async def _close_websocket_gracefully(self, generation_id: str, code: int, reason: str):
        """Close WebSocket connection gracefully."""
        try:
            await manager.broadcast(generation_id, {
                "type": "error",
                "message": reason,
            })
        except Exception:
            pass

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

        With stream_mode="updates", each event is {node_name: node_output}.
        A node appearing as a key in the event means it just completed.
        We return the first matching tracked node found in the event.
        """
        for node_name, node_data in event.items():
            if node_name in self.AGENT_TO_STEP and node_data is not None:
                step_info = self.AGENT_TO_STEP[node_name]
                # Check if the node failed — if so, skip the "completed" broadcast
                if isinstance(node_data, dict):
                    node_errors = node_data.get("errors", {}) or {}
                    if node_errors.get(node_name):
                        logger.warning(f"[orchestrator] {node_name} reported error, skipping progress broadcast")
                        return None
                return step_info

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
        existing_project_id: Optional[int] = None,
        timeout_seconds: int = 1800
    ) -> Optional[int]:
        """
        Run LangGraph-based generation pipeline with WebSocket progress streaming.

        Returns:
            Project ID if successful, None if failed
        """
        # Shared context so the inner coroutine can expose project/attempt to the wrapper
        ctx: dict = {"project": None, "generation_attempt": 1}

        try:
            return await asyncio.wait_for(
                self._run_generation_internal(
                    generation_id, request, db, user_id, existing_project_id, ctx
                ),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            logger.error(f"Generation {generation_id} timed out after {timeout_seconds}s")
            project = ctx["project"]
            generation_attempt = ctx["generation_attempt"]
            if project:
                try:
                    crud.update_project_status(db, project.id, "failed")
                    crud.create_generation_log(
                        db=db, project_id=project.id,
                        step_name="error", status="failed",
                        message=f"Generation timed out after {timeout_seconds} seconds",
                        generation_attempt=generation_attempt
                    )
                    db.commit()
                except Exception as db_err:
                    logger.error("Failed to persist timeout state: %s", db_err)
                    db.rollback()
            await self._close_websocket_gracefully(generation_id, 1011, "Generation timed out")
            return None
        except ValidationError as e:
            logger.error(f"Validation error in generation {generation_id}: {e}")
            project = ctx["project"]
            generation_attempt = ctx["generation_attempt"]
            if project:
                try:
                    crud.update_project_status(db, project.id, "failed")
                    crud.create_generation_log(
                        db=db, project_id=project.id,
                        step_name="error", status="failed",
                        message="Validation error: " + str(e)[:500].replace("{", "{{").replace("}", "}}"),
                        generation_attempt=generation_attempt
                    )
                    db.commit()
                except Exception as db_err:
                    logger.error("Failed to persist validation error: %s", db_err)
                    db.rollback()
            await self._close_websocket_gracefully(generation_id, 1011, "Validation error")
            return None
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Exception during generation {generation_id}:\n{tb}")
            project = ctx["project"]
            generation_attempt = ctx["generation_attempt"]
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
                except Exception as db_err:
                    logger.error("Failed to save error state to DB: %s", db_err)
                    db.rollback()
            error_msg = str(e)[:100].replace("{", "{{").replace("}", "}}")
            await self._close_websocket_gracefully(generation_id, 1011, f"Internal error: {error_msg}")
            return None

    async def _run_generation_internal(
        self,
        generation_id: str,
        request: schemas.GenerationRequest,
        db: Session,
        user_id: Optional[int],
        existing_project_id: Optional[int],
        ctx: dict,
    ) -> Optional[int]:
        """Internal generation logic without timeout wrapper. Updates ctx['project'] and ctx['generation_attempt']."""
        project = None
        generation_attempt = 1

        try:
            if existing_project_id:
                # Resume mode: use existing project
                project = crud.get_project_by_id(db, existing_project_id)
                if not project:
                    raise ValueError(f"Project {existing_project_id} not found")
                generation_attempt = project.generation_attempt
                ctx["project"] = project
                ctx["generation_attempt"] = generation_attempt
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
                ctx["project"] = project
                ctx["generation_attempt"] = generation_attempt

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

            # Load saved artifacts for resume mode (empty dict for new generations)
            saved_artifacts = {}
            if existing_project_id:
                # generation_attempt is already the NEW attempt (incremented before resume call),
                # so artifacts from the previous run live under generation_attempt - 1.
                saved_artifacts = crud.get_project_artifacts(
                    db, existing_project_id, for_attempt=generation_attempt - 1
                )
                if saved_artifacts:
                    logger.info(f"[orchestrator] Resume: found saved artifacts for {list(saved_artifacts.keys())}")
                    await self.broadcast_progress(
                        generation_id, "resume_info", 0, 5,
                        f"Resuming: skipping {len(saved_artifacts)} already-completed step(s) "
                        f"({', '.join(saved_artifacts.keys())})",
                    )

            # Build initial state (pre-populated with saved artifacts on resume)
            initial_state = self._build_initial_state(
                request, str(project.id), user_id or 1, ai_provider, saved_artifacts
            )

            # Stream LangGraph execution
            current_step = "start"
            final_state = None

            print(f"[OK] Starting LangGraph execution for project {project.id}")

            async for event in langgraph_app.astream(
                initial_state,
                config={"configurable": {"thread_id": generation_id}},
                stream_mode="updates",
            ):
                print(f"[LangGraph Event] {list(event.keys())}")

                for node_name, node_data in event.items():
                    if not isinstance(node_data, dict):
                        continue

                    # Always track the latest node output as final_state candidate
                    final_state = node_data

                    # Persist artifacts to DB as each node completes
                    if node_name in self.ARTIFACT_MAP:
                        fields = {
                            f: node_data[f]
                            for f in self.ARTIFACT_MAP[node_name]
                            if node_data.get(f) is not None
                        }
                        if fields:
                            try:
                                crud.upsert_project_artifacts(
                                    db, project.id, generation_attempt, **fields
                                )
                                logger.info(f"[orchestrator] Saved artifacts for {node_name}: {list(fields.keys())}")
                            except Exception as ae:
                                logger.warning(f"[orchestrator] Failed to save artifacts for {node_name}: {ae}")

                # Map event to step info and broadcast progress
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

            print(f"[OK] LangGraph execution completed for project {project.id}")

            # Check for critical errors in final state
            # Non-critical failures (backlog, publish) are logged but don't block success
            CRITICAL_AGENTS = {"design", "backend_agent", "frontend_agent"}
            if final_state and final_state.get("errors"):
                all_errors = final_state["errors"]
                critical_errors = {a: m for a, m in all_errors.items() if m and a in CRITICAL_AGENTS}
                non_critical_errors = {a: m for a, m in all_errors.items() if m and a not in CRITICAL_AGENTS}

                if non_critical_errors:
                    logger.warning("[orchestrator] Non-critical agent errors (ignored): %s", list(non_critical_errors.keys()))

                if critical_errors:
                    error_summary = ", ".join(f"{a}: {m}" for a, m in critical_errors.items())
                    print(f"[ERROR] Critical agent failures: {error_summary}")
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
            tb = traceback.format_exc()
            print(f"[ERROR] Exception during generation:\n{tb}")
            if project:
                ctx["project"] = project
                ctx["generation_attempt"] = generation_attempt
                try:
                    crud.update_project_status(db, project.id, "failed")
                    crud.create_generation_log(
                        db=db, project_id=project.id,
                        step_name="error", status="failed",
                        message=tb[:500],
                        generation_attempt=generation_attempt
                    )
                    db.commit()
                except Exception as db_err:
                    logger.error("Failed to persist inner exception state: %s", db_err)
                    db.rollback()
            await self.broadcast_progress(
                generation_id, "error", 0, 0, "Exception: " + str(e).replace("{", "{{").replace("}", "}}")
            )
            return None


def generate_id() -> str:
    """Generate unique generation session ID."""
    return str(uuid.uuid4())
