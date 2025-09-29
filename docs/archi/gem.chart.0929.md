# Gemini Chart Implementation Plan - Minute Data (2025-09-29)

## 📁 Project Goal
Implement real-time minute-by-minute candlestick chart display for Samsung Electronics (005930) on the `/test-chart` frontend page.

## 🏗️ Current State Analysis

### Frontend (`stock-trading-ui`)
*   `stock-trading-ui/src/app/test-chart/page.tsx`: Displays a "Live Chart" section using `KoreanTradingChart`.
*   `stock-trading-ui/src/components/trading/KoreanTradingChart.tsx`: Currently uses a *mock chart area* with random data for its line path. It does not actually render a chart based on `chartData`.
*   `useRealChartData` hook (from `@/hooks/useRealChartData`): Fetches `chartData` with a `refreshInterval` of 30 seconds, primarily for daily/weekly/monthly data.
*   `useSamsungRealTimePrice` hook: Fetches real-time price data, now configured to refresh every 1 second.
*   `KoreanStockChart` interface (frontend): Defines the expected structure for chart data.

### Backend (`backend`)
*   FastAPI application.
*   `KoreaInvestAPIService` (in `backend/app/core/korea_invest.py`): Wraps `brokers.korea_investment.ki_api.KoreaInvestAPI`.
*   `ki_api.py` (in `brokers/korea_investment/ki_api.py`):
    *   `get_minute_chart_data(self, stock_code)`: Fetches minute data for the *current day* up to the *current time*. Returns a `pd.DataFrame`.
    *   `get_daily_price_chart(self, stock_code, start_date, end_date, period_code='D')`: Fetches daily/weekly/monthly historical data.
*   `backend/app/models/schemas.py`: Pydantic models for API request/response.

## ⚠️ Limitation of `ki_api.get_minute_chart_data`
The `ki_api.get_minute_chart_data` method only provides minute data for the *current day* up to the *current time*. It does not allow specifying historical dates or a specific number of past candles. This means a full historical minute chart cannot be drawn using this single API call.

## ✅ Proposed Solution (Best Effort - Current Day Minute Chart)
Given the API limitation, the initial implementation will focus on displaying a minute chart for the *current trading day*. If historical minute data is required, a more complex solution (e.g., looping through previous days, or finding an alternative API) would be necessary.

## 🚀 Implementation Plan

### Phase 1: Backend Development

1.  **Add `ChartCandle` Pydantic Model:**
    *   **File:** `backend/app/models/schemas.py`
    *   **Action:** Add a new Pydantic model `ChartCandle` that mirrors the frontend's `KoreanStockChart` interface. This will ensure data consistency.
    *   **Status:** **PENDING** (Will be done in the next step)

2.  **Enhance `KoreaInvestAPIService.get_minute_chart_data`:**
    *   **File:** `backend/app/core/korea_invest.py`
    *   **Action:** Modify the existing `get_minute_chart_data` method to:
        *   Call `self.api_instance.get_minute_chart_data(stock_code)`.
        *   Process the returned `pd.DataFrame` into a list of `ChartCandle` objects. This involves:
            *   Constructing a proper ISO-formatted `timestamp` from the `일자` and `시간` columns.
            *   Mapping `시가`, `고가`, `저가`, `종가`, `거래량` to `open`, `high`, `low`, `close`, `volume` respectively.
            *   Ensuring data types match the `ChartCandle` model.

3.  **Create Backend FastAPI Endpoint for Minute Data:**
    *   **File:** `backend/app/api/trading.py` (or a new `chart.py` if preferred for separation)
    *   **Action:** Create a new FastAPI endpoint `GET /api/chart/{stock_code}/minute`.
    *   **Functionality:**
        *   Takes `stock_code` as a path parameter.
        *   Calls `KoreaInvestAPIService.get_minute_chart_data(stock_code)`.
        *   Returns the processed list of `ChartCandle` objects.

### Phase 2: Frontend Development

1.  **Install Charting Library:**
    *   **Location:** `stock-trading-ui` directory.
    *   **Action:** Install `lightweight-charts` for rendering financial charts.
    *   **Command:** `npm install lightweight-charts`

2.  **Create `RealtimeCandlestickChart` Component:**
    *   **File:** `stock-trading-ui/src/components/trading/RealtimeCandlestickChart.tsx` (new file)
    *   **Functionality:**
        *   Accepts `chartData: ChartCandle[]` as a prop.
        *   Uses `lightweight-charts` to render a candlestick chart.
        *   Implements logic to update the chart when `chartData` changes, specifically handling the appending of new candles or updating the last candle for real-time effect.

3.  **Update `useRealChartData` Hook:**
    *   **File:** `stock-trading-ui/src/hooks/useRealChartData.ts`
    *   **Action:**
        *   Add a new `timeframe` option, e.g., `'1m'`.
        *   When `timeframe` is `'1m'`, make an API call to the new backend endpoint `GET /api/chart/{stock_code}/minute`.
        *   Adjust `refreshInterval` for `'1m'` to be more frequent (e.g., 5-10 seconds) to update the *current* minute's candle.

4.  **Modify `KoreanTradingChart` Component:**
    *   **File:** `stock-trading-ui/src/components/trading/KoreanTradingChart.tsx`
    *   **Action:**
        *   Remove the existing mock chart rendering logic (the SVG path and `generateMockChartData`).
        *   Conditionally render the new `RealtimeCandlestickChart` component when `useRealData` is true and the selected `timeframe` is `'1m'`.
        *   Pass the `chartData` obtained from `useRealChartData` to `RealtimeCandlestickChart`.
        *   Add a UI control (e.g., a button or dropdown option) to select the "1분봉" (1-minute candle) timeframe.

5.  **Update `TestChartPage`:**
    *   **File:** `stock-trading-ui/src/app/test-chart/page.tsx`
    *   **Action:**
        *   Ensure `KoreanTradingChart` is passed `useRealData={true}` and `autoRefresh={true}`.
        *   Add a UI control (e.g., a button or dropdown) to select the "1분봉" (1-minute candle) timeframe for the `KoreanTradingChart`.

## 📊 Data Design Matching

### Frontend `KoreanStockChart` (or `ChartCandle` equivalent)
```typescript
export interface KoreanStockChart {
  timestamp: string; // ISO string for date/time (YYYY-MM-DDTHH:MM:SS)
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  // Optional fields for future expansion or if available from API
  tradingValue?: number;
  foreignBuy?: number;
  foreignSell?: number;
  institutionalBuy?: number;
  institutionalSell?: number;
  individualBuy?: number;
  individualSell?: number;
}
```

### Backend `ChartCandle` Pydantic Model
```python
from pydantic import BaseModel, Field
from typing import Optional

class ChartCandle(BaseModel):
    timestamp: str = Field(..., description="ISO 형식의 타임스탬프 (YYYY-MM-DDTHH:MM:SS)")
    open: float = Field(..., description="시가")
    high: float = Field(..., description="고가")
    low: float = Field(..., description="저가")
    close: float = Field(..., description="종가")
    volume: int = Field(..., description="거래량")
    tradingValue: Optional[float] = Field(None, description="거래대금")
    foreignBuy: Optional[int] = Field(None, description="외국인 순매수")
    foreignSell: Optional[int] = Field(None, description="외국인 순매도")
    institutionalBuy: Optional[int] = Field(None, description="기관 순매수")
    institutionalSell: Optional[int] = Field(None, description="기관 순매도")
    individualBuy: Optional[int] = Field(None, description="개인 순매수")
    individualSell: Optional[int] = Field(None, description="개인 순매도")
```

### Backend API Response Transformation
The `pd.DataFrame` returned by `ki_api.get_minute_chart_data` will be transformed into a list of `ChartCandle` objects.
*   `일자` (date) + `시간` (time) -> `timestamp` (ISO format)
*   `시가` -> `open`
*   `고가` -> `high`
*   `저가` -> `low`
*   `종가` -> `close`
*   `거래량` -> `volume`

---