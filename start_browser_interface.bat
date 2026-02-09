@echo off
REM Quick start script for DREAM.AI Browser Interface
REM Run this from the project root directory

echo Starting DREAM.AI Browser Interface...
echo.

REM Check if Node is installed
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found. Please install Node.js from https://nodejs.org/
    exit /b 1
)

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python from https://www.python.org/
    exit /b 1
)

echo [1/4] Installing backend dependencies...
cd dreamai
pip install -r requirements.txt >nul 2>nul
pip install fastapi uvicorn pillow >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies
    exit /b 1
)
cd ..

echo [2/4] Installing frontend dependencies...
cd dreamai\frontend
call npm install >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to install frontend dependencies
    exit /b 1
)
cd ..\..

echo [3/4] Starting backend server...
start "DREAM.AI Backend" cmd /k "cd dreamai && python -m backend.api.app"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo [4/4] Starting frontend development server...
start "DREAM.AI Frontend" cmd /k "cd dreamai\frontend && npm run dev"

echo.
echo ============================================
echo DREAM.AI Browser Interface Started!
echo ============================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Open your browser to http://localhost:5173
echo.
echo Press Ctrl+C in either terminal to stop
echo.
timeout /t 5 >nul
