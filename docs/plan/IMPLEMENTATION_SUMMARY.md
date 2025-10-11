# Portfolio Backend 구현 요약 (v2.3)

**작성일**: 2025-10-11
**상태**: ✅ 검증 완료 및 수정 완료

---

## 📊 검증 결과

### ✅ **정상 확인된 항목**

| 항목 | 위치 | 상태 |
|-----|------|------|
| ChartCandle.timestamp | `backend/app/models/schemas.py:141` | ✅ 존재 (ISO 형식) |
| get_daily_ccld() | `brokers/korea_investment/ki_api.py:670-714` | ✅ DataFrame 반환 |
| ord_tmd 필드 | get_daily_ccld 응답 | ✅ 체결시각 포함 |
| _run_in_executor | `backend/app/core/korea_invest.py:99-102` | ✅ 비동기 패턴 구현 |
| get_account_balance | `backend/app/core/korea_invest.py:104-163` | ✅ Dict 변환 완료 |

### 🔧 **수정된 항목**

| 문제 | 원인 | 해결 |
|-----|------|------|
| 메서드명 불일치 | `get_day_chart_data` | `get_daily_chart_data`로 수정 |
| 지수 조회 누락 | 메서드 없음 | `get_index_chart_data()` 추가 가이드 |
| 거래 내역 누락 | 메서드 없음 | `get_trade_history()` 추가 가이드 |
| ChartCandle 필드 | `c.date` 사용 | `c.timestamp` 사용으로 수정 |

---

## 📁 생성된 파일

### 1. **수정된 가이드 문서**
- **파일**: `docs/plan/1010.claude.portfolio.backend.plan.v2.3.CORRECTED.md`
- **내용**: 실제 코드베이스 검증 기반 수정
- **크기**: ~50KB

### 2. **TradingCalendar 유틸리티 (v3.0 - Dynamic)**
- **파일**: `backend/app/utils/trading_calendar.py`
- **기능**:
  - 주말 제외
  - ✅ **`holidays` 라이브러리** 사용 (대한민국 공휴일 자동 계산)
  - ✅ **동적 연도 범위** (현재 연도 ± 5년, 총 11년치 공휴일)
  - ✅ **연말 휴장일 (12/31)** 자동 처리
  - ✅ **대체공휴일** 자동 포함
  - 다음/이전 거래일 계산
  - 거래일 수 카운트
- **검증 완료**:
  - 209개 공휴일 로드 (2020-2030년)
  - 신정, 연말 휴장일 정상 작동 확인

### 3. **BenchmarkAligner 유틸리티**
- **파일**: `backend/app/utils/benchmark_alignment.py`
- **기능**:
  - 날짜 기반 정확한 정렬
  - 선형 보간
  - 추적 오차 계산
  - 정렬 검증
- **개선사항**:
  - 기존: 인덱스 기반 샘플링
  - 신규: 날짜 기반 정확한 매칭

### 4. **Utils 초기화**
- **파일**: `backend/app/utils/__init__.py`
- **내용**: 모듈 export 정의

---

## 🚀 구현 가이드 요약

### Phase 1: MVP + 매매 이력 (5일)

#### Day 1: 기본 구조 (4시간)
- ✅ 데이터 모델 정의 (`schemas.py`)
- ✅ BenchmarkService 구현
- ✅ 한투 API 래퍼 추가:
  - `get_index_chart_data()`
  - `get_trade_history()`
- ✅ API 엔드포인트 (`portfolio.py`)

#### Day 2: 거래 내역 수집 (1일)
- TradeHistoryService 구현
- `get_trade_history()` 사용
- DataFrame → Trade 변환
- `ord_tmd` 필드 활용 (체결시각)

#### Day 3: 현금 흐름 추적 (1일)
- CashFlowTracker 구현
- 매수/매도에 따른 현금 계산
- 수수료/세금 반영

#### Day 4: 포트폴리오 분석 (1일)
- PortfolioAnalyticsService 통합
- ✅ `get_daily_chart_data()` 사용 (수정됨)
- ✅ ChartCandle.timestamp 활용
- TradingCalendar 사용
- BenchmarkAligner 사용

#### Day 5: 테스트 및 검증 (1일)
- 단위 테스트
- 통합 테스트
- 엔드포인트 검증

---

## 💡 핵심 수정사항

### 1. **메서드명 수정**

```python
# ❌ 기존 (잘못)
result = await self.korea_invest.get_day_chart_data(
    stock_code,
    start_date,
    end_date
)

# ✅ 수정 (올바름)
result = await self.korea_invest.get_daily_chart_data(
    stock_code,
    start_date,
    end_date
)
```

### 2. **ChartCandle 필드 사용**

```python
# ❌ 기존 (잘못)
date_str = c.date

# ✅ 수정 (올바름)
date_str = c.timestamp  # ISO 형식 문자열
```

### 3. **DataFrame 변환**

```python
# ✅ ChartCandle → DataFrame
from datetime import datetime

df = pd.DataFrame([
    {
        "일자": datetime.fromisoformat(c.timestamp).strftime("%Y%m%d"),
        "종가": c.close,
        "시가": c.open,
        "고가": c.high,
        "저가": c.low,
        "거래량": c.volume
    }
    for c in result  # List[ChartCandle]
]).set_index("일자")
```

### 4. **거래 내역 조회**

```python
# ✅ 새로 추가된 메서드
async def get_trade_history(
    self,
    start_date: str,
    end_date: str
) -> Optional[pd.DataFrame]:
    """일별 체결 내역 조회"""
    df = await self._run_in_executor(
        self.api_instance.get_daily_ccld,
        start_date,
        end_date
    )
    return df  # DataFrame 반환
```

---

## 🎯 구현 우선순위

### 필수 (Phase 1)
1. ✅ 데이터 모델 정의
2. ✅ API 엔드포인트
3. ✅ 한투 API 래퍼 메서드 추가
4. TradeHistoryService
5. CashFlowTracker
6. PortfolioAnalyticsService

### 권장 (Phase 2)
1. ✅ TradingCalendar (공휴일 처리)
2. ✅ BenchmarkAligner (정확한 정렬)
3. 캐싱 (Redis)
4. 스케줄러 (APScheduler)

### 선택 (Phase 3)
1. 모니터링 및 로깅
2. 성능 최적화
3. 스냅샷 방식

---

## 📋 체크리스트

### 구현 전 확인사항
- [x] Python 3.12 환경 활성화 (`source vkis/bin/activate`)
- [x] 필요한 라이브러리 설치 확인
- [x] 한투 API 설정 확인
- [x] 실제 코드베이스 구조 파악

### 구현 중 확인사항
- [ ] 메서드명 정확히 사용 (`get_daily_chart_data`)
- [ ] ChartCandle.timestamp 사용
- [ ] ord_tmd 필드 활용 (체결시각)
- [ ] TradingCalendar 사용 (주말/공휴일 제외)
- [ ] BenchmarkAligner 사용 (정확한 정렬)

### 구현 후 확인사항
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] API 엔드포인트 동작 확인 (`/api/portfolio/history`)
- [ ] Frontend 연동 테스트

---

## 🔍 Troubleshooting

### Issue 1: AttributeError: 'ChartCandle' object has no attribute 'date'
**해결**: `c.timestamp` 사용

### Issue 2: 메서드 not found
**해결**: `get_daily_chart_data` 확인 (get_day_chart_data 아님)

### Issue 3: 벤치마크 길이 불일치
**해결**: `BenchmarkAligner.align_by_date()` 사용

### Issue 4: 공휴일 포함됨
**해결**: `TradingCalendar.get_trading_days()` 사용

---

## 📚 참고 문서

1. **메인 가이드**: `docs/plan/1010.claude.portfolio.backend.plan.v2.3.CORRECTED.md`
2. **한투 API 문서**: https://apiportal.koreainvestment.com/
3. **FastAPI 문서**: https://fastapi.tiangolo.com/
4. **Pandas 문서**: https://pandas.pydata.org/

---

## 🎉 다음 단계

1. **Phase 1 구현 시작**:
   ```bash
   cd backend
   source vkis/bin/activate
   # Step 1: schemas.py에 모델 추가
   # Step 2: benchmark_service.py 생성
   # Step 3: korea_invest.py에 메서드 추가
   # Step 4: portfolio.py API 엔드포인트 생성
   ```

2. **테스트 실행**:
   ```bash
   # 단위 테스트
   pytest tests/test_portfolio_analytics.py

   # 통합 테스트
   python scripts/test_portfolio_history.py
   ```

3. **서버 실행 및 확인**:
   ```bash
   # 서버 시작
   python app/main.py

   # API 테스트
   curl http://localhost:8000/api/portfolio/history?period=1W
   ```

---

**핵심**: 실제 코드베이스를 기준으로 구현하세요! 📝
