# Agentic Orchestra — Project Memory

## ⚡ START OF EVERY SESSION — do this first
1. Read `.claude/context/migration_status.md`
2. Tell me: what step we are on, what files exist, any open blockers
3. Ask me which task to work on if not clear from the status file
Do not write any code before completing steps 1-3.

---

## How to run a task
All tasks are pre-written as prompt files. Execute them like this:

```
Read and execute the task in .claude/prompts/prompt_01_analysis.md
```

### Available prompts (execute in order)
| File | Task |
|---|---|
| `.claude/prompts/prompt_01_analysis.md` | Analyse current codebase, map agent flow and integrations |
| `.claude/prompts/prompt_02_state_schema.md` | Create OrchestraState TypedDict + AgentStatus enum |
| `.claude/prompts/prompt_03_langgraph_graph.md` | Create LangGraph graph with parallel fan-out (stub nodes) |
| `.claude/prompts/prompt_04_knowledge_agent.md` | Generic Knowledge Agent + RAG sources + pgvector |
| `.claude/prompts/prompt_05_mcp_servers.md` | MCP server wrappers for GitHub, Azure DevOps, Deploy |
| `.claude/prompts/prompt_06_backend_integration.md` | Wire LangGraph into FastAPI orchestrator |
| `.claude/prompts/prompt_07_agent_nodes.md` | Implement real agent nodes (one per session) |
| `.claude/prompts/prompt_08_checkpoint_hitl.md` | Postgres checkpointing + human-in-the-loop design review |
| `.claude/prompts/prompt_09_knowledge_ui.md` | React UI for managing Knowledge Sources |
| `.claude/prompts/prompt_10_testing.md` | Test suite for all new AI components |

Current step: see `.claude/context/migration_status.md`

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
- NEVER modify `run_all_agents.py` - kept as legacy fallback
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

## Session management rule (mandatory)
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
