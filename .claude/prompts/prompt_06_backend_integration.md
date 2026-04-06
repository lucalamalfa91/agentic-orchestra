# Prompt 06 — Backend FastAPI Integration

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.
You have: `AI_agents/graph/graph.py`, `AI_agents/knowledge/`, `mcp_servers/`.

## Task: Wire the new LangGraph orchestrator into the existing FastAPI backend

## 1. Modify `orchestrator-ui/backend/orchestrator.py`

Replace the subprocess approach with LangGraph:
- Import the compiled graph `app` from `AI_agents.graph.graph`
- `async def run(self, request: GenerationRequest) -> AsyncIterator[str]:`
  a. Build initial `OrchestraState` from request fields
  b. Read user's integration tokens from DB (via crud functions),
     decrypt via `encryption_service.py`,
     set as env vars for MCP server processes
  c. Load user's configured `KnowledgeSource` objects from DB
     and instantiate `KnowledgeAgent` with them
  d. Stream graph execution:
     ```python
     async for event in graph_app.astream(state, config={"thread_id": project_id}):
         yield map_event_to_websocket_message(event)
     ```
  e. `map_event_to_websocket_message()` must produce the SAME string format
     as the current `STEP_MARKERS` so the frontend needs zero changes
  f. On completion, save final state to `GenerationLog` in DB

Do NOT change the WebSocket endpoint or message format.

## 2. Modify `orchestrator-ui/backend/models.py`

Add model `KnowledgeSourceConfig`:
- `id`: UUID primary key
- `user_id`: FK to user
- `name`: str
- `source_type`: Enum("web", "file", "api")
- `config_json`: str (encrypted JSON — use `encryption_service.py`)
- `last_indexed_at`: Optional[datetime]
- `created_at`: datetime

Also create the Alembic migration for this model.

## 3. Create `orchestrator-ui/backend/api/knowledge.py`

New FastAPI router with:
- `GET /api/knowledge/sources` — list user's configured sources
- `POST /api/knowledge/sources` — save a new source (encrypts config_json)
- `DELETE /api/knowledge/sources/{id}` — remove a source
- `POST /api/knowledge/index/{id}` — trigger background re-indexing
  of a specific source (use FastAPI `BackgroundTasks`)
- `GET /api/knowledge/index/{id}/status` — returns indexing status
  (polling endpoint for the frontend spinner)

Register this router in the main FastAPI app.

Show exact diffs for modified files.
Preserve ALL existing functionality.
When done, update `.claude/context/migration_status.md` marking Prompt 06 complete.
