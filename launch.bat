@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Check if container is running
docker ps | find "dreamai-backend" >nul 2>&1
if !errorlevel! equ 0 (
    echo.
    echo Stopping DREAM.AI...
    cd docker
    docker-compose down
    cd ..
    echo.
    echo ✓ DREAM.AI stopped
    echo.
) else (
    echo.
    echo Starting DREAM.AI...
    cd docker
    docker-compose up -d
    cd ..
    echo.
    echo ✓ Backend started! Opening browser...
    echo.
    echo Starting HTTP server on port 8888...
    echo.
    start http://localhost:8888/test_websocket.html
    python -m http.server 8888 --directory .
)
pause
