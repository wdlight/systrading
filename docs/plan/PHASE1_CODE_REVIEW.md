# Phase 1 코드 검토 보고서

**검토일**: 2025-10-11
**상태**: ✅ Critical 이슈 수정 완료

---

## 📋 검토 파일 목록

### 새로 생성된 파일
- `app/api/portfolio.py` - Portfolio API 엔드포인트
- `app/services/benchmark_service.py` - 벤치마크(KOSPI) 서비스
- `app/services/trade_history_service.py` - 거래 내역 수집 서비스
- `app/services/cash_flow_tracker.py` - 현금 흐름 추적
- `app/services/portfolio_analytics_service.py` - 포트폴리오 분석 서비스
- `tests/test_portfolio_analytics.py` - 단위 테스트
- `scripts/test_portfolio_history.py` - 통합 테스트

### 수정된 파일
- `app/core/korea_invest.py` - 한투 API 래퍼 (메서드 추가)
- `app/main.py` - Portfolio 라우터 등록
- `app/models/schemas.py` - 데이터 모델 추가
- `requirements.txt` - 의존성 추가

---

## ❌ 발견된 문제 (Critical)

### 1. **portfolio.py Line 17: Syntax Error**

**문제**: 함수 정의에 `def` 키워드 중복
```python
# ❌ Before
def def get_analytics_service(
    korea_invest: KoreaInvestAPIService = Depends(get_korea_invest_service)
) -> PortfolioAnalyticsService:
```

**수정**:
```python
# ✅ After
def get_analytics_service(
    korea_invest: KoreaInvestAPIService = Depends(get_korea_invest_service)
) -> PortfolioAnalyticsService:
```

**영향**: 서버 시작 불가 (ImportError)

**상태**: ✅ 수정 완료

---

### 2. **portfolio_analytics_service.py Line 213: 잘못된 메서드명**

**문제**: 존재하지 않는 메서드 호출
```python
# ❌ Before
result = await self.korea_invest.get_day_chart_data(
    stock_code,
    start_date.strftime("%Y%m%d"),
    end_date.strftime("%Y%m%d")
)
```

**수정**:
```python
# ✅ After
result = await self.korea_invest.get_daily_chart_data(
    stock_code,
    start_date.strftime("%Y%m%d"),
    end_date.strftime("%Y%m%d")
)
```

**영향**: 종목별 가격 조회 실패 (AttributeError)

**상태**: ✅ 수정 완료

**근거**: `korea_invest.py` line 470에 정의된 메서드명은 `get_daily_chart_data`

---

## ✅ 검증 완료 항목

### 1. **한투 API 래퍼 메서드 추가**

#### ✅ get_index_chart_data() (Line 936)
```python
async def get_index_chart_data(
    self,
    market_code: str,
    index_code: str,
    start_date: str,
    end_date: str,
    period_code: str = "D"
) -> Optional[pd.DataFrame]:
```

**용도**: KOSPI/KOSDAQ 지수 차트 조회
**구현**: ✅ `_run_in_executor` 패턴 사용
**TR_ID**: FHKUP03500100

---

#### ✅ get_trade_history() (Line 981)
```python
async def get_trade_history(
    self,
    start_date: str,
    end_date: str
) -> Optional[List[Dict[str, Any]]]:
```

**용도**: 일별 체결 내역 조회
**구현**: ✅ `_run_in_executor` 패턴 사용
**TR_ID**: TTTC8001R
**반환**: DataFrame (pandas)

---

### 2. **데이터 모델 정의**

#### ✅ PortfolioHistoryPoint (schemas.py Line 227)
```python
class PortfolioHistoryPoint(BaseModel):
    date: str = Field(..., description="ISO 8601 형식 (KST)")
    portfolio: float = Field(..., description="포트폴리오 총자산 (KRW)")
    benchmark: float = Field(..., description="KOSPI 벤치마크 (KRW, 정규화)")
```

**Frontend 호환성**: ✅ 타입 일치 확인
- ❌ `timestamp` (X)
- ✅ `date` (O)
- ✅ `portfolio` (O)
- ✅ `benchmark` (O)

---

#### ✅ Trade 모델 (schemas.py Line 241)
```python
class Trade(BaseModel):
    trade_date: str
    trade_time: str = Field("000000", description="체결시각 (HHMMSS)")  # ✅ 추가됨
    stock_code: str
    stock_name: str
    trade_type: Literal["buy", "sell"]
    quantity: int
    price: int
    amount: int
    fee: int
    tax: int
```

**중요**: `trade_time` 필드가 추가되어 동일 날짜 내 거래 순서 정렬 가능

---

### 3. **ChartCandle.timestamp 사용 검증**

#### ✅ schemas.py Line 141
```python
class ChartCandle(BaseModel):
    timestamp: str = Field(..., description="ISO 형식의 타임스탬프 (YYYY-MM-DDTHH:MM:SS)")
    # ❌ date 필드 없음!
```

#### ✅ portfolio_analytics_service.py Line 228
```python
# ✅ 올바른 사용
datetime.fromisoformat(c.timestamp).strftime("%Y%m%d")

# ❌ 잘못된 예 (가이드 문서의 실수)
# datetime.fromisoformat(c.date)  # date 필드 존재하지 않음!
```

**결론**: ChartCandle은 `timestamp` 필드만 존재하며, 코드에서 정확히 사용됨

---

### 4. **ord_tmd 필드 활용**

#### ✅ trade_history_service.py Line 62
```python
trade = Trade(
    trade_date=item["ord_dt"],
    trade_time=item.get("ord_tmd", "000000"),  # ✅ 체결시각 추가
    stock_code=item["pdno"],
    # ...
)
```

#### ✅ 동일 날짜 거래 정렬 (Line 117)
```python
trades_by_date[date_str] = sorted(
    trades_by_date[date_str],
    key=lambda t: t.trade_time,  # ✅ 체결시각 기준
    reverse=True  # 역순 정렬 (최신 → 과거)
)
```

**중요**: 포지션 재구성 시 동일 날짜 내 거래 순서가 정확해야 올바른 복원 가능

---

### 5. **TradingCalendar 사용**

#### ✅ portfolio_analytics_service.py Line 192
```python
def _generate_trading_days(
    self,
    start_date: datetime,
    end_date: datetime
) -> List[datetime]:
    """거래일 리스트 생성"""
    calendar = TradingCalendar()  # ✅ v3.0 사용
    return calendar.get_trading_days(start_date, end_date)
```

**효과**:
- 주말 자동 제외
- 공휴일 자동 제외 (209개, 11년치)
- 연말 휴장일 (12/31) 자동 제외

---

### 6. **비동기 패턴 준수**

#### ✅ _run_in_executor 사용 검증
```python
# benchmark_service.py Line 74
df = await self.korea_invest.get_index_chart_data(...)

# trade_history_service.py Line 35
result = await self.korea_invest.get_trade_history(...)

# portfolio_analytics_service.py Line 52
balance = await self.korea_invest.get_account_balance()
```

**결론**: 모든 한투 API 호출이 비동기 래퍼를 통해 실행됨

---

### 7. **API 라우터 등록**

#### ✅ main.py Line 39, 142
```python
from app.api.portfolio import router as portfolio_router

app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])
```

**엔드포인트**:
- `GET /api/portfolio/history?period=1W`
- `GET /api/portfolio/health`

---

## ⚠️ 잠재적 개선사항 (Phase 2 권장)

### 1. **벤치마크 정렬 로직**

**현재**: 단순 샘플링/패딩 (portfolio_analytics_service.py Line 281)
```python
def _align_benchmark(
    self,
    benchmark_data: List[float],
    trading_days: List[datetime]
) -> List[float]:
    # 간단한 보간: 비율 맞춰서 샘플링
    if len(benchmark_data) > len(trading_days):
        step = len(benchmark_data) / len(trading_days)
        return [
            benchmark_data[int(i * step)]
            for i in range(len(trading_days))
        ]
```

**문제점**: 날짜 기반 정확한 매칭 없음 (인덱스 기반)

**권장**: `BenchmarkAligner.align_by_date()` 사용
```python
# ✅ 개선안
from app.utils.benchmark_alignment import BenchmarkAligner

# 날짜 기반 정확한 정렬 + 선형 보간
aligned = BenchmarkAligner.align_by_date(
    benchmark_data=[{"date": "20251010", "value": 2500}, ...],
    target_dates=trading_days,
    interpolate=True
)
```

**효과**:
- 날짜 기반 정확한 매칭
- 선형 보간으로 누락 데이터 처리
- 추적 오차 계산 가능

---

### 2. **캐싱 최적화**

**현재**: 파일 캐시만 사용 (benchmark_service.py)

**권장**:
```python
# Redis 캐시 추가 (Phase 2)
import redis

class BenchmarkService:
    def __init__(self, korea_invest_service, redis_client):
        self.redis = redis_client
        # ...

    async def get_kospi_history(self, start_date, end_date):
        # 1. Redis 캐시 확인 (빠름)
        cache_key = f"kospi:{start_date}:{end_date}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # 2. 파일 캐시 확인
        # 3. API 조회
        # 4. Redis + 파일 캐시 저장
```

---

### 3. **에러 핸들링 강화**

**현재**: 기본 try-except

**권장**:
```python
from fastapi import HTTPException

@router.get("/history")
async def get_portfolio_history(...):
    try:
        data = await analytics.get_portfolio_history(period)

        if not data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NO_DATA",
                    "message": f"{period} 기간의 데이터가 없습니다.",
                    "suggestion": "기간을 조정하거나 거래 내역을 확인하세요."
                }
            )

        return data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Portfolio history 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="서버 내부 오류")
```

---

### 4. **성능 최적화**

**병렬 처리**: ✅ 이미 구현됨 (portfolio_analytics_service.py Line 245)
```python
tasks = [fetch_one(code) for code in stock_codes]
results = await asyncio.gather(*tasks)
```

**권장 추가**:
```python
# Semaphore로 동시 요청 수 제한
async def _fetch_stock_histories(self, stock_codes, start_date, end_date):
    semaphore = asyncio.Semaphore(5)  # 최대 5개 동시 요청

    async def fetch_one_limited(stock_code):
        async with semaphore:
            return await self._fetch_one(stock_code)

    tasks = [fetch_one_limited(code) for code in stock_codes]
    results = await asyncio.gather(*tasks)
```

---

## 📊 Python Syntax 검증

### ✅ 모든 파일 Syntax Check 통과
```bash
cd backend
source vkis/bin/activate
python -m py_compile \
    app/api/portfolio.py \
    app/services/portfolio_analytics_service.py \
    app/services/benchmark_service.py \
    app/services/trade_history_service.py \
    app/services/cash_flow_tracker.py

# 결과: ✅ All syntax checks passed
```

---

## 🎯 Phase 1 체크리스트

### Day 1: 기본 구조 ✅
- [x] 데이터 모델 정의 (`schemas.py`)
  - [x] PortfolioHistoryPoint
  - [x] Trade (trade_time 필드 포함)
- [x] BenchmarkService 구현
  - [x] KOSPI 조회 (한투 API + pykrx fallback)
  - [x] 파일 캐시
  - [x] 정규화 로직
- [x] 한투 API 래퍼 메서드 추가
  - [x] `get_index_chart_data()`
  - [x] `get_trade_history()`
- [x] API 엔드포인트 (`portfolio.py`)
  - [x] GET `/api/portfolio/history`
  - [x] GET `/api/portfolio/health`

### Day 2: 거래 내역 수집 ✅
- [x] TradeHistoryService 구현
  - [x] `get_trade_history()` 사용
  - [x] DataFrame → Trade 변환
  - [x] ord_tmd 필드 활용
  - [x] 동일 날짜 거래 시간순 정렬

### Day 3: 현금 흐름 추적 ✅
- [x] CashFlowTracker 구현
  - [x] 매수/매도 현금 계산
  - [x] 수수료/세금 반영
  - [x] 일별 현금 역산

### Day 4: 포트폴리오 분석 ✅
- [x] PortfolioAnalyticsService 통합
  - [x] `get_daily_chart_data()` 사용 (✅ 메서드명 수정됨)
  - [x] ChartCandle.timestamp 활용
  - [x] TradingCalendar 사용
  - [x] 벤치마크 정규화

### Day 5: 테스트 및 검증 ⏳
- [ ] 단위 테스트 실행
- [ ] 통합 테스트 실행
- [ ] 엔드포인트 검증 (`/api/portfolio/history`)
- [ ] Frontend 연동 테스트

---

## 🚀 다음 단계

### 1. **즉시 실행 가능**
```bash
cd backend
source vkis/bin/activate

# 서버 시작
python app/main.py

# 엔드포인트 테스트
curl http://localhost:8000/api/portfolio/health
curl "http://localhost:8000/api/portfolio/history?period=1W"
```

### 2. **통합 테스트**
```bash
# 통합 테스트 스크립트 실행
python scripts/test_portfolio_history.py
```

### 3. **단위 테스트**
```bash
pytest tests/test_portfolio_analytics.py -v
```

---

## 📝 핵심 수정사항 요약

| 파일 | Line | 문제 | 수정 | 상태 |
|------|------|------|------|------|
| portfolio.py | 17 | `def def` Syntax Error | `def` 중복 제거 | ✅ |
| portfolio_analytics_service.py | 213 | `get_day_chart_data` | `get_daily_chart_data`로 수정 | ✅ |

---

## ✅ 검증 완료 항목 요약

| 항목 | 위치 | 상태 |
|------|------|------|
| ChartCandle.timestamp | schemas.py:141 | ✅ 존재 |
| get_daily_chart_data() | korea_invest.py:470 | ✅ 구현됨 |
| get_index_chart_data() | korea_invest.py:936 | ✅ 추가됨 |
| get_trade_history() | korea_invest.py:981 | ✅ 추가됨 |
| ord_tmd 필드 활용 | trade_history_service.py:62 | ✅ 사용 중 |
| TradingCalendar 사용 | portfolio_analytics_service.py:192 | ✅ v3.0 사용 |
| Portfolio 라우터 등록 | main.py:142 | ✅ 등록됨 |
| 비동기 패턴 | 전체 | ✅ _run_in_executor 사용 |

---

## 🎉 결론

**Phase 1 구현 상태**: ✅ **양호 (2개 Critical 이슈 수정 완료)**

**핵심 성과**:
1. ✅ 모든 필수 서비스 구현 완료
2. ✅ 한투 API 래퍼 메서드 추가
3. ✅ Frontend 호환 데이터 모델
4. ✅ 거래 내역 기반 정확한 포트폴리오 계산
5. ✅ Python syntax 검증 통과

**다음 작업**:
- Day 5: 테스트 및 검증 (진행 필요)
- Phase 2: 캐싱, 벤치마크 정렬 개선, 성능 최적화

---

**검토자**: Claude Code
**검토 일시**: 2025-10-11
**승인 상태**: ✅ Phase 1 구현 완료, 테스트 진행 가능
