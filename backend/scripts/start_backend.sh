#!/bin/bash

# Stock Trading Backend Server Start Script
# This script activates the virtual environment and starts the FastAPI backend server
# 
# 사용법: 어디서든 실행 가능하지만, 반드시 backend 폴더에서 실행됩니다.
# 예: ./backend/scripts/start_backend.sh 또는 cd backend/scripts && ./start_backend.sh

echo "🚀 Starting Stock Trading Backend Server..."
echo "============================================"

# 실행 위치 저장 (나중에 복원용)
ORIGINAL_DIR="$(pwd)"
echo "📁 Original execution directory: $ORIGINAL_DIR"

# 스크립트 파일의 절대 경로 찾기
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Script location: $SCRIPT_DIR"

# Backend 디렉토리 찾기 (스크립트의 상위 폴더)
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
echo "📁 Backend directory: $BACKEND_DIR"

# Backend 구조 검증
if [ ! -d "$BACKEND_DIR/vkis" ]; then
    echo "❌ Error: 'vkis' virtual environment not found in backend directory"
    echo "💡 Expected structure: backend/vkis/"
    echo "📁 Backend directory: $BACKEND_DIR"
    echo "💡 Please ensure this script is in the correct location: backend/scripts/"
    exit 1
fi

if [ ! -f "$BACKEND_DIR/simple_server.py" ]; then
    echo "❌ Error: 'simple_server.py' not found in backend directory"
    echo "💡 Expected file: backend/simple_server.py"
    echo "📁 Backend directory: $BACKEND_DIR"
    exit 1
fi

# Backend 디렉토리로 이동 (반드시 여기서 실행)
echo "📁 Navigating to backend directory for execution..."
cd "$BACKEND_DIR" || {
    echo "❌ Error: Failed to navigate to backend directory"
    exit 1
}
echo "📁 Now executing from: $(pwd)"

# Check if virtual environment exists
VENV_DIR="./vkis"
echo "🐍 Virtual environment directory: $VENV_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Error: Virtual environment not found at $VENV_DIR"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated successfully"
echo "🐍 Python version: $(python --version)"
echo "🐍 Python path: $(which python)"

# Check if simple_server.py exists
SERVER_FILE="./simple_server.py"
echo "📄 Server file: $SERVER_FILE"

if [ ! -f "$SERVER_FILE" ]; then
    echo "❌ Error: simple_server.py not found at $SERVER_FILE"
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking required packages..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Some required packages may not be installed"
    echo "💡 You may need to run: pip install -r requirements.txt"
fi

# Start the server
echo ""
echo "🌟 Starting FastAPI server..."
echo "🌐 Server will be available at: http://localhost:8000"
echo "📊 API documentation at: http://localhost:8000/docs"
echo "🔗 Health check at: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================"

# Run the server
python "$SERVER_FILE"
