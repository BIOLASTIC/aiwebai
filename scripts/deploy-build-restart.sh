#!/bin/bash
set -e

# Gemini Unified Gateway — Production Build & Restart Script
# Usage: ./scripts/deploy-build-restart.sh

echo ">>> Starting Production Build & Restart Process..."

# 1. Ensure we are in the project root
BASE_DIR=$(pwd)
export PYTHONPATH=$PYTHONPATH:$BASE_DIR

# 2. Setup/Update Python Virtual Environment
if [ ! -d ".venv" ]; then
    echo ">>> Creating production virtual environment..."
    python3.11 -m venv .venv
fi

echo ">>> Activating virtual environment..."
source .venv/bin/activate

# 3. Install/Update Dependencies
echo ">>> Installing/Updating production dependencies..."
pip install --upgrade pip
pip install -e "backend/."
pip install bcrypt==4.0.1 # Ensure compatibility

# 4. Database Migrations
echo ">>> Running database migrations..."
cd backend && alembic upgrade head && cd ..

# 5. Build Frontend (if node/npm is available)
if command -v npm &> /dev/null; then
    echo ">>> Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
else
    echo ">>> WARNING: npm not found. Skipping frontend build."
fi

# 6. Restart Services
echo ">>> Restarting services..."

# If using dev-stop.sh to clear existing processes
if [ -f "scripts/dev-stop.sh" ]; then
    bash scripts/dev-stop.sh
fi

# Ensure log directory exists
mkdir -p logs

# Start Backend in background (Production mode)
echo ">>> Starting Backend (Gunicorn/Uvicorn)..."
# In a real production environment, you might use systemd or supervisor
# For this script, we'll use a background process recorded in .dev.pids
gunicorn backend.app.main:app 
    --workers 4 
    --worker-class uvicorn.workers.UvicornWorker 
    --bind 0.0.0.0:6400 
    --daemon 
    --access-logfile logs/gunicorn-access.log 
    --error-logfile logs/gunicorn-error.log 
    --pid logs/gunicorn.pid

# We'll store the pid from the pidfile into our .dev.pids for dev-stop.sh compatibility
sleep 2
if [ -f "logs/gunicorn.pid" ]; then
    cat logs/gunicorn.pid >> .dev.pids
fi

# Frontend is usually served by Nginx in production, but for this script
# we can start a simple server if needed or assume it's built and ready.
echo ">>> Frontend build complete in frontend/dist"

echo ">>> Deployment and restart complete!"
echo ">>> Backend running on http://0.0.0.0:6400"
