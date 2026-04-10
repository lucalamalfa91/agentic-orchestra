# Agentic Orchestra

AI-powered system that transforms text requirements into complete applications through orchestrated AI agents.

## Quick Start

### Prerequisites
- Node.js 18+ | Python 3.10+ | Git

### Setup

⚠️ **IMPORTANT**: All commands below must be run from the **project root** (`agentic-orchestra/`), not from subdirectories.

**Quick health check**: Run `bash check_setup.sh` to verify your setup.

```bash
# 0. Navigate to project root (adjust path as needed)
cd ~/PycharmProjects/agentic-orchestra
# OR on Windows: cd C:\Users\YourName\PycharmProjects\agentic-orchestra

# Optional: Check setup status
bash check_setup.sh

# 1. Environment
cp .env.example .env
# Edit .env: add GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, AI_BASE_URL, AI_API_KEY

# 2. Install Dependencies
pip install -r requirements.txt
cd orchestrator-ui/frontend && npm install && cd ../..

# 3. Backend (Terminal 1) - Open NEW terminal, navigate to project root first!

# Linux/Mac:
cd orchestrator-ui/backend
export PYTHONPATH="$(cd ../.. && pwd)"
python main.py

# Windows Git Bash:
cd orchestrator-ui/backend
export PYTHONPATH="$(cd ../.. && pwd -W)"  # -W gives Windows path
python main.py

# Windows (PowerShell):
cd orchestrator-ui\backend
$env:PYTHONPATH = (Resolve-Path ..\.. ).Path
python main.py

# Windows (CMD):
cd orchestrator-ui\backend
for /f %i in ('cd') do set PYTHONPATH=%i\..\..
python main.py

# 4. Frontend (Terminal 2) - Open NEW terminal, navigate to project root first!
cd orchestrator-ui/frontend
npm run dev

# 5. Open http://localhost:5173
```

### GitHub OAuth Setup

1. Go to https://github.com/settings/developers
2. Create OAuth App with callback: `http://localhost:5173/auth/callback`
3. Copy Client ID/Secret to `.env`

### First Generation

1. Connect GitHub account
2. Configure AI Provider (Base URL + API Key)
3. Enter app description: "Weather app with 7-day forecast"
4. Click Generate → Watch progress → View repo on GitHub

**Resume failed generations**: Project History → Click "▶ Resume Generation"

### Quick Start (Step by Step)

If you're getting errors, follow this exact sequence:

```bash
# 1. Verify you're in project root
pwd  # Should show: .../agentic-orchestra
ls .env.example requirements.txt  # Should list both files

# 2. If not in root, navigate there first
cd ~/PycharmProjects/agentic-orchestra  # Adjust path as needed

# 3. Setup environment (if .env doesn't exist)
cp .env.example .env
# Edit .env with your credentials

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Install frontend dependencies
cd orchestrator-ui/frontend
npm install
cd ../..  # Back to root

# 6. Start Backend (Terminal 1)
cd orchestrator-ui/backend
export PYTHONPATH="$(cd ../.. && pwd -W)"  # Git Bash on Windows
python main.py
# Should show: "Starting Orchestrator UI Backend..." and "Database initialized"

# 7. Start Frontend (Terminal 2 - NEW terminal, start from root again!)
cd orchestrator-ui/frontend
npm run dev
# Should show: "Local: http://localhost:5173"

# 8. Open browser
# Go to: http://localhost:5173
```

### Verify Installation

```bash
# Check backend is running
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Check frontend is running
curl http://localhost:5173
# Should return: HTML response

# Check database (automatically initialized on first backend start)
ls database/orchestrator.db  # Should exist after backend starts
```

**Note**: Database is auto-initialized by `main.py` on first startup (no manual `init_db.py` needed)

---

## What It Does

Specialized AI agents collaborate via **LangGraph** to generate complete applications:

1. **Design Node** (`design_node.py`) → Architecture design, database schema (PlantUML), system docs
2. **Backend Node** (`backend_node.py`) → .NET 8 API, models, services, DTOs, repositories
3. **Frontend Node** (`frontend_node.py`) → React + TypeScript components, routing, state management
4. **DevOps Node** (`devops_node.py`) → GitHub Actions CI/CD, deployment workflows
5. **Backlog Node** (`backlog_node.py`) → Azure DevOps work items and task backlog
6. **Publish Node** (`publish_node.py`) → GitHub repository creation and code push

Each node's output feeds the next in a LangGraph-orchestrated pipeline from requirements to deployed repo.

**Best for**: MVPs, prototypes, CRUD apps, small teams needing rapid iteration
**Not for**: Complex algorithms, legacy integration, production without human review

---

## Environment Variables

```bash
# Required
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
AI_BASE_URL=https://api.openai.com/v1  # or compatible endpoint
AI_API_KEY=sk-...
JWT_SECRET=your-secret-min-32-chars
ENCRYPTION_KEY=your-encryption-key

# Optional (for deployment features)
VERCEL_CLIENT_ID=...
VERCEL_CLIENT_SECRET=...
RAILWAY_CLIENT_ID=...
RAILWAY_CLIENT_SECRET=...
```

---

## API

Full API docs: http://localhost:8000/docs (Swagger UI)

### Key Endpoints

**Authentication**
- `GET /api/auth/github/login` → GitHub OAuth URL
- `GET /api/auth/github/callback?code=X` → Exchange for JWT

**Generation**
- `POST /api/generation/start` → Start generation (returns WebSocket URL)
- `POST /api/projects/{id}/resume` → Retry failed generation
- `WS /ws/generation/{id}` → Real-time progress updates

**Configuration**
- `POST /api/config/ai-provider` → Save AI provider config
- `POST /api/config/ai-provider/test` → Test connection

---

## Troubleshooting

**ModuleNotFoundError: No module named 'orchestrator_ui' or 'AI_agents'**

This means PYTHONPATH is not set correctly. Make sure you:
1. Are starting from project root (not from `orchestrator-ui/backend`)
2. Set PYTHONPATH before running `python main.py`

```bash
# Git Bash (Windows):
cd ~/PycharmProjects/agentic-orchestra  # Go to root first!
cd orchestrator-ui/backend
export PYTHONPATH="$(cd ../.. && pwd -W)"
python main.py

# Verify PYTHONPATH is set:
echo $PYTHONPATH  # Should show full path to project root
```

**Port 8000 locked**
```bash
# Linux/Mac: Kill process
lsof -ti:8000 | xargs kill -9

# Windows (PowerShell): Kill process
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force

# Windows (CMD): Kill process
for /f "tokens=5" %a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do taskkill /F /PID %a

# Alternative: Use different port (all platforms)
cd orchestrator-ui/backend
python main.py 9000
```

**GitHub OAuth fails**
- Verify Client ID/Secret in `.env`
- Check callback URL: `http://localhost:5173/auth/callback`

**AI Provider fails**
- Test connection in UI
- Verify API key has quota

**Database locked**
```bash
# Linux/Mac: Kill all Python processes
pkill -f python
rm -f database/orchestrator.db

# Windows (PowerShell): Kill Python processes
Get-Process python | Stop-Process -Force
Remove-Item database\orchestrator.db -Force -ErrorAction SilentlyContinue

# Windows (CMD): Kill Python processes
taskkill /F /IM python.exe
del /F database\orchestrator.db

# Restart backend (database auto-initializes on startup)
cd orchestrator-ui/backend
python main.py
```

---

## Security

- **API Keys**: Encrypted with Fernet (ENCRYPTION_KEY)
- **JWT**: HS256, 24h expiration (JWT_SECRET)
- **CORS**: Configure `allow_origins` for production
- **Generated Code**: Review for vulnerabilities before deployment

**Pre-Production Checklist**
- [ ] Strong JWT_SECRET (32+ random chars)
- [ ] Strong ENCRYPTION_KEY
- [ ] CORS restricted to production domain
- [ ] HTTPS enabled
- [ ] Security audit on generated code
- [ ] Rate limiting enabled

---

## Limitations

- ⚠️ Generated code needs human review
- ⚠️ Quality depends on input clarity ("garbage in, garbage out")
- ⚠️ No memory between generations
- ⚠️ Predefined stacks only (.NET, React, GitHub Actions)
- ⚠️ Basic tests included, not comprehensive
- ⚠️ Not optimized for performance

**Use as**: Acceleration tool and starting point
**Not as**: Replacement for developers or production-ready code

---

## Resume Feature

Failed generations can be retried with one click:

**How**: Project History → Failed project card → "▶ Resume Generation"

**Details**:
- Restarts from beginning (not from failure point)
- Uses same requirements (no modifications)
- Increments attempt counter
- Separate logs per attempt

**API**: `POST /api/projects/{id}/resume`

**Limitations**: No mid-flow resume, no requirement editing during resume

---

## Architecture

### LangGraph Pipeline Flow
```
User Input → Design Node → Backend Node → Frontend Node → DevOps Node → Backlog Node → Publish Node → GitHub Repo
              (design)      (.NET code)    (React code)    (CI/CD)        (tasks)       (publish)
```

**Orchestration**: `AI_agents/graph/graph.py` (LangGraph StateGraph)
**Shared State**: `AI_agents/graph/state.py` (OrchestraState TypedDict)
**Nodes**: `AI_agents/graph/nodes/*.py` (one file per agent)

### Frontend Flow
```
AuthScreen → AIProviderSetup → MVPCreationScreen → ConfirmationScreen → DeployAuth → Progress → Success
```

### Tech Details
- **Database**: SQLite (local), PostgreSQL (production)
- **Auth**: GitHub OAuth → JWT (24h)
- **WebSocket**: Real-time generation progress
- **Encryption**: Fernet (API keys)
- **LLM Client**: `AI_agents/utils/llm_client.py` (factory pattern, supports OpenAI/Anthropic/custom)

---

## Tech Stack

**Backend**: FastAPI, SQLAlchemy, WebSocket, Alembic
**Frontend**: React, TypeScript, Vite, Tailwind
**Orchestration**: LangGraph (multi-agent workflow)
**AI**: OpenAI API compatible (OpenAI, Anthropic, local LLMs)
**Auth**: GitHub OAuth, JWT
**Database**: SQLite (dev), PostgreSQL (prod)

---

## Project Structure

```
AI_agents/
├── graph/               # LangGraph workflow
│   ├── graph.py        # Agent orchestration
│   ├── state.py        # Shared state schema
│   └── nodes/          # Individual agents
├── knowledge/          # RAG context sources
└── utils/              # LLM client factory

orchestrator-ui/
├── backend/
│   ├── main.py         # FastAPI app
│   ├── orchestrator.py # LangGraph bridge
│   ├── api/            # Route handlers
│   ├── models.py       # DB models
│   └── alembic/        # Migrations
└── frontend/
    ├── src/
    │   ├── screens/    # Main pages
    │   ├── components/ # Reusable UI
    │   └── api/        # API client
    └── package.json

generated_app/          # Agent outputs
```

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Backend Logs**: Terminal running `python main.py`
- **Frontend Logs**: Browser DevTools console
- **Database**: `sqlite3 database/orchestrator.db`
- **Issues**: GitHub Issues

---

**Made with ❤️ using Claude AI**
