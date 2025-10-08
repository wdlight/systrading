고객님, 안녕하십니까?

**KOSPI / KOSDAQ 정보를 가져오는 방법**은 크게 두 가지로 나뉩니다.

---

### 📊 1️⃣ 종목정보(코드, 시장구분 등) 조회

**KOSPI / KOSDAQ 상장 종목 목록**이나 **기초정보(코드, 명칭, 업종 등)**를 얻으시려면
다음 FAQ에 명시된 **마스터파일(.mst)**을 활용하시면 됩니다.

> * KOSPI 종목정보:
>   → `kis_kospi_code_mst.py`
> * KOSDAQ 종목정보:
>   → `kis_kosdaq_code_mst.py`
>
> 두 파일 모두 한국투자증권 공식 GitHub에 공개되어 있으며,
> 파일을 `.txt`로 확장자 변경 후 텍스트로 열면 종목코드와 시장구분을 확인하실 수 있습니다.

해당 자료는 아래 공식 경로에서 확인 가능합니다.
👉 [https://github.com/koreainvestment/open-trading-api/tree/main/stocks_info](https://github.com/koreainvestment/open-trading-api/tree/main/stocks_info)

---

### 📈 2️⃣ 시세(가격, 지수, 변동률 등) 조회

KOSPI / KOSDAQ 지수나 종목별 시세를 실시간 또는 과거 데이터로 조회하시려면
**한국투자증권 Open API의 ‘국내주식시세’ 카테고리**를 사용합니다.

| 구분                    | 주요 API                                                   | 설명                                   |
| --------------------- | -------------------------------------------------------- | ------------------------------------ |
| **실시간 시세(WebSocket)** | `/uapi/domestic-stock/v1/market-data` (통합/KRX/NXT)       | 국내주식(KOSPI·KOSDAQ) 실시간 호가 및 체결 정보 수신 |
| **일별/기간별 시세(REST)**   | `/uapi/domestic-stock/v1/quotations/inquire-daily-price` | 일/주/월/년 단위 시세 조회                     |
| **현재가/지수 조회**         | `/uapi/domestic-stock/v1/quotations/inquire-price`       | 개별 종목 또는 KOSPI·KOSDAQ 업종지수 조회 가능     |

> 💡 지수 조회 시
>
> * `fid_cond_mrkt_div_code`: 시장구분코드 (`U`: KOSPI, `J`: KOSDAQ)
> * `fid_input_iscd`: 지수코드 (예: `0001` = 코스피, `1001` = 코스닥)

---

### ✅ 요약

| 목적                | 방법 / API                               | 비고               |
| ----------------- | -------------------------------------- | ---------------- |
| KOSPI/KOSDAQ 종목목록 | “종목정보 다운로드(국내)” FAQ → `.mst` 파일 이용     | GitHub에서 다운로드 가능 |
| 실시간 시세            | WebSocket API (KRX 또는 통합)              | 체결/호가/예상체결 등     |
| 일별/기간별 시세         | REST `/quotations/inquire-daily-price` | 과거 데이터 분석용       |
| 업종/지수 시세          | REST `/quotations/inquire-index`       | 코스피·코스닥 지수 등     |

---

보다 구체적인 사용 예제 및 샘플 코드는
**KIS 공식 GitHub** 내 `examples_llm/domestic_stock` 폴더에서 확인하실 수 있습니다.
👉 [https://github.com/koreainvestment/open-trading-api](https://github.com/koreainvestment/open-trading-api)

---

이와 같은 방식으로 KOSPI, KOSDAQ 데이터를 안정적으로 조회하실 수 있습니다.
