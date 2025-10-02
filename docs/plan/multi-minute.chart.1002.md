# 다중 분봉 차트 구현 계획 (Multi-Timeframe Chart)

**문서 ID:** `multi-minute.chart.1002`
**작성일:** 2025-10-02
**최종 수정:** 2025-10-02 (v2.0 - 에러 처리 및 최적화 전략 추가)

## 1. 목표

현재 1분봉 위주로 제공되는 차트 기능을 확장하여, 사용자가 **1분, 5분, 10분, 30분** 등 다양한 시간 단위(Interval)를 선택하여 차트를 조회할 수 있도록 구현한다.

## 2. 핵심 전략

**백엔드 중심의 데이터 리샘플링 (Backend-Driven Resampling)**

- **원칙:** 클라이언트(프론트엔드)는 항상 최소한의 데이터만 받는다. 데이터 집계 및 가공(Resampling)은 모두 백엔드에서 처리한다.
- **근거:** 네트워크 효율성, 중앙화된 비즈니스 로직, 서버의 강력한 데이터 처리 성능 활용.
- **기술 스택:** 백엔드에서는 `pandas` 라이브러리를 사용하여 시계열 데이터를 효율적으로 리샘플링한다.
- **구현 전략:** 점진적 구현 (MVP → 최적화 → 캐싱)으로 빠른 배포와 안정성 확보

## 3. 수정 대상 파일 및 함수

### 3.1. Backend (FastAPI)

#### 1. 의존성 추가
- **파일:** `backend/requirements.txt`
- **작업:** `pandas` 라이브러리를 추가한다.
  ```
  pandas
  ```

#### 2. API 엔드포인트 수정
- **파일:** `backend/app/api/chart.py`
- **함수:** `get_minute_chart_data`
- **작업:**
    - `interval` 쿼리 파라미터를 추가하여 다양한 시간 단위를 받을 수 있도록 시그니처를 수정한다.
    - 기본값은 '1m'으로 설정한다.
    - **✅ 입력 검증 추가**: 정규식과 예외 처리로 유효성 검증
- **수정 전:**
  ```python
  async def get_minute_chart_data(
      stock_code: str,
      trading_service: TradingService = Depends(get_trading_service),
      date: Optional[str] = Query(None, ...),
      ...
  ) -> List[ChartCandle]:
  ```
- **수정 후 (검증 포함):**
  ```python
  from fastapi import HTTPException
  import logging
  import time

  logger = logging.getLogger(__name__)

  # ✅ 지원되는 interval 상수 정의
  VALID_INTERVALS = ['1m', '5m', '10m', '30m', '60m']

  async def get_minute_chart_data(
      stock_code: str,
      trading_service: TradingService = Depends(get_trading_service),
      interval: str = Query(
          '1m',
          regex='^(1m|5m|10m|30m|60m)$',  # ✅ 정규식 검증
          description="Time interval: 1m, 5m, 10m, 30m, 60m"
      ),
      date: Optional[str] = Query(None, ...),
      ...
  ) -> List[ChartCandle]:
      # ✅ 추가 검증 (이중 안전장치)
      if interval not in VALID_INTERVALS:
          raise HTTPException(
              status_code=400,
              detail=f"Invalid interval '{interval}'. Use: {VALID_INTERVALS}"
          )

      # ✅ 로깅 추가
      start_time = time.time()
      logger.info(f"📊 Chart request: {stock_code}, interval={interval}, date={date}")

      try:
          result = await trading_service.get_minute_chart_data(
              stock_code, interval, date, ...
          )

          # ✅ 성능 로깅
          elapsed = time.time() - start_time
          logger.info(f"✅ Chart response: {len(result)} candles in {elapsed:.2f}s")

          return result
      except Exception as e:
          logger.error(f"❌ Chart error: {stock_code}, interval={interval} - {str(e)}")
          raise
  ```

#### 2-1. 하위 호환성 유지 (선택 사항)
- **작업:** 기존 `/minute/full` 엔드포인트를 유지하여 기존 클라이언트 호환성 보장
  ```python
  @router.get("/{stock_code}/minute/full")
  async def get_minute_chart_data_legacy(
      stock_code: str,
      trading_service: TradingService = Depends(get_trading_service),
      date: Optional[str] = Query(None, ...),
      ...
  ) -> List[ChartCandle]:
      """Legacy endpoint - redirects to new endpoint with interval=1m"""
      return await get_minute_chart_data(stock_code, '1m', trading_service, date, ...)
  ```

#### 3. 서비스 로직 구현 (데이터 리샘플링)
- **파일:** `backend/app/services/trading_service.py`
- **함수:** `get_minute_chart_data` (또는 이 함수가 호출하는 내부 함수)
- **작업:**
    - `interval` 파라미터를 받도록 함수 시그니처를 수정한다.
    - `pandas`를 사용하여 데이터 리샘플링 로직을 구현한다.
    - **로직 순서:**
        1. 기존 로직대로 데이터 소스에서 **1분봉** 데이터를 조회한다.
        2. 조회된 데이터를 `pandas.DataFrame`으로 변환하고, 시간을 인덱스로 설정한다.
        3. `interval` 값이 '1m'이 아닐 경우, `df.resample(interval).agg(...)`를 사용하여 데이터를 집계한다.
            - `open`: `first`
            - `high`: `max`
            - `low`: `min`
            - `close`: `last`
            - `volume`: `sum`
        4. 집계 과정에서 발생한 결측치(`NaN`)는 `dropna()`로 제거한다.
        5. 최종 결과를 JSON 형태로 변환하여 반환한다.

### 3.2. Frontend (Next.js)

#### 1. 데이터 Fetching Hook 수정
- **파일:** `stock-trading-ui/src/hooks/useRealChartData.ts`
- **함수:** `fetchChartData` (내부 `useCallback` 함수)
- **작업:**
    - 현재 '1m'일 때와 아닐 때로 분기되는 URL 생성 로직을 통합하고, `timeframe` 값을 `interval` 쿼리 파라미터로 전달하도록 수정한다.
- **수정 전:**
  ```typescript
  let url = '';
  if (timeframe === '1m') {
    url = `${API_BASE_URL}/api/chart/${stockCode}/minute/full?${params.toString()}`;
  } else {
    url = `${API_BASE_URL}/api/stocks/${stockCode}/chart?period=${timeframe}&format=frontend`;
  }
  ```
- **수정 후 (제안):**
  ```typescript
  const params = new URLSearchParams();
  if (targetDate) params.append('date', targetDate);

  // 분봉, 일봉, 주봉 등을 모두 새로운 통합 API 엔드포인트로 처리하도록 변경
  // 여기서는 분봉(minute) 단위를 처리하는 로직을 수정
  const isMinuteChart = ['1m', '5m', '10m', '30m'].includes(timeframe);

  let url = '';
  if (isMinuteChart) {
      params.append('interval', timeframe); // <--- interval 파라미터 추가
      url = `${API_BASE_URL}/api/chart/${stockCode}/minute?${params.toString()}`;
  } else {
      // 일/주/월봉 처리 로직 (기존 유지 또는 통합)
      url = `${API_BASE_URL}/api/stocks/${stockCode}/chart?period=${timeframe}&format=frontend`;
  }
  ```

#### 2. 차트 컴포넌트 UI 수정
- **파일:** `stock-trading-ui/src/components/trading/KoreanTradingChart.tsx`
- **작업:**
    - 사용자가 선택할 시간 단위 UI를 수정/확장한다.
    - `ChartTimeframe` 타입을 새로운 분봉 단위를 포함하도록 확장한다.
    - `timeframes` 배열에 새로운 버튼 정보를 추가한다.
- **`ChartTimeframe` 타입 수정:**
  ```typescript
  // 수정 전
  type ChartTimeframe = '1m' | '1D' | '1W' | '1M' | '3M' | '6M' | '1Y';
  // 수정 후
  type ChartTimeframe = '1m' | '5m' | '10m' | '30m' | '1D' | '1W' | '1Y';
  ```
- **`timeframes` 배열 수정:**
  ```typescript
  // 수정 전
  const timeframes: { value: ChartTimeframe; label: string }[] = [
    { value: '1m', label: '1분' },
    { value: '1D', label: '1일' },
    ...
  ];
  // 수정 후
  const timeframes: { value: ChartTimeframe; label: string }[] = [
    { value: '1m', label: '1분' },
    { value: '5m', label: '5분' },   // <--- 추가
    { value: '10m', label: '10분' }, // <--- 추가
    { value: '30m', label: '30분' }, // <--- 추가
    { value: '1D', label: '1일' },
    ...
  ];
  ```
  - 이 컴포넌트는 이미 `timeframe` 상태를 `useRealChartData` 훅으로 전달하고 있으므로, 위 수정만으로 데이터 요청이 동적으로 변경된다.

## 4. 실행 순서 제안

1.  **Backend:** `requirements.txt`에 `pandas` 추가.
2.  **Backend:** `trading_service.py`에 리샘플링 로직 구현.
3.  **Backend:** `chart.py`의 API 엔드포인트에 `interval` 파라미터 추가.
4.  **Frontend:** `KoreanTradingChart.tsx`에 새로운 시간 단위(5m, 10m 등) 버튼 추가.
5.  **Frontend:** `useRealChartData.ts` 훅이 `interval` 파라미터를 API 요청 URL에 포함하도록 수정.
6.  **통합 테스트:** 프론트엔드에서 각 시간 단위 버튼을 클릭했을 때, 백엔드가 정상적으로 집계된 데이터를 반환하고 차트가 올바르게 렌더링되는지 확인.
