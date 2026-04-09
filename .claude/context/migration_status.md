# Migration Status — Last updated: 2026-04-09

## Completed steps
- [ ] Prompt 01 — Analysis
- [x] Prompt 02 — LangGraph state schema ✓
- [x] Prompt 03 — LangGraph graph + parallelismo ✓
- [x] Prompt 04 — Knowledge Agent (RAG generico) ✓
- [x] Prompt 05 — MCP Servers ✓
- [ ] Prompt 06 — Backend FastAPI integration
- [ ] Prompt 07 — Agent nodes reali (design + altri)
- [ ] Prompt 08 — Checkpoint + human-in-the-loop
- [ ] Prompt 09 — UI Knowledge Sources
- [ ] Prompt 10 — Testing

## Current step
**Prompt 05 — MCP Servers COMPLETED**
Working on: Created MCP server layer for GitHub, Azure DevOps, and deployment tools
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

## Next action
Execute Prompt 06: Backend FastAPI Integration
- Initialize VectorStoreService at FastAPI startup
- Inject user tokens as env vars before starting MCP servers
- Wire LangGraph app with FastAPI orchestrator endpoint
- Load knowledge sources configuration from DB
