#!/usr/bin/env python
"""
Full end-to-end generation test.
Tests the complete pipeline from requirements to completion.
"""
import sys
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup paths
project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, 'orchestrator-ui', 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

print("=" * 60)
print("FULL END-TO-END GENERATION TEST")
print("=" * 60)

# Import modules
from database import SessionLocal
import crud
import schemas
from orchestrator import GenerationOrchestrator, generate_id

async def test_full_generation():
    """Run a complete generation from scratch."""
    db = SessionLocal()

    try:
        # 1. Create generation request
        print("\n[1] Creating generation request...")
        request = schemas.GenerationRequest(
            mvp_description="A simple task manager app with user authentication",
            features=[
                "User registration and login",
                "Create, edit, and delete tasks",
                "Mark tasks as complete",
                "Filter tasks by status"
            ],
            user_stories=[
                "As a user, I want to create an account so I can save my tasks",
                "As a user, I want to create tasks so I can track my work",
                "As a user, I want to mark tasks as complete so I can track progress"
            ],
            tech_stack=schemas.TechStack(
                frontend="react",
                backend="python",
                database="postgresql",
                deploy_platform="vercel"
            )
        )
        print(f"  OK Request created:")
        print(f"    MVP: {request.mvp_description[:50]}...")
        print(f"    Features: {len(request.features)} items")
        print(f"    Tech: {request.tech_stack.backend}/{request.tech_stack.frontend}")

        # 2. Initialize orchestrator
        print("\n[2] Initializing orchestrator...")
        orchestrator = GenerationOrchestrator()
        generation_id = generate_id()
        print(f"  OK Orchestrator initialized")
        print(f"  OK Generation ID: {generation_id}")

        # 3. Run generation
        print("\n[3] Starting generation pipeline...")
        print("  This will take several minutes...")
        print("  Press Ctrl+C to cancel")
        print()

        project_id = await orchestrator.run_generation(
            generation_id=generation_id,
            request=request,
            db=db,
            user_id=None  # No user for this test
        )

        # 4. Check result
        print("\n[4] Checking generation result...")
        if project_id:
            project = crud.get_project_by_id(db, project_id)
            print(f"  OK Project created: ID {project.id}")
            print(f"    Name: {project.name}")
            print(f"    Status: {project.status}")
            print(f"    Attempt: {project.generation_attempt}")
            print(f"    GitHub: {project.github_repo_url or 'N/A'}")

            # Get logs
            logs = crud.get_project_logs(db, project_id)
            print(f"\n  Generation logs: {len(logs)} entries")
            completed_steps = [l.step_name for l in logs if l.status == 'completed']
            failed_steps = [l.step_name for l in logs if l.status == 'failed']

            print(f"    Completed steps: {', '.join(completed_steps) if completed_steps else 'none'}")
            if failed_steps:
                print(f"    Failed steps: {', '.join(failed_steps)}")

            # Final status
            if project.status == 'completed':
                print("\n" + "=" * 60)
                print("GENERATION COMPLETED SUCCESSFULLY!")
                print("=" * 60)
                print(f"\nProject ID: {project.id}")
                print(f"GitHub URL: {project.github_repo_url}")
                print("\nAll steps executed successfully.")
            elif project.status == 'failed':
                print("\n" + "=" * 60)
                print("GENERATION FAILED")
                print("=" * 60)
                print("\nThis is expected if there are missing API keys or configuration.")
                print("The resume functionality can now be tested on this failed project.")
                print(f"\nTo test resume:")
                print(f"  python test_resume_direct.py")
                print(f"\nOr via API (if server running):")
                print(f"  curl -X POST http://localhost:9000/api/projects/{project.id}/resume")
            else:
                print(f"\nGeneration status: {project.status}")

        else:
            print("  FAIL No project was created")

    except KeyboardInterrupt:
        print("\n\nGeneration cancelled by user.")
    except Exception as e:
        print(f"\nFAIL Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\nWARNING: This will start a full generation pipeline.")
    print("Make sure you have:")
    print("  - Valid API keys in .env file")
    print("  - GitHub token configured")
    print("  - All dependencies installed")
    print()

    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(test_full_generation())
    else:
        print("Test cancelled.")
