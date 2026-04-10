#!/bin/bash
# Quick setup verification script for Agentic Orchestra
# Run from project root: bash check_setup.sh

set -e

echo "🔍 Checking Agentic Orchestra Setup..."
echo ""

# Check if in project root
if [ ! -f "CLAUDE.md" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: Not in project root!"
    echo "   Please run from: agentic-orchestra/"
    echo "   Current dir: $(pwd)"
    exit 1
fi
echo "✓ In project root"

# Check .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: .env not found"
    echo "   Run: cp .env.example .env"
    echo "   Then edit .env with your credentials"
else
    echo "✓ .env exists"
fi

# Check Python dependencies
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  WARNING: Python dependencies not installed"
    echo "   Run: pip install -r requirements.txt"
else
    echo "✓ Python dependencies installed"
fi

# Check frontend dependencies
if [ ! -d "orchestrator-ui/frontend/node_modules" ]; then
    echo "⚠️  WARNING: Frontend dependencies not installed"
    echo "   Run: cd orchestrator-ui/frontend && npm install"
else
    echo "✓ Frontend dependencies installed"
fi

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is running (port 8000)"
else
    echo "⚠️  Backend not running"
    echo "   Start with: cd orchestrator-ui/backend && export PYTHONPATH=\"\$(cd ../.. && pwd -W)\" && python main.py"
fi

# Check if frontend is running
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✓ Frontend is running (port 5173)"
else
    echo "⚠️  Frontend not running"
    echo "   Start with: cd orchestrator-ui/frontend && npm run dev"
fi

# Check database
if [ -f "database/orchestrator.db" ]; then
    echo "✓ Database exists"
else
    echo "⚠️  Database not initialized (will auto-create on first backend start)"
fi

echo ""
echo "🎯 Setup check complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env if not done yet"
echo "2. Terminal 1: cd orchestrator-ui/backend && export PYTHONPATH=\"\$(cd ../.. && pwd -W)\" && python main.py"
echo "3. Terminal 2: cd orchestrator-ui/frontend && npm run dev"
echo "4. Open: http://localhost:5173"
