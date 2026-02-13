#!/bin/bash
# DREAM.AI Launch Script (macOS/Linux)
# Starts backend + frontend and opens the app in your browser.

set -e
cd "$(dirname "$0")"

BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
# Backend can take 2–4 min to init AI2-THOR/ProcTHOR; allow up to ~8 min
HEALTH_RETRIES=48
HEALTH_INTERVAL=10

check_docker() {
    if ! command -v docker &>/dev/null; then
        echo "Error: Docker is not installed or not in PATH."
        echo "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    if ! docker info &>/dev/null; then
        echo "Error: Docker is not running. Please start Docker Desktop."
        exit 1
    fi
}

check_env() {
    if [ -f .env ]; then
        echo "Using .env for GEMINI_API_KEY / GOOGLE_API_KEY"
    else
        echo "Note: No .env file found. Create one with GEMINI_API_KEY or GOOGLE_API_KEY for the Orchestrator LLM."
    fi
}

wait_for_backend() {
    echo "Waiting for backend to be ready (AI2-THOR init can take 2–4 min)..."
    for i in $(seq 1 $HEALTH_RETRIES); do
        if curl -sf "$BACKEND_URL/health" &>/dev/null; then
            echo "Backend is ready."
            return 0
        fi
        echo "  Attempt $i/$HEALTH_RETRIES - backend not ready yet..."
        sleep $HEALTH_INTERVAL
    done
    echo "Error: Backend did not become ready in time."
    exit 1
}

open_browser() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$FRONTEND_URL"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$FRONTEND_URL" 2>/dev/null || echo "Open $FRONTEND_URL in your browser"
    else
        echo "Open $FRONTEND_URL in your browser"
    fi
}

# ----- Main -----
check_docker
check_env

if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "src-backend"; then
    echo
    echo "Stopping DREAM.AI..."
    cd docker
    DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose down 2>/dev/null || docker-compose down 2>/dev/null
    cd ..
    echo "DREAM.AI stopped."
    echo
    exit 0
fi

echo
echo "Starting DREAM.AI (backend + frontend)..."
echo "This may take a few minutes on first run (building images)."
echo

cd docker
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up -d --build 2>/dev/null || DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose up -d --build 2>/dev/null
cd ..

wait_for_backend

echo
echo "DREAM.AI is running!"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo
echo "Opening browser..."
sleep 2
open_browser

echo
echo "To stop: run launch.sh again, or 'cd docker && docker compose down'"
echo
