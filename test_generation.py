"""
Test script to debug generation execution.
"""
import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
env_path = project_root / '.env'
load_dotenv(env_path)
print(f"[DEBUG] Loaded .env from: {env_path}")
print(f"[DEBUG] ADESSO_BASE_URL: {os.getenv('ADESSO_BASE_URL')}")
print(f"[DEBUG] ADESSO_AI_HUB_KEY: {os.getenv('ADESSO_AI_HUB_KEY', 'NOT SET')[:20]}...")

async def test_generation():
    print("=" * 80)
    print("TEST GENERATION DEBUG")
    print("=" * 80)

    try:
        # Change to backend directory for imports
        import os
        os.chdir('orchestrator-ui/backend')
        sys.path.insert(0, os.getcwd())

        # Import with relative imports
        from database import SessionLocal, init_db
        import schemas
        from orchestrator import GenerationOrchestrator

        print("\n[OK] Imports successful")

        # Initialize DB
        init_db()
        print("[OK] Database initialized")

        # Create orchestrator
        orchestrator = GenerationOrchestrator()
        print("[OK] Orchestrator created")

        # Create test request
        request = schemas.GenerationRequest(
            mvp_description="Simple test app",
            features=["Feature 1", "Feature 2"],
            user_stories=None,
            tech_stack=schemas.TechStack(
                frontend="react",
                backend="node",
                database="none",
                deploy_platform="vercel"
            )
        )
        print("[OK] Request created")

        # Create DB session
        db = SessionLocal()
        print("[OK] DB session created")

        # Run generation
        print("\n[START] Starting generation...")
        print("-" * 80)

        generation_id = "test-debug-001"
        user_id = 1

        project_id = await orchestrator.run_generation(
            generation_id=generation_id,
            request=request,
            db=db,
            user_id=user_id
        )

        print("-" * 80)
        if project_id:
            print(f"[SUCCESS] Generation completed! Project ID: {project_id}")
        else:
            print("[FAILED] Generation failed (returned None)")

        db.close()

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    print("\nRunning test generation...")
    success = asyncio.run(test_generation())
    sys.exit(0 if success else 1)
