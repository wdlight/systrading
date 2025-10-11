# 해외 API 404 에러 수정 (2025-10-11)

## 🐛 버그 설명

**증상:**
해외 지수/환율 기간별 시세 조회 API 호출 시 HTTP 404 Not Found 에러 발생.

**로그:**
```
ERROR    | brokers.korea_investment.ki_api:_url_fetch:959 - Response Text:
ERROR    | brokers.korea_investment.ki_api:_url_fetch:960 - Request URL: https://openapi.koreainvestment.com:9443/uapi/overseas-price/v1/quotations/price-periodic
```

**원인:**
`brokers/korea_investment/ki_api.py`의 `get_overseas_price_periodic` 함수에 잘못된 API 엔드포인트와 TR_ID가 하드코딩되어 있었음.

- **잘못된 URL**: `/uapi/overseas-price/v1/quotations/price-periodic`
- **잘못된 TR_ID**: `FHKST03030100`

**참고 문서:** `docs/KIS-API/oversea-stock.md`에 따르면 올바른 값은 다음과 같음.

- **올바른 URL**: `/uapi/overseas-stock/v1/quotations/price-periodic`
- **올바른 TR_ID**: `CTRP6504R`

---

## ✅ 적용된 수정

### Fix: `ki_api.py` URL 및 TR_ID 수정

**파일:** `/home/wide/projects/systrading/brokers/korea_investment/ki_api.py`

**변경 전 (594-596 라인):**
```python
def get_overseas_price_periodic(...):
    """해외 지수/환율 기간별 시세 조회 (price-periodic)"""
    url = "/uapi/overseas-price/v1/quotations/price-periodic"
    tr_id = "FHKST03030100"
    ...
```

**변경 후:**
```python
def get_overseas_price_periodic(...):
    """해외 지수/환율 기간별 시세 조회 (price-periodic)"""
    url = "/uapi/overseas-stock/v1/quotations/price-periodic"
    tr_id = "CTRP6504R"
    ...
```

---

## 📊 수정 전/후 비교

### 수정 전
- **API 요청 URL**: `.../uapi/overseas-price/...`
- **TR_ID**: `FHKST03030100`
- **결과**: HTTP 404 Not Found ❌

### 수정 후
- **API 요청 URL**: `.../uapi/overseas-stock/...`
- **TR_ID**: `CTRP6504R`
- **결과**: HTTP 200 OK ✅

---

## 📁 수정 파일 목록

### Backend
- ✅ `/home/wide/projects/systrading/brokers/korea_investment/ki_api.py`
  - `get_overseas_price_periodic` 메서드의 `url` 및 `tr_id` 변수 수정

### Documentation
- ✅ `/home/wide/projects/systrading/docs/bugfix/overseas-api-404-fix-20251011.md` (이 문서)

---

**수정 완료일**: 2025-10-11
**작성자**: Gemini
**상태**: ✅ 404 에러 수정 완료

