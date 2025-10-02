### 1. 일별 차트 관련 백엔드 핵심 함수

코드베이스 분석 결과, 일별 차트 데이터 처리는 다음 함수들이 담당합니다.

1.  **API 라우터 (Endpoint)**
    *   **파일:** `backend/app/api/stocks.py`
    *   **함수 (예상):** `get_stock_chart_data` (또는 유사한 이름)
    *   **경로 (예상):** `GET /api/stocks/{stock_code}/chart`
    *   **역할:** 프론트엔드로부터 `period=D` (일봉) 파라미터를 포함한 요청을 받아 `StockService`의 `get_chart_data` 함수를 호출합니다.

2.  **서비스 레이어 (Business Logic)**
    *   **파일:** `backend/app/services/stock_service.py`
    *   **함수:** `async def get_chart_data(self, stock_code: str, period: str)`
    *   **역할:** `period` 값('D', 'W', 'M')에 따라 조회 기간을 설정하고, 실제 데이터 소스(한국투자증권 API)에 데이터를 요청하는 핵심 로직을 수행합니다.

3.  **API 서비스 (External API Wrapper)**
    *   **파일:** `backend/app/core/korea_invest.py` (또는 하위 모듈)
    *   **함수:** `get_daily_price_chart` (또는 유사한 이름)
    *   **역할:** `stock_service`의 요청을 받아 한국투자증권 API의 명세에 맞는 형식으로 변환하여 외부 API를 직접 호출하고 응답을 반환합니다.

**요약:** 프론트엔드가 `period=D`로 요청하면, `stocks.py`가 받아서 `stock_service.py`의 `get_chart_data`를 실행하고, 이 함수는 최종적으로 `korea_invest.py`를 통해 외부 API에서 일봉 데이터를 가져오는 구조입니다.

---

### **2. 일별 차트 데이터 흐름 설계 (Flow Design)**

일별 차트 요청부터 화면에 그려지기까지의 전체 데이터 흐름은 다음과 같습니다.

1.  **[사용자]** 프론트엔드 UI에서 '일봉(1D)' 시간 단위 버튼을 클릭합니다.

2.  **[Frontend: `KoreanTradingChart.tsx`]** `timeframe` 상태가 '1D'로 변경됩니다. 이 컴포넌트는 `useRealChartData` 훅을 호출하고 있습니다.

3.  **[Frontend: `useRealChartData.ts`]** `timeframe` 상태 변경을 감지한 `useEffect` 훅이 재실행됩니다. `timeframe`이 '1m'이 아니므로, `period=D` 파라미터를 사용하여 백엔드 API를 호출할 URL을 생성합니다.
    *   `GET http://localhost:8000/api/stocks/005930/chart?period=D`

4.  **[Backend: `stocks.py`]** `/api/stocks/{stock_code}/chart` 경로의 API 라우터가 요청을 수신합니다. `stock_code`와 `period='D'` 값을 추출하여 `StockService`의 `get_chart_data` 함수를 호출합니다.

5.  **[Backend: `stock_service.py`]** `get_chart_data` 함수가 실행됩니다.
    *   조회 기간(예: 최근 1년)을 설정합니다.
    *   `KoreaInvestAPIService`의 일봉 조회 함수(`get_daily_price_chart`)를 `stock_code`, 기간, `period='D'`와 함께 호출합니다.

6.  **[Backend: `korea_invest.py`]** 한국투자증권 API 명세에 맞춰 요청을 보냅니다.

7.  **[External API]** 한국투자증권 서버에서 해당 종목의 일봉 데이터를 찾아 응답합니다.

8.  **[Backend: `stock_service.py`]** 외부 API로부터 받은 데이터를 `pandas` DataFrame 등으로 가공한 후, 프론트엔드가 사용하기 쉬운 JSON 배열 형태로 변환하여 반환합니다.

9.  **[Backend: `stocks.py`]** 서비스로부터 받은 JSON 데이터를 HTTP 응답(200 OK)으로 프론트엔드에 전송합니다.

10. **[Frontend: `useRealChartData.ts`]** `fetch`가 성공적으로 완료되고, 응답받은 JSON 데이터를 `chartData` 상태에 저장(`setChartData`)합니다.

11. **[Frontend: React Engine]** `chartData` 상태 변경으로 인해 `KoreanTradingChart` 및 하위 차트 렌더링 컴포넌트(`RealtimeCandlestickChart`)가 리렌더링됩니다.

12. **[사용자]** 화면의 차트가 새로운 일봉 데이터로 갱신된 것을 확인합니다.