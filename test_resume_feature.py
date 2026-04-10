#!/usr/bin/env python
"""
Test script for resume capability implementation.

Tests:
1. State conflict fix (backlog_items reducer)
2. Database schema (generation_attempt columns)
3. Backend CRUD functions
4. Resume API endpoint
5. Orchestrator resume mode
"""
import sys
import os

# Add both paths to allow imports
project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, 'orchestrator-ui', 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

# Import with fallback
try:
    from orchestrator_ui.backend.database import SessionLocal
    from orchestrator_ui.backend import crud, models, schemas
except ModuleNotFoundError:
    from database import SessionLocal
    import crud
    import models
    import schemas

from AI_agents.graph.state import OrchestraState
from typing import get_type_hints, get_origin, get_args
import operator

print("=" * 60)
print("RESUME CAPABILITY TEST SUITE")
print("=" * 60)

# Test 1: State Conflict Fix
print("\n[Test 1] Checking LangGraph state reducers...")
try:
    hints = get_type_hints(OrchestraState, include_extras=True)

    # Check backlog_items has Annotated reducer
    backlog_type = hints.get('backlog_items')
    if backlog_type and get_origin(backlog_type) is not None:
        args = get_args(backlog_type)
        if len(args) > 1 and args[1] == operator.add:
            print("✓ backlog_items has operator.add reducer")
        else:
            print("✗ backlog_items missing reducer annotation")
    else:
        print("✗ backlog_items type annotation incorrect")

    # Check rag_context has Annotated reducer
    rag_type = hints.get('rag_context')
    if rag_type and get_origin(rag_type) is not None:
        args = get_args(rag_type)
        if len(args) > 1 and args[1] == operator.add:
            print("✓ rag_context has operator.add reducer")
        else:
            print("✗ rag_context missing reducer annotation")
    else:
        print("✗ rag_context type annotation incorrect")

except Exception as e:
    print(f"✗ State annotation check failed: {e}")

# Test 2: Database Schema
print("\n[Test 2] Checking database schema...")
try:
    db = SessionLocal()

    # Check Project table has generation_attempt
    project_columns = models.Project.__table__.columns.keys()
    if 'generation_attempt' in project_columns:
        print("✓ projects table has generation_attempt column")
    else:
        print("✗ projects table missing generation_attempt column")

    # Check GenerationLog table has generation_attempt
    log_columns = models.GenerationLog.__table__.columns.keys()
    if 'generation_attempt' in log_columns:
        print("✓ generation_logs table has generation_attempt column")
    else:
        print("✗ generation_logs table missing generation_attempt column")

    db.close()
except Exception as e:
    print(f"✗ Database schema check failed: {e}")

# Test 3: CRUD Functions
print("\n[Test 3] Testing CRUD functions...")
try:
    db = SessionLocal()

    # Create test project
    test_project = crud.create_project(
        db=db,
        name="Test Resume Project",
        description="Test project for resume functionality",
        status="failed"
    )
    print(f"✓ Created test project with ID: {test_project.id}")

    # Check default generation_attempt is 1
    if test_project.generation_attempt == 1:
        print("✓ Default generation_attempt is 1")
    else:
        print(f"✗ Default generation_attempt is {test_project.generation_attempt}, expected 1")

    # Test increment_generation_attempt
    updated_project = crud.increment_generation_attempt(db, test_project.id)
    if updated_project.generation_attempt == 2:
        print("✓ increment_generation_attempt() works correctly")
    else:
        print(f"✗ increment_generation_attempt() failed: attempt is {updated_project.generation_attempt}")

    # Test create_generation_log with generation_attempt
    log = crud.create_generation_log(
        db=db,
        project_id=test_project.id,
        step_name="test_step",
        status="completed",
        message="Test log entry",
        generation_attempt=2
    )
    if log.generation_attempt == 2:
        print("✓ create_generation_log() accepts generation_attempt parameter")
    else:
        print(f"✗ Log generation_attempt is {log.generation_attempt}, expected 2")

    # Cleanup
    crud.delete_project(db, test_project.id)
    print("✓ Cleaned up test project")

    db.close()
except Exception as e:
    print(f"✗ CRUD functions test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Resume API Endpoint (Import Check)
print("\n[Test 4] Checking resume API endpoint...")
try:
    try:
        from orchestrator_ui.backend.api import projects
    except ModuleNotFoundError:
        from api import projects

    # Check if resume_generation endpoint exists
    if hasattr(projects, 'resume_generation'):
        print("✓ resume_generation endpoint exists in projects router")
    else:
        # Check in router
        router = projects.router
        resume_exists = False
        for route in router.routes:
            if hasattr(route, 'path') and 'resume' in route.path:
                resume_exists = True
                break

        if resume_exists:
            print("✓ /resume endpoint registered in router")
        else:
            print("✗ /resume endpoint not found")

except Exception as e:
    print(f"✗ API endpoint check failed: {e}")

# Test 5: Orchestrator Resume Mode (Signature Check)
print("\n[Test 5] Checking orchestrator resume support...")
try:
    try:
        from orchestrator_ui.backend.orchestrator import GenerationOrchestrator
    except ModuleNotFoundError:
        from orchestrator import GenerationOrchestrator

    import inspect

    # Check run_generation signature
    sig = inspect.signature(GenerationOrchestrator.run_generation)
    params = sig.parameters

    if 'existing_project_id' in params:
        print("✓ run_generation() accepts existing_project_id parameter")

        # Check if it's Optional
        param = params['existing_project_id']
        if param.default is not inspect.Parameter.empty:
            print("✓ existing_project_id parameter is optional")
        else:
            print("✗ existing_project_id parameter should be optional")
    else:
        print("✗ run_generation() missing existing_project_id parameter")

except Exception as e:
    print(f"✗ Orchestrator check failed: {e}")

# Test 6: Pydantic Schemas
print("\n[Test 6] Checking Pydantic schemas...")
try:
    try:
        from orchestrator_ui.backend.schemas import ProjectResponse, GenerationLogResponse
    except ModuleNotFoundError:
        import schemas
        ProjectResponse = schemas.ProjectResponse
        GenerationLogResponse = schemas.GenerationLogResponse

    # Check ProjectResponse
    project_fields = ProjectResponse.model_fields.keys()
    if 'generation_attempt' in project_fields:
        print("✓ ProjectResponse includes generation_attempt field")
    else:
        print("✗ ProjectResponse missing generation_attempt field")

    # Check GenerationLogResponse
    log_fields = GenerationLogResponse.model_fields.keys()
    if 'generation_attempt' in log_fields:
        print("✓ GenerationLogResponse includes generation_attempt field")
    else:
        print("✗ GenerationLogResponse missing generation_attempt field")

except Exception as e:
    print(f"✗ Pydantic schema check failed: {e}")

print("\n" + "=" * 60)
print("TEST SUITE COMPLETED")
print("=" * 60)
print("\nTo fully test the resume feature:")
print("1. Start the backend: cd orchestrator-ui/backend && python main.py")
print("2. Create a failed project via the UI")
print("3. Click 'Resume Generation' button on the failed project card")
print("4. Verify the generation restarts with incremented attempt number")
