# WebSocket 실시간 호가 시스템 통합 개선 계획

**계획 문서 저장 위치**: `docs/plan/20251015_1245_websocket-queue-fix-plan.md`

## 문제 요약

1015.hoga.analysis.md 분석 결과, 핵심 문제는 **Queue.empty() 멀티프로세스 환경 신뢰성 문제**입니다.
- `ws_req_queue_size: 4`로 요청이 쌓이지만 처리되지 않음
- Python 공식 문서: 멀티프로세스 환경에서 `empty()`는 신뢰할 수 없음
- 데이터가 있어도 `empty()`가 `True`를 반환할 수 있음

## 개선 범위

1. Queue 처리 로직 수정 (핵심)
2. 프론트엔드 WebSocket 구독 순서 개선
3. 로깅 및 모니터링 강화

## 구현 단계

### 1. domestic_websocket.py Queue 처리 로직 수정

**파일**: `backend/app/domestic_websocket.py`

**문제 코드** (라인 435-436):
```python
if not ws_req_queue.empty():
    req_data = ws_req_queue.get()
```

**수정 방안**:
```python
try:
    req_data = ws_req_queue.get_nowait()
    action_id = req_data['action_id']
    stock_code = req_data.get('종목코드')
    # ... 기존 처리 로직
except queue.Empty:
    pass  # Queue가 비어있으면 계속 진행
```

**변경 사항**:
- `if not ws_req_queue.empty()` 조건문 제거
- `get()` 대신 `get_nowait()` 사용
- `except queue.Empty` 처리 추가
- Queue 처리와 WebSocket 수신을 분리하여 블로킹 방지

### 2. realtime_service.py Queue 처리 로직 수정

**파일**: `backend/app/services/realtime_service.py`

**문제 코드** (라인 202-210):
```python
for _ in range(self.batch_size):
    if not self.ws_result_queue.empty():
        try:
            message = self.ws_result_queue.get_nowait()
            messages.append(message)
        except Empty:
            break
    else:
        break
```

**수정 방안**:
```python
for _ in range(self.batch_size):
    try:
        message = self.ws_result_queue.get_nowait()
        messages.append(message)
        self.metrics_collector.metrics.record_message_received()
    except Empty:
        break
```

**변경 사항**:
- `if not self.ws_result_queue.empty()` 조건문 제거
- 직접 `get_nowait()` 시도 후 `Empty` 예외 처리
- 중첩된 if-else 구조 단순화

### 3. 프론트엔드 WebSocket 구독 순서 개선

**파일**: `stock-trading-ui/src/hooks/useOrderBook.ts`

**문제**: WebSocket 연결 전에 구독 메시지가 전송되어 누락될 수 있음

**현재 코드** (라인 74-82):
```typescript
if (wsManager.isConnected()) {
    wsManager.send({
        type: 'subscribe',
        stock_code: stockCode
    });
} else {
    console.warn('WebSocket이 연결되지 않아 구독 등록을 할 수 없습니다.');
}
setIsSubscribed(true);
```

**수정 방안**:
```typescript
// WebSocket 연결 대기 및 구독
const waitForConnection = async (maxWait = 5000) => {
    const startTime = Date.now();
    while (!wsManager.isConnected() && Date.now() - startTime < maxWait) {
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    return wsManager.isConnected();
};

const isConnected = await waitForConnection();
if (isConnected) {
    wsManager.send({
        type: 'subscribe',
        stock_code: stockCode
    });
    setIsSubscribed(true);
    console.log(`✅ 호가 구독 시작: ${stockCode}`);
} else {
    throw new Error('WebSocket 연결 타임아웃');
}
```

**변경 사항**:
- WebSocket 연결 완료 대기 로직 추가
- 연결 확인 후에만 `setIsSubscribed(true)` 설정
- 타임아웃 처리로 무한 대기 방지

**⚠️ 주의사항**:
- `waitForConnection()`은 최대 5초까지 대기하므로, 호출 측에서 반드시 `await`와 에러 처리를 해야 함
- UI 컴포넌트에서 `subscribe()` 호출 시 Promise를 제대로 처리하지 않으면 UX 문제 발생 가능
- 예시:
```typescript
// 올바른 호출 방법
try {
    await subscribe();
    console.log('구독 성공');
} catch (error) {
    console.error('구독 실패:', error);
    // 에러 UI 표시 등
}
```

### 4. 프론트엔드 WebSocket 재연결 시 구독 복원

**파일**: `stock-trading-ui/src/lib/websocket.ts`

**추가 기능**: 재연결 시 이전 구독 상태 복원

**수정 위치**: `ws.onopen` 핸들러 (라인 51-62)

**추가 코드**:
```typescript
this.ws.onopen = () => {
    console.log('WebSocket 연결됨');
    this.reconnectAttempts = 0;
    this.updateConnectionState({
        status: 'connected',
        lastConnected: new Date(),
        reconnectAttempts: 0,
        error: undefined,
    });
    this.startHeartbeat();
    
    // 재연결 시 구독 복원
    this.restorePendingSubscriptions();
    
    resolve();
};

private pendingSubscriptions: Set<string> = new Set();

private restorePendingSubscriptions() {
    if (this.pendingSubscriptions.size > 0) {
        console.log(`🔄 ${this.pendingSubscriptions.size}개 구독 복원 중...`);
        this.pendingSubscriptions.forEach(stockCode => {
            this.send({
                type: 'subscribe',
                stock_code: stockCode
            });
        });
    }
}

public addPendingSubscription(stockCode: string) {
    this.pendingSubscriptions.add(stockCode);
}

public removePendingSubscription(stockCode: string) {
    this.pendingSubscriptions.delete(stockCode);
}
```

### 4-1. pendingSubscriptions 사용 방법

**useOrderBook.ts 수정**:
```typescript
const subscribe = useCallback(async () => {
    if (isSubscribed) return;

    try {
        // REST API로 백엔드 KIS WebSocket 구독 요청
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/realtime/subscribe/orderbook?stock_code=${stockCode}`,
            { method: 'POST' }
        );

        if (!response.ok) {
            throw new Error('호가 구독 실패');
        }

        // WebSocket 연결 대기 및 구독
        const waitForConnection = async (maxWait = 5000) => {
            const startTime = Date.now();
            while (!wsManager.isConnected() && Date.now() - startTime < maxWait) {
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            return wsManager.isConnected();
        };

        const isConnected = await waitForConnection();
        if (isConnected) {
            wsManager.send({
                type: 'subscribe',
                stock_code: stockCode
            });
            // 구독 성공 시 pending list에 추가
            wsManager.addPendingSubscription(stockCode);
            setIsSubscribed(true);
            console.log(`✅ 호가 구독 시작: ${stockCode}`);
        } else {
            throw new Error('WebSocket 연결 타임아웃');
        }
    } catch (err) {
        setError(err instanceof Error ? err.message : '구독 실패');
        console.error('호가 구독 오류:', err);
        throw err; // 호출 측에서 처리할 수 있도록 에러 재throw
    }
}, [stockCode, isSubscribed]);

const unsubscribe = useCallback(async () => {
    if (!isSubscribed) return;

    try {
        const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL}/api/realtime/unsubscribe/orderbook?stock_code=${stockCode}`,
            { method: 'POST' }
        );

        if (!response.ok) {
            throw new Error('호가 구독 해제 실패');
        }

        // WebSocket 구독 해제
        if (wsManager.isConnected()) {
            wsManager.send({
                type: 'unsubscribe',
                stock_code: stockCode
            });
            console.log(`❌ 호가 WebSocket 구독 해제: ${stockCode}`);
        }

        // pending list에서 제거
        wsManager.removePendingSubscription(stockCode);
        setIsSubscribed(false);
        console.log(`❌ 호가 구독 해제: ${stockCode}`);
    } catch (err) {
        console.error('호가 구독 해제 오류:', err);
        throw err; // 호출 측에서 처리할 수 있도록 에러 재throw
    }
}, [stockCode, isSubscribed]);
```

**변경 사항**:
- `addPendingSubscription(stockCode)` 호출: 구독 성공 시 추가
- `removePendingSubscription(stockCode)` 호출: 구독 해제 시 제거
- 에러 발생 시 `throw err`로 호출 측에서 처리할 수 있도록 함

## 테스트 시나리오

### 1. Queue 처리 검증
```bash
# 백엔드 재시작
cd backend
./vkis/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Queue 상태 확인
curl http://localhost:8000/api/realtime/debug/queue-status

# 호가 구독
curl -X POST "http://localhost:8000/api/realtime/subscribe/orderbook?stock_code=005930"

# Queue 크기 감소 확인 (5초 후)
sleep 5
curl http://localhost:8000/api/realtime/debug/queue-status
```

**기대 결과**: `ws_req_queue_size`가 0으로 감소

### 2. 실시간 데이터 수신 검증
```bash
# 로그 모니터링
tail -f logs/backend_app_2025-10-15.log | grep -E "(호가.*등록|H0STASP0|📊|📡)"
```

**기대 결과**: 
- `[DEBUG] Queue에서 요청 수신` 로그 출력
- `실시간호가등록 005930` 로그 출력
- `📊 호가 데이터 처리` 주기적 출력
- `📡 호가 데이터 브로드캐스트` 주기적 출력

### 3. 프론트엔드 구독 검증
- 브라우저에서 `/trview` 페이지 접속
- 개발자 도구 콘솔에서 `✅ 호가 구독 시작` 확인
- Network 탭 WebSocket 프레임에서 `subscribe` 메시지 확인
- `📊 호가 데이터 업데이트` 로그 주기적 출력 확인

### 4. WebSocket 재연결 및 구독 복원 검증
- 브라우저에서 WebSocket 연결을 강제로 끊기 (개발자 도구에서)
- 네트워크 복구 후 자동 재연결 확인
- 콘솔에서 `🔄 X개 구독 복원 중...` 메시지 확인
- 복원된 구독에서 실시간 데이터 수신 확인

### 5. UI 컴포넌트 에러 처리 검증
- `useOrderBook` 훅의 `subscribe()` 함수 호출 시 에러 처리 확인
- WebSocket 연결 타임아웃 시 적절한 에러 메시지 표시 확인
- `pendingSubscriptions` 관리 상태 확인 (구독/해제 시 추가/제거)

## 검증 체크리스트

### 백엔드 검증
- [ ] `ws_req_queue_size`가 정상적으로 감소하는가?
- [ ] domestic_websocket 로그에 호가 등록 메시지가 나타나는가?
- [ ] realtime_service 로그에 호가 데이터 처리 메시지가 나타나는가?
- [ ] 캐시 API(`/api/realtime/orderbook/005930`)에서 최신 데이터가 조회되는가?

### 프론트엔드 검증
- [ ] 프론트엔드에서 실시간 호가 데이터가 1초에 2회 이상 업데이트되는가?
- [ ] WebSocket 연결 타임아웃 시 적절한 에러 메시지가 표시되는가?
- [ ] `pendingSubscriptions`가 구독 성공 시 추가되고 해제 시 제거되는가?
- [ ] WebSocket 재연결 시 구독이 자동으로 복원되는가?
- [ ] `useOrderBook` 훅의 Promise 처리가 올바르게 작동하는가?

### 통합 검증
- [ ] 전체 시스템에서 실시간 호가 데이터가 안정적으로 수신되는가?
- [ ] 네트워크 불안정 상황에서도 자동 복구가 되는가?
- [ ] UI에서 구독 상태가 정확하게 표시되는가?

## 참조 문서

- `docs/bugfix/20251015_1240_websocket-orderbook-troubleshooting.md` - 시도한 해결책 기록
- `docs/analysis/1015.hoga.analysis.md` - 근본 원인 분석
- Python multiprocessing Queue 공식 문서: https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Queue.empty

## 문서 위치 안내

**이 계획 문서의 최종 저장 위치**: `docs/plan/20251015_1245_websocket-queue-fix-plan.md`

모든 관련 문서는 `docs/` 하위에서 찾을 수 있습니다:
- 분석: `docs/analysis/1015.hoga.analysis.md`
- 버그픽스 기록: `docs/bugfix/20251015_1240_websocket-orderbook-troubleshooting.md`
- 실행 계획: `docs/plan/20251015_1245_websocket-queue-fix-plan.md` (이 문서)

## 실행 단계

1. **Queue 처리 로직 수정** (백엔드)
   - `backend/app/domestic_websocket.py` 수정
   - `backend/app/services/realtime_service.py` 수정

2. **프론트엔드 WebSocket 개선**
   - `stock-trading-ui/src/hooks/useOrderBook.ts` 수정 (pendingSubscriptions 관리 포함)
   - `stock-trading-ui/src/lib/websocket.ts` 수정 (재연결 시 구독 복원)

3. **UI 컴포넌트 Promise 처리 강화**
   - `useOrderBook` 훅 호출부에서 `await` 및 에러 처리 추가
   - WebSocket 연결 타임아웃 시 사용자 피드백 개선

4. **테스트 및 검증**
   - Queue 처리 검증
   - 실시간 데이터 수신 검증
   - 프론트엔드 구독 검증
   - WebSocket 재연결 및 구독 복원 검증
   - UI 에러 처리 검증

5. **문서 정리**
   - 기존 루트 계획 문서 이동 (필요시)
   - 모든 문서를 `docs/` 하위로 통합

## 주요 개선사항 요약

### 🔧 백엔드 개선
- **Queue.empty() 제거**: 멀티프로세스 환경 신뢰성 문제 해결
- **get_nowait() + except Empty 패턴**: 안정적인 Queue 처리

### 🔧 프론트엔드 개선
- **WebSocket 연결 대기**: 5초 타임아웃으로 연결 안정성 확보
- **구독 복원 기능**: 재연결 시 자동으로 이전 구독 상태 복원
- **Promise 처리 강화**: 에러 상황에서 적절한 사용자 피드백

### 🔧 시스템 안정성
- **네트워크 불안정 대응**: 자동 재연결 및 구독 복원
- **에러 처리 개선**: 타임아웃, 연결 실패 등 다양한 상황 대응
- **상태 관리 강화**: pendingSubscriptions로 구독 상태 추적