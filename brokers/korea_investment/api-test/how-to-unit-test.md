# Korea Investment API 스모크 테스트 실행 가이드

이 문서는 `brokers/korea_investment/api-test/test_api_calls.py`에 정의된 샘플 시나리오를 실제 환경에서 실행하기 위한 설정 방법과 명령어를 정리합니다.

---

## 1. 사전 준비

### 1.1 가상환경 및 의존성
```bash
cd /home/wide/projects/systrading
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1.2 인증 정보
1. **backend/.env**에 한국투자증권 실계좌 정보를 입력합니다. `Settings` 클래스가 가장 먼저 이 파일을 읽어 `KI_API_KEY`, `KI_SECRET_KEY`, `KI_ACCOUNT_NUMBER` 등을 로드합니다.
2. 추가/대체 구성이 필요한 경우 **backend/config.yaml**에 동일 키를 넣을 수 있습니다. `.env`가 존재하면 우선순위가 더 높으므로, 샘플 플레이스홀더(`your_account_number_here`)는 삭제하거나 실제 값으로 덮어써야 합니다.  
   - 테스트 코드(`test_api_calls.py`)는 내부적으로 `get_korea_invest_config()` 결과를 사용해 `api_key`, `api_secret_key`, `stock_account_number` 등의 소문자 키로 변환합니다. 따라서 `.env`/`config.yaml`에 값만 정확히 들어 있으면 별도 매핑은 필요하지 않습니다.
   - 모의투자 계정을 사용할 경우 `paper_api_key`, `paper_api_secret_key`, `is_paper_trading=true`도 함께 설정하세요.
3. `access.tok`(토큰 캐시)이 오래된 상태라면 삭제 후 테스트를 실행해 새 토큰을 받아 두는 것이 안전합니다.
4. 값이 정상적으로 로드되었는지 확인하려면 테스트 실행 시 로그에서 `base_headers['appkey']`, `env.config['stock_account_number']`가 비어 있지 않은지 확인합니다. 비어 있다면 `.env` 또는 `config.yaml`에 올바른 키 이름이 들어갔는지 다시 점검하세요.

### 1.3 환경 변수로 테스트 대상 제어

| 환경 변수 | 의미 | 기본값 |
|-----------|------|--------|
| `KI_TEST_STOCK_CODE` | 국내 종목 코드 | `005930` (삼성전자) |
| `KI_TEST_INDEX_MARKET` | 지수 시장 코드 (`U`: KOSPI, `J`: KOSDAQ) | `U` |
| `KI_TEST_INDEX_CODE` | 지수 코드 | `0001` (KOSPI) |
| `KI_TEST_SAMPLE_PRICE` | 주문가능금액 조회용 가격 | `70000` |

---

## 2. 테스트 실행 방법

모든 테스트 실행:
```bash
cd /home/wide/projects/systrading
python -m unittest brokers.korea_investment.api-test.test_api_calls -v
```

특정 테스트만 실행(예: 계좌 잔고 확인):
```bash
python -m unittest \
  brokers.korea_investment.api-test.test_api_calls.KoreaInvestAccountScopedTests.test_get_account_balance \
  -v
```

환경 변수와 함께 실행(다른 종목으로 현재가 확인):
```bash
KI_TEST_STOCK_CODE=000660 \
python -m unittest brokers.korea_investment.api-test.test_api_calls.KoreaInvestAPISmokeTests.test_get_current_price -v
```

> 각 테스트는 Raw JSON 응답을 그대로 stdout에 출력합니다. API 오류가 발생하면 `skipTest` 상태로 이유를 알려줍니다.

---

## 3. 시나리오별 가이드

### 3.1 `test_get_account_balance`
- **목적**: `/uapi/domestic-stock/v1/trading/inquire-balance`
- **필수 조건**: 실계좌 권한 필요
- **출력**: 보유 종목(`output1`), 계좌 요약(`output2`)
```bash
python -m unittest brokers.korea_investment.api-test.test_api_calls.KoreaInvestAccountScopedTests.test_get_account_balance -v
```

### 3.2 `test_get_current_price`
- **목적**: `/uapi/domestic-stock/v1/quotations/inquire-price`
- **출력**: 단일 종목 현재가(`stck_prpr`)
```bash
python -m unittest brokers.korea_investment.api-test.test_api_calls.KoreaInvestAPISmokeTests.test_get_current_price -v
```

### 3.3 `test_get_minute_chart_data`
- **목적**: `/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice`
- **특징**: pandas DataFrame으로 분봉 데이터 반환 (장 외 시간에는 데이터가 없을 수 있음)
```bash
python -m unittest brokers.korea_investment.api-test.test_api_calls.KoreaInvestAPISmokeTests.test_get_minute_chart_data -v
```

### 3.4 `test_get_index_current_price`
- **목적**: 국내 업종/지수 현재가 조회
- **환경 변수**: `KI_TEST_INDEX_MARKET`, `KI_TEST_INDEX_CODE`
```bash
python -m unittest brokers.korea_investment.api-test.test_api_calls.KoreaInvestAPISmokeTests.test_get_index_current_price -v
```

### 3.5 `test_get_daily_price_chart`
- **목적**: `/uapi/domestic-stock/v1/quotations/inquire-daily-price`
- **출력**: 지정 기간의 일봉 데이터 DataFrame
```bash
python -m unittest brokers.korea_investment.api-test.test_api_calls.KoreaInvestAPISmokeTests.test_get_daily_price_chart -v
```

### 3.6 `test_get_orderable_amount`
- **목적**: `/uapi/domestic-stock/v1/trading/inquire-psbl-order`
- **필수 조건**: 계좌 거래 권한
```bash
python -m unittest brokers.korea_investment.api-test.test_api_calls.KoreaInvestAccountScopedTests.test_get_orderable_amount -v
```

---

## 4. 자주 발생하는 문제와 해결

| 증상 | 원인 | 해결 방법 |
|------|------|-----------|
| 요청 파라미터에 `your_account_number_here`가 포함 | `.env` 플레이스홀더가 우선 적용됨 | `.env`의 값을 실제 값으로 교체하거나 키 삭제 |
| 401/500 응답 | 토큰 만료 혹은 권한 부족 | `access.tok` 삭제 후 재실행, 계좌 권한 확인 |
| 테스트가 모두 skip | 장 외 시간 또는 데이터 없음 | 장 중에 재실행하거나 다른 종목/지수로 변경 |

---

## 5. 주문/해외 API 확장 (옵션)
- 주문 관련 테스트는 실계좌 위험이 크므로 기본 스위트에 포함하지 않았습니다.
- 필요 시 `RUN_ORDER_TESTS=true` 같은 플래그를 사용해 조건부 실행하도록 확장하세요.
- 해외 시세 API(`get_overseas_price_periodic`, `get_overseas_daily_chartprice`)도 동일 패턴으로 추가할 수 있습니다.

---
