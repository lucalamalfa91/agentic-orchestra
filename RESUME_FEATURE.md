# Resume Capability for Failed Generations

## Overview

This feature allows users to resume failed MVP generations without re-entering requirements. When a generation fails, users can click a "Resume Generation" button to restart the process with the same original requirements.

## Key Features

✅ **One-Click Resume**: Simple button on failed project cards
✅ **Attempt Tracking**: Each resume increments `generation_attempt` counter
✅ **Full History**: All attempts logged separately for debugging
✅ **No Data Re-entry**: Uses stored requirements from database
✅ **Clean Restart**: Always starts from step 1 (no partial state)
✅ **WebSocket Progress**: Real-time progress updates like new generations

## User Flow

1. **Generation Fails**: User's MVP generation encounters an error and status becomes "failed"
2. **Navigate to History**: User goes to Project History screen
3. **Click Resume**: User clicks green "▶ Resume Generation" button on failed project card
4. **Confirmation**: Browser confirms: "Resume this generation with the same requirements?"
5. **Progress Viewer Opens**: WebSocket connection established, progress streaming begins
6. **Generation Restarts**: Pipeline runs from beginning with attempt #2
7. **New Logs Created**: All logs tagged with `generation_attempt = 2`

## Technical Implementation

### Architecture Decision: Restart vs. Checkpoint Resume

We chose **restart with same requirements** over **checkpoint resume** because:

| Restart Approach | Checkpoint Approach |
|------------------|---------------------|
| ✅ Simple: reuses existing flow | ❌ Complex: requires state restoration |
| ✅ Reliable: same code path | ❌ Risky: state corruption possible |
| ✅ Stateless: works across restarts | ❌ Stateful: in-memory dependencies |
| ✅ Full logs: separate per attempt | ❌ Merged logs: harder to debug |
| ⚠️ Slower: reruns all steps | ✅ Faster: skips completed steps |

**Result**: Simpler implementation with lower risk, acceptable tradeoff for current use case.

### Database Schema

#### `projects` table
```sql
ALTER TABLE projects ADD COLUMN generation_attempt INTEGER NOT NULL DEFAULT 1;
```

- Incremented on each resume
- Tracks total number of attempts for a project
- Used in API responses and frontend display

#### `generation_logs` table
```sql
ALTER TABLE generation_logs ADD COLUMN generation_attempt INTEGER NOT NULL DEFAULT 1;
```

- Tags each log entry with attempt number
- Allows filtering logs by attempt: `WHERE generation_attempt = 2`
- Enables debugging of specific failed attempts

### API Endpoints

#### `POST /api/projects/{project_id}/resume`

**Request**: No body required (requirements fetched from database)

**Response**:
```json
{
  "generation_id": "abc-123-def-456",
  "message": "Resuming generation for project My App (attempt #2)",
  "websocket_url": "ws://localhost:8000/ws/generation/abc-123-def-456"
}
```

**Error Cases**:
- `404`: Project not found
- `400`: Project status is not 'failed' (e.g., already completed)
- `404`: Requirements not found in database
- `500`: Failed to reconstruct requirements from stored data

**Logic**:
1. Verify project exists and status = 'failed'
2. Fetch stored requirements from `project_requirements` table
3. Reconstruct `GenerationRequest` object
4. Increment `generation_attempt` counter
5. Update status to 'in_progress'
6. Log resume event
7. Start generation in background (async task)
8. Return new `generation_id` and WebSocket URL

### LangGraph State Fix

**Problem**: Parallel agents (e.g., `backend_agent`, `frontend_agent`, `backlog_agent`) caused state conflicts:
```
InvalidUpdateError: Can receive only one value per step
```

**Solution**: Added `Annotated` reducers to state fields updated by multiple agents:

```python
from typing import Annotated
import operator

class OrchestraState(TypedDict):
    # Before: backlog_items: Optional[list]
    # After:
    backlog_items: Optional[Annotated[list, operator.add]]
    rag_context: Optional[Annotated[list, operator.add]]
```

**Why**: LangGraph requires explicit merge strategies. `operator.add` concatenates lists from parallel branches.

### Frontend UI

#### Failed Project Card (Before)
```
┌─────────────────────────┐
│ Project Name            │
│ Status: failed          │
│ [Delete]                │
└─────────────────────────┘
```

#### Failed Project Card (After)
```
┌─────────────────────────┐
│ Project Name            │
│ Status: failed          │
│ [▶ Resume] | [Delete]   │
└─────────────────────────┘
```

**Button Styles**:
- **Resume**: Green glassmorphism, hover lift effect
- **Delete**: Red glassmorphism, hover lift effect
- Both buttons: 0.3s transition, cursor pointer

## Testing

### Automated Verification

Run the included test script:

```bash
python verify_resume.py
```

**Expected Output**:
```
[1] LangGraph state reducers: [OK]
[2] Database schema: [OK]
[3] CRUD functions: [OK]
[4] Resume API endpoint: [OK]
[5] Orchestrator support: [OK]
[6] Pydantic schemas: [OK]
[7] Frontend TypeScript types: [OK]
[8] Frontend API client: [OK]
```

### Manual Testing

1. **Start Backend**:
   ```bash
   cd orchestrator-ui/backend
   python main.py
   ```

2. **Start Frontend**:
   ```bash
   cd orchestrator-ui/frontend
   npm run dev
   ```

3. **Create Failed Generation**:
   - Navigate to MVP Creation screen
   - Submit generation request
   - Let it fail (or force failure)

4. **Test Resume**:
   - Go to Project History
   - Find failed project
   - Click "▶ Resume Generation"
   - Confirm dialog
   - **Verify**:
     - Progress viewer opens
     - WebSocket connects
     - Generation starts from step 1
     - Logs show `generation_attempt = 2`

5. **Test Multiple Resumes**:
   - Let generation fail again
   - Resume again
   - Verify `generation_attempt = 3`

6. **Test Error Cases**:
   ```bash
   # Try resuming completed project
   curl -X POST http://localhost:8000/api/projects/1/resume
   # Expected: HTTP 400 "Can only resume failed projects"
   ```

## Database Queries

### View All Attempts for a Project
```sql
SELECT
    id,
    step_name,
    status,
    message,
    generation_attempt,
    created_at
FROM generation_logs
WHERE project_id = 1
ORDER BY generation_attempt, created_at;
```

### Count Failed Attempts
```sql
SELECT
    project_id,
    MAX(generation_attempt) as total_attempts
FROM generation_logs
WHERE status = 'failed'
GROUP BY project_id;
```

### Find Projects with Multiple Attempts
```sql
SELECT
    p.id,
    p.name,
    p.generation_attempt
FROM projects p
WHERE p.generation_attempt > 1
ORDER BY p.generation_attempt DESC;
```

## Limitations

1. **No Mid-Flow Resume**: Always restarts from beginning, not from where it failed
   - **Workaround**: None (by design for simplicity)

2. **Requirements Locked**: Cannot modify requirements during resume
   - **Workaround**: Delete project and create new one with modified requirements

3. **No Automatic Retry**: User must manually click Resume
   - **Future Enhancement**: Auto-retry transient failures after delay

4. **No Attempt Limit**: Users can resume indefinitely
   - **Future Enhancement**: Add max_attempts configuration

## Future Enhancements

### Phase 2: Editable Resume
```typescript
// Allow modifying requirements before resuming
POST /api/projects/{id}/resume
{
  "modifications": {
    "features": ["new feature", "another feature"],
    "mvp_description": "Updated description"
  }
}
```

### Phase 3: Checkpoint Resume
```typescript
// Resume from specific step using LangGraph checkpoints
POST /api/projects/{id}/resume
{
  "resume_from_step": "backend_agent",
  "use_checkpoint": true
}
```

### Phase 4: Auto-Retry
```python
# In orchestrator.py
if is_transient_error(error):
    schedule_auto_retry(project_id, delay=300)  # 5 min delay
```

### Phase 5: Attempt Analytics
```typescript
// Dashboard showing:
// - Average attempts per project
// - Most common failure points
// - Success rate by attempt number
GET /api/analytics/generation-attempts
```

## Migration Notes

**Database Migration**: `b644db3e3f27_add_generation_attempt_tracking`

**Applied**: ✅ Yes (automatically sets default=1 for existing rows)

**Rollback** (if needed):
```bash
cd orchestrator-ui/backend
alembic downgrade -1
```

**Verify Migration**:
```bash
cd orchestrator-ui/backend
alembic current
# Should show: b644db3e3f27 (head)
```

## Files Modified

| File | Purpose | Changes |
|------|---------|---------|
| `AI_agents/graph/state.py` | State reducers | Added `Annotated[list, operator.add]` |
| `orchestrator-ui/backend/models.py` | DB models | Added `generation_attempt` column |
| `orchestrator-ui/backend/alembic/versions/b644db3e3f27_*.py` | Migration | Created migration script |
| `orchestrator-ui/backend/crud.py` | CRUD ops | Added `increment_generation_attempt()` |
| `orchestrator-ui/backend/api/projects.py` | API endpoint | Added `/resume` endpoint |
| `orchestrator-ui/backend/orchestrator.py` | Orchestration | Resume mode support |
| `orchestrator-ui/backend/schemas.py` | Validation | Added field to Pydantic models |
| `orchestrator-ui/frontend/src/api/client.ts` | API client | Added `resumeGeneration()` |
| `orchestrator-ui/frontend/src/types/index.ts` | Types | Updated interfaces |
| `orchestrator-ui/frontend/src/components/ProjectCard.tsx` | UI | Added Resume button |

**Total**: 10 files modified

## Support

**Issues**: If you encounter problems, check:
1. Backend logs: `orchestrator-ui/backend/logs/`
2. Database state: `SELECT * FROM projects WHERE status='failed'`
3. API directly: `curl -X POST http://localhost:8000/api/projects/{id}/resume`

**Common Issues**:

| Issue | Cause | Fix |
|-------|-------|-----|
| "Project not found" | Wrong project_id | Check `SELECT id FROM projects` |
| "Can only resume failed projects" | Status not 'failed' | Verify `SELECT status FROM projects WHERE id=X` |
| "Requirements not found" | Missing in DB | Check `SELECT * FROM project_requirements WHERE project_id=X` |
| WebSocket doesn't connect | Backend not running | Start backend: `python main.py` |

## Credits

**Implemented**: 2026-04-10
**Author**: Claude Sonnet 4.5
**Verified**: Automated test suite + manual testing
**Status**: ✅ Production ready
