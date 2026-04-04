"""
Orchestrator for running run_all_agents.py as a subprocess with progress tracking.
"""
import asyncio
import subprocess
import re
import uuid
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

try:
    from orchestrator_ui.backend import crud, schemas
    from orchestrator_ui.backend.websocket import manager
except ModuleNotFoundError:
    import crud
    import schemas
    from websocket import manager


class GenerationOrchestrator:
    """
    Manages the execution of run_all_agents.py and tracks progress.
    """

    # Map step markers to progress percentages
    STEP_MARKERS = {
        "README update completed": {"step": "readme", "step_number": 1, "percentage": 16},
        "Design completed": {"step": "design", "step_number": 2, "percentage": 33},
        "Backend completed": {"step": "backend", "step_number": 3, "percentage": 50},
        "Frontend completed": {"step": "frontend", "step_number": 4, "percentage": 67},
        "DevOps completed": {"step": "devops", "step_number": 5, "percentage": 83},
        "Publish completed": {"step": "publish", "step_number": 6, "percentage": 100},
    }

    def __init__(self, project_root: Path = None):
        """
        Initialize orchestrator.

        Args:
            project_root: Root directory of agentic-orchestra project
        """
        if project_root is None:
            # Assume we're in orchestrator-ui/backend, go up 2 levels
            project_root = Path(__file__).parent.parent.parent
        self.project_root = project_root
        self.pipeline_data_dir = project_root / "pipeline_data"
        self.requirements_file = self.pipeline_data_dir / "requirements.txt"

    def generate_requirements_txt(
        self,
        request: schemas.GenerationRequest
    ) -> str:
        """
        Generate requirements.txt content from GenerationRequest.

        Args:
            request: Generation request with MVP description, features, tech stack

        Returns:
            Generated requirements.txt content
        """
        lines = []

        # MVP Description
        lines.append(request.mvp_description)
        lines.append("")

        # Features
        lines.append("Features:")
        for feature in request.features:
            lines.append(f"- {feature}")
        lines.append("")

        # User Stories (optional)
        if request.user_stories:
            lines.append("User stories:")
            for story in request.user_stories:
                lines.append(f"- {story}")
            lines.append("")

        # Technical Requirements
        lines.append("Technical:")
        lines.append(f"- Frontend: {request.tech_stack.frontend}")
        lines.append(f"- Backend: {request.tech_stack.backend}")
        lines.append(f"- Database: {request.tech_stack.database}")
        lines.append(f"- Deploy to: {request.tech_stack.deploy_platform}")

        return "\n".join(lines)

    def write_requirements_file(self, content: str) -> None:
        """
        Write requirements.txt to pipeline_data directory.

        Args:
            content: Requirements text content
        """
        # Ensure directory exists
        self.pipeline_data_dir.mkdir(parents=True, exist_ok=True)

        # Write file
        self.requirements_file.write_text(content, encoding="utf-8")
        print(f"✅ Written requirements to: {self.requirements_file}")

    async def broadcast_progress(
        self,
        generation_id: str,
        step: str,
        step_number: int,
        percentage: int,
        message: str
    ):
        """
        Broadcast progress update via WebSocket.

        Args:
            generation_id: Unique generation ID
            step: Step name (readme, design, backend, etc.)
            step_number: Step number (1-6)
            percentage: Completion percentage (0-100)
            message: Progress message
        """
        progress_message = {
            "type": "progress",
            "step": step,
            "step_number": step_number,
            "percentage": percentage,
            "message": message
        }
        await manager.broadcast(generation_id, progress_message)

    async def run_generation(
        self,
        generation_id: str,
        request: schemas.GenerationRequest,
        db: Session
    ) -> Optional[int]:
        """
        Run the full generation process.

        Args:
            generation_id: Unique generation ID for WebSocket tracking
            request: Generation request with requirements
            db: Database session

        Returns:
            Project ID if successful, None if failed
        """
        project = None

        try:
            # Create project in database
            project = crud.create_project(
                db=db,
                name=f"Generated App - {generation_id[:8]}",
                description=request.mvp_description,
                status="in_progress"
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
                requirements_text=requirements_text
            )

            # Write requirements file
            self.write_requirements_file(requirements_text)

            # Log start
            crud.create_generation_log(
                db=db,
                project_id=project.id,
                step_name="start",
                status="started",
                message="Starting app generation"
            )

            # Broadcast initial progress
            await self.broadcast_progress(
                generation_id=generation_id,
                step="start",
                step_number=0,
                percentage=0,
                message="Starting app generation..."
            )

            # Run run_all_agents.py as subprocess
            process = await asyncio.create_subprocess_exec(
                "python",
                "run_all_agents.py",
                cwd=str(self.project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Track progress by parsing stdout
            current_step = "start"
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                line_text = line.decode("utf-8").strip()
                print(f"[STDOUT] {line_text}")

                # Check for step completion markers
                for marker, step_info in self.STEP_MARKERS.items():
                    if marker in line_text:
                        current_step = step_info["step"]

                        # Log step completion
                        crud.create_generation_log(
                            db=db,
                            project_id=project.id,
                            step_name=current_step,
                            status="completed",
                            message=f"{current_step.capitalize()} step completed"
                        )

                        # Broadcast progress
                        await self.broadcast_progress(
                            generation_id=generation_id,
                            step=current_step,
                            step_number=step_info["step_number"],
                            percentage=step_info["percentage"],
                            message=f"{current_step.capitalize()} generation completed"
                        )

            # Wait for process to complete
            await process.wait()

            if process.returncode == 0:
                # Success!
                crud.update_project_status(db, project.id, "completed")

                # Broadcast completion
                await self.broadcast_progress(
                    generation_id=generation_id,
                    step="complete",
                    step_number=7,
                    percentage=100,
                    message="App generation completed successfully!"
                )

                return project.id
            else:
                # Failed
                stderr = await process.stderr.read()
                error_message = stderr.decode("utf-8")
                print(f"❌ Generation failed: {error_message}")

                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db,
                    project_id=project.id,
                    step_name=current_step,
                    status="failed",
                    message=f"Generation failed: {error_message[:500]}"
                )

                # Broadcast error
                await self.broadcast_progress(
                    generation_id=generation_id,
                    step="error",
                    step_number=0,
                    percentage=0,
                    message=f"Generation failed: {error_message[:200]}"
                )

                return None

        except Exception as e:
            print(f"❌ Exception during generation: {e}")

            if project:
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db,
                    project_id=project.id,
                    step_name="error",
                    status="failed",
                    message=str(e)
                )

            # Broadcast error
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
