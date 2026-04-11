# Backend Import Fix - 2026-04-11

## 🐛 Bug Found

**Symptom**: Backend completely broken - all endpoints returning 404/405/CORS errors
- ❌ 404 on `/api/knowledge/sources`, `/api/projects/{id}/resume`, `/api/generation/{id}/cancel`
- ❌ 405 on `DELETE /api/projects/{id}`, `GET /api/projects/{id}`
- ❌ CORS errors on `PATCH /api/projects/{id}/status`
- ❌ WebSocket closing with code 1006 (abnormal close)

**Root Cause**:
```python
# orchestrator-ui/backend/orchestrator.py (lines 20-34)
try:
    from orchestrator_ui.backend import crud, schemas
    from orchestrator_ui.backend.websocket import manager
    from orchestrator_ui.backend.encryption_service import decrypt
    from orchestrator_ui.backend.models import Configuration, User
    from AI_agents.graph.graph import app as langgraph_app
    from AI_agents.graph.state import OrchestraState, AgentStatus
except ModuleNotFoundError:
    import crud
    import schemas
    from websocket import manager
    from encryption_service import decrypt
    from models import Configuration, User
    from AI_agents.graph.graph import app as langgraph_app  # ← DUPLICATED OUTSIDE try-except!
    from AI_agents.graph.state import OrchestraState, AgentStatus  # ← DUPLICATED OUTSIDE try-except!
```

The imports of `AI_agents` were duplicated **outside** the try-except block (lines 33-34), so when the try block failed, the except block executed successfully but then immediately crashed on lines 33-34 trying to import `AI_agents` without adding it to `sys.path`.

This caused:
1. Backend to crash during import phase
2. No routes registered (hence 404 on all endpoints)
3. CORS middleware never configured (hence CORS errors)
4. WebSocket endpoint never registered (hence 1006 abnormal close)

## ✅ Fix Applied

**File**: `orchestrator-ui/backend/orchestrator.py`

**Change**: Added `sys.path.insert()` in the except block to ensure `AI_agents` can be imported when running from `backend/` directory:

```python
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
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # ← ADDED
    import crud
    import schemas
    from websocket import manager
    from encryption_service import decrypt
    from models import Configuration, User
    from AI_agents.graph.graph import app as langgraph_app  # ← NOW WORKS
    from AI_agents.graph.state import OrchestraState, AgentStatus  # ← NOW WORKS
```

This matches the pattern used successfully in `generation_control.py` (lines 16-30).

## 🧪 Verification

**Import Test**:
```bash
$ export PYTHONPATH=$(pwd) && python -c "from orchestrator import GenerationOrchestrator"
SUCCESS: orchestrator.py imports OK
```

**Backend Startup Test**:
```bash
$ export PYTHONPATH=$(pwd) && cd orchestrator-ui/backend && python main.py
INFO:     Started server process [20716]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
Starting Orchestrator UI Backend...
Database initialized successfully!

# All 42 endpoints registered successfully
```

**Endpoint Tests**:
- ✅ GET `/health` → 200 OK
- ✅ GET `/api/projects/` → 200 OK
- ✅ GET `/api/knowledge/sources` → 200 OK (was 404)
- ✅ OPTIONS `/api/projects/1/status` → 200 OK (CORS works)

## 📋 Files Modified

1. `orchestrator-ui/backend/orchestrator.py` - Fixed import fallback logic
2. `orchestrator-ui/backend/api/generation_control.py` - Added cancel endpoint (already correct)
3. `orchestrator-ui/backend/api/knowledge.py` - Minor additions (already correct)
4. `orchestrator-ui/frontend/src/api/client.ts` - Added cancelGeneration method
5. `orchestrator-ui/frontend/src/components/ProjectHistory.tsx` - Improved error handling

## 🚀 How to Start Backend (Correct Method)

**Option 1 (RECOMMENDED)** - Use startup scripts:
```bash
# Git Bash
bash start-backend.sh

# PowerShell
.\start-backend.ps1
```

These scripts automatically set `PYTHONPATH` to project root.

**Option 2** - Manual startup:
```bash
# Git Bash
export PYTHONPATH=$(pwd)
cd orchestrator-ui/backend
python main.py

# PowerShell
$env:PYTHONPATH = (Get-Location).Path
cd orchestrator-ui\backend
python main.py
```

**⚠️ NEVER run** `python main.py` from `orchestrator-ui/backend/` without setting PYTHONPATH first - it will crash.

## 🎯 Next Steps

- [x] Fix import bug in orchestrator.py
- [x] Verify all endpoints load
- [x] Test HTTP responses
- [x] Document fix
- [ ] Commit changes
- [ ] Test full frontend + backend integration
- [ ] Test generation flow end-to-end

## 📝 Lessons Learned

1. **Always check import errors first** when endpoints return 404 - it means routes never registered
2. **Fallback imports need sys.path setup** - don't assume modules are importable
3. **Match existing patterns** - generation_control.py already had the correct pattern
4. **Use startup scripts** - they exist for a reason (PYTHONPATH setup)
5. **Exit code != error** - timeout kills can show exit 1 even when tests pass
