# Fix Backend Queue Initialization Issue

## Problem Analysis

### Root Cause Identified

1. **현재 프로세스 상태**:
   - `python ./app/main.py`로 직접 실행되고 있음 (PID: 72488)
   - uvicorn을 통해 실행되지 않음
   - `lifespan` 함수가 실행되지 않아 Queue가 초기화되지 않음

2. **Queue 초기화 실패**:
   - `ws_req_queue`와 `ws_result_queue`가 `None` 상태
   - 호가 구독 요청이 실패하는 근본 원인

3. **기존 프로세스 충돌**:
   - 포트 8000이 이미 사용 중 (Address already in use)
   - 기존 프로세스를 종료하지 않고 새로 시작하려고 시도

### Additional Issues to Consider

1. **Multiprocessing Queue 직렬화 문제**:
   - `KoreaInvestAPI` 인스턴스를 `Process`에 전달할 때 pickle 직렬화 문제 가능성
   - 복잡한 객체는 multiprocessing으로 전달하기 어려움

2. **WebSocket 프로세스 생명주기**:
   - 프로세스가 정상적으로 시작되었는지 확인 필요
   - 프로세스가 죽었을 때 재시작 메커니즘 필요

3. **프론트엔드 WebSocket 재연결**:
   - 백엔드 재시작 시 프론트엔드 WebSocket 재연결 필요
   - 자동 재연결 로직 검증 필요

## Solution

### Step 1: Kill Existing Process and Restart Properly

**Action**: 기존 프로세스를 완전히 종료하고 uvicorn을 통해 올바르게 재시작

```bash
# 1. 기존 프로세스 종료
pkill -9 -f "python.*app.main"
pkill -9 -f "uvicorn"

# 2. 포트 확인
lsof -i :8000

# 3. uvicorn으로 재시작
cd /home/wide/projects/systrading/backend
./vkis/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Result**:
- `lifespan` 함수가 실행되어 Queue 초기화
- `domestic_websocket` 프로세스 시작
- 로그에 "FastAPI 애플리케이션 초기화를 시작합니다." 메시지 출력

### Step 2: Verify Queue Initialization

**Action**: Queue가 정상적으로 초기화되었는지 확인

```bash
# Queue 상태 확인
curl -s "http://localhost:8000/api/realtime/debug/queue-status" | jq '.'
```

**Expected Output**:
```json
{
  "ws_req_queue_size": 0,
  "ws_result_queue_size": 0,
  "ws_req_queue_initialized": true,
  "ws_result_queue_initialized": true
}
```

### Step 3: Verify WebSocket Process

**Action**: `domestic_websocket` 프로세스가 정상적으로 실행되는지 확인

```bash
# 프로세스 확인
ps aux | grep domestic_websocket

# 백엔드 로그 확인
grep -E "(domestic_websocket 프로세스|한국투자증권 API Web Socket)" /home/wide/projects/systrading/logs/API_20251015.log | tail -n 5
```

**Expected Result**:
- `domestic_websocket` 프로세스가 실행 중
- 로그에 "domestic_websocket 프로세스를 시작했습니다" 메시지 출력
- 로그에 "한국투자증권 API Web Socket 연결 try!" 메시지 출력

### Step 4: Test Orderbook Subscription

**Action**: 호가 구독이 정상적으로 작동하는지 테스트

```bash
# 호가 구독 요청
curl -s "http://localhost:8000/api/realtime/subscribe/orderbook?stock_code=005930" -X POST | jq '.'
```

**Expected Output**:
```json
{
  "success": true,
  "message": "종목 005930 호가 구독 시작",
  "stock_code": "005930"
}
```

### Step 5: Verify Real-time Data Flow

**Action**: 실시간 호가 데이터가 정상적으로 수신되는지 확인

```bash
# 백엔드 로그 모니터링
tail -f /home/wide/projects/systrading/logs/API_20251015.log | grep -E "(🔥|📊|H0STASP0|호가.*파싱)"
```

**Expected Result**:
- `H0STASP0` 메시지 수신 로그
- `🔥 호가 데이터 Queue 추가` 로그
- `📊 호가 데이터 처리` 로그

### Step 6: Frontend Verification

**Action**: 프론트엔드에서 실시간 업데이트 확인

1. 브라우저에서 `http://localhost:9000/trview` 페이지 새로고침
2. 콘솔에서 다음 로그 확인:
   - `✅ 호가 WebSocket 구독 등록: 005930`
   - `📊 호가 데이터 업데이트: 005930`
   - `🔥 실시간 WebSocket 업데이트 - 현재가: ...`
3. 호가창이 자동으로 업데이트되는지 확인 (폴링 로그 없음)

## Potential Issues and Solutions

### Issue 1: KoreaInvestAPI Serialization Error

**Symptom**: `domestic_websocket` 프로세스가 시작되지 않거나 즉시 종료됨

**Solution**: `KoreaInvestAPI` 인스턴스 대신 설정 정보만 전달

**File**: `backend/app/main.py`

현재 코드 (line 133-137):
```python
websocket_process = Process(
    target=run_websocket,
    args=(korea_invest_service.api_instance, ws_url, ws_req_queue, ws_result_queue),
    daemon=True
)
```

**If needed**, 수정:
```python
# KoreaInvestAPI 인스턴스 대신 설정 전달
websocket_process = Process(
    target=run_websocket,
    args=(settings, ws_url, ws_req_queue, ws_result_queue),
    daemon=True
)
```

그리고 `domestic_websocket.py`의 `run_websocket` 함수에서 API 인스턴스 생성

### Issue 2: Process Monitoring and Auto-Restart

**Symptom**: `domestic_websocket` 프로세스가 죽었을 때 재시작되지 않음

**Solution**: 프로세스 헬스 체크 및 자동 재시작 메커니즘 추가

**File**: `backend/app/main.py`

`lifespan` 함수에 프로세스 모니터링 추가:
```python
async def monitor_websocket_process():
    while True:
        await asyncio.sleep(30)  # 30초마다 체크
        if websocket_process and not websocket_process.is_alive():
            logger.error("domestic_websocket 프로세스가 종료되었습니다. 재시작합니다.")
            # 재시작 로직
```

### Issue 3: Frontend WebSocket Reconnection

**Symptom**: 백엔드 재시작 후 프론트엔드 WebSocket이 재연결되지 않음

**Solution**: 프론트엔드 WebSocket 재연결 로직 검증

**File**: `stock-trading-ui/src/lib/websocket.ts`

현재 재연결 로직이 있는지 확인하고, 필요시 개선

## Verification Checklist

- [ ] 기존 프로세스 완전히 종료
- [ ] uvicorn으로 백엔드 재시작
- [ ] `lifespan` 함수 실행 확인 (로그)
- [ ] Queue 초기화 확인 (`ws_req_queue_initialized: true`)
- [ ] `domestic_websocket` 프로세스 실행 확인
- [ ] 호가 구독 성공 확인
- [ ] 실시간 호가 데이터 수신 확인 (백엔드 로그)
- [ ] 프론트엔드 WebSocket 연결 확인
- [ ] 프론트엔드 호가창 자동 업데이트 확인
- [ ] 폴링 로그 없음 확인

## Files to Check/Modify

1. **Backend Process Management**:
   - `backend/app/main.py` - lifespan 함수 및 프로세스 관리
   - `backend/app/domestic_websocket.py` - WebSocket 프로세스 로직

2. **Frontend WebSocket**:
   - `stock-trading-ui/src/lib/websocket.ts` - 재연결 로직
   - `stock-trading-ui/src/hooks/useOrderBook.ts` - 구독 로직 (이미 수정됨)

3. **Monitoring**:
   - `/home/wide/projects/systrading/logs/API_20251015.log` - 백엔드 로그

## Success Criteria

1. ✅ Queue가 정상적으로 초기화됨
2. ✅ 호가 구독이 성공함
3. ✅ 실시간 호가 데이터가 백엔드에서 수신됨
4. ✅ 프론트엔드에서 실시간 업데이트가 자동으로 이루어짐
5. ✅ 폴링 로직이 완전히 제거되어 서버 부하 감소
6. ✅ WebSocket 기반의 진정한 실시간 시스템 구현 완료

## Implementation To-dos

- [ ] 기존 프로세스 완전히 종료하고 uvicorn으로 재시작
- [ ] Queue 초기화 확인 및 WebSocket 프로세스 검증
- [ ] 호가 구독 테스트 및 실시간 데이터 흐름 확인
- [ ] 프론트엔드 실시간 업데이트 검증
- [ ] 직렬화 오류, 프로세스 모니터링 등 엣지 케이스 처리 (필요시)

