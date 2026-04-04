#!/bin/bash
# Startup script for Orchestrator UI backend

echo "🚀 Starting Orchestrator UI Backend..."

# Initialize database if not exists
if [ ! -f "../../database/orchestrator.db" ]; then
    echo "📦 Initializing database..."
    python init_db.py
fi

# Start FastAPI server
echo "Starting FastAPI server on http://localhost:8000"
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../.."
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
