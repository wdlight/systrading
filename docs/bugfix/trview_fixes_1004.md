# 🐞 TRView 차트 표시 오류 수정 내역 (2025-10-04)

TRView 차트 구현 후 발생한 두 가지 주요 문제점에 대한 원인 분석 및 수정 내역을 기록합니다.

---

## 1. "차트 데이터 없음" 문제

###  sympton (문제 현상)
- `/trview` 페이지에 접속했을 때, 차트가 렌더링되지 않고 "차트 데이터 없음" 메시지가 표시됨.

### Root Cause (근본 원인)
- 날짜 확인 결과, 테스트를 진행한 **2025년 10월 4일은 토요일(비거래일)**이었음.
- 프론트엔드는 날짜 지정 없이 "오늘" 데이터를 요청했고, 백엔드는 비거래일이므로 데이터를 반환하지 않는 것이 정상 동작이었음.
- 이로 인해 API 응답으로 빈 배열(`[]`)이 반환되었고, 프론트엔드는 데이터가 없는 것으로 올바르게 처리함.

### Solution (해결 방안)
- 개발 및 데모 환경의 사용성 향상을 위해, **비거래일에 "오늘" 데이터를 요청하면 가장 최근 거래일의 데이터를 대신 반환**하도록 백엔드 로직을 수정함.
- **파일**: `backend/app/services/trading_service.py`
- **수정 내용**:
    1. `TradingCalendar` 유틸리티를 import 함.
    2. `get_minute_chart_data` 함수에 진입 시, 날짜 요청이 "오늘"이고 오늘이 비거래일인지 확인하는 로직 추가.
    3. 조건 충족 시, 조회 날짜(`query_date`)를 가장 최근 거래일로 동적으로 변경하여 데이터를 조회하도록 수정.

```python
# trading_service.py 수정된 부분

# ...
from app.utils.trading_calendar import TradingCalendar
# ...

class TradingService:
    # ...
    async def get_minute_chart_data(
        self,
        stock_code: str,
        target_date: Optional[datetime] = None,
        # ...
    ):
        # ...
        # 날짜 설정 (None이면 오늘)
        query_date = target_date if target_date else datetime.now()

        # 오늘 데이터 요청 시 비거래일이면 최근 거래일로 변경
        if target_date is None and not TradingCalendar.is_trading_day(query_date):
            try:
                last_trading_day = TradingCalendar.get_previous_trading_days(query_date, 1)[0]
                logger.info(f"오늘은 비거래일입니다. 최근 거래일({last_trading_day.strftime('%Y-%m-%d')}) 데이터로 대체합니다.")
                query_date = last_trading_day
            except IndexError:
                # ...

        # 이후 로직은 query_date를 사용하여 데이터 조회
        # ...
```

---

## 2. `chart.addCandlestickSeries is not a function` 런타임 오류

### sympton (문제 현상)
- 백엔드 데이터가 정상적으로 수신된 후, 프론트엔드에서 차트를 렌더링하는 과정에서 `Runtime TypeError` 발생.
- Next.js 오류 오버레이에 `chart.addCandlestickSeries is not a function` 메시지 표시.

### Root Cause (근본 원인)
- 설치된 `lightweight-charts` 라이브러리는 **v5**이지만, 작성된 코드는 **v4**의 API를 사용하고 있었음.
- **v4 API**: `chart.addCandlestickSeries()`, `chart.addHistogramSeries()` 등 개별 메서드 사용.
- **v5 API**: `chart.addSeries(SeriesType, ...)` 형태의 통합된 단일 메서드 사용.

### Solution (해결 방안)
- `lightweight-charts` v5 API 명세에 맞게 코드 전체를 수정함.
- **파일**: `stock-trading-ui/src/components/trading/TRViewChart.tsx`
- **수정 내용**:
    1.  **Import 구문 변경**: `CandlestickSeries`, `HistogramSeries` 등 Series의 타입을 명시적으로 import.
    2.  **Series 생성 코드 변경**: `chart.addCandlestickSeries()` 호출을 `chart.addSeries(CandlestickSeries, ...)`로 변경.
    3.  `chart.addHistogramSeries()` 호출을 `chart.addSeries(HistogramSeries, ...)`로 변경.

```typescript
// TRViewChart.tsx 수정된 부분

// 1. Import 구문 수정
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickSeries, // 추가
  HistogramSeries    // 추가
} from 'lightweight-charts';

// ...

// 2. Series 생성 코드 수정
const candleSeries = chart.addSeries(CandlestickSeries, {
  upColor: CHART_COLORS.CANDLE_UP,
  // ...
});

// ...

if (showVolume) {
  const volumeSeries = chart.addSeries(HistogramSeries, {
    priceFormat: { type: 'volume' },
    // ...
  });
  // ...
}
```

---

## 3. 차트 시간 축(Time Axis) 표시 오류

### sympton (문제 현상)
- 차트 하단의 시간 축이 한국 증시 시간(09:00, 10:00 등)이 아닌, 사용자의 브라우저 타임존 기준으로 표시됨 (예: 01:00, 02:00).

### Root Cause (근본 원인)
- `lightweight-charts` 라이브러리는 전달된 UTC 타임스탬프를 기본적으로 **사용자 브라우저의 로컬 타임존**에 맞춰 변환 후 표시함.
- 이로 인해 한국(UTC+9)이 아닌 다른 타임존의 사용자가 차트를 볼 경우, 시간 축이 의도와 다르게 표시됨.

### Solution (해결 방안)
- 차트의 `timeScale` 옵션에 `tickMarkFormatter`를 추가하여, 시간 축의 라벨을 항상 **한국 표준시(KST, Asia/Seoul)** 기준으로 강제 변환하도록 수정함.
- **파일**: `stock-trading-ui/src/lib/tradingview/chartConfig.ts`
- **수정 내용**:
    - `getTRViewChartOptions` 함수 내 `timeScale` 객체에 `tickMarkFormatter` 추가.
    - `Intl.DateTimeFormat` API를 사용하여 타임스탬프를 `Asia/Seoul` 타임존의 `HH:mm` 형식으로 포맷팅.

```typescript
// chartConfig.ts 수정된 부분
// ...
import { ChartOptions, DeepPartial, UTCTimestamp } from 'lightweight-charts';
// ...
timeScale: {
  // ...
  tickMarkFormatter: (time: UTCTimestamp) => {
    const date = new Date(time * 1000);
    // Intl.DateTimeFormat을 사용하여 한국 시간으로 포맷
    return new Intl.DateTimeFormat('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
      timeZone: 'Asia/Seoul',
    }).format(date);
  },
},
// ...
```