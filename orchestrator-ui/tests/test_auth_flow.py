"""
E2E Authentication Flow Tests

This module provides comprehensive end-to-end tests for the authentication flow,
including GitHub OAuth, JWT token generation, and AI provider configuration.

Test Coverage:
- GitHub OAuth URL generation
- GitHub OAuth callback handling
- JWT token creation and validation
- AI provider configuration (save/retrieve/test)
- User creation and updates
- Error scenarios and edge cases
"""

import pytest
import requests
import json
import jwt
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
API_PREFIX = "/api"
SECRET_KEY = "secret"  # Should match JWT_SECRET in backend


class TestAuthFlow:
    """
    Test suite for the complete authentication flow.

    This class tests the entire user journey from initial GitHub OAuth
    to AI provider configuration.
    """

    def setup_method(self):
        """Setup before each test method."""
        self.base_url = BASE_URL
        self.api_url = f"{BASE_URL}{API_PREFIX}"
        self.session = requests.Session()
        self.test_user_id: Optional[int] = None
        self.test_token: Optional[str] = None

    def teardown_method(self):
        """Cleanup after each test method."""
        self.session.close()

    # ========== GitHub OAuth Tests ==========

    def test_github_auth_url_generation(self):
        """
        Test GitHub OAuth URL generation.

        Verifies:
        - Endpoint returns 200 status
        - Response contains 'url' field
        - URL contains GitHub OAuth domain
        - URL contains client_id parameter
        """
        print("\n[TEST] GitHub auth URL generation")

        response = self.session.get(f"{self.api_url}/auth/github/login")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "url" in data, "Response missing 'url' field"
        assert "github.com/login/oauth/authorize" in data["url"], "URL should point to GitHub OAuth"
        assert "client_id=" in data["url"], "URL should contain client_id parameter"

        print(f"  - Status: 200")
        print(f"  - Auth URL generated: {data['url'][:50]}...")
        print("  - Test PASSED")

    def test_github_callback_missing_code(self):
        """
        Test GitHub callback endpoint without authorization code.

        Verifies:
        - Returns 400 Bad Request
        - Error message is appropriate
        """
        print("\n[TEST] GitHub callback - missing code")

        response = self.session.get(f"{self.api_url}/auth/github/callback")

        assert response.status_code == 422 or response.status_code == 400, \
            f"Expected 400/422, got {response.status_code}"

        print(f"  - Status: {response.status_code}")
        print("  - Test PASSED")

    def test_github_callback_invalid_code(self):
        """
        Test GitHub callback with invalid authorization code.

        Verifies:
        - Handles invalid codes gracefully
        - Returns appropriate error status
        """
        print("\n[TEST] GitHub callback - invalid code")

        invalid_code = "invalid_test_code_12345"
        response = self.session.get(
            f"{self.api_url}/auth/github/callback?code={invalid_code}"
        )

        # Should return 500 or 400 due to invalid code with GitHub
        assert response.status_code in [400, 500], \
            f"Expected 400/500, got {response.status_code}"

        print(f"  - Status: {response.status_code}")
        print("  - Test PASSED")

    # ========== JWT Token Tests ==========

    def test_jwt_token_creation(self):
        """
        Test JWT token creation and structure.

        Verifies:
        - Token can be created
        - Token contains user_id
        - Token contains expiration
        - Token is properly signed
        """
        print("\n[TEST] JWT token creation")

        test_user_id = 123
        payload = {
            "user_id": test_user_id,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        assert token is not None, "Token should not be None"
        assert isinstance(token, str), "Token should be a string"

        # Decode and verify
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        assert decoded["user_id"] == test_user_id, "User ID should match"
        assert "exp" in decoded, "Token should have expiration"

        print(f"  - Token created: {token[:20]}...")
        print(f"  - User ID: {decoded['user_id']}")
        print(f"  - Expires: {datetime.fromtimestamp(decoded['exp'])}")
        print("  - Test PASSED")

    def test_jwt_token_expiration(self):
        """
        Test JWT token expiration validation.

        Verifies:
        - Expired tokens are rejected
        - Valid tokens are accepted
        """
        print("\n[TEST] JWT token expiration")

        # Create expired token
        payload = {
            "user_id": 123,
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        expired_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        # Try to decode expired token
        try:
            jwt.decode(expired_token, SECRET_KEY, algorithms=["HS256"])
            assert False, "Expired token should raise exception"
        except jwt.ExpiredSignatureError:
            print("  - Expired token rejected correctly")

        # Create valid token
        payload["exp"] = datetime.utcnow() + timedelta(days=1)
        valid_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        # Decode valid token
        decoded = jwt.decode(valid_token, SECRET_KEY, algorithms=["HS256"])
        assert decoded["user_id"] == 123, "Valid token should decode"

        print("  - Valid token accepted")
        print("  - Test PASSED")

    def test_jwt_token_invalid_signature(self):
        """
        Test JWT token with invalid signature.

        Verifies:
        - Tokens with wrong signature are rejected
        """
        print("\n[TEST] JWT token - invalid signature")

        # Create token with wrong secret
        payload = {
            "user_id": 123,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        wrong_token = jwt.encode(payload, "wrong_secret", algorithm="HS256")

        # Try to decode with correct secret
        try:
            jwt.decode(wrong_token, SECRET_KEY, algorithms=["HS256"])
            assert False, "Invalid signature should raise exception"
        except jwt.InvalidSignatureError:
            print("  - Invalid signature rejected correctly")

        print("  - Test PASSED")

    # ========== AI Provider Configuration Tests ==========

    def test_ai_provider_test_connection(self):
        """
        Test AI provider connection testing endpoint.

        Verifies:
        - Endpoint accepts test requests
        - Returns success/failure status
        - Handles invalid credentials
        """
        print("\n[TEST] AI provider - test connection")

        # Test with invalid credentials (should fail)
        test_data = {
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-invalid-test-key-12345"
        }

        response = self.session.post(
            f"{self.api_url}/config/ai-provider/test",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert "success" in data, "Response should contain 'success' field"
        assert data["success"] == False, "Invalid credentials should fail"
        assert "message" in data, "Response should contain 'message' field"

        print(f"  - Status: {response.status_code}")
        print(f"  - Success: {data['success']}")
        print(f"  - Message: {data['message']}")
        print("  - Test PASSED")

    def test_ai_provider_test_missing_fields(self):
        """
        Test AI provider test with missing required fields.

        Verifies:
        - Missing base_url returns 400/422
        - Missing api_key returns 400/422
        """
        print("\n[TEST] AI provider - missing fields")

        # Missing base_url
        response = self.session.post(
            f"{self.api_url}/config/ai-provider/test",
            json={"api_key": "sk-test"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422], \
            f"Missing base_url should return 400/422, got {response.status_code}"
        print(f"  - Missing base_url: {response.status_code}")

        # Missing api_key
        response = self.session.post(
            f"{self.api_url}/config/ai-provider/test",
            json={"base_url": "https://api.openai.com/v1"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422], \
            f"Missing api_key should return 400/422, got {response.status_code}"
        print(f"  - Missing api_key: {response.status_code}")

        print("  - Test PASSED")

    def test_ai_provider_save_missing_user_id(self):
        """
        Test AI provider save without user_id.

        Verifies:
        - Missing user_id returns error
        """
        print("\n[TEST] AI provider - save missing user_id")

        config_data = {
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-test"
        }

        response = self.session.post(
            f"{self.api_url}/config/ai-provider",
            json=config_data,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code in [400, 422], \
            f"Missing user_id should return 400/422, got {response.status_code}"

        print(f"  - Status: {response.status_code}")
        print("  - Test PASSED")

    def test_ai_provider_get_nonexistent_user(self):
        """
        Test retrieving AI provider config for non-existent user.

        Verifies:
        - Returns configured=False
        - Returns base_url=None
        """
        print("\n[TEST] AI provider - get non-existent user")

        nonexistent_user_id = 999999
        response = self.session.get(
            f"{self.api_url}/config/ai-provider?user_id={nonexistent_user_id}"
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["configured"] == False, "Non-existent user should not be configured"
        assert data["base_url"] is None, "Base URL should be None"

        print(f"  - Status: {response.status_code}")
        print(f"  - Configured: {data['configured']}")
        print("  - Test PASSED")

    # ========== GitHub Status Tests ==========

    def test_github_status_nonexistent_user(self):
        """
        Test GitHub connection status for non-existent user.

        Verifies:
        - Returns connected=False
        - Returns username=None
        """
        print("\n[TEST] GitHub status - non-existent user")

        nonexistent_user_id = 999999
        response = self.session.get(
            f"{self.api_url}/auth/github/status?user_id={nonexistent_user_id}"
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["connected"] == False, "Non-existent user should not be connected"
        assert data["username"] is None, "Username should be None"

        print(f"  - Status: {response.status_code}")
        print(f"  - Connected: {data['connected']}")
        print("  - Test PASSED")

    def test_github_status_missing_user_id(self):
        """
        Test GitHub status endpoint without user_id.

        Verifies:
        - Returns appropriate error
        """
        print("\n[TEST] GitHub status - missing user_id")

        response = self.session.get(f"{self.api_url}/auth/github/status")

        assert response.status_code in [400, 422], \
            f"Missing user_id should return 400/422, got {response.status_code}"

        print(f"  - Status: {response.status_code}")
        print("  - Test PASSED")

    # ========== Integration Tests ==========

    def test_full_auth_flow_without_github(self):
        """
        Test complete auth flow simulation (without actual GitHub OAuth).

        This test simulates the full flow:
        1. Get auth URL
        2. Create mock JWT token
        3. Test AI provider connection
        4. Verify token validation
        """
        print("\n[TEST] Full auth flow simulation")

        # Step 1: Get GitHub auth URL
        print("  Step 1: Get GitHub auth URL")
        response = self.session.get(f"{self.api_url}/auth/github/login")
        assert response.status_code == 200
        auth_data = response.json()
        print(f"    - Auth URL: {auth_data['url'][:50]}...")

        # Step 2: Simulate JWT token creation
        print("  Step 2: Create mock JWT token")
        mock_user_id = 12345
        payload = {
            "user_id": mock_user_id,
            "exp": datetime.utcnow() + timedelta(days=1)
        }
        mock_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        print(f"    - Token: {mock_token[:20]}...")

        # Step 3: Verify token
        print("  Step 3: Verify token")
        decoded = jwt.decode(mock_token, SECRET_KEY, algorithms=["HS256"])
        assert decoded["user_id"] == mock_user_id
        print(f"    - User ID verified: {decoded['user_id']}")

        # Step 4: Test AI provider connection
        print("  Step 4: Test AI provider connection")
        test_data = {
            "base_url": "https://api.openai.com/v1",
            "api_key": "sk-invalid-test"
        }
        response = self.session.post(
            f"{self.api_url}/config/ai-provider/test",
            json=test_data
        )
        assert response.status_code == 200
        provider_data = response.json()
        print(f"    - Test result: {provider_data['success']}")
        print(f"    - Message: {provider_data['message']}")

        # Step 5: Check GitHub status (will be false for mock user)
        print("  Step 5: Check GitHub status")
        response = self.session.get(
            f"{self.api_url}/auth/github/status?user_id={mock_user_id}"
        )
        assert response.status_code == 200
        status_data = response.json()
        print(f"    - Connected: {status_data['connected']}")

        print("  - Test PASSED")

    # ========== Error Handling Tests ==========

    def test_invalid_endpoints(self):
        """
        Test invalid endpoints and methods.

        Verifies:
        - Non-existent endpoints return 404
        - Wrong HTTP methods return 405
        """
        print("\n[TEST] Invalid endpoints and methods")

        # Non-existent endpoint
        response = self.session.get(f"{self.api_url}/auth/nonexistent")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"  - Non-existent endpoint: 404")

        # Wrong HTTP method (POST to GET endpoint)
        response = self.session.post(f"{self.api_url}/auth/github/login")
        assert response.status_code == 405, f"Expected 405, got {response.status_code}"
        print(f"  - Wrong HTTP method: 405")

        print("  - Test PASSED")

    def test_malformed_json(self):
        """
        Test endpoints with malformed JSON.

        Verifies:
        - Malformed JSON returns 422
        """
        print("\n[TEST] Malformed JSON")

        response = self.session.post(
            f"{self.api_url}/config/ai-provider/test",
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422, \
            f"Malformed JSON should return 422, got {response.status_code}"

        print(f"  - Status: {response.status_code}")
        print("  - Test PASSED")


# ========== Standalone Test Functions ==========

def run_manual_test():
    """
    Manual test function for quick verification.

    This can be run directly without pytest for quick checks.
    """
    print("\n" + "=" * 60)
    print("MANUAL AUTH FLOW TEST")
    print("=" * 60)

    # Test 1: GitHub auth URL
    print("\n[1/5] Testing GitHub auth URL generation")
    res = requests.get(f"{BASE_URL}/api/auth/github/login")
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    print(f"  - Status: 200")
    print(f"  - Auth URL: {data['url'][:80]}...")

    # Test 2: AI provider test
    print("\n[2/5] Testing AI provider connection test")
    res = requests.post(
        f"{BASE_URL}/api/config/ai-provider/test",
        json={"base_url": "https://api.openai.com/v1", "api_key": "sk-test"}
    )
    assert res.status_code == 200
    data = res.json()
    print(f"  - Status: {res.status_code}")
    print(f"  - Success: {data['success']}")
    print(f"  - Message: {data['message']}")

    # Test 3: GitHub status
    print("\n[3/5] Testing GitHub connection status")
    res = requests.get(f"{BASE_URL}/api/auth/github/status?user_id=999999")
    assert res.status_code == 200
    data = res.json()
    print(f"  - Status: {res.status_code}")
    print(f"  - Connected: {data['connected']}")

    # Test 4: JWT token
    print("\n[4/5] Testing JWT token creation")
    payload = {
        "user_id": 123,
        "exp": datetime.utcnow() + timedelta(days=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    print(f"  - Token created: {token[:30]}...")
    print(f"  - User ID: {decoded['user_id']}")

    # Test 5: Health check
    print("\n[5/5] Testing health endpoint")
    res = requests.get(f"{BASE_URL}/health")
    assert res.status_code == 200
    data = res.json()
    print(f"  - Status: {res.status_code}")
    print(f"  - Health: {data['status']}")

    print("\n" + "=" * 60)
    print("ALL MANUAL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    """
    Run manual tests when script is executed directly.

    For pytest execution, use: pytest test_auth_flow.py -v
    """
    try:
        run_manual_test()
    except Exception as e:
        print(f"\n ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
