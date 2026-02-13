@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set BACKEND_URL=http://localhost:8000
set FRONTEND_URL=http://localhost:5173
REM Backend can take 2-4 min to init AI2-THOR/ProcTHOR; allow up to ~8 min
set HEALTH_RETRIES=48
set HEALTH_INTERVAL=10

REM Check Docker
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed or not running.
    echo Install Docker Desktop: https://docs.docker.com/get-docker/
    pause
    exit /b 1
)

REM Check .env
if exist .env (
    echo Using .env for GEMINI_API_KEY / GOOGLE_API_KEY
) else (
    echo Note: No .env file. Create one with GEMINI_API_KEY or GOOGLE_API_KEY for the Orchestrator LLM.
)

REM Check if already running
docker ps --format "{{.Names}}" 2>nul | findstr "src-backend" >nul 2>&1
if !errorlevel! equ 0 (
    echo.
    echo Stopping DREAM.AI...
    cd docker
    docker compose down 2>nul || docker-compose down 2>nul
    cd ..
    echo DREAM.AI stopped.
    echo.
    pause
    exit /b 0
)

echo.
echo Starting DREAM.AI ^(backend + frontend^)...
echo This may take a few minutes on first run.
echo.

cd docker
docker compose up -d --build 2>nul || docker-compose up -d --build 2>nul
cd ..

REM Wait for backend
echo Waiting for backend to be ready...
set /a count=0
:health_loop
set /a count+=1
curl -sf %BACKEND_URL%/health >nul 2>&1
if !errorlevel! equ 0 goto backend_ready
if !count! geq %HEALTH_RETRIES% (
    echo Error: Backend did not become ready in time.
    pause
    exit /b 1
)
echo   Attempt !count!/%HEALTH_RETRIES% - backend not ready yet...
timeout /t %HEALTH_INTERVAL% /nobreak >nul
goto health_loop

:backend_ready
echo Backend is ready.
echo.
echo DREAM.AI is running!
echo   Frontend: %FRONTEND_URL%
echo   Backend:  %BACKEND_URL%
echo.
echo Opening browser...
timeout /t 2 /nobreak >nul
start "" "%FRONTEND_URL%"
echo.
echo To stop: run launch.bat again, or "cd docker ^&^& docker compose down"
echo.
pause
