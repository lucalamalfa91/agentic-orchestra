# Migration Status — Last updated: 2026-04-08

## Completed steps
- [ ] Prompt 01 — Analysis
- [x] Prompt 02 — LangGraph state schema ✓
- [ ] Prompt 03 — LangGraph graph + parallelismo
- [ ] Prompt 04 — Knowledge Agent (RAG generico)
- [ ] Prompt 05 — MCP Servers
- [ ] Prompt 06 — Backend FastAPI integration
- [ ] Prompt 07 — Agent nodes reali (design + altri)
- [ ] Prompt 08 — Checkpoint + human-in-the-loop
- [ ] Prompt 09 — UI Knowledge Sources
- [ ] Prompt 10 — Testing

## Current step
**Prompt 02 — LangGraph state schema COMPLETED**
Working on: Created OrchestraState TypedDict and AgentStatus enum
Blocker: none

## Decisions made
- LangGraph invece di CrewAI: controllo deterministico del flusso
- pgvector invece di Qdrant: già presente Postgres, riduce infra
- MCP servers come processi separati su porte 8001-8003
- Multilingual embeddings: paraphrase-multilingual-mpnet-base-v2
- interrupt_before=["backend_agent"] per human-in-the-loop sul design
- **OrchestraState TypedDict**: 17 fields with producer→consumer docstrings
- **AgentStatus enum**: str subclass for JSON serialization compatibility

## Files created by this migration
### Prompt 02 (2026-04-08)
- `AI_agents/graph/__init__.py` - Package initialization
- `AI_agents/graph/nodes/__init__.py` - Nodes package initialization
- `AI_agents/graph/state.py` - OrchestraState TypedDict + AgentStatus enum (4504 bytes)
  - 17 state fields (4 user input, 7 agent data, 2 supporting, 4 orchestration)
  - AgentStatus enum with 5 values (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
  - Comprehensive docstrings mapping producers → consumers
  - All imports verified, type checking passes

## Next action
Execute Prompt 03: Create `AI_agents/graph/graph.py` with LangGraph graph definition
- Define agent nodes (stubs initially)
- Set up parallel execution paths (backend + frontend can read same design_yaml)
- Configure conditional edges (skip steps based on config)
- Add error handling (agents return state with errors dict instead of raising)
