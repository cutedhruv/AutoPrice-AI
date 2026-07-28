@echo off
REM AutoPrice AI - Quick Start Script for Windows

echo.
echo ===================================
echo  AutoPrice AI - Windows Quick Start
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo ✓ Python found
echo ✓ Node.js found
echo.

REM Setup Backend (if needed)
if not exist "backend\venv\Scripts\python.exe" (
    echo Setting up backend...
    cd backend
    python -m venv venv
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
    cd ..
    echo ✓ Backend setup complete
    echo.
)

REM Setup Frontend (if needed)
if not exist "frontend\node_modules" (
    echo Setting up frontend...
    cd frontend
    call npm install
    cd ..
    echo ✓ Frontend setup complete
    echo.
)

REM Start Backend
echo Starting Backend Server (http://localhost:8000)...
echo.
start cmd /k "cd backend && venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000"

REM Wait a bit for backend to start
timeout /t 3 /nobreak

REM Start Frontend
echo Starting Frontend Server (http://localhost:3000)...
echo.
start cmd /k "cd frontend && npm start"

echo.
echo ===================================
echo  ✓ Servers Starting
echo ===================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window...
pause
