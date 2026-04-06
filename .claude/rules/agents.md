---
paths: ["AI_agents/**"]
---
# Agent Development Rules

- Every agent node lives in `AI_agents/graph/nodes/{name}_node.py`
- Every node function signature:
  `async def run(state: OrchestraState) -> OrchestraState`
- Import `OrchestraState` from `AI_agents.graph.state` — never redefine it
- Always update `state["completed_steps"]` and `state["current_step"]` before returning
- LLM calls: use `get_llm_client()` from `AI_agents/utils/llm_client.py`
  Never instantiate `ChatOpenAI` or `ChatAnthropic` directly in node files
- On error: set `state["errors"]["{node_name}"] = str(e)`,
  set agent status to FAILED, return state — NEVER raise exceptions from nodes
- Knowledge sources: never hardcode URLs or file paths in agent code;
  always read from `state["rag_context"]` which is populated by KnowledgeAgent
