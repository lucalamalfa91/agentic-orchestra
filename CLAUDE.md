# Agentic Orchestra — Project Memory

## ⚡ START OF EVERY SESSION — do this first
1. Read `.claude/context/migration_status.md`
2. Tell me: what step we are on, what files exist, any open blockers
3. Ask me which task to work on if not clear from the status file
Do not write any code before completing steps 1-3.

---

## What this project is
A FastAPI + React app that orchestrates multiple AI agents to generate
full-stack MVP applications from a text description.
NOT a chatbot. NOT a simple CRUD app.

## Current architecture state
- Backend: FastAPI, Python, SQLAlchemy, PostgreSQL, WebSocket
- Frontend: React + TypeScript + Vite + Tailwind
- Original orchestration: `run_all_agents.py` (subprocess-based, LEGACY - do not modify)
- NEW orchestration: `AI_agents/graph/graph.py` (LangGraph-based, IN PROGRESS)

---

## Key files map

```
AI_agents/graph/state.py                -> shared state schema between agents
AI_agents/graph/graph.py                -> LangGraph graph definition
AI_agents/graph/nodes/                  -> one file per agent node
AI_agents/knowledge/                    -> Knowledge Agent + sources + vector store
AI_agents/utils/llm_client.py           -> LLM factory (always use this, never direct)
mcp_servers/                            -> MCP server wrappers for integrations
orchestrator-ui/backend/orchestrator.py -> bridges FastAPI <-> LangGraph
orchestrator-ui/backend/models.py       -> DB models (add here first)
orchestrator-ui/backend/api/            -> FastAPI routers
.claude/prompts/                        -> task prompts, one file per step
.claude/context/migration_status.md    -> session handoff - update at end of every session
.claude/rules/                          -> contextual rules loaded per directory
```

---

## Absolute rules (never break these) 
- NEVER change the WebSocket message format in `orchestrator.py`
  (frontend depends on exact string format of STEP_MARKERS)
- NEVER hardcode API keys or tokens - always read from env vars
  or decrypt via `encryption_service.py`
- ALWAYS use `OrchestraState` (TypedDict) as the only data contract
  between agents - no ad-hoc dicts
- ALWAYS use `get_llm_client()` from `AI_agents/utils/llm_client.py`
  for LLM calls - never instantiate ChatOpenAI/ChatAnthropic directly
- New DB model -> add to `models.py` AND create Alembic migration
- New API endpoint -> add to the appropriate router in `backend/api/`
- On agent error: set `state["errors"]["node_name"] = str(e)`,
  set status FAILED, return state - NEVER raise from agent nodes

---

## Conventions
- Python: async/await everywhere, Pydantic for validation, type hints mandatory
- Agent nodes: each in its own file in `AI_agents/graph/nodes/`
- Knowledge sources: never hardcoded - always configured by user via UI
  and read from DB at runtime
- MCP server tokens: injected as env vars by backend before agent run;
  user connects accounts once via UI, never interrupted during generation

---

## Session management rules (mandatory)

### For sequential tasks (e.g., Prompt 02 → 03 → 04 → 05...)
When working through sequential prompts/tasks that are being tracked:
1. Complete the current prompt/task fully
2. Update `.claude/context/migration_status.md` marking the task as complete
3. Commit changes with clear commit message
4. Push to remote if requested
5. Display completion message with explicit reminder:

```
✅ Prompt X completed and committed.

NEXT STEPS:
1. You run: /clear
2. You say: "procedi con prompt Y" (or "prosegui con l'implementazione")
3. I start Prompt Y with clean context

Ready when you are! 🚀
```

6. STOP and WAIT - do NOT continue until user starts new message after /clear

**Why**: Sequential tasks build on each other but don't need shared context.
Starting each with clean context prevents context bloat and keeps sessions focused.

### For non-sequential tasks (ad-hoc work, debugging, exploration)
Monitor context usage continuously during the session.

When context usage reaches ~75%:
1. STOP the current task immediately, even if mid-implementation
2. Update `.claude/context/migration_status.md` with:
   - Every file created or modified in this session
   - Every architectural decision made and why
   - Exact current state of any in-progress file (what is done, what is missing)
   - The next action to take in the next session
3. Commit all changes: `git commit -m "wip: session checkpoint - [brief description]"`
4. Say: "Context at 75% - migration_status.md updated. Run /clear when ready."

Never let auto-compaction happen without updating migration_status.md first.
Auto-compaction is lossy - it loses exact variable names, interfaces, decisions.
The migration_status.md file is the only reliable memory across sessions.
