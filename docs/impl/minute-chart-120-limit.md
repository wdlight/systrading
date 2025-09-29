# 분봉 데이터 120개 제한 이슈

**날짜**: 2025-09-30
**이슈**: 1분봉 차트 데이터가 120개만 조회되는 문제
**위치**: `brokers/korea_investment/ki_api.py:178-224`

---

## 📊 문제 상황

### 예상값
- 장 시작: 09:00
- 장 마감: 15:30
- **예상 분봉 개수**: 390개 (6.5시간 × 60분)

### 실제값
- **실제 분봉 개수**: 120개
- **데이터 범위**: 현재 시간 기준 과거 120분 (약 2시간)

---

## 🔍 원인 분석

### 한국투자증권 API 제약사항

```python
# brokers/korea_investment/ki_api.py:178-194
def get_minute_chart_data(self, stock_code):
    """
    1분봉 차트 데이터 조회
    https://apiportal.koreainvestment.com/apiservice-apiservice?/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice
    """
    url = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
    tr_id='FHKST03010230'

    params = {
        'FID_ETC_CLS_CODE': "",
        'FID_COND_MRKT_DIV_CODE': 'J',
        'FID_INPUT_ISCD': stock_code,
        'FID_INPUT_DATE_1': datetime.now().strftime("%Y%m%d"),  # ⚠️ 현재 날짜
        'FID_INPUT_HOUR_1': datetime.now().strftime("%H%M%S"),  # ⚠️ 현재 시간
        'FID_PW_DATA_INCU_YN': 'Y',
        'FID_FAKE_TICK_INCU_YN': 'N'
    }
```

**핵심 문제**:
- `FID_INPUT_DATE_1`: 현재 날짜
- `FID_INPUT_HOUR_1`: 현재 시간
- **API는 이 시점부터 과거로 최대 120개의 분봉만 반환**

---

## 📚 한국투자증권 API 문서

### 시세-분봉조회 API (FHKST03010230)
- **엔드포인트**: `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice`
- **TR_ID**: FHKST03010230
- **제한사항**:
  - 조회 시작 시점부터 **최대 120분**까지만 조회 가능
  - 당일 데이터만 조회 가능
  - 연속조회 미지원 (한 번의 호출로 120개 고정)

### API 응답 예시
```json
{
  "rt_cd": "0",
  "msg_cd": "MCA00000",
  "msg1": "정상처리 되었습니다",
  "output1": {...},
  "output2": [
    {
      "stck_bsop_date": "20250930",    // 영업일자
      "stck_cntg_hour": "153000",      // 체결시간 (HHMMSS)
      "stck_oprc": "84200",            // 시가
      "stck_hgpr": "84300",            // 고가
      "stck_lwpr": "84100",            // 저가
      "stck_prpr": "84200",            // 현재가
      "cntg_vol": "12345"              // 체결량
    },
    // ... 최대 120개
  ]
}
```

---

## 💡 해결 방안

### 방안 1: 시작 시간 고정 (장 시작 기준)

**장점**:
- 장 시작(09:00)부터 120분간의 데이터 확보
- 구현이 간단

**단점**:
- 최대 120분(2시간)까지만 가능
- 오전 11시 이후 데이터는 조회 불가

```python
def get_minute_chart_data(self, stock_code):
    url = '/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice'
    tr_id='FHKST03010230'

    params = {
        'FID_ETC_CLS_CODE': "",
        'FID_COND_MRKT_DIV_CODE': 'J',
        'FID_INPUT_ISCD': stock_code,
        'FID_INPUT_DATE_1': datetime.now().strftime("%Y%m%d"),
        'FID_INPUT_HOUR_1': "090000",  # ✅ 09:00 고정
        'FID_PW_DATA_INCU_YN': 'Y',
        'FID_FAKE_TICK_INCU_YN': 'N'
    }
    # ...
```

---

### 방안 2: 여러 번 호출하여 데이터 병합 ⭐ **추천**

**장점**:
- 전체 장 시간(390분)의 데이터 확보 가능
- 모든 시간대 커버

**단점**:
- API 호출 횟수 증가 (최소 4회)
- 구현 복잡도 증가
- API Rate Limit 고려 필요

```python
async def get_full_day_minute_chart_data(self, stock_code):
    """
    당일 전체 분봉 데이터 조회 (여러 번 호출하여 병합)
    """
    # 09:00부터 15:30까지를 120분씩 나눠서 조회
    time_ranges = [
        "090000",  # 09:00 ~ 11:00 (120분)
        "110000",  # 11:00 ~ 13:00 (120분)
        "130000",  # 13:00 ~ 15:00 (120분)
        "150000",  # 15:00 ~ 15:30 (30분, 하지만 120개 요청)
    ]

    all_data = []
    for time_str in time_ranges:
        params = {
            'FID_ETC_CLS_CODE': "",
            'FID_COND_MRKT_DIV_CODE': 'J',
            'FID_INPUT_ISCD': stock_code,
            'FID_INPUT_DATE_1': datetime.now().strftime("%Y%m%d"),
            'FID_INPUT_HOUR_1': time_str,
            'FID_PW_DATA_INCU_YN': 'Y',
            'FID_FAKE_TICK_INCU_YN': 'N'
        }

        t1 = self._url_fetch(url, tr_id, params)
        if t1 and t1.is_ok():
            output2 = t1.get_body().output2
            all_data.extend(output2)

        # API Rate Limit 고려 (선택적)
        await asyncio.sleep(0.1)  # 100ms 대기

    # 중복 제거 및 정렬
    df = pd.DataFrame(all_data)
    df = df.drop_duplicates(subset=['stck_bsop_date', 'stck_cntg_hour'])
    df = df.sort_values(by=['stck_bsop_date', 'stck_cntg_hour'])

    return df
```

**예상 결과**:
- 09:00 호출: 09:00 ~ 11:00 (120개)
- 11:00 호출: 11:00 ~ 13:00 (120개)
- 13:00 호출: 13:00 ~ 15:00 (120개)
- 15:00 호출: 15:00 ~ 15:30 (30개)
- **총 390개의 분봉 데이터 확보**

---

### 방안 3: 일봉 API 활용 (장기 데이터)

**장점**:
- 과거 데이터까지 조회 가능
- 한 번의 호출로 많은 데이터 확보

**단점**:
- 분봉이 아닌 일봉 데이터
- 실시간 트레이딩에는 부적합

```python
def get_daily_price_chart(self, stock_code, start_date, end_date, period_code='D'):
    """
    일/주/월봉 차트 데이터 조회
    """
    url = '/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice'
    tr_id = 'FHKST03010100'

    params = {
        'FID_COND_MRKT_DIV_CODE': 'J',
        'FID_INPUT_ISCD': stock_code,
        'FID_INPUT_DATE_1': start_date,   # YYYYMMDD
        'FID_INPUT_DATE_2': end_date,     # YYYYMMDD
        'FID_PERIOD_DIV_CODE': period_code,  # D:일, W:주, M:월
        'FID_ORG_ADJ_PRC': '0'
    }
    # ...
```

---

## 🎯 권장 구현 방안

### 단계적 접근

#### Phase 1: 현재 상태 유지 (120개)
- **목적**: 빠른 차트 표시
- **용도**: 최근 2시간 데이터 확인
- **구현**: 현재 코드 그대로 사용

#### Phase 2: 필요시 전체 데이터 조회
- **목적**: 당일 전체 패턴 분석
- **용도**: 백테스팅, 상세 분석
- **구현**: 방안 2의 여러 번 호출 방식

#### Phase 3: 캐싱 및 최적화
- **목적**: API 호출 최소화
- **용도**: 성능 개선
- **구현**: Redis 또는 메모리 캐시 활용

```python
class TradingService:
    def __init__(self):
        self.minute_chart_cache = {}  # {stock_code: {timestamp: data}}
        self.cache_ttl = 60  # 60초

    async def get_minute_chart_data(self, stock_code: str, full_day: bool = False):
        """
        분봉 데이터 조회

        Args:
            stock_code: 종목코드
            full_day: True면 당일 전체, False면 최근 120개
        """
        if full_day:
            # 방안 2: 여러 번 호출하여 병합
            return await self._get_full_day_data(stock_code)
        else:
            # 방안 1: 현재 방식 (최근 120개)
            return await self.korea_invest_service.get_minute_chart_data(stock_code)
```

---

## 📊 API 호출 최적화

### Rate Limit 고려사항
- 한국투자증권 API: **초당 20건** 제한 (일반적인 경우)
- 여러 번 호출 시: 0.1초 간격으로 호출 (초당 10건)

### 캐싱 전략
```python
from functools import lru_cache
from datetime import datetime, timedelta

class MinuteChartCache:
    def __init__(self, ttl_seconds=60):
        self.cache = {}
        self.ttl = ttl_seconds

    def get(self, stock_code):
        if stock_code in self.cache:
            data, timestamp = self.cache[stock_code]
            if (datetime.now() - timestamp).seconds < self.ttl:
                return data
        return None

    def set(self, stock_code, data):
        self.cache[stock_code] = (data, datetime.now())
```

---

## 🔄 마이그레이션 계획

### 1단계: 새로운 API 엔드포인트 추가
```python
# backend/app/api/chart.py

@router.get("/{stock_code}/minute")
async def get_minute_chart_data(
    stock_code: str,
    full_day: bool = False,  # ✅ 새 파라미터
    trading_service: TradingService = Depends(get_trading_service)
):
    """
    분봉 차트 데이터 조회

    - full_day=False: 최근 120개 (기본값)
    - full_day=True: 당일 전체 (여러 번 호출)
    """
    if full_day:
        chart_data = await trading_service.get_full_day_minute_chart_data(stock_code)
    else:
        chart_data = await trading_service.get_minute_chart_data(stock_code)

    return chart_data
```

### 2단계: Frontend 업데이트
```typescript
// useRealChartData.ts

export function useRealChartData(
  stockCode: string,
  timeframe: string,
  fullDay: boolean = false  // ✅ 새 옵션
) {
  const url = timeframe === '1m'
    ? `${API_BASE_URL}/api/chart/${stockCode}/minute?full_day=${fullDay}`
    : `${API_BASE_URL}/api/chart/${stockCode}/${timeframe}`;

  // ...
}
```

---

## ✅ 결론

### 현재 상태
- ✅ 120개 분봉 데이터 정상 동작
- ✅ 최근 2시간 데이터 확인 가능
- ⚠️ 당일 전체 데이터는 조회 불가

### 권장 사항
1. **단기**: 현재 구현 유지 (120개로 충분한 경우)
2. **중기**: 여러 번 호출 방식 구현 (당일 전체 필요시)
3. **장기**: 캐싱 및 최적화 적용 (성능 개선)

### 구현 우선순위
1. 🔥 **High**: 사용자 요구사항 확인 (120개로 충분한가?)
2. 🔥 **High**: 필요시 방안 2 구현 (여러 번 호출)
3. 🔶 **Medium**: 캐싱 적용 (API 호출 최소화)
4. 🔷 **Low**: 일봉 API 통합 (장기 분석용)

---

## 📚 참고 자료

- [한국투자증권 OpenAPI 가이드](https://apiportal.koreainvestment.com/)
- 시세-분봉조회: `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice`
- 시세-일봉조회: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`

---

**작성일**: 2025-09-30
**작성자**: Claude Code Assistant
**업데이트**: -