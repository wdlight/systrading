#!/bin/bash

# Frontend Development Server Startup Script
# 자동으로 기존 서버를 종료하고 새로 시작합니다

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Next.js 개발 서버 시작..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. 기존 서버 자동 종료
if [ -f "$SCRIPT_DIR/stop-server.sh" ]; then
    echo "📍 기존 서버 확인 및 종료..."
    bash "$SCRIPT_DIR/stop-server.sh" 2>/dev/null || true
else
    # stop-server.sh가 없는 경우 직접 종료
    echo "🔄 기존 개발 서버 확인 중..."
    if pgrep -f "next dev" > /dev/null; then
        echo "⏹️  기존 Next.js 서버 종료 중..."
        pkill -9 -f "next dev" || true
        sleep 2
    fi

    if lsof -ti:9000 > /dev/null 2>&1; then
        echo "⏹️  포트 9000 프로세스 종료 중..."
        lsof -ti:9000 | xargs kill -9 || true
        sleep 1
    fi
fi

# Navigate to project directory
cd "$PROJECT_DIR"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start development server on port 9000
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 개발 서버 시작: http://localhost:9000"
echo ""
echo "📌 주요 페이지:"
echo "   • 메인: http://localhost:9000"
echo "   • Brush 디버그: http://localhost:9000/debug-brush"
echo "   • 무한 스크롤: http://localhost:9000/test-infinite-scroll"
echo "   • Test Chart: http://localhost:9000/test-chart"
echo "   • Korean Trading: http://localhost:9000/korean-trading"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "ℹ️  서버 중지: Ctrl+C 또는 ./scripts/stop-server.sh"
echo ""

# Start the development server
npm run dev

echo "✅ 개발 서버 종료됨"
