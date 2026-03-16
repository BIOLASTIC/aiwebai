#!/bin/bash

# Development restart script for Gemini Unified Gateway
# This script will restart both frontend and backend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running in a terminal
check_terminal() {
    if [ -t 1 ]; then
        return 0
    else
        return 1
    fi
}

# Stop existing processes
stop_processes() {
    log_info "Stopping existing processes..."

    # Stop backend (if using systemd)
    if pgrep -f "uvicorn.*backend.app.main:app" > /dev/null 2>&1; then
        log_info "Stopping backend..."
        pkill -f "uvicorn.*backend.app.main:app"
        sleep 2
        if pgrep -f "uvicorn.*backend.app.main:app" > /dev/null 2>&1; then
            log_warning "Backend is still running, force killing..."
            pkill -9 -f "uvicorn.*backend.app.main:app"
            sleep 1
        fi
        log_success "Backend stopped"
    fi

    # Stop frontend (if using pm2)
    if command -v pm2 &> /dev/null; then
        if pm2 list | grep -q "gemini-frontend"; then
            log_info "Stopping frontend..."
            pm2 stop gemini-frontend
            sleep 2
            log_success "Frontend stopped"
        fi
    else
        # Try to stop with pkill
        if pgrep -f "vite.*6401" > /dev/null 2>&1; then
            log_info "Stopping frontend..."
            pkill -f "vite.*6401"
            sleep 2
        fi
    fi

    log_success "All processes stopped"
}

# Start backend
start_backend() {
    log_info "Starting backend..."

    cd "$PROJECT_ROOT"

    # Set up environment
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    # Start backend in background
    .venv/bin/python -m uvicorn backend.app.main:app \
        --host 0.0.0.0 \
        --port 6400 \
        --log-level info \
        > "$LOG_DIR/backend.log" 2>&1 &

    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid

    log_success "Backend started (PID: $BACKEND_PID)"

    # Wait for backend to be ready
    log_info "Waiting for backend to be ready..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:6400/docs > /dev/null 2>&1; then
            log_success "Backend is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    log_error "Backend failed to start after $max_attempts attempts"
    return 1
}

# Start frontend
start_frontend() {
    log_info "Starting frontend..."

    cd "$PROJECT_ROOT/frontend"

    # Set up environment
    export NODE_ENV=development

    # Start frontend in background
    if command -v pm2 &> /dev/null; then
        pm2 start npm --name "gemini-frontend" -- start
    else
        # Without pm2, just start it
        npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
        echo $! > ../.frontend.pid
        log_info "Frontend started in background (PID: $!)"
    fi

    log_success "Frontend started"

    # Wait for frontend to be ready
    log_info "Waiting for frontend to be ready..."
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:6401 > /dev/null 2>&1; then
            log_success "Frontend is ready!"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done

    log_error "Frontend failed to start after $max_attempts attempts"
    return 1
}

# Main restart logic
main() {
    log_info "========================================="
    log_info "Gemini Unified Gateway - Restart"
    log_info "========================================="
    log_info ""

    # Parse command line arguments
    RESTART_BACKEND=true
    RESTART_FRONTEND=true

    if [ "$1" == "--frontend-only" ]; then
        RESTART_BACKEND=false
    elif [ "$1" == "--backend-only" ]; then
        RESTART_FRONTEND=false
    fi

    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"

    # Stop processes
    stop_processes

    sleep 2

    # Start processes
    if [ "$RESTART_BACKEND" = true ]; then
        start_backend || {
            log_error "Failed to start backend"
            exit 1
        }
    fi

    if [ "$RESTART_FRONTEND" = true ]; then
        start_frontend || {
            log_error "Failed to start frontend"
            exit 1
        }
    fi

    echo ""
    log_success "========================================="
    log_success "System Restart Complete!"
    log_success "========================================="
    echo ""
    log_info "Services:"
    if [ "$RESTART_BACKEND" = true ]; then
        BACKEND_PID=$(cat .backend.pid 2>/dev/null || echo "Not found")
        log_info "  Backend: http://0.0.0.0:6400 (PID: $BACKEND_PID)"
    fi
    if [ "$RESTART_FRONTEND" = true ]; then
        FRONTEND_PID=$(cat .frontend.pid 2>/dev/null || echo "Not found")
        log_info "  Frontend: http://0.0.0.0:6401 (PID: $FRONTEND_PID)"
    fi
    echo ""
    log_info "Access points:"
    log_info "  Admin Panel: http://0.0.0.0:6401"
    log_info "  API Docs: http://0.0.0.0:6400/docs"
    log_info "  API Base: http://0.0.0.0:6400"
    echo ""
    log_success "System is ready!"
}

# Run main function
main "$@"
