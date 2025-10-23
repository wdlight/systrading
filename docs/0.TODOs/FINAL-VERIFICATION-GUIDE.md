# ✅ 실시간 데이터 업데이트 최종 검증 가이드

**작성 시각**: 2025-10-20 10:00
**상태**: 🟢 **모든 코드 수정 완료 - 검증 대기**

---

## 📋 수행된 모든 수정 사항

### 1️⃣ Frontend 수정 (완료)

#### ✅ useRealtimeMinuteCandles.ts - 종목 구독 요청 추가
**파일**: `stock-trading-ui/src/hooks/useRealtimeMinuteCandles.ts`

**문제**: WebSocket 연결만 하고 종목 구독 요청을 전송하지 않음
**해결**: 종목 구독/구독 해제 로직 추가

```typescript
// 구독 요청 전송
wsManager.send({
  type: 'subscribe',
  stock_code: stockCode
});
wsManager.addPendingSubscription(stockCode);

// 구독 해제 (cleanup)
wsManager.send({
  type: 'unsubscribe',
  stock_code: stockCode
});
wsManager.removePendingSubscription(stockCode);
```

#### ✅ RealtimeCandlestickChart.tsx - React.memo 제거
**파일**: `stock-trading-ui/src/components/trading/RealtimeCandlestickChart.tsx`

**문제**: React.memo가 props만 비교하여 내부 hook 상태 변경 무시
**해결**: React.memo 제거하여 정상 리렌더링 허용

---

### 2️⃣ Backend 수정 (완료)

#### ✅ realtime_service.py - 장 시간 체크 추가
**파일**: `backend/app/services/realtime_service.py:423-436`

**문제**: 장 시간 외에도 체결 데이터 처리 시도 (실제 데이터 없음)
**해결**: 장 시간 체크 추가

```python
# 🔥 장 시간 체크 추가
from app.utils.trading_hours import TradingHoursManager
if not TradingHoursManager.is_trading_hours(datetime.now()):
    logger.debug(f"장 시간 외 체결 데이터 무시: {stock_code}")
    return
```

#### ✅ realtime_service.py - 분봉 브로드캐스트 구독자 전용 변경
**파일**: `backend/app/services/realtime_service.py:513-532, 534-551`

**문제**: 모든 클라이언트에게 브로드캐스트 (비효율적)
**해결**: 구독자에게만 전송

```python
# ✅ minute_candle_update - 구독자에게만
await self.connection_manager.broadcast_to_stock_subscribers(
    stock_code,
    payload
)

# ✅ minute_candle_finalize - 구독자에게만
await self.connection_manager.broadcast_to_stock_subscribers(
    stock_code,
    finalize_message
)
```

---

## 🔬 Frontend 코드 검증 결과

### ✅ useOrderBook 훅 (정상)
**파일**: `stock-trading-ui/src/hooks/useOrderBook.ts`

**확인 사항**:
- Line 130-135: WebSocket 구독 요청 전송 ✅
- Line 164-169: WebSocket 구독 해제 전송 ✅
- Line 198-227: WebSocket 메시지 리스너 등록 ✅
- Line 217-218: 디버그 로그 출력 ✅

**예상 Console 로그**:
```
✅ 호가 구독 시작: 005930
📊 호가 데이터 업데이트: 005930
🔥 실시간 WebSocket 업데이트 - 현재가: 71700, 매도1: 71800, 매수1: 71600
```

### ✅ WebSocket Manager (정상)
**파일**: `stock-trading-ui/src/lib/websocket.ts`

**확인 사항**:
- Line 283-286: `orderbook_update` 메시지 처리 ✅
- Line 277-282: `minute_candle_update/finalize` 메시지 처리 ✅
- Line 308-324: `notifyListeners` 정상 동작 ✅
- Line 560-578: `subscribeToOrderBookUpdates` 정상 동작 ✅

**예상 Console 로그**:
```
🔍 WebSocket 메시지 수신: { type: 'orderbook_update', data: {...} }
📊 호가 업데이트 메시지 수신: {...}
🔔 notifyListeners 호출: orderbook_update, 리스너 수: 1
📤 리스너 실행: orderbook_update
```

### ✅ OrderBook 컴포넌트 (정상)
**파일**: `stock-trading-ui/src/components/trading/OrderBook.tsx`

**확인 사항**:
- Line 15-18: `useOrderBook` 훅 사용 ✅
- Line 36-54: 장 시간 체크 ✅
- Line 106-202: 호가 데이터 표시 ✅

---

## 🎯 검증 절차

### 준비 단계

#### 1. 현재 장 시간 확인
```bash
date "+%H:%M"
```

**장 시간**: 09:00 - 15:30 (KST)
- 장 시간 **중**: 실시간 데이터 수신 가능 ✅
- 장 시간 **외**: "장 시간 외" 메시지 표시 (정상)

#### 2. Backend 서버 재시작 (선택사항)
```bash
# Backend 디렉토리로 이동
cd /home/wide/projects/systrading/backend

# 기존 프로세스 종료
pkill -f "python.*main.py"

# 가상환경 활성화 후 서버 시작
source vkis/bin/activate
python app/main.py
```

**Note**: 현재 Backend 코드는 이미 수정되었으므로, 서버가 실행 중이라면 재시작이 필요합니다.

#### 3. Frontend 서버 상태 확인
```bash
# 서버 실행 중인지 확인
curl http://localhost:9000

# 응답이 없으면 서버 시작
cd /home/wide/projects/systrading/stock-trading-ui
npm run dev
```

---

### 검증 단계 1: WebSocket 연결 및 메시지 수신 확인

#### Browser Console 열기
1. http://localhost:9000/trading 접속
2. **F12** → **Console** 탭

#### 예상 로그 (순서대로)
```
🔧 WebSocketManager 생성됨: ws://localhost:8000/ws
🚀 WebSocket 연결 시도: ws://localhost:8000/ws
📡 WebSocket 객체 생성됨
✅ WebSocket 연결됨

🔍 WebSocket 메시지 수신: { type: 'connection_status', ... }
📝 [WS] orderbook_update 리스너 등록

// 종목 선택 시 (삼성전자 005930)
✅ [useRealtimeMinuteCandles] 분봉 구독 시작: 005930
📤 [useRealtimeMinuteCandles] 종목 구독 요청 전송: 005930
✅ [useRealtimeMinuteCandles] 종목 구독 완료: 005930

✅ 호가 구독 시작: 005930
📝 구독 대기 목록에 추가: 005930
```

**✅ 성공 기준**: 위 로그가 모두 나타나야 함

**❌ 실패 시**: "구독 완료" 로그가 없으면 Frontend 코드 미반영

---

### 검증 단계 2: 실시간 호가 데이터 수신 확인 (장 시간 중)

#### 예상 Console 로그 (2초마다 반복)
```
🔍 WebSocket 메시지 수신: { type: 'orderbook_update', stock_code: '005930', data: {...} }
📊 호가 업데이트 메시지 수신: { stock_code: '005930', data: {...} }
🔔 notifyListeners 호출: orderbook_update, 리스너 수: 1
📤 리스너 실행: orderbook_update
📊 호가 데이터 수신: 005930 { stock_code: '005930', data: {...} }
📊 호가 데이터 업데이트: 005930 { ..., asks: [...], bids: [...], current_price: 71700, ... }
🔥 실시간 WebSocket 업데이트 - 현재가: 71700, 매도1: 71800, 매수1: 71600
```

#### UI 확인
- 왼쪽 호가창에 실시간 가격 업데이트 ✅
- 매도/매수 호가 수량 변경 ✅
- 현재가 실시간 갱신 ✅

**✅ 성공 기준**:
- Console 로그 2초마다 출력
- 호가창 UI 실시간 업데이트

**❌ 실패 시**:
- 로그만 나오고 UI 안 바뀜 → React 렌더링 문제
- 로그도 안 나옴 → Backend 브로드캐스트 문제

---

### 검증 단계 3: 실시간 분봉 데이터 수신 확인 (장 시간 중)

#### 예상 Console 로그 (체결 발생 시)
```
🔍 WebSocket 메시지 수신: { type: 'minute_candle_update', stock_code: '005930', data: {...} }
🔄 [UPDATE] 분봉 업데이트 메시지 수신: { stock_code: '005930', ... }
✅ [UPDATE] 분봉 업데이트 처리: 005930 2025-10-20T09:46:00+09:00
📊 [RealtimeCandlestickChart] 실시간 분봉 상태: {
  stockCode: '005930',
  currentCandle: '2025-10-20T09:46:30+09:00',
  finalizedCount: 0,
  baseDataLength: 90
}

🔄 [Chart] 차트 데이터 병합 시작: { baseLength: 90, finalizedLength: 0, currentCandle: '...' }
🔄 [Chart] 진행 중 분봉 병합: { currentMinute: '2025-10-20T09:46', lastMinute: '2025-10-20T09:45' }
✨ [Chart] 새 진행 중 분봉 추가: 2025-10-20T09:46:00+09:00
✅ [Chart] 최종 차트 데이터: 91개 분봉
```

#### 1분 경과 후 (분봉 완성 시)
```
🔍 WebSocket 메시지 수신: { type: 'minute_candle_finalize', stock_code: '005930', data: {...} }
🎉 [FINALIZE] 분봉 완성 메시지 수신: { stock_code: '005930', ... }
✅ [FINALIZE] 완성된 분봉 처리 시작: 005930 2025-10-20T09:46:00+09:00
📊 [FINALIZE] 생성된 ChartCandle: { timestamp: '2025-10-20T09:46:00+09:00', ... }
✅ [FINALIZE] finalizedCandles 배열에 추가: 2025-10-20T09:46:00+09:00 (기존 0개 → 1개)
✅ [FINALIZE] currentCandle 초기화 완료

📥 [Chart] 1개 완성된 분봉 병합 중...
✨ [Chart] 새 분봉 추가: 2025-10-20T09:46:00+09:00
✅ [Chart] 최종 차트 데이터: 91개 분봉
```

#### UI 확인
- 차트에 새 분봉 추가 ✅
- 진행 중인 분봉 실시간 갱신 (OHLC 변화) ✅
- 1분 경과 시 분봉 확정 및 새 분봉 시작 ✅

**✅ 성공 기준**:
- `minute_candle_update` 메시지 수신
- `minute_candle_finalize` 메시지 수신 (1분 후)
- 차트 자동 업데이트

**❌ 실패 시**:
- UPDATE 메시지 없음 → Backend에서 체결 데이터 미수신 (장 시간 외 또는 거래 없음)
- UPDATE 있지만 FINALIZE 없음 → 1분 대기 필요
- 로그만 있고 차트 안 바뀜 → Recharts 렌더링 문제

---

## 🚨 장 시간 외 예상 동작

### 현재 시각이 09:00-15:30 범위 밖일 경우

#### Backend 동작
```python
# 체결 데이터 무시
logger.debug(f"장 시간 외 체결 데이터 무시: {stock_code}")
return

# 호가 데이터도 무시
logger.debug(f"장 시간 외 호가 데이터 무시: {stock_code}")
return
```

#### Frontend 동작
- 호가창: "장 시간 외입니다. 다음 거래일 09:00에 다시 시작됩니다." 표시
- 차트: 과거 데이터만 표시 (실시간 업데이트 없음)
- WebSocket: 연결 유지하지만 실시간 데이터 없음

**이것은 정상 동작입니다!**

---

## 🔍 문제 해결

### 문제 1: "종목 구독 완료" 로그가 안 나옴

**원인**: Frontend 코드가 Hot Reload로 반영 안됨

**해결**:
```bash
cd /home/wide/projects/systrading/stock-trading-ui
rm -rf .next
pkill -f "next dev"
npm run dev
```

**브라우저**: Ctrl+Shift+R (강력 새로고침)

---

### 문제 2: 호가/분봉 메시지가 안 옴

**원인 A**: 장 시간 외
- **확인**: `date "+%H:%M"` 실행 → 09:00-15:30 범위 확인
- **해결**: 장 시간 중에 다시 테스트

**원인 B**: Backend 수정사항 미반영
- **확인**: Backend 로그에 "장 시간 체크 추가" 코드 반영 여부
- **해결**: Backend 서버 재시작

```bash
cd /home/wide/projects/systrading/backend
source vkis/bin/activate
pkill -f "python.*main.py"
python app/main.py
```

**원인 C**: WebSocket 연결 끊김
- **확인**: Browser Console에 "WebSocket 연결됨" 확인
- **해결**: 페이지 새로고침 또는 Backend 재시작

---

### 문제 3: 로그는 나오는데 UI가 안 바뀜

**원인 A**: React 컴포넌트 메모이제이션
- **확인**: `React.memo` 완전 제거 여부 확인
- **해결**: Frontend 코드 재확인 및 재시작

**원인 B**: useMemo 의존성 문제
- **확인**: `finalChartData` useMemo 의존성 배열 확인
- **해결**: 의존성 배열에 `currentCandle`, `finalizedCandles` 포함 확인

**원인 C**: Browser 캐시
- **해결**: Ctrl+Shift+R (강력 새로고침)

---

## 📊 최종 체크리스트

### Backend (수정 완료 ✅)
- [x] realtime_service.py - 장 시간 체크 추가
- [x] realtime_service.py - 분봉 브로드캐스트 구독자 전용 변경
- [ ] Backend 서버 재시작 필요 (수정사항 반영 위해)

### Frontend (수정 완료 ✅)
- [x] useRealtimeMinuteCandles.ts - 종목 구독 요청 추가
- [x] RealtimeCandlestickChart.tsx - React.memo 제거
- [ ] Frontend 서버 재시작 권장 (캐시 클리어)

### 검증 필요
- [ ] Browser Console에서 구독 로그 확인
- [ ] 호가 데이터 실시간 수신 확인 (장 시간 중)
- [ ] 분봉 데이터 실시간 수신 확인 (장 시간 중)
- [ ] UI 실시간 업데이트 확인

---

## 🎉 기대 결과

### 장 시간 중 (09:00-15:30)
1. ✅ WebSocket 연결 성공
2. ✅ 호가 데이터 2초마다 자동 갱신
3. ✅ 분봉 데이터 체결 시마다 갱신
4. ✅ 1분 경과 시 분봉 완성 및 캐시 저장
5. ✅ 차트/호가창 실시간 UI 반영

### 장 시간 외
1. ✅ WebSocket 연결 유지
2. ✅ "장 시간 외" 메시지 표시
3. ✅ 과거 데이터만 표시 (실시간 없음)

---

**모든 코드 수정이 완료되었습니다. 이제 서버를 재시작하고 위 검증 절차를 따라 테스트하시면 됩니다!** 🚀
