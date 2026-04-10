#!/usr/bin/env python
"""Simple verification script for resume capability (no Unicode output)."""
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, 'orchestrator-ui', 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_dir)

print("=" * 60)
print("RESUME CAPABILITY VERIFICATION")
print("=" * 60)

# Test 1: State annotations
print("\n[1] LangGraph state reducers:")
try:
    from AI_agents.graph.state import OrchestraState
    from typing import get_type_hints
    hints = get_type_hints(OrchestraState, include_extras=True)
    print("    backlog_items type:", hints.get('backlog_items'))
    print("    rag_context type:", hints.get('rag_context'))
    print("    [OK] State annotations present")
except Exception as e:
    print(f"    [FAIL] {e}")

# Test 2: Database schema
print("\n[2] Database schema:")
try:
    try:
        from orchestrator_ui.backend import models
    except:
        import models

    project_cols = models.Project.__table__.columns.keys()
    log_cols = models.GenerationLog.__table__.columns.keys()

    if 'generation_attempt' in project_cols:
        print("    [OK] projects.generation_attempt exists")
    else:
        print("    [FAIL] projects.generation_attempt missing")

    if 'generation_attempt' in log_cols:
        print("    [OK] generation_logs.generation_attempt exists")
    else:
        print("    [FAIL] generation_logs.generation_attempt missing")
except Exception as e:
    print(f"    [FAIL] {e}")

# Test 3: CRUD functions
print("\n[3] CRUD functions:")
try:
    try:
        from orchestrator_ui.backend import crud
    except:
        import crud

    if hasattr(crud, 'increment_generation_attempt'):
        print("    [OK] increment_generation_attempt() exists")
    else:
        print("    [FAIL] increment_generation_attempt() missing")
except Exception as e:
    print(f"    [FAIL] {e}")

# Test 4: Resume API
print("\n[4] Resume API endpoint:")
try:
    try:
        from orchestrator_ui.backend.api import projects
    except:
        from api import projects

    router = projects.router
    resume_found = False
    for route in router.routes:
        if hasattr(route, 'path') and 'resume' in route.path:
            resume_found = True
            print(f"    [OK] Found route: {route.path}")
            break

    if not resume_found:
        print("    [FAIL] /resume endpoint not found")
except Exception as e:
    print(f"    [FAIL] {e}")

# Test 5: Orchestrator
print("\n[5] Orchestrator support:")
try:
    try:
        from orchestrator_ui.backend.orchestrator import GenerationOrchestrator
    except:
        from orchestrator import GenerationOrchestrator

    import inspect
    sig = inspect.signature(GenerationOrchestrator.run_generation)

    if 'existing_project_id' in sig.parameters:
        print("    [OK] run_generation() has existing_project_id parameter")
    else:
        print("    [FAIL] existing_project_id parameter missing")
except Exception as e:
    print(f"    [FAIL] {e}")

# Test 6: Pydantic schemas
print("\n[6] Pydantic schemas:")
try:
    try:
        from orchestrator_ui.backend import schemas
    except:
        import schemas

    proj_fields = schemas.ProjectResponse.model_fields.keys()
    log_fields = schemas.GenerationLogResponse.model_fields.keys()

    if 'generation_attempt' in proj_fields:
        print("    [OK] ProjectResponse.generation_attempt exists")
    else:
        print("    [FAIL] ProjectResponse.generation_attempt missing")

    if 'generation_attempt' in log_fields:
        print("    [OK] GenerationLogResponse.generation_attempt exists")
    else:
        print("    [FAIL] GenerationLogResponse.generation_attempt missing")
except Exception as e:
    print(f"    [FAIL] {e}")

# Test 7: Frontend types
print("\n[7] Frontend TypeScript types:")
frontend_types_path = os.path.join(project_root, 'orchestrator-ui', 'frontend', 'src', 'types', 'index.ts')
if os.path.exists(frontend_types_path):
    content = open(frontend_types_path).read()
    if 'generation_attempt: number' in content:
        print("    [OK] TypeScript types updated")
    else:
        print("    [FAIL] generation_attempt not in TypeScript types")
else:
    print("    [SKIP] Frontend types file not found")

# Test 8: Frontend API client
print("\n[8] Frontend API client:")
client_path = os.path.join(project_root, 'orchestrator-ui', 'frontend', 'src', 'api', 'client.ts')
if os.path.exists(client_path):
    content = open(client_path).read()
    if 'resumeGeneration' in content:
        print("    [OK] resumeGeneration() method exists")
    else:
        print("    [FAIL] resumeGeneration() method missing")
else:
    print("    [SKIP] Frontend client file not found")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Start backend: cd orchestrator-ui/backend && python main.py")
print("2. Start frontend: cd orchestrator-ui/frontend && npm run dev")
print("3. Create a failed generation")
print("4. Click 'Resume Generation' button")
print("5. Verify generation restarts with attempt #2")
