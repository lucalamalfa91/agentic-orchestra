"""MCP Server for Azure DevOps integration."""

import logging
from datetime import datetime
from typing import Optional

from azure.devops.connection import Connection
from azure.devops.v7_0.work_item_tracking.models import JsonPatchOperation
from msrest.authentication import BasicAuthentication
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
app = Server("azuredevops-server")


def get_azdo_client() -> Connection:
    """Get authenticated Azure DevOps client using injected credentials."""
    token = inject_token("AZDO_TOKEN")
    org_url = inject_token("AZDO_ORG")  # e.g., "https://dev.azure.com/myorg"

    credentials = BasicAuthentication('', token)
    return Connection(base_url=org_url, creds=credentials)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Azure DevOps tools."""
    return [
        Tool(
            name="create_work_item",
            description="Create a work item (User Story, Task, Bug, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name"},
                    "type": {"type": "string", "description": "Work item type (User Story, Task, Bug, Epic)", "default": "User Story"},
                    "title": {"type": "string", "description": "Work item title"},
                    "description": {"type": "string", "description": "Work item description", "default": ""},
                    "tags": {"type": "string", "description": "Semicolon-separated tags", "default": ""}
                },
                "required": ["project", "title"]
            }
        ),
        Tool(
            name="create_sprint",
            description="Create a new sprint/iteration",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name"},
                    "name": {"type": "string", "description": "Sprint name"},
                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                },
                "required": ["project", "name", "start_date", "end_date"]
            }
        ),
        Tool(
            name="create_pipeline",
            description="Create a CI/CD pipeline",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name"},
                    "name": {"type": "string", "description": "Pipeline name"},
                    "yaml_path": {"type": "string", "description": "Path to YAML file in repo"},
                    "repo_url": {"type": "string", "description": "Git repository URL"}
                },
                "required": ["project", "name", "yaml_path", "repo_url"]
            }
        )
    ]


@app.call_tool()
@log_tool_call
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute an Azure DevOps tool."""
    try:
        if name == "create_work_item":
            result = await create_work_item(**arguments)
        elif name == "create_sprint":
            result = await create_sprint(**arguments)
        elif name == "create_pipeline":
            result = await create_pipeline(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        response = format_success_response(result)

    except Exception as e:
        response = format_error_response(e)

    return [TextContent(type="text", text=str(response))]


# ============================================================================
# Tool Implementations
# ============================================================================

async def create_work_item(
    project: str,
    title: str,
    type: str = "User Story",
    description: str = "",
    tags: str = ""
) -> dict:
    """Create a work item in Azure DevOps."""
    connection = get_azdo_client()
    wit_client = connection.clients.get_work_item_tracking_client()

    # Build JSON patch document
    document = [
        JsonPatchOperation(
            op="add",
            path="/fields/System.Title",
            value=title
        )
    ]

    if description:
        document.append(
            JsonPatchOperation(
                op="add",
                path="/fields/System.Description",
                value=description
            )
        )

    if tags:
        document.append(
            JsonPatchOperation(
                op="add",
                path="/fields/System.Tags",
                value=tags
            )
        )

    # Create work item
    work_item = wit_client.create_work_item(
        document=document,
        project=project,
        type=type
    )

    logger.info(f"[AzDO] Created work item #{work_item.id} in {project}")

    return {
        "id": work_item.id,
        "type": type,
        "title": title,
        "url": work_item._links.additional_properties.get("html", {}).get("href"),
        "state": work_item.fields.get("System.State")
    }


async def create_sprint(
    project: str,
    name: str,
    start_date: str,
    end_date: str
) -> dict:
    """Create a sprint/iteration in Azure DevOps."""
    connection = get_azdo_client()
    work_client = connection.clients.get_work_client()

    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # Get team context
    core_client = connection.clients.get_core_client()
    project_obj = core_client.get_project(project)
    teams = core_client.get_teams(project_obj.id)

    if not teams:
        raise ValueError(f"No teams found in project {project}")

    default_team = teams[0]

    # Create iteration
    iteration = work_client.post_team_iteration(
        iteration={
            "name": name,
            "attributes": {
                "startDate": start,
                "finishDate": end
            }
        },
        team_context={
            "project": project,
            "team": default_team.name
        }
    )

    logger.info(f"[AzDO] Created sprint '{name}' in {project}")

    return {
        "id": iteration.id,
        "name": name,
        "path": iteration.path,
        "start_date": start_date,
        "end_date": end_date
    }


async def create_pipeline(
    project: str,
    name: str,
    yaml_path: str,
    repo_url: str
) -> dict:
    """
    Create a CI/CD pipeline in Azure DevOps.

    Note: This is a simplified implementation. Full pipeline creation
    requires repository setup and YAML validation.
    """
    connection = get_azdo_client()
    pipelines_client = connection.clients.get_pipelines_client()

    # Create pipeline configuration
    pipeline = pipelines_client.create_pipeline(
        pipeline={
            "name": name,
            "folder": "\\",
            "configuration": {
                "type": "yaml",
                "path": yaml_path,
                "repository": {
                    "type": "git",
                    "url": repo_url
                }
            }
        },
        project=project
    )

    logger.info(f"[AzDO] Created pipeline '{name}' in {project}")

    return {
        "id": pipeline.id,
        "name": name,
        "url": pipeline._links.additional_properties.get("web", {}).get("href"),
        "yaml_path": yaml_path
    }


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
