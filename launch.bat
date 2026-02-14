@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Configuration
set NGINX_URL=http://localhost
set BACKEND_URL=http://localhost:8000
set FRONTEND_URL=http://localhost:5173
set NGINX_PORT=80
set NUM_INSTANCES=1

REM Parse arguments
if "%1"=="--stop" goto stop_mode
if "%1"=="--shutdown" goto stop_mode
if "%1"=="--instances" (
    if not "%2"=="" (
        set NUM_INSTANCES=%2
    )
)
if "%1"=="--help" goto show_usage
if "%1"=="-h" goto show_usage

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
    echo ^✓ Using .env for GEMINI_API_KEY / GOOGLE_API_KEY
) else (
    echo ^⚠ Note: No .env file. Create one with GEMINI_API_KEY / GOOGLE_API_KEY
)

REM Check for old single-instance setup
docker ps --format "{{.Names}}" 2>nul | findstr "src-backend" >nul 2>&1
if !errorlevel! equ 0 (
    echo.
    echo Stopping old single-instance setup...
    cd docker
    docker compose down 2>nul || docker-compose down 2>nul
    cd ..
    echo ^✓ Old instance stopped
    echo.
)

echo.
if %NUM_INSTANCES% equ 1 (
    echo Starting DREAM.AI ^(1 instance^)...
    echo This may take a few minutes on first run.
    echo.
    
    cd docker
    docker compose up -d --build 2>nul || docker-compose up -d --build 2>nul
    cd ..
    
    echo Waiting for backend to be ready ^(AI2-THOR init can take 2-4 min^)...
    set /a count=0
    :health_loop
    set /a count+=1
    curl -sf %BACKEND_URL%/health >nul 2>&1
    if !errorlevel! equ 0 goto backend_ready
    if !count! geq 48 (
        echo Error: Backend did not become ready in time.
        pause
        exit /b 1
    )
    echo   Attempt !count!/48 - backend not ready yet...
    timeout /t 10 /nobreak >nul
    goto health_loop
    
    :backend_ready
    echo ^✓ Backend is ready.
    echo.
    echo ^✓ DREAM.AI is running!
    echo   Frontend: %FRONTEND_URL%
    echo   Backend:  %BACKEND_URL%
    echo.
    echo Opening browser...
    timeout /t 2 /nobreak >nul
    start "" "%FRONTEND_URL%"
) else (
    echo Starting DREAM.AI with %NUM_INSTANCES% instances + Nginx load balancer...
    echo This may take a few minutes on first run.
    echo.
    
    cd docker
    if %NUM_INSTANCES% geq 2 (
        docker compose -f docker-compose.orchestrator.yml --profile multi-instance up -d --build 2>nul
    ) else (
        docker compose -f docker-compose.orchestrator.yml up -d --build 2>nul
    )
    cd ..
    
    echo Waiting for Nginx to be ready...
    set /a count=0
    :nginx_check
    set /a count+=1
    curl -sf http://localhost/health >nul 2>&1
    if !errorlevel! equ 0 goto nginx_ready
    if !count! geq 12 goto nginx_ready
    echo   Attempt !count!/12 - nginx not ready yet...
    timeout /t 5 /nobreak >nul
    goto nginx_check
    
    :nginx_ready
    echo ^✓ Nginx is ready.
    echo.
    echo ^✓ DREAM.AI is running with %NUM_INSTANCES% instances!
    echo   Load Balancer: %NGINX_URL% ^(port %NGINX_PORT%^)
    echo   Instances:
    if %NUM_INSTANCES% geq 1 echo     - alice
    if %NUM_INSTANCES% geq 2 echo     - bob
    if %NUM_INSTANCES% geq 3 echo     - charlie
    if %NUM_INSTANCES% geq 4 echo     - dave
    if %NUM_INSTANCES% geq 5 echo     - eve
    if %NUM_INSTANCES% geq 6 echo     - frank
    echo.
    echo Opening browser...
    timeout /t 2 /nobreak >nul
    start "" "%NGINX_URL%"
)

echo.
echo To view logs:
echo   docker compose -f docker/docker-compose.orchestrator.yml logs -f
echo.
echo To stop: launch.bat --stop
echo.
pause
exit /b 0

:stop_mode
echo.
echo Stopping DREAM.AI ^(all instances^)...
cd docker
docker ps --format "{{.Names}}" 2>nul | findstr "dreamai-" >nul 2>&1
if !errorlevel! equ 0 (
    docker compose -f docker-compose.orchestrator.yml down 2>nul || true
) else (
    echo No DREAM.AI containers found running
)
cd ..
echo ^✓ DREAM.AI stopped
echo.
pause
exit /b 0

:show_usage
cls
echo DREAM.AI Launcher - Multi-Instance Support
echo.
echo Usage:
echo   launch.bat                  Start with 1 instance ^(simple setup^)
echo   launch.bat --instances 3    Start with 3 instances + nginx load balancer
echo   launch.bat --stop           Stop all running instances
echo.
echo Examples:
echo   REM Single instance ^(development^)
echo   launch.bat
echo.
echo   REM Multi-instance load-balanced setup ^(production^)
echo   launch.bat --instances 3
echo.
echo   REM Stop everything
echo   launch.bat --stop
echo.
echo Instance Names:
echo   - alice ^(always running^)
echo   - bob ^(if instances ^>= 2^)
echo   - charlie ^(if instances ^>= 3^)
echo.
pause
exit /b 0
