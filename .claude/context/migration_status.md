# Migration Status — Last updated: 2026-04-09

## Completed steps
- [ ] Prompt 01 — Analysis
- [x] Prompt 02 — LangGraph state schema ✓
- [x] Prompt 03 — LangGraph graph + parallelismo ✓
- [x] Prompt 04 — Knowledge Agent (RAG generico) ✓
- [ ] Prompt 05 — MCP Servers
- [ ] Prompt 06 — Backend FastAPI integration
- [ ] Prompt 07 — Agent nodes reali (design + altri)
- [ ] Prompt 08 — Checkpoint + human-in-the-loop
- [ ] Prompt 09 — UI Knowledge Sources
- [ ] Prompt 10 — Testing

## Current step
**Prompt 04 — Knowledge Agent COMPLETED**
Working on: Created complete RAG system with source-agnostic architecture
Blocker: none

## Decisions made
- LangGraph invece di CrewAI: controllo deterministico del flusso
- pgvector invece di Qdrant: già presente Postgres, riduce infra
- MCP servers come processi separati su porte 8001-8003
- Multilingual embeddings: paraphrase-multilingual-mpnet-base-v2
- interrupt_before=["backend_agent"] per human-in-the-loop sul design
- **OrchestraState TypedDict**: 17 fields with producer→consumer docstrings
- **AgentStatus enum**: str subclass for JSON serialization compatibility
- **Parallel execution**: backend + frontend + backlog run concurrently after design
- **Conditional routing**: integration_check routes to error_handler if any agent failed
- **Send API**: LangGraph Send() for parallel fan-out (3 agents receive same state)
- **Knowledge sources**: Abstract base class with 3 implementations (web, file, API)
- **Content deduplication**: SHA-256 hashing in vector store to prevent duplicates
- **Chunking strategy**: ~500 words with 50-word overlap for all sources
- **Embedding model**: paraphrase-multilingual-mpnet-base-v2 (768-dim, IT/EN/FR/DE support)

## Files created by this migration
### Prompt 02 (2026-04-08)
- `AI_agents/graph/__init__.py` - Package initialization
- `AI_agents/graph/nodes/__init__.py` - Nodes package initialization
- `AI_agents/graph/state.py` - OrchestraState TypedDict + AgentStatus enum (4504 bytes)
  - 17 state fields (4 user input, 7 agent data, 2 supporting, 4 orchestration)
  - AgentStatus enum with 5 values (PENDING, RUNNING, COMPLETED, FAILED, SKIPPED)
  - Comprehensive docstrings mapping producers → consumers
  - All imports verified, type checking passes

### Prompt 03 (2026-04-09)
- `AI_agents/graph/graph.py` - LangGraph StateGraph definition (11KB)
  - 9 agent node stubs: knowledge_retrieval, design, backend_agent, frontend_agent, backlog_agent, integration_check, error_handler, devops_agent, publish_agent
  - `fan_out_to_parallel_agents()`: Send API for parallel execution after design
  - `route_after_integration_check()`: conditional routing (errors → error_handler, success → devops_agent)
  - `create_graph()`: builds StateGraph with edges
  - `app`: compiled graph (checkpointer=None for now)
  - All nodes update current_step, completed_steps, agent_statuses

### Prompt 04 (2026-04-09)
- `AI_agents/knowledge/__init__.py` - Package initialization
- `AI_agents/knowledge/sources/__init__.py` - Exports all source classes
- `AI_agents/knowledge/sources/base_source.py` - Abstract KnowledgeSource + Document dataclass
- `AI_agents/knowledge/sources/web_scraper_source.py` - Web crawling with BeautifulSoup (7KB)
  - Configurable CSS selectors, depth-limited crawling, robots.txt compliance
  - Custom auth headers, content chunking, link extraction
- `AI_agents/knowledge/sources/file_source.py` - Local file processing (6KB)
  - Supports .txt, .md, .pdf (pypdf), .docx (python-docx)
  - Recursive directory scanning, chunking with overlap
- `AI_agents/knowledge/sources/api_source.py` - REST API fetching (5KB)
  - Dot-notation JSON path extraction, auth headers, chunking
- `AI_agents/knowledge/vector_store.py` - pgvector service (8KB)
  - sentence-transformers embeddings, SHA-256 deduplication
  - Cosine similarity search, auto table creation, connection pooling
- `AI_agents/knowledge/knowledge_agent.py` - Main RAG orchestrator (5KB)
  - Searches vector store, triggers fresh fetch if needed, returns top-K
  - Error handling with state["errors"] dict, AgentStatus tracking
- `requirements-knowledge.txt` - New dependencies for Knowledge Agent

## Next action
Execute Prompt 05: Create MCP Server wrappers
- Create `mcp_servers/github_server.py` (GitHub API wrapper)
- Create `mcp_servers/confluence_server.py` (Confluence API wrapper)
- Create `mcp_servers/jira_server.py` (Jira API wrapper)
- Each server runs on separate port (8001-8003), uses encrypted tokens from DB
