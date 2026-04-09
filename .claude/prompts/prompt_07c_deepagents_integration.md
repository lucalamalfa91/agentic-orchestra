# Prompt 07c — Deep Agents Integration

You are working on `lucalamalfa91/agentic-orchestra`.
Check `.claude/context/migration_status.md` before starting.
`BaseAgent` abstraction from Prompt 07b is already in place.
All real agent nodes are implemented.
LangGraph remains the top-level orchestrator — do NOT replace it.

## Context

Some agent nodes in this project are more than one-shot LLM calls:
they involve multiple sub-steps, file reading/writing, or structured output
validation with retries. Deep Agents (from the `deepagents` package, built
on LangGraph) provides built-in primitives for these patterns:
- filesystem tools (`read_file`, `write_file`, `ls`)
- task planning (`write_todos`)
- sub-agent delegation (`task` tool)
- long-term memory via LangGraph Memory Store

This prompt selectively applies Deep Agents only where it adds clear value.
Do NOT apply Deep Agents to simple one-shot nodes (backlog_agent, devops_agent).

## Install

Add to `requirements.txt`:
```
deepagents
```

## Task 1: Refactor `design_node.py` using Deep Agents

The design node has multiple sub-steps (parse requirements → produce YAML →
extract api_schema → extract db_schema) and benefits from explicit planning.

Replace the current implementation in `AI_agents/graph/nodes/design_node.py`:

```python
from deepagents import create_deep_agent
from AI_agents.utils.llm_client import get_llm_client
from AI_agents.graph.state import OrchestraState, AgentStatus
import logging

logger = logging.getLogger("design_node")

async def design_node(state: OrchestraState) -> OrchestraState:
    provider = state.get("ai_provider", "anthropic")
    llm = get_llm_client(provider, {})

    agent = create_deep_agent(
        llm=llm,
        tools=[],  # no external tools needed here — pure LLM generation
        system_prompt=(
            "You are a .NET/React/Azure architect. "
            "Your job is to analyse software requirements and produce "
            "a structured design covering: app_name, stack, entities, "
            "api_endpoints, and deployment_target. "
            "Think step by step before writing the final design."
        ),
        # write_todos forces the agent to plan before executing
        enable_todos=True,
    )

    rag_docs = state.get("rag_context") or []
    rag_section = "\n".join(
        f"## Relevant Context\n{d['content']}" for d in rag_docs
    ) if rag_docs else ""

    message = f"""
Requirements:
{state['requirements']}

{rag_section}

Produce a JSON object with keys:
app_name, description, stack (backend_framework, frontend_framework,
database, auth_method), entities (list of {{name, fields}}),
api_endpoints (list of {{method, path, description}}),
deployment_target.
    """.strip()

    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})
        # extract the last assistant message as raw output
        raw = result["messages"][-1].content

        import json, re
        # strip markdown fences if present
        match = re.search(r"```(?:json)?\s*\n(.*?)```", raw, re.DOTALL)
        parsed = json.loads(match.group(1).strip() if match else raw.strip())

        state["design_yaml"] = parsed
        state["api_schema"] = parsed.get("api_endpoints", [])
        state["db_schema"] = [
            {"table": e["name"], "fields": e.get("fields", [])}
            for e in parsed.get("entities", [])
        ]
        state["completed_steps"].append("design")
        state["agent_statuses"]["design"] = AgentStatus.COMPLETED
    except Exception as e:
        logger.error(f"[design_node] failed: {e}")
        state["errors"]["design"] = str(e)
        state["agent_statuses"]["design"] = AgentStatus.FAILED

    return state
```

## Task 2: Refactor `publish_agent` using Deep Agents with filesystem tools

The publish step reads generated files and pushes them to GitHub via MCP.
Deep Agents filesystem tools (`ls`, `read_file`) make this safer and more
explicit than the current manual file I/O.

Update `AI_agents/graph/nodes/publish_node.py`:

```python
from deepagents import create_deep_agent
from deepagents.tools.filesystem import ls, read_file
from AI_agents.utils.llm_client import get_llm_client
from AI_agents.graph.state import OrchestraState, AgentStatus
from mcp_servers.client import MCPClientManager

async def publish_node(state: OrchestraState) -> OrchestraState:
    provider = state.get("ai_provider", "anthropic")
    llm = get_llm_client(provider, {})
    mcp = MCPClientManager()
    github_tools = await mcp.get_tools(["github"])

    agent = create_deep_agent(
        llm=llm,
        tools=[ls, read_file] + github_tools,
        system_prompt=(
            "You are a DevOps agent responsible for publishing "
            "generated application code to a GitHub repository. "
            "Use the filesystem tools to list and read generated files, "
            "then use the GitHub tools to push them."
        ),
    )

    message = (
        f"Publish the generated application for project '{state['project_id']}' "
        f"to the GitHub repository. "
        f"The generated files are in the 'generated_app/' directory. "
        f"Create a new repository named '{state['project_id']}', "
        f"push all files to the main branch, "
        f"and return the repository URL."
    )

    try:
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})
        raw = result["messages"][-1].content
        # extract repo URL if present
        import re
        url_match = re.search(r"https://github\.com/[\w/-]+", raw)
        if url_match:
            state["github_repo_url"] = url_match.group(0)
        state["completed_steps"].append("publish_agent")
        state["agent_statuses"]["publish_agent"] = AgentStatus.COMPLETED
    except Exception as e:
        state["errors"]["publish_agent"] = str(e)
        state["agent_statuses"]["publish_agent"] = AgentStatus.FAILED

    return state
```

## What NOT to migrate

Leave these nodes as standard `BaseAgent` subclasses (from Prompt 07b):
- `backend_node` — one-shot code generation, no tool loop needed
- `frontend_node` — same
- `backlog_node` — same
- `devops_node` — same

Explain the decision briefly in a comment at the top of each unchanged file:
```python
# Deep Agents not used here: this node is a one-shot code generator.
# BaseAgent abstraction (prompt_07b) is sufficient.
```

## LangGraph graph.py

Do NOT change `graph.py`. The nodes are wired the same way — only their
internal implementation changes. LangGraph remains the orchestrator.

When done, update `.claude/context/migration_status.md` marking Prompt 07c complete.
