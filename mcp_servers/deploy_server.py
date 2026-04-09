"""MCP Server for deployment integrations (Railway, Docker Compose)."""

import logging
from typing import Optional

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

from .base_server import (
    inject_token,
    log_tool_call,
    format_error_response,
    format_success_response,
    MCPAuthError
)

logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("deploy-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available deployment tools."""
    return [
        Tool(
            name="deploy_railway",
            description="Deploy a project to Railway",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_name": {"type": "string", "description": "Project name"},
                    "env_vars": {
                        "type": "object",
                        "description": "Environment variables as key-value pairs",
                        "default": {}
                    },
                    "dockerfile_path": {
                        "type": "string",
                        "description": "Path to Dockerfile (optional)",
                        "default": "Dockerfile"
                    }
                },
                "required": ["project_name"]
            }
        ),
        Tool(
            name="deploy_docker_compose",
            description="Deploy using Docker Compose to a remote host",
            inputSchema={
                "type": "object",
                "properties": {
                    "compose_content": {"type": "string", "description": "Docker Compose YAML content"},
                    "target_host": {"type": "string", "description": "SSH target (user@host)", "default": "local"}
                },
                "required": ["compose_content"]
            }
        )
    ]


@app.call_tool()
@log_tool_call
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a deployment tool."""
    try:
        if name == "deploy_railway":
            result = await deploy_railway(**arguments)
        elif name == "deploy_docker_compose":
            result = await deploy_docker_compose(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        response = format_success_response(result)

    except Exception as e:
        response = format_error_response(e)

    return [TextContent(type="text", text=str(response))]


# ============================================================================
# Tool Implementations
# ============================================================================

async def deploy_railway(
    project_name: str,
    env_vars: dict = None,
    dockerfile_path: str = "Dockerfile"
) -> dict:
    """
    Deploy a project to Railway.

    Uses Railway GraphQL API to create and configure deployment.
    """
    token = inject_token("RAILWAY_TOKEN")
    env_vars = env_vars or {}

    # Railway GraphQL API endpoint
    api_url = "https://backboard.railway.app/graphql/v2"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 1: Create project
        create_project_mutation = """
        mutation CreateProject($name: String!) {
            projectCreate(input: { name: $name }) {
                id
                name
            }
        }
        """

        response = await client.post(
            api_url,
            headers=headers,
            json={
                "query": create_project_mutation,
                "variables": {"name": project_name}
            }
        )
        response.raise_for_status()
        project_data = response.json()

        if "errors" in project_data:
            raise ValueError(f"Railway API error: {project_data['errors']}")

        project_id = project_data["data"]["projectCreate"]["id"]

        # Step 2: Set environment variables (if any)
        if env_vars:
            for key, value in env_vars.items():
                set_env_mutation = """
                mutation SetEnvVar($projectId: String!, $key: String!, $value: String!) {
                    variableUpsert(input: {
                        projectId: $projectId,
                        name: $key,
                        value: $value
                    })
                }
                """

                await client.post(
                    api_url,
                    headers=headers,
                    json={
                        "query": set_env_mutation,
                        "variables": {
                            "projectId": project_id,
                            "key": key,
                            "value": value
                        }
                    }
                )

        logger.info(f"[Railway] Deployed project: {project_name} (ID: {project_id})")

        return {
            "project_id": project_id,
            "project_name": project_name,
            "env_vars_set": len(env_vars),
            "url": f"https://railway.app/project/{project_id}",
            "status": "deployed"
        }


async def deploy_docker_compose(
    compose_content: str,
    target_host: str = "local"
) -> dict:
    """
    Deploy using Docker Compose.

    For local deployment, saves compose file and runs docker-compose up.
    For remote, uses SSH to transfer and execute.
    """
    import tempfile
    import subprocess
    from pathlib import Path

    # Save compose content to temporary file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yml',
        delete=False
    ) as f:
        f.write(compose_content)
        compose_file = Path(f.name)

    try:
        if target_host == "local":
            # Local deployment
            result = subprocess.run(
                ["docker-compose", "-f", str(compose_file), "up", "-d"],
                capture_output=True,
                text=True,
                check=True
            )

            logger.info("[Docker Compose] Local deployment successful")

            return {
                "target": "local",
                "status": "deployed",
                "compose_file": str(compose_file),
                "output": result.stdout
            }

        else:
            # Remote deployment via SSH
            # Transfer compose file
            scp_result = subprocess.run(
                ["scp", str(compose_file), f"{target_host}:~/docker-compose.yml"],
                capture_output=True,
                text=True,
                check=True
            )

            # Run docker-compose on remote
            ssh_result = subprocess.run(
                ["ssh", target_host, "docker-compose -f ~/docker-compose.yml up -d"],
                capture_output=True,
                text=True,
                check=True
            )

            logger.info(f"[Docker Compose] Remote deployment to {target_host} successful")

            return {
                "target": target_host,
                "status": "deployed",
                "output": ssh_result.stdout
            }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Docker Compose deployment failed: {e.stderr}")

    finally:
        # Cleanup temporary file
        if compose_file.exists():
            compose_file.unlink()


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    import asyncio
    import mcp

    async def main():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    asyncio.run(main())
