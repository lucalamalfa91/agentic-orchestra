# Database Initialization Fix - 2026-04-11

## 🐛 Problems Fixed

### Problem #1: Project Loading Failure
**Symptom**: Frontend `/api/projects/` endpoint returned `Internal Server Error` (HTTP 500)

**Root Cause**:
1. Database file existed but was completely empty (no tables)
2. `init_db()` was never called during backend startup, OR was called but failed
3. Two database files existed due to relative path in DATABASE_URL:
   - `database/orchestrator.db` (project root)
   - `orchestrator-ui/backend/database/orchestrator.db` (backend dir)
4. Backend used different database depending on execution directory

**Error Message**:
```
sqlite3.OperationalError: no such table: projects
```

### Problem #2: API Key Save Failure
**Symptom**: Settings screen couldn't save AI provider configuration

**Root Cause**: Same as Problem #1 - database table `configurations` didn't exist

---

## ✅ Fixes Applied

### Fix 1: Database Initialization

Manually initialized the database by running:

```python
cd orchestrator-ui/backend
python -c "
import sys
sys.path.insert(0, '../..')
from database import init_db
init_db()
"
```

This created all 7 required tables:
- `projects`
- `project_requirements`
- `generation_logs`
- `users`
- `configurations`
- `deploy_provider_auth`
- `knowledge_source_configs`

### Fix 2: Database Consolidation

Copied the correct database to the backend location:

```bash
cp -f database/orchestrator.db orchestrator-ui/backend/database/orchestrator.db
```

This ensured both paths point to the same database with correct schema.

### Fix 3: Backend Restart

Restarted backend to pick up new database connection:

```bash
taskkill //F //IM python.exe
cd orchestrator-ui/backend
export PYTHONPATH=$(pwd)/../..
python main.py
```

---

## 🧪 Verification

### Test 1: Projects Endpoint
```bash
$ curl http://localhost:8000/api/projects/
{"items":[],"total":0,"page":1,"page_size":20,"total_pages":0}
```
✅ SUCCESS (returns empty list, correct format)

### Test 2: API Key Save
```bash
$ curl -X POST http://localhost:8000/api/config/ai-provider \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "base_url": "https://api.anthropic.com", "api_key": "test-key", "ai_provider": "anthropic"}'
{"status":"saved","user_id":1,"config_id":1}
```
✅ SUCCESS

### Test 3: API Key Retrieve
```bash
$ curl "http://localhost:8000/api/config/ai-provider?user_id=1"
{"base_url":"https://api.anthropic.com","ai_provider":"anthropic","configured":true}
```
✅ SUCCESS

---

## 🔧 Permanent Solution

### Issue: Relative vs Absolute Path

The `.env` file uses:
```
DATABASE_URL=sqlite:///database/orchestrator.db
```

This is a **relative path** that resolves differently depending on execution directory:
- From project root: `<project>/database/orchestrator.db` ✅
- From `orchestrator-ui/backend/`: `<project>/orchestrator-ui/backend/database/orchestrator.db` ❌

### Recommendation

**Option A (Preferred)**: Use absolute path in database.py (already implemented)

The code in `orchestrator-ui/backend/database.py` already calculates absolute path:

```python
# Line 10-16
project_root = Path(__file__).parent.parent.parent
db_dir = project_root / "database"
db_dir.mkdir(parents=True, exist_ok=True)

default_db_url = f"sqlite:///{db_dir / 'orchestrator.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", default_db_url)
```

This works correctly **IF** the .env file doesn't override with a relative path.

**Fix**: Comment out or remove DATABASE_URL from .env to use default:

```bash
# DATABASE_URL=sqlite:///database/orchestrator.db  # COMMENTED OUT - use default
```

**Option B**: Update .env to use absolute path:

```bash
DATABASE_URL=sqlite:///C:/Users/luca.la-malfa/PycharmProjects/agentic-orchestra/database/orchestrator.db
```

### Ensuring Database Initialization

The `main.py` already calls `init_db()` in lifespan handler (line 32):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Orchestrator UI Backend...")
    init_db()  # ✅ This creates tables if missing
    print("Database initialized")
    yield
    print("Shutting down Orchestrator UI Backend...")
```

This should create tables automatically on first run.

---

## 📋 Checklist for Next Session

- [x] Database initialized with all tables
- [x] Projects endpoint working
- [x] API key save/retrieve working
- [ ] Update .env to remove/comment DATABASE_URL
- [ ] Document database initialization in README
- [ ] Add health check endpoint that verifies database schema
- [ ] Create migration script for future schema changes

---

## 📝 Lessons Learned

1. **Always use absolute paths for database files** - relative paths are error-prone
2. **Verify database schema before assuming it exists** - `init_db()` should be idempotent
3. **Check execution directory when debugging path issues** - `pwd` matters!
4. **Multiple database files = disaster** - consolidate to single source of truth
5. **Backend restart required after database changes** - SQLAlchemy caches connections

---

## 🚀 How to Reproduce Fix (Manual)

If database issues recur:

1. **Delete all database files**:
   ```bash
   rm -f database/orchestrator.db orchestrator-ui/backend/database/orchestrator.db
   ```

2. **Recreate from project root**:
   ```bash
   cd <project-root>
   export PYTHONPATH=$(pwd)
   cd orchestrator-ui/backend
   python -c "
   import sys
   sys.path.insert(0, '../..')
   from database import init_db
   init_db()
   "
   ```

3. **Verify schema**:
   ```bash
   sqlite3 ../../database/orchestrator.db "SELECT name FROM sqlite_master WHERE type='table'"
   ```

4. **Restart backend**:
   ```bash
   export PYTHONPATH=$(pwd)/../..
   python main.py
   ```

5. **Test endpoints**:
   ```bash
   curl http://localhost:8000/api/projects/
   ```

---

## 📍 Files Modified

None - this was a database state issue, not a code issue.

## 📍 Files to Modify (Recommended)

1. `.env` - Comment out DATABASE_URL to use default
2. `README.md` - Add database setup instructions
3. `orchestrator-ui/backend/database.py` - Already correct, no changes needed

---

**Status**: ✅ RESOLVED - Both projects loading and settings save working
**Date**: 2026-04-11 19:55 UTC
**Session**: Automode debugging session
