# E2E Authentication Flow Tests

Comprehensive end-to-end test suite for the authentication flow in the Agentic Orchestra Orchestrator UI.

## Overview

This test suite covers the complete authentication flow:

1. GitHub OAuth integration
2. JWT token generation and validation
3. AI provider configuration
4. User session management
5. Frontend UI interactions

## Test Files

### 1. `test_auth_flow.py`
**Purpose:** API-level integration tests

**Coverage:**
- GitHub OAuth URL generation
- GitHub callback handling
- JWT token creation/validation/expiration
- AI provider configuration (save/retrieve/test)
- User status checks
- Error handling
- Full authentication flow simulation

**Test Methods:**
- `test_github_auth_url_generation()` - Verify GitHub OAuth URL is generated correctly
- `test_github_callback_missing_code()` - Test error handling for missing OAuth code
- `test_github_callback_invalid_code()` - Test error handling for invalid OAuth code
- `test_jwt_token_creation()` - Verify JWT tokens are created correctly
- `test_jwt_token_expiration()` - Test token expiration validation
- `test_jwt_token_invalid_signature()` - Test invalid token signature rejection
- `test_ai_provider_test_connection()` - Test AI provider connection testing
- `test_ai_provider_test_missing_fields()` - Test validation for missing fields
- `test_ai_provider_save_missing_user_id()` - Test save validation
- `test_ai_provider_get_nonexistent_user()` - Test retrieving non-existent config
- `test_github_status_nonexistent_user()` - Test status for non-existent user
- `test_github_status_missing_user_id()` - Test validation
- `test_full_auth_flow_without_github()` - Complete flow simulation
- `test_invalid_endpoints()` - Test error responses
- `test_malformed_json()` - Test JSON validation

### 2. `test_auth_flow_browser.py`
**Purpose:** Browser-based UI tests

**Coverage:**
- Frontend UI rendering
- Form interactions
- Navigation flow
- Button functionality
- Client-side validation
- User experience flow

**Test Classes:**
- `TestAuthFlowSelenium` - Tests using Selenium WebDriver
- `TestAuthFlowPlaywright` - Tests using Playwright

**Test Methods:**
- `test_auth_screen_loads()` - Verify auth screen renders correctly
- `test_github_button_click()` - Test GitHub button functionality
- `test_redirect_to_auth_when_not_authenticated()` - Test auth redirects
- `test_provider_setup_screen_loads()` - Verify provider setup UI
- `test_provider_setup_form_validation()` - Test form validation
- `test_navigation_flow_playwright()` - Test complete navigation

### 3. `run_tests.py`
**Purpose:** Test orchestration and reporting

**Features:**
- Dependency checking
- Service availability verification
- Test execution
- Comprehensive reporting
- Manual test support

## Installation

### Required Dependencies

```bash
# Core dependencies (required)
pip install requests pytest PyJWT

# Browser testing (optional)
pip install selenium playwright

# Install Playwright browsers
playwright install chromium
```

### Full Installation

```bash
cd orchestrator-ui/tests
pip install -r requirements.txt
```

## Running Tests

### Option 1: Quick Manual Test

Run the manual test script (no pytest required):

```bash
python test_auth_flow.py
```

This runs a quick verification of all endpoints.

### Option 2: Run All Tests with Test Runner

```bash
# Run all tests with report
python run_tests.py

# Verbose output
python run_tests.py --verbose

# Include browser tests
python run_tests.py --browser

# Manual tests only
python run_tests.py --manual
```

### Option 3: Run with pytest

```bash
# Run API tests
pytest test_auth_flow.py -v

# Run browser tests
pytest test_auth_flow_browser.py -v

# Run all tests
pytest -v

# Run specific test
pytest test_auth_flow.py::TestAuthFlow::test_github_auth_url_generation -v

# Run with coverage
pytest --cov=../backend --cov-report=html
```

## Prerequisites

### 1. Start Backend Service

```bash
cd orchestrator-ui/backend
uvicorn main:app --reload
```

Backend should be running on `http://localhost:8000`

### 2. Start Frontend Service

```bash
cd orchestrator-ui/frontend
npm install
npm run dev
```

Frontend should be running on `http://localhost:5173`

### 3. Verify Services

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:5173
```

## Manual Testing Guide

### Complete Flow Test

1. **Open Auth Screen**
   - Navigate to: `http://localhost:5173/auth`
   - Verify: "Agentic Orchestra" title visible
   - Verify: "Connect GitHub" button present

2. **GitHub OAuth Flow**
   - Click "Connect GitHub"
   - Should redirect to GitHub OAuth page
   - Authorize the application
   - Should redirect back to `/auth/callback`
   - Should automatically redirect to `/provider-setup`

3. **AI Provider Setup**
   - Verify: "Configure AI Provider" page loads
   - Verify: Two input fields present (Base URL, API Key)
   - Enter Base URL: `https://api.openai.com/v1`
   - Enter API Key: `sk-test-key` (or real key)

4. **Test Connection**
   - Click "Test" button
   - Verify: Shows success or failure message
   - With invalid key: Should show error
   - With valid key: Should show success

5. **Save Configuration**
   - Click "Save & Continue"
   - Should save to database
   - Should redirect to main dashboard `/`

6. **Verify Persistence**
   - Refresh page
   - Should remain authenticated
   - Should show dashboard

7. **Test Logout**
   - Open browser console: `F12`
   - Run: `localStorage.clear()`
   - Refresh page
   - Should redirect to `/auth`

### API Endpoint Tests

Use curl or Postman to test individual endpoints:

```bash
# 1. Get GitHub auth URL
curl http://localhost:8000/api/auth/github/login

# 2. Test AI provider connection
curl -X POST http://localhost:8000/api/config/ai-provider/test \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://api.openai.com/v1", "api_key": "sk-test"}'

# 3. Check GitHub status
curl "http://localhost:8000/api/auth/github/status?user_id=1"

# 4. Get AI provider config
curl "http://localhost:8000/api/config/ai-provider?user_id=1"

# 5. Health check
curl http://localhost:8000/health
```

## Test Coverage

### API Endpoints Tested

- `GET /api/auth/github/login` - GitHub OAuth URL generation
- `GET /api/auth/github/callback` - GitHub OAuth callback
- `GET /api/auth/github/status` - GitHub connection status
- `POST /api/config/ai-provider` - Save AI provider config
- `GET /api/config/ai-provider` - Retrieve AI provider config
- `POST /api/config/ai-provider/test` - Test AI provider connection
- `GET /health` - Health check

### Frontend Routes Tested

- `/auth` - Authentication screen
- `/auth/callback` - OAuth callback handler
- `/provider-setup` - AI provider setup
- `/` - Main dashboard (requires auth)

### Test Scenarios

**Happy Path:**
- User authenticates with GitHub
- User configures AI provider
- User accesses dashboard
- Session persists across refreshes

**Error Scenarios:**
- Missing OAuth code
- Invalid OAuth code
- Expired JWT token
- Invalid JWT signature
- Missing user ID
- Invalid AI provider credentials
- Malformed JSON requests
- Non-existent endpoints

**Edge Cases:**
- Token expiration
- Service unavailability
- Network timeouts
- Invalid input validation
- Concurrent requests

## Test Results

### Expected Output (All Passing)

```
==================================================================
E2E AUTHENTICATION FLOW TEST SUITE
==================================================================

Checking dependencies...
  - requests     INSTALLED
  - pytest       INSTALLED
  - jwt          INSTALLED
  - selenium     INSTALLED
  - playwright   INSTALLED

Checking services...
  - Backend     RUNNING
  - Frontend    RUNNING

==================================================================
RUNNING MANUAL TESTS
==================================================================

[1/5] Testing GitHub auth URL generation
  - Status: 200
  - Auth URL: https://github.com/login/oauth/authorize?client_id=...

[2/5] Testing AI provider connection test
  - Status: 200
  - Success: False
  - Message: Failed with status 401

[3/5] Testing GitHub connection status
  - Status: 200
  - Connected: False

[4/5] Testing JWT token creation
  - Token created: eyJhbGciOiJIUzI1NiIsInR5cCI6...
  - User ID: 123

[5/5] Testing health endpoint
  - Status: 200
  - Health: healthy

==================================================================
ALL MANUAL TESTS PASSED
==================================================================

==================================================================
RUNNING PYTEST TESTS
==================================================================

test_auth_flow.py::TestAuthFlow::test_github_auth_url_generation PASSED
test_auth_flow.py::TestAuthFlow::test_github_callback_missing_code PASSED
test_auth_flow.py::TestAuthFlow::test_jwt_token_creation PASSED
test_auth_flow.py::TestAuthFlow::test_ai_provider_test_connection PASSED
... (all tests pass)

==================================================================
TEST EXECUTION REPORT
==================================================================

Execution Time: 2024-04-05 15:30:00

Dependencies:
  - requests      INSTALLED
  - pytest        INSTALLED
  - jwt           INSTALLED
  - selenium      INSTALLED
  - playwright    INSTALLED

Services:
  - Backend      RUNNING
  - Frontend     RUNNING

Test Results:
  - Manual Tests       PASSED
  - Pytest Tests       PASSED

Overall Status:
  ALL TESTS PASSED

==================================================================
```

## Troubleshooting

### Backend Not Running

**Error:** `Connection refused` or `Service not running`

**Solution:**
```bash
cd orchestrator-ui/backend
uvicorn main:app --reload
```

### Frontend Not Running

**Error:** Frontend service not accessible

**Solution:**
```bash
cd orchestrator-ui/frontend
npm install
npm run dev
```

### Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
```bash
pip install requests pytest PyJWT
# For browser tests
pip install selenium playwright
playwright install chromium
```

### GitHub OAuth Not Configured

**Error:** OAuth redirects fail or client_id is empty

**Solution:**
1. Register GitHub OAuth App at: https://github.com/settings/developers
2. Set environment variables:
   ```bash
   export GITHUB_CLIENT_ID=your_client_id
   export GITHUB_CLIENT_SECRET=your_client_secret
   export GITHUB_REDIRECT_URI=http://localhost:5173/auth/callback
   ```

### Database Errors

**Error:** Database connection or query errors

**Solution:**
```bash
cd orchestrator-ui/backend
python init_db.py  # Initialize database
```

### Browser Tests Fail

**Error:** Selenium or Playwright tests fail

**Solution:**
```bash
# For Selenium
pip install selenium
# Download ChromeDriver: https://chromedriver.chromium.org/

# For Playwright
pip install playwright
playwright install chromium
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r orchestrator-ui/tests/requirements.txt
          playwright install chromium

      - name: Start backend
        run: |
          cd orchestrator-ui/backend
          uvicorn main:app &
          sleep 5

      - name: Start frontend
        run: |
          cd orchestrator-ui/frontend
          npm install
          npm run dev &
          sleep 10

      - name: Run tests
        run: |
          cd orchestrator-ui/tests
          python run_tests.py --verbose --browser
```

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Use descriptive test names
3. Include docstrings explaining what is tested
4. Add both positive and negative test cases
5. Update this README with new test coverage

## License

Same as parent project.
