# 포트폴리오 주말 스냅샷 이슈 해결

**문제 발견일**: 2025-10-11  
**심각도**: Medium (API 응답 없음)  
**해결 상태**: ✅ 완료

---

## 🐛 문제 설명

### 증상
- 통합 테스트 실행 시 `/api/portfolio/history` API가 `HTTP 204 No Content` 반환
- 실제로는 스냅샷이 정상 저장되어 있음
- 데이터 포인트: 0개로 표시

### 재현 조건
- 주말(토요일/일요일)이나 공휴일에 스냅샷이 저장됨
- 스냅샷 날짜가 조회 기간의 시작일보다 늦음
- 스냅샷 날짜가 비거래일

---

## 🔍 원인 분석

### 상세 분석
```
현재 날짜: 2025-10-11 (토요일) ← 비거래일
조회 기간 (1M): 2025-09-11 ~ 2025-10-11
실제 거래일: 2025-09-11 ~ 2025-10-10 (17일)

스냅샷: 2025-10-11 (토요일에 저장됨)

기존 로직:
1. snapshot_date (2025-10-11) > start_date (2025-09-11)
2. start_date를 snapshot_date로 조정: 2025-10-11
3. 거래일 계산: 2025-10-11 ~ 2025-10-11
4. 결과: 거래일 0일 ❌
```

### 핵심 문제
`portfolio_analytics_service.py`의 스냅샷 기반 start_date 조정 로직이 **비거래일을 고려하지 않음**

```python
# 기존 코드 (문제)
if snapshot_date > start_date:
    start_date = snapshot_date  # 토요일을 그대로 사용
    logger.info(f"   스냅샷 사용. 계산 시작일 조정: {start_date.date()}")
```

---

## ✅ 해결 방법

### 수정 내역

**파일**: `backend/app/services/portfolio_analytics_service.py`  
**라인**: 63-67

```python
# 수정된 코드
snapshot_date = datetime.strptime(baseline_snapshot['date'], "%Y-%m-%d")

# 스냅샷 날짜가 비거래일이면 이전 거래일로 조정
calendar = TradingCalendar()
if not calendar.is_trading_day(snapshot_date):
    snapshot_date = calendar.get_previous_trading_day(snapshot_date)
    logger.info(f"   스냅샷 날짜가 비거래일, 이전 거래일로 조정: {snapshot_date.date()}")

if snapshot_date > start_date:
    start_date = snapshot_date
    logger.info(f"   스냅샷 사용. 계산 시작일 조정: {start_date.date()}")
```

### 동작 예시

**수정 전**:
```
스냅샷: 2025-10-11 (토)
조정된 start_date: 2025-10-11 (토)
거래일: 0일
결과: 204 No Content ❌
```

**수정 후**:
```
스냅샷: 2025-10-11 (토)
→ 이전 거래일로 조정: 2025-10-10 (금)
조정된 start_date: 2025-10-10 (금)
거래일: 1일
결과: 200 OK, 1개 데이터 포인트 ✅
```

---

## 🧪 검증 방법

### 1. 디버깅 스크립트 실행
```bash
cd backend
source vkis/bin/activate
python scripts/debug_portfolio_api.py
```

**예상 출력**:
```
📸 스냅샷 발견
   날짜: 2025-10-11
   스냅샷 날짜: 2025-10-11 Saturday
   스냅샷 날짜가 비거래일, 이전 거래일로 조정: 2025-10-10

📊 조정된 거래일: 1일
   첫날: 2025-10-10 Friday
   마지막: 2025-10-10 Friday

✅ 결과: 1개 데이터 포인트
```

### 2. API 직접 테스트
```bash
curl -s http://localhost:8000/api/portfolio/history?period=1M | python3 -m json.tool
```

**예상 응답**:
```json
[
  {
    "date": "2025-10-10T15:30:00+09:00",
    "portfolio": 101456.0,
    "benchmark": 101456.0
  }
]
```

### 3. 통합 테스트 실행
```bash
bash scripts/test-portfolio-integration.sh
```

**예상 결과**: ✅ 모든 테스트 통과

---

## 📚 관련 코드

### TradingCalendar.is_trading_day()
```python
def is_trading_day(self, date: datetime) -> bool:
    """
    특정 날짜가 거래일인지 확인합니다.
    주말, 공휴일, 연말 휴장일을 제외합니다.
    """
    # 주말 체크 (토요일=5, 일요일=6)
    if date.weekday() >= 5:
        return False
    
    # 공휴일 체크 (holidays 라이브러리 사용)
    if date.date() in self.holidays:
        return False
    
    return True
```

### TradingCalendar.get_previous_trading_day()
```python
def get_previous_trading_day(self, date: datetime, max_attempts: int = 30) -> datetime:
    """
    주어진 날짜 이전의 가장 가까운 거래일을 반환합니다.
    """
    prev_day = date - timedelta(days=1)
    for _ in range(max_attempts):
        if self.is_trading_day(prev_day):
            return prev_day
        prev_day -= timedelta(days=1)
    raise ValueError(f"{max_attempts}일 내에 이전 거래일을 찾을 수 없습니다: {date}")
```

---

## 🎯 예방 조치

### 1. 스케줄러 개선 (선택 사항)
현재는 5분마다 무조건 스냅샷을 저장하지만, 거래일에만 저장하도록 변경 가능:

```python
# backend/app/main.py
from app.utils.trading_calendar import TradingCalendar

def is_trading_time():
    """현재가 거래 시간인지 확인"""
    now = datetime.now()
    calendar = TradingCalendar()
    
    # 거래일이 아니면 False
    if not calendar.is_trading_day(now):
        return False
    
    # 장 시간 체크 (09:00 ~ 15:30)
    current_time = now.time()
    market_open = time(9, 0)
    market_close = time(15, 30)
    
    return market_open <= current_time <= market_close

# 조건부 스케줄링
if is_trading_time():
    scheduler.add_job(save_portfolio_snapshot, 'interval', minutes=5)
```

### 2. 로깅 강화
비거래일 조정이 발생하면 항상 로그를 남기도록 함:

```python
if not calendar.is_trading_day(snapshot_date):
    original_date = snapshot_date.strftime("%Y-%m-%d %A")
    snapshot_date = calendar.get_previous_trading_day(snapshot_date)
    adjusted_date = snapshot_date.strftime("%Y-%m-%d %A")
    logger.warning(
        f"스냅샷 날짜가 비거래일입니다. "
        f"원본: {original_date}, 조정: {adjusted_date}"
    )
```

---

## 📝 교훈

1. **비즈니스 로직은 도메인 규칙을 엄격히 따라야 함**
   - 주식 시장은 주말/공휴일에 거래되지 않음
   - 모든 날짜 계산은 거래일 기준이어야 함

2. **엣지 케이스 테스트의 중요성**
   - 평일에는 발견되지 않는 문제
   - 주말/공휴일 시나리오 반드시 테스트

3. **디버깅 도구의 가치**
   - 상세한 로그와 디버깅 스크립트가 문제 해결 시간을 크게 단축

---

**해결 완료**: 2025-10-11 16:03  
**검증 완료**: 2025-10-11 16:04  
**문서 작성**: 2025-10-11 16:05
