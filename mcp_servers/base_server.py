"""Base utilities for MCP servers."""

import logging
import os
import time
from typing import Any, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class MCPAuthError(Exception):
    """Raised when authentication credentials are missing or invalid."""
    pass


def inject_token(env_var: str) -> str:
    """
    Read authentication token from environment variable.

    Args:
        env_var: Name of the environment variable (e.g., "GITHUB_TOKEN")

    Returns:
        Token value

    Raises:
        MCPAuthError: If environment variable is not set
    """
    token = os.getenv(env_var)
    if not token:
        raise MCPAuthError(
            f"Missing authentication: {env_var} environment variable not set. "
            f"User must connect their account via the UI first."
        )
    return token


def log_tool_call(func: Callable) -> Callable:
    """
    Decorator to log MCP tool calls with duration and status.

    Usage:
        @log_tool_call
        async def my_tool(arg1, arg2):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        tool_name = func.__name__
        start_time = time.time()

        logger.info(f"[MCP] Starting tool call: {tool_name}")
        logger.debug(f"[MCP] Tool args: {kwargs}")

        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                f"[MCP] Tool call succeeded: {tool_name} "
                f"(duration: {duration:.2f}s)"
            )

            return result

        except MCPAuthError as e:
            duration = time.time() - start_time
            logger.error(
                f"[MCP] Tool call auth error: {tool_name} "
                f"(duration: {duration:.2f}s) - {e}"
            )
            raise

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"[MCP] Tool call failed: {tool_name} "
                f"(duration: {duration:.2f}s) - {type(e).__name__}: {e}"
            )
            raise

    return wrapper


def format_error_response(error: Exception) -> dict[str, Any]:
    """
    Format exception into standardized MCP error response.

    Args:
        error: Exception that occurred

    Returns:
        Dictionary with error details
    """
    if isinstance(error, MCPAuthError):
        return {
            "error": "authentication_required",
            "message": str(error),
            "code": "AUTH_MISSING"
        }
    else:
        return {
            "error": type(error).__name__,
            "message": str(error),
            "code": "TOOL_ERROR"
        }


def format_success_response(data: Any) -> dict[str, Any]:
    """
    Format successful result into standardized MCP response.

    Args:
        data: Result data from tool execution

    Returns:
        Dictionary with success flag and data
    """
    return {
        "success": True,
        "data": data
    }
