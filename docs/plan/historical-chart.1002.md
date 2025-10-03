# 과거 분봉 차트 구현 계획 (Historical Chart Data)

**문서 ID:** `historical-chart.1002`
**작성일:** 2025-10-02
**최종 수정:** 2025-10-02 (v1.0 - 초안)

## 1. 목표

현재 **오늘 데이터만 표시**되는 분봉 차트를 확장하여:
- **과거 날짜(어제, 그제 등)의 전체 분봉 데이터** 조회 및 표시
- **다양한 시간 단위** 지원: 1분, 5분, 10분, 30분, **1시간**
- **차트 드래그**로 과거 데이터 자동 로딩
- **날짜/시간 표시**: MM-DD HH:MM 형식

---

## 2. 핵심 전략

### 2.1 API 선택 전략
| 상황 | 사용 API | TR_ID | 특징 |
|------|---------|-------|------|
| **당일 데이터** | `/inquire-time-itemchartprice` | FHKST03010230 | 실시간 업데이트, Gap-fill 지원 |
| **과거 데이터** | `/inquire-time-dailychartprice` | FHKST03010320 | 특정 날짜 전체 분봉 (09:00~15:30) |

### 2.2 데이터 흐름
```
사용자 액션 (날짜 선택 또는 차트 드래그)
  ↓
Frontend: 날짜 파라미터 전송 (YYYY-MM-DD)
  ↓
Backend: 날짜 판별
  ├─ 오늘: 기존 실시간 API → Gap-fill → 리샘플링
  └─ 과거: 신규 일자별 API → 영구 캐싱 → 리샘플링
  ↓
Frontend: 차트 렌더링 (MM-DD HH:MM 형식 표시)
```

### 2.3 캐싱 전략
- **당일 데이터**: 짧은 TTL (5분) + Gap-fill로 실시간성 유지
- **과거 데이터**: 영구 캐싱 (과거 데이터는 변경되지 않음)

---

## 3. Phase별 구현 계획

## 📌 Phase 1: Backend - 과거 데이터 API 구현 및 테스트

**목표**: 과거 날짜의 분봉 데이터를 가져오는 Backend 구축 및 검증

### 3.1 새로운 API 메서드 추가
**파일**: `brokers/korea_investment/ki_api.py`

```python
def get_daily_minute_chart_data(self, stock_code, target_date):
    """
    특정 날짜의 전체 분봉 데이터 조회 (과거 날짜용)

    API: /uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice
    TR_ID: FHKST03010320

    Args:
        stock_code (str): 종목코드 (예: "005930")
        target_date (datetime or str): 조회 날짜 (datetime 또는 "YYYYMMDD")

    Returns:
        DataFrame: 해당 날짜의 전체 분봉 데이터 (09:00~15:30)
        Columns: ['일자', '시간', '시가', '고가', '저가', '종가', '거래량']

    Example:
        >>> api.get_daily_minute_chart_data("005930", "20251001")
        >>> # 2025년 10월 1일의 삼성전자 전체 분봉 데이터 반환
    """
    url = '/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice'
    tr_id = 'FHKST03010320'

    # 날짜 형식 변환
    if isinstance(target_date, datetime):
        date_str = target_date.strftime("%Y%m%d")
    else:
        date_str = target_date

    params = {
        'FID_COND_MRKT_DIV_CODE': 'J',      # 주식시장
        'FID_INPUT_ISCD': stock_code,        # 종목코드
        'FID_INPUT_DATE_1': date_str,        # 조회 대상 날짜
        'FID_HOUR_CLS_CODE': '1',            # 1분봉 (1=1분, 2=5분, 3=10분, 등)
        'FID_PW_DATA_INCU_YN': 'Y'           # 가격 데이터 포함
    }

    logger.info(f"📅 과거 분봉 조회: {stock_code}, 날짜={date_str}")

    response = self._url_fetch(url, tr_id, params)

    if response is None or not response.is_ok():
        logger.warning(f"❌ 과거 데이터 조회 실패: {stock_code}, {date_str}")
        return pd.DataFrame()

    try:
        output2 = response.get_body().output2

        if not output2:
            logger.warning(f"⚠️ 데이터 없음: {stock_code}, {date_str}")
            return pd.DataFrame()

        # DataFrame 변환
        df = pd.DataFrame(output2)

        target_columns = [
            'stck_bsop_date',   # 영업일자
            'stck_cntg_hour',   # 체결시간
            'stck_oprc',        # 시가
            'stck_hgpr',        # 고가
            'stck_lwpr',        # 저가
            'stck_prpr',        # 종가
            'cntg_vol',         # 거래량
        ]

        output_columns = ['일자', '시간', '시가', '고가', '저가', '종가', '거래량']

        df = df[target_columns]
        df[target_columns[2:]] = df[target_columns[2:]].apply(pd.to_numeric)
        df.rename(columns=dict(zip(target_columns, output_columns)), inplace=True)

        # 시간 순으로 정렬 (과거 → 최신)
        df = df.sort_values(by='시간', ascending=True).reset_index(drop=True)

        logger.info(f"✅ 과거 데이터 {len(df)}개 수집 완료: {stock_code}, {date_str}")
        return df

    except Exception as e:
        logger.error(f"❌ 데이터 변환 실패: {stock_code}, {date_str}, 오류: {e}")
        return pd.DataFrame()
```

### 3.2 캐시 서비스 확장
**파일**: `backend/app/services/chart_cache_service.py`

```python
async def get_historical_minute_candles(
    self,
    stock_code: str,
    target_date: datetime,
    korea_invest_service
) -> Optional[List[ChartCandle]]:
    """
    과거 날짜의 분봉 데이터 조회 (영구 캐싱)

    Args:
        stock_code: 종목코드
        target_date: 조회 날짜
        korea_invest_service: KoreaInvestAPIService 인스턴스

    Returns:
        Optional[List[ChartCandle]]: 과거 날짜의 전체 분봉 데이터
    """
    # 1. 캐시 조회 (과거 데이터는 변경되지 않으므로 영구 캐싱)
    cached_data = self._load_from_cache(stock_code, target_date)

    if cached_data:
        logger.info(f"✅ Historical cache hit: {stock_code}, {target_date.strftime('%Y%m%d')}")
        return cached_data

    # 2. 비거래일 체크
    if not TradingCalendar.is_trading_day(target_date):
        logger.info(f"⚠️ 비거래일: {target_date.strftime('%Y%m%d')}, 이전 거래일 조회")
        previous_day = TradingCalendar.get_previous_trading_day(target_date)
        return await self.get_historical_minute_candles(
            stock_code, previous_day, korea_invest_service
        )

    # 3. 신규 API 호출 (일자별 분봉 데이터)
    logger.info(f"📅 과거 데이터 API 호출: {stock_code}, {target_date.strftime('%Y%m%d')}")

    try:
        df = await korea_invest_service.get_daily_minute_chart_data(
            stock_code, target_date
        )

        if df.empty:
            logger.warning(f"❌ 과거 데이터 없음: {stock_code}, {target_date.strftime('%Y%m%d')}")
            return None

        # DataFrame → ChartCandle 변환
        candles = self._convert_df_to_candles(df, target_date)

        # 4. 영구 캐싱 (과거 데이터는 변경되지 않음)
        self._save_to_cache(stock_code, target_date, candles)
        logger.info(f"💾 과거 데이터 캐싱 완료: {stock_code}, {target_date.strftime('%Y%m%d')}, {len(candles)}개")

        return candles

    except Exception as e:
        logger.error(f"❌ 과거 데이터 조회 실패: {stock_code}, {target_date.strftime('%Y%m%d')}, 오류: {e}")
        return None
```

### 3.3 Service Layer 통합
**파일**: `backend/app/services/trading_service.py`

```python
async def get_minute_chart_data(
    self,
    stock_code: str,
    target_date: Optional[datetime] = None,
    include_extended_hours: bool = False,
    regular_hours_only: bool = True
) -> Optional[List[ChartCandle]]:
    """
    분봉 데이터 조회 (날짜에 따라 API 자동 선택)

    - target_date가 오늘: 실시간 API + Gap-fill
    - target_date가 과거: 일자별 API + 영구 캐싱
    """
    query_date = target_date if target_date else datetime.now()

    # ✅ 오늘 vs 과거 날짜 판별
    is_today = query_date.date() == datetime.now().date()

    logger.info(f"📊 분봉 조회: {stock_code}, 날짜={query_date.strftime('%Y-%m-%d')}, 오늘여부={is_today}")

    if is_today:
        # 기존 로직: 실시간 API + Gap-fill
        raw_data = await self.chart_cache_service.get_minute_candles(
            stock_code=stock_code,
            target_date=query_date,
            korea_invest_service=self.korea_invest_service
        )
    else:
        # ✅ 신규 로직: 과거 날짜 전체 조회
        raw_data = await self.chart_cache_service.get_historical_minute_candles(
            stock_code=stock_code,
            target_date=query_date,
            korea_invest_service=self.korea_invest_service
        )

    if not raw_data:
        logger.warning(f"⚠️ 데이터 없음: {stock_code}, {query_date.strftime('%Y-%m-%d')}")
        return None

    # 필터링 로직 (기존 동일)
    # ... (생략)

    return filtered_data
```

### 3.4 API 엔드포인트 수정
**파일**: `backend/app/api/chart.py`

```python
@router.get("/{stock_code}/minute")
async def get_minute_chart_data(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service),
    date: Optional[str] = Query(None, description="조회 날짜 (YYYY-MM-DD). 미지정시 오늘"),
    interval: str = Query('1m', regex='^(1m|5m|10m|30m|60m)$', description="시간 단위"),
    include_extended_hours: bool = Query(False),
    regular_hours_only: bool = Query(True)
) -> List[ChartCandle]:
    """
    분봉 차트 데이터 조회 (당일 + 과거 날짜 지원)

    - date 없음: 오늘 데이터 (실시간)
    - date 있음: 해당 날짜 전체 데이터 (과거)
    - interval: 1m, 5m, 10m, 30m, 60m (1시간)
    """
    # 날짜 파싱
    target_date = None
    if date:
        try:
            target_date = datetime.strptime(date, "%Y-%m-%d")

            # ✅ 미래 날짜 방지
            if target_date.date() > datetime.now().date():
                raise HTTPException(400, "미래 날짜는 조회할 수 없습니다")

        except ValueError:
            raise HTTPException(400, "날짜 형식 오류. YYYY-MM-DD 형식을 사용하세요")

    # 데이터 조회 (자동으로 API 선택됨)
    chart_data = await trading_service.get_minute_chart_data(
        stock_code=stock_code,
        target_date=target_date,
        include_extended_hours=include_extended_hours,
        regular_hours_only=regular_hours_only
    )

    if not chart_data:
        raise HTTPException(404, "차트 데이터를 찾을 수 없습니다")

    # ✅ 리샘플링 (1m이 아닌 경우)
    if interval != '1m':
        chart_data = await trading_service.resample_candles(chart_data, interval)

    logger.info(f"✅ 차트 응답: {stock_code}, {len(chart_data)}개, interval={interval}")
    return chart_data
```

### 3.5 Backend 테스트 스크립트 작성
**파일**: `backend/tests/test_historical_chart.py`

```python
"""
과거 분봉 데이터 조회 테스트 스크립트
실행: python -m pytest backend/tests/test_historical_chart.py -v -s
또는: python backend/tests/test_historical_chart.py
"""
import asyncio
from datetime import datetime, timedelta
from app.services.trading_service import TradingService
from app.services.chart_cache_service import ChartCacheService
from brokers.korea_investment.ki_service import KoreaInvestAPIService

async def test_historical_data():
    """과거 데이터 조회 테스트"""

    # 서비스 초기화
    ki_service = KoreaInvestAPIService()
    cache_service = ChartCacheService()
    trading_service = TradingService(ki_service, cache_service)

    stock_code = "005930"  # 삼성전자

    # 테스트 1: 어제 데이터
    yesterday = datetime.now() - timedelta(days=1)
    print(f"\n📅 테스트 1: 어제 데이터 ({yesterday.strftime('%Y-%m-%d')})")
    data = await trading_service.get_minute_chart_data(
        stock_code=stock_code,
        target_date=yesterday
    )
    print(f"✅ 데이터 개수: {len(data) if data else 0}")
    if data and len(data) > 0:
        print(f"   첫 데이터: {data[0].timestamp}")
        print(f"   마지막 데이터: {data[-1].timestamp}")

    # 테스트 2: 그제 데이터
    two_days_ago = datetime.now() - timedelta(days=2)
    print(f"\n📅 테스트 2: 그제 데이터 ({two_days_ago.strftime('%Y-%m-%d')})")
    data = await trading_service.get_minute_chart_data(
        stock_code=stock_code,
        target_date=two_days_ago
    )
    print(f"✅ 데이터 개수: {len(data) if data else 0}")

    # 테스트 3: 오늘 데이터 (기존 API 검증)
    print(f"\n📅 테스트 3: 오늘 데이터")
    data = await trading_service.get_minute_chart_data(
        stock_code=stock_code,
        target_date=None  # 오늘
    )
    print(f"✅ 데이터 개수: {len(data) if data else 0}")

    print("\n🎉 모든 테스트 완료")

if __name__ == "__main__":
    asyncio.run(test_historical_data())
```

### ✅ Phase 1 완료 기준
- [ ] `ki_api.py`에 `get_daily_minute_chart_data()` 메서드 구현
- [ ] `chart_cache_service.py`에 `get_historical_minute_candles()` 메서드 구현
- [ ] `trading_service.py`에서 날짜 판별 로직 추가
- [ ] `chart.py` API에 `date` 파라미터 처리 추가
- [ ] 테스트 스크립트로 어제/그제/오늘 데이터 정상 조회 확인
- [ ] 캐시 동작 확인 (과거 데이터 영구 캐싱)

---

## 📌 Phase 2: Frontend - 차트 드래그 및 날짜 표시

**목표**: 차트 드래그로 과거 데이터 자동 로딩 및 MM-DD HH:MM 형식 표시

### 2.1 차트 어댑터 확장 (드래그 이벤트)
**파일**: `stock-trading-ui/src/components/trading/chart-adapters/ChartAdapter.tsx`

```typescript
export interface ChartAdapter {
  // 기존 메서드들...

  // ✅ 새로운 메서드: 드래그/스크롤 이벤트 핸들링
  onChartDrag?: (direction: 'left' | 'right', distance: number) => void;
  onChartScrollEnd?: (visibleRange: { start: Date; end: Date }) => void;

  // ✅ 날짜 포맷터
  formatTimestamp?: (timestamp: string) => string;
}
```

### 2.2 Recharts 어댑터 구현
**파일**: `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx`

```tsx
import { format, parseISO } from 'date-fns';
import { ko } from 'date-fns/locale';

export const RechartsAdapter: ChartAdapter = {
  // ... 기존 코드

  // ✅ 타임스탬프 포맷터: MM-DD HH:MM
  formatTimestamp: (timestamp: string) => {
    try {
      const date = parseISO(timestamp);
      return format(date, 'MM-dd HH:mm', { locale: ko });
    } catch {
      return timestamp;
    }
  },

  // ✅ X축 라벨 커스터마이징
  renderXAxis: () => (
    <XAxis
      dataKey="timestamp"
      tickFormatter={(value) => {
        // MM-DD HH:MM 형식
        return RechartsAdapter.formatTimestamp?.(value) || value;
      }}
      angle={-45}
      textAnchor="end"
      height={80}
    />
  ),

  // ✅ 차트 드래그 핸들러 (추후 구현)
  onChartDrag: (direction, distance) => {
    console.log(`차트 드래그: ${direction}, 거리: ${distance}px`);
    // TODO: 이전/다음 날짜 데이터 로딩 트리거
  }
};
```

### 2.3 Hook 개선 - 날짜 관리
**파일**: `stock-trading-ui/src/hooks/useRealChartData.ts`

```typescript
interface UseRealChartDataOptions {
  enabled?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  includeExtendedHours?: boolean;
  regularHoursOnly?: boolean;
  targetDate?: string;  // ✅ YYYY-MM-DD 형식
}

export function useRealChartData(
  stockCode: string,
  timeframe: string = '1m',
  options: UseRealChartDataOptions = {}
): UseRealChartDataReturn {
  const { targetDate, enabled = true } = options;

  const fetchChartData = useCallback(async () => {
    if (!stockCode || !enabled) return;

    const params = new URLSearchParams();

    // ✅ 날짜 파라미터 추가
    if (targetDate) {
      params.append('date', targetDate);
    }

    // ✅ interval 파라미터 추가 (1m, 5m, 10m, 30m, 60m)
    if (['1m', '5m', '10m', '30m', '60m'].includes(timeframe)) {
      params.append('interval', timeframe);
      url = `${API_BASE_URL}/api/chart/${stockCode}/minute?${params.toString()}`;
    } else {
      url = `${API_BASE_URL}/api/stocks/${stockCode}/chart?period=${timeframe}`;
    }

    const response = await fetch(url);
    const data = await response.json();

    setChartData(data);
    setLastUpdated(new Date());
  }, [stockCode, timeframe, targetDate, enabled]);

  // ✅ targetDate 변경 시 자동 리페치
  useEffect(() => {
    if (enabled) {
      fetchChartData();
    }
  }, [stockCode, timeframe, targetDate, enabled, fetchChartData]);

  return {
    chartData,
    isLoading,
    error,
    refetch: fetchChartData,
    // ✅ 날짜 변경 헬퍼
    loadPreviousDay: () => {
      // 이전 날짜 로딩 로직
    },
    loadNextDay: () => {
      // 다음 날짜 로딩 로직
    }
  };
}
```

### 2.4 차트 컴포넌트 UI - 날짜 네비게이션
**파일**: `stock-trading-ui/src/components/trading/KoreanTradingChart.tsx`

```tsx
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, CalendarIcon } from 'lucide-react';
import { format, subDays, addDays } from 'date-fns';

export function KoreanTradingChart({ stockCode }: Props) {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(undefined);
  const [timeframe, setTimeframe] = useState<ChartTimeframe>('1m');

  const { chartData, isLoading, loadPreviousDay, loadNextDay } = useRealChartData(
    stockCode,
    timeframe,
    {
      targetDate: selectedDate ? format(selectedDate, 'yyyy-MM-dd') : undefined,
      enabled: true
    }
  );

  // ✅ 날짜 변경 핸들러
  const handlePreviousDay = () => {
    if (selectedDate) {
      setSelectedDate(subDays(selectedDate, 1));
    } else {
      setSelectedDate(subDays(new Date(), 1));
    }
  };

  const handleNextDay = () => {
    if (!selectedDate) return; // 오늘보다 미래는 불가

    const nextDate = addDays(selectedDate, 1);
    if (nextDate <= new Date()) {
      setSelectedDate(nextDate);
    }
  };

  return (
    <div className="space-y-4">
      {/* ✅ 날짜 네비게이션 UI */}
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center gap-2">
          {/* 이전 날짜 */}
          <Button
            variant="outline"
            size="icon"
            onClick={handlePreviousDay}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          {/* 날짜 선택기 */}
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="min-w-[150px]">
                <CalendarIcon className="mr-2 h-4 w-4" />
                {selectedDate ? format(selectedDate, 'yyyy-MM-dd') : '오늘'}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar
                mode="single"
                selected={selectedDate}
                onSelect={setSelectedDate}
                disabled={(date) => date > new Date()}
                initialFocus
              />
            </PopoverContent>
          </Popover>

          {/* 다음 날짜 */}
          <Button
            variant="outline"
            size="icon"
            onClick={handleNextDay}
            disabled={!selectedDate || selectedDate >= new Date()}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>

          {/* 빠른 선택 */}
          <Button
            variant="ghost"
            onClick={() => setSelectedDate(undefined)}
          >
            오늘
          </Button>
        </div>

        {/* ✅ 시간 단위 선택 (1시간 추가) */}
        <div className="flex gap-2">
          {['1m', '5m', '10m', '30m', '60m'].map((tf) => (
            <Button
              key={tf}
              variant={timeframe === tf ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeframe(tf as ChartTimeframe)}
            >
              {tf === '60m' ? '1시간' : tf}
            </Button>
          ))}
        </div>
      </div>

      {/* ✅ 차트 렌더링 */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
        </div>
      ) : (
        <ChartRenderer
          data={chartData}
          adapter={RechartsAdapter}
          height={600}
        />
      )}
    </div>
  );
}
```

### 2.5 타입 정의 업데이트
**파일**: `stock-trading-ui/src/types/chart.ts`

```typescript
// ✅ 1시간 추가
export type ChartTimeframe = '1m' | '5m' | '10m' | '30m' | '60m' | '1D' | '1W' | '1Y';

export interface UseRealChartDataReturn {
  chartData: KoreanStockChart[];
  metadata: ChartApiResponse['metadata'] | null;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
  retry: () => Promise<void>;

  // ✅ 날짜 네비게이션 헬퍼
  loadPreviousDay?: () => void;
  loadNextDay?: () => void;
}
```

### ✅ Phase 2 완료 기준
- [ ] 날짜 선택 UI (Calendar Popover) 구현
- [ ] 이전/다음 날짜 버튼 동작 확인
- [ ] `useRealChartData` Hook에서 `targetDate` 파라미터 전달
- [ ] 차트 X축 라벨이 MM-DD HH:MM 형식으로 표시
- [ ] 1시간(60m) 버튼 추가 및 동작 확인
- [ ] 과거 날짜 선택 시 데이터 정상 로딩 확인
- [ ] 오늘 선택 시 실시간 데이터 표시 확인

---

## 🔮 TODO: Next Phase (미구현 항목)

### Phase 3: 차트 드래그 자동 로딩
- [ ] 차트를 왼쪽으로 드래그 시 이전 날짜 데이터 자동 로딩
- [ ] 차트를 오른쪽으로 드래그 시 다음 날짜 데이터 자동 로딩
- [ ] 무한 스크롤 방식으로 여러 날짜 데이터 연속 표시
- [ ] 드래그 중 로딩 인디케이터 표시

### Phase 4: 다중 날짜 데이터 통합 차트
- [ ] 여러 날짜의 데이터를 하나의 차트에 연속으로 표시
- [ ] 날짜 경계선 표시 (시각적 구분)
- [ ] 데이터 프리로딩 (미리 앞뒤 날짜 캐싱)

### Phase 5: 성능 최적화
- [ ] 과거 데이터 로딩 성능 모니터링
- [ ] 캐시 용량 관리 전략 (오래된 데이터 자동 삭제)
- [ ] 리샘플링 성능 최적화 (Pandas → 병렬 처리)
- [ ] 로깅 및 에러 처리 강화

### Phase 6: 추가 기능
- [ ] 날짜 범위 선택 (시작일 ~ 종료일)
- [ ] 데이터 다운로드 (CSV, Excel)
- [ ] 차트 비교 모드 (여러 날짜 비교)
- [ ] 거래량 프로필 표시

---

## 📝 참고 사항

### API 제약사항
- 한국투자증권 API는 **당일 데이터만 실시간** 제공
- 과거 데이터는 **일자별 API**로 전체 조회 필요
- API 호출 제한: 초당 20건 (Rate Limiting 고려 필요)

### 캐싱 전략
- **당일 데이터**: 짧은 TTL (5분) → 실시간성 유지
- **과거 데이터**: 영구 캐싱 → 빠른 재조회

### 시간대 처리
- 한국 시장 거래 시간: 09:00 ~ 15:30
- 시간외 거래: 08:30 ~ 09:00, 15:30 ~ 16:00
- 타임스탬프는 ISO 8601 형식 사용 (`YYYY-MM-DDTHH:MM:SS`)

---

## ✅ 최종 검증 항목

### Backend
- [ ] 과거 날짜 데이터 정상 조회 (어제, 그제, 일주일 전 등)
- [ ] 비거래일 처리 (자동으로 이전 거래일 반환)
- [ ] 미래 날짜 요청 시 400 에러 반환
- [ ] 캐시 동작 확인 (과거 데이터는 두 번째 요청부터 빠름)
- [ ] 1시간봉(60m) 리샘플링 정상 동작

### Frontend
- [ ] 날짜 선택 UI 정상 동작
- [ ] 이전/다음 날짜 버튼 정상 동작
- [ ] "오늘" 버튼으로 현재 날짜로 복귀
- [ ] 차트 X축 라벨이 MM-DD HH:MM 형식
- [ ] 1시간 버튼 클릭 시 차트 정상 표시
- [ ] 로딩 상태 표시
- [ ] 에러 메시지 표시

---

**문서 끝**
