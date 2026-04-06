# Prompt 02 — LangGraph State Schema

Based on your previous analysis of `lucalamalfa91/agentic-orchestra`
(see `.claude/context/migration_status.md`), design the LangGraph state schema.
Do not modify any existing files.

## Task: Create `AI_agents/graph/state.py`

The file must define a `TypedDict` called `OrchestraState` with ALL fields
needed to carry data between agents in the LangGraph graph.

Requirements:
- Fields to include:
  - `requirements`: str — raw text from user
  - `parsed_requirements`: Optional[dict] — structured after parsing
  - `design_yaml`: Optional[dict] — produced by Design Agent
  - `api_schema`: Optional[list] — extracted from design_yaml
  - `db_schema`: Optional[list] — extracted from design_yaml
  - `backend_code`: Optional[dict] — produced by Backend Agent
  - `frontend_code`: Optional[dict] — produced by Frontend Agent
  - `devops_config`: Optional[dict] — produced by DevOps Agent
  - `backlog_items`: Optional[list] — produced by Backlog Agent
  - `rag_context`: Optional[list] — produced by Knowledge Agent
  - `errors`: dict[str, str] — key=agent_name, value=error message
  - `current_step`: str
  - `completed_steps`: list[str]
  - `project_id`: str
  - `user_id`: str
  - `ai_provider`: str — "openai" or "anthropic"
  - `agent_statuses`: dict[str, str] — key=agent_name, value=AgentStatus

- Add a short docstring comment on each field explaining:
  what agent PRODUCES it and what agent CONSUMES it
- Use `Optional[]` for fields that may not be present at all steps
- Add an `AgentStatus` enum with values:
  PENDING, RUNNING, COMPLETED, FAILED, SKIPPED

## Also create:
- `AI_agents/graph/__init__.py` (empty)
- `AI_agents/graph/nodes/__init__.py` (empty)

Output the complete file contents.
Do not modify any existing files.
When done, update `.claude/context/migration_status.md` marking Prompt 02 complete.
