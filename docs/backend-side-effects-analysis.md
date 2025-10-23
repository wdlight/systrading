# Backend Side Effects Analysis - Real-time Minute Candle Update

**Document ID**: `backend-side-effects-analysis.md`
**Date**: 2025-10-21
**Author**: Claude Code Analysis
**Status**: 🔴 **HIGH PRIORITY REVIEW REQUIRED**

---

## Executive Summary

⚠️ **CRITICAL FINDINGS**: The plan in `1021.chart.rtupdate.plan.md.md` to connect `TradingService.update_minute_candle` as the persistence handler **IS ALREADY IMPLEMENTED** in `backend/app/main.py` (lines 127-174).

**Current Status**:
- ✅ Persistence handler: **CONNECTED** (line 173)
- ⚠️ Cache file locking: **NO LOCK MECHANISM**
- ⚠️ Performance impact: **NOT MEASURED**
- ⚠️ Error handling: **BASIC ONLY**

---

## 1. Current Implementation Analysis

### 1.1 Persistence Handler - **ALREADY ACTIVE**

**Location**: `backend/app/main.py:127-174`

```python
# TradingService 인스턴스 생성
trading_service = TradingService(korea_invest_service)

# Persistence 콜백 함수 정의
async def minute_persist_callback(stock_code: str, candle: ChartCandle):
    """WebSocket으로 완성된 분봉을 kordata/ 캐시에 저장"""
    try:
        target_date = datetime.fromisoformat(candle.timestamp)

        # 캐시 파일 업데이트
        success = await trading_service.update_minute_candle(
            stock_code=stock_code,
            target_date=target_date,
            candle_data=candle
        )

        if success:
            logger.info(f"✅ [Persistence] 분봉 캐시 저장 성공: {stock_code} {candle.timestamp}")
        else:
            logger.warning(f"⚠️ [Persistence] 분봉 저장 실패: {stock_code} {candle.timestamp}")

    except Exception as e:
        logger.error(f"❌ [Persistence] 분봉 저장 오류: {stock_code} {candle.timestamp} - {e}")

# RealtimeDataService에 핸들러 주입
realtime_service.set_minute_persist_handler(minute_persist_callback)
logger.info("🔗 [Startup] 분봉 Persistence Handler 연결 완료")
```

**⚠️ IMPLICATION**: The plan's "Phase 3" is ALREADY DONE. No additional work needed.

---

## 2. Backend-Specific Risks

### 2.1 🔴 **HIGH RISK**: File I/O Lock Contention

**Risk Level**: **HIGH**
**Impact**: Data corruption, partial writes, race conditions

#### Problem Analysis

**Current Flow (Every Minute)**:
```
1. WebSocket receives tick data → _handle_tick_data()
2. Minute boundary detected → _flush_closed_candle()
3. Enqueue to minute_finalize_queue (Line 566)
4. _minute_persistence_worker() processes queue
5. Calls minute_persist_callback()
6. TradingService.update_minute_candle()
7. ChartCacheService._load_from_cache() → Read JSON file
8. Modify candles list
9. ChartCacheService._save_to_cache() → Write JSON file
```

**Lock Mechanism**: ❌ **NONE**

**Code Evidence**:
```python
# chart_cache_service.py:173-198
def _save_to_cache(self, stock_code: str, date: datetime, candles: List[ChartCandle]):
    """캐시에 데이터 저장 - NO LOCKING!"""
    cache_file = self._get_cache_file_path(stock_code, date)

    try:
        data = [candle.model_dump() for candle in candles]

        # ⚠️ CRITICAL: No file lock before write!
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"캐시 저장 성공: {cache_file}, {len(candles)}개 캔들")

    except Exception as e:
        logger.error(f"캐시 저장 실패: {cache_file}, 오류: {e}")
```

**Concurrent Access Scenarios**:
1. **WebSocket persistence** writes at 09:01:00
2. **REST API read** (`/api/chart/minute`) reads at 09:01:00.5
3. **Race condition**: Partial read during write

**Potential Failures**:
- Corrupted JSON (incomplete write)
- Empty candles list (read during write)
- Chart data mismatch (old + new data mixed)

---

### 2.2 🔴 **HIGH RISK**: File I/O Performance

**Risk Level**: **HIGH**
**Impact**: Backend latency, WebSocket delays

#### Performance Bottleneck

**Current Implementation**:
```python
# trading_service.py:481-538
async def update_minute_candle(
    self,
    stock_code: str,
    target_date: datetime,
    candle_data: ChartCandle
) -> bool:
    try:
        # 1. FULL FILE READ (391 candles × JSON parsing)
        cached_candles = self.chart_cache_service._load_from_cache(stock_code, target_date)

        # 2. LINEAR SEARCH (O(n) - up to 391 iterations)
        for i, candle in enumerate(cached_candles):
            if candle.timestamp == candle_timestamp:
                cached_candles[i] = candle_data
                updated = True
                break

        # 3. FULL FILE WRITE (391 candles × JSON serialization)
        self.chart_cache_service._save_to_cache(stock_code, target_date, cached_candles)

        return True
```

**Per-Minute Cost** (5 active stocks):
```
Read:  5 stocks × 391 candles × 150 bytes = 292 KB
Write: 5 stocks × 391 candles × 150 bytes = 292 KB
Total: 584 KB/min file I/O
```

**Annual Cost** (Trading hours: 6.5h/day × 250 days):
```
Minutes per year: 6.5h × 60min × 250days = 97,500 min
Total I/O: 97,500 × 584 KB ≈ 55.7 GB/year
```

**Disk Wear**: SSD write cycles consumed by continuous JSON updates

---

### 2.3 🟡 **MEDIUM RISK**: WebSocket Broadcast Overhead

**Risk Level**: **MEDIUM**
**Impact**: Network bandwidth, client processing

#### Broadcast Analysis

**Current Implementation** (`realtime_service.py:548-561`):
```python
async def _flush_closed_candle(self, stock_code: str, state: MinuteCandleState) -> None:
    """분 경계 통과 시 완료된 캔들을 확정하고 persistence 큐로 전달"""
    candle = state.to_chart_candle()
    await self._enqueue_candle_for_persistence(stock_code, candle)

    finalize_message = {
        "type": "minute_candle_finalize",
        "stock_code": stock_code,
        "data": candle.model_dump(),  # Full OHLCV data
    }

    # ⚠️ Broadcast to ALL connected clients (no stock_code filtering)
    await self.connection_manager.broadcast(finalize_message)

    self.minute_candle_state.pop(stock_code, None)
```

**Overhead Per Minute** (10 clients, 5 active stocks):
```
Payload size: ~200 bytes (JSON)
Broadcasts per minute: 5 stocks
Total: 5 × 200 bytes × 10 clients = 10 KB/min
```

**Annual Cost**:
```
97,500 min × 10 KB = 975 MB/year
```

**⚠️ Issue**: No client-side filtering. All clients receive all stocks' finalize events.

---

### 2.4 🟡 **MEDIUM RISK**: Memory Accumulation

**Risk Level**: **MEDIUM**
**Impact**: Memory leaks, OOM crashes

#### Memory Analysis

**Data Structures**:
```python
# realtime_service.py:58-63
self.minute_candle_state: Dict[str, MinuteCandleState] = {}
self.minute_state_lock = asyncio.Lock()
self.minute_state_ttl = timedelta(minutes=10)
self._last_acc_volume: Dict[str, int] = {}
self.minute_finalize_queue: asyncio.Queue[Tuple[str, ChartCandle]] = asyncio.Queue(maxsize=200)
```

**Cleanup Mechanism**:
```python
# realtime_service.py:596-615
async def _minute_state_cleanup_loop(self):
    """분봉 상태 정리 루프 (60초 주기)"""
    while self.is_running:
        await asyncio.sleep(60)
        await self._drain_stale_states()

async def _drain_stale_states(self):
    """TTL=10분 초과 상태 제거"""
    cutoff = datetime.now() - self.minute_state_ttl
    async with self.minute_state_lock:
        stale_keys = [
            code for code, state in self.minute_candle_state.items()
            if state.last_tick_ts < cutoff
        ]
        for code in stale_keys:
            self.minute_candle_state.pop(code, None)
            self._last_acc_volume.pop(code, None)
```

**⚠️ Potential Issue**: If cleanup loop fails, states accumulate indefinitely.

**Memory Growth** (100 stocks):
```
Per state: ~500 bytes (MinuteCandleState object)
Max states: 100 stocks
Max memory: 100 × 500 bytes = 50 KB (negligible)
```

**✅ ASSESSMENT**: Low risk due to cleanup loop + small footprint.

---

## 3. Data Consistency Risks

### 3.1 🔴 **HIGH RISK**: REST API Cache vs WebSocket Cache Desync

**Risk Level**: **HIGH**
**Impact**: Chart shows incorrect data

#### Scenario Analysis

**Timeline**:
```
09:00:00 - WebSocket receives tick → updates minute_candle_state
09:00:30 - REST API /api/chart/minute called
09:00:30 - Reads cache file (stale, no WebSocket data yet)
09:01:00 - Minute boundary → WebSocket persists to cache
09:01:05 - REST API /api/chart/minute called
09:01:05 - Reads cache file (now includes 09:00 candle)
```

**Gap Window**: 0-60 seconds where REST API returns stale data.

**Code Evidence**:
```python
# chart.py (REST API endpoint)
@router.get("/minute/{stock_code}")
async def get_minute_chart(...):
    # Reads from cache file (ChartCacheService)
    candles = await trading_service.get_minute_chart_data(...)

    # ⚠️ WebSocket-generated candle NOT in cache yet!
    return {"data": candles}
```

**⚠️ Impact**: Frontend shows incomplete chart until next minute boundary.

---

### 3.2 🟡 **MEDIUM RISK**: Race Condition - Persist vs API Read

**Risk Level**: **MEDIUM**
**Impact**: Partial data returned to client

#### Concurrent Access Pattern

```
Thread 1 (WebSocket):                Thread 2 (REST API):
09:01:00.000 - Minute boundary
09:01:00.050 - _flush_closed_candle
09:01:00.100 - Enqueue persistence
09:01:00.150 - Dequeue from worker
09:01:00.200 - update_minute_candle
09:01:00.250 - _load_from_cache ──┐
09:01:00.300 - Modify candles      │  09:01:00.275 - API request
09:01:00.350 - _save_to_cache ─────┼─ 09:01:00.300 - _load_from_cache (READ)
                                   │  09:01:00.350 - Return data
                                   └─ ⚠️ RACE: Read during write!
```

**Failure Mode**: REST API returns partial JSON (corrupted data).

---

## 4. Error Handling Gaps

### 4.1 🔴 **CRITICAL**: WebSocket Disconnection

**Risk Level**: **CRITICAL**
**Impact**: Persistence stops, cache becomes stale

#### Current Handling

```python
# realtime_service.py:570-594
async def _minute_persistence_worker(self):
    """분봉 persistence worker 시작"""
    try:
        while self.is_running or not self.minute_finalize_queue.empty():
            try:
                stock_code, candle = await asyncio.wait_for(
                    self.minute_finalize_queue.get(),
                    timeout=1.0
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            try:
                if self._minute_persist_handler:
                    await self._minute_persist_handler(stock_code, candle)
                else:
                    logger.warning(
                        f"⚠️ Handler 미설정! 분봉이 캐시에 저장되지 않음"
                    )
            except Exception as exc:
                logger.error(f"분봉 persistence 처리 실패: {exc}")
            finally:
                self.minute_finalize_queue.task_done()
```

**⚠️ Gaps**:
1. **No retry**: Failed persistence is discarded (data loss)
2. **No dead-letter queue**: Lost candles are unrecoverable
3. **No alerting**: Silent failures

---

### 4.2 🟡 **MEDIUM RISK**: Failed Persistence Operations

**Risk Level**: **MEDIUM**
**Impact**: Data loss, manual recovery required

#### Failure Scenarios

**Scenario 1: Disk Full**
```python
# chart_cache_service.py:189-198
with open(cache_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)  # ⚠️ May fail if disk full
```

**Scenario 2: Permission Denied**
```python
cache_file = self._get_cache_file_path(stock_code, date)  # kordata/005930/20251021.json
# ⚠️ If file permissions changed externally → Permission denied
```

**Scenario 3: JSON Encoding Error**
```python
data = [candle.model_dump() for candle in candles]  # ⚠️ If candle has invalid data
json.dump(data, f, ensure_ascii=False, indent=2)    # → JSON encoding error
```

**Current Handling**: ❌ **Exception logged, data discarded**

---

### 4.3 🟢 **LOW RISK**: Partial Data Corruption

**Risk Level**: **LOW**
**Impact**: Single candle data loss

#### Scenario

**Concurrent Write**:
```
Process 1: Writing 391 candles → {"timestamp": "09:00:00", "open": 71000, ...
Process 2: Reading during write → {"timestamp": "09:00:00", "open": 71 (PARTIAL)
```

**Protection**: ❌ **None** (Python `json.dump` is atomic at file level, but not guaranteed)

---

## 5. Performance Impact Assessment

### 5.1 File I/O Latency

**Measurement** (Need to measure in production):
```
Read:  391 candles × 150 bytes = 58.7 KB → ~1-5 ms (SSD)
Write: 391 candles × 150 bytes = 58.7 KB → ~5-10 ms (SSD)
Total: ~6-15 ms per minute per stock
```

**5 Stocks**: 30-75 ms/min
**10 Stocks**: 60-150 ms/min

**⚠️ Recommendation**: Add latency monitoring (`time.time()` before/after).

---

### 5.2 WebSocket Broadcast Latency

**Current Implementation**:
```python
# connection.py (assumed broadcast implementation)
async def broadcast(self, message: dict):
    for connection in self.active_connections:
        await connection.send_json(message)
```

**Latency** (10 clients):
```
Send time per client: ~1 ms (local network)
Total: 10 × 1 ms = 10 ms/broadcast
```

**5 Stocks**: 50 ms/min
**10 Stocks**: 100 ms/min

**✅ ASSESSMENT**: Acceptable overhead.

---

### 5.3 Cache File Lock Contention

**Expected Behavior** (if locks were implemented):
```
Thread 1: Lock → Read → Modify → Write → Unlock (10 ms)
Thread 2: Wait for lock (blocked)
Thread 3: Wait for lock (blocked)
```

**Worst Case** (3 concurrent writes):
```
Total latency: 10 ms + 10 ms + 10 ms = 30 ms
```

**✅ ASSESSMENT**: Would be acceptable IF locks were implemented.

---

## 6. Recommendations

### 6.1 🔴 **IMMEDIATE ACTIONS** (Before Frontend Implementation)

#### 1. Add File Locking Mechanism

**Implementation**:
```python
# chart_cache_service.py
import fcntl  # Unix file locking
from contextlib import contextmanager

@contextmanager
def file_lock(file_path: Path, mode: str = 'r'):
    """Context manager for file locking"""
    with open(file_path, mode, encoding="utf-8") as f:
        try:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
            yield f
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock

def _save_to_cache(self, stock_code: str, date: datetime, candles: List[ChartCandle]):
    """캐시에 데이터 저장 (with locking)"""
    cache_file = self._get_cache_file_path(stock_code, date)

    try:
        data = [candle.model_dump() for candle in candles]

        # ✅ ADD FILE LOCK
        with file_lock(cache_file, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"캐시 저장 성공 (locked): {cache_file}")

    except Exception as e:
        logger.error(f"캐시 저장 실패: {e}")
```

**Priority**: 🔴 **CRITICAL**

---

#### 2. Add Retry Mechanism for Failed Persistence

**Implementation**:
```python
# main.py
async def minute_persist_callback(stock_code: str, candle: ChartCandle):
    """Persistence with retry logic"""
    max_retries = 3
    retry_delay = 1.0  # seconds

    for attempt in range(max_retries):
        try:
            target_date = datetime.fromisoformat(candle.timestamp)
            success = await trading_service.update_minute_candle(
                stock_code=stock_code,
                target_date=target_date,
                candle_data=candle
            )

            if success:
                logger.info(f"✅ [Persistence] 분봉 저장 성공 (attempt {attempt + 1})")
                return
            else:
                logger.warning(f"⚠️ [Persistence] 저장 실패 (attempt {attempt + 1})")

        except Exception as e:
            logger.error(f"❌ [Persistence] 오류 (attempt {attempt + 1}): {e}")

        # Retry with backoff
        if attempt < max_retries - 1:
            await asyncio.sleep(retry_delay * (attempt + 1))

    # All retries failed
    logger.critical(f"🚨 [Persistence] 모든 재시도 실패: {stock_code} {candle.timestamp}")
    # TODO: Send to dead-letter queue or alert system
```

**Priority**: 🔴 **HIGH**

---

#### 3. Add Performance Monitoring

**Implementation**:
```python
# trading_service.py
async def update_minute_candle(
    self,
    stock_code: str,
    target_date: datetime,
    candle_data: ChartCandle
) -> bool:
    import time
    start_time = time.time()

    try:
        # ... existing logic ...

        return True

    finally:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"⏱️ [Performance] update_minute_candle: {elapsed_ms:.2f} ms")

        # Alert if slow
        if elapsed_ms > 50:
            logger.warning(f"⚠️ [Performance] Slow persistence: {elapsed_ms:.2f} ms")
```

**Priority**: 🟡 **MEDIUM**

---

### 6.2 🟡 **RECOMMENDED ENHANCEMENTS**

#### 1. Optimize File I/O (Append-Only Strategy)

**Current**: Full file rewrite every minute
**Proposed**: Append new candles to end of file

```python
def _append_to_cache(self, stock_code: str, date: datetime, new_candle: ChartCandle):
    """Append single candle (O(1) write instead of O(n))"""
    cache_file = self._get_cache_file_path(stock_code, date)

    # Read existing candles
    existing = self._load_from_cache(stock_code, date) or []

    # Append new candle
    existing.append(new_candle)

    # Write only the new candle (append mode)
    with file_lock(cache_file, 'a') as f:
        f.write(',\n' + json.dumps(new_candle.model_dump()))
```

**Benefit**: Reduces I/O from 58.7 KB/min to ~150 bytes/min (99.7% reduction)

---

#### 2. Add Client-Side Stock Filtering for WebSocket

**Current**: Broadcast all `minute_candle_finalize` to all clients
**Proposed**: Filter by subscribed stocks

```python
# connection.py
async def broadcast_to_subscribers(self, message: dict, stock_code: str):
    """Broadcast only to clients subscribed to this stock"""
    for connection in self.active_connections:
        subscriptions = self.subscriptions.get(connection, set())
        if stock_code in subscriptions:
            await connection.send_json(message)
```

**Benefit**: Reduces network traffic by 80-90% (if clients subscribe to 1-2 stocks only)

---

#### 3. Implement Dead-Letter Queue for Failed Persistence

**Purpose**: Preserve data when persistence fails

```python
# main.py
failed_persistence_queue = asyncio.Queue(maxsize=1000)

async def minute_persist_callback(stock_code: str, candle: ChartCandle):
    try:
        # ... retry logic ...

    except Exception as e:
        # All retries failed → Save to DLQ
        await failed_persistence_queue.put((stock_code, candle, datetime.now()))
        logger.critical(f"🚨 [DLQ] 분봉 저장 실패, DLQ에 저장: {stock_code}")

# Periodic DLQ processor
async def process_dead_letters():
    """Retry failed persistence from DLQ"""
    while True:
        await asyncio.sleep(60)  # Every minute

        while not failed_persistence_queue.empty():
            stock_code, candle, failed_at = await failed_persistence_queue.get()

            # Retry with exponential backoff
            # ...
```

**Benefit**: Prevents permanent data loss

---

## 7. Testing Strategy

### 7.1 Load Testing

**Scenario 1: High-Frequency Trading Day**
```bash
# Simulate 100 stocks with tick data every second
python tests/load_test_persistence.py --stocks 100 --duration 60s
```

**Metrics to Measure**:
- Persistence latency (p50, p95, p99)
- Queue depth (minute_finalize_queue)
- File I/O errors
- Memory usage

---

### 7.2 Chaos Testing

**Scenario 2: Disk Full**
```bash
# Fill disk to 95%
dd if=/dev/zero of=/tmp/filler bs=1M count=1000

# Observe persistence failures
tail -f logs/app.log | grep "Persistence 저장 실패"
```

**Scenario 3: Permission Denied**
```bash
# Change cache file permissions
chmod 444 kordata/005930/20251021.json

# Trigger persistence
# Observe error handling
```

---

### 7.3 Integration Testing

**Test Case**: REST API + WebSocket Consistency

```python
import asyncio
import httpx

async def test_api_websocket_consistency():
    # 1. Subscribe to WebSocket (stock_code=005930)
    ws = await websocket.connect("ws://localhost:8000/ws")

    # 2. Wait for minute_candle_finalize event
    finalize_event = await ws.receive_json()
    assert finalize_event["type"] == "minute_candle_finalize"
    ws_candle = finalize_event["data"]

    # 3. Immediately call REST API
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/chart/minute/005930")
        api_candles = response.json()["data"]

    # 4. Verify WebSocket candle exists in API response
    ws_timestamp = ws_candle["timestamp"]
    api_timestamps = [c["timestamp"] for c in api_candles]

    assert ws_timestamp in api_timestamps, "WebSocket candle not in API response!"
```

---

## 8. Risk Matrix Summary

| Risk Category | Severity | Likelihood | Impact | Priority |
|---------------|----------|------------|--------|----------|
| File Lock Contention | 🔴 HIGH | HIGH | Data corruption | 🔴 CRITICAL |
| File I/O Performance | 🔴 HIGH | MEDIUM | Backend latency | 🔴 HIGH |
| REST/WebSocket Desync | 🔴 HIGH | HIGH | Wrong chart data | 🔴 HIGH |
| Failed Persistence | 🟡 MEDIUM | MEDIUM | Data loss | 🟡 MEDIUM |
| WebSocket Broadcast | 🟡 MEDIUM | LOW | Network overhead | 🟢 LOW |
| Memory Accumulation | 🟢 LOW | LOW | OOM crash | 🟢 LOW |

---

## 9. Implementation Checklist

### Phase 1: Critical Safety (MUST DO BEFORE FRONTEND)
- [ ] Add file locking (`fcntl` or `filelock` library)
- [ ] Add persistence retry logic (3 attempts with backoff)
- [ ] Add performance logging (latency measurement)
- [ ] Test concurrent API + WebSocket access

### Phase 2: Enhanced Reliability
- [ ] Implement dead-letter queue
- [ ] Add alerting for failed persistence
- [ ] Optimize file I/O (append-only strategy)
- [ ] Add client-side stock filtering

### Phase 3: Production Readiness
- [ ] Load testing (100 stocks)
- [ ] Chaos testing (disk full, permissions)
- [ ] Integration testing (API + WebSocket consistency)
- [ ] Monitoring dashboard (Grafana/Prometheus)

---

## 10. Code Locations Requiring Careful Implementation

| File | Lines | Description | Risk |
|------|-------|-------------|------|
| `chart_cache_service.py` | 173-198 | `_save_to_cache()` - No locking | 🔴 CRITICAL |
| `chart_cache_service.py` | 53-81 | `_load_from_cache()` - No locking | 🔴 CRITICAL |
| `trading_service.py` | 481-538 | `update_minute_candle()` - Full file R/W | 🔴 HIGH |
| `main.py` | 138-170 | `minute_persist_callback()` - No retry | 🔴 HIGH |
| `realtime_service.py` | 548-561 | `_flush_closed_candle()` - Broadcast logic | 🟡 MEDIUM |
| `realtime_service.py` | 570-594 | `_minute_persistence_worker()` - Error handling | 🟡 MEDIUM |

---

## 11. Conclusion

### ✅ Good News
- Persistence handler already connected (no additional work needed)
- Code structure is clean and well-organized
- Logging is comprehensive for debugging

### ⚠️ Concerns
- **NO FILE LOCKING**: Critical data corruption risk
- **NO RETRY LOGIC**: Failed persistence = data loss
- **NO PERFORMANCE MONITORING**: Cannot detect slowdowns
- **FULL FILE REWRITE**: Inefficient I/O pattern

### 🎯 Recommended Action Plan
1. **BEFORE Frontend Implementation**: Add file locking + retry logic (2-3 days)
2. **Before Production**: Load testing + monitoring (1 week)
3. **Post-Deployment**: Optimize I/O + DLQ (1-2 weeks)

**Total Estimated Time**: 2-4 weeks for full production readiness

---

**Document End**
