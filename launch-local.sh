#!/bin/bash
# DREAM.AI Local Launch (no Docker) - macOS/Linux
# Starts backend (Python) and frontend (npm) directly.

set -e
cd "$(dirname "$0")"

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:8080"
HEALTH_RETRIES=30
HEALTH_INTERVAL=2

# Load .env
[ -f .env ] && set -a && source .env && set +a

check_deps() {
    if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
        echo "Error: Python not found. Install Python 3.10+."
        exit 1
    fi
    PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)
    export PYTHON_CMD
    if ! command -v node &>/dev/null; then
        echo "Error: Node.js not found. Install Node.js 18+."
        exit 1
    fi
    if ! command -v npm &>/dev/null; then
        echo "Error: npm not found. Install Node.js (includes npm)."
        exit 1
    fi
}

check_ports() {
    if lsof -i :8000 &>/dev/null 2>&1; then
        echo "Error: Port 8000 is in use. Stop the process using it or run 'lsof -i :8000' to see what's using it."
        exit 1
    fi
    if lsof -i :8080 &>/dev/null 2>&1; then
        echo "Error: Port 8080 is in use. Stop the process using it."
        exit 1
    fi
}

wait_for_backend() {
    echo "Waiting for backend..."
    for i in $(seq 1 $HEALTH_RETRIES); do
        if curl -sf "$BACKEND_URL/health" &>/dev/null; then
            echo "Backend ready."
            return 0
        fi
        sleep $HEALTH_INTERVAL
    done
    echo "Error: Backend did not become ready."
    return 1
}

open_browser() {
    sleep 3
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$FRONTEND_URL"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$FRONTEND_URL" 2>/dev/null || true
    fi
}

cleanup() {
    trap - SIGINT SIGTERM EXIT 2>/dev/null
    echo ""
    echo "Stopping DREAM.AI..."
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# ----- Main -----
check_deps
check_ports

echo
echo "Starting DREAM.AI (local, no Docker)..."
echo "  Backend:  port 8000 (Python)"
echo "  Frontend: port 8080 (Vite)"
echo
echo "Prerequisites: pip install -r src/requirements.txt, cd src/frontend && npm install"
echo

# Backend - PYTHONPATH needs project root (for src.* imports) and src/ (for envs.*)
export PYTHONPATH="${PWD}:${PWD}/src"
cd src
$PYTHON_CMD -m backend.api.app &
BACKEND_PID=$!
cd ..

# Wait for backend before starting frontend
if ! wait_for_backend; then
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Frontend
cd src/frontend
npm run dev &
FRONTEND_PID=$!
cd ../..

trap cleanup SIGINT SIGTERM EXIT

echo
echo "DREAM.AI is running at $FRONTEND_URL"
open_browser
echo "Press Ctrl+C to stop"
echo

wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
