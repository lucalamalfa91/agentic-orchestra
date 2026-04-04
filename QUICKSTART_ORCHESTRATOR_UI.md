# Orchestrator UI - Quick Start Guide

This guide gets you up and running with the Orchestrator UI in 5 minutes.

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 18+ installed
- [ ] `.env` file configured (see below)

## Step 1: Configure Environment (1 minute)

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials
nano .env
```

**Required in `.env`:**
```bash
ADESSO_AI_HUB_KEY=your-actual-api-key
ADESSO_BASE_URL=https://adesso-ai-hub.3asabc.de/v1
GITHUB_TOKEN=your-github-token
```

**How to get credentials:**
- **Adesso AI Hub Key**: Contact your Adesso administrator
- **GitHub Token**: https://github.com/settings/tokens → Generate new token → Select `repo` scope

## Step 2: Install Dependencies (2 minutes)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd orchestrator-ui/frontend
npm install
cd ../..
```

## Step 3: Initialize Database (10 seconds)

```bash
cd orchestrator-ui/backend
python init_db.py
```

You should see:
```
Initializing database...
Database initialized successfully!
```

## Step 4: Start Backend (1 minute)

**Terminal 1:**
```bash
cd orchestrator-ui/backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Verify backend**: Open http://localhost:8000/docs (should show Swagger UI)

## Step 5: Start Frontend (1 minute)

**Terminal 2:**
```bash
cd orchestrator-ui/frontend
npm run dev
```

Wait for:
```
  ➜  Local:   http://localhost:5173/
```

**Open browser**: http://localhost:5173

## Step 6: Generate Your First App (5 minutes)

1. **Fill the form:**
   - **MVP Description**: "Weather app showing 7-day forecast for Como, Italy"
   - **Features** (one per line):
     ```
     Display current temperature
     Show 7-day forecast
     Show precipitation and wind speed
     ```
   - **Tech Stack**:
     - Frontend: React
     - Backend: none
     - Database: none
     - Deploy: github-pages

2. **Click "Generate App"**

3. **Watch progress:**
   - ✅ README Update (16%)
   - ✅ Design Phase (33%)
   - ✅ Backend Code (50%)
   - ✅ Frontend Code (67%)
   - ✅ CI/CD Pipeline (83%)
   - ✅ GitHub Publish (100%)

4. **Result:**
   - Green success banner appears
   - Project shows in "Project History" section
   - Click "View on GitHub" to see your new repository

## Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.9+

# Verify dependencies
pip list | grep fastapi

# Check .env file exists
ls -la .env
```

### Frontend won't start
```bash
# Check Node version
node --version  # Should be 18+

# Clear cache and reinstall
cd orchestrator-ui/frontend
rm -rf node_modules package-lock.json
npm install
```

### Database error
```bash
# Verify database exists
ls -lh database/orchestrator.db

# Reinitialize if needed
cd orchestrator-ui/backend
rm -f ../../database/orchestrator.db
python init_db.py
```

### Generation fails
```bash
# Check backend logs in Terminal 1
# Common issues:
# - Missing ADESSO_AI_HUB_KEY
# - GitHub token not configured
# - `gh` CLI not authenticated

# Test GitHub CLI
gh auth status

# If not authenticated:
gh auth login
```

## What's Next?

- **Edit a project**: Click "Edit" on any project in history to modify and regenerate
- **View API docs**: http://localhost:8000/docs
- **Customize tech stack**: Try different combinations (React + .NET + PostgreSQL + Railway)
- **Read full docs**: See `orchestrator-ui/README.md`

## Common Use Cases

### Static Website (FREE)
```
Frontend: React
Backend: none
Database: none
Deploy: github-pages
```

### Fullstack App with Database
```
Frontend: React
Backend: dotnet
Database: postgresql
Deploy: railway
```

### Serverless App
```
Frontend: React
Backend: node
Database: none
Deploy: vercel
```

## Getting Help

- **Backend logs**: Check Terminal 1 for FastAPI logs
- **Frontend logs**: Check browser DevTools console
- **Database**: `sqlite3 database/orchestrator.db` to inspect directly
- **Full documentation**: `orchestrator-ui/README.md`
- **Main README**: `README.md` for AI Factory overview

---

**Happy generating! 🎉**
