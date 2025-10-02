# Gap 구간만 조회하는 API 최적화 Plan

**날짜**: 2025-10-02
**목표**: Gap-fill 시 불필요한 전체 데이터 조회 제거, Gap 구간만 API 호출

---

## 📊 현재 상황 분석

### 한국투자증권 API 기능
```python
def get_minute_chart_data(self, stock_code, start_time=None, max_count=None):
    """
    1분봉 차트 데이터 조회

    Args:
        stock_code: 종목 코드
        start_time: 시작 시간 (HHMMSS 형식, 기본값: 090000)
        max_count: 최대 조회 개수

    Returns:
        DataFrame: start_time부터 현재까지 분봉 데이터
    """
```

**핵심 기능**: ✅ 시작 시간 지정 가능 (`start_time` 파라미터)

### 현재 Gap-Fill 방식의 비효율

**문제 시나리오**:
```
Cache: 9:00~11:18 (129 candles)
Gap: 11:19~12:32 (74 candles 필요)

현재 방식:
1. API 호출: 9:00~12:32 전체 조회 (203 candles)
2. 필터링: gap_time > 11:18인 데이터만 추출 (74 candles)
3. 병합: Cache (129) + Gap (74) = 203 candles

❌ 문제: 9:00~11:18 데이터를 불필요하게 다시 조회 (129 candles 낭비)
```

**코드 위치**: `backend/app/services/chart_cache_service.py:_fill_gap()`
```python
# 현재 코드 (비효율)
api_data = await api_fallback(stock_code)  # 전체 조회
gap_candles = [
    c for c in api_candles
    if datetime.fromisoformat(c.timestamp) > gap_start_time
]  # gap만 필터링
```

---

## ✅ 최적화 전략

### 핵심 아이디어
**Gap 시작 시간을 API `start_time`으로 직접 전달** → Gap 구간만 조회

### 성능 개선 효과
```
Before:
- API 데이터량: 203 candles (전체)
- 네트워크: 전체 데이터 전송
- 처리 시간: 전체 데이터 파싱 + 필터링

After:
- API 데이터량: 74 candles (gap만)
- 네트워크: 63% 감소 ✅
- 처리 시간: 필터링 불필요 ✅
```

---

## 🔧 구현 계획

### Step 1: KoreaInvestAPIService에 Gap 전용 메서드 추가

**파일**: `backend/app/core/korea_invest.py`

```python
async def get_minute_chart_data_from(
    self,
    stock_code: str,
    start_time: str  # HHMMSS 형식
) -> Optional[List[ChartCandle]]:
    """
    특정 시간부터 현재까지 분봉 데이터 조회 (Gap-fill 최적화)

    Args:
        stock_code: 종목 코드 (예: "005930")
        start_time: 시작 시간 HHMMSS 형식 (예: "113000" = 11:30:00)

    Returns:
        start_time 이후 분봉 데이터만 반환

    Example:
        # 11:30부터 현재까지만 조회
        candles = await service.get_minute_chart_data_from("005930", "113000")
    """
    if not self.is_connected or not self.api_instance:
        logger.error("API가 연결되지 않았습니다.")
        return None

    try:
        logger.info(f"Gap 구간 조회: {stock_code}, {start_time}~현재")

        # API 호출 (start_time 지정)
        df = await self._run_in_executor(
            self.api_instance.get_minute_chart_data,
            stock_code,
            start_time=start_time,  # 🔑 Gap 시작 시간
            max_count=None
        )

        if df is None or df.empty:
            return []

        # 중복 제거
        df = df.drop_duplicates(subset=['일자', '시간'], keep='first')
        logger.info(f"Gap 데이터 수집: {len(df)}개 ({start_time}~)")

        # DataFrame → ChartCandle 변환
        chart_candles: List[ChartCandle] = []
        for _, row in df.iterrows():
            try:
                date_str = str(row['일자'])
                time_str = str(row['시간']).zfill(6)

                if time_str == "240000":
                    dt_object = datetime.strptime(date_str, "%Y%m%d") + timedelta(days=1)
                    timestamp_iso = dt_object.strftime("%Y-%m-%dT00:00:00")
                else:
                    dt_object = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
                    timestamp_iso = dt_object.isoformat()

                candle = ChartCandle(
                    timestamp=timestamp_iso,
                    open=float(row['시가']),
                    high=float(row['고가']),
                    low=float(row['저가']),
                    close=float(row['종가']),
                    volume=int(row['거래량'])
                )
                chart_candles.append(candle)
            except Exception as e:
                logger.warning(f"데이터 변환 오류: {e}")
                continue

        return chart_candles

    except Exception as e:
        logger.error(f"Gap 구간 조회 실패: {e}")
        return None
```

### Step 2: ChartCacheService._fill_gap() 최적화

**파일**: `backend/app/services/chart_cache_service.py`

**Before (현재 - 비효율)**:
```python
async def _fill_gap(
    self,
    cached_candles: List[ChartCandle],
    api_candles: List[ChartCandle]
) -> List[ChartCandle]:
    """Cache gap을 API 데이터로 채움"""

    # Gap 시작 시간 계산
    latest_cached = max(cached_candles, key=lambda c: datetime.fromisoformat(c.timestamp))
    gap_start_time = datetime.fromisoformat(latest_cached.timestamp)

    # API에서 gap 이후 데이터만 추출 (비효율 - 전체 조회 후 필터링)
    gap_candles = [
        c for c in api_candles
        if datetime.fromisoformat(c.timestamp) > gap_start_time
    ]

    # 병합
    all_candles = cached_candles + gap_candles
    unique_map = {candle.timestamp: candle for candle in all_candles}

    return sorted(unique_map.values(), key=lambda c: datetime.fromisoformat(c.timestamp))
```

**After (최적화 - Gap만 조회)**:
```python
async def _fill_gap(
    self,
    cached_candles: List[ChartCandle],
    stock_code: str,
    korea_invest_service  # KoreaInvestAPIService 인스턴스
) -> List[ChartCandle]:
    """
    Cache gap을 API로 채움 (최적화: Gap 구간만 조회)

    Args:
        cached_candles: 기존 cache 데이터
        stock_code: 종목 코드
        korea_invest_service: API 서비스 인스턴스

    Returns:
        Gap이 채워진 완전한 데이터
    """
    # 1. Cache의 마지막 시간
    latest_cached = max(
        cached_candles,
        key=lambda c: datetime.fromisoformat(c.timestamp)
    )
    gap_start_time = datetime.fromisoformat(latest_cached.timestamp)

    # 2. Gap 시작 시간 계산 (마지막 캔들 + 1분)
    gap_start = gap_start_time + timedelta(minutes=1)
    gap_start_hhmmss = gap_start.strftime("%H%M%S")

    logger.info(
        f"Gap 구간만 조회: {stock_code}, "
        f"{gap_start.strftime('%H:%M')}~현재"
    )

    # 3. ✨ Gap 구간만 API 호출 (최적화)
    gap_candles = await korea_invest_service.get_minute_chart_data_from(
        stock_code=stock_code,
        start_time=gap_start_hhmmss
    )

    if not gap_candles:
        logger.warning(f"Gap 데이터 없음: {stock_code}")
        return cached_candles

    logger.info(
        f"Gap 채우기: {len(gap_candles)}개 추가 "
        f"({gap_start_hhmmss}~현재)"
    )

    # 4. 병합 및 중복 제거
    all_candles = cached_candles + gap_candles
    unique_map = {candle.timestamp: candle for candle in all_candles}

    # 5. 시간순 정렬
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

### Step 3: get_minute_candles() 메서드 시그니처 변경

**파일**: `backend/app/services/chart_cache_service.py`

**Before**:
```python
async def get_minute_candles(
    self,
    stock_code: str,
    target_date: datetime,
    api_fallback: Callable,  # ❌ Generic callback
    skip_cache_save: bool = False
) -> Optional[List[ChartCandle]]:
```

**After**:
```python
async def get_minute_candles(
    self,
    stock_code: str,
    target_date: datetime,
    korea_invest_service,  # ✅ 직접 service 전달
    skip_cache_save: bool = False
) -> Optional[List[ChartCandle]]:
    """분봉 데이터 조회 (캐시 우선, gap-fill 최적화)"""

    # 1. 캐시 로드
    cached_data = self._load_from_cache(stock_code, target_date)

    # 2. Gap 감지 및 채우기 (최적화)
    if cached_data and self._needs_gap_fill(cached_data, target_date):
        logger.info(f"Gap 감지, 구간만 조회: {stock_code}")

        try:
            # ✅ Gap 구간만 조회 (전체 조회 X)
            filled_data = await self._fill_gap(
                cached_candles=cached_data,
                stock_code=stock_code,
                korea_invest_service=korea_invest_service
            )

            if not skip_cache_save:
                self._save_to_cache(stock_code, target_date, filled_data)

            return filled_data

        except Exception as e:
            logger.error(f"Gap fill 실패: {e}")
            return cached_data

    # 3. Cache hit (gap 없음)
    if cached_data:
        return cached_data

    # 4. Cache miss (전체 조회)
    logger.info(f"캐시 미스: {stock_code}, 전체 조회")
    candles = await korea_invest_service.get_minute_chart_data(stock_code)

    if candles and not skip_cache_save:
        self._save_to_cache(stock_code, target_date, candles)

    return candles
```

### Step 4: TradingService 호출부 수정

**파일**: `backend/app/services/trading_service.py`

**Before**:
```python
# api_fallback 함수 정의
async def api_fallback(code: str) -> Optional[List[ChartCandle]]:
    return await self.korea_invest_service.get_minute_chart_data(code)

# 캐시 서비스 호출
raw_data = await self.chart_cache_service.get_minute_candles(
    stock_code=stock_code,
    target_date=query_date,
    api_fallback=api_fallback  # ❌ Callback
)
```

**After**:
```python
# 직접 service 전달
raw_data = await self.chart_cache_service.get_minute_candles(
    stock_code=stock_code,
    target_date=query_date,
    korea_invest_service=self.korea_invest_service  # ✅ Direct service
)
```

---

## 🎯 테스트 시나리오

### Scenario 1: Gap-Fill 최적화 검증

**Setup**:
```
Cache: 11:18까지 (129 candles)
현재 시간: 12:32
Gap: 11:19~12:32 (74 candles 필요)
```

**Expected**:
```
1. Gap 감지: ✅ (latest=11:18 < now=12:32)
2. Gap 시작 계산: 11:19 (11:18 + 1분)
3. API 호출: start_time="111900"
4. API 데이터: 74 candles (11:19~12:32만)
5. 병합: 129 + 74 = 203 candles
6. Cache 저장: 203 candles
```

**Verification**:
```bash
# 로그 확인
tail -f backend.log | grep "Gap 구간"
# Expected: "Gap 구간만 조회: 005930, 11:19~현재"
# Expected: "Gap 채우기: 74개 추가 (111900~현재)"
```

### Scenario 2: 성능 측정

**Metrics**:
- API 데이터량 감소율
- 처리 시간 개선
- 메모리 사용량

**Before vs After**:
```
Before (전체 조회):
- API 데이터: 203 candles
- 처리 시간: ~500ms
- 메모리: 203 * sizeof(ChartCandle)

After (Gap만 조회):
- API 데이터: 74 candles (-63%)
- 처리 시간: ~200ms (-60%)
- 메모리: 74 * sizeof(ChartCandle) (-63%)
```

---

## 📋 구현 체크리스트

### Backend
- [ ] `KoreaInvestAPIService.get_minute_chart_data_from()` 추가
- [ ] `ChartCacheService._fill_gap()` 최적화
- [ ] `ChartCacheService.get_minute_candles()` 시그니처 변경
- [ ] `TradingService.get_minute_chart_data()` 호출부 수정
- [ ] 로깅 추가 (Gap 구간, API 데이터량)

### Testing
- [ ] Gap-fill 정확성 테스트 (11:18 → 12:32)
- [ ] API 데이터량 측정 (Before vs After)
- [ ] 처리 시간 측정
- [ ] 에러 케이스 테스트 (API 실패, 빈 데이터 등)

### Documentation
- [ ] 최적화 전략 문서화
- [ ] API 메서드 주석 추가
- [ ] 성능 개선 결과 기록

---

## 🚀 기대 효과

### 1. 네트워크 효율
- **API 데이터 전송량 63% 감소**
- 한투 API 호출 제한 여유 확보

### 2. 처리 속도
- **Gap-fill 처리 시간 60% 단축**
- 불필요한 필터링 제거

### 3. 메모리
- **메모리 사용량 63% 감소**
- GC 부담 감소

### 4. 확장성
- Gap이 클수록 효과 증가
- 예: 3시간 gap (11:00~14:00)
  - Before: 391 candles 조회
  - After: 180 candles 조회 (54% 감소)

---

## 📌 주의사항

### 1. API 시간 형식
- 한투 API: `HHMMSS` 형식 (예: "113000")
- 내부 timestamp: ISO 형식 (예: "2025-10-02T11:30:00")
- 변환 필요: `datetime.strftime("%H%M%S")`

### 2. 경계 처리
- Gap 시작: `latest_time + 1분` (중복 방지)
- 시간 형식: 6자리 zero-padding (예: "090000")

### 3. 에러 처리
- API 실패 시: 기존 cache 반환
- 빈 데이터: 빈 리스트 반환
- Gap 데이터 없음: cache 그대로 반환

---

## 🔄 향후 개선 방향

### 1. Batch Gap-Fill
여러 gap을 한 번에 처리
```python
gaps = [(start1, end1), (start2, end2), ...]
fill_multiple_gaps(gaps)
```

### 2. 예측적 Pre-Fetch
거래 종료 시 다음 날 일부 데이터 미리 로드

### 3. WebSocket 실시간 스트리밍
Gap 자체를 발생시키지 않도록 실시간 구독

---

**작성일**: 2025-10-02
**목표 구현일**: 2025-10-03
