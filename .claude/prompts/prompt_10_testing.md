# Prompt 10 — Testing Suite

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.
All features are implemented.

## Task: Add test coverage for all new AI components

## Files to create

### `tests/conftest.py`
Shared fixtures:
- `mock_state` — a valid `OrchestraState` with minimal required fields populated
- `mock_vector_store` — mocked `VectorStoreService` with:
  - `search()` returning empty list by default (configurable)
  - `upsert()` as a no-op mock
- `mock_llm` — mocked LangChain LLM that returns a fixed `DesignSchema` response
- `mock_mcp_client` — mocked `MCPClientManager`

### `tests/test_graph_state.py`
- `test_orchestrastate_instantiation` — state can be created with required fields
- `test_agent_status_transitions` — all `AgentStatus` enum values are valid
- `test_errors_dict_update` — errors field can be set per agent key
- `test_completed_steps_append` — completed_steps can be extended

### `tests/test_knowledge_agent.py`
All tests use mocked sources and mocked vector store:
- `test_empty_store_triggers_fetch` — if `search()` returns [],
  all sources' `fetch()` methods are called
- `test_populated_store_skips_fetch` — if `search()` returns 3+ results,
  source `fetch()` is NOT called
- `test_multilingual_query` — agent handles Italian and English queries
  without error
- `test_source_fetch_failure_is_graceful` — if a source raises an exception,
  agent logs the error and continues with other sources (does not crash)
- `test_rag_context_set_in_state` — after run, `state["rag_context"]`
  is populated with Document objects

### `tests/test_graph_flow.py`
Integration tests with mocked LLM and MCP:
- `test_graph_runs_end_to_end` — graph runs from START to END given
  a simple requirements string, all steps complete
- `test_backend_agent_failure_routes_to_error_handler` — if backend_agent
  sets `state["errors"]["backend"]`, the error_handler node is invoked
- `test_parallel_nodes_all_update_state` — backend, frontend, and backlog
  nodes all update state correctly when run concurrently
- `test_state_preserved_across_nodes` — data set in design node
  is accessible in backend and frontend nodes

### `tests/test_mcp_servers.py`
- `test_github_server_tool_list` — server exposes expected tools
- `test_push_files_formats_request_correctly` — correct payload structure
- `test_missing_token_raises_mcp_auth_error` — missing env var raises
  `MCPAuthError`, not a generic `KeyError` or `AttributeError`
- `test_tool_call_logged` — every tool call produces a log entry

## Setup
- Use `pytest` + `pytest-asyncio` for all async tests
- Use `unittest.mock` / `pytest-mock` for mocking
- Add `pytest.ini` or `pyproject.toml` section:
  ```toml
  [tool.pytest.ini_options]
  asyncio_mode = "auto"
  testpaths = ["tests"]
  ```

Before outputting, mentally trace each test to verify there are no
obvious import errors or missing fixtures.
Write complete test files.
When done, update `.claude/context/migration_status.md` marking Prompt 10 complete
and the migration as DONE.
