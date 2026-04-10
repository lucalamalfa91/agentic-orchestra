#!/bin/bash
# Bash script to start Agentic Orchestra frontend
# Run from project root: bash start-frontend.sh

echo "🎨 Starting Agentic Orchestra Frontend..."
echo ""

# Check if in project root
if [ ! -f "CLAUDE.md" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: Not in project root!"
    echo "   Please navigate to agentic-orchestra/ first"
    echo "   Example: cd ~/PycharmProjects/agentic-orchestra"
    exit 1
fi

echo "✓ In project root: $(pwd)"

# Check if node_modules exists
if [ ! -d "orchestrator-ui/frontend/node_modules" ]; then
    echo "⚠️  node_modules not found, installing dependencies..."
    cd orchestrator-ui/frontend
    npm install
    cd ../..
    echo "✓ Dependencies installed"
fi

# Navigate to frontend directory
cd orchestrator-ui/frontend
echo "✓ Changed to frontend directory"
echo ""

# Start frontend
echo "Starting Vite dev server..."
echo "Press Ctrl+C to stop"
echo ""

npm run dev
