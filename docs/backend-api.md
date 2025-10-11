# Backend API Documentation

이 문서는 Frontend 개발자가 백엔드 API를 쉽게 이해하고 사용할 수 있도록 작성되었습니다.

**Base URL**: `http://localhost:8000`

---

## 📖 목차

1.  [공통 데이터 모델 (Schemas)](#-공통-데이터-모델-schemas)
2.  [WebSocket API](#-websocket-api)
3.  [계좌 API (Account)](#-계좌-api-account)
4.  [매매 API (Trading)](#-매매-api-trading)
5.  [워치리스트 API (Watchlist)](#-워치리스트-api-watchlist)
6.  [주식 정보 API (Stocks)](#-주식-정보-api-stocks)
7.  [차트 API (Chart)](#-차트-api-chart)

---

## 共通データモデル (Schemas)

API 전반에서 사용되는 주요 데이터 모델입니다.

### `Position`

보유 종목 정보

```json
{
  "stock_code": "005930",
  "stock_name": "삼성전자",
  "quantity": 10,
  "sellable_quantity": 10,
  "avg_price": 75000,
  "current_price": 80000,
  "unrealized_pnl": 50000,
  "profit_rate": 6.67,
  "day_change": 1000,
  "day_change_rate": 1.27
}
```

### `AccountSummary`

계좌 요약 정보

```json
{
  "account_number": "12345678-01",
  "total_asset": 10000000,
  "total_evaluation": 8000000,
  "available_cash": 2000000,
  "total_profit_loss": 500000,
  "total_profit_rate": 6.25
}
```

### `AccountBalance`

계좌 잔고 상세 정보

```json
{
  "summary": {
    // AccountSummary 모델
  },
  "positions": [
    // Position 모델 배열
  ]
}
```

### `WatchlistItem`

워치리스트 종목 정보

```json
{
  "stock_code": "005930",
  "current_price": 80000,
  "profit_rate": 6.67,
  "avg_price": 75000,
  "quantity": 10,
  "macd": 150.5,
  "macd_signal": 120.2,
  "rsi": 65.7,
  "trailing_stop_activated": false,
  "trailing_stop_high": null
}
```

### `ApiResponse`

성공 시의 일반적인 응답 형식

```json
{
  "success": true,
  "message": "요청이 성공적으로 처리되었습니다.",
  "data": {
    "key": "value"
  },
  "timestamp": "2025-10-11T12:00:00Z"
}
```

---

## 🔌 WebSocket API

실시간 데이터 수신을 위한 WebSocket 엔드포인트입니다.

-   **URL**: `ws://localhost:8000/ws`

### 메시지 형식

서버로부터 받는 모든 메시지는 아래와 같은 형식을 따릅니다.

```json
{
  "type": "price_update" | "watchlist_update" | "account_update" | "...",
  "timestamp": "2025-10-11T12:00:00Z",
  "data": {
    // 메시지 타입에 따른 데이터
  }
}
```

-   `price_update`: 개별 종목의 실시간 가격 및 정보 업데이트
-   `watchlist_update`: 워치리스트 전체 상태 업데이트
-   `account_update`: 계좌 잔고 정보 업데이트
-   `order_update`: 주문 체결 상태 업데이트
-   `connection_status`: API 연결 상태 업데이트

---

## 🏦 계좌 API (Account)

**Prefix**: `/api/account`

### `GET /api/account/balance`

**계좌 잔고 조회**
계좌의 전체 잔고 정보와 보유 종목 목록을 조회합니다.

-   **응답 (200 OK)**: `AccountBalance`

```json
{
  "summary": {
    "account_number": "12345678-01",
    "total_asset": 10000000,
    "total_evaluation": 8000000,
    "available_cash": 2000000,
    "total_profit_loss": 500000,
    "total_profit_rate": 6.25
  },
  "positions": [
    {
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "quantity": 10,
      "sellable_quantity": 10,
      "avg_price": 75000,
      "current_price": 80000,
      "unrealized_pnl": 50000,
      "profit_rate": 6.67,
      "day_change": 1000,
      "day_change_rate": 1.27
    }
  ]
}
```

### `GET /api/account/summary`

**계좌 요약 정보**
계좌의 요약 정보(총 자산, 현금 등)만 조회합니다.

-   **응답 (200 OK)**: `AccountSummary`

### `GET /api/account/positions`

**보유 종목 목록**
현재 보유 중인 종목들의 상세 정보를 조회합니다.

-   **응답 (200 OK)**: `List[Position]`

### `GET /api/account/positions/{stock_code}`

**특정 종목 포지션 조회**
특정 종목의 보유 정보를 조회합니다.

-   **경로 파라미터**:
    -   `stock_code` (string): 조회할 종목의 코드
-   **응답 (200 OK)**: `Position`
-   **에러**:
    -   `404 Not Found`: 해당 종목을 보유하고 있지 않을 경우

### `POST /api/account/refresh`

**계좌 정보 갱신**
계좌 정보를 강제로 갱신합니다.

-   **응답 (200 OK)**: `ApiResponse`

### `GET /api/account/status`

**계좌 연결 상태**
한국투자증권 API 연결 상태를 확인합니다.

-   **응답 (200 OK)**:

```json
{
  "connected": true,
  "last_update": "2025-10-11T11:59:00Z",
  "account_number": "12345678-01",
  "message": "계좌 연결 상태가 정상입니다."
}
```

---

## 📈 매매 API (Trading)

**Prefix**: `/api`

### `GET /api/conditions`

**매매 조건 조회**
현재 설정된 자동매매의 매수/매도 조건을 조회합니다.

-   **응답 (200 OK)**: `TradingConditions`

### `POST /api/conditions`

**매매 조건 설정**
자동매매의 매수/매도 조건을 설정합니다.

-   **요청 본문**: `TradingConditions`
-   **응답 (200 OK)**: `ApiResponse`

### `POST /api/start`

**자동매매 시작**
설정된 조건에 따라 자동매매를 시작합니다.

-   **응답 (200 OK)**: `ApiResponse`

### `POST /api/stop`

**자동매매 중지**
실행 중인 자동매매를 중지합니다.

-   **응답 (200 OK)**: `ApiResponse`

### `GET /api/status`

**매매 상태 조회**
현재 자동매매 실행 상태와 통계를 조회합니다.

-   **응답 (200 OK)**:

```json
{
  "is_running": true,
  "start_time": "2025-10-11T09:00:00Z",
  "total_trades": 5,
  "profit_trades": 3,
  "loss_trades": 2
}
```

### `GET /api/execution-history`

**매매 실행 기록 조회**
자동매매 실행 기록을 조회합니다.

-   **응답 (200 OK)**: `List[dict]`

### `POST /api/clear-history`

**매매 기록 초기화**
자동매매 실행 기록을 초기화합니다.

-   **응답 (200 OK)**: `ApiResponse`

---

## ❤️ 워치리스트 API (Watchlist)

**Prefix**: `/api/watchlist`

### `GET /api/watchlist`

**워치리스트 조회**
현재 모니터링 중인 모든 종목의 실시간 정보를 조회합니다.

-   **응답 (200 OK)**: `List[WatchlistItem]`

### `POST /api/watchlist/add`

**종목 추가**
워치리스트에 새로운 종목을 추가합니다.

-   **요청 본문**:
    ```json
    {
      "stock_code": "035720"
    }
    ```
-   **응답 (200 OK)**: `ApiResponse`

### `DELETE /api/watchlist/{stock_code}`

**종목 제거**
워치리스트에서 종목을 제거합니다.

-   **경로 파라미터**:
    -   `stock_code` (string): 제거할 종목의 코드
-   **응답 (200 OK)**: `ApiResponse`

### `GET /api/watchlist/{stock_code}/indicators`

**기술적 지표 조회**
특정 종목의 RSI, MACD 등 기술적 지표를 조회합니다.

-   **경로 파라미터**:
    -   `stock_code` (string): 조회할 종목의 코드
-   **응답 (200 OK)**: `TechnicalIndicators`
-   **에러**:
    -   `404 Not Found`: 해당 종목이 워치리스트에 없거나 지표를 계산할 수 없을 경우

### `POST /api/watchlist/refresh`

**워치리스트 갱신**
워치리스트의 모든 데이터를 강제로 갱신합니다.

-   **응답 (200 OK)**: `ApiResponse`

### `POST /api/watchlist/clear`

**워치리스트 초기화**
워치리스트를 완전히 초기화합니다.

-   **응답 (200 OK)**: `ApiResponse`

---

## 📊 주식 정보 API (Stocks)

**Prefix**: `/api/stocks`

(현재 `stocks_router` 관련 코드가 없어 추후 추가 예정)

---

## 📉 차트 API (Chart)

**Prefix**: `/api/chart`

(현재 `chart_router` 관련 코드가 없어 추후 추가 예정)
