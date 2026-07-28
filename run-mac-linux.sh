#!/bin/bash

# AutoPrice AI - Quick Start Script for Mac/Linux

echo ""
echo "==================================="
echo " AutoPrice AI - Mac/Linux Quick Start"
echo "==================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.9+ from https://www.python.org/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found!"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"
echo "✓ Node.js found: $(node --version)"
echo ""

# Setup Backend (if needed)
if [ ! -d "backend/venv" ]; then
    echo "Setting up backend..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo "✓ Backend setup complete"
    echo ""
fi

# Setup Frontend (if needed)
if [ ! -d "frontend/node_modules" ]; then
    echo "Setting up frontend..."
    cd frontend
    npm install
    cd ..
    echo "✓ Frontend setup complete"
    echo ""
fi

echo ""
echo "==================================="
echo " Starting AutoPrice AI"
echo "==================================="
echo ""

# Start Backend
echo "Starting Backend Server (http://localhost:8000)..."
cd backend
source venv/bin/activate
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start Frontend
echo "Starting Frontend Server (http://localhost:3000)..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo ""
echo "==================================="
echo " ✓ Servers Starting"
echo "==================================="
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press CTRL+C to stop all servers"
echo ""

# Keep script running and handle cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
