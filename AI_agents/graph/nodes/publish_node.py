"""
Publish Agent Node for Agentic Orchestra (Deep Agents Integration).

Publishes generated application code to GitHub repository using Deep Agents
with filesystem tools for file reading and MCP tools for GitHub integration.

This node uses Deep Agents (Prompt 07c) because publishing involves multiple steps:
list generated files → read file contents → create GitHub repo → push files → verify.
The filesystem tools (ls, read_file) make this safer and more explicit than manual I/O.

Input:
    - state["project_id"]: Project identifier for naming repository
    - state["design_yaml"]: Application design (used for metadata)
    - Generated files in 'generated_app/' directory

Output:
    - state["github_repo_url"]: URL of created GitHub repository

Error Handling:
    - Sets state["errors"]["publish_agent"] on failure
    - Never raises exceptions (returns state with FAILED status)
"""

import logging
import re
from deepagents import create_deep_agent
from deepagents.tools.filesystem import ls, read_file
from AI_agents.utils.llm_client import get_llm_client
from AI_agents.graph.state import OrchestraState, AgentStatus
from mcp_servers.client import MCPClientManager

logger = logging.getLogger(__name__)


async def publish_node(state: OrchestraState) -> OrchestraState:
    """
    Publish generated application to GitHub using Deep Agents.

    Algorithm:
        1. Initialize Deep Agent with filesystem tools + GitHub MCP tools
        2. Agent lists files in generated_app/ directory
        3. Agent reads file contents
        4. Agent creates new GitHub repository
        5. Agent pushes all files to main branch
        6. Extract repository URL from agent response

    Args:
        state: Current orchestration state

    Returns:
        Updated state with github_repo_url or error information
    """
    logger.info("[publish_node] Starting GitHub publish with Deep Agents")

    # Update orchestration state
    state["current_step"] = "publish_agent"
    state["agent_statuses"]["publish_agent"] = AgentStatus.RUNNING

    # Extract input data
    project_id = state.get("project_id", "")
    if not project_id:
        logger.error("[publish_node] No project_id provided")
        state["errors"]["publish_agent"] = "No project_id in state"
        state["agent_statuses"]["publish_agent"] = AgentStatus.FAILED
        return state

    # Get LLM client
    provider = state.get("ai_provider", "anthropic")
    try:
        llm = get_llm_client(provider, {"temperature": 0.1, "max_tokens": 4000})
    except Exception as e:
        logger.error(f"[publish_node] Failed to create LLM client: {e}")
        state["errors"]["publish_agent"] = f"LLM client error: {str(e)}"
        state["agent_statuses"]["publish_agent"] = AgentStatus.FAILED
        return state

    # Get GitHub tools from MCP server
    try:
        mcp = MCPClientManager()
        github_tools = await mcp.get_tools(["github"])
        logger.info(f"[publish_node] Loaded {len(github_tools)} GitHub tools from MCP")
    except Exception as e:
        logger.error(f"[publish_node] Failed to load GitHub MCP tools: {e}")
        state["errors"]["publish_agent"] = f"MCP GitHub tools error: {str(e)}"
        state["agent_statuses"]["publish_agent"] = AgentStatus.FAILED
        return state

    # Create Deep Agent with filesystem + GitHub tools
    agent = create_deep_agent(
        llm=llm,
        tools=[ls, read_file] + github_tools,
        system_prompt=(
            "You are a DevOps agent responsible for publishing "
            "generated application code to a GitHub repository. "
            "Use the filesystem tools to list and read generated files, "
            "then use the GitHub tools to create a repository and push them. "
            "Always verify the repository was created successfully."
        ),
    )

    # Build user message
    design = state.get("design_yaml", {})
    app_name = design.get("app_name", project_id)

    message = (
        f"Publish the generated application for project '{project_id}' "
        f"to GitHub. "
        f"\n\nSteps:"
        f"\n1. List files in the 'generated_app/' directory using the ls tool"
        f"\n2. Read important files (README.md, package.json, etc.) using read_file"
        f"\n3. Create a new GitHub repository named '{app_name}'"
        f"\n4. Push all files from 'generated_app/' to the main branch"
        f"\n5. Return the repository URL"
        f"\n\nThe app is named: {app_name}"
        f"\nDescription: {design.get('description', 'Generated MVP application')}"
    )

    try:
        # Invoke Deep Agent
        logger.info("[publish_node] Invoking Deep Agent with GitHub tools")
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]})

        # Extract last assistant message
        raw = result["messages"][-1].content
        logger.debug(f"[publish_node] Raw agent response: {raw[:200]}...")

        # Extract GitHub repository URL
        url_match = re.search(r"https://github\.com/[\w/-]+", raw)
        if url_match:
            repo_url = url_match.group(0)
            state["github_repo_url"] = repo_url
            logger.info(f"[publish_node] Repository created: {repo_url}")
        else:
            logger.warning("[publish_node] Could not extract repository URL from response")
            state["github_repo_url"] = ""

        # Mark success
        state["completed_steps"].append("publish_agent")
        state["agent_statuses"]["publish_agent"] = AgentStatus.COMPLETED

        logger.info("[publish_node] Publish completed successfully")

    except Exception as e:
        logger.error(f"[publish_node] Publish failed: {e}")
        state["errors"]["publish_agent"] = str(e)
        state["agent_statuses"]["publish_agent"] = AgentStatus.FAILED

    return state
