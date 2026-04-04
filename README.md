# Agentic Orchestra - AI-Powered Application Factory

A revolutionary system that automates the entire software development lifecycle, transforming text requirements into complete, production-ready applications through orchestrated AI agents.

## Table of Contents

- [Quick Start](#quick-start)
- [Using requirements.txt](#using-requirementstxt)
- [Concept & Vision](#concept--vision)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Setup Guide](#setup-guide)
- [API Documentation](#api-documentation)
- [Security](#security)
- [Limitations & Considerations](#limitations--considerations)
- [Possible Extensions](#possible-extensions)

---

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.10+
- Git

### 5-Minute Setup

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies
pip install -r requirements.txt
cd orchestrator-ui/frontend && npm install && cd ../..

# 3. Initialize database
cd orchestrator-ui/backend && python init_db.py

# 4. Start backend (Terminal 1)
cd orchestrator-ui/backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. Start frontend (Terminal 2)
cd orchestrator-ui/frontend
npm run dev

# 6. Open browser
# Frontend: http://localhost:5173
# Backend Docs: http://localhost:8000/docs
```

### First Generation

1. Click "Connect GitHub" and authorize
2. Configure AI Provider (Base URL + API Key)
3. Enter prompt: "Weather app showing 7-day forecast"
4. Select tech stack (React, dotnet, postgresql, railway)
5. Watch the generation progress
6. View your new repository on GitHub

---

## Using requirements.txt

The `requirements.txt` file is your **input template** for generating applications. It describes what you want to build.

### Format

```
Your MVP description goes here.

Write a clear, detailed description of the application you want to generate.

Example:
A weather app that shows the 7-day forecast for any city. Users can search by city name,
see current temperature, precipitation chance, wind speed, and hourly breakdown.

Features:
- Search by city name
- Display current temperature and conditions
- Show 7-day forecast with daily high/low
- Display precipitation and wind speed
- Hourly breakdown for today
- Responsive design for mobile

Technical:
- Frontend: React
- Backend: dotnet
- Database: postgresql
- Deploy to: railway
```

### How to Use

**Option 1: Via UI (Recommended)**
1. Start the application with the steps above
2. Fill in the form with your app description
3. Click "Generate App"

**Option 2: Manual CLI Mode (Future)**
1. Edit `requirements.txt` with your app description
2. Run `python run_all_agents.py`
3. Generated app appears in `generated_app/` folder

### Key Sections

- **MVP Description:** Clear overview of what the app does
- **Features:** Specific, measurable features (one per line)
- **Technical Stack:**
  - **Frontend:** react, vue, angular, or none
  - **Backend:** dotnet, node, python, or none
  - **Database:** postgresql, mysql, mongodb, or none
  - **Deploy to:** railway, vercel, github-pages, render, azure-free

### Example Applications

**Weather App (Free)**
```
Frontend: React
Backend: none
Database: none
Deploy to: github-pages
```

**Full-Stack Todo App**
```
Frontend: React
Backend: dotnet
Database: postgresql
Deploy to: railway
```

**Serverless API**
```
Frontend: React
Backend: node
Database: none
Deploy to: vercel
```

---

## Concept & Vision

### The Problem

Transforming text requirements into production applications requires:
- Analysts writing specifications
- Architects designing infrastructure
- Backend/frontend developers writing code
- DevOps engineers configuring pipelines
- Project managers creating backlogs

This process is slow, expensive, and prone to communication errors.

### The Solution: AI Factory

An orchestrated system of specialized intelligent agents that collaborate to automate the entire lifecycle:

1. **Design Agent** → Architecture, documentation, design decisions
2. **Backend Agent** → API, database, business logic (.NET)
3. **Frontend Agent** → UI components, pages, API integration (React)
4. **DevOps Agent** → CI/CD pipelines, deployment configuration (GitHub Actions)
5. **Backlog Agent** → User stories, tasks, acceptance criteria (Azure DevOps)

Each agent's output feeds into the next, creating a complete value chain from conception to deployment.

### When to Use

**Ideal for:**
- Prototypes and MVPs
- Projects with clear requirements
- Small teams needing productivity amplification
- Standard CRUD applications (todo apps, CRMs, inventory management)
- Rapid iteration on evolving requirements
- Automatic documentation generation

**Not suitable for:**
- Highly specialized systems (proprietary algorithms, ML, real-time critical systems)
- Vague or evolving requirements
- Legacy code integration/refactoring
- Replacement for expert architects
- Production without human review

---

## Architecture

### Frontend Flow

```
App (Router + Contexts)
├── No Auth? → AuthScreen (GitHub login)
├── Auth OK, No AI Config? → AIProviderSetup
└── Both OK? → MVPCreationScreen
   ├── User enters prompt
   ├── User clicks Generate
   ├── WebSocket step 2 completes → ConfirmationScreen
   ├── User confirms
   ├── Check deploy provider needed
   │   ├── If yes → DeployAuthScreen (OAuth)
   │   └── If no → continue
   └── WebSocket steps 3-6 → Success
```

### Authentication System

**GitHub OAuth:**
```
User clicks login
  ↓
/api/auth/github/login
  ↓
User authorizes on GitHub
  ↓
/api/auth/github/callback?code=X
  ↓
Exchange code for JWT token
  ↓
Store in localStorage
```

**JWT Token:**
- Sent in `Authorization: Bearer` header
- Validated on protected endpoints
- 24-hour expiration
- HS256 algorithm with JWT_SECRET

### State Management

```
AuthContext
├── user (id, github_username)
├── token (JWT)
└── setToken, setUser

AIProviderContext
├── config (base_url, api_key_set)
└── setConfig

GenerationContext
├── currentScreen
├── design (from Design Agent)
├── deployProvider
└── startGeneration, confirmGeneration
```

### Database Schema

```
User
├── id (PK)
├── github_id (UNIQUE)
├── github_username
├── github_token
└── created_at

Configuration
├── id (PK)
├── user_id (FK)
├── ai_base_url
├── ai_api_key_encrypted (Fernet)
└── is_active

DeployProviderAuth
├── id (PK)
├── user_id (FK)
├── provider_name (vercel, railway)
├── access_token
├── refresh_token (optional)
└── expires_at (optional)

Project
├── id
├── name
├── description
├── github_repo_url
└── ...

ProjectRequirement
├── id
├── project_id
├── mvp_description
├── features
├── tech_stack (frontend, backend, db, deploy)
└── ...
```

### Design Agent Enhancement

The Design Agent analyzes requirements and auto-decides technology stack:

```yaml
decisions:
  tech_stack:
    frontend: "react"
    backend: "dotnet"
    database: "postgresql"
    deploy_platform: "railway"
  reasoning: "..."
```

**Priority for API Configuration:**
1. Database Configuration (if user configured via UI)
2. Environment variables (ADESSO_* or AI_*)
3. Default (fallback, may fail)

---

## Repository Structure

### Main Components

```
agentic-orchestra/
├── AI_agents/                    # Specialized agents
│   ├── design_agent.py          # Architecture & documentation
│   ├── backend_agent.py         # API, database, business logic
│   ├── frontend_agent.py        # React UI components
│   ├── devops_agent.py          # CI/CD, deployment
│   └── backlog_agent.py         # User stories & tasks
├── orchestrator-ui/
│   ├── frontend/                # React application
│   │   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── package.json
│   └── backend/                 # FastAPI server
│       ├── main.py              # API routes
│       ├── init_db.py           # Database initialization
│       ├── auth.py              # GitHub OAuth
│       ├── config.py            # Configuration management
│       └── requirements.txt
├── generated_app/               # Generated artifacts
│   ├── docs/                    # Design specifications
│   ├── backend/                 # Generated .NET code
│   ├── frontend/                # Generated React code
│   ├── devops/                  # GitHub Actions workflows
│   └── backlog/                 # Azure DevOps exports
├── run_all_agents.py            # Central orchestrator
└── README.md                    # This file
```

### Execution Flow

```
Phase 1: Input
  └─ User provides text requirement

Phase 2: Design Agent
  ├─ Analyzes requirement
  ├─ Identifies necessary components
  ├─ Defines architecture
  ├─ Chooses technologies
  └─ Produces design.yaml contract

Phase 3: Backend Agent
  ├─ Reads design contract
  ├─ Generates .NET code
  ├─ Creates data models
  ├─ Implements authentication
  └─ API routes consistent with design

Phase 4: Frontend Agent
  ├─ Reads design and API contract
  ├─ Generates React components
  ├─ Creates HTTP services
  ├─ Implements state management
  └─ Matches design specifications

Phase 5: DevOps Agent
  ├─ Creates build pipelines
  ├─ Configures GitHub Actions
  ├─ Creates Dockerfile
  └─ Generates deployment scripts

Phase 6: Backlog Agent
  ├─ Transforms design into user stories
  ├─ Creates technical tasks
  ├─ Defines acceptance criteria
  └─ Creates Azure DevOps work items

Phase 7: Output
  └─ All artifacts collected in generated_app/
```

---

## Setup Guide

### Environment Configuration

```bash
cp .env.example .env
nano .env
```

**Required Variables:**

```bash
# GitHub OAuth
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# AI Provider (choose one)
# Option 1: OpenAI
AI_BASE_URL=https://api.openai.com/v1
AI_API_KEY=sk-...

# Option 2: Adesso AI Hub
ADESSO_BASE_URL=https://adesso-ai-hub.3asabc.de/v1
ADESSO_AI_HUB_KEY=your-key

# Security
JWT_SECRET=your-secret-key-min-32-chars
ENCRYPTION_KEY=your-encryption-key

# Optional: Deploy Providers
VERCEL_CLIENT_ID=...
VERCEL_CLIENT_SECRET=...
RAILWAY_CLIENT_ID=...
RAILWAY_CLIENT_SECRET=...
```

### GitHub OAuth Setup

1. Go to https://github.com/settings/developers
2. Create New OAuth App
3. Set **Authorization callback URL** to `http://localhost:5173/auth/callback`
4. Copy **Client ID** and **Client Secret** to `.env`

### AI Provider Configuration

**Option 1: OpenAI**
- Base URL: `https://api.openai.com/v1`
- Get API Key from https://platform.openai.com/api-keys

**Option 2: Adesso AI Hub**
- Contact your Adesso administrator for Base URL and API Key
- Hub dashboard: https://adesso-ai-hub.3asabc.de

**Option 3: Compatible Provider**
- Any OpenAI-compatible API endpoint works
- Supports local Ollama, vLLM, or other compatible services

### Backend Setup

```bash
cd orchestrator-ui/backend
pip install -r requirements.txt
python init_db.py
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verify:** Open http://localhost:8000/docs → Swagger UI

### Frontend Setup

```bash
cd orchestrator-ui/frontend
npm install
npm run dev
```

**Open:** http://localhost:5173

### Troubleshooting

**Port already in use:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
# Or change port in main.py
```

**GitHub OAuth error:**
- Verify Client ID/Secret in .env
- Check callback URL matches: `http://localhost:5173/auth/callback`

**AI Provider error:**
- Test connection in UI
- Verify API Key is valid and has quota

**Database locked:**
```bash
# Kill all Python processes
pkill -f python
# Reinitialize
cd orchestrator-ui/backend
rm -f ../../database/orchestrator.db
python init_db.py
```

**Node dependencies error:**
```bash
cd orchestrator-ui/frontend
rm -rf node_modules package-lock.json
npm install
```

---

## API Documentation

### Authentication Endpoints

**GET** `/api/auth/github/login`
- Returns GitHub OAuth authorization URL
- Response: `{"url": "https://github.com/login/oauth/authorize?..."}`

**GET** `/api/auth/github/callback?code=X`
- Exchanges authorization code for JWT token
- Query params: `code` (from GitHub)
- Response: `{"token": "jwt_token", "user_id": 1}`

**GET** `/api/auth/github/status`
- Check GitHub connection status
- Response: `{"connected": true, "username": "octocat"}`

### AI Provider Configuration

**POST** `/api/config/ai-provider`
- Save AI provider configuration
- Headers: `Authorization: Bearer jwt_token`
- Body: `{"base_url": "https://...", "api_key": "sk-..."}`
- Response: `{"status": "saved"}`

**GET** `/api/config/ai-provider`
- Get AI provider config (API key not exposed)
- Response: `{"base_url": "https://..."}`

**POST** `/api/config/ai-provider/test`
- Test connection to AI provider
- Body: `{"base_url": "https://...", "api_key": "sk-..."}`
- Response: `{"success": true}`

### Generation Endpoints

**POST** `/api/generation/start`
- Start application generation
- Headers: `Authorization: Bearer jwt_token`
- Body:
  ```json
  {
    "mvp_description": "Weather app with 7-day forecast",
    "tech_stack": {
      "frontend": "react",
      "backend": "dotnet",
      "database": "postgresql",
      "deploy_platform": "railway"
    },
    "auto_decide": true
  }
  ```
- Response: `{"id": "gen_123", "websocket_url": "ws://..."}`

**WS** `/ws/generation/{generation_id}`
- WebSocket connection for real-time progress updates
- Messages: `{"step": 1, "status": "completed", "message": "..."}`

### Deploy Provider OAuth

**GET** `/api/auth/deploy/{provider}/login`
- Start OAuth flow for deploy provider (vercel, railway)
- Response: `{"url": "https://..."}`

**GET** `/api/auth/deploy/{provider}/callback?code=X`
- Exchange code for deploy provider access token
- Response: `{"status": "ok"}`

### Error Responses

All errors return:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

Common status codes:
- 400: Bad request
- 401: Unauthorized (missing/invalid token)
- 404: Not found
- 500: Server error

---

## Security

### Data Protection

- **GitHub Token:** Stored in database (GitHub manages revocation)
- **API Key:** Encrypted with Fernet algorithm (ENCRYPTION_KEY from .env)
- **JWT Token:** HS256 algorithm with 24-hour expiration (JWT_SECRET from .env)

### API Security

- **CORS:** Only configured frontend origins allowed
- **Authentication:** All sensitive endpoints require JWT in Authorization header
- **Rate Limiting:** Recommended to enable before production

### Pre-Deployment Checklist

- [ ] Change JWT_SECRET to strong random value
- [ ] Change ENCRYPTION_KEY to strong random value
- [ ] Enable CORS for production domain only
- [ ] Use HTTPS in production
- [ ] Run security audit on generated code
- [ ] Configure proper logging and monitoring
- [ ] Set up database backups
- [ ] Enable rate limiting on API endpoints

---

## Limitations & Considerations

### Important Disclaimers

**Human supervision required:** Generated code must be reviewed by experienced developers. Agents can make logical errors, generate inefficient code, or miss important details.

**Quality depends on input:** Vague or incomplete requirements produce vague or incomplete code. "Garbage in, garbage out" remains valid.

**Limited context:** Agents have no memory of past decisions or deep business context. Each generation is independent.

**Predefined technology stacks:** Factory generates code for specific stacks (.NET, React, GitHub Actions). Not easily adaptable to different stacks without modification.

**Incomplete testing:** Generated code has basic tests but doesn't cover all edge cases or complex scenarios.

**Security consideration:** Generated code follows common best practices but isn't immune to vulnerabilities. Human security audits are essential.

**Performance:** Generated code is functionally correct but not optimized. Profiling and manual optimization may be necessary.

### Recommendation

The AI Factory is an acceleration tool, not a replacement. Maximum value emerges when used as a starting point for a team of developers who refine, test, and evolve the generated code.

---

## Possible Extensions

The architecture supports adding new agents to the flow:

### Security Agent
- Analyzes design and generated code
- Identifies vulnerabilities
- Suggests security mitigations
- Generates security tests

### Test Agent
- Generates automated test suites
- Unit, integration, and e2e tests
- Coverage reports

### Documentation Agent
- Produces end-user documentation
- Installation guides
- API documentation
- Tutorials

### Performance Agent
- Analyzes design and code
- Identifies bottlenecks
- Suggests optimizations
- Generates load tests

### Compliance Agent
- Verifies GDPR compliance
- Checks HIPAA requirements
- Regulatory standard validation

### Adding a New Agent

1. Create a module in `AI_agents/` implementing standard interface
2. Define expected input and output schemas
3. Integrate into `run_all_agents.py` at appropriate logical point
4. Test consistency with adjacent agents
5. Document integration steps

---

## Migration Guide (v2)

### Backward Compatibility

✓ Fully backward compatible with existing `.env` configuration
✓ Existing projects continue to work
✓ No breaking changes to API

### For Existing Users

**Option 1: Keep Using .env (No Changes)**
```bash
# Your existing configuration still works
ADESSO_BASE_URL=...
ADESSO_AI_HUB_KEY=...
# Config loader automatically falls back to .env
```

**Option 2: Migrate to Database Config (Recommended)**
1. Start backend with existing .env
2. Open http://localhost:5173
3. Click "Connect GitHub"
4. Go to AI Provider Setup
5. Enter your Base URL and API Key
6. Click "Test Connection" → "Save"
7. Config now stored in encrypted database

### Upgrade Steps

```bash
# 1. Get latest code
git pull origin main

# 2. Backend
cd orchestrator-ui/backend
pip install -r requirements.txt
# Database tables auto-created
python -m uvicorn main:app --reload

# 3. Frontend
cd orchestrator-ui/frontend
npm install
npm run dev
```

---

## Support & Help

- **Backend API Docs:** http://localhost:8000/docs (Swagger UI)
- **Backend Logs:** Check Terminal 1 running uvicorn
- **Frontend Logs:** Check browser DevTools console
- **Database:** `sqlite3 database/orchestrator.db` for direct inspection
- **Issues:** Report at https://github.com/anthropics/claude-code/issues
- **Help with Claude Code:** Use `/help` command

---

**Made with ❤️ using Claude AI**
