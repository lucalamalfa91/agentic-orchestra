# Quick Start Guide - E2E Auth Tests

## TL;DR - Run Tests in 30 Seconds

```bash
# 1. Navigate to tests directory
cd orchestrator-ui/tests

# 2. Install dependencies (first time only)
pip install requests pytest PyJWT

# 3. Run tests
python test_auth_flow.py
```

That's it! You should see:
```
============================================================
ALL MANUAL TESTS PASSED
============================================================
```

---

## Full Setup (5 Minutes)

### Step 1: Ensure Services are Running

```bash
# Terminal 1: Start Backend
cd orchestrator-ui/backend
uvicorn main:app --reload

# Terminal 2: Start Frontend
cd orchestrator-ui/frontend
npm install
npm run dev
```

### Step 2: Install Test Dependencies

```bash
cd orchestrator-ui/tests
pip install -r requirements.txt
```

### Step 3: Run Tests

```bash
# Quick manual test
python test_auth_flow.py

# Full pytest suite
pytest -v

# With test runner and report
python run_tests.py --verbose
```

---

## Test Options

### 1. Quick Manual Test (No pytest needed)

```bash
python test_auth_flow.py
```

**What it tests:**
- GitHub auth URL generation
- AI provider connection test
- GitHub status check
- JWT token creation
- Health endpoint

**Duration:** ~2 seconds

---

### 2. Full pytest Suite

```bash
pytest -v
```

**What it tests:**
- All API endpoints (15+ tests)
- Error scenarios
- Edge cases
- Validation logic
- Token handling

**Duration:** ~10 seconds

---

### 3. Browser Tests (Optional)

```bash
# Install browser tools first
pip install selenium playwright
playwright install chromium

# Run browser tests
pytest test_auth_flow_browser.py -v
```

**What it tests:**
- Frontend UI rendering
- Form interactions
- Navigation flow
- User experience

**Duration:** ~30 seconds

---

### 4. Complete Test Suite with Report

```bash
python run_tests.py --verbose --browser
```

**What it does:**
- Checks dependencies
- Verifies services are running
- Runs all tests
- Generates comprehensive report

**Duration:** ~1 minute

---

## Common Commands

```bash
# Run specific test
pytest test_auth_flow.py::TestAuthFlow::test_github_auth_url_generation -v

# Run with coverage
pytest --cov=../backend --cov-report=html

# Run in parallel (faster)
pytest -n auto

# Generate HTML report
python test_report_generator.py
```

---

## Troubleshooting

### Backend Not Running?

```bash
cd orchestrator-ui/backend
uvicorn main:app --reload
```

Verify: `curl http://localhost:8000/health`

### Frontend Not Running?

```bash
cd orchestrator-ui/frontend
npm run dev
```

Verify: `curl http://localhost:5173`

### Missing Dependencies?

```bash
pip install requests pytest PyJWT
```

### Tests Failing?

1. Check services are running
2. Check .env file has correct configuration
3. Check database is initialized: `python backend/init_db.py`
4. Try: `pytest -v -s` for detailed output

---

## Manual Browser Test (2 Minutes)

1. Open: `http://localhost:5173/auth`
2. Click: "Connect GitHub"
3. Authorize on GitHub
4. Redirects to `/provider-setup`
5. Enter Base URL: `https://api.openai.com/v1`
6. Enter API Key: `sk-your-key`
7. Click: "Test" (verify connection)
8. Click: "Save & Continue"
9. Should redirect to dashboard

---

## What Each Test File Does

| File | Purpose | Run Command |
|------|---------|-------------|
| `test_auth_flow.py` | API tests | `python test_auth_flow.py` |
| `test_auth_flow_browser.py` | UI tests | `pytest test_auth_flow_browser.py` |
| `run_tests.py` | Test runner | `python run_tests.py` |
| `test_report_generator.py` | Reports | `python test_report_generator.py` |

---

## Expected Output

### Successful Test Run:

```
============================================================
MANUAL AUTH FLOW TEST
============================================================

[1/5] Testing GitHub auth URL generation
  - Status: 200
  - Auth URL: https://github.com/login/oauth/authorize?client_id=...
  ✓ PASSED

[2/5] Testing AI provider connection test
  - Status: 200
  - Success: False
  - Message: Failed with status 401
  ✓ PASSED

[3/5] Testing GitHub connection status
  - Status: 200
  - Connected: False
  ✓ PASSED

[4/5] Testing JWT token creation
  - Token created: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...
  - User ID: 123
  ✓ PASSED

[5/5] Testing health endpoint
  - Status: 200
  - Health: healthy
  ✓ PASSED

============================================================
ALL MANUAL TESTS PASSED
============================================================
```

---

## Need Help?

- See `README.md` for full documentation
- See `TEST_EXECUTION_REPORT.md` for detailed results
- Check service logs for errors:
  - Backend: Terminal running uvicorn
  - Frontend: Terminal running npm

---

## Quick Links

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

**Happy Testing!** 🚀
