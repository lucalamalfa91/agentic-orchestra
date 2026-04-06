# Prompt 03 — LangGraph Graph with Parallelism

You are refactoring `lucalamalfa91/agentic-orchestra` to use LangGraph.
You have already created `AI_agents/graph/state.py` with `OrchestraState`.
Check `.claude/context/migration_status.md` before starting.

## Task: Create `AI_agents/graph/graph.py`

This file must define the main LangGraph `StateGraph` that replaces
`run_all_agents.py`. Do NOT modify `run_all_agents.py`.

## Graph structure (implement exactly this)

```
START
  └── knowledge_retrieval          (sequential)
        └── design                 (sequential)
              ├── backend_agent    (parallel fan-out)
              ├── frontend_agent   (parallel fan-out)
              └── backlog_agent    (parallel fan-out)
                    └── integration_check  (fan-in, waits for all 3)
                          └── [conditional]
                               ├── error_handler  (if any agent FAILED)
                               └── devops_agent   (if all OK)
                                     └── publish_agent
                                           └── END
```

## Implementation rules
- Each node is a function: `async def node_name(state: OrchestraState) -> OrchestraState`
- For now every node is a STUB:
  - logs `"[{node_name}] running..."`
  - updates `state["current_step"]` and appends to `state["completed_steps"]`
  - sets `state["agent_statuses"][node_name] = AgentStatus.COMPLETED`
  - returns state
- Use LangGraph `Send` API for the parallel fan-out after `design`
- Add conditional edge after `integration_check`:
  - if any value in `state["errors"]` is non-empty → route to `error_handler`
  - otherwise → route to `devops_agent`
- `error_handler` node: logs all errors from `state["errors"]`, sets
  `state["current_step"] = "FAILED"`, returns state
- At the bottom, compile the graph:
  ```python
  app = graph.compile(checkpointer=None)  # checkpointer added in Prompt 08
  ```
- Import `OrchestraState`, `AgentStatus` from `.state`

Output the complete `graph.py` file.
Do not modify any existing files.
When done, update `.claude/context/migration_status.md` marking Prompt 03 complete.
