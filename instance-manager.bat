@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

REM DREAM.AI Instance Manager for Windows
REM Helper script for managing individual instances in multi-instance deployments

set COMPOSE_FILE=docker\docker-compose.orchestrator.yml

if "%1"=="" goto show_help
if "%1"=="--help" goto show_help
if "%1"=="-h" goto show_help
if "%1"=="list" goto list_instances
if "%1"=="status" goto show_status

REM Commands that require instance name
if "%1"=="start" goto start_instance
if "%1"=="stop" goto stop_instance
if "%1"=="logs" goto view_logs

echo Unknown command: %1
goto show_help

:start_instance
if "%2"=="" (
    echo Error: Instance name required
    echo Usage: instance-manager.bat start ^<instance-name^>
    goto list_instances
)
echo Starting instance: %2
docker ps -a --format "{{.Names}}" | find /I "dreamai-backend-%2" >nul
if errorlevel 1 (
    echo Error: Instance '%2' not found
    goto list_instances
)
docker start dreamai-backend-%2 dreamai-frontend-%2
echo Waiting for %2 to be ready...
set /a count=0
:start_check
set /a count+=1
docker exec dreamai-backend-%2 curl -sf http://localhost:8000/health >nul 2>&1
if !errorlevel! equ 0 (
    echo ^✓ Instance %2 is ready
    exit /b 0
)
if !count! geq 48 (
    echo ^⚠ Instance %2 may not be fully ready yet
    exit /b 0
)
timeout /t 10 /nobreak >nul
goto start_check

:stop_instance
if "%2"=="" (
    echo Error: Instance name required
    echo Usage: instance-manager.bat stop ^<instance-name^>
    goto list_instances
)
echo Stopping instance: %2
docker ps --format "{{.Names}}" | find /I "dreamai-backend-%2" >nul
if errorlevel 1 (
    echo No running instance '%2' found
    exit /b 0
)
docker stop dreamai-backend-%2 dreamai-frontend-%2
echo ^✓ Instance %2 stopped
exit /b 0

:list_instances
echo Available instances:
echo   1. alice
echo   2. bob
echo   3. charlie
exit /b 0

:show_status
echo Instance Status:
echo ================
for %%I in (alice bob charlie) do (
    docker ps --format "{{.Names}}" | find /I "dreamai-backend-%%I" >nul
    if !errorlevel! equ 0 (
        docker exec dreamai-backend-%%I curl -sf http://localhost:8000/health >nul 2>&1
        if !errorlevel! equ 0 (
            echo   ^✓ %%I: RUNNING ^(healthy^)
        ) else (
            echo   ^⚠ %%I: RUNNING ^(unhealthy^)
        )
    ) else (
        docker ps -a --format "{{.Names}}" | find /I "dreamai-backend-%%I" >nul
        if !errorlevel! equ 0 (
            echo   ^◯ %%I: STOPPED
        ) else (
            echo   - %%I: NOT CREATED
        )
    )
)
exit /b 0

:view_logs
if "%2"=="" (
    echo Error: Instance name required
    echo Usage: instance-manager.bat logs ^<instance-name^>
    goto list_instances
)
echo Logs for instance: %2
docker logs -f --tail 100 dreamai-backend-%2
exit /b 0

:show_help
cls
echo DREAM.AI Instance Manager
echo.
echo Usage:
echo   instance-manager.bat start ^<instance-name^>     Start a specific instance
echo   instance-manager.bat stop ^<instance-name^>      Stop a specific instance
echo   instance-manager.bat list                       List all instances
echo   instance-manager.bat logs ^<instance-name^>     View logs for instance
echo   instance-manager.bat status                     Show all instance statuses
echo.
echo Examples:
echo   REM Start Alice instance
echo   instance-manager.bat start alice
echo.
echo   REM Stop Bob instance
echo   instance-manager.bat stop bob
echo.
echo   REM View logs for Charlie
echo   instance-manager.bat logs charlie
echo.
echo   REM Show all instances and their status
echo   instance-manager.bat status
echo.
echo Valid instance names: alice, bob, charlie
echo.
pause
exit /b 0
