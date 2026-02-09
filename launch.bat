@echo off
REM DREAM.AI Launcher - Starts Docker containers and opens the game interface

cd /d "%~dp0"

echo ========================================
echo DREAM.AI - Starting Services
echo ========================================
echo.

echo [1/4] Starting Docker containers...
docker-compose down >nul 2>&1
docker-compose up -d

echo [2/4] Waiting for services to initialize (45 seconds)...
timeout /t 45 /nobreak

echo.
echo [3/4] Checking container status...
docker-compose ps

echo.
echo [4/4] Starting HTTP server and opening browser...
start python -m http.server 8888 --directory .
timeout /t 2

echo.
echo ========================================
echo Launching browser at http://localhost:8888/test_websocket.html
echo ========================================
echo.

start http://localhost:8888/test_websocket.html

echo.
echo Done! The game should open in your browser.
echo.
echo To stop everything later, run: docker-compose down
echo.
pause
