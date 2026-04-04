# Agentic Orchestra - Setup Guide

## Prerequisites
- Node.js 18+
- Python 3.10+
- Git

## Backend Setup

### 1. Environment Variables
```bash
cp .env.example .env
# Edit .env con tuoi valori
```

### 2. GitHub OAuth App
1. Vai a https://github.com/settings/developers
2. New OAuth App
3. Authorization callback URL: `http://localhost:5173/auth/callback`
4. Copia Client ID e Secret in .env

### 3. AI Provider
Scegli uno:
- **OpenAI**: Base URL `https://api.openai.com/v1`, API Key da OpenAI
- **Adesso**: Base URL dal tuo hub, API Key
- Altro provider compatibile OpenAI

### 4. Start Backend
```bash
cd orchestrator-ui/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Frontend Setup

### 1. Install
```bash
cd orchestrator-ui/frontend
npm install
```

### 2. Start
```bash
npm run dev
```

## First Run

1. Apri http://localhost:5173
2. Click "Connect GitHub"
3. Autorizza su GitHub
4. Setup AI Provider (Base URL + API Key)
5. Scrivi prompt app
6. Generate!

## Troubleshooting

**Port in use**:
- Backend: cambia port in main.py
- Frontend: vite usa porta diversa automaticamente

**GitHub OAuth error**:
- Verifica Client ID/Secret in .env
- Callback URL deve matchare

**AI Provider error**:
- Testa connessione nel form
- Verifica API Key valida
