# Cache Gap-Fill 및 실시간 Polling 구현 완료

**날짜**: 2025-10-02
**작업자**: Claude
**목표**: 사용자 재접속 시 Cache Gap 자동 채우기 + 실시간 1분 Polling 구현

---

## 📋 문제 상황

### 1차 문제: Cache Gap 발생
- **증상**: Cache 파일이 11:18까지만 데이터 보유 (129 candles)
- **시나리오**: 사용자가 12:10에 재접속 시 gap 발생 (11:19~12:10 누락)
- **원인**: Cache miss 시 전체 API 호출만 가능, gap 구간만 채우는 로직 없음

### 2차 문제: 실시간 Polling 미작동
- **증상**: 12:38 이후 cache 업데이트 정지
- **원인**: `/echart` 페이지가 `useInfiniteChartData` 훅을 사용하지 않음
- **결과**: 60초 polling 미실행, cache 자동 업데이트 안됨

---

## ✅ 구현 내용

### 1. Backend: Cache Gap-Fill 로직 구현

#### 📁 파일: `backend/app/services/chart_cache_service.py`

#### 추가된 메서드:

**1) `_needs_gap_fill()` - Gap 감지 (Lines 108-160)**
```python
def _needs_gap_fill(
    self,
    cached_candles: List[ChartCandle],
    target_date: datetime
) -> bool:
    """
    Gap fill이 필요한지 판단

    조건:
    - 오늘 날짜만 체크
    - 거래시간 또는 장 종료 후 체크
    - Cache 마지막 시간이 현재보다 2분 이상 이전이면 gap 존재
    """
    # 오늘 날짜가 아니면 gap-fill 불필요
    if target_date.date() != datetime.now().date():
        return False

    # 거래시간 체크
    now = datetime.now()
    from app.utils.trading_hours import TradingHoursManager
    if not TradingHoursManager.is_trading_hours(now):
        if now.hour < 15 or (now.hour == 15 and now.minute < 30):
            return False

    # Cache의 마지막 캔들 시간 확인
    latest_cached = max(
        cached_candles,
        key=lambda c: datetime.fromisoformat(c.timestamp)
    )
    latest_time = datetime.fromisoformat(latest_cached.timestamp)

    # 2분 이상 차이나면 gap 존재
    gap_minutes = (now - latest_time).total_seconds() / 60

    if gap_minutes >= 2:
        logger.info(
            f"Gap detected: latest={latest_time.strftime('%H:%M')}, "
            f"now={now.strftime('%H:%M')}, gap={gap_minutes:.1f}분"
        )
        return True

    return False
```

**2) `_fill_gap()` - Gap 채우기 (Lines 162-218)**
```python
def _fill_gap(
    self,
    cached_candles: List[ChartCandle],
    api_candles: List[ChartCandle]
) -> List[ChartCandle]:
    """
    Cache gap을 API 데이터로 채움

    동작:
    1. Cache의 마지막 시간 확인
    2. API에서 해당 시간 이후 데이터만 추출
    3. 병합 및 중복 제거 (timestamp 기준)
    4. 시간순 정렬
    """
    # 1. Cache의 마지막 시간
    latest_cached = max(
        cached_candles,
        key=lambda c: datetime.fromisoformat(c.timestamp)
    )
    gap_start_time = datetime.fromisoformat(latest_cached.timestamp)

    # 2. API에서 gap 이후 데이터만 추출
    gap_candles = []
    for candle in api_candles:
        candle_time = datetime.fromisoformat(candle.timestamp)
        if candle_time > gap_start_time:
            gap_candles.append(candle)

    logger.info(
        f"Gap 채우기: {len(gap_candles)}개 새 캔들 추가 "
        f"(after {gap_start_time.strftime('%H:%M')})"
    )

    # 3. 병합 및 중복 제거
    all_candles = cached_candles + gap_candles
    unique_map = {candle.timestamp: candle for candle in all_candles}

    # 4. 시간순 정렬
    sorted_candles = sorted(
        unique_map.values(),
        key=lambda c: datetime.fromisoformat(c.timestamp)
    )

    logger.info(
        f"Gap fill 완료: {len(cached_candles)}개 → {len(sorted_candles)}개 "
        f"(+{len(sorted_candles) - len(cached_candles)}개)"
    )

    return sorted_candles
```

**3) `get_minute_candles()` 수정 - Gap-Fill 통합 (Lines 220-298)**
```python
async def get_minute_candles(
    self,
    stock_code: str,
    target_date: datetime,
    api_fallback: Callable,
    skip_cache_save: bool = False
) -> Optional[List[ChartCandle]]:
    """
    분봉 데이터 조회 (캐시 우선, gap-fill 지원)
    """
    # 1. 캐시에서 조회 시도
    cached_data = self._load_from_cache(stock_code, target_date)

    # 2. Gap 감지 및 채우기 ✨ NEW
    if cached_data and self._needs_gap_fill(cached_data, target_date):
        logger.info(f"Gap 감지, 채우기 시작: {stock_code}")

        try:
            # API 호출하여 전체 데이터 가져오기
            api_data = await api_fallback(stock_code)

            if api_data:
                # Gap 채우기 (cache 마지막 이후 데이터만 병합)
                filled_data = self._fill_gap(cached_data, api_data)

                # 캐시 저장
                if not skip_cache_save:
                    self._save_to_cache(stock_code, target_date, filled_data)

                return filled_data
            else:
                # API 실패 시 기존 캐시 반환
                return cached_data

        except Exception as e:
            logger.error(f"Gap fill 실패: {stock_code}, 오류: {e}")
            return cached_data

    # 3. Cache hit (gap 없음)
    if cached_data:
        return cached_data

    # 4. 거래일이 아닌 경우 이전 거래일 데이터 반환
    if not TradingCalendar.is_trading_day(target_date):
        previous_trading_day = TradingCalendar.get_previous_trading_day(target_date)
        return await self.get_minute_candles(stock_code, previous_trading_day, api_fallback, skip_cache_save)

    # 5. API 호출하여 데이터 가져오기
    candles = await api_fallback(stock_code)
    if candles and not skip_cache_save:
        self._save_to_cache(stock_code, target_date, candles)

    return candles
```

**4) Import 수정**
```python
# Line 131: 올바른 모듈에서 import
from app.utils.trading_hours import TradingHoursManager
```

---

### 2. Frontend: 실시간 Polling 활성화

#### 📁 파일: `stock-trading-ui/src/app/echart/page.tsx`

**변경 전** (실시간 polling 없음):
```typescript
'use client';

import React, { useEffect, useState } from 'react';
import EChartsCandlestickChart from '@/components/trading/EChartsCandlestickChart';
import { chartAPI } from '@/lib/chart-api';
import { ChartCandle } from '@/types/korean-stocks';

export default function EChartTestPage() {
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadChartData() {
      setLoading(true);
      const data = await chartAPI.getMinuteCandles("005930");
      setChartData(data);
      setLoading(false);
    }
    loadChartData();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1>ECharts 캔들스틱 차트 테스트</h1>
      <Card>
        <CardHeader>
          <CardTitle>삼성전자 (005930) 캔들 차트</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <p>차트 데이터를 불러오는 중...</p>}
          {!loading && chartData.length > 0 && (
            <EChartsCandlestickChart chartData={chartData} height={500} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

**변경 후** (실시간 polling 포함):
```typescript
'use client';

import React from 'react';
import InfiniteScrollCandlestickChart from '@/components/trading/InfiniteScrollCandlestickChart';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function EChartTestPage() {
  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-white">실시간 캔들스틱 차트</h1>
      <Card className="bg-gray-800 border-gray-700 text-white">
        <CardHeader>
          <CardTitle className="text-xl">삼성전자 (005930) - 실시간 업데이트</CardTitle>
        </CardHeader>
        <CardContent>
          <InfiniteScrollCandlestickChart
            stockCode="005930"
            height={500}
            timeframe="1m"
            chartLibrary="recharts"
            maxDays={5}
            loadThreshold={20}
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

**핵심 변경**:
- `InfiniteScrollCandlestickChart` 컴포넌트 사용
- 내부적으로 `useInfiniteChartData` 훅 실행
- 60초마다 `/minute/current` API 호출
- Cache 자동 업데이트

---

## 🔄 전체 동작 흐름

### Scenario: Cache 11:18 → 사용자 12:10 접속

```
1️⃣ 사용자 접속 (12:10)
   ↓
2️⃣ Frontend: chartAPI.getFullDayCandles("005930")
   ↓
3️⃣ Backend: ChartCacheService.get_minute_candles()
   - Cache 로드: 9:00~11:18 (129개)
   - Gap 감지: latest=11:18 < now=12:10 ✅
   ↓
4️⃣ Gap Fill 트리거
   - API 조회: korea_invest.get_minute_chart_data()
   - 전체 데이터: 9:00~12:10 (203개)
   ↓
5️⃣ _fill_gap() 실행
   - Cache: 9:00~11:18 (129개)
   - Gap: 11:19~12:10 (74개 새로 추가)
   - Merged: 9:00~12:10 (203개)
   ↓
6️⃣ Cache 저장: 20251002.dat 업데이트 (203개)
   ↓
7️⃣ Frontend: 203개 candles 수신 및 렌더링
   ↓
8️⃣ Real-time polling 시작 (60초마다)
   - 12:11 → /minute/current → cache 업데이트
   - 12:12 → /minute/current → cache 업데이트
   - ...계속
```

### Real-time Polling Flow

```
Frontend (useInfiniteChartData)
    ↓ (every 60s)
GET /api/chart/005930/minute/current
    ↓
Backend: get_current_minute_candle()
    ↓
1. API 호출: korea_invest.get_minute_chart_data()
2. 최신 캔들 추출: max(candles, key=timestamp)
3. Cache 자동 업데이트: update_minute_candle()
4. 최신 캔들 반환
    ↓
Frontend: 차트 실시간 갱신
```

---

## 📊 테스트 결과

### 1. Gap-Fill 테스트
```bash
# Before
Cache: 129 candles (9:10~11:18)
Gap: 11:19~12:32

# API 호출 후
✅ Gap detected: latest=11:18, now=12:32, gap=74.0분
✅ Gap 채우기: 74개 새 캔들 추가 (after 11:18)
✅ Gap fill 완료: 129개 → 203개 (+74개)

# Cache 저장
kordata/005930/20251002.dat: 203 candles
```

### 2. Real-time Polling 테스트 (Playwright)
```bash
🔍 Testing /echart page polling...

📍 Loading http://localhost:9000/echart

⏳ Waiting 3 minutes...

📝 [useInfiniteChartData] Starting real-time polling for 005930
✅ [64s] /minute/current called (count: 1)
✅ [126s] /minute/current called (count: 2)

=== Result ===
API calls: 2 (expected: ~3)
✅ Polling working
```

### 3. Cache 업데이트 확인
```bash
# Before (문제 상황)
Cache: 209 candles (last: 12:38)
Status: 정체됨 ❌

# After (수정 후)
Cache: 236 candles (last: 12:55)
Status: 매분 업데이트됨 ✅

Last 5 candles:
  2025-10-02T12:51:00 - vol: 46301
  2025-10-02T12:52:00 - vol: 43283
  2025-10-02T12:53:00 - vol: 21048
  2025-10-02T12:54:00 - vol: 3413
  2025-10-02T12:55:00 - vol: 3391
```

---

## 🎯 검증 완료

### ✅ Gap-Fill 기능
- [x] Cache gap 자동 감지 (2분 이상 차이)
- [x] API 호출하여 gap 구간 데이터만 추출
- [x] 기존 cache와 병합 (중복 제거)
- [x] Cache 파일 자동 저장
- [x] 오늘 날짜만 gap-fill (과거 데이터는 제외)
- [x] 거래시간 체크 (9:00~15:30 + 장 종료 후)

### ✅ Real-time Polling 기능
- [x] Frontend 60초마다 `/minute/current` 호출
- [x] Backend 최신 캔들 조회 및 반환
- [x] Cache 자동 업데이트 (update_minute_candle)
- [x] 거래시간 체크 (9:00~15:30)
- [x] 오늘 날짜만 polling (과거 데이터 제외)

### ✅ 전체 통합 시나리오
- [x] 사용자 재접속 시 gap 자동 채우기
- [x] 초기 로드 후 실시간 polling 시작
- [x] 매분 cache 자동 업데이트
- [x] Frontend 차트 실시간 갱신

---

## 📝 주요 기술 결정

### 1. Gap 감지 임계값: 2분
- **이유**: 1분 polling 주기 고려, 네트워크 지연 허용
- **로직**: `(now - latest_time).total_seconds() / 60 >= 2`

### 2. Gap-Fill 방식: 부분 병합
- **전체 교체 방식 (X)**: Cache 전체를 API 데이터로 덮어쓰기
- **부분 병합 방식 (O)**: Gap 구간만 추출하여 기존 cache에 추가
- **장점**: API 호출 최소화, 기존 데이터 보존

### 3. Frontend 변경: InfiniteScrollCandlestickChart 사용
- **이전**: 직접 API 호출 (초기 로드만)
- **변경**: InfiniteScrollCandlestickChart 컴포넌트 사용
- **효과**: useInfiniteChartData 훅 자동 실행 → 실시간 polling

### 4. Import 경로 수정
- **오류**: `from app.utils.trading_calendar import TradingHoursManager`
- **수정**: `from app.utils.trading_hours import TradingHoursManager`
- **원인**: 잘못된 모듈 경로

---

## 🚀 배포 체크리스트

### Backend
- [x] chart_cache_service.py - Gap-fill 로직 추가
- [x] Import 경로 수정 (trading_hours)
- [x] 로깅 추가 (gap 감지, 채우기 완료)
- [x] Backend 재시작 및 테스트

### Frontend
- [x] echart/page.tsx - InfiniteScrollCandlestickChart 사용
- [x] 실시간 polling 활성화 확인
- [x] Next.js HMR 적용 확인
- [x] Playwright 테스트 통과

### 문서화
- [x] 구현 내역 문서 작성
- [x] 코드 주석 추가
- [x] 테스트 결과 기록

---

## 📌 참고 사항

### 관련 파일
- **Backend**: `backend/app/services/chart_cache_service.py`
- **Frontend**: `stock-trading-ui/src/app/echart/page.tsx`
- **Hook**: `stock-trading-ui/src/hooks/useInfiniteChartData.ts`
- **Component**: `stock-trading-ui/src/components/trading/InfiniteScrollCandlestickChart.tsx`

### 핵심 API 엔드포인트
- **Full Day**: `GET /api/chart/{stock_code}/minute`
- **Real-time**: `GET /api/chart/{stock_code}/minute/current`

### 접속 URL
- **실시간 차트**: http://localhost:9000/echart
- **테스트 페이지**: http://localhost:9000/test-infinite-scroll

---

## 🔧 향후 개선 사항

### 1. Gap-Fill 성능 최적화
- [ ] Gap 구간만 API 호출 (현재는 전체 조회)
- [ ] Batch API 활용 (여러 gap을 한 번에 처리)

### 2. Polling 전략 개선
- [ ] WebSocket 실시간 스트리밍 도입 고려
- [ ] Adaptive polling (거래량 기반 interval 조정)

### 3. 오류 처리 강화
- [ ] Gap-fill 실패 시 재시도 로직
- [ ] Polling 실패 시 exponential backoff

### 4. 모니터링
- [ ] Gap-fill 성공/실패 메트릭 추가
- [ ] Polling 성능 모니터링 (latency, error rate)

---

**작성일**: 2025-10-02
**최종 업데이트**: 2025-10-02 12:56
