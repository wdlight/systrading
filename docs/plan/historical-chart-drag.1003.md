# 과거 데이터 조회 및 차트 드래그 기능 구현 계획

**작성일**: 2025-10-03
**목표**: 차트에서 왼쪽 드래그 시 과거 데이터 자동 로드 및 초기 3일치 사전 로드

---

## 🎯 요구사항

### 핵심 기능
1. **차트에서 왼쪽 드래그 시 과거 데이터 자동 로드**
2. **초기 로딩 시 과거 3일치 데이터 사전 로드** (월요일 기준: 월/금/목/수)
3. **캐시 우선 사용** - 캐시 존재 시 API 호출 없이 즉시 로드
4. **거래일 기준** - 비거래일(주말/공휴일) 자동 스킵

---

## 📐 아키텍처 설계

### Phase 1: Backend - 다중 날짜 조회 API 개선

#### 1.1 새로운 API 엔드포인트
**파일**: `backend/app/api/chart.py`

```python
@router.get("/{stock_code}/minute-range")
async def get_minute_chart_data_range(
    stock_code: str,
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD, 미지정 시 오늘)"),
    max_days: int = Query(10, le=30, description="최대 조회 일수 (1~30)"),
):
    """
    지정된 날짜 범위의 분봉 데이터를 조회
    - 비거래일 자동 제외
    - 캐시 우선 사용
    - 최대 30일까지 조회 가능

    Returns:
        {
            "20251001": [360개 캔들],
            "20251002": [360개 캔들],
            "20251003": [360개 캔들]
        }
    """
```

#### 1.2 TradingService 메서드 추가
**파일**: `backend/app/services/trading_service.py`

```python
async def get_minute_chart_data_range(
    self,
    stock_code: str,
    end_date: datetime,
    max_days: int = 10
) -> Dict[str, List[ChartCandle]]:
    """
    날짜 범위의 분봉 데이터 조회

    전략:
    1. 종료일로부터 이전 N개 거래일 계산
    2. 각 날짜별로 get_minute_chart_data() 호출 (캐시 우선)
    3. 날짜별 딕셔너리로 반환
    """
```

#### 1.3 TradingCalendar 유틸리티 확장
**파일**: `backend/app/utils/trading_calendar.py`

```python
class TradingCalendar:
    @staticmethod
    def get_previous_trading_days(from_date: datetime, count: int) -> List[datetime]:
        """
        특정 날짜로부터 이전 N개 거래일 반환

        예: 월요일(10/6)로부터 3개 → [금(10/3), 목(10/2), 수(10/1)]
        """

    @staticmethod
    def get_trading_days_between(start: datetime, end: datetime) -> List[datetime]:
        """시작~종료 날짜 사이의 거래일 리스트 반환"""
```

---

### Phase 2: Frontend - 초기 로딩 시 과거 3일치 데이터 사전 로드

#### 2.1 ChartDataManager 확장
**파일**: `stock-trading-ui/src/components/trading/chart-adapters/core/ChartDataManager.ts`

```typescript
interface ChartDataManagerOptions {
  preloadDays?: number;  // 초기 로드할 과거 일수 (기본값: 3)
  enableHistoricalLoad?: boolean;  // 과거 데이터 로드 활성화
}

class ChartDataManager {
  private historicalData: Map<string, CandleData[]> = new Map();
  private oldestLoadedDate: Date | null = null;
  private isLoadingHistorical: boolean = false;

  async initialize(symbol: string, date?: Date) {
    // 1. 현재 날짜 데이터 로드
    await this.loadCurrentData(symbol, date);

    // 2. 과거 3일치 데이터 사전 로드 (백그라운드)
    if (this.options.enableHistoricalLoad) {
      this.preloadHistoricalData(symbol, this.options.preloadDays || 3);
    }
  }

  private async preloadHistoricalData(symbol: string, days: number) {
    const response = await fetch(
      `/api/chart/${symbol}/minute-range?` +
      `end_date=${formatDate(this.currentDate)}&max_days=${days}`
    );

    const dataByDate = await response.json();

    // 날짜별로 저장
    Object.entries(dataByDate).forEach(([date, candles]) => {
      this.historicalData.set(date, candles);
    });
  }

  async loadMoreHistoricalData(direction: 'past' | 'future') {
    if (direction === 'past' && !this.isLoadingHistorical) {
      this.isLoadingHistorical = true;
      await this.preloadHistoricalData(this.currentSymbol, 3);
      this.isLoadingHistorical = false;
    }
  }

  getAllData(): CandleData[] {
    // 모든 날짜 데이터를 시간순으로 병합
    const allDates = Array.from(this.historicalData.keys()).sort();
    return allDates.flatMap(date => this.historicalData.get(date) || []);
  }
}
```

#### 2.2 차트 어댑터에 드래그 이벤트 통합

**Recharts 어댑터**: `RechartsAdapter.tsx`
```typescript
const handleBrushChange = async (range: { startIndex: number; endIndex: number }) => {
  // 왼쪽 끝까지 드래그 시 과거 데이터 로드
  if (range.startIndex <= 5) {
    await dataManager.loadMoreHistoricalData('past');
    const updatedData = dataManager.getAllData();
    setChartData(updatedData);
  }

  setVisibleRange(range);
};
```

**Lightweight Charts 어댑터**: `LightweightChartsAdapter.tsx`
```typescript
chart.timeScale().subscribeVisibleLogicalRangeChange(async (range) => {
  if (!range) return;

  // 왼쪽 끝 (과거)에 도달 시
  if (range.from <= 10) {
    await dataManager.loadMoreHistoricalData('past');
    const updatedData = dataManager.getAllData();
    candlestickSeries.setData(updatedData);
  }
});
```

---

### Phase 3: 캐시 전략

#### 3.1 Backend 캐시 (이미 구현됨)
```python
# backend/app/services/chart_cache_service.py
# ✅ 이미 구현됨 - 변경 불필요

async def get_historical_minute_candles(...):
    # 1. 캐시 조회 (kordata/005930/20251001.json)
    cached = self._load_from_cache(stock_code, target_date)
    if cached:
        return cached  # 즉시 반환

    # 2. 캐시 없으면 API 호출 후 저장
    candles = await self._fetch_and_cache(...)
    return candles
```

#### 3.2 Frontend 메모리 캐시
```typescript
private historicalData: Map<string, CandleData[]> = new Map();
private readonly MAX_CACHED_DAYS = 30;

private evictOldData() {
  if (this.historicalData.size > this.MAX_CACHED_DAYS) {
    const oldestDate = Array.from(this.historicalData.keys()).sort()[0];
    this.historicalData.delete(oldestDate);
  }
}
```

---

## 🔄 데이터 흐름

### 초기 로딩 (월요일 10/6)

```
1. Frontend 초기화
   ↓
2. ChartDataManager.initialize("005930")
   ↓
3. 현재 날짜(월요일) 데이터 로드 → 차트 표시
   ↓
4. 백그라운드: 과거 3일치 사전 로드
   Backend API: /api/chart/005930/minute-range?end_date=2025-10-06&max_days=3
   ↓
5. Backend가 거래일 계산
   월요일(10/6) → 금요일(10/3) → 목요일(10/2) → 수요일(10/1)
   ↓
6. 각 날짜별로 캐시 조회 → 없으면 API 호출 (3회x3구간=9회)
   ↓
7. Frontend에 반환
   {
     "20251006": [360개],
     "20251003": [360개],
     "20251002": [360개],
     "20251001": [360개]
   }
   ↓
8. 메모리에 저장 완료
```

### 왼쪽 드래그 시

```
1. 사용자가 차트를 왼쪽으로 드래그
   ↓
2. visibleRange.from <= 5 감지
   ↓
3. dataManager.loadMoreHistoricalData('past')
   ↓
4. 추가 3일치 데이터 요청
   Backend API: /api/chart/005930/minute-range?end_date=2025-09-30&max_days=3
   ↓
5. 기존 데이터에 병합 → 차트 업데이트
```

---

## 📂 구현 파일 목록

### Backend (Phase 1)
1. `backend/app/utils/trading_calendar.py` - 거래일 계산 유틸리티
2. `backend/app/services/trading_service.py` - 범위 조회 메서드
3. `backend/app/api/chart.py` - 새 API 엔드포인트

### Frontend (Phase 2)
4. `stock-trading-ui/src/components/trading/chart-adapters/core/ChartDataManager.ts` - 사전 로드 로직
5. `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx` - 드래그 이벤트
6. `stock-trading-ui/src/components/trading/chart-adapters/LightweightChartsAdapter.tsx` - 드래그 이벤트

### 테스트
7. `backend/tests/test_chart_range.py` - Backend 테스트
8. `backend/tests/test_trading_calendar.py` - 거래일 계산 테스트

---

## 🧪 테스트 시나리오

### Backend 테스트
```python
async def test_get_minute_chart_data_range():
    """월요일 기준 과거 3일치 조회"""
    service = TradingService()

    end_date = datetime(2025, 10, 6)  # 월요일
    data = await service.get_minute_chart_data_range(
        "005930",
        end_date=end_date,
        max_days=3
    )

    assert len(data) == 4  # 월/금/목/수
    assert "20251006" in data
    assert "20251003" in data
    assert len(data["20251001"]) == 360
```

### Frontend 테스트
1. 페이지 로드 시 4일치 데이터 로드 확인
2. 네트워크 탭에서 `/minute-range` API 호출 1회 확인
3. 차트를 왼쪽으로 드래그 → 추가 데이터 로드 확인
4. 새로고침 후 캐시에서 즉시 로드 확인

---

## ⚠️ 주의사항

### 1. 성능 최적화
- 초기 로딩: 현재 날짜 먼저 표시 → 과거 데이터는 백그라운드
- 메모리 관리: 최대 30일치만 캐시 (LRU 전략)

### 2. API Rate Limit
- 캐시 활용으로 실제 API 호출은 최초 1회만
- 3일치 조회 = 9회 API 호출 (구간별 3회씩)

### 3. 비거래일 처리
- 주말/공휴일 자동 스킵
- 연휴 시 실제 거래일만 반환

### 4. 에러 처리
```typescript
try {
  await dataManager.loadMoreHistoricalData('past');
} catch (error) {
  console.error('❌ Failed to load historical data:', error);
  showErrorToast('과거 데이터를 불러오지 못했습니다.');
}
```

---

## 🎯 구현 우선순위

### Phase 1 (필수): Backend
1. ✅ 거래일 유틸리티 구현
2. ✅ TradingService 범위 조회 메서드
3. ✅ API 엔드포인트 추가
4. ✅ 테스트 작성

### Phase 2 (필수): Frontend 초기 로딩
1. ✅ ChartDataManager 확장
2. ✅ 사전 로드 로직
3. ✅ API 통합

### Phase 3 (선택): 드래그 기능
1. ⏳ Recharts 드래그 이벤트
2. ⏳ Lightweight Charts 드래그 이벤트
3. ⏳ 무한 스크롤 로직

---

## 📊 예상 결과

### 초기 로딩 후
```
Timeline: [수 360개] [목 360개] [금 360개] [월 360개]
          └─ 09:01~15:30 ─┘ └─ 09:01~15:30 ─┘

Visible:                                     [====월요일====]
```

### 왼쪽 드래그 후
```
Timeline: [화] [수] [목] [금] [월]

Visible:  [==화==][==수==][==목==]
```

---

**작성자**: Claude
**최종 업데이트**: 2025-10-03
