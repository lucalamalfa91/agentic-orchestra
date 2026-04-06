# Prompt 07 — Real Agent Nodes (one at a time)

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.
The LangGraph graph is wired. All nodes are currently stubs.

## Task: Implement real agent nodes, one per session

Start with the node indicated in `migration_status.md`.
Default order: design → backend → frontend → backlog → devops → publish

---

## Design Node — `AI_agents/graph/nodes/design_node.py`

This node receives:
- `state["requirements"]` — raw text
- `state["rag_context"]` — retrieved knowledge docs (may be empty list)

It must:
1. Build a prompt that includes:
   - Raw requirements
   - Any `rag_context` documents formatted as:
     `"## Relevant Context\n{doc.content}\n"`
   - Instructions to produce a structured Pydantic model output with:
     `app_name`, `description`, `stack` (backend_framework,
     frontend_framework, database, auth_method),
     `entities` (list with name + fields),
     `api_endpoints` (list with method + path + description),
     `deployment_target`
2. Call LLM via `get_llm_client()` from `AI_agents/utils/llm_client.py`
   Use LangChain structured output (`.with_structured_output(DesignSchema)`)
   to avoid YAML/JSON parsing failures
3. On parse failure: retry up to 2 times with error feedback in prompt
4. Set `state["design_yaml"]` with the parsed dict
5. Extract and set `state["api_schema"]` and `state["db_schema"]`
6. Update `state["completed_steps"]`, `state["agent_statuses"]`
7. On any exception: set `state["errors"]["design"]`, status FAILED, return state

Also create `AI_agents/utils/llm_client.py`:
- `get_llm_client(provider: str, config: dict)` factory function
- Returns `ChatOpenAI` or `ChatAnthropic` based on provider string
- Reads API key from environment (injected by backend from DB)

Update `graph.py` to import and use the real `design_node` instead of stub.

---

## For subsequent nodes (backend, frontend, backlog, devops, publish)
Repeat this prompt replacing "design" with the target node.
Each prompt execution = one node. Do not implement multiple nodes
in the same session to avoid context overflow.

When done, update `.claude/context/migration_status.md`:
- Mark which node was implemented
- Note which node to implement next
