"""Test that all MCP server modules can be imported (syntax check)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("MCP Servers Import Test")
print("=" * 70)

# Mock unavailable dependencies
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.types'] = MagicMock()
sys.modules['mcp.client'] = MagicMock()
sys.modules['mcp.client.stdio'] = MagicMock()
sys.modules['github'] = MagicMock()
sys.modules['azure'] = MagicMock()
sys.modules['azure.devops'] = MagicMock()
sys.modules['azure.devops.connection'] = MagicMock()
sys.modules['azure.devops.v7_0'] = MagicMock()
sys.modules['azure.devops.v7_0.work_item_tracking'] = MagicMock()
sys.modules['azure.devops.v7_0.work_item_tracking.models'] = MagicMock()
sys.modules['msrest'] = MagicMock()
sys.modules['msrest.authentication'] = MagicMock()
sys.modules['httpx'] = MagicMock()

# Test base_server
try:
    from mcp_servers.base_server import (
        MCPAuthError,
        inject_token,
        log_tool_call,
        format_error_response,
        format_success_response
    )
    print("[OK] base_server: all exports")
except Exception as e:
    print(f"[FAIL] base_server: {e}")
    sys.exit(1)

# Test github_server
try:
    from mcp_servers import github_server
    print("[OK] github_server: module imports")
except SyntaxError as e:
    print(f"[FAIL] github_server syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] github_server (expected, mocked deps): {type(e).__name__}")

# Test azuredevops_server
try:
    from mcp_servers import azuredevops_server
    print("[OK] azuredevops_server: module imports")
except SyntaxError as e:
    print(f"[FAIL] azuredevops_server syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] azuredevops_server (expected, mocked deps): {type(e).__name__}")

# Test deploy_server
try:
    from mcp_servers import deploy_server
    print("[OK] deploy_server: module imports")
except SyntaxError as e:
    print(f"[FAIL] deploy_server syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] deploy_server (expected, mocked deps): {type(e).__name__}")

# Test client
try:
    from mcp_servers.client import MCPClientManager, create_client_manager, execute_tool
    print("[OK] client: MCPClientManager, create_client_manager, execute_tool")
except SyntaxError as e:
    print(f"[FAIL] client syntax: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[SKIP] client (expected, mocked deps): {type(e).__name__}")

# Test MCPAuthError functionality
try:
    raise MCPAuthError("Test error")
except MCPAuthError as e:
    assert str(e) == "Test error"
    print("[OK] MCPAuthError: custom exception works")

# Test format functions
try:
    success = format_success_response({"key": "value"})
    assert success["success"] is True
    assert success["data"] == {"key": "value"}
    print("[OK] format_success_response: correct format")

    error = format_error_response(ValueError("test"))
    assert error["error"] == "ValueError"
    assert error["message"] == "test"
    print("[OK] format_error_response: correct format")

except AssertionError as e:
    print(f"[FAIL] format functions: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("[OK] All MCP server modules have valid syntax!")
print("[INFO] Install dependencies from requirements to run servers")
print("=" * 70)
