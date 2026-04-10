# Agentic Orchestra

AI-powered system that transforms text requirements into complete applications through orchestrated AI agents.

## Quick Start

### Prerequisites
- Node.js 18+ | Python 3.10+ | Git

### Setup

```bash
# 1. Environment
cp .env.example .env
# Edit .env: add GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, AI_BASE_URL, AI_API_KEY

# 2. Install
pip install -r requirements.txt
cd orchestrator-ui/frontend && npm install && cd ../..

# 3. Database
cd orchestrator-ui/backend && python init_db.py && cd ../..

# 4. Backend (Terminal 1)
cd orchestrator-ui/backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
python main.py

# 5. Frontend (Terminal 2)
cd orchestrator-ui/frontend
npm run dev

# 6. Open http://localhost:5173
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

---

## What It Does

Specialized AI agents collaborate to generate complete applications:

1. **Architect Agent** → Design, architecture, database schema
2. **Backend Agent** → .NET API, models, services
3. **Frontend Agent** → React components, routing, state
4. **DevOps Agent** → GitHub Actions, deployment config
5. **Backlog Agent** → Azure DevOps work items

Each agent's output feeds the next, creating a full pipeline from requirements to deployment.

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

**Port 8000 locked**
```bash
# Option 1: Kill process
lsof -ti:8000 | xargs kill -9

# Option 2: Use different port (Windows TIME_WAIT workaround)
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
pkill -f python
cd orchestrator-ui/backend
rm -f ../../database/orchestrator.db
python init_db.py
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

```
User Input → Architect → Backend Agent → Frontend Agent → DevOps Agent → Backlog Agent → GitHub Repo
              (design)    (.NET code)    (React code)    (CI/CD)         (tasks)
```

**Frontend Flow**
```
AuthScreen → AIProviderSetup → MVPCreationScreen → ConfirmationScreen → DeployAuth → Progress → Success
```

**Database**: SQLite (local), PostgreSQL (production)
**Auth**: GitHub OAuth → JWT (24h)
**WebSocket**: Real-time generation progress
**Encryption**: Fernet (API keys)

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
