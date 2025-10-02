# Brush 이벤트 수정 및 서버 스크립트 개선

**날짜**: 2025-09-30  
**작업**: ChartSelector 임포트 오류 수정 및 서버 관리 스크립트 개선

---

## 🐛 발견된 문제

### 1. ChartSelector 임포트 오류
**증상**: `/debug-brush` 페이지 접속 시 런타임 에러 발생
```
Element type is invalid: expected a string (for built-in components) 
or a class/function (for composite components) but got: undefined.
```

**원인**: 
- `chart-adapters/index.tsx`에서 `UniversalChart`를 export
- 하지만 `BrushDebugChart.tsx`와 `InfiniteScrollCandlestickChart.tsx`에서 `ChartSelector`를 import하려고 시도

**영향 파일**:
- `stock-trading-ui/src/components/trading/BrushDebugChart.tsx`
- `stock-trading-ui/src/components/trading/InfiniteScrollCandlestickChart.tsx`

---

## ✅ 수정 내용

### 1. BrushDebugChart.tsx 수정
```typescript
// ❌ Before
import { ChartSelector } from './chart-adapters';
<ChartSelector ... />

// ✅ After
import { UniversalChart } from './chart-adapters';
<UniversalChart ... />
```

### 2. InfiniteScrollCandlestickChart.tsx 수정
```typescript
// ❌ Before
import { ChartSelector } from './chart-adapters';
<ChartSelector ... />

// ✅ After
import { UniversalChart } from './chart-adapters';
<UniversalChart ... />
```

---

## 🔧 서버 스크립트 개선

### 1. stop-server.sh 생성
새로운 서버 중지 스크립트 생성:

**위치**: `stock-trading-ui/scripts/stop-server.sh`

**기능**:
- Next.js 프로세스 종료 (`pkill -f "next dev"`)
- 포트 9000 사용 프로세스 종료 (`fuser -k 9000/tcp`)
- 포트 해제 확인 및 검증
- 명확한 로그 출력

**사용법**:
```bash
# 직접 실행
./scripts/stop-server.sh

# npm 스크립트 사용
npm run stop
```

### 2. start-server.sh 개선
기존 서버 자동 종료 기능 추가:

**개선 사항**:
- 서버 시작 전 자동으로 `stop-server.sh` 호출
- 기존 서버 충돌 방지
- 주요 페이지 URL 안내 개선
- 한글 로그 메시지로 가독성 향상

**주요 페이지 안내**:
```
• 메인: http://localhost:9000
• Brush 디버그: http://localhost:9000/debug-brush
• 무한 스크롤: http://localhost:9000/test-infinite-scroll
• Test Chart: http://localhost:9000/test-chart
• Korean Trading: http://localhost:9000/korean-trading
```

### 3. package.json 스크립트 추가
```json
{
  "scripts": {
    "dev": "next dev --port 9000",
    "build": "next build",
    "start": "next start --port 9000",
    "lint": "eslint",
    "serve": "./scripts/start-server.sh",
    "server": "./scripts/start-server.sh",
    "stop": "./scripts/stop-server.sh"  // ✅ 새로 추가
  }
}
```

---

## 📋 사용 가이드

### 서버 시작
```bash
# 방법 1: npm 스크립트
npm run server

# 방법 2: 직접 실행
./scripts/start-server.sh
```

### 서버 중지
```bash
# 방법 1: npm 스크립트
npm run stop

# 방법 2: 직접 실행
./scripts/stop-server.sh

# 방법 3: Ctrl+C (포그라운드 실행 시)
```

### 서버 재시작
```bash
# start-server.sh는 자동으로 기존 서버 종료 후 재시작
npm run server
```

---

## 🧪 테스트 결과

### 1. ChartSelector 수정 확인
✅ `/debug-brush` 페이지 정상 로드  
✅ UniversalChart 컴포넌트 정상 렌더링  
✅ 런타임 에러 해결  

### 2. 서버 스크립트 테스트
✅ stop-server.sh 정상 동작 (포트 9000 해제)  
✅ start-server.sh 자동 재시작 기능 동작  
✅ npm run stop/server 명령어 정상 작동  

### 3. 서버 실행 로그
```
🚀 Next.js 개발 서버 시작...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 기존 서버 확인 및 종료...
🛑 Next.js 개발 서버 중지 중...
   ✅ 포트 9000 프로세스 종료 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 개발 서버 시작: http://localhost:9000
   ▲ Next.js 15.5.2
   - Local:        http://localhost:9000
   ✓ Ready in 2.4s
   ✓ Compiled /debug-brush in 4s
```

---

## 🔍 다음 단계

### 1. Brush 이벤트 테스트 (진행 예정)
- [ ] `/debug-brush` 페이지에서 Brush 컴포넌트 확인
- [ ] 왼쪽 드래그 시 onChange 이벤트 발생 확인
- [ ] startIndex < 20일 때 녹색 하이라이트 표시 확인
- [ ] 콘솔 로그 `🔥 Brush Event` 출력 확인

### 2. 무한 스크롤 통합 테스트
- [ ] `/test-infinite-scroll` 페이지에서 실제 데이터 로드 확인
- [ ] 왼쪽 드래그 시 이전 거래일 데이터 자동 로드 확인
- [ ] 캐시 hit/miss 동작 확인

### 3. 문서화
- [ ] 테스트 가이드 업데이트 (`docs/test/brush-event-test-guide.md`)
- [ ] 사용자 매뉴얼 작성

---

## 📝 참고 파일

**수정된 파일**:
- `stock-trading-ui/src/components/trading/BrushDebugChart.tsx`
- `stock-trading-ui/src/components/trading/InfiniteScrollCandlestickChart.tsx`
- `stock-trading-ui/scripts/start-server.sh`
- `stock-trading-ui/package.json`

**새로 생성된 파일**:
- `stock-trading-ui/scripts/stop-server.sh`

**관련 문서**:
- `docs/test/brush-event-test-guide.md` - Brush 이벤트 테스트 가이드
- `docs/arch/chart-drag-previous.0930.md` - 무한 스크롤 설계 문서
- `docs/impl/rechart.impl.drag.data.0930.md` - 구현 내역

---

**작성자**: Claude Code  
**최종 업데이트**: 2025-09-30
