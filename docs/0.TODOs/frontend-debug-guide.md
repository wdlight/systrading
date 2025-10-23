# 🔍 Frontend 분봉 실시간 업데이트 디버깅 가이드

**작성일**: 2025-10-20
**목적**: Frontend에서 분봉 실시간 업데이트가 안 되는 문제 진단

---

## 📋 현재 상황

### ✅ Backend (정상 작동)
- WebSocket 데이터 수신: **정상**
- 브로드캐스트 전송: **정상**
- Persistence handler 연결: **정상** (main.py:173-174)

### ❓ Frontend (업데이트 안 됨)
- 원인을 파악하기 위해 디버깅 로그 추가 완료

---

## 🚀 테스트 방법

### 1단계: Frontend 재시작

```bash
cd /home/wide/projects/systrading/stock-trading-ui

# 서버 중지 (기존 프로세스 종료)
pkill -f "next dev"

# 서버 재시작
npm run dev
# 또는
./scripts/start-server.sh
```

### 2단계: 브라우저 접속 및 DevTools 열기

1. 브라우저에서 http://localhost:9000/trading 접속
2. **F12** 또는 **우클릭 → 검사** → **Console** 탭 열기
3. **종목 선택** (예: 삼성전자 005930)
4. **분봉 차트** 선택 (1분 타임프레임)

### 3단계: 로그 확인

#### ✅ 정상 로그 (예상)

```
🔄 [useRealtimeMinuteCandles] 훅 초기화: stockCode=005930, enabled=true
✅ [useRealtimeMinuteCandles] 분봉 구독 시작: 005930
📝 [WS] minute_candle_update 리스너 등록
📝 [WS] minute_candle_finalize 리스너 등록
📊 [RealtimeCandlestickChart] 실시간 분봉 상태: {...}

// 1분 경과 후
🔍 WebSocket 메시지 수신: { type: 'minute_candle_finalize', ... }
📨 [WS] minute_candle_finalize 리스너 실행: {...}
🎉 [FINALIZE] 분봉 완성 메시지 수신: {...}
✅ [FINALIZE] 완성된 분봉 처리 시작: 005930 2025-10-20T14:35:00+09:00
📊 [FINALIZE] 생성된 ChartCandle: {...}
✅ [FINALIZE] finalizedCandles 배열에 추가: ... (기존 0개 → 1개)
✅ [FINALIZE] currentCandle 초기화 완료

🔄 [Chart] 차트 데이터 병합 시작: {...}
📥 [Chart] 1개 완성된 분봉 병합 중...
✨ [Chart] 새 분봉 추가: 2025-10-20T14:35:00+09:00
✅ [Chart] 완성된 분봉 병합 완료, 총 91개
✅ [Chart] 최종 차트 데이터: 91개 분봉
```

#### ❌ 문제 시나리오별 로그

##### 시나리오 A: WebSocket 메시지 자체가 안 옴
```
🔍 WebSocket 메시지 수신: { type: 'minute_candle_update', ... }  ← update만 오고
// finalize 메시지 없음 ❌
```

**원인**: Backend 브로드캐스트 문제 또는 WebSocket 연결 끊김
**해결**: Backend 로그 확인 (`backend/logs/app.log`)

---

##### 시나리오 B: 메시지는 오지만 리스너 미등록
```
🔍 WebSocket 메시지 수신: { type: 'minute_candle_finalize', ... }  ← 메시지는 옴
⚠️ minute_candle_finalize에 대한 리스너가 없습니다  ← 리스너 없음 ❌
```

**원인**: `useRealtimeMinuteCandles` 훅이 마운트 안 됨 또는 enabled=false
**해결**:
1. Console에서 `🔄 [useRealtimeMinuteCandles] 훅 초기화` 로그 확인
2. `enabled` 값 확인 (false면 리스너 등록 안 됨)

---

##### 시나리오 C: 리스너는 있지만 콜백 실행 안 됨
```
🔍 WebSocket 메시지 수신: { type: 'minute_candle_finalize', ... }
🔔 notifyListeners 호출: minute_candle_finalize, 리스너 수: 1
// 📨 [WS] minute_candle_finalize 리스너 실행 로그 없음 ❌
```

**원인**: `notifyListeners` 내부 오류 또는 메시지 타입 불일치
**해결**:
1. `WS_MESSAGE_TYPES.MINUTE_CANDLE_FINALIZE` 값 확인
2. Backend 메시지 타입과 일치하는지 확인

---

##### 시나리오 D: 콜백은 실행되지만 종목 코드 불일치
```
📨 [WS] minute_candle_finalize 리스너 실행: {...}
🎉 [FINALIZE] 분봉 완성 메시지 수신: {...}
⚠️ [FINALIZE] 종목 코드 불일치: 000660 !== 005930  ← 종목 코드 다름 ❌
```

**원인**: 차트 컴포넌트의 `stockCode` prop이 잘못 전달됨
**해결**:
1. `📊 [RealtimeCandlestickChart] 실시간 분봉 상태` 로그에서 stockCode 확인
2. 부모 컴포넌트에서 올바른 종목 코드 전달하는지 확인

---

##### 시나리오 E: 상태는 업데이트되지만 차트 렌더링 안 됨
```
✅ [FINALIZE] finalizedCandles 배열에 추가: ... (기존 0개 → 1개)
// 🔄 [Chart] 차트 데이터 병합 시작 로그 없음 ❌
```

**원인**: `useMemo` 의존성 배열 문제 또는 React 렌더링 문제
**해결**:
1. React DevTools로 `finalizedCandles` 상태 직접 확인
2. 컴포넌트 re-render 트리거되는지 확인

---

## 🔧 추가 디버깅 명령어

### Backend 로그 확인
```bash
cd /home/wide/projects/systrading/backend

# 실시간 로그 모니터링 (finalize 메시지만)
tail -f logs/app.log | grep -E "finalize|Finalize|FINALIZE"

# persistence 로그 확인
tail -f logs/app.log | grep "Persistence"
```

### 브라우저 Console에서 WebSocket 상태 확인
```javascript
// WebSocket 연결 상태 확인
wsManager.isConnected()  // true여야 함

// 리스너 등록 상태 확인
wsManager.listeners.get('minute_candle_finalize')?.size  // 1 이상이어야 함

// 수동 메시지 시뮬레이션 (테스트용)
wsManager.handleMessage({
  type: 'minute_candle_finalize',
  stock_code: '005930',
  data: {
    timestamp: '2025-10-20T14:35:00+09:00',
    open: 62000,
    high: 62200,
    low: 61900,
    close: 62100,
    volume: 1500
  }
})
```

---

## 📊 예상 결과

### 성공 시
- Console에 모든 단계별 로그 출력
- `finalizedCandles` 배열에 분봉 추가
- 차트에 새 분봉 자동 표시
- REST API 호출 없음 (Network 탭 확인)

### 실패 시
- 위 시나리오별 로그 패턴 확인
- 해당 시나리오의 해결 방법 적용

---

## 📝 디버깅 체크리스트

- [ ] Frontend 서버 재시작 완료
- [ ] 브라우저 DevTools Console 열림
- [ ] 종목 선택 및 분봉 차트 표시
- [ ] 1분 경과 대기
- [ ] 로그에서 finalize 메시지 수신 확인
- [ ] `finalizedCandles` 배열 업데이트 확인
- [ ] 차트 자동 업데이트 확인

---

## 🚨 긴급 연락처

문제가 계속되면:
1. **Console 로그 전체 복사** → Claude에게 공유
2. **Backend 로그 복사** → `logs/app.log` 마지막 100줄
3. **Network 탭 WebSocket 프레임** 확인

---

**다음 단계**: 위 테스트 완료 후 결과를 공유해주시면 정확한 원인 파악 및 수정 진행하겠습니다!
