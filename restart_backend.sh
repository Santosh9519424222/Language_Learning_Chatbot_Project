#!/bin/bash
# Restart Backend Script for PDF Learning Platform
# This script safely restarts the backend with all fixes applied

echo "========================================="
echo "PDF Learning Platform - Backend Restart"
echo "========================================="
echo ""

# Kill existing backend processes
echo "🛑 Stopping existing backend..."
pkill -9 -f "uvicorn.*8080" 2>/dev/null || true
sleep 2

# Navigate to backend directory
cd /home/santoshyadav_951942/Language_Learning_Chatbot_Project/backend

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source ../venv/bin/activate

# Set environment variables
echo "⚙️  Setting environment variables..."
export GEMINI_API_KEY="AIzaSyCGfe19ObPbhOV1MdmjDJpkQUYddWlzUPU"
export DATABASE_URL="sqlite:///../demo.db"
export ENVIRONMENT="development"
export PYTHONPATH=/home/santoshyadav_951942/Language_Learning_Chatbot_Project/backend

# Start backend
echo "🚀 Starting backend on port 8080..."
nohup uvicorn main:app --host 0.0.0.0 --port 8080 > ../backend.log 2>&1 &
BACKEND_PID=$!

echo ""
echo "⏳ Waiting for backend to start..."
sleep 5

# Test backend
echo "🔍 Testing backend health..."
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✅ Backend is running successfully!"
    echo ""
    echo "📊 Backend Status:"
    curl -s http://localhost:8080/health | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'   Status: {d[\"status\"]}'); print(f'   Gemini: {d[\"services\"][\"gemini_api\"]}'); print(f'   Agents: {d[\"agents_active\"]}')"
    echo ""
    echo "🌐 Access Points:"
    echo "   Backend API: http://localhost:8080"
    echo "   API Docs: http://localhost:8080/docs"
    echo "   Frontend: http://localhost:3000/index.html"
    echo ""
    echo "📝 Logs: tail -f /home/santoshyadav_951942/Language_Learning_Chatbot_Project/backend.log"
    echo ""
    echo "Process ID: $BACKEND_PID"
else
    echo "❌ Backend failed to start. Check logs:"
    echo "   tail -30 /home/santoshyadav_951942/Language_Learning_Chatbot_Project/backend.log"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Backend restart complete!"
echo "========================================="

