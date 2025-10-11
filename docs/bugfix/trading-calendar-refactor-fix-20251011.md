# `TradingCalendar` 설계 변경으로 인한 API 호출 에러 수정 (2025-10-11)

## 🐛 버그 설명

**증상:**
`get_full_day_candles` 함수 등에서 다음과 같은 `TypeError`가 발생했습니다.

```
TypeError: TradingCalendar.is_trading_day() missing 1 required positional argument: 'date'
```

**원인:**
`app/utils/trading_calendar.py`의 `TradingCalendar` 클래스가 리팩토링되어, 기존의 클래스 메서드(`@classmethod`) 방식에서 **인스턴스 메서드** 방식으로 변경되었습니다. 하지만 `trading_service.py`와 `chart_cache_service.py` 등 여러 파일에서 여전히 `TradingCalendar.is_trading_day()`와 같이 클래스 이름으로 직접 메서드를 호출하고 있었습니다.

이로 인해 메서드의 첫 번째 인자인 `self` (인스턴스 자신)가 전달되지 않아, 그 다음 인자인 `date`가 누락되었다는 에러가 발생했습니다.


## ✅ 적용된 수정

**핵심 해결 방안:**
`TradingCalendar` 클래스를 직접 호출하는 모든 코드를 `get_default_calendar()` 함수를 통해 싱글톤(singleton) 인스턴스를 얻은 후, 그 인스턴스를 통해 메서드를 호출하도록 수정했습니다.

**수정 전 (잘못된 호출):**
```python
from app.utils.trading_calendar import TradingCalendar

# ...
if not TradingCalendar.is_trading_day(some_date):
    # ...
```

**수정 후 (올바른 호출):**
```python
from app.utils.trading_calendar import get_default_calendar

# ...
calendar = get_default_calendar()
if not calendar.is_trading_day(some_date):
    # ...
```

---

## 📁 수정된 파일 목록

아래 파일들에 포함된 모든 `TradingCalendar` 직접 호출을 `get_default_calendar()` 인스턴스를 사용하도록 수정했습니다.

### 1. 서비스 파일
-   ✅ `backend/app/services/chart_cache_service.py`
-   ✅ `backend/app/services/trading_service.py`

### 2. 테스트 파일
-   ✅ `backend/tests/test_trading_calendar_range.py`
    -   변경된 API(`get_previous_trading_day`, `get_trading_days`)에 맞게 테스트 로직을 재작성했습니다.
-   ✅ `backend/tests/test_chart_cache.py`
    -   `is_holiday`, `get_trading_days_between` 등 존재하지 않는 이전 API 호출을 현재 API에 맞게 수정했습니다.

---

## 🎯 최종 결과

-   `is_trading_day()` 관련 `TypeError`가 모두 해결되었습니다.
-   서비스 코드와 테스트 코드가 모두 변경된 `TradingCalendar` 설계에 맞게 업데이트되었습니다.

**수정 완료일**: 2025-10-11
**작성자**: Gemini
**상태**: ✅ 수정 완료
