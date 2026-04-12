# Agentic Orchestra

AI-powered system that transforms text requirements into complete applications through orchestrated AI agents.

## Quick Start

### Prerequisites
- Node.js 18+ | Python 3.10+ | Git

### Setup

⚠️ **IMPORTANT**: Use **Git Bash** and run all commands from the **project root** (`agentic-orchestra/`).

```bash
# 1. Navigate to project root
cd ~/PycharmProjects/agentic-orchestra

# 2. Check setup (optional)
bash check_setup.sh

# 3. Setup environment (first time only)
cp .env.example .env
# Edit .env with GitHub OAuth credentials (GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET)
# Note: AI provider (API key) is configured later from the UI Settings screen

# 4. Install dependencies (first time only)
pip install -r requirements.txt
cd orchestrator-ui/frontend && npm install && cd ../..

# 5. Start Backend (Terminal 1)
bash start-backend.sh

# 6. Start Frontend (Terminal 2 - NEW terminal!)
bash start-frontend.sh

# 7. Open http://localhost:5173
```

### GitHub OAuth Setup

1. Go to https://github.com/settings/developers
2. Create OAuth App with callback: `http://localhost:5173/auth/callback`
3. Copy Client ID/Secret to `.env`

### First Generation

1. Connect GitHub account (GitHub OAuth)
2. **Configure AI Provider** in Settings:
   - Click Settings icon
   - Enter Base URL (e.g., `https://api.anthropic.com` for Claude)
   - Enter API Key
   - Click Save (key is encrypted and stored securely)
3. Enter app description: "Weather app with 7-day forecast"
4. Click Generate → Watch progress → View repo on GitHub

**Resume failed generations**: Project History → Click "▶ Resume Generation"


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
# Required (in .env file)
GITHUB_CLIENT_ID=...           # GitHub OAuth App credentials
GITHUB_CLIENT_SECRET=...
JWT_SECRET=your-secret-min-32-chars  # For JWT token signing

# Optional (for deployment features)
VERCEL_CLIENT_ID=...
VERCEL_CLIENT_SECRET=...
RAILWAY_CLIENT_ID=...
RAILWAY_CLIENT_SECRET=...
```

**Note**:
- **AI Provider** (Base URL + API Key) is configured from UI Settings, not .env
- **ENCRYPTION_KEY** is auto-generated at first startup and saved in `database/encryption.key` (not in .env)

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

Solution: Use the startup scripts instead of manual commands:

```bash
cd ~/PycharmProjects/agentic-orchestra
bash start-backend.sh
```

The script handles PYTHONPATH automatically.

**Port 8000 locked**
```bash
# Git Bash: Kill process on port 8000
netstat -ano | grep :8000 | awk '{print $5}' | xargs taskkill //F //PID

# Or just use a different port
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
# Kill all Python processes
taskkill //F //IM python.exe

# Remove database
rm -f database/orchestrator.db

# Restart backend (database auto-initializes on startup)
bash start-backend.sh
```

---

## Security

- **API Keys**: Encrypted with Fernet and stored in database
  - Encryption key auto-generated in `database/encryption.key` (persistent, not in git)
  - Keys encrypted at rest, decrypted only when needed for generation
- **JWT**: HS256, 24h expiration (JWT_SECRET in .env)
- **CORS**: Configure `allow_origins` for production (currently allows all for dev)
- **Generated Code**: Always review for vulnerabilities before deployment

**Pre-Production Checklist**
- [ ] Strong JWT_SECRET (32+ random chars, in .env)
- [ ] Backup `database/encryption.key` securely (required to decrypt API keys)
- [ ] CORS restricted to production domain
- [ ] HTTPS enabled
- [ ] Security audit on generated code
- [ ] Rate limiting enabled
- [ ] Move database to PostgreSQL with encrypted connections

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
