@echo off
REM DREAM.AI Production Docker Quick Start
REM This script builds and starts the entire production stack

setlocal enabledelayedexpansion

echo.
echo ========================================
echo DREAM.AI Production Deployment
echo ========================================
echo.

REM Check Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker not found. Install from https://www.docker.com/
    exit /b 1
)

REM Check Docker Compose
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose not found.
    exit /b 1
)

echo [1/3] Building Docker images...
docker-compose build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    exit /b 1
)

echo.
echo [2/3] Starting containers...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start containers
    exit /b 1
)

echo.
echo [3/3] Waiting for services to be healthy...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo DREAM.AI is running!
echo ========================================
echo.
echo Frontend:   http://localhost
echo API Health: http://localhost/health
echo WebSocket: ws://localhost/ws/game
echo.
echo View logs:     docker-compose logs -f
echo Stop services: docker-compose down
echo.
echo Opening browser...
start http://localhost

echo.
echo Ready! Check READY_TO_DEPLOY.md for next steps.
echo.
