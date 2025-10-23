# Korea Investment API 통합 테스트 계획

## 🎯 목적
- `KoreaInvestEnv`를 활용해 토큰을 자동 발급/갱신하면서 주요 REST API가 정상 응답하는지 간단히 검증한다.
- 각 API 호출의 Raw Response를 바로 확인할 수 있는 도구를 마련해 장애/지연 발생 시 빠르게 진단한다.

## 📚 테스트 대상 API 목록
`brokers/korea_investment/ki_api.py`에서 직접 제공하는 메서드를 중심으로 샘플 호출을 구성한다.

| 구분 | 메서드 | 주요 Endpoint / 용도 |
|------|--------|----------------------|
| 계좌 | `get_acct_balance` | `/uapi/domestic-stock/v1/trading/inquire-balance` 잔고 조회 |
| 시세 | `get_current_price` | `/uapi/domestic-stock/v1/quotations/inquire-price` 현재가 |
| 시세 | `get_minute_chart_data` / `get_daily_minute_chart_data` | `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice` 분봉 |
| 차트 | `get_daily_price_chart` | `/uapi/domestic-stock/v1/quotations/inquire-daily-price` 일봉 |
| 가능수량 | `get_orderable_amount` | `/uapi/domestic-stock/v1/trading/inquire-psbl-order` 주문가능수량 |
| 국내지수 | `get_index_current_price` | `/uapi/domestic-stock/v1/quotations/inquire-index-price` 지수 현재가 |
| 지수차트 | `get_index_chart_data` | `/uapi/domestic-stock/v1/quotations/inquire-index-daily-chartprice` |
| 해외 | `get_overseas_price_periodic`, `get_overseas_daily_chartprice` | `/uapi/overseas-stock/...` 해외 시세 |
| 체결 | `get_daily_ccld` | `/uapi/domestic-stock/v1/trading/inquire-daily-ccld` 일별 체결 |
| 주문 | `buy_order`, `sell_order`, `cancel_order`, `revise_order` | 실제 주문(모의/실계좌) ⇒ **옵션** | 

> ⚠️ 주문 관련 API는 위험도가 높으므로 기본 테스트 스위트에서는 제외하고, 필요 시 별도 플래그로 실행하도록 설계한다.

## 🧰 환경 준비
1. **설정 로드**
   - 기존 FastAPI 설정과 동일하게 `backend/app/core/config.get_settings()` 또는 `/config/secret_key/...`에 있는 KIS 설정을 사용한다.
   - 테스트 스크립트는 `sys.path`에 `backend` 를 추가한 뒤 `get_settings()` 호출로 환경을 로드한다.

2. **토큰 관리**
   - `KoreaInvestEnv(settings.model_dump())` 로 초기화하면 토큰 발급/갱신 및 헤더 구성이 자동 처리된다.
   - Env가 반환하는 `get_base_headers()` 를 `KoreaInvestAPI` 초기화 시 전달해 일관된 토큰을 사용한다.

3. **API 인스턴스**
   ```python
   from brokers.korea_investment.ki_env import KoreaInvestEnv
   from brokers.korea_investment.ki_api import KoreaInvestAPI

   env = KoreaInvestEnv(config_dict)
   api = KoreaInvestAPI(config_dict, base_headers=env.get_base_headers())
   ```

## 🏗️ 테스트 프로그램 설계
- Python `unittest` 모듈을 활용한 스위트(`test_api_calls.py`)을 작성한다.
- 공통 기반 클래스에서 `setUpClass`로 Env/API 객체를 생성하고, 각 테스트에서 개별 메서드를 호출한다.
- Raw Response 확인을 위해 `_url_fetch`가 반환하는 `APIResponse` 의 `get_body()` 결과를 `json.dumps(..., indent=2, ensure_ascii=False)` 로 출력한다.
- 호출 성공 여부는 `APIResponse.is_ok()` 또는 응답 코드(`rt_cd`, `msg1`)를 기반으로 단언한다.
- 네트워크 오류 시 재시도 대신 즉시 실패하도록 하여 문제 원인을 그대로 노출한다.

### 테스트 구성 초안
```python
class BaseKoreaInvestAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        settings = get_settings()
        config = settings.model_dump()
        cls.env = KoreaInvestEnv(config)
        cls.api = KoreaInvestAPI(config, base_headers=cls.env.get_base_headers())

    def _print_response(self, name, response):
        payload = response.get_body()
        print(f"\n[{name}] raw response:\n", json.dumps(payload.__dict__, indent=2, ensure_ascii=False))
        return payload
```
- 각 테스트 메서드는 `_print_response` 를 활용해 결과를 출력하고, 필요 시 특정 필드 존재 여부를 검증한다.

### 샘플 테스트 시나리오
1. `test_get_account_balance` – 계좌번호가 설정된 경우 잔고 조회.
2. `test_get_current_price` – 대표 종목(예: 삼성전자 005930)의 현재가 확인.
3. `test_get_minute_chart_data` – 동일 종목의 최근 분봉 10개 요청.
4. `test_get_orderable_amount` – 지정가 주문에 필요한 가능금액/수량 조회.
5. `test_get_index_current_price` – KOSPI/코스닥 지수 현재가.
6. `test_get_index_chart_data` – 동일 지수의 일봉 데이터 범위 요청.
7. `test_get_daily_ccld` – 일별 체결 내역 (데이터 없으면 gracefully skip).
8. `test_overseas_price_periodic` – 해외 종목(예: AAPL) 시세 조회. (환경에 해외 권한이 없는 경우 skip 처리.)

> ❗ 실계좌 환경에서는 API 호출에 제약이 있을 수 있으므로, 각 테스트는 예외 발생 시 `self.skipTest(...)`로 전환해 통과 판단한다.

## 🧾 로그 & 출력 정책
- stdout에 Raw JSON을 그대로 남겨 추후 복사/분석이 가능하도록 한다.
- `loguru` 기본 로거를 사용하면 headers/token 등 민감 정보가 출력될 수 있으니, 테스트 스크립트에서는 최소한의 정보만 출력하거나 `logger.remove()` 로 콘솔 로그를 제어한다.

## 🚀 실행 계획
1. `brokers/korea_investment/api-test/test_api_calls.py` 생성.
2. `python -m unittest brokers.korea_investment.api-test.test_api_calls` 형태로 실행.
3. 향후 CI에 통합할 경우, 환경 변수로 실계좌/모의계좌/주문 테스트 여부를 제어하는 플래그 제공 (`RUN_ORDER_TESTS=false` 등).
4. 필요 시 `pytest` 전환을 고려하지만, 초기 버전은 표준 라이브러리 `unittest`로 구현해 의존성을 최소화한다.

---

이 계획을 기반으로 테스트 스위트를 구현하면, 주요 REST API가 현재 네트워크/토큰 설정에서 정상 동작하는지 빠르게 검증할 수 있다.

## 🧪 실행 방법 (상세)
1. 프로젝트 루트에서 아래 명령을 실행합니다.
   ```bash
   cd /home/wide/projects/systrading
   python -m unittest brokers.korea_investment.api-test.test_api_calls -v
   ```
2. 필요 시 테스트 대상 종목 또는 지수 코드를 환경 변수로 지정할 수 있습니다.
   ```bash
   KI_TEST_STOCK_CODE=000660 KI_TEST_INDEX_CODE=1001 python -m unittest brokers.korea_investment.api-test.test_api_calls -v
   ```
3. 실행 결과는 각 테스트 케이스마다 Raw JSON이 출력되며, API 오류가 발생하면 `skipTest`로 표시되어 즉시 원인을 파악할 수 있습니다.
4. 주문 관련 테스트를 추가로 작성할 경우, `RUN_ORDER_TESTS=true` 와 같은 플래그를 사용해 선택적으로 실행하도록 구성합니다.

> ✅ 테스트는 실제 KIS 서버에 요청을 보내므로, 장 시간/권한 여부에 따라 일부 케이스가 자동으로 skip 될 수 있습니다.

