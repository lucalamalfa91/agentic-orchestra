# Prompt 05 — MCP Server Layer

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.

## Context: how user credentials work with MCP servers
Users connect their accounts ONCE via the UI (GitHub OAuth already exists,
other tokens saved encrypted in DB via `encryption_service.py` and
`DeployProviderAuth` model). At generation runtime, the backend reads the
user's tokens from DB, decrypts them, and injects them as env vars before
starting the MCP server processes. The user is NEVER interrupted during
agent execution for authentication.

## Task: Create `mcp_servers/` directory

### `mcp_servers/base_server.py`
Base helper for all MCP servers:
- Standard error handling and JSON response format
- `inject_token(env_var: str)` — reads from environment, raises
  `MCPAuthError` with clear message if missing (never a generic KeyError)
- Structured logging of all tool calls (tool name, args, duration, status)

### `mcp_servers/github_server.py`
MCP server exposing tools:
- `create_repository(name, private, description)`
- `push_files(repo, branch, files: list[{path, content}], message)`
- `create_pull_request(repo, title, head, base, body)`
- `read_file(repo, path, ref)`
Auth: reads `GITHUB_TOKEN` from environment.

### `mcp_servers/azuredevops_server.py`
MCP server exposing tools:
- `create_work_item(project, type, title, description, tags)`
- `create_sprint(project, name, start_date, end_date)`
- `create_pipeline(project, name, yaml_path, repo_url)`
Auth: reads `AZDO_TOKEN` and `AZDO_ORG` from environment.

### `mcp_servers/deploy_server.py`
MCP server exposing tools:
- `deploy_railway(project_name, env_vars: dict, dockerfile_path)`
- `deploy_docker_compose(compose_content: str, target_host: str)`
Auth: reads `RAILWAY_TOKEN` from environment.

### `mcp_servers/client.py`
Class `MCPClientManager`:
- `async def get_tools(server_names: list[str]) -> list[Tool]`
- `async def call_tool(server: str, tool_name: str, args: dict) -> ToolResult`
- Connects to servers via HTTP SSE
- Servers run as separate processes; this client connects to them

### `mcp_servers/__init__.py`
Empty.

### `mcp_servers/README.md`
Document:
- How to start each server (command)
- Port assignments (github: 8001, azuredevops: 8002, deploy: 8003)
- How the backend injects user tokens at runtime via env vars
- How to add a new MCP server for a new integration (step-by-step)

Use the official `mcp` Python library (`pip install mcp`).
Write complete working code for all files.
When done, update `.claude/context/migration_status.md` marking Prompt 05 complete.
