# 분봉 차트 일일 리셋 및 거래시간 관리 플랜

## 📋 현재 상황 분석

### 현재 구현
- **차트 페이지**: `http://localhost:9000/test-chart`
- **데이터 제한**: 120개 캔들까지만 표시
- **시간 필터링**: 없음 (모든 데이터 표시)
- **일일 리셋**: 없음 (데이터 계속 누적)

### 문제점
1. ❌ **120개 제한**: 장 시작 9:00부터 장 마감 15:30까지 약 390분(6.5시간) 동안의 모든 데이터를 보기 어려움
2. ❌ **일일 리셋 없음**: 전날 데이터가 섞여서 표시될 수 있음
3. ❌ **시간 필터링 없음**: 장 외 시간(시간외 거래 등) 데이터가 섞일 수 있음
4. ❌ **자동 갱신**: 매일 0시 자동 리셋 기능 없음

---

## 🎯 목표

### 상용화 요구사항
1. ✅ **일일 리셋**: 매일 0시에 자동으로 데이터 초기화
2. ✅ **거래시간 필터링**: 9:00 ~ 15:30 사이의 데이터만 표시
3. ✅ **데이터 확장**: 120개 제한 해제 → 당일 전체 분봉 데이터 표시 (최대 390개)
4. ✅ **시간외 거래 처리**: 필요시 시간외 거래(8:30~9:00, 15:30~16:00) 옵션 제공

---

## 📐 아키텍처 설계

### 1️⃣ Backend 레이어 (Python/FastAPI)

#### 파일 구조
```
backend/
├── app/
│   ├── core/
│   │   └── korea_invest.py          # ✏️ 수정: 시간 필터링 로직 추가
│   ├── services/
│   │   └── trading_service.py       # ✏️ 수정: 거래시간 검증
│   ├── api/
│   │   └── chart.py                 # ✏️ 수정: 날짜/시간 파라미터 추가
│   └── utils/
│       └── trading_hours.py         # 🆕 신규: 거래시간 유틸리티
```

#### 구현 내용

##### A. 거래시간 유틸리티 (`utils/trading_hours.py`)
```python
from datetime import datetime, time
from typing import Optional, Tuple
from enum import Enum

class TradingSession(Enum):
    """거래 세션 구분"""
    PRE_MARKET = "pre_market"      # 8:30 ~ 9:00 (시간외 종가)
    REGULAR = "regular"             # 9:00 ~ 15:30 (정규 장)
    AFTER_MARKET = "after_market"   # 15:30 ~ 16:00 (시간외 단일가)
    CLOSED = "closed"               # 장 외 시간

class TradingHoursManager:
    """한국 주식시장 거래시간 관리"""

    # 정규 장 시간
    REGULAR_MARKET_START = time(9, 0, 0)
    REGULAR_MARKET_END = time(15, 30, 0)

    # 시간외 거래 시간
    PRE_MARKET_START = time(8, 30, 0)
    AFTER_MARKET_END = time(16, 0, 0)

    @classmethod
    def get_session(cls, dt: datetime) -> TradingSession:
        """주어진 시간의 거래 세션 반환"""
        t = dt.time()

        if cls.PRE_MARKET_START <= t < cls.REGULAR_MARKET_START:
            return TradingSession.PRE_MARKET
        elif cls.REGULAR_MARKET_START <= t < cls.REGULAR_MARKET_END:
            return TradingSession.REGULAR
        elif cls.REGULAR_MARKET_END <= t < cls.AFTER_MARKET_END:
            return TradingSession.AFTER_MARKET
        else:
            return TradingSession.CLOSED

    @classmethod
    def is_regular_hours(cls, dt: datetime) -> bool:
        """정규 장 시간 여부"""
        return cls.get_session(dt) == TradingSession.REGULAR

    @classmethod
    def is_trading_hours(cls, dt: datetime, include_extended: bool = False) -> bool:
        """거래 시간 여부 (시간외 포함 옵션)"""
        session = cls.get_session(dt)
        if include_extended:
            return session in [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_MARKET]
        else:
            return session == TradingSession.REGULAR

    @classmethod
    def is_today(cls, dt: datetime) -> bool:
        """오늘 날짜인지 확인"""
        today = datetime.now().date()
        return dt.date() == today

    @classmethod
    def get_trading_day_start(cls, date: Optional[datetime] = None) -> datetime:
        """거래일의 시작 시간 (0시)"""
        if date is None:
            date = datetime.now()
        return datetime.combine(date.date(), time(0, 0, 0))

    @classmethod
    def get_regular_market_range(cls, date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """정규 장 시작/종료 시간"""
        if date is None:
            date = datetime.now()
        start = datetime.combine(date.date(), cls.REGULAR_MARKET_START)
        end = datetime.combine(date.date(), cls.REGULAR_MARKET_END)
        return start, end
```

##### B. Backend API 수정 (`api/chart.py`)
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.core.dependencies import get_trading_service
from app.services.trading_service import TradingService
from app.models.schemas import ChartCandle
from app.models.chart import ChartCandleResponse
from app.utils.trading_hours import TradingHoursManager
from loguru import logger

router = APIRouter(tags=["Chart"])

@router.get(
    "/{stock_code}/minute",
    response_model=List[ChartCandle],
    summary="분봉 차트 데이터 조회",
    description="특정 종목의 분봉 차트 데이터를 조회합니다. 거래시간 필터링 옵션 제공."
)
async def get_minute_chart_data(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service),
    date: Optional[str] = Query(None, description="조회 날짜 (YYYY-MM-DD). 미지정시 오늘"),
    include_extended_hours: bool = Query(False, description="시간외 거래 포함 여부"),
    regular_hours_only: bool = Query(True, description="정규 장 시간만 (9:00~15:30)")
) -> List[ChartCandle]:
    """
    분봉 차트 데이터 조회

    - regular_hours_only=True: 9:00 ~ 15:30만 (기본값)
    - include_extended_hours=True: 8:30 ~ 16:00 (시간외 포함)
    - 둘 다 False: 모든 데이터
    """
    try:
        # 날짜 파싱
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="잘못된 날짜 형식. YYYY-MM-DD 형식을 사용하세요.")

        # 차트 데이터 조회
        chart_data = await trading_service.get_minute_chart_data(
            stock_code=stock_code,
            target_date=target_date,
            include_extended_hours=include_extended_hours,
            regular_hours_only=regular_hours_only
        )

        if chart_data is None:
            raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다.")

        logger.info(f"분봉 데이터 조회 완료: {stock_code}, {len(chart_data)}개 캔들")
        return chart_data

    except Exception as e:
        logger.error(f"분봉 차트 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분봉 차트 데이터 조회 중 오류가 발생했습니다: {str(e)}")
```

##### C. Service 레이어 수정 (`services/trading_service.py`)
```python
from typing import Optional, List
from datetime import datetime

from app.models.schemas import ChartCandle
from app.utils.trading_hours import TradingHoursManager

class TradingService:
    async def get_minute_chart_data(
        self,
        stock_code: str,
        target_date: Optional[datetime] = None,
        include_extended_hours: bool = False,
        regular_hours_only: bool = True
    ) -> Optional[List[ChartCandle]]:
        """
        분봉 차트 데이터 조회 (거래시간 필터링 포함)
        """
        # 원본 데이터 조회
        raw_data = await self.korea_invest_service.get_minute_chart_data(stock_code)

        if not raw_data:
            return None

        # 필터링 로직
        filtered_data = []

        for candle in raw_data:
            # 타임스탬프 파싱
            try:
                candle_time = datetime.fromisoformat(candle.timestamp)
            except ValueError:
                logger.warning(f"잘못된 타임스탬프: {candle.timestamp}")
                continue

            # 날짜 필터링 (지정된 날짜만)
            if target_date and not TradingHoursManager.is_today(candle_time):
                if candle_time.date() != target_date.date():
                    continue
            elif not target_date and not TradingHoursManager.is_today(candle_time):
                # 날짜 미지정 시 오늘 데이터만
                continue

            # 거래시간 필터링
            if regular_hours_only:
                # 정규 장만 (9:00 ~ 15:30)
                if not TradingHoursManager.is_regular_hours(candle_time):
                    continue
            elif not include_extended_hours:
                # 시간외 미포함, 정규장만
                if not TradingHoursManager.is_regular_hours(candle_time):
                    continue
            else:
                # 시간외 포함 (8:30 ~ 16:00)
                if not TradingHoursManager.is_trading_hours(candle_time, include_extended=True):
                    continue

            filtered_data.append(candle)

        logger.info(f"필터링 완료: {len(raw_data)}개 → {len(filtered_data)}개")
        return filtered_data
```

##### D. Korea Invest API 수정 (`core/korea_invest.py`)
```python
# 기존 get_minute_chart_data 메서드는 유지
# 필터링은 Service 레이어에서 처리하므로 변경 불필요
# 다만, 120개 제한은 제거할 수 있음

async def get_minute_chart_data(self, stock_code: str) -> Optional[List[ChartCandle]]:
    """1분봉 차트 데이터 조회 (비동기)"""
    # ... 기존 로직 유지 ...

    # 한국투자증권 API는 기본적으로 120개 제한이 있을 수 있음
    # 더 많은 데이터가 필요하면 여러 번 호출하거나 API 파라미터 조정 필요
    pass
```

---

### 2️⃣ Frontend 레이어 (Next.js/React)

#### 파일 구조
```
stock-trading-ui/
├── src/
│   ├── hooks/
│   │   ├── useRealChartData.ts      # ✏️ 수정: 시간 필터링 파라미터
│   │   └── useTradingHours.ts       # 🆕 신규: 거래시간 Hook
│   ├── app/
│   │   └── test-chart/
│   │       └── page.tsx             # ✏️ 수정: UI 개선
│   └── lib/
│       └── utils/
│           └── tradingHours.ts      # 🆕 신규: 거래시간 유틸
```

#### 구현 내용

##### A. 거래시간 유틸리티 (`lib/utils/tradingHours.ts`)
```typescript
export enum TradingSession {
  PRE_MARKET = 'pre_market',
  REGULAR = 'regular',
  AFTER_MARKET = 'after_market',
  CLOSED = 'closed'
}

export class TradingHoursManager {
  private static REGULAR_MARKET_START = { hour: 9, minute: 0 };
  private static REGULAR_MARKET_END = { hour: 15, minute: 30 };
  private static PRE_MARKET_START = { hour: 8, minute: 30 };
  private static AFTER_MARKET_END = { hour: 16, minute: 0 };

  static getSession(date: Date): TradingSession {
    const hour = date.getHours();
    const minute = date.getMinutes();

    if (this.isTimeBetween(hour, minute, this.PRE_MARKET_START, this.REGULAR_MARKET_START)) {
      return TradingSession.PRE_MARKET;
    } else if (this.isTimeBetween(hour, minute, this.REGULAR_MARKET_START, this.REGULAR_MARKET_END)) {
      return TradingSession.REGULAR;
    } else if (this.isTimeBetween(hour, minute, this.REGULAR_MARKET_END, this.AFTER_MARKET_END)) {
      return TradingSession.AFTER_MARKET;
    } else {
      return TradingSession.CLOSED;
    }
  }

  static isRegularHours(date: Date): boolean {
    return this.getSession(date) === TradingSession.REGULAR;
  }

  static isTradingHours(date: Date, includeExtended: boolean = false): boolean {
    const session = this.getSession(date);
    if (includeExtended) {
      return [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_MARKET].includes(session);
    }
    return session === TradingSession.REGULAR;
  }

  static isToday(date: Date): boolean {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }

  static getNextResetTime(): Date {
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    return tomorrow;
  }

  static getTimeUntilReset(): number {
    const now = new Date();
    const nextReset = this.getNextResetTime();
    return nextReset.getTime() - now.getTime();
  }

  private static isTimeBetween(
    hour: number,
    minute: number,
    start: { hour: number; minute: number },
    end: { hour: number; minute: number }
  ): boolean {
    const timeInMinutes = hour * 60 + minute;
    const startInMinutes = start.hour * 60 + start.minute;
    const endInMinutes = end.hour * 60 + end.minute;
    return timeInMinutes >= startInMinutes && timeInMinutes < endInMinutes;
  }
}
```

##### B. Chart Data Hook 수정 (`hooks/useRealChartData.ts`)
```typescript
interface UseRealChartDataOptions {
  enabled?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  includeExtendedHours?: boolean;  // 🆕 시간외 거래 포함
  regularHoursOnly?: boolean;      // 🆕 정규장만
  targetDate?: string;             // 🆕 대상 날짜 (YYYY-MM-DD)
}

export function useRealChartData(
  stockCode: string,
  timeframe: string = 'D',
  options: UseRealChartDataOptions = {}
): UseRealChartDataReturn {
  const {
    enabled = true,
    autoRefresh = false,
    refreshInterval = timeframe === '1m' ? 5000 : 60000,
    includeExtendedHours = false,    // 기본값: 시간외 미포함
    regularHoursOnly = true,          // 기본값: 정규장만
    targetDate = undefined            // 기본값: 오늘
  } = options;

  // ... 기존 state ...

  const fetchChartData = useCallback(async (): Promise<void> => {
    if (!stockCode || !enabled) return;

    setIsLoading(true);
    setError(null);

    try {
      let url = '';
      if (timeframe === '1m') {
        // 쿼리 파라미터 추가
        const params = new URLSearchParams();
        if (targetDate) params.append('date', targetDate);
        params.append('include_extended_hours', String(includeExtendedHours));
        params.append('regular_hours_only', String(regularHoursOnly));

        url = `${API_BASE_URL}/api/chart/${stockCode}/minute?${params.toString()}`;
      } else {
        url = `${API_BASE_URL}/api/stocks/${stockCode}/chart?period=${timeframe}&format=frontend`;
      }

      // ... 나머지 로직 ...
    } catch (err) {
      // ... 에러 처리 ...
    }
  }, [stockCode, timeframe, enabled, includeExtendedHours, regularHoursOnly, targetDate]);

  // ... 나머지 로직 ...
}
```

##### C. Trading Hours Hook (`hooks/useTradingHours.ts`)
```typescript
'use client';

import { useState, useEffect } from 'react';
import { TradingHoursManager, TradingSession } from '@/lib/utils/tradingHours';

export function useTradingHours() {
  const [currentSession, setCurrentSession] = useState<TradingSession>(TradingSession.CLOSED);
  const [timeUntilReset, setTimeUntilReset] = useState<number>(0);
  const [isMarketOpen, setIsMarketOpen] = useState<boolean>(false);

  useEffect(() => {
    const updateStatus = () => {
      const now = new Date();
      setCurrentSession(TradingHoursManager.getSession(now));
      setTimeUntilReset(TradingHoursManager.getTimeUntilReset());
      setIsMarketOpen(TradingHoursManager.isRegularHours(now));
    };

    updateStatus();
    const interval = setInterval(updateStatus, 1000); // 1초마다 업데이트

    return () => clearInterval(interval);
  }, []);

  const formatTimeUntilReset = (): string => {
    const hours = Math.floor(timeUntilReset / (1000 * 60 * 60));
    const minutes = Math.floor((timeUntilReset % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeUntilReset % (1000 * 60)) / 1000);
    return `${hours}시간 ${minutes}분 ${seconds}초`;
  };

  return {
    currentSession,
    timeUntilReset,
    isMarketOpen,
    formatTimeUntilReset
  };
}
```

##### D. Test Chart Page 수정 (`app/test-chart/page.tsx`)
```typescript
export default function TestChartPage() {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [includeExtendedHours, setIncludeExtendedHours] = useState(false);
  const [regularHoursOnly, setRegularHoursOnly] = useState(true);

  // 거래시간 Hook
  const { currentSession, isMarketOpen, formatTimeUntilReset } = useTradingHours();

  // 차트 데이터 Hook (시간 필터링 옵션 추가)
  const {
    chartData,
    metadata,
    isLoading,
    error,
    isConnected,
    lastUpdated,
    refetch,
    retry
  } = useSamsungChartData('1m', {
    enabled: true,
    autoRefresh: autoRefresh && isMarketOpen, // 장 열렸을 때만 자동 새로고침
    includeExtendedHours,
    regularHoursOnly
  });

  return (
    <div className="min-h-screen bg-[#0a0a0b] p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          {/* ... 기존 헤더 ... */}

          {/* 🆕 거래시간 상태 표시 */}
          <div className="flex items-center gap-3">
            <Badge variant={isMarketOpen ? "default" : "outline"}>
              {isMarketOpen ? "장 진행 중" : "장 마감"}
            </Badge>
            <span className="text-sm text-gray-400">
              {currentSession === TradingSession.REGULAR && "정규장"}
              {currentSession === TradingSession.PRE_MARKET && "시간외 종가"}
              {currentSession === TradingSession.AFTER_MARKET && "시간외 단일가"}
              {currentSession === TradingSession.CLOSED && "장 외 시간"}
            </span>
          </div>
        </div>

        {/* 🆕 시간 필터링 옵션 */}
        <Card className="bg-[#1a1a1b] border-gray-700">
          <CardHeader>
            <CardTitle className="text-white">거래시간 설정</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={regularHoursOnly}
                  onChange={(e) => {
                    setRegularHoursOnly(e.target.checked);
                    if (e.target.checked) setIncludeExtendedHours(false);
                  }}
                  className="w-4 h-4"
                />
                <span className="text-white">정규장만 (9:00~15:30)</span>
              </label>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={includeExtendedHours}
                  onChange={(e) => {
                    setIncludeExtendedHours(e.target.checked);
                    if (e.target.checked) setRegularHoursOnly(false);
                  }}
                  className="w-4 h-4"
                />
                <span className="text-white">시간외 포함 (8:30~16:00)</span>
              </label>

              <div className="ml-auto text-sm text-gray-400">
                다음 리셋까지: {formatTimeUntilReset()}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* ... 나머지 UI ... */}
      </div>
    </div>
  );
}
```

---

### 3️⃣ 자동 리셋 메커니즘

#### 옵션 1: Frontend 자동 리셋 (권장)
```typescript
// app/test-chart/page.tsx
useEffect(() => {
  // 매일 0시 자동 새로고침
  const timeUntilMidnight = TradingHoursManager.getTimeUntilReset();

  const resetTimeout = setTimeout(() => {
    console.log('🔄 자동 리셋: 새로운 거래일 시작');
    refetch(); // 차트 데이터 다시 가져오기

    // 다음 리셋 예약 (24시간 후)
    const nextResetTimeout = setInterval(() => {
      refetch();
    }, 24 * 60 * 60 * 1000);

    return () => clearInterval(nextResetTimeout);
  }, timeUntilMidnight);

  return () => clearTimeout(resetTimeout);
}, [refetch]);
```

#### 옵션 2: Backend 스케줄러 (선택사항)
```python
# backend/app/scheduler/daily_reset.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import time

scheduler = AsyncIOScheduler()

async def reset_chart_cache():
    """매일 0시에 차트 캐시 초기화"""
    logger.info("🔄 Daily reset: Clearing chart cache...")
    # 캐시 초기화 로직
    # Redis나 메모리 캐시가 있다면 여기서 초기화

# 매일 0시에 실행
scheduler.add_job(
    reset_chart_cache,
    'cron',
    hour=0,
    minute=0,
    id='daily_chart_reset'
)

scheduler.start()
```

---

## 🔄 구현 순서

### Phase 1: Backend 기반 작업 (1-2일)
1. ✅ `utils/trading_hours.py` 생성 - 거래시간 유틸리티
2. ✅ `api/chart.py` 수정 - 쿼리 파라미터 추가
3. ✅ `services/trading_service.py` 수정 - 필터링 로직
4. ✅ Backend 테스트 - Postman/curl로 API 검증

### Phase 2: Frontend 개선 (1-2일)
1. ✅ `lib/utils/tradingHours.ts` 생성 - TS 유틸리티
2. ✅ `hooks/useTradingHours.ts` 생성 - 거래시간 Hook
3. ✅ `hooks/useRealChartData.ts` 수정 - 파라미터 추가
4. ✅ `app/test-chart/page.tsx` 수정 - UI 개선

### Phase 3: 자동 리셋 (1일)
1. ✅ Frontend 자동 리셋 구현
2. ✅ (선택) Backend 스케줄러 구현

### Phase 4: 테스트 및 검증 (1일)
1. ✅ 시간대별 필터링 동작 확인
2. ✅ 자동 리셋 동작 확인
3. ✅ 경계 케이스 테스트 (9:00, 15:30 정각 등)

---

## ✅ 검증 체크리스트

### Backend 검증
- [ ] `/api/chart/{stock_code}/minute` - 기본 호출 (정규장만)
- [ ] `/api/chart/{stock_code}/minute?regular_hours_only=true` - 9:00~15:30만
- [ ] `/api/chart/{stock_code}/minute?include_extended_hours=true` - 8:30~16:00
- [ ] `/api/chart/{stock_code}/minute?date=2025-01-15` - 특정 날짜

### Frontend 검증
- [ ] 정규장 시간 필터링 (9:00~15:30)
- [ ] 시간외 거래 포함 (8:30~16:00)
- [ ] 장 상태 표시 (진행 중/마감)
- [ ] 자동 리셋 카운트다운
- [ ] 매일 0시 자동 데이터 갱신

### 엣지 케이스
- [ ] 9:00 정각 데이터 포함 여부
- [ ] 15:30 정각 데이터 포함 여부
- [ ] 주말/공휴일 처리
- [ ] 데이터가 없는 경우 UI

---

## 📊 예상 결과

### Before (현재)
- ❌ 120개 캔들 제한
- ❌ 시간 필터링 없음
- ❌ 전날 데이터 섞임

### After (개선 후)
- ✅ 당일 전체 분봉 (최대 390개)
- ✅ 9:00~15:30 정규장 데이터만 표시
- ✅ 매일 0시 자동 리셋
- ✅ 시간외 거래 옵션 제공
- ✅ 실시간 장 상태 표시

---

## 🚀 추가 개선 아이디어 (향후)

1. **휴장일 처리**: 주말/공휴일 자동 감지
2. **데이터 캐싱**: Redis 캐싱으로 성능 개선
3. **과거 데이터 조회**: 날짜 선택 UI
4. **프리마켓 알림**: 장 시작 10분 전 알림
5. **장 마감 요약**: 15:30 이후 당일 요약 표시

---

## 📝 참고 문서

- 한국 증시 거래시간: https://www.krx.co.kr/
- FastAPI 스케줄러: https://apscheduler.readthedocs.io/
- Next.js 시간 처리: https://nextjs.org/docs

---

**작성일**: 2025-09-30
**버전**: 1.0.0
**상태**: ✅ 플랜 완료 - 구현 대기