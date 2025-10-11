# 한투 API Endpoint 분석: price-periodic vs inquire-daily-chartprice

**분석일**: 2025-10-11
**이슈**: `price-periodic` endpoint 404 에러

---

## 🔍 현재 상황

### 에러 로그 분석
```
TR_ID: FHKST03030100
URL: /uapi/overseas-price/v1/quotations/price-periodic
Status: 404 (Not Found)
```

### 코드 분석 (ki_api.py)

#### 1. get_overseas_price_periodic() - Line 586
```python
def get_overseas_price_periodic(
    self,
    market_code: str,
    item_code: str,
    start_date: str,
    end_date: str,
    period_code: str = "D",
):
    """해외 지수/환율 기간별 시세 조회 (price-periodic)"""
    url = "/uapi/overseas-price/v1/quotations/price-periodic"  # ❌ 404
    tr_id = "FHKST03030100"

    params = {
        "fid_cond_mrkt_div_code": market_code,
        "fid_input_iscd": item_code,
        "fid_input_date_1": start_date,
        "fid_input_date_2": end_date,
        "fid_period_div_code": period_code,
    }
```

#### 2. get_overseas_daily_chartprice() - Line 628
```python
def get_overseas_daily_chartprice(
    self,
    market_code: str,
    item_code: str,
    start_date: str,
    end_date: str,
    period_code: str = "D",
):
    """해외 종목/지수/환율 기간별 시세 조회 (inquire-daily-chartprice)"""
    url = "/uapi/overseas-price/v1/quotations/inquire-daily-chartprice"  # ✅ 정상
    tr_id = "FHKST03030100"  # 동일한 TR_ID!

    params = {
        "fid_cond_mrkt_div_code": market_code,
        "fid_input_iscd": item_code,
        "fid_input_date_1": start_date,
        "fid_input_date_2": end_date,
        "fid_period_div_code": period_code,
    }
```

---

## 📊 비교 분석

| 항목 | price-periodic | inquire-daily-chartprice |
|------|----------------|--------------------------|
| **Base Path** | `/uapi/overseas-price/v1/quotations/` | `/uapi/overseas-price/v1/quotations/` |
| **Endpoint** | `price-periodic` | `inquire-daily-chartprice` |
| **Full URL** | `.../price-periodic` | `.../inquire-daily-chartprice` |
| **TR_ID** | FHKST03030100 | FHKST03030100 |
| **Parameters** | 동일 | 동일 |
| **목적** | 해외 지수/환율 기간별 시세 | 해외 종목/지수/환율 기간별 시세 |
| **상태** | ❌ 404 에러 | ✅ 정상 작동 |

---

## 🎯 핵심 발견사항

### 1. 동일한 TR_ID 사용
- 두 endpoint 모두 `FHKST03030100` 사용
- **한투 API 특성**: 하나의 TR_ID가 여러 endpoint에 매핑될 수 있음

### 2. Base Path 동일
- 둘 다 `/uapi/overseas-price/v1/quotations/` 경로 하위
- `overseas-price` 경로는 **정확함**

### 3. Endpoint 이름만 다름
- `price-periodic` ❌ (존재하지 않음 또는 폐기됨)
- `inquire-daily-chartprice` ✅ (정상 작동)

---

## 🔍 가능한 시나리오

### Scenario 1: API 문서 변경 (가능성 ⭐⭐⭐⭐⭐)
**추측**:
- 초기에 `price-periodic` endpoint가 존재했음
- 한투에서 API 개편 시 `inquire-daily-chartprice`로 이름 변경
- TR_ID는 그대로 유지 (FHKST03030100)
- 구 endpoint는 폐기되어 404 반환

**근거**:
- 두 메서드의 파라미터와 목적이 거의 동일
- 같은 TR_ID 사용
- 한투 API는 버전 관리 시 endpoint 이름을 변경하는 경우가 많음

### Scenario 2: 문서 오류 (가능성 ⭐⭐)
**추측**:
- `price-periodic`은 처음부터 존재하지 않았음
- 누군가 잘못된 문서를 참고하여 코드 작성

### Scenario 3: 환경별 차이 (가능성 ⭐)
**추측**:
- 모의투자 vs 실전투자 환경에서 endpoint가 다를 수 있음
- 하지만 로그상 실전 URL 사용 중 (`openapi.koreainvestment.com:9443`)

---

## ✅ 결론 및 권장사항

### 결론
1. **`price-periodic` endpoint는 존재하지 않거나 폐기됨**
2. **`inquire-daily-chartprice`가 정식 endpoint임**
3. **두 메서드는 동일한 기능을 수행하려 했으나, periodic은 작동 불가**
4. **`/uapi/overseas-price/v1/quotations/` 경로는 정확함**

### 권장사항

#### Option 1: Fallback 제거 (✅ 추천)
```python
# korea_invest.py Line 639-656
async def get_overseas_index_price(...):
    try:
        # ✅ inquire-daily-chartprice만 사용
        raw_result = await self._run_in_executor(
            self.api_instance.get_overseas_daily_chartprice,
            market_code,
            index_code,
            start_date,
            end_date,
            period_code,
        )

        # ❌ Fallback 제거 (price-periodic 호출 삭제)
        # if not raw_result:
        #     raw_result = await self._run_in_executor(
        #         self.api_instance.get_overseas_price_periodic,
        #         ...
        #     )
```

**효과**:
- 불필요한 404 에러 로그 제거
- API 호출 횟수 감소 (성능 향상)
- 코드 간결화

#### Option 2: get_overseas_price_periodic() 메서드 제거
```python
# ki_api.py Line 586-626 삭제
# 아무도 사용하지 않는다면 완전 제거
```

**사전 확인 필요**:
```bash
# 사용처 확인
grep -rn "get_overseas_price_periodic" app/ services/ --include="*.py"
```

#### Option 3: 메서드 Deprecated 마크
```python
# ki_api.py
def get_overseas_price_periodic(...):
    """
    ⚠️ DEPRECATED: 이 endpoint는 존재하지 않습니다.
    대신 get_overseas_daily_chartprice()를 사용하세요.

    해외 지수/환율 기간별 시세 조회 (price-periodic)
    """
    raise DeprecationWarning(
        "price-periodic endpoint는 폐기되었습니다. "
        "get_overseas_daily_chartprice()를 사용하세요."
    )
```

---

## 📝 추가 조사 필요

### 한투 API 포털에서 확인 필요
1. TR_ID FHKST03030100의 공식 문서
2. 해외시세 API 목록
3. API 변경 이력 (Changelog)

### 확인 방법
```
1. https://apiportal.koreainvestment.com/ 로그인
2. [API 문서] → [해외주식] 메뉴 진입
3. "해외주식 기간별시세" 또는 TR_ID "FHKST03030100" 검색
4. 공식 endpoint URL 확인
```

---

## 🚨 즉시 조치 필요

**파일**: `app/core/korea_invest.py`
**Line**: 648-656
**조치**: Fallback 로직 제거

```python
# ❌ 제거할 코드
if not raw_result:
    raw_result = await self._run_in_executor(
        self.api_instance.get_overseas_price_periodic,
        market_code,
        index_code,
        start_date,
        end_date,
        period_code,
    )
```

**이유**:
- 매번 404 에러 발생 (로그 오염)
- 불필요한 API 호출
- 실제로 작동하지 않는 코드

---

**작성자**: Claude Code
**참고**: 한투 API 공식 문서 확인 후 최종 결정 필요
