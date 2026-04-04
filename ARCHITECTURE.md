# Architecture Overview

## Frontend Flow

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

## Backend Authentication

```
GitHub OAuth:
User clicks login → /api/auth/github/login →
  GitHub OAuth URL → User authorizes →
  /api/auth/github/callback?code=X →
  Exchange code for token → Save User → Create JWT → Return token

JWT Token:
- Stored in localStorage
- Sent in Authorization: Bearer header
- Validated on protected endpoints
- Expires after 24 hours
```

## State Management

```
AuthContext
├── user (id, github_username)
├── token (JWT)
└── setToken, setUser

AIProviderContext
├── config (base_url, api_key_set)
└── setConfig

GenerationContext (existing)
├── currentScreen
├── design (from Design Agent)
├── deployProvider
└── startGeneration, confirmGeneration
```

## Database Schema

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

Project (existing)
├── id
├── name
├── description
├── github_repo_url
└── ...

ProjectRequirement (existing)
├── id
├── project_id
├── mvp_description
├── features
├── tech_stack (frontend, backend, db, deploy)
└── ...
```

## Design Agent Enhancement

```
Input: requirements.txt (MVP description + optional tech stack)

If tech_stack is NOT specified OR auto_decide=true:
  → Analyze prompt
  → Decide: frontend, backend, database, deploy platform
  → Add decisions section to design.yaml

Output design.yaml:
```yaml
decisions:
  tech_stack:
    frontend: "react"
    backend: "dotnet"
    database: "postgresql"
    deploy_platform: "vercel"
  reasoning: "..."
```
```

## Security

- GitHub token: Stored in User table (plain, GitHub manages revocation)
- API Key: Encrypted with Fernet (ENCRYPTION_KEY in .env)
- JWT: HS256 with JWT_SECRET (24h expiration)
- CORS: Only frontend origins allowed
- Auth: All sensitive endpoints require JWT

## API Configuration Loading

Priority:
1. Database Configuration (if user configured via UI)
2. Environment variables (ADESSO_* or AI_* from .env)
3. Default (fallback, may fail)

Support for both old (ADESSO_) and new (AI_) variable names for backward compatibility.
