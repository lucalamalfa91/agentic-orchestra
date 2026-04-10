# Migration Status — Last updated: 2026-04-10

## Completed steps
- [ ] Prompt 01 — Analysis
- [x] Prompt 02 — LangGraph state schema ✓
- [x] Prompt 03 — LangGraph graph + parallelismo ✓
- [x] Prompt 04 — Knowledge Agent (RAG generico) ✓
- [x] Prompt 05 — MCP Servers ✓
- [x] Prompt 06 — Backend FastAPI integration ✓
- [x] Prompt 07a — design_node (real implementation) ✓
- [x] Prompt 07b — BaseAgent abstraction ✓
- [x] Prompt 07c — DeepAgents integration ✓
- [x] Prompt 07d — backend_agent, frontend_agent, backlog_agent nodes (using BaseAgent) ✓
- [x] Prompt 07e — devops_agent node (using BaseAgent) ✓
- [x] Prompt 07f — publish_agent node verification ✓
- [x] Prompt 08 — Checkpoint + human-in-the-loop ✓
- [ ] Prompt 09 — UI Knowledge Sources
- [ ] Prompt 10 — Testing

## Current step
**Prompt 08 — Checkpoint + Human-in-the-Loop COMPLETED**
Working on: Added PostgreSQL checkpointing and design approval flow
Next: Prompt 09 — UI Knowledge Sources
Blocker: None

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
- **BaseAgent abstraction**: Shared foundation for all agent nodes (Prompt 07b)
- **Agent DRY pattern**: Agents implement only system_prompt(), build_input(), parse_output()
- **Centralized retry logic**: MAX_RETRIES=2 in BaseAgent.run(), automatic error handling
- **Consistent state updates**: BaseAgent auto-updates current_step, completed_steps, agent_statuses
- **Deep Agents integration**: design_node and publish_node use Deep Agents framework (Prompt 07c)
- **Selective Deep Agents use**: Only nodes with multi-step planning or tool loops use Deep Agents
- **Deep Agents planning**: enable_todos=True forces agent to plan before executing
- **Deep Agents filesystem tools**: ls, read_file for safe file operations in publish_node
- **Hybrid architecture**: Deep Agents nodes coexist with BaseAgent nodes in same LangGraph graph

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

### Prompt 07a — design_node (2026-04-09)
- `AI_agents/utils/__init__.py` - Utils package initialization, exports get_llm_client
- `AI_agents/utils/llm_client.py` - LLM client factory (3.6KB)
  - get_llm_client(provider, config) factory function
  - Supports "openai" and "anthropic" providers
  - Reads API keys from env vars (injected by backend)
  - Configurable model, temperature, max_tokens
  - Default: temp=0.1, max_tokens=4000 for design tasks
- `AI_agents/graph/nodes/design_node.py` - Design agent implementation (8.5KB)
  - Pydantic schemas: DesignSchema, StackConfig, Entity, EntityField, APIEndpoint
  - design_node(state) async function with structured LLM output
  - Reads state["requirements"] and state["rag_context"]
  - Uses LangChain .with_structured_output() to avoid parsing failures
  - Retry logic: up to 2 retries with error feedback in prompt
  - Populates: state["design_yaml"], state["api_schema"], state["db_schema"]
  - Error handling: sets state["errors"]["design"], never raises exceptions
  - Updates: state["current_step"], state["completed_steps"], state["agent_statuses"]
- `AI_agents/graph/nodes/__init__.py` - UPDATED to export design_node
- `AI_agents/graph/graph.py` - UPDATED to import and use design_node
  - Replaced stub design() function with real design_node import
  - graph.add_node("design", design_node) now uses real implementation
  - Comment updated: "Real implementations: design_node (Prompt 07)"
- `requirements-knowledge.txt` - UPDATED with LLM providers
  - Added langchain-openai>=0.2.0
  - Added langchain-anthropic>=0.2.0

### Prompt 07b — BaseAgent Abstraction (2026-04-09)
- `AI_agents/base_agent.py` - Abstract base class for all agent nodes (7.8KB)
  - BaseAgent abstract class with MAX_RETRIES = 2, agent_name attribute
  - `_build_chain()`: constructs LangChain LCEL chain (prompt | llm | parser)
  - Abstract methods: `system_prompt()`, `build_input()`, `parse_output()`
  - `run()`: main execution method with retry logic and error handling
  - Centralizes: LLM initialization, prompt rendering, retries, logging, state updates
  - Error handling: catches all exceptions, sets state["errors"], never raises
  - Updates: current_step, completed_steps, agent_statuses automatically
  - Comprehensive docstrings explaining design pattern and benefits
- `AI_agents/base_agent_test_demo.py` - Validation demo script (3.8KB)
  - EchoAgent: minimal concrete BaseAgent subclass
  - main(): runs EchoAgent with fake OrchestraState
  - Validates: imports work, LLM client initializes, retry logic functions
  - Checks: state updates (agent_statuses, completed_steps, errors)
  - NOT a pytest test — standalone script for quick validation
  - Includes instructions for deletion after validation

### Prompt 07c — DeepAgents Integration (2026-04-10)
- `requirements-knowledge.txt` - UPDATED with deepagents package
  - Added: deepagents (LangChain Deep Agents framework)
  - Enables multi-step planning, filesystem tools, sub-agent spawning
- `AI_agents/graph/nodes/design_node.py` - REFACTORED to use Deep Agents (5.7KB)
  - Replaced Pydantic structured output with Deep Agents planning
  - Uses create_deep_agent() with enable_todos=True for step-by-step design
  - Simplified JSON parsing (strips markdown fences, parses raw JSON)
  - Maintains same state contract: design_yaml, api_schema, db_schema
  - Error handling: catches JSON errors, sets state["errors"]["design"]
- `AI_agents/graph/nodes/publish_node.py` - NEW Deep Agents node (4.8KB)
  - Uses Deep Agents with filesystem tools (ls, read_file) + GitHub MCP tools
  - Agent autonomously: lists files → reads content → creates repo → pushes files
  - Extracts repository URL from agent response via regex
  - Populates state["github_repo_url"]
  - Error handling: catches all exceptions, sets state["errors"]["publish_agent"]
- `AI_agents/graph/nodes/__init__.py` - UPDATED exports
  - Added publish_node to exports
  - Documented Deep Agents integration strategy in module docstring
- `AI_agents/graph/graph.py` - UPDATED agent stubs
  - Imported publish_node, replaced stub with real implementation
  - Added docstring comments to backend_agent, frontend_agent, backlog_agent, devops_agent
  - Comment: "Deep Agents not used here: one-shot code generator, BaseAgent sufficient"
  - Updated graph.add_node("publish_agent", publish_node) to use real implementation

**Deep Agents Design Decisions** (Prompt 07c):
- **Selective application**: Only design_node and publish_node use Deep Agents
- **design_node rationale**: Multi-step process (parse → analyze → structure → validate)
- **publish_node rationale**: Tool loop required (filesystem + GitHub MCP tools)
- **Not for simple nodes**: backend/frontend/backlog/devops remain BaseAgent (one-shot LLM calls)
- **Hybrid graph**: Deep Agents nodes coexist with BaseAgent nodes in same LangGraph
- **LangGraph remains orchestrator**: Deep Agents used inside specific nodes, not replacing top-level flow

### Prompt 07d — Backend/Frontend/Backlog Agents (2026-04-10)
- `AI_agents/graph/nodes/backend_node.py` - Backend code generator (LANGUAGE-AGNOSTIC)
  - BackendAgent extends BaseAgent
  - **Polyglot support**: Generates backend in ANY framework specified in design_yaml["stack"]
  - Supported: C#/ASP.NET Core, Python/FastAPI, Node.js/Express, Java/Spring Boot, Go/Gin, Ruby/Rails, PHP/Laravel, etc.
  - Inputs: design_yaml, api_schema, db_schema, rag_context
  - Output: state["backend_code"] as dict {file_path: code_content}
  - Features: Framework-specific patterns, ORM, API docs, validation, error handling
  - JSON output format with framework-appropriate file structure
  - Retry logic (MAX_RETRIES=2) via BaseAgent
- `AI_agents/graph/nodes/frontend_node.py` - Frontend code generator (FRAMEWORK-AGNOSTIC)
  - FrontendAgent extends BaseAgent
  - **Multi-framework support**: Generates frontend in ANY framework specified in design_yaml["stack"]
  - Supported: React, Vue 3, Angular, Svelte, Next.js, Nuxt, SolidJS, Qwik, etc. (TypeScript or JavaScript)
  - Inputs: design_yaml, api_schema, rag_context
  - Output: state["frontend_code"] as dict {file_path: code_content}
  - Features: Framework-specific patterns, routing, state management, API client, styling
  - JSON output format with framework-appropriate file structure
  - Responsive design, WCAG 2.1 AA accessibility
- `AI_agents/graph/nodes/backlog_node.py` - Backlog generator (8.5KB)
  - BacklogAgent extends BaseAgent
  - Generates product backlog (user stories, technical tasks, testing, docs, technical debt)
  - Inputs: requirements, design_yaml, api_schema, db_schema, rag_context
  - Output: state["backlog_items"] as list of dicts [{title, body, labels, priority}]
  - Features: GitHub issue format, acceptance criteria, technical notes, dependencies
  - Priority levels: critical, high, medium, low
  - Labels: type + component + priority (e.g., ["feature", "backend", "P1"])
  - Generates 15-25 comprehensive backlog items
- `AI_agents/graph/nodes/__init__.py` - UPDATED exports
  - Added backend_node, frontend_node, backlog_node exports
  - Updated module docstring with BaseAgent nodes section
- `AI_agents/graph/graph.py` - UPDATED to use real implementations
  - Imported backend_node, frontend_node, backlog_node
  - Replaced stub functions with real node implementations
  - Updated graph.add_node() calls to use imported nodes
  - Updated comments to reflect Prompt 07d completion

**BaseAgent pattern** (established by Prompt 07b):
- All new agent nodes should extend BaseAgent
- Implement only: system_prompt(), build_input(), parse_output()
- BaseAgent handles: LLM init, retries (MAX_RETRIES=2), logging, state updates
- Error handling: BaseAgent catches exceptions, sets state["errors"], never raises
- Automatic state updates: current_step, completed_steps, agent_statuses

### Prompt 07e — DevOps Agent (2026-04-10)
- `AI_agents/graph/nodes/devops_node.py` - NEW DevOps configuration generator (13.8KB)
  - DevopsAgent extends BaseAgent
  - Generates CI/CD workflows, Docker configuration, deployment manifests
  - **Supported CI/CD platforms**: GitHub Actions, Azure Pipelines, GitLab CI, CircleCI
  - **Supported deployment targets**: Docker Compose, Kubernetes, Railway, Vercel, Azure App Service, AWS ECS
  - Inputs: design_yaml, backend_code, frontend_code, rag_context
  - Output: state["devops_config"] as dict {file_path: config_content}
  - **Generated files**:
    - CI/CD workflow (.github/workflows/ci-cd.yml, azure-pipelines.yml, .gitlab-ci.yml)
    - Docker configuration (backend/Dockerfile, frontend/Dockerfile, docker-compose.yml, .dockerignore)
    - Deployment manifests (k8s/*, railway.json, vercel.json, etc.)
    - Environment template (.env.example, README-DEPLOYMENT.md)
  - **CI/CD features**:
    - Pipeline stages: checkout, install deps, lint, test, build images, push to registry, deploy
    - Environment variables via secrets (GitHub Secrets, Azure Key Vault)
    - Triggers: push to main → production, push to develop → staging, PRs → tests only
  - **Dockerfile best practices**:
    - Multi-stage builds (builder + runtime stages)
    - Framework-specific optimization (Node.js/alpine, Python/slim, .NET/aspnet, Go/scratch)
    - Non-root user, layer caching, health checks
    - Minimal image size (alpine, distroless)
  - **Docker Compose features**:
    - Services: backend, frontend, database, redis (optional), nginx (optional)
    - Custom network, persistent volumes, health checks
    - Environment variables from .env file
  - **Security**: No hardcoded secrets, .env templates, vulnerability scanning, resource limits
  - Retry logic (MAX_RETRIES=2) via BaseAgent
- `AI_agents/graph/nodes/__init__.py` - UPDATED exports
  - Added devops_node export
  - Updated module docstring with Prompt 07e section
- `AI_agents/graph/graph.py` - UPDATED to use devops_node implementation
  - Imported devops_node from nodes
  - Removed stub devops_agent function
  - Updated graph.add_node("devops_agent", devops_node) to use real implementation
  - Updated comments: devops_node now in "Real implementations" list
  - Stubs remaining: knowledge_retrieval, integration_check

**Verification**:
- ✅ devops_node imports successfully
- ✅ Python syntax check passed
- ✅ DevopsAgent.agent_name = "devops_agent"
- ✅ Extends BaseAgent correctly
- ✅ Implements system_prompt(), build_input(), parse_output()

### Prompt 07f — Publish Agent Verification (2026-04-10)
- **Dependencies installed**: deepagents==0.5.1, mcp==1.27.0
- **publish_node.py fixed**:
  - Removed non-existent import `from deepagents.tools.filesystem`
  - Changed `llm=llm` to `model=llm` (correct API)
  - Removed redundant tools (filesystem tools are built-in)
- **design_node.py fixed**:
  - Changed `llm=llm` to `model=llm`
  - Removed non-existent parameter `enable_todos=True`
- **Verification**:
  - ✅ Both nodes have valid Python syntax
  - ✅ Correctly imported in graph.py (lines 18-19)
  - ✅ Correctly added to graph (lines 152, 159)
  - ✅ Exported from nodes/__init__.py
- **Known issue**: mcp_servers/client.py uses deprecated API (Prompt 05 issue, not 07f)

### Prompt 08 — Checkpoint + Human-in-the-Loop (2026-04-10)
- **AI_agents/graph/graph.py** - UPDATED with PostgreSQL checkpointer (260 lines)
  - Added imports: `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio`, `DATABASE_URL`
  - Created async `get_app()` function for lazy checkpointer initialization
  - Checkpointer setup: `AsyncPostgresSaver.from_conn_string(DATABASE_URL)`, `await checkpointer.setup()`
  - Graph compiled with `interrupt_before=["backend_agent"]` to pause after design phase
  - Maintains backward compatible `app` export (legacy sync version)
  - Global `_app` and `_checkpointer` for singleton pattern
- **orchestrator-ui/backend/api/generation_control.py** - NEW router (375 lines)
  - Three endpoints for design approval workflow:
    - `GET /api/generation/{project_id}/state` - retrieve checkpoint state for design review
    - `POST /api/generation/{project_id}/approve` - accept optional design_changes, resume execution
    - `POST /api/generation/{project_id}/reject` - cancel generation, mark project as failed
  - Uses `app.aget_state()` to read checkpoint, `app.aupdate_state()` to modify design
  - Pydantic schemas: `DesignApprovalRequest`, `DesignStateResponse`
  - Logs design approval/rejection/modifications to `GenerationLog` table
  - WebSocket broadcasts for progress updates (design_approved, design_rejected)
  - CORS preflight handlers for all endpoints
- **orchestrator-ui/backend/main.py** - UPDATED router registration
  - Import: `generation_control` from api
  - Registered: `app.include_router(generation_control.router)`
- **orchestrator-ui/frontend/src/types/index.ts** - ADDED design state types
  - `EntityField`, `Entity`, `APIEndpoint` interfaces
  - `DesignYaml` interface with optional app_name, description, stack, entities, api_endpoints
  - `DesignStateResponse` interface matching backend Pydantic schema
  - `DesignApprovalRequest` interface for approval endpoint
- **orchestrator-ui/frontend/src/api/client.ts** - ADDED generationControlApi
  - `getDesignState(projectId)` - GET request to fetch checkpoint state
  - `approveDesign(projectId, designChanges?)` - POST with optional modifications
  - `rejectDesign(projectId)` - POST to cancel generation
  - Updated imports to include `DesignStateResponse`, `DesignApprovalRequest`
- **orchestrator-ui/frontend/src/screens/DesignReviewScreen.tsx** - NEW component (450 lines)
  - Displays design for human approval: app name, description, tech stack, entities table, API endpoints list
  - **Entities section**: Table view with field names, types, required flags
  - **API endpoints section**: List with method badges (colored by HTTP verb), paths, descriptions
  - **Advanced JSON editor**: Toggle to show/hide raw design_yaml JSON editor
  - Action buttons: "Reject Design" (red), "Approve & Continue" (gradient)
  - Loading states, error handling, glassmorphism UI matching existing screens
  - Integrates with `generationControlApi` for state fetch and approval/rejection
  - Reuses existing Tailwind patterns and CSS variables from MVPCreationScreen

**Human-in-the-Loop Flow** (Prompt 08):
1. User submits MVP generation request
2. LangGraph executes: knowledge_retrieval → design → **INTERRUPT**
3. Backend checkpoint saves state, frontend polls for design state
4. DesignReviewScreen displays design (entities, API endpoints, stack)
5. User reviews, optionally edits JSON, then clicks "Approve & Continue" or "Reject"
6. If approved: backend resumes graph execution (backend_agent, frontend_agent, backlog_agent in parallel)
7. If rejected: generation cancelled, project marked as failed

**Technical Decisions** (Prompt 08):
- PostgreSQL checkpointer instead of in-memory: enables multi-session persistence
- Lazy initialization pattern: checkpointer setup only when `get_app()` first called
- Interrupt point: `interrupt_before=["backend_agent"]` pauses after design, before expensive code generation
- Thread ID: `project_id` used as `thread_id` for checkpoint identification
- Design changes: optional deep merge into `design_yaml`, logged to DB
- Frontend integration: DesignReviewScreen can be inserted into existing generation progress flow

**Verification**:
- ✅ graph.py imports successfully with AsyncPostgresSaver
- ✅ generation_control.py router has valid FastAPI endpoints
- ✅ Pydantic schemas match between backend and frontend TypeScript types
- ✅ DesignReviewScreen component follows existing UI patterns
- ✅ API client methods added with correct type signatures
- ✅ CORS headers included for all endpoints

## Next action
Move to Prompt 09: UI Knowledge Sources
- Frontend screens for managing knowledge sources (web, file, API)
- Integration with backend knowledge API endpoints (from Prompt 06)
- Connect to Knowledge Agent RAG workflow
