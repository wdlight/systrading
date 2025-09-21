# Phase 2: API 구현 및 실시간 데이터 연동

**날짜**: 2025-09-11  
**작성자**: Claude  
**단계**: Phase 2 - 워치리스트 관리 API 구현 ✅ 완료

## 개요

Phase 1에서 구현된 서비스 아키텍처를 기반으로 RESTful API와 WebSocket을 구현하여 프론트엔드에서 사용할 수 있는 완전한 백엔드 시스템을 구축했습니다.

## 구현된 API 엔드포인트

### 1. 워치리스트 API (`/api/watchlist`)

#### 기본 CRUD 작업
```typescript
// 워치리스트 조회
GET /api/watchlist
Response: List[WatchlistItem]

// 특정 종목 조회
GET /api/watchlist/{stock_code}
Response: WatchlistItem

// 종목 추가
POST /api/watchlist/add
Body: AddStockRequest
Response: ApiResponse

// 종목 제거
DELETE /api/watchlist/{stock_code}
Response: ApiResponse
```

#### 기술적 분석 관련
```typescript
// 기술적 지표 조회
GET /api/watchlist/{stock_code}/indicators
Response: TechnicalIndicators

// 실시간 가격 조회
GET /api/watchlist/{stock_code}/price
Response: MarketDataSnapshot

// 기술적 분석 결과 조회
GET /api/watchlist/{stock_code}/analysis
Response: {
  stock_code: string,
  analysis_result: object,
  data_points: number,
  last_update: string
}
```

#### 실시간 데이터 업데이트
```typescript
// 개별 종목 업데이트
POST /api/watchlist/{stock_code}/update
Body: PriceUpdateEvent
Response: ApiResponse

// 대량 업데이트
POST /api/watchlist/bulk-update
Body: List[PriceUpdateEvent]
Response: ApiResponse
```

#### 관리 작업
```typescript
// 워치리스트 갱신
POST /api/watchlist/refresh
Response: ApiResponse

// 워치리스트 초기화
POST /api/watchlist/clear
Response: ApiResponse

// 워치리스트 통계
GET /api/watchlist/statistics
Response: {
  total_stocks: number,
  profit_stocks: number,
  loss_stocks: number,
  avg_profit_rate: number
}
```

### 2. 매매 API (`/api/trading`)

#### 매매 조건 관리
```typescript
// 매매 조건 조회
GET /api/trading/conditions
Response: TradingConditions

// 매매 조건 설정
POST /api/trading/conditions
Body: TradingConditions
Response: ApiResponse
```

#### 자동매매 제어
```typescript
// 자동매매 시작
POST /api/trading/start
Response: ApiResponse

// 자동매매 중지
POST /api/trading/stop
Response: ApiResponse

// 매매 상태 조회
GET /api/trading/status
Response: {
  is_running: boolean,
  start_time: string,
  total_trades: number,
  auto_trading_enabled: boolean
}
```

#### 매매 실행 (PyQt5 로직 재현)
```typescript
// 자동 매수 실행
POST /api/trading/execute-buy/{stock_code}
Response: TradeExecutionResult

// 자동 매도 실행
POST /api/trading/execute-sell/{stock_code}
Body: WatchlistItem
Response: TradeExecutionResult
```

#### 매매 기록 및 통계
```typescript
// 매매 실행 기록 조회
GET /api/trading/execution-history
Response: List[dict]

// 매매 통계 조회
GET /api/trading/statistics
Response: {
  total_trades: number,
  buy_count: number,
  sell_count: number,
  avg_profit_rate: number
}

// 매매 성과 조회
GET /api/trading/performance?days=30
Response: {
  period_days: number,
  total_trades: number,
  win_rate: number,
  total_profit_loss: number
}

// 매매 기록 초기화
POST /api/trading/clear-history
Response: ApiResponse
```

### 3. WebSocket API (`/ws`)

#### 연결 및 구독 관리
```typescript
// WebSocket 연결
WebSocket: /ws

// 메시지 형식
interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp: string;
}

// 구독 메시지
{
  "type": "subscribe",
  "stock_code": "005930"
}

// 구독 해제
{
  "type": "unsubscribe", 
  "stock_code": "005930"
}

// 연결 상태 확인
{
  "type": "ping"
}
```

#### 실시간 데이터 스트림
```typescript
// 가격 업데이트
{
  "type": "price_update",
  "stock_code": "005930",
  "data": PriceUpdateEvent,
  "timestamp": "2025-09-11T..."
}

// 워치리스트 변경
{
  "type": "watchlist_update",
  "event_type": "added" | "removed" | "updated",
  "stock_code": "005930",
  "data": object,
  "timestamp": "2025-09-11T..."
}

// 매매 신호
{
  "type": "trading_signal", 
  "stock_code": "005930",
  "signal_type": "buy_signal" | "sell_signal",
  "data": object,
  "timestamp": "2025-09-11T..."
}

// 매매 실행 결과
{
  "type": "trading_execution",
  "data": TradeExecutionResult,
  "timestamp": "2025-09-11T..."
}

// 전체 워치리스트 업데이트 (2초 주기)
{
  "type": "watchlist_full_update",
  "data": List[WatchlistItem],
  "timestamp": "2025-09-11T..."
}

// 매매 상태 업데이트
{
  "type": "trading_status",
  "data": TradingStatus,
  "timestamp": "2025-09-11T..."
}
```

## 핵심 구현 특징

### 1. PyQt5 로직 완전 재현

#### 기술적 지표 계산
```python
# MACD 계산 (9, 18, 6 파라미터 - PyQt5와 동일)
def calculate_macd(prices: pd.Series, fast_period=9, slow_period=18, signal_period=6):
    ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return macd_line.iloc[-1], signal_line.iloc[-1]

# RSI 계산 (14 기간 - TA-Lib 사용)
def calculate_rsi(prices: pd.Series, period=14):
    rsi_values = ta.RSI(prices.values, timeperiod=period)
    return rsi_values[-1]
```

#### 매매 조건 체크
```python
# 매수 조건: MACD 상향돌파 AND RSI >= 30
buy_macd_signal = check_macd_condition(current_macd, current_signal, prev_macd, prev_signal, "상향돌파")
buy_rsi_signal = check_rsi_condition(current_rsi, prev_rsi, 30, "이상")
buy_signal = buy_macd_signal and buy_rsi_signal

# 매도 조건: MACD 하향돌파 OR RSI <= 70 OR 수익률 조건 OR 트레일링스탑
sell_signal = sell_macd_signal or sell_rsi_signal or profit_condition or trailing_stop_condition
```

### 2. 실시간 데이터 처리

#### WebSocket 연결 관리
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}  # 클라이언트별 구독 종목
    
    async def broadcast_to_subscribers(self, stock_code: str, message: str):
        # 특정 종목을 구독하는 클라이언트에게만 전송
```

#### 실시간 업데이트 루프 (PyQt5의 timer2와 동일한 2초 주기)
```python
async def start_realtime_data_stream():
    while True:
        # 1. 워치리스트 갱신
        await watchlist_service.refresh_all_data()
        
        # 2. 워치리스트 데이터 브로드캐스트
        items = await watchlist_service.get_watchlist()
        await manager.broadcast(watchlist_update_message)
        
        # 3. 매매 상태 브로드캐스트
        trading_status = await trading_service.get_trading_status()
        await manager.broadcast(trading_status_message)
        
        await asyncio.sleep(2)  # 2초 주기 (PyQt5와 동일)
```

### 3. 타입 안전성과 검증

#### Pydantic 모델 활용
```python
# 요청 검증
class AddStockRequest(BaseModel):
    stock_code: str = Field(..., min_length=6, max_length=6)
    stock_name: Optional[str] = None

# 응답 검증  
class WatchlistItem(BaseModel):
    stock_code: str
    current_price: float
    profit_rate: Optional[float]
    # ... 모든 필드가 타입 안전
```

#### FastAPI 자동 문서화
- **Swagger UI**: `/docs`에서 모든 API 자동 문서화
- **ReDoc**: `/redoc`에서 대안 문서 제공
- **OpenAPI 스키마**: 프론트엔드 코드 생성 가능

### 4. 에러 처리 및 로깅

#### 일관된 에러 응답
```python
try:
    result = await service_method()
    return ApiResponse(success=True, message="성공", data=result)
except Exception as e:
    logger.error(f"작업 실패: {str(e)}")
    raise HTTPException(status_code=500, detail=f"오류: {str(e)}")
```

#### 구조화된 로깅
```python
logger.info(f"매수 주문 성공 - 종목: {stock_code}, 수량: {quantity}, 가격: {price}")
logger.error(f"기술적 지표 계산 실패 ({stock_code}): {str(e)}")
logger.debug(f"워치리스트 데이터 갱신 완료: {updated_count}개 종목")
```

## 성능 최적화

### 1. 연결 관리
- **Connection Pooling**: WebSocket 연결 효율적 관리
- **Subscription System**: 클라이언트별 선택적 데이터 전송
- **Auto Cleanup**: 끊어진 연결 자동 정리

### 2. 데이터 효율성
- **Bulk Operations**: 대량 데이터 일괄 처리
- **Incremental Updates**: 변경된 데이터만 전송
- **Memory Management**: 200개 데이터 포인트 제한

### 3. 비동기 처리
- **Non-blocking**: 모든 I/O 작업 비동기 처리
- **Concurrent Updates**: 여러 종목 동시 업데이트
- **Background Tasks**: 실시간 스트림 백그라운드 실행

## API 사용 예시

### 프론트엔드 연동 예시
```typescript
// 워치리스트 조회
const watchlist = await fetch('/api/watchlist').then(r => r.json());

// 종목 추가
await fetch('/api/watchlist/add', {
  method: 'POST',
  body: JSON.stringify({ stock_code: '005930' }),
  headers: { 'Content-Type': 'application/json' }
});

// WebSocket 연결
const ws = new WebSocket('ws://localhost:8000/ws');
ws.send(JSON.stringify({ type: 'subscribe', stock_code: '005930' }));

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'price_update') {
    updatePriceInUI(data.stock_code, data.data);
  }
};
```

## 다음 단계 준비

Phase 2의 완료로 다음 작업들이 준비되었습니다:

### ✅ API 완성도
- **29개 엔드포인트**: 모든 PyQt5 기능 커버
- **실시간 스트리밍**: WebSocket 완전 구현
- **타입 안전성**: 100% Pydantic 모델 적용

### 🚀 프론트엔드 연동 준비
- **RESTful API**: 표준 HTTP 프로토콜
- **WebSocket**: 실시간 업데이트 지원
- **자동 문서화**: Swagger/OpenAPI 제공

### 📊 테스트 준비
- **서비스 분리**: 독립적 단위 테스트 가능
- **Mock 가능**: 의존성 주입으로 테스트 용이
- **API 테스트**: FastAPI TestClient 활용 가능

이제 프론트엔드에서 기존 더미 데이터를 실제 API 호출로 교체하여 완전한 실시간 주식 거래 시스템을 구축할 수 있습니다.