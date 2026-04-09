# Migration Status — Last updated: 2026-04-09

## Completed steps
- [ ] Prompt 01 — Analysis
- [x] Prompt 02 — LangGraph state schema ✓
- [x] Prompt 03 — LangGraph graph + parallelismo ✓
- [x] Prompt 04 — Knowledge Agent (RAG generico) ✓
- [x] Prompt 05 — MCP Servers ✓
- [x] Prompt 06 — Backend FastAPI integration ✓
- [ ] Prompt 07 — Agent nodes reali (design + altri)
- [ ] Prompt 08 — Checkpoint + human-in-the-loop
- [ ] Prompt 09 — UI Knowledge Sources
- [ ] Prompt 10 — Testing

## Current step
**Prompt 06 — Backend FastAPI Integration COMPLETED**
Working on: Integrated LangGraph orchestrator into FastAPI, added KnowledgeSourceConfig model
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
- **MCP architecture**: Servers run as separate processes, stdio communication via MCP protocol
- **Token injection**: Backend decrypts user tokens from DB, injects as env vars before server start
- **Structured logging**: All tool calls logged with name, args, duration, status
- **Standardized responses**: success/error format across all MCP servers
- **Alembic migrations**: Initialized for database schema versioning, first migration for KnowledgeSourceConfig
- **LangGraph integration**: Orchestrator.py refactored from subprocess to direct LangGraph streaming
- **WebSocket format preservation**: Map LangGraph events to legacy STEP_MARKERS for frontend compatibility
- **Knowledge sources encryption**: All config_json encrypted before DB storage using encryption_service
- **Background indexing**: FastAPI BackgroundTasks for async knowledge source indexing

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

### Prompt 05 (2026-04-09)
- `mcp_servers/__init__.py` - Package initialization
- `mcp_servers/base_server.py` - Base utilities for all MCP servers (3KB)
  - `MCPAuthError` custom exception, `inject_token()` helper
  - `@log_tool_call` decorator for structured logging (tool name, args, duration, status)
  - `format_error_response()`, `format_success_response()` for standardized responses
- `mcp_servers/github_server.py` - GitHub integration (10KB)
  - Tools: create_repository, push_files, create_pull_request, read_file
  - Uses PyGithub library, reads GITHUB_TOKEN from env
  - Batch file push in single commit
- `mcp_servers/azuredevops_server.py` - Azure DevOps integration (9KB)
  - Tools: create_work_item, create_sprint, create_pipeline
  - Uses azure-devops library, reads AZDO_TOKEN + AZDO_ORG from env
  - JsonPatchOperation for work item creation
- `mcp_servers/deploy_server.py` - Deployment tools (8KB)
  - Tools: deploy_railway, deploy_docker_compose
  - Railway via GraphQL API, Docker Compose via subprocess
  - Supports local and remote (SSH) deployment
- `mcp_servers/client.py` - MCPClientManager (6KB)
  - Manages connections to multiple MCP servers via stdio
  - `get_tools()` - retrieve tools from servers with caching
  - `call_tool()` - execute tools with error handling
  - Server registry with command/args configuration
- `mcp_servers/README.md` - Comprehensive documentation (7KB)
  - How to start each server, port assignments
  - Authentication flow (user connects → backend injects tokens)
  - Step-by-step guide for adding new MCP servers
  - Testing examples, error handling patterns
- `test_mcp_imports.py` - Import verification test

### Prompt 06 (2026-04-09)
- `orchestrator-ui/backend/models.py` - Added KnowledgeSourceConfig model + SourceType enum
  - UUID primary key, user_id FK, name, source_type (web/file/api)
  - Encrypted config_json field, last_indexed_at timestamp
  - Relationship to User model
- `orchestrator-ui/backend/alembic/` - Alembic migration system initialized
  - `alembic.ini` - Configuration file
  - `alembic/env.py` - Environment setup, imports Base and models, overrides DATABASE_URL
  - `alembic/versions/29ffc17e697b_add_knowledge_source_config.py` - Initial migration
- `orchestrator-ui/backend/crud.py` - Added knowledge source CRUD functions (6 functions)
  - create_knowledge_source(), get_knowledge_sources(), get_knowledge_source()
  - delete_knowledge_source(), update_last_indexed()
  - All operations include user_id ownership verification
- `orchestrator-ui/backend/schemas.py` - Added Pydantic schemas for knowledge sources
  - KnowledgeSourceCreate (request schema with config dict)
  - KnowledgeSourceResponse (response schema with datetime serialization)
  - IndexingStatusResponse (status polling response)
- `orchestrator-ui/backend/api/knowledge.py` - New API router (8KB, 5 endpoints)
  - GET /api/knowledge/sources - list user's sources
  - POST /api/knowledge/sources - create source (encrypts config)
  - DELETE /api/knowledge/sources/{id} - delete source
  - POST /api/knowledge/index/{id} - trigger background indexing
  - GET /api/knowledge/index/{id}/status - poll indexing status
  - perform_indexing() background task using KnowledgeSource classes
- `orchestrator-ui/backend/orchestrator.py` - REFACTORED from subprocess to LangGraph (10KB)
  - Removed subprocess/threading approach
  - Added _inject_env_vars() for token/config injection
  - Added _build_initial_state() to construct OrchestraState
  - Added _map_event_to_step_info() to preserve STEP_MARKERS format
  - run_generation() now streams LangGraph events via app.astream()
  - AGENT_TO_STEP mapping preserves exact WebSocket message format
- `orchestrator-ui/backend/main.py` - Registered knowledge router
  - Import knowledge module
  - app.include_router(knowledge.router)

## Next action
Execute Prompt 07: Implement Real Agent Nodes
- Replace stub agent nodes in AI_agents/graph/nodes/ with real implementations
- design node: Generate design.yaml using architect_agent logic
- backend_agent node: Generate backend code using LLM
- frontend_agent node: Generate frontend code using LLM
- devops_agent node: Generate CI/CD workflows
- publish_agent node: Push to GitHub using MCP GitHub server
- All nodes must follow async def run(state: OrchestraState) -> OrchestraState signature
- All nodes must use get_llm_client() from AI_agents/utils/llm_client.py
- Error handling: set state["errors"][node_name], never raise exceptions
