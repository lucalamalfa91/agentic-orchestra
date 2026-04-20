"""MCP Client Manager - connects to MCP servers and executes tools."""

import logging
from typing import Any, Optional

import os
import sys
import httpx
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logger = logging.getLogger(__name__)


class MCPClientManager:
    """
    Manages connections to MCP servers and tool execution.

    Each MCP server runs as a separate process. This client connects
    to them via stdio and provides a unified interface for tool calls.
    """

    # Server configuration: name -> command to start server
    SERVERS = {
        "github": {
            "command": "python",
            "args": ["-m", "mcp_servers.github_server"],
            "description": "GitHub integration (create repos, push files, PRs)"
        },
        "azuredevops": {
            "command": "python",
            "args": ["-m", "mcp_servers.azuredevops_server"],
            "description": "Azure DevOps integration (work items, sprints, pipelines)"
        },
        "deploy": {
            "command": "python",
            "args": ["-m", "mcp_servers.deploy_server"],
            "description": "Deployment tools (Railway, Docker Compose)"
        }
    }

    def __init__(self):
        """Initialize the MCP client manager."""
        self._clients: dict[str, ClientSession] = {}
        self._tools_cache: dict[str, list] = {}

    async def connect(self, server_name: str):
        """
        Connect to an MCP server.

        Args:
            server_name: Name of the server to connect to

        Raises:
            ValueError: If server name is not recognized
        """
        if server_name not in self.SERVERS:
            raise ValueError(
                f"Unknown server: {server_name}. "
                f"Available: {list(self.SERVERS.keys())}"
            )

        if server_name in self._clients:
            logger.debug(f"[MCPClient] Already connected to {server_name}")
            return

        server_config = self.SERVERS[server_name]

        # Build env with project root in PYTHONPATH for subprocess
        project_root = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env = dict(os.environ)
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{project_root}:{existing}" if existing else project_root

        # Create server parameters
        server_params = StdioServerParameters(
            command=server_config["command"],
            args=server_config["args"],
            env=env
        )

        # Connect to server
        logger.info(f"[MCPClient] Connecting to {server_name}...")

        async with stdio_client(server_params) as (read, write):
            client = ClientSession(read, write)
            await client.initialize()

            self._clients[server_name] = client
            logger.info(f"[MCPClient] Connected to {server_name}")

    async def disconnect(self, server_name: str):
        """
        Disconnect from an MCP server.

        Args:
            server_name: Name of the server to disconnect from
        """
        if server_name in self._clients:
            # MCP client cleanup happens automatically via context manager
            del self._clients[server_name]
            if server_name in self._tools_cache:
                del self._tools_cache[server_name]

            logger.info(f"[MCPClient] Disconnected from {server_name}")

    async def disconnect_all(self):
        """Disconnect from all servers."""
        for server_name in list(self._clients.keys()):
            await self.disconnect(server_name)

    async def get_tools(self, server_names: list[str]) -> list[dict]:
        """
        Get available tools from specified servers.

        Args:
            server_names: List of server names to query

        Returns:
            List of tool definitions
        """
        all_tools = []

        for server_name in server_names:
            # Connect if not already connected
            if server_name not in self._clients:
                await self.connect(server_name)

            # Check cache first
            if server_name in self._tools_cache:
                all_tools.extend(self._tools_cache[server_name])
                continue

            # Fetch tools from server
            client = self._clients[server_name]
            tools = await client.list_tools()

            # Convert to dict format and cache
            tools_list = [
                {
                    "server": server_name,
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ]

            self._tools_cache[server_name] = tools_list
            all_tools.extend(tools_list)

        logger.info(
            f"[MCPClient] Retrieved {len(all_tools)} tools from "
            f"{len(server_names)} servers"
        )

        return all_tools

    async def call_tool(
        self,
        server: str,
        tool_name: str,
        args: dict
    ) -> dict:
        """
        Execute a tool on a specific MCP server.

        Args:
            server: Server name
            tool_name: Name of the tool to call
            args: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If server is not connected or tool doesn't exist
            RuntimeError: If tool execution fails
        """
        # Ensure connected
        if server not in self._clients:
            await self.connect(server)

        client = self._clients[server]

        logger.info(f"[MCPClient] Calling {server}.{tool_name}")
        logger.debug(f"[MCPClient] Arguments: {args}")

        try:
            # Call tool
            result = await client.call_tool(tool_name, args)

            # Extract text content from result
            if result and len(result) > 0:
                response_text = result[0].text

                # Parse response (it's a string representation of a dict)
                import ast
                response_dict = ast.literal_eval(response_text)

                logger.info(f"[MCPClient] Tool call succeeded: {server}.{tool_name}")

                return response_dict
            else:
                raise RuntimeError("Empty response from tool")

        except Exception as e:
            logger.error(
                f"[MCPClient] Tool call failed: {server}.{tool_name} - {e}"
            )
            raise

    async def list_available_servers(self) -> dict[str, dict]:
        """
        List all available MCP servers and their descriptions.

        Returns:
            Dictionary mapping server names to their configurations
        """
        return {
            name: {
                "description": config["description"],
                "connected": name in self._clients
            }
            for name, config in self.SERVERS.items()
        }


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_client_manager() -> MCPClientManager:
    """Create and return a new MCP client manager instance."""
    return MCPClientManager()


async def execute_tool(
    server: str,
    tool_name: str,
    args: dict,
    manager: Optional[MCPClientManager] = None
) -> dict:
    """
    Convenience function to execute a tool.

    Creates a temporary client manager if none provided.

    Args:
        server: Server name
        tool_name: Tool name
        args: Tool arguments
        manager: Optional existing MCPClientManager instance

    Returns:
        Tool execution result
    """
    if manager is None:
        manager = await create_client_manager()

    try:
        return await manager.call_tool(server, tool_name, args)
    finally:
        if manager is None:
            await manager.disconnect_all()
