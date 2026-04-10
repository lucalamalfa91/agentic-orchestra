"""Tests for MCP servers."""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock
from mcp_servers.base_server import (
    inject_token,
    log_tool_call,
    format_error_response,
    format_success_response,
    MCPAuthError,
)


@pytest.mark.unit
def test_github_server_tool_list():
    """Test that GitHub server exposes expected tools."""
    from mcp_servers.github_server import list_tools

    # Get tools list
    tools = list_tools()

    # Verify it's a coroutine (async function)
    assert hasattr(tools, '__await__')


@pytest.mark.asyncio
@pytest.mark.unit
async def test_github_server_has_required_tools():
    """Test that GitHub server has the required tools."""
    from mcp_servers.github_server import list_tools

    tools = await list_tools()

    # Extract tool names
    tool_names = [tool.name for tool in tools]

    # Verify expected tools are present
    assert "create_repository" in tool_names
    assert "push_files" in tool_names
    assert "create_pull_request" in tool_names
    assert "read_file" in tool_names


@pytest.mark.asyncio
@pytest.mark.unit
async def test_push_files_tool_schema():
    """Test that push_files tool has correct request schema."""
    from mcp_servers.github_server import list_tools

    tools = await list_tools()

    # Find push_files tool
    push_files_tool = next(t for t in tools if t.name == "push_files")

    # Verify schema structure
    assert push_files_tool.inputSchema["type"] == "object"

    # Verify required fields
    required = push_files_tool.inputSchema["required"]
    assert "repo" in required
    assert "files" in required
    assert "message" in required

    # Verify files is an array
    props = push_files_tool.inputSchema["properties"]
    assert props["files"]["type"] == "array"

    # Verify file item schema
    file_schema = props["files"]["items"]
    assert file_schema["type"] == "object"
    assert "path" in file_schema["required"]
    assert "content" in file_schema["required"]


@pytest.mark.unit
def test_missing_token_raises_mcp_auth_error():
    """Test that missing environment variable raises MCPAuthError."""
    # Ensure env var is not set
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(MCPAuthError) as exc_info:
            inject_token("GITHUB_TOKEN")

        # Verify exception message
        assert "GITHUB_TOKEN" in str(exc_info.value)
        assert "not set" in str(exc_info.value)


@pytest.mark.unit
def test_inject_token_returns_value():
    """Test that inject_token returns token value when set."""
    test_token = "ghp_test1234567890"

    with patch.dict(os.environ, {"GITHUB_TOKEN": test_token}):
        result = inject_token("GITHUB_TOKEN")
        assert result == test_token


@pytest.mark.unit
def test_inject_token_raises_on_empty_string():
    """Test that empty string token also raises MCPAuthError."""
    with patch.dict(os.environ, {"GITHUB_TOKEN": ""}):
        with pytest.raises(MCPAuthError):
            inject_token("GITHUB_TOKEN")


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tool_call_logged():
    """Test that log_tool_call decorator logs tool calls."""
    # Create a mock tool function
    @log_tool_call
    async def mock_tool(arg1: str, arg2: int):
        return {"result": f"{arg1}_{arg2}"}

    # Patch logger to verify logging
    with patch("mcp_servers.base_server.logger") as mock_logger:
        result = await mock_tool("test", 42)

        # Verify function executed correctly
        assert result["result"] == "test_42"

        # Verify logging calls
        mock_logger.info.assert_called()

        # Verify log messages contain tool name
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("mock_tool" in msg for msg in log_calls)
        assert any("Starting tool call" in msg for msg in log_calls)
        assert any("succeeded" in msg for msg in log_calls)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tool_call_logs_duration():
    """Test that log_tool_call decorator logs execution duration."""
    @log_tool_call
    async def slow_tool():
        import asyncio
        await asyncio.sleep(0.1)
        return {"done": True}

    with patch("mcp_servers.base_server.logger") as mock_logger:
        await slow_tool()

        # Find the success log message
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        success_msg = next(msg for msg in log_calls if "succeeded" in msg)

        # Verify duration is logged
        assert "duration:" in success_msg
        assert "s)" in success_msg  # Seconds


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tool_call_logs_errors():
    """Test that log_tool_call decorator logs exceptions."""
    @log_tool_call
    async def failing_tool():
        raise ValueError("Test error")

    with patch("mcp_servers.base_server.logger") as mock_logger:
        with pytest.raises(ValueError):
            await failing_tool()

        # Verify error was logged
        mock_logger.error.assert_called()

        # Verify error log contains details
        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("failing_tool" in msg for msg in error_calls)
        assert any("failed" in msg for msg in error_calls)
        assert any("ValueError" in msg for msg in error_calls)


@pytest.mark.asyncio
@pytest.mark.unit
async def test_tool_call_logs_auth_errors():
    """Test that log_tool_call decorator logs MCPAuthError separately."""
    @log_tool_call
    async def auth_failing_tool():
        raise MCPAuthError("Token missing")

    with patch("mcp_servers.base_server.logger") as mock_logger:
        with pytest.raises(MCPAuthError):
            await auth_failing_tool()

        # Verify auth error was logged
        mock_logger.error.assert_called()

        # Verify log contains "auth error"
        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("auth error" in msg for msg in error_calls)


@pytest.mark.unit
def test_format_error_response_mcp_auth_error():
    """Test error response formatting for MCPAuthError."""
    error = MCPAuthError("Token not found")

    response = format_error_response(error)

    assert response["error"] == "authentication_required"
    assert response["message"] == "Token not found"
    assert response["code"] == "AUTH_MISSING"


@pytest.mark.unit
def test_format_error_response_generic_error():
    """Test error response formatting for generic exceptions."""
    error = ValueError("Invalid input")

    response = format_error_response(error)

    assert response["error"] == "ValueError"
    assert response["message"] == "Invalid input"
    assert response["code"] == "TOOL_ERROR"


@pytest.mark.unit
def test_format_success_response():
    """Test success response formatting."""
    data = {"repo_url": "https://github.com/user/repo"}

    response = format_success_response(data)

    assert response["success"] is True
    assert response["data"] == data


@pytest.mark.unit
def test_format_success_response_with_various_data_types():
    """Test success response with different data types."""
    # String data
    response_str = format_success_response("Operation completed")
    assert response_str["success"] is True
    assert response_str["data"] == "Operation completed"

    # List data
    response_list = format_success_response([1, 2, 3])
    assert response_list["success"] is True
    assert response_list["data"] == [1, 2, 3]

    # None data
    response_none = format_success_response(None)
    assert response_none["success"] is True
    assert response_none["data"] is None


@pytest.mark.unit
def test_mcp_auth_error_is_exception():
    """Test that MCPAuthError is a proper Exception subclass."""
    error = MCPAuthError("Test")

    # Verify it's an Exception
    assert isinstance(error, Exception)

    # Verify it can be raised and caught
    with pytest.raises(MCPAuthError):
        raise error


@pytest.mark.asyncio
@pytest.mark.unit
async def test_azuredevops_server_tool_list():
    """Test that Azure DevOps server exposes expected tools."""
    from mcp_servers.azuredevops_server import list_tools

    tools = await list_tools()

    # Extract tool names
    tool_names = [tool.name for tool in tools]

    # Verify expected tools
    assert "create_work_item" in tool_names
    assert "create_sprint" in tool_names
    assert "create_pipeline" in tool_names


@pytest.mark.asyncio
@pytest.mark.unit
async def test_deploy_server_tool_list():
    """Test that Deploy server exposes expected tools."""
    from mcp_servers.deploy_server import list_tools

    tools = await list_tools()

    # Extract tool names
    tool_names = [tool.name for tool in tools]

    # Verify expected tools
    assert "deploy_railway" in tool_names
    assert "deploy_docker_compose" in tool_names


@pytest.mark.unit
def test_all_servers_import_successfully():
    """Test that all MCP server modules can be imported."""
    # This test verifies no import errors exist
    import mcp_servers.github_server
    import mcp_servers.azuredevops_server
    import mcp_servers.deploy_server
    import mcp_servers.base_server

    # If we reach here, all imports succeeded
    assert True


@pytest.mark.asyncio
@pytest.mark.integration
async def test_github_tool_execution_with_mock():
    """Test GitHub tool execution with mocked PyGithub."""
    from mcp_servers.github_server import create_repository

    # Mock GitHub client
    mock_repo = MagicMock()
    mock_repo.html_url = "https://github.com/test/test-repo"
    mock_repo.name = "test-repo"

    mock_user = MagicMock()
    mock_user.create_repo.return_value = mock_repo

    mock_github = MagicMock()
    mock_github.get_user.return_value = mock_user

    # Mock environment and GitHub client
    with patch.dict(os.environ, {"GITHUB_TOKEN": "test_token"}):
        with patch("mcp_servers.github_server.get_github_client", return_value=mock_github):
            # Call tool
            result = await create_repository(name="test-repo", private=False, description="Test")

            # Verify result structure
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], TextContent)

            # Verify GitHub API was called
            mock_user.create_repo.assert_called_once()
