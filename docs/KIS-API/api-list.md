# 한국투자증권 국내 주식 API 목록

이 문서는 한국투자증권의 국내 주식 관련 주요 API에 대한 명세와 사용법을 정리합니다.

## API 요약 목록

| ID | API 명 (URL) | 요약 설명 (20자 이내) |
| :--- | :--- | :--- |
| KIS-01 | 주식 잔고 조회 (`/uapi/domestic-stock/v1/trading/inquire-balance`) | 계좌 잔고 및 보유 종목 조회 |
| KIS-02 | 주식 주문 (현금) (`/uapi/domestic-stock/v1/trading/order-cash`) | 주식 현금 매수/매도 주문 실행 |
| KIS-03 | 주식 주문 정정/취소 (`/uapi/domestic-stock/v1/trading/order-rvsecncl`) | 미체결 주문 정정 또는 취소 |
| KIS-04 | 일별 주문 체결 조회 (`/uapi/domestic-stock/v1/trading/inquire-daily-ccld`) | 당일 및 과거 주문 체결 내역 조회 |
| KIS-05 | 기간별 시세 조회 (`/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`) | 일/주/월봉 등 과거 시세 조회 |
| KIS-06 | 현재가 조회 (`/uapi/domestic-stock/v1/quotations/inquire-price`) | 종목 현재가 및 호가 정보 조회 |
| KIS-07 | 매수 가능 조회 (`/uapi/domestic-stock/v1/trading/inquire-psbl-order`) | 최대 매수 가능 금액/수량 조회 |
| KIS-08 | Hashkey 발급 (`/uapi/hashkey`) | 주문용 일회성 해시키 발급 |

---

## KIS-01: 주식 잔고 조회
- **API 명**: 주식 잔고 조회
- **URL**: `/uapi/domestic-stock/v1/trading/inquire-balance`
- **요약**: 계좌의 총 평가금액, 개별 종목의 보유 수량, 수익률 등 잔고 현황을 조회합니다.
- **자동매매 활용 방안**: 매매 시작 전 보유 종목 및 수량 파악, 매매 후 포트폴리오 상태 확인, 리스크 관리(총 자산 대비 비중 조절)에 사용합니다.

### 요청 파라미터 예시
```json
{
    "CANO": "50087600",
    "ACNT_PRDT_CD": "01",
    "AFHR_FLPR_YN": "N",
    "OFL_YN": "",
    "INQR_DVSN": "02",
    "UNPR_DVSN": "01",
    "FUND_STTL_ICLD_YN": "N",
    "FNCG_AMT_AUTO_RDPT_YN": "N",
    "PRCS_DVSN": "00",
    "CTX_AREA_FK100": "",
    "CTX_AREA_NK100": ""
}
```

### 응답 예시
```json
{
    "ctx_area_fk100": "",
    "ctx_area_nk100": "",
    "output1": [
        {
            "pdno": "005930",
            "prdt_name": "삼성전자",
            "hldg_qty": "10",
            "ord_psbl_qty": "10",
            "pchs_amt": "75000",
            "prpr": "80000",
            "evlu_erng_rt": "6.67"
        }
    ],
    "output2": [
        {
            "tot_evlu_amt": "800000",
            "dnca_tot_amt": "750000"
        }
    ],
    "rt_cd": "0",
    "msg_cd": "SUCCESS",
    "msg1": "조회되었습니다."
}
```

### 주의사항
- 1회 조회 시 최대 20건까지 응답합니다. 보유 종목이 20건을 초과할 경우, 응답의 `ctx_area_fk100`, `ctx_area_nk100` 값을 다음 요청의 동일한 파라미터에 넣어 연속 조회해야 합니다.

---

## KIS-02: 주식 주문 (현금)
- **API 명**: 주식 주문 (현금)
- **URL**: `/uapi/domestic-stock/v1/trading/order-cash`
- **요약**: 지정가, 시장가 등 다양한 조건으로 현금 매수/매도 주문을 실행합니다.
- **자동매매 활용 방안**: 매매 전략에 따라 계산된 가격과 수량으로 실제 매수/매도 주문을 넣는 핵심 기능입니다.

### 요청 파라미터 예시 (매수)
```json
{
    "CANO": "50087600",
    "ACNT_PRDT_CD": "01",
    "PDNO": "005930",
    "ORD_DVSN": "01",
    "ORD_QTY": "10",
    "ORD_UNPR": "80000"
}
```

### 응답 예시
```json
{
    "output": {
        "ODNO": "0000123456",
        "ORD_TMD": "090001"
    },
    "rt_cd": "0",
    "msg_cd": "SUCCESS",
    "msg1": "주문 접수되었습니다."
}
```

### 주의사항
- 주문 API는 반드시 **Hashkey API(KIS-08)**를 먼저 호출하여 해시키를 발급받고, 그 값을 요청 헤더(header)에 포함해야 합니다.
- `ORD_DVSN` (주문 구분) 파라미터에 따라 지정가, 시장가 등 다양한 주문 유형을 선택할 수 있습니다.

---

## KIS-03: 주식 주문 정정/취소
- **API 명**: 주식 주문 정정/취소
- **URL**: `/uapi/domestic-stock/v1/trading/order-rvsecncl`
- **요약**: 미체결된 주문에 대해 가격, 수량 등을 정정하거나 주문 자체를 취소합니다.
- **자동매매 활용 방안**: 주문이 즉시 체결되지 않았을 경우, 시장 상황 변화에 대응하여 주문을 수정하거나 철회할 때 사용합니다.

### 요청 파라미터 예시 (취소)
```json
{
    "CANO": "50087600",
    "ACNT_PRDT_CD": "01",
    "KRX_FWDG_ORD_ORGNO": "90001",
    "ORGN_ODNO": "0000123456",
    "ORD_DVSN": "02",
    "RVSE_CNCL_DVSN_CD": "02",
    "ORD_QTY": "10",
    "ORD_UNPR": "80100",
    "QTY_ALL_ORD_YN": "Y"
}
```

### 응답 예시
```json
{
    "output": {
        "ODNO": "0000123457",
        "ORD_TMD": "090501"
    },
    "rt_cd": "0",
    "msg_cd": "SUCCESS",
    "msg1": "취소 주문 접수되었습니다."
}
```

### 주의사항
- 원주문 정보를 식별하기 위한 `KRX_FWDG_ORD_ORGNO`(한국거래소전송주문조직번호)와 `ORGN_ODNO`(원주문번호)가 필요합니다. 이 값들은 주문 실행 시 응답으로 받거나, 체결 내역 조회로 확인할 수 있습니다.
- 이 API 또한 **Hashkey API(KIS-08)** 호출이 선행되어야 합니다.

---

## KIS-04: 일별 주문 체결 조회
- **API 명**: 일별 주문 체결 조회
- **URL**: `/uapi/domestic-stock/v1/trading/inquire-daily-ccld`
- **요약**: 당일 및 과거 주문 체결 내역을 조회합니다.
- **자동매매 활용 방안**: 주문이 정상적으로 체결되었는지 확인하고, 실제 체결된 내역(가격, 수량)을 기록/분석하여 매매 일지를 작성하거나 성과를 분석하는 데 활용합니다.

### 요청 파라미터 예시
```json
{
    "CANO": "50087600",
    "ACNT_PRDT_CD": "01",
    "INQR_STRT_DT": "20240101",
    "INQR_END_DT": "20240131",
    "SLL_BUY_DVSN_CD": "00",
    "INQR_DVSN": "00",
    "PDNO": "",
    "CCLD_DVSN": "00",
    "ORD_GNO_BRNO": "",
    "ODNO": "",
    "INQR_DVSN_3": "00",
    "INQR_DVSN_1": "",
    "CTX_AREA_FK100": "",
    "CTX_AREA_NK100": ""
}
```

### 응답 예시
```json
{
    "output1": [
        {
            "ord_dt": "20240115",
            "ord_gno_brno": "06010",
            "odno": "0000123456",
            "orgn_odno": "",
            "ord_dvsn_name": "매수",
            "pdno": "005930",
            "prdt_name": "삼성전자",
            "ord_qty": "10",
            "ord_unpr": "80000",
            "tot_ccld_qty": "10",
            "avg_prvs": "80000",
            "tot_ccld_amt": "800000"
        }
    ],
    "rt_cd": "0",
    "msg_cd": "SUCCESS"
}
```

### 주의사항
- 조회 기간은 최대 90일까지 가능합니다.
- 조회할 데이터가 많을 경우 연속 조회가 필요할 수 있습니다. (`CTX_AREA_FK100`, `CTX_AREA_NK100` 사용)

---

## KIS-05: 기간별 시세 조회
- **API 명**: 기간별 시세 조회
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`
- **요약**: 일/주/월봉 등 과거 시세 데이터를 조회합니다.
- **자동매매 활용 방안**: 기술적 분석 지표(이동평균, RSI, MACD 등) 계산을 위한 기초 데이터를 확보합니다. 매매 전략을 개발하고 검증(백테스팅)하는 데 필수적입니다.

### 요청 파라미터 예시
```json
{
    "FID_COND_MRKT_DIV_CODE": "J",
    "FID_INPUT_ISCD": "005930",
    "FID_INPUT_DATE_1": "20240101",
    "FID_INPUT_DATE_2": "20240331",
    "FID_PERIOD_DIV_CODE": "D",
    "FID_ORG_ADJ_PRC": "1"
}
```

### 응답 예시
```json
{
    "output1": {
        "prdy_vrss_sign": "2",
        "prdy_vrss": "1000",
        "prdy_ctrt": "1.25"
    },
    "output2": [
        {
            "stck_bsop_date": "20240329",
            "stck_oprc": "79800",
            "stck_hgpr": "80800",
            "stck_lwpr": "79500",
            "stck_clpr": "80800",
            "acml_vol": "14789123"
        }
    ],
    "rt_cd": "0",
    "msg_cd": "SUCCESS"
}
```

### 주의사항
- 1회 조회 시 최대 100건의 봉 데이터를 응답합니다. 100건 이상의 데이터를 원할 경우, 마지막 날짜를 기준으로 다시 요청하는 방식으로 여러 번 호출해야 합니다.

---

## KIS-06: 현재가 조회
- **API 명**: 현재가 조회
- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-price`
- **요약**: 특정 종목의 현재가, 호가, 등락률 등 실시간 시세 정보를 조회합니다.
- **자동매매 활용 방안**: 실시간으로 시장 상황을 모니터링하고, 매수/매도 조건(예: 목표가 도달, 손절가 이탈)을 판단하는 데 사용합니다.

### 요청 파라미터 예시
```json
{
    "FID_COND_MRKT_DIV_CODE": "J",
    "FID_INPUT_ISCD": "005930"
}
```

### 응답 예시
```json
{
    "output": {
        "stck_prpr": "80800",
        "prdy_vrss": "1000",
        "prdy_vrss_sign": "2",
        "prdy_ctrt": "1.25",
        "askp1": "80800",
        "bidp1": "80700"
    },
    "rt_cd": "0",
    "msg_cd": "SUCCESS"
}
```

### 주의사항
- 실시간 데이터는 웹소켓(WebSocket)을 사용하는 것이 더 효율적입니다. 이 API는 특정 시점의 스냅샷을 얻는 데 유용합니다.

---

## KIS-07: 매수 가능 조회
- **API 명**: 매수 가능 조회
- **URL**: `/uapi/domestic-stock/v1/trading/inquire-psbl-order`
- **요약**: 최대 매수 가능 금액/수량 조회
- **자동매매 활용 방안**: 주문 실행 전, 주문 수량이 실제 매수 가능한 범위 내에 있는지 검증하여 주문 실패를 방지합니다.

### 요청 파라미터 예시
```json
{
    "CANO": "50087600",
    "ACNT_PRDT_CD": "01",
    "PDNO": "005930",
    "ORD_UNPR": "80000",
    "ORD_DVSN": "01",
    "CMA_EVLU_AMT_ICLD_YN": "N",
    "OVRS_ICLD_YN": "N"
}
```

### 응답 예시
```json
{
    "output": {
        "ord_psbl_cash": "1000000",
        "ord_psbl_qty": "12"
    },
    "rt_cd": "0",
    "msg_cd": "SUCCESS"
}
```

### 주의사항
- `ORD_UNPR` (주문 단가)를 얼마로 지정하는지에 따라 매수 가능 수량이 달라집니다.

---

## KIS-08: Hashkey 발급
- **API 명**: Hashkey 발급
- **URL**: `/uapi/hashkey`
- **요약**: 주문용 일회성 해시키 발급
- **자동매매 활용 방안**: 모든 매수/매도/정정/취소 주문 API 호출 직전에 반드시 호출해야 하는 선행 단계입니다. 보안을 위해 주문 요청을 암호화하는 데 사용됩니다.

### 요청 파라미터 예시
```json
{
    "CANO": "50087600",
    "ACNT_PRDT_CD": "01",
    "PDNO": "005930",
    "ORD_DVSN": "01",
    "ORD_QTY": "10",
    "ORD_UNPR": "80000"
}
```

### 응답 예시
```json
{
    "HASH": "verylonghashedstring...",
    "rt_cd": "0",
    "msg_cd": "SUCCESS"
}
```

### 주의사항
- Hashkey 발급 시 사용된 파라미터는 이후 실제 주문 요청의 파라미터와 동일해야 합니다.
- POST 요청으로 호출해야 합니다.