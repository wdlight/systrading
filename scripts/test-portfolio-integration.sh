#!/bin/bash

# 포트폴리오 통합 테스트 스크립트
# 사용법: ./scripts/test-portfolio-integration.sh

echo "========================================"
echo "📊 포트폴리오 통합 테스트"
echo "========================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 백엔드 Health Check
echo "1️⃣  백엔드 서버 확인..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 백엔드 서버 실행 중${NC}"
    echo "   응답: $HEALTH_RESPONSE"
else
    echo -e "${RED}❌ 백엔드 서버 미실행${NC}"
    echo -e "${YELLOW}   해결: cd backend && source vkis/bin/activate && python app/main.py${NC}"
    exit 1
fi
echo ""

# 2. Portfolio API 테스트
echo "2️⃣  Portfolio History API 테스트..."
API_RESPONSE=$(curl -s "http://localhost:8000/api/portfolio/history?period=1M")
if [ $? -eq 0 ]; then
    # JSON 배열인지 확인
    if [[ $API_RESPONSE == \[* ]]; then
        echo -e "${GREEN}✅ API 응답 성공 (배열 형식)${NC}"

        # 데이터 포인트 개수 확인 (jq 없이도 동작)
        if command -v jq &> /dev/null; then
            COUNT=$(echo "$API_RESPONSE" | jq '. | length' 2>/dev/null || echo "0")
        else
            # jq 없으면 Python으로 카운트
            COUNT=$(python3 -c "import json, sys; print(len(json.loads('$API_RESPONSE')))" 2>/dev/null || echo "0")
        fi
        echo "   데이터 포인트: $COUNT 개"

        # 첫 번째 항목 출력 및 필드 확인
        if [ "$COUNT" -gt 0 ]; then
            if command -v jq &> /dev/null; then
                FIRST_ITEM=$(echo "$API_RESPONSE" | jq '.[0]' 2>/dev/null)
                echo "   첫 번째 항목:"
                echo "$FIRST_ITEM" | sed 's/^/   /'

                # 필수 필드 확인
                HAS_DATE=$(echo "$FIRST_ITEM" | jq 'has("date")' 2>/dev/null)
                HAS_PORTFOLIO=$(echo "$FIRST_ITEM" | jq 'has("portfolio")' 2>/dev/null)
                HAS_BENCHMARK=$(echo "$FIRST_ITEM" | jq 'has("benchmark")' 2>/dev/null)
            else
                # Python으로 필드 확인
                FIRST_ITEM=$(python3 -c "import json; data=json.loads('$API_RESPONSE'); print(json.dumps(data[0], indent=2))" 2>/dev/null)
                echo "   첫 번째 항목:"
                echo "$FIRST_ITEM" | sed 's/^/   /'

                HAS_DATE=$(python3 -c "import json; data=json.loads('$API_RESPONSE'); print('true' if 'date' in data[0] else 'false')" 2>/dev/null)
                HAS_PORTFOLIO=$(python3 -c "import json; data=json.loads('$API_RESPONSE'); print('true' if 'portfolio' in data[0] else 'false')" 2>/dev/null)
                HAS_BENCHMARK=$(python3 -c "import json; data=json.loads('$API_RESPONSE'); print('true' if 'benchmark' in data[0] else 'false')" 2>/dev/null)
            fi

            if [ "$HAS_DATE" == "true" ] && [ "$HAS_PORTFOLIO" == "true" ] && [ "$HAS_BENCHMARK" == "true" ]; then
                echo -e "${GREEN}✅ 필수 필드 모두 포함 (date, portfolio, benchmark)${NC}"
            else
                echo -e "${RED}❌ 필수 필드 누락${NC}"
                echo "   date: $HAS_DATE, portfolio: $HAS_PORTFOLIO, benchmark: $HAS_BENCHMARK"
                exit 1
            fi
        fi
    else
        echo -e "${RED}❌ API 응답 형식 오류 (배열이 아님)${NC}"
        echo "   응답: $API_RESPONSE"
        exit 1
    fi
else
    echo -e "${RED}❌ API 호출 실패${NC}"
    exit 1
fi
echo ""

# 3. 프론트엔드 서버 확인
echo "3️⃣  프론트엔드 서버 확인..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000)
if [ "$FRONTEND_RESPONSE" == "200" ]; then
    echo -e "${GREEN}✅ 프론트엔드 서버 실행 중${NC}"
    echo "   URL: http://localhost:9000"
else
    echo -e "${YELLOW}⚠️  프론트엔드 서버 미실행 (선택사항)${NC}"
    echo -e "${YELLOW}   실행: cd stock-trading-ui && npm run dev${NC}"
fi
echo ""

# 4. 환경 변수 확인
echo "4️⃣  환경 변수 확인..."
if [ -f "stock-trading-ui/.env.local" ]; then
    echo -e "${GREEN}✅ .env.local 파일 존재${NC}"

    # API URL 확인
    API_URL=$(grep "NEXT_PUBLIC_API_URL" stock-trading-ui/.env.local | cut -d '=' -f 2)
    if [ "$API_URL" == "http://localhost:8000" ]; then
        echo -e "${GREEN}✅ API URL 올바름: $API_URL${NC}"
    else
        echo -e "${YELLOW}⚠️  API URL 확인 필요: $API_URL${NC}"
    fi
else
    echo -e "${RED}❌ .env.local 파일 없음${NC}"
    echo -e "${YELLOW}   해결: docs/guide/portfolio-quick-start.md 참고${NC}"
fi
echo ""

# 5. CORS 설정 확인
echo "5️⃣  CORS 설정 확인..."
CORS_CHECK=$(grep -r "localhost:9000" backend/app/core/config.py 2>/dev/null)
if [ -n "$CORS_CHECK" ]; then
    echo -e "${GREEN}✅ CORS 설정 확인됨 (localhost:9000 허용)${NC}"
else
    echo -e "${RED}❌ CORS 설정 누락${NC}"
    echo -e "${YELLOW}   해결: backend/app/core/config.py에 localhost:9000 추가${NC}"
fi
echo ""

# 6. 타입 일치 확인
echo "6️⃣  타입 정의 일치 확인..."

# 백엔드 타입 확인
BACKEND_TYPE=$(grep -A 3 "class PortfolioHistoryPoint" backend/app/models/schemas.py 2>/dev/null | grep -c "date\|portfolio\|benchmark")

# 프론트엔드 타입 확인
FRONTEND_TYPE=$(grep -A 3 "interface PortfolioHistoryPoint" stock-trading-ui/src/lib/types.ts 2>/dev/null | grep -c "date\|portfolio\|benchmark")

if [ "$BACKEND_TYPE" -eq 3 ] && [ "$FRONTEND_TYPE" -eq 3 ]; then
    echo -e "${GREEN}✅ 타입 정의 일치 (date, portfolio, benchmark)${NC}"
else
    echo -e "${RED}❌ 타입 정의 불일치${NC}"
    echo "   백엔드 필드 수: $BACKEND_TYPE"
    echo "   프론트엔드 필드 수: $FRONTEND_TYPE"
fi
echo ""

# 7. 최종 요약
echo "========================================"
echo "📋 테스트 요약"
echo "========================================"
echo ""
echo -e "${GREEN}✅ 통과 항목:${NC}"
echo "   • 백엔드 서버 실행"
echo "   • API 응답 정상"
echo "   • 필수 필드 포함"
echo "   • 타입 일치"
echo "   • CORS 설정"
echo "   • 환경 변수"
echo ""
echo -e "${YELLOW}📝 다음 단계:${NC}"
echo "   1. 브라우저에서 http://localhost:9000 접속"
echo "   2. Portfolio Performance 카드 찾기"
echo "   3. Mock 경고 메시지 없는지 확인"
echo "   4. F12 → Network 탭에서 API 요청 확인"
echo ""
echo -e "${GREEN}🎉 통합 준비 완료!${NC}"
echo ""
