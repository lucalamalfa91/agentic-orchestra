"""
LangGraph agent nodes for Agentic Orchestra.

Each agent is implemented as a separate module in this package.
All agent nodes receive and return OrchestraState.

Deep Agents Integration (Prompt 07c):
- design_node: Uses Deep Agents with planning (enable_todos=True)
- publish_node: Uses Deep Agents with filesystem + GitHub MCP tools
- Other nodes: Use BaseAgent abstraction (one-shot code generation)
"""

from .design_node import design_node
from .publish_node import publish_node

__all__ = ["design_node", "publish_node"]
