# Migration Guide: Orchestrator UI v2

## Backward Compatibility

✓ Fully backward compatible with existing .env configuration
✓ Existing projects continue to work
✓ No breaking changes to API

## For Existing Users

### Option 1: Use Existing .env (No Changes)
```bash
# Keep your .env as is
ADESSO_BASE_URL=...
ADESSO_AI_HUB_KEY=...

# Still works! Config loader falls back to .env
```

### Option 2: Migrate to Database Config (Recommended)

1. Start backend with existing .env
2. Open http://localhost:5173
3. Click "Connect GitHub"
4. Go to AI Provider Setup
5. Copy your ADESSO_BASE_URL and ADESSO_AI_HUB_KEY
6. Paste into the UI
7. Click "Test Connection" → "Save"
8. Done! Config now in database

### Remove .env (Optional)

Once all users migrated to database:
```bash
# Remove or clear ADESSO_* variables
# Keep JWT_SECRET, ENCRYPTION_KEY, OAuth variables
```

## Upgrading

### 1. Pull latest code
```bash
git pull origin main
```

### 2. Backend
```bash
cd orchestrator-ui/backend
pip install -r requirements.txt
# Database tables auto-created by init_db()
python -m uvicorn main:app --reload
```

### 3. Frontend
```bash
cd orchestrator-ui/frontend
npm install
npm run dev
```

## OAuth Setup (New)

### GitHub
1. https://github.com/settings/developers
2. New OAuth App
3. Authorization callback: http://localhost:5173/auth/callback
4. Copy Client ID/Secret to .env

### Vercel (Optional)
1. https://vercel.com/integrations
2. Create Integration
3. Copy to .env

### Railway (Optional)
1. Railway Dashboard
2. OAuth settings
3. Copy to .env

## Troubleshooting

**Error: "AI provider not configured"**
- Go to AI Provider Setup screen
- Enter Base URL and API Key
- Save

**Error: "GitHub not connected"**
- Click "Connect GitHub" on auth screen
- Authorize app

**Database locked**
- Kill all Python processes
- Restart backend

**Port in use**
- Change port in main.py line ~110
- Update FRONTEND_URL in frontend if needed
