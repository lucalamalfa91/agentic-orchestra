"""
Orchestrator for running run_all_agents.py as a subprocess with progress tracking.

Windows note: asyncio.create_subprocess_exec does NOT work on Windows with
SelectorEventLoop (uvicorn default). We use subprocess.Popen in a thread
(asyncio.to_thread) and communicate progress back to the async layer via
an asyncio.Queue.
"""
import asyncio
import os
import queue
import subprocess
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

    STEP_MARKERS = {
        "README update completed": {"step": "readme",   "step_number": 1, "percentage": 16},
        "Design completed":        {"step": "design",   "step_number": 2, "percentage": 33},
        "Backend completed":       {"step": "backend",  "step_number": 3, "percentage": 50},
        "Frontend completed":      {"step": "frontend", "step_number": 4, "percentage": 67},
        "DevOps completed":        {"step": "devops",   "step_number": 5, "percentage": 83},
        "Publish completed":       {"step": "publish",  "step_number": 6, "percentage": 100},
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

    def _build_subprocess_env(self, db: Session, user_id: int) -> dict:
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
        return env

    def generate_requirements_txt(self, request: schemas.GenerationRequest) -> str:
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
        self.pipeline_data_dir.mkdir(parents=True, exist_ok=True)
        self.requirements_file.write_text(content, encoding="utf-8")
        print(f"[OK] Written requirements to: {self.requirements_file}")

    async def broadcast_progress(self, generation_id, step, step_number, percentage, message):
        await manager.broadcast(generation_id, {
            "type": "progress",
            "step": step,
            "step_number": step_number,
            "percentage": percentage,
            "message": message,
        })

    # ------------------------------------------------------------------
    # Subprocess runner (thread-safe, works on Windows)
    # ------------------------------------------------------------------

    def _run_subprocess_in_thread(
        self,
        env: dict,
        line_queue: queue.Queue,
    ) -> int:
        """
        Run run_all_agents.py synchronously in a worker thread.
        Each stdout/stderr line is pushed to line_queue as a tuple:
          ('out', text) or ('err', text)
        A sentinel ('done', returncode) is pushed when the process exits.
        This approach works on Windows with any asyncio event loop policy.
        """
        import threading

        proc = subprocess.Popen(
            [sys.executable, "run_all_agents.py"],
            cwd=str(self.project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        def drain(stream, tag):
            for line in stream:
                line_queue.put((tag, line.rstrip()))
            stream.close()

        t_out = threading.Thread(target=drain, args=(proc.stdout, "out"), daemon=True)
        t_err = threading.Thread(target=drain, args=(proc.stderr, "err"), daemon=True)
        t_out.start()
        t_err.start()
        t_out.join()
        t_err.join()
        proc.wait()
        line_queue.put(("done", proc.returncode))
        return proc.returncode

    # ------------------------------------------------------------------
    # Main generation coroutine
    # ------------------------------------------------------------------

    async def run_generation(
        self,
        generation_id: str,
        request: schemas.GenerationRequest,
        db: Session,
        user_id: int = None,
    ) -> Optional[int]:
        project = None

        try:
            project = crud.create_project(
                db=db,
                name=f"Generated App - {generation_id[:8]}",
                description=request.mvp_description,
                status="in_progress",
            )
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
            crud.create_generation_log(
                db=db, project_id=project.id,
                step_name="start", status="started",
                message="Starting app generation",
            )
            await self.broadcast_progress(generation_id, "start", 0, 0, "Starting app generation...")

            subprocess_env = (
                self._build_subprocess_env(db, user_id) if user_id else os.environ.copy()
            )

            # asyncio.Queue bridges the worker thread -> async world
            line_q: asyncio.Queue = asyncio.Queue()
            sync_q: queue.Queue = queue.Queue()
            loop = asyncio.get_event_loop()

            # Forward from sync queue to async queue on the event loop
            def _forward():
                self._run_subprocess_in_thread(subprocess_env, sync_q)

            # Bridge: polls sync_q and puts items into async line_q
            async def _bridge():
                while True:
                    try:
                        item = await asyncio.to_thread(sync_q.get, True, 0.05)
                        await line_q.put(item)
                        if item[0] == "done":
                            break
                    except queue.Empty:
                        continue

            # Run subprocess in thread, bridge results to async queue
            subprocess_task = asyncio.create_task(
                asyncio.to_thread(self._run_subprocess_in_thread, subprocess_env, sync_q)
            )
            bridge_task = asyncio.create_task(_bridge())

            current_step = "start"
            stderr_lines = []
            returncode = 1

            # Consume the async queue while both tasks run
            while True:
                tag, value = await line_q.get()

                if tag == "out":
                    print(f"[STDOUT] {value}")
                    for marker, step_info in self.STEP_MARKERS.items():
                        if marker in value:
                            current_step = step_info["step"]
                            crud.create_generation_log(
                                db=db, project_id=project.id,
                                step_name=current_step, status="completed",
                                message=f"{current_step.capitalize()} step completed",
                            )
                            await self.broadcast_progress(
                                generation_id,
                                current_step,
                                step_info["step_number"],
                                step_info["percentage"],
                                f"{current_step.capitalize()} generation completed",
                            )

                elif tag == "err":
                    print(f"[STDERR] {value}")
                    stderr_lines.append(value)

                elif tag == "done":
                    returncode = value
                    break

            await subprocess_task  # ensure thread is finished
            bridge_task.cancel()

            stderr_full = "\n".join(stderr_lines)

            if returncode == 0:
                crud.update_project_status(db, project.id, "completed")
                await self.broadcast_progress(
                    generation_id, "complete", 7, 100,
                    "App generation completed successfully!"
                )
                return project.id
            else:
                error_summary = (
                    stderr_full[-1000:] if stderr_full
                    else f"Process exited with code {returncode} (no stderr captured)"
                )
                print(f"[ERROR] Generation failed (rc={returncode}):\n{error_summary}")
                crud.update_project_status(db, project.id, "failed")
                crud.create_generation_log(
                    db=db, project_id=project.id,
                    step_name=current_step, status="failed",
                    message=f"rc={returncode}: {error_summary[:500]}",
                )
                await self.broadcast_progress(
                    generation_id, "error", 0, 0,
                    f"[rc={returncode}] {error_summary[:400]}"
                )
                return None

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
                )
            await self.broadcast_progress(
                generation_id, "error", 0, 0, f"Exception: {str(e)}"
            )
            return None


def generate_id() -> str:
    return str(uuid.uuid4())
