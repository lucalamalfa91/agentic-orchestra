"""
LangGraph agent nodes for Agentic Orchestra.

Each agent is implemented as a separate module in this package.
All agent nodes receive and return OrchestraState.

Deep Agents Integration (Prompt 07c):
- design_node: Uses Deep Agents with planning (enable_todos=True)
- publish_node: Uses Deep Agents with filesystem + GitHub MCP tools

BaseAgent Nodes (Prompt 07d):
- backend_node: Generates backend code (language-agnostic)
- frontend_node: Generates frontend code (framework-agnostic)
- backlog_node: Generates product backlog (user stories, issues)

BaseAgent Nodes (Prompt 07e):
- devops_node: Generates CI/CD workflows and Docker configuration
"""

from .design_node import design_node
from .publish_node import publish_node
from .backend_node import backend_node
from .frontend_node import frontend_node
from .backlog_node import backlog_node
from .devops_node import devops_node

__all__ = [
    "design_node",
    "publish_node",
    "backend_node",
    "frontend_node",
    "backlog_node",
    "devops_node",
]
