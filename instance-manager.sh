#!/bin/bash
# DREAM.AI Instance Manager
# Helper script for managing individual instances in multi-instance deployments

cd "$(dirname "$0")"

INSTANCES=("alice" "bob" "charlie" "dave" "eve" "frank" "grace" "henry")
COMPOSE_FILE="docker/docker-compose.orchestrator.yml"

show_help() {
    cat << 'EOF'
DREAM.AI Instance Manager

Usage:
  ./instance-manager.sh start <instance-name>     Start a specific instance
  ./instance-manager.sh stop <instance-name>      Stop a specific instance
  ./instance-manager.sh list                       List all instances
  ./instance-manager.sh logs <instance-name>      View logs for instance
  ./instance-manager.sh status                    Show all instance statuses

Examples:
  # Start Alice instance
  ./instance-manager.sh start alice

  # Stop Bob instance
  ./instance-manager.sh stop bob

  # View logs for Charlie
  ./instance-manager.sh logs charlie

  # Show all instances and their status
  ./instance-manager.sh status

Valid instance names: ${INSTANCES[@]}
EOF
}

list_instances() {
    echo "Available instances:"
    for i in "${!INSTANCES[@]}"; do
        echo "  $((i+1)). ${INSTANCES[$i]}"
    done
}

get_instance_containers() {
    local instance=$1
    echo "backend-$instance frontend-$instance"
}

start_instance() {
    local instance=$1
    echo "Starting instance: $instance"
    docker ps --all --format "{{.Names}}" | grep -q "dreamai-backend-$instance" || {
        echo "Error: Instance '$instance' not defined in docker-compose"
        return 1
    }
    
    docker start "dreamai-backend-$instance" "dreamai-frontend-$instance" 2>/dev/null
    
    echo "Waiting for $instance to be ready..."
    for i in {1..48}; do
        if docker exec "dreamai-backend-$instance" curl -sf "http://localhost:8000/health" &>/dev/null 2>&1; then
            echo "✓ Instance $instance is ready"
            return 0
        fi
        sleep 10
    done
    echo "⚠ Instance $instance may not be fully ready yet"
    return 0
}

stop_instance() {
    local instance=$1
    echo "Stopping instance: $instance"
    docker ps --format "{{.Names}}" | grep -q "dreamai-backend-$instance" || {
        echo "No running instance '$instance' found"
        return 0
    }
    
    docker stop "dreamai-backend-$instance" "dreamai-frontend-$instance" 2>/dev/null
    echo "✓ Instance $instance stopped"
}

show_status() {
    echo "Instance Status:"
    echo "════════════════"
    for instance in "${INSTANCES[@]}"; do
        local backend="dreamai-backend-$instance"
        local frontend="dreamai-frontend-$instance"
        
        if docker ps --format "{{.Names}}" | grep -q "^${backend}$"; then
            docker exec "$backend" curl -sf "http://localhost:8000/health" &>/dev/null 2>&1
            if [ $? -eq 0 ]; then
                echo "  ✓ $instance: RUNNING (healthy)"
            else
                echo "  ⚠ $instance: RUNNING (unhealthy)"
            fi
        elif docker ps --all --format "{{.Names}}" | grep -q "^${backend}$"; then
            echo "  ◯ $instance: STOPPED"
        else
            echo "  - $instance: NOT CREATED"
        fi
    done
}

view_logs() {
    local instance=$1
    echo "Logs for instance: $instance"
    docker logs -f --tail 100 "dreamai-backend-$instance" "dreamai-frontend-$instance"
}

# Main
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    start)
        if [ -z "$2" ]; then
            echo "Error: Instance name required"
            echo "Usage: $0 start <instance-name>"
            list_instances
            exit 1
        fi
        start_instance "$2"
        ;;
    stop)
        if [ -z "$2" ]; then
            echo "Error: Instance name required"
            echo "Usage: $0 stop <instance-name>"
            list_instances
            exit 1
        fi
        stop_instance "$2"
        ;;
    list)
        list_instances
        ;;
    status)
        show_status
        ;;
    logs)
        if [ -z "$2" ]; then
            echo "Error: Instance name required"
            echo "Usage: $0 logs <instance-name>"
            list_instances
            exit 1
        fi
        view_logs "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
