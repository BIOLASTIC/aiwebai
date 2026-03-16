#!/bin/bash
set -e

# Base directory
BASE_DIR=$(pwd)
export PYTHONPATH=$PYTHONPATH:$BASE_DIR

# Check for venv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e "backend/.[dev]"
pip install bcrypt==4.0.1 # Ensure compatible bcrypt version

# Database migrations
echo "Running migrations..."
cd backend && alembic upgrade head && cd ..

# Create admin user if not exists
echo "Seeding database..."
python backend/app/db/seed.py

# Start services
echo "Starting services..."
mkdir -p logs

# 1. FastAPI backend
echo "Starting Backend on http://0.0.0.0:6400"
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 6400 --reload > logs/api.log 2>&1 &
echo $! >> .dev.pids

# 2. Vite frontend
echo "Starting Frontend on http://0.0.0.0:6401"
# We assume npm install was run
cd frontend && npm run dev -- --host 0.0.0.0 --port 6401 > ../logs/frontend.log 2>&1 &
echo $! >> ../.dev.pids
cd ..

# 3. MCP server (if needed separate from main API)
# python -m backend.app.api.mcp.server > logs/mcp.log 2>&1 &
# echo $! >> .dev.pids

echo "Gemini Unified Gateway started!"
echo "API: http://0.0.0.0:6400"
echo "Frontend: http://0.0.0.0:6401"
echo "Swagger: http://0.0.0.0:6400/docs"
