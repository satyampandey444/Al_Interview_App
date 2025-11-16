#!/bin/bash

# Interview Management System - Startup Script

echo "🚀 Starting Interview Management System..."
echo ""

# Check if backend .env exists
if [ ! -f backend/.env ]; then
    echo "⚠️  Warning: backend/.env file not found!"
    echo "Please create backend/.env file from backend/.env.example"
    echo "and add your configuration (API keys, MongoDB URI, JWT secret)."
    exit 1
fi

# Check if MongoDB is running
echo "🔍 Checking MongoDB connection..."
if command -v mongosh &> /dev/null; then
    if mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        echo "✅ MongoDB is running"
    else
        echo "⚠️  Warning: MongoDB is not running!"
        echo "Please start MongoDB:"
        echo "  macOS: brew services start mongodb-community"
        echo "  Linux: sudo systemctl start mongod"
        echo ""
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
elif command -v mongo &> /dev/null; then
    if mongo --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
        echo "✅ MongoDB is running"
    else
        echo "⚠️  Warning: MongoDB is not running!"
        echo "Please start MongoDB or use MongoDB Atlas."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "⚠️  MongoDB client not found, skipping connection check"
    echo "Make sure MongoDB is running or you're using MongoDB Atlas"
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run backend
start_backend() {
    echo -e "${BLUE}📦 Starting Backend Server...${NC}"
    cd backend
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Start Flask server
    python api.py &
    BACKEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Backend server started (PID: $BACKEND_PID)${NC}"
}

# Function to run frontend
start_frontend() {
    echo -e "${BLUE}📦 Starting Frontend Server...${NC}"
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing frontend dependencies..."
        npm install
    fi
    
    # Start Vite dev server
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Frontend server started (PID: $FRONTEND_PID)${NC}"
}

# Start both servers
start_backend
sleep 3
start_frontend

echo ""
echo -e "${GREEN}🎉 Application started successfully!${NC}"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend:  http://localhost:5001"
echo ""
echo "👉 First time setup:"
echo "   1. Register as Admin or Candidate"
echo "   2. Admin: Create tests and assign to candidates"
echo "   3. Candidate: Take assigned tests"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Keep script running
wait

