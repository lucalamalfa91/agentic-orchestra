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
- Original orchestration: `run_all_agents.py` (subprocess-based, LEGACY)
- NEW orchestration: `AI_agents/graph/graph.py` (LangGraph-based, IN PROGRESS)

## Migration status
See `.claude/context/migration_status.md` for full current state.

---

## Absolute rules (never break these)
- NEVER modify `run_all_agents.py` — kept as legacy fallback
- NEVER change the WebSocket message format in `orchestrator.py`
  (frontend depends on exact string format of STEP_MARKERS)
- NEVER hardcode API keys or tokens — always read from env vars
  or `encryption_service.py`
- ALWAYS use `OrchestraState` (TypedDict) as the only data contract
  between agents — no ad-hoc dicts
- New DB model → add to `models.py` AND create Alembic migration
- New API endpoint → add to the appropriate router in `backend/api/`

---

## Key files map
```
AI_agents/graph/state.py          → shared state schema between agents
AI_agents/graph/graph.py          → LangGraph graph definition
AI_agents/graph/nodes/            → one file per agent node
AI_agents/knowledge/              → Knowledge Agent + sources + vector store
mcp_servers/                      → MCP server wrappers for integrations
orchestrator-ui/backend/orchestrator.py  → bridges FastAPI ↔ LangGraph
orchestrator-ui/backend/models.py        → DB models (add here first)
.claude/prompts/                  → task prompts, one file per step
.claude/context/migration_status.md     → session handoff state
```

---

## Conventions
- Python: async/await everywhere, Pydantic for validation, type hints mandatory
- Agent nodes: each in its own file in `AI_agents/graph/nodes/`
- LLM calls: always use `get_llm_client()` from `AI_agents/utils/llm_client.py`
  Never instantiate ChatOpenAI/ChatAnthropic directly in node files
- On agent error: set `state.errors["{node_name}"] = str(e)`,
  set agent status to FAILED, return state — never raise exceptions

---

## 🔴 Session management rule (mandatory)
Monitor context usage continuously during the session.

When context usage reaches ~75%:
1. STOP the current task immediately, even if mid-implementation
2. Update `.claude/context/migration_status.md` with:
   - Every file created or modified in this session
   - Every architectural decision made and why
   - Exact current state of any in-progress file (what is done, what is missing)
   - The next action to take in the next session
3. Commit all changes with message: "wip: session checkpoint — [brief description]"
4. Tell me: "⚠️ Context at 75% — migration_status.md updated. Run /clear when ready."

Never let auto-compaction happen without updating migration_status.md first.
Auto-compaction is lossy — it loses exact variable names, interfaces, and decisions.
The migration_status.md file is the only reliable memory across sessions.
