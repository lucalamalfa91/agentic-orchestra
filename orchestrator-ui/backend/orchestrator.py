"""
Orchestrator for running run_all_agents.py as a subprocess with progress tracking.
"""
import asyncio
import os
import sys
import uuid
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

try:
    from orchestrator_ui.backend import crud, schemas
    from orchestrator_ui.backend.websocket import manager
    from orchestrator_ui.backend.encryption_service import decrypt
except ModuleNotFoundError:
    import crud
    import schemas
    from websocket import manager
    from encryption_service import decrypt


class GenerationOrchestrator:
    """
    Manages the execution of run_all_agents.py and tracks progress.
    """

    STEP_MARKERS = {
        "README update completed": {"step": "readme", "step_number": 1, "percentage": 16},
        "Design completed": {"step": "design", "step_number": 2, "percentage": 33},
        "Backend completed": {"step": "backend", "step_number": 3, "percentage": 50},
        "Frontend completed": {"step": "frontend", "step_number": 4, "percentage": 67},
        "DevOps completed": {"step": "devops", "step_number": 5, "percentage": 83},
        "Publish completed": {"step": "publish", "step_number": 6, "percentage": 100},
    }

    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.pipeline_data_dir = project_root / "pipeline_data"
        self.requirements_file = self.pipeline_data_dir / "requirements.txt"

    def _build_subprocess_env(self, db: Session, user_id: int) -> dict:
        """
        Build the environment dict to pass to the subprocess.

        Reads the active AI Configuration from DB, decrypts the API key,
        and returns a copy of the current process env with the AI provider
        variables injected so that AI_agents/ai_utils.py can call the AI.

        Also injects GITHUB_TOKEN from the user record for the publish agent.
        Falls back to current process env if no config is found.
        """
        env = os.environ.copy()

        try:
            try:
                from orchestrator_ui.backend.models import Configuration, User
            except ModuleNotFoundError:
                from models import Configuration, User

            config = db.query(Configuration).filter(
                Configuration.user_id == user_id,
                Configuration.is_active == True
            ).first()

            if config:
                api_key = decrypt(config.ai_api_key_encrypted)
                env["ADESSO_BASE_URL"] = config.ai_base_url
                env["ADESSO_AI_HUB_KEY"] = api_key
                print(f"[OK] Injected AI config: ADESSO_BASE_URL={config.ai_base_url}")
            else:
                print("[WARN] No active AI config in DB for user, using .env fallback")

            user = db.query(User).filter(User.id == user_id).first()
            if user and user.github_token:
                env["GITHUB_TOKEN"] = user.github_token
                print(f"[OK] Injected GITHUB_TOKEN for user {user.github_username}")

        except Exception as e:
            print(f"[WARN] Could not inject AI config into subprocess env: {e}")
            print("[WARN] Subprocess will rely on .env values")

        return env

    def generate_requirements_txt(self, request: schemas.GenerationRequest) -> str:
        lines = []
        lines.append(request.mvp_description)
        lines.append("")
        lines.append("Features:")
        for feature in request.features:
            lines.append(f"- {feature}")
        lines.append("")
        if request.user_stories:
            lines.append("User stories:")
            for story in request.user_stories:
                lines.append(f"- {story}")
            lines.append("")
        lines.append("Technical:")
        lines.append(f"- Frontend: {request.tech_stack.frontend}")
        lines.append(f"- Backend: {request.tech_stack.backend}")
        lines.append(f"- Database: {request.tech_stack.database}")
        lines.append(f"- Deploy to: {request.tech_stack.deploy_platform}")
        return "\n".join(lines)

    def write_requirements_file(self, content: str) -> None:
        self.pipeline_data_dir.mkdir(parents=True, exist_ok=True)
        self.requirements_file.write_text(content, encoding="utf-8")
        print(f"[OK] Written requirements to: {self.requirements_file}")

    async def broadcast_progress(
        self,
        generation_id: str,
        step: str,
        step_number: int,
        percentage: int,
        message: str
    ):
        await manager.broadcast(generation_id, {
            "type": "progress",
            "step": step,
            "step_number": step_number,
            "percentage": percentage,
            "message": message
        })

    async def run_generation(
        self,
        generation_id: str,
        request: schemas.GenerationRequest,
        db: Session,
        user_id: int = None
    ) -> Optional[int]:
        """
        Run the full generation process.

        Args:
            generation_id: Unique generation ID for WebSocket tracking
            request: Generation request with requirements
            db: Database session
            user_id: ID of the requesting user (used to fetch AI config from DB)
        """
        project = None

        try:
            project = crud.create_project(
                db=db,
                name=f"Generated App - {generation_id[:8]}",
                description=request.mvp_description,
                status="in_progress"
            )

            requirements_text = self.generate_requirements_txt(request)
            crud.create_project_requirement(
                db=db,
                project_id=project.id,
                mvp_description=request.mvp_description,
                features=request.features,
                user_stories=request.user_stories,
                tech_stack=request.tech_stack,
                requirements_text=requirements_text
            )

            self.write_requirements_file(requirements_text)

            crud.create_generation_log(
                db=db,
                project_id=project.id,
                step_name="start",
                status="started",
                message="Starting app generation"
            )

            await self.broadcast_progress(
                generation_id=generation_id,
                step="start",
                step_number=0,
                percentage=0,
                message="Starting app generation..."
            )

            # Build env: inject AI config + GitHub token from DB into subprocess
            subprocess_env = (
                self._build_subprocess_env(db, user_id)
                if user_id is not None
                else os.environ.copy()
            )

            # Use sys.executable so the same virtualenv is used
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "run_all_agents.py",
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=subprocess_env
            )

            current_step = "start"
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line_text = line.decode("utf-8").strip()
                print(f"[STDOUT] {line_text}")

                for marker, step_info in self.STEP_MARKERS.items():
                    if marker in line_text:
                        current_step = step_info["step"]
                        crud.create_generation_log(
                            db=db,
                            project_id=project.id,
                            step_name=current_step,
                            status="completed",
                            message=f"{current_step.capitalize()} step completed"
                        )
                        await self.broadcast_progress(
                            generation_id=generation_id,
                            step=current_step,
                            step_number=step_info["step_number"],
                            percentage=step_info["percentage"],
                            message=f"{current_step.capitalize()} generation completed"
                        )

            await process.wait()

            if process.returncode == 0:
                crud.update_project_status(db, project.id, "completed")
                await self.broadcast_progress(
                    generation_id=generation_id,
                    step="complete",
                    step_number=7,
                    percentage=100,
                    message="App generation completed successfully!"
                )
                return project.id
            else:
                stderr = await process.stderr.read()
                error_message = stderr.decode("utf-8")
                print(f"[ERROR] Generation failed:\n{error_message}")
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db,
                    project_id=project.id,
                    step_name=current_step,
                    status="failed",
                    message=f"Generation failed: {error_message[:500]}"
                )
                await self.broadcast_progress(
                    generation_id=generation_id,
                    step="error",
                    step_number=0,
                    percentage=0,
                    message=f"Generation failed: {error_message[:200]}"
                )
                return None

        except Exception as e:
            print(f"[ERROR] Exception during generation: {e}")
            if project:
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db,
                    project_id=project.id,
                    step_name="error",
                    status="failed",
                    message=str(e)
                )
            await self.broadcast_progress(
                generation_id=generation_id,
                step="error",
                step_number=0,
                percentage=0,
                message=f"Error: {str(e)}"
            )
            return None


def generate_id() -> str:
    """Generate a unique ID for a generation."""
    return str(uuid.uuid4())
