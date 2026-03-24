#!/bin/bash
# Gemini Unified Gateway - Production/Development Mode Toggle Script
# Usage: ./scripts/prod-toggle.sh [dev|prod]

set -e

# Base directory
BASE_DIR=$(pwd)
export PYTHONPATH=$PYTHONPATH:$BASE_DIR

# Log directory
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

echo "================================================"
echo "Gemini Unified Gateway - Mode Toggle Script"
echo "================================================"

# Function to stop development processes
stop_dev() {
    echo "Stopping development processes..."
    if [ -f ".worktrees/generations-2.0/scripts/dev-stop.sh" ]; then
        bash .worktrees/generations-2.0/scripts/dev-stop.sh
    else
        # Fallback: stop processes using .dev.pids
        if [ -f ".dev.pids" ]; then
            while read pid; do
                echo "Stopping process $pid..."
                kill $pid || true
            done < .dev.pids
            rm .dev.pids
        fi
    fi
    
    # Stop any Vite dev servers that might be running
    pkill -f "vite" || true
    pkill -f "npm run dev" || true
    
    echo "Development processes stopped."
}

# Function to stop production processes
stop_prod() {
    echo "Stopping production processes..."
    if command -v pm2 &> /dev/null; then
        pm2 stop all || true
        pm2 delete all || true
    else
        echo "PM2 not found, skipping production process stop"
    fi
    
    echo "Production processes stopped."
}

# Function to start development mode
start_dev() {
    echo "Starting development mode..."
    
    # Ensure we're in the project root
    cd "$BASE_DIR"
    
    # Start development services
    DEV_START_SCRIPT="$BASE_DIR/.worktrees/generations-2.0/scripts/dev-start.sh"
    if [ -f "$DEV_START_SCRIPT" ]; then
        echo "Running development start script..."
        bash "$DEV_START_SCRIPT"
    else
        echo "ERROR: dev-start.sh not found at $DEV_START_SCRIPT!"
        exit 1
    fi
    
    echo "Development mode started."
    echo "Frontend: http://0.0.0.0:6401"
    echo "Backend API: http://0.0.0.0:6400"
    echo "Swagger Docs: http://0.0.0.0:6400/docs"
}

# Function to start production mode
start_prod() {
    echo "Starting production mode..."
    
    # Ensure we're in the project root
    cd "$BASE_DIR"
    
    # Start production services using PM2
    if [ -f "ecosystem.config.js" ]; then
        echo "Starting services with PM2..."
        pm2 start ecosystem.config.js --env production
        
        # Save the process list for startup
        pm2 save
        
        # Setup PM2 to start on boot (if not already setup)
        pm2 startup | grep -v "sudo" | tail -n 1
    else
        echo "ERROR: ecosystem.config.js not found!"
        exit 1
    fi
    
    echo "Production mode started."
    echo("Frontend: http://0.0.0.0:6401")
    echo("Backend API: http://0.0.0.0:6400")
    echo("Swagger Docs: http://0.0.0.0:6400/docs")
    
    # Check if Cloudflare tunnels are running and start them if needed
    if [ -f "scripts/cloudflared-backend.yml" ] || [ -f "scripts/cloudflared-frontend.yml" ]; then
        echo "Checking Cloudflare tunnels..."
        # Start Cloudflare tunnels if they exist
        if [ -f "scripts/cloudflared-backend.yml" ] && ! pgrep -f "cloudflared.*backend" > /dev/null; then
            echo "Starting backend Cloudflare tunnel..."
            cloudflared tunnel --config scripts/cloudflared-backend.yml run &
        fi
        
        if [ -f "scripts/cloudflared-frontend.yml" ] && ! pgrep -f "cloudflared.*frontend" > /dev/null; then
            echo "Starting frontend Cloudflare tunnel..."
            cloudflared tunnel --config scripts/cloudflared-frontend.yml run &
        fi
    else
        echo "Note: Cloudflare tunnel configs not found. Skipping tunnel startup."
    fi
}

# Main script logic
if [ "$1" = "dev" ]; then
    echo "Switching to DEVELOPMENT mode..."
    stop_prod
    stop_dev  # Ensure clean state
    start_dev
elif [ "$1" = "prod" ]; then
    echo "Switching to PRODUCTION mode..."
    stop_dev
    stop_prod  # Ensure clean state
    start_prod
else
    # Toggle mode based on current state
    echo "Checking current state..."
    
    # Check if PM2 processes are running (production)
    if command -v pm2 &> /dev/null && pm2 list | grep -E "(gemini-backend|gemini-frontend)" > /dev/null; then
        echo "Production mode detected. Switching to DEVELOPMENT..."
        stop_prod
        stop_dev  # Ensure clean state
        start_dev
    else
        # Check if dev processes are running
        if [ -f ".dev.pids" ] && [ -s ".dev.pids" ]; then
            echo "Development mode detected. Switching to PRODUCTION..."
            stop_dev
            stop_prod  # Ensure clean state
            start_prod
        else
            # No clear state, default to development
            echo "No clear mode detected. Defaulting to DEVELOPMENT..."
            stop_dev
            stop_prod  # Ensure clean state
            start_dev
        fi
    fi
fi

echo "================================================"
echo "Mode switch completed successfully!"
echo "================================================"