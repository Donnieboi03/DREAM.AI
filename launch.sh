#!/bin/bash
# DREAM.AI Launch Script (macOS/Linux)
# Supports single-instance and multi-instance (Nginx load balancer) deployments
#
# Usage:
#   ./launch.sh                    # Start 1 instance (default)
#   ./launch.sh --instances 3      # Start 3 instances with nginx load balancer
#   ./launch.sh --stop             # Stop all instances

set -e
cd "$(dirname "$0")"

# Configuration
NGINX_URL="http://localhost"
BACKEND_URL="http://localhost:8000"
FRONTEND_URL="http://localhost:5173"
NGINX_PORT="${NGINX_PORT:-80}"
NUM_INSTANCES="${1:-1}"

# Backend can take 2–4 min to init AI2-THOR/ProcTHOR; allow up to ~8 min
HEALTH_RETRIES=48
HEALTH_INTERVAL=10

# Parse arguments
if [[ "$1" == "--stop" ]] || [[ "$1" == "--shutdown" ]]; then
    STOP_MODE=true
elif [[ "$1" == "--instances" ]] && [[ -n "$2" ]]; then
    NUM_INSTANCES="$2"
else
    NUM_INSTANCES="${NUM_INSTANCES:-1}"
fi

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
        echo "✓ Using .env for GEMINI_API_KEY / GOOGLE_API_KEY"
    else
        echo "⚠ Note: No .env file found. Create one with GEMINI_API_KEY or GOOGLE_API_KEY"
    fi
}

wait_for_nginx() {
    echo "Waiting for Nginx to be ready..."
    for i in $(seq 1 12); do
        if curl -sf "http://localhost/health" &>/dev/null; then
            echo "✓ Nginx is ready"
            return 0
        fi
        echo "  Attempt $i/12 - nginx not ready yet..."
        sleep 5
    done
    echo "✓ Nginx health check unreliable, continuing anyway"
}

wait_for_backends() {
    echo "Waiting for all backends to be ready (AI2-THOR init can take 2–4 min)..."
    
    local backends=("alice" "bob" "charlie")
    local count=0
    for i in $(seq 1 $NUM_INSTANCES); do
        count=$((count + 1))
    done

    for backend_name in "${backends[@]:0:$count}"; do
        echo "  Checking backend-$backend_name..."
        for retry in $(seq 1 $HEALTH_RETRIES); do
            if docker exec "dreamai-backend-$backend_name" curl -sf "http://localhost:8000/health" &>/dev/null 2>&1; then
                echo "    ✓ backend-$backend_name is ready"
                break
            fi
            if [ $retry -eq $HEALTH_RETRIES ]; then
                echo "    ✗ backend-$backend_name failed to become ready"
                return 1
            fi
            sleep $HEALTH_INTERVAL
        done
    done
    echo "✓ All backends are ready"
}

open_browser() {
    local url="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$url"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$url" 2>/dev/null || echo "Open $url in your browser"
    else
        echo "Open $url in your browser"
    fi
}

show_usage() {
    cat << 'EOF'
DREAM.AI Launcher - Multi-Instance Support

Usage:
  ./launch.sh                     Start with 1 instance (simple setup)
  ./launch.sh --instances 3       Start with 3 instances + nginx load balancer
  ./launch.sh --stop              Stop all running instances

Examples:
  # Single instance (development)
  ./launch.sh

  # Multi-instance load-balanced setup (production)
  ./launch.sh --instances 3

  # Stop everything
  ./launch.sh --stop

Environment Variables:
  NUM_INSTANCES         Number of instances to start (default: 1)
  NGINX_PORT            Port for nginx load balancer (default: 80)

Instance Names (for reference):
  - alice (always running)
  - bob (if NUM_INSTANCES >= 2)
  - charlie (if NUM_INSTANCES >= 3)
EOF
}

# ----- Main -----
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_usage
    exit 0
fi

check_docker
check_env

if [ "$STOP_MODE" = true ]; then
    echo ""
    echo "Stopping DREAM.AI (all instances)..."
    cd docker
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "dreamai-"; then
        DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose -f docker-compose.orchestrator.yml down 2>/dev/null || true
    else
        echo "No DREAM.AI containers found running"
    fi
    cd ..
    echo "✓ DREAM.AI stopped"
    echo ""
    exit 0
fi

# Check if single instance is already running
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "src-backend"; then
    echo ""
    echo "Old single-instance setup detected. Stopping..."
    cd docker
    DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose down 2>/dev/null || docker-compose down 2>/dev/null
    cd ..
    echo "✓ Old instance stopped"
    echo ""
fi

echo ""
if [ "$NUM_INSTANCES" -eq 1 ]; then
    echo "Starting DREAM.AI (1 instance)..."
    echo "This may take a few minutes on first run (building images)."
    cd docker
    DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up -d --build 2>/dev/null || DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose up -d --build 2>/dev/null
    cd ..
    
    wait_for_backend
    
    echo ""
    echo "✓ DREAM.AI is running!"
    echo "  Frontend: $FRONTEND_URL"
    echo "  Backend:  $BACKEND_URL"
    echo ""
    echo "Opening browser..."
    sleep 2
    open_browser "$FRONTEND_URL"
else
    echo "Starting DREAM.AI with $NUM_INSTANCES instances + Nginx load balancer..."
    echo "This may take a few minutes on first run (building images)."
    cd docker
    
    # Start with profiles for multi-instance based on number requested
    if [ "$NUM_INSTANCES" -ge 2 ]; then
        DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose -f docker-compose.orchestrator.yml --profile multi-instance up -d --build 2>/dev/null || true
    else
        DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose -f docker-compose.orchestrator.yml up -d --build 2>/dev/null || true
    fi
    
    cd ..
    
    wait_for_nginx
    wait_for_backends
    
    echo ""
    echo "✓ DREAM.AI is running with $NUM_INSTANCES instances!"
    echo "  Load Balancer: $NGINX_URL (port $NGINX_PORT)"
    echo "  Instances:"
    for i in $(seq 1 $NUM_INSTANCES); do
        instance_names=("alice" "bob" "charlie" "dave" "eve" "frank")
        echo "    - ${instance_names[$((i-1))]}"
    done
    echo ""
    echo "Opening browser..."
    sleep 2
    open_browser "$NGINX_URL"
fi

echo ""
echo "To view logs:"
echo "  docker compose -f docker/docker-compose.orchestrator.yml logs -f"
echo ""
echo "To stop: ./launch.sh --stop"
echo ""
