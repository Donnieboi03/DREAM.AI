#!/bin/bash
cd "$(dirname "$0")"

# Check if container is running
if docker ps | grep -q "dreamai-backend"; then
    echo
    echo "Stopping DREAM.AI..."
    cd docker
    DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose down
    cd ..
    echo
    echo "✓ DREAM.AI stopped"
    echo
else
    echo
    echo "Starting DREAM.AI..."
    cd docker
    DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose up -d --build
    cd ..
    echo
    echo "✓ Backend started! Opening browser..."
    echo
    echo "Starting HTTP server on port 8888..."
    echo
    
    # Open browser (platform-specific)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost:8888/test_websocket.html
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open http://localhost:8888/test_websocket.html 2>/dev/null || echo "Please open http://localhost:8888/test_websocket.html in your browser"
    fi
    
    python3 -m http.server 8888 --directory .
fi

# Pause equivalent (wait for user input)
read -p "Press any key to continue..."
