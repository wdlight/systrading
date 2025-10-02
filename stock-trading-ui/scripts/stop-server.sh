#!/bin/bash

# Next.js 개발 서버 중지 스크립트
# 포트 9000에서 실행 중인 서버를 안전하게 종료합니다

PORT=9000
PROJECT_DIR="/home/wide/projects/systrading/stock-trading-ui"

echo "🛑 Next.js 개발 서버 중지 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_DIR" || exit 1

# 1. Next.js 프로세스 종료 (프로세스 이름으로)
echo "📍 Next.js 프로세스 검색 및 종료..."
pkill -9 -f "next dev" 2>/dev/null && echo "   ✅ Next.js 프로세스 종료 완료" || echo "   ℹ️  실행 중인 Next.js 프로세스 없음"

# 2. 포트 9000 사용 중인 프로세스 종료 (fuser 사용)
echo "📍 포트 $PORT 확인 및 종료..."
if fuser -k $PORT/tcp 2>/dev/null; then
    echo "   ✅ 포트 $PORT 프로세스 종료 완료"
else
    echo "   ℹ️  포트 $PORT 사용 중인 프로세스 없음"
fi

# 3. 잠시 대기 (포트 해제 확인)
sleep 2

# 4. 최종 확인
PID=$(lsof -ti:$PORT 2>/dev/null)
if [ -n "$PID" ]; then
    echo "   ⚠️  포트 $PORT 여전히 사용 중 (PID: $PID)"
    echo "   수동 종료 필요: kill -9 $PID"
    exit 1
else
    echo "   ✅ 포트 $PORT 정상 해제됨"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 서버 중지 완료!"
echo ""
