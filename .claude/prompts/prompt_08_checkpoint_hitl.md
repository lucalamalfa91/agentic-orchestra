# Prompt 08 — Checkpoint + Human-in-the-Loop

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.
All agent nodes are implemented.

## Task: Add persistence and human approval on the design step

## 1. Update `AI_agents/graph/graph.py`

Replace `checkpointer=None` with PostgreSQL checkpointer:
```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# Use same DATABASE_URL as main app (read from env)
checkpointer = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
await checkpointer.setup()  # creates checkpoint tables
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["backend_agent"]  # pause after design, before code gen
)
```

## 2. Create `orchestrator-ui/backend/api/generation_control.py`

New FastAPI router:

### `GET /api/generation/{project_id}/state`
Returns current graph state from checkpoint:
- `current_step`, `design_yaml`, `errors`, `agent_statuses`
Frontend uses this to display the design review screen.

### `POST /api/generation/{project_id}/approve`
Body: `{ "design_changes": {} }` (optional user modifications to design_yaml)
1. Load checkpoint state via `graph_app.aget_state(thread_config)`
2. If `design_changes` provided, merge into `state["design_yaml"]`
3. Resume: `await graph_app.ainvoke(None, thread_config)`
4. Continue streaming events to WebSocket

### `POST /api/generation/{project_id}/reject`
Cancels generation, marks `GenerationLog` as REJECTED.

## 3. Create `DesignReviewScreen` in frontend

File: `orchestrator-ui/frontend/src/screens/DesignReview/DesignReviewScreen.tsx`

This screen appears between "Generating design..." and "Generating code..."
in the existing progress flow.

Display:
- App name, description, stack (as readable labels, not raw YAML)
- Entities as a table (name + fields)
- API endpoints as a list (METHOD /path — description)
- Deployment target badge

Actions:
- "Approve & Continue" → `POST /api/generation/{id}/approve`
- "Reject" → `POST /api/generation/{id}/reject`
- Optional: JSON editor toggle for advanced users to edit `design_yaml`

Use the same Tailwind classes and component patterns as existing screens.
Do NOT create a new design system — reuse existing components.

Register the router in the main FastAPI app.
Show diffs for all modified files.
When done, update `.claude/context/migration_status.md` marking Prompt 08 complete.
