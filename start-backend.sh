#!/bin/bash
# Bash script to start Agentic Orchestra backend
# Run from project root: bash start-backend.sh

echo "🚀 Starting Agentic Orchestra Backend..."
echo ""

# Check if in project root
if [ ! -f "CLAUDE.md" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: Not in project root!"
    echo "   Please navigate to agentic-orchestra/ first"
    echo "   Example: cd ~/PycharmProjects/agentic-orchestra"
    exit 1
fi

echo "✓ In project root: $(pwd)"

# Set PYTHONPATH to project root (Windows path format for Git Bash)
export PYTHONPATH="$(pwd -W 2>/dev/null || pwd)"
echo "✓ PYTHONPATH set to: $PYTHONPATH"

# Add GitHub CLI to PATH (if not already there)
GH_CLI_PATH="/c/Program Files/GitHub CLI"
if [ -d "$GH_CLI_PATH" ] && [[ ":$PATH:" != *":$GH_CLI_PATH:"* ]]; then
    export PATH="$GH_CLI_PATH:$PATH"
    echo "✓ Added GitHub CLI to PATH"
fi

# Navigate to backend directory
cd orchestrator-ui/backend
echo "✓ Changed to backend directory"
echo ""

# Start backend
echo "Starting FastAPI server..."
echo "Press Ctrl+C to stop"
echo ""

python main.py
