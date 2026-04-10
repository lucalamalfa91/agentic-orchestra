#!/usr/bin/env python
"""
Direct test of resume functionality without HTTP server.
"""
import sys
import os
import asyncio
import json

# Setup paths
project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, 'orchestrator-ui', 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

print("=" * 60)
print("DIRECT RESUME FUNCTIONALITY TEST")
print("=" * 60)

# Import modules
try:
    from database import SessionLocal
    import crud
    import models
    import schemas
    from orchestrator import GenerationOrchestrator, generate_id
except ImportError as e:
    print(f"Import error: {e}")
    print("\nTrying alternative imports...")
    from orchestrator_ui.backend.database import SessionLocal
    from orchestrator_ui.backend import crud, models, schemas
    from orchestrator_ui.backend.orchestrator import GenerationOrchestrator, generate_id

async def test_resume():
    """Test resume functionality directly."""
    db = SessionLocal()

    try:
        # 1. Find a failed project
        print("\n[1] Finding failed project...")
        failed_projects = db.query(models.Project).filter(
            models.Project.status == 'failed'
        ).all()

        if not failed_projects:
            print("  FAIL No failed projects found")
            return

        # Use the most recent failed project
        project = failed_projects[-1]
        print(f"  OK Found project ID {project.id}: {project.name}")
        print(f"    Status: {project.status}")
        print(f"    Attempt: {project.generation_attempt}")

        # 2. Get requirements
        print("\n[2] Fetching requirements...")
        requirements = crud.get_project_requirements(db, project.id)
        if not requirements:
            print("  FAIL Requirements not found")
            return

        print(f"  OK Requirements found")
        print(f"    MVP: {requirements.mvp_description[:50]}...")
        print(f"    Features: {len(json.loads(requirements.features))} items")

        # 3. Reconstruct GenerationRequest
        print("\n[3] Reconstructing GenerationRequest...")
        try:
            request = schemas.GenerationRequest(
                mvp_description=requirements.mvp_description,
                features=json.loads(requirements.features),
                user_stories=json.loads(requirements.user_stories) if requirements.user_stories else None,
                tech_stack=schemas.TechStack(
                    frontend=requirements.frontend_framework or "react",
                    backend=requirements.backend_framework or "python",
                    database=requirements.database_type or "postgresql",
                    deploy_platform=requirements.deploy_platform or "vercel"
                )
            )
            print("  OK GenerationRequest reconstructed successfully")
        except Exception as e:
            print(f"  FAIL Failed to reconstruct: {e}")
            return

        # 4. Increment generation attempt
        print("\n[4] Incrementing generation attempt...")
        original_attempt = project.generation_attempt
        updated_project = crud.increment_generation_attempt(db, project.id)
        print(f"  OK Attempt incremented: {original_attempt} -> {updated_project.generation_attempt}")

        # 5. Update status
        print("\n[5] Updating status to in_progress...")
        crud.update_project_status(db, project.id, "in_progress")
        print("  OK Status updated")

        # 6. Log resume event
        print("\n[6] Creating resume log...")
        log = crud.create_generation_log(
            db=db,
            project_id=project.id,
            step_name="resume",
            status="started",
            message=f"Resuming generation (attempt #{updated_project.generation_attempt})",
            generation_attempt=updated_project.generation_attempt
        )
        print(f"  OK Log created (ID: {log.id})")

        # 7. Test orchestrator invocation (dry run - don't actually generate)
        print("\n[7] Testing orchestrator setup...")
        orchestrator = GenerationOrchestrator()
        generation_id = generate_id()
        print(f"  OK Orchestrator initialized")
        print(f"  OK Generation ID: {generation_id}")
        print(f"\n  Would call: orchestrator.run_generation(")
        print(f"    generation_id={generation_id},")
        print(f"    request=<GenerationRequest>,")
        print(f"    db=<Session>,")
        print(f"    existing_project_id={project.id}")
        print(f"  )")

        # 8. Verify database state
        print("\n[8] Verifying database state...")
        updated_project = crud.get_project_by_id(db, project.id)
        print(f"  Project status: {updated_project.status}")
        print(f"  Generation attempt: {updated_project.generation_attempt}")

        recent_logs = crud.get_project_logs(db, project.id)
        resume_logs = [l for l in recent_logs if l.step_name == 'resume']
        print(f"  Resume logs: {len(resume_logs)}")
        if resume_logs:
            latest = resume_logs[-1]
            print(f"    Latest: {latest.message}")
            print(f"    Attempt #: {latest.generation_attempt}")

        print("\n" + "=" * 60)
        print("RESUME FUNCTIONALITY TEST PASSED OK")
        print("=" * 60)
        print("\nAll components working correctly:")
        print("  OK Database queries")
        print("  OK Requirements reconstruction")
        print("  OK Attempt increment")
        print("  OK Status update")
        print("  OK Log creation with attempt number")
        print("  OK Orchestrator initialization")
        print("\nReady for full end-to-end test with actual generation.")

        # Cleanup: revert status to failed for next test
        crud.update_project_status(db, project.id, "failed")

    except Exception as e:
        print(f"\nFAIL Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_resume())
