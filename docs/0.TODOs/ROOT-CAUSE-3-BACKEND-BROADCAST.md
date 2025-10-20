# 🚨 근본 원인 #3: Backend 분봉 브로드캐스트 문제

**발견 시각**: 2025-10-20 09:54
**심각도**: 🔴 **CRITICAL** - 분봉 데이터 미전송

---

## 🔍 문제 현상

### WebSocket 테스트 결과
```bash
node test-websocket-simple.js
```

**수신된 메시지:**
- ✅ `orderbook_update`: 정상 수신 (2초마다)
- ❌ `minute_candle_update`: **0개 수신**
- ❌ `minute_candle_finalize`: **0개 수신**

**통계 (2분간 테스트):**
```
총 메시지: 400개
UPDATE: 0개
FINALIZE: 0개
기타: 400개 (모두 orderbook_update)
```

---

## 🔬 근본 원인 분석

### 파일: `backend/app/services/realtime_service.py`

#### 문제 1: 장 시간 체크 누락 가능성

**Line 423-505: `_handle_tick_data` 함수**

```python
async def _handle_tick_data(self, message: Dict[str, Any]):
    """체결 데이터 처리 및 분봉 집계"""
    try:
        data = message.get("data", {})
        stock_code = message.get("stock_code") or data.get("stock_code")

        if not stock_code:
            return

        price = float(data.get("price", 0) or 0)
        if price <= 0:
            return

        executed_time = data.get("executed_time")
        if not executed_time:
            return

        # ❌ 장 시간 체크가 없음!
        # 호가 데이터(_handle_hoga_data)에는 있지만 체결 데이터에는 없음

        # 분봉 상태 갱신 로직...
        await self._broadcast_minute_snapshot(stock_code, state)
```

**Line 301-333: `_handle_hoga_data` 비교 (장 시간 체크 존재)**

```python
async def _handle_hoga_data(self, message: Dict[str, Any]):
    """실시간 호가 데이터 처리"""
    # ...

    # ✅ 장 시간 체크 존재
    from app.utils.trading_hours import TradingHoursManager
    from datetime import datetime
    if not TradingHoursManager.is_trading_hours(datetime.now()):
        logger.debug(f"장 시간 외 호가 데이터 무시: {stock_code}")
        return

    # 캐시 저장 및 브로드캐스트...
```

**결론**: 체결 데이터 처리 함수에 장 시간 체크가 없어서, 장 시간 외에도 처리되지만 실제 체결 데이터가 없어서 분봉이 생성되지 않음.

#### 문제 2: 브로드캐스트 대상 불일치

**Line 507-522: `_broadcast_minute_snapshot` 함수**

```python
async def _broadcast_minute_snapshot(self, stock_code: str, state: MinuteCandleState):
    """현재 진행 중인 분봉 스냅샷 브로드캐스트"""
    payload = {
        "type": "minute_candle_update",
        "stock_code": stock_code,
        "data": {
            "timestamp": state.minute_key,
            "open": state.open,
            "high": state.high,
            "low": state.low,
            "close": state.close,
            "volume": state.volume,
            "last_tick": state.last_tick_ts.isoformat(),
        }
    }
    # ❌ 모든 클라이언트에게 브로드캐스트 (구독 여부 무시)
    await self.connection_manager.broadcast(payload)
```

**Line 528-533: `_flush_closed_candle` 함수**

```python
async def _flush_closed_candle(self, stock_code: str, state: MinuteCandleState) -> None:
    """분 경계 통과 시 완료된 캔들을 확정"""
    candle = state.to_chart_candle()
    await self._enqueue_candle_for_persistence(stock_code, candle)

    # ❌ 모든 클라이언트에게 브로드캐스트
    await self.connection_manager.broadcast({
        "type": "minute_candle_finalize",
        "stock_code": stock_code,
        "data": candle.model_dump(),
    })
    self.minute_candle_state.pop(stock_code, None)
```

**비교: 호가 데이터는 구독자에게만 전송**

**Line 349-365: `_handle_hoga_data`의 브로드캐스트 (올바른 방법)**

```python
# ✅ 구독자에게만 브로드캐스트
await self.connection_manager.broadcast_to_stock_subscribers(
    stock_code,
    broadcast_message
)
```

---

## ✅ 해결 방법

### 수정 1: 체결 데이터 처리에 장 시간 체크 추가

**파일**: `backend/app/services/realtime_service.py:423-505`

```python
async def _handle_tick_data(self, message: Dict[str, Any]):
    """체결 데이터 처리 및 분봉 집계"""
    try:
        data = message.get("data", {})
        stock_code = message.get("stock_code") or data.get("stock_code")

        if not stock_code:
            return

        # 🔥 장 시간 체크 추가
        from app.utils.trading_hours import TradingHoursManager
        from datetime import datetime
        if not TradingHoursManager.is_trading_hours(datetime.now()):
            logger.debug(f"장 시간 외 체결 데이터 무시: {stock_code}")
            return

        price = float(data.get("price", 0) or 0)
        if price <= 0:
            return

        # ... 나머지 로직 동일
```

### 수정 2: 분봉 브로드캐스트를 구독자에게만 전송

**수정할 함수 1: `_broadcast_minute_snapshot`**

```python
async def _broadcast_minute_snapshot(self, stock_code: str, state: MinuteCandleState):
    """현재 진행 중인 분봉 스냅샷 브로드캐스트"""
    payload = {
        "type": "minute_candle_update",
        "stock_code": stock_code,
        "data": {
            "timestamp": state.minute_key,
            "open": state.open,
            "high": state.high,
            "low": state.low,
            "close": state.close,
            "volume": state.volume,
            "last_tick": state.last_tick_ts.isoformat(),
        }
    }
    # ✅ 구독자에게만 브로드캐스트
    await self.connection_manager.broadcast_to_stock_subscribers(
        stock_code,
        payload
    )
```

**수정할 함수 2: `_flush_closed_candle`**

```python
async def _flush_closed_candle(self, stock_code: str, state: MinuteCandleState) -> None:
    """분 경계 통과 시 완료된 캔들을 확정하고 persistence 큐로 전달"""
    candle = state.to_chart_candle()
    await self._enqueue_candle_for_persistence(stock_code, candle)

    finalize_message = {
        "type": "minute_candle_finalize",
        "stock_code": stock_code,
        "data": candle.model_dump(),
    }

    # ✅ 구독자에게만 브로드캐스트
    await self.connection_manager.broadcast_to_stock_subscribers(
        stock_code,
        finalize_message
    )

    self.minute_candle_state.pop(stock_code, None)
```

---

## 🚀 적용 방법

### 1단계: Backend 코드 수정

```bash
cd /home/wide/projects/systrading/backend

# 가상환경 활성화
source vkis/bin/activate

# realtime_service.py 수정 (위 변경사항 적용)
```

### 2단계: Backend 서버 재시작

```bash
# Backend 프로세스 종료
pkill -f "python.*main.py"

# 서버 재시작
cd /home/wide/projects/systrading/backend
source vkis/bin/activate
python app/main.py
```

### 3단계: 검증

```bash
# WebSocket 테스트 (1분 이상 대기)
cd /home/wide/projects/systrading
node test-websocket-simple.js
```

**예상 결과 (장 시간 중):**
```
✅ WebSocket 연결 성공!
📤 구독 요청 전송: 005930

🔄 [2025-10-20T09:46:30.123Z] MINUTE_CANDLE_UPDATE
   종목: 005930
   시간: 2025-10-20T09:46:00+09:00
   OHLCV: O=71700 H=71800 L=71600 C=71750 V=12345

🎉 [2025-10-20T09:47:00.456Z] MINUTE_CANDLE_FINALIZE ⭐⭐⭐
   종목: 005930
   시간: 2025-10-20T09:46:00+09:00
   OHLCV: O=71700 H=71900 L=71600 C=71800 V=98765
   ✅ 이 분봉이 완성되어 캐시에 저장되었어야 합니다!
```

---

## 🔬 추가 조사 필요 사항

### 장 시간 확인

**현재 시각**: 2025-10-20 09:54 (KST 기준 아침 9시 54분)

**장 시간:**
- 정규장: 09:00 - 15:30
- 장 전 시간외: 08:30 - 09:00
- 장 후 시간외: 15:30 - 16:00

**현재 상태**: ✅ **정규장 시간** (체결 데이터 생성 가능)

### 체결 데이터 수신 확인

Backend 로그에서 확인:
```bash
tail -100 /home/wide/projects/systrading/backend/logs/app.log | grep "체결"
```

**예상 로그:**
```
2025-10-20 09:46:15 | INFO | 📊 체결 데이터 처리: 005930, 가격=71750, 거래량=100
```

**만약 체결 로그가 없다면:**
- WebSocket 연결이 끊김
- 한국투자증권 API 연결 문제
- 실제 체결 데이터가 발생하지 않음 (거래량 없음)

---

## 📊 검증 기준

### ✅ 성공 지표 (장 시간 중)

- [ ] Backend 로그에 "체결 데이터 처리" 로그 확인
- [ ] WebSocket 테스트에서 `minute_candle_update` 수신
- [ ] WebSocket 테스트에서 `minute_candle_finalize` 수신 (1분 경과 후)
- [ ] Frontend Console에 "분봉 업데이트 메시지 수신" 로그
- [ ] Frontend Console에 "분봉 완성 메시지 수신" 로그
- [ ] 차트에 새 분봉 자동 표시

### ⚠️ 장 시간 외 확인

장 시간 외에는 체결 데이터가 발생하지 않으므로:
- `minute_candle_update` 메시지 없음 (정상)
- `minute_candle_finalize` 메시지 없음 (정상)
- `orderbook_update`만 수신 (정상)

**테스트는 장 시간 중에 진행해야 합니다!**

---

## 🎯 다음 단계

1. **Backend 코드 수정** (위 2가지 수정사항 적용)
2. **Backend 서버 재시작**
3. **장 시간 확인** (09:00-15:30 KST)
4. **WebSocket 테스트 실행** (최소 1분 대기)
5. **Frontend 브라우저 테스트**

**중요**: 현재 시각이 장 시간 외라면, 내일 장 시작 후 테스트해야 합니다!

---

**문제 요약**: Backend는 분봉 데이터를 생성하고 있지만, 모든 클라이언트에게 브로드캐스트하지 않고 구독자에게만 전송해야 하며, 장 시간 체크도 추가해야 합니다.
