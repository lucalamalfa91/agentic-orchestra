"""MCP Server for GitHub integration."""

import logging
import base64
from typing import Optional

from github import Github, GithubException
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
app = Server("github-server")


def get_github_client() -> Github:
    """Get authenticated GitHub client using injected token."""
    token = inject_token("GITHUB_TOKEN")
    return Github(token)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available GitHub tools."""
    return [
        Tool(
            name="create_repository",
            description="Create a new GitHub repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Repository name"},
                    "private": {"type": "boolean", "description": "Make repository private", "default": False},
                    "description": {"type": "string", "description": "Repository description", "default": ""}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="push_files",
            description="Push multiple files to a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository full name (owner/repo)"},
                    "branch": {"type": "string", "description": "Branch name", "default": "main"},
                    "files": {
                        "type": "array",
                        "description": "List of files to push",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "content": {"type": "string"}
                            },
                            "required": ["path", "content"]
                        }
                    },
                    "message": {"type": "string", "description": "Commit message"}
                },
                "required": ["repo", "files", "message"]
            }
        ),
        Tool(
            name="create_pull_request",
            description="Create a pull request",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository full name (owner/repo)"},
                    "title": {"type": "string", "description": "PR title"},
                    "head": {"type": "string", "description": "Branch containing changes"},
                    "base": {"type": "string", "description": "Branch to merge into", "default": "main"},
                    "body": {"type": "string", "description": "PR description", "default": ""}
                },
                "required": ["repo", "title", "head"]
            }
        ),
        Tool(
            name="read_file",
            description="Read a file from a repository",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository full name (owner/repo)"},
                    "path": {"type": "string", "description": "File path in repository"},
                    "ref": {"type": "string", "description": "Branch/tag/commit ref", "default": "main"}
                },
                "required": ["repo", "path"]
            }
        )
    ]


@app.call_tool()
@log_tool_call
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute a GitHub tool."""
    try:
        if name == "create_repository":
            result = await create_repository(**arguments)
        elif name == "push_files":
            result = await push_files(**arguments)
        elif name == "create_pull_request":
            result = await create_pull_request(**arguments)
        elif name == "read_file":
            result = await read_file(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        response = format_success_response(result)

    except Exception as e:
        response = format_error_response(e)

    return [TextContent(type="text", text=str(response))]


# ============================================================================
# Tool Implementations
# ============================================================================

async def create_repository(
    name: str,
    private: bool = False,
    description: str = ""
) -> dict:
    """Create a new GitHub repository."""
    client = get_github_client()
    user = client.get_user()

    repo = user.create_repo(
        name=name,
        private=private,
        description=description,
        auto_init=True  # Create with README
    )

    logger.info(f"[GitHub] Created repository: {repo.full_name}")

    return {
        "name": repo.name,
        "full_name": repo.full_name,
        "url": repo.html_url,
        "clone_url": repo.clone_url,
        "private": repo.private
    }


async def push_files(
    repo: str,
    files: list[dict],
    message: str,
    branch: str = "main"
) -> dict:
    """
    Push multiple files to a repository in a single commit.

    Args:
        repo: Repository full name (owner/repo)
        files: List of {path: str, content: str} dictionaries
        message: Commit message
        branch: Branch name

    Returns:
        Dictionary with commit details
    """
    client = get_github_client()
    repository = client.get_repo(repo)

    # Get the reference to the branch
    ref = repository.get_git_ref(f"heads/{branch}")
    base_tree = repository.get_git_tree(ref.object.sha)

    # Create blobs for each file
    tree_elements = []
    for file_info in files:
        blob = repository.create_git_blob(file_info["content"], "utf-8")
        tree_elements.append({
            "path": file_info["path"],
            "mode": "100644",  # Regular file
            "type": "blob",
            "sha": blob.sha
        })

    # Create tree
    tree = repository.create_git_tree(tree_elements, base_tree)

    # Get parent commit
    parent = repository.get_git_commit(ref.object.sha)

    # Create commit
    commit = repository.create_git_commit(message, tree, [parent])

    # Update reference
    ref.edit(commit.sha)

    logger.info(f"[GitHub] Pushed {len(files)} files to {repo}/{branch}")

    return {
        "commit_sha": commit.sha,
        "commit_url": commit.html_url,
        "files_pushed": len(files),
        "branch": branch
    }


async def create_pull_request(
    repo: str,
    title: str,
    head: str,
    base: str = "main",
    body: str = ""
) -> dict:
    """Create a pull request."""
    client = get_github_client()
    repository = client.get_repo(repo)

    pr = repository.create_pull(
        title=title,
        body=body,
        head=head,
        base=base
    )

    logger.info(f"[GitHub] Created PR #{pr.number} in {repo}")

    return {
        "number": pr.number,
        "title": pr.title,
        "url": pr.html_url,
        "state": pr.state,
        "head": head,
        "base": base
    }


async def read_file(
    repo: str,
    path: str,
    ref: str = "main"
) -> dict:
    """Read a file from a repository."""
    client = get_github_client()
    repository = client.get_repo(repo)

    try:
        content_file = repository.get_contents(path, ref=ref)

        # Decode content (it's base64 encoded)
        if isinstance(content_file, list):
            raise ValueError(f"Path '{path}' is a directory, not a file")

        content = base64.b64decode(content_file.content).decode("utf-8")

        logger.info(f"[GitHub] Read file: {repo}/{path} @ {ref}")

        return {
            "path": path,
            "content": content,
            "sha": content_file.sha,
            "size": content_file.size,
            "ref": ref
        }

    except GithubException as e:
        if e.status == 404:
            raise FileNotFoundError(f"File not found: {path} in {repo} @ {ref}")
        raise


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
