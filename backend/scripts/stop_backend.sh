#!/bin/bash

# Stock Trading Backend Server Stop Script
# This script stops the running FastAPI backend server
# 
# 사용법: 어디서든 실행 가능하지만, backend 서버를 찾아서 중지시킵니다.

echo "🛑 Stopping Stock Trading Backend Server..."
echo "============================================"

# 실행 위치 저장
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
    exit 1
fi

echo ""
echo "🔍 Searching for running backend server processes..."

# 방법 1: 포트 8000을 사용하는 프로세스 찾기
echo "📡 Checking processes using port 8000..."
PORT_PROCESSES=$(lsof -ti:8000 2>/dev/null)

if [ ! -z "$PORT_PROCESSES" ]; then
    echo "✅ Found process(es) using port 8000: $PORT_PROCESSES"
    
    # 각 프로세스에 대해 상세 정보 표시
    for pid in $PORT_PROCESSES; do
        PROCESS_INFO=$(ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null)
        if [ ! -z "$PROCESS_INFO" ]; then
            echo "  📋 Process $pid: $PROCESS_INFO"
        fi
    done
    
    echo ""
    echo "🛑 Stopping processes using port 8000..."
    
    # 프로세스들을 우아하게 종료 시도
    for pid in $PORT_PROCESSES; do
        echo "  🔄 Sending SIGTERM to process $pid..."
        kill -TERM $pid 2>/dev/null
        
        # 잠시 대기 후 여전히 실행 중이면 강제 종료
        sleep 2
        if kill -0 $pid 2>/dev/null; then
            echo "  ⚡ Process $pid still running, sending SIGKILL..."
            kill -KILL $pid 2>/dev/null
        fi
    done
    
    # 최종 확인
    sleep 1
    REMAINING_PROCESSES=$(lsof -ti:8000 2>/dev/null)
    if [ -z "$REMAINING_PROCESSES" ]; then
        echo "✅ Successfully stopped all processes using port 8000"
    else
        echo "⚠️  Some processes may still be running: $REMAINING_PROCESSES"
    fi
else
    echo "ℹ️  No processes found using port 8000"
fi

echo ""
echo "🔍 Searching for Python processes running simple_server.py..."

# 방법 2: simple_server.py를 실행하는 Python 프로세스 찾기
PYTHON_PROCESSES=$(pgrep -f "simple_server.py" 2>/dev/null)

if [ ! -z "$PYTHON_PROCESSES" ]; then
    echo "✅ Found Python process(es) running simple_server.py: $PYTHON_PROCESSES"
    
    # 각 프로세스에 대해 상세 정보 표시
    for pid in $PYTHON_PROCESSES; do
        PROCESS_INFO=$(ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null)
        if [ ! -z "$PROCESS_INFO" ]; then
            echo "  📋 Process $pid: $PROCESS_INFO"
        fi
    done
    
    echo ""
    echo "🛑 Stopping Python processes running simple_server.py..."
    
    # 프로세스들을 우아하게 종료 시도
    for pid in $PYTHON_PROCESSES; do
        echo "  🔄 Sending SIGTERM to process $pid..."
        kill -TERM $pid 2>/dev/null
        
        # 잠시 대기 후 여전히 실행 중이면 강제 종료
        sleep 2
        if kill -0 $pid 2>/dev/null; then
            echo "  ⚡ Process $pid still running, sending SIGKILL..."
            kill -KILL $pid 2>/dev/null
        fi
    done
    
    # 최종 확인
    sleep 1
    REMAINING_PYTHON_PROCESSES=$(pgrep -f "simple_server.py" 2>/dev/null)
    if [ -z "$REMAINING_PYTHON_PROCESSES" ]; then
        echo "✅ Successfully stopped all Python processes running simple_server.py"
    else
        echo "⚠️  Some Python processes may still be running: $REMAINING_PYTHON_PROCESSES"
    fi
else
    echo "ℹ️  No Python processes found running simple_server.py"
fi

echo ""
echo "🔍 Searching for uvicorn processes..."

# 방법 3: uvicorn 프로세스 찾기 (FastAPI 서버)
UVICORN_PROCESSES=$(pgrep -f "uvicorn" 2>/dev/null)

if [ ! -z "$UVICORN_PROCESSES" ]; then
    echo "✅ Found uvicorn process(es): $UVICORN_PROCESSES"
    
    # 각 프로세스에 대해 상세 정보 표시
    for pid in $UVICORN_PROCESSES; do
        PROCESS_INFO=$(ps -p $pid -o pid,ppid,cmd --no-headers 2>/dev/null)
        if [ ! -z "$PROCESS_INFO" ]; then
            echo "  📋 Process $pid: $PROCESS_INFO"
        fi
    done
    
    echo ""
    echo "🛑 Stopping uvicorn processes..."
    
    # 프로세스들을 우아하게 종료 시도
    for pid in $UVICORN_PROCESSES; do
        echo "  🔄 Sending SIGTERM to process $pid..."
        kill -TERM $pid 2>/dev/null
        
        # 잠시 대기 후 여전히 실행 중이면 강제 종료
        sleep 2
        if kill -0 $pid 2>/dev/null; then
            echo "  ⚡ Process $pid still running, sending SIGKILL..."
            kill -KILL $pid 2>/dev/null
        fi
    done
    
    # 최종 확인
    sleep 1
    REMAINING_UVICORN_PROCESSES=$(pgrep -f "uvicorn" 2>/dev/null)
    if [ -z "$REMAINING_UVICORN_PROCESSES" ]; then
        echo "✅ Successfully stopped all uvicorn processes"
    else
        echo "⚠️  Some uvicorn processes may still be running: $REMAINING_UVICORN_PROCESSES"
    fi
else
    echo "ℹ️  No uvicorn processes found"
fi

echo ""
echo "📊 Final Status Check:"
echo "====================="

# 최종 상태 확인
FINAL_PORT_PROCESSES=$(lsof -ti:8000 2>/dev/null)
FINAL_PYTHON_PROCESSES=$(pgrep -f "simple_server.py" 2>/dev/null)
FINAL_UVICORN_PROCESSES=$(pgrep -f "uvicorn" 2>/dev/null)

if [ -z "$FINAL_PORT_PROCESSES" ] && [ -z "$FINAL_PYTHON_PROCESSES" ] && [ -z "$FINAL_UVICORN_PROCESSES" ]; then
    echo "✅ All backend server processes have been successfully stopped!"
    echo "🌐 Port 8000 is now available"
    echo ""
    echo "💡 To start the server again, run:"
    echo "   ./backend/scripts/start_backend.sh"
else
    echo "⚠️  Some processes may still be running:"
    [ ! -z "$FINAL_PORT_PROCESSES" ] && echo "   - Port 8000: $FINAL_PORT_PROCESSES"
    [ ! -z "$FINAL_PYTHON_PROCESSES" ] && echo "   - Python simple_server.py: $FINAL_PYTHON_PROCESSES"
    [ ! -z "$FINAL_UVICORN_PROCESSES" ] && echo "   - uvicorn: $FINAL_UVICORN_PROCESSES"
    echo ""
    echo "💡 If processes are still running, you may need to manually kill them:"
    echo "   kill -9 <process_id>"
fi

echo ""
echo "============================================"
echo "🏁 Backend server stop script completed"

