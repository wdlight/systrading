해외 지수 / 환율 / 국채 / 금선물 시세 조회 API 안내

한국투자증권 OpenAPI를 활용하여 해외 지수 / 원달러 환율 / 국채 / 금선물 등의 기간별 시세 데이터를 조회하기 위한 상세 가이드입니다.

✅ API 개요

API 이름: 해외 종목/지수/환율/국채/금선물 기간별 시세

Endpoint: /uapi/overseas-stock/v1/quotations/price-periodic

TR_ID: CTRP6504R

HTTP Method: GET

응답 형식: JSON

✅ 요청 헤더 (Headers)

Content-Type: application/json; charset=utf-8
Accept: application/json
authorization: Bearer {ACCESS_TOKEN}
appkey: {APP_KEY}
appsecret: {APP_SECRET}
tr_id: CTRP6504R
custtype: P

✅ 요청 파라미터 (Params)

fid_cond_mrkt_div_code (시장 구분 코드): N (지수), X (환율), I (국채), S (금선물)

fid_input_iscd (종목 코드): 예) IXIC, FX@KRW 등

fid_input_date_1 (조회 시작일): 예) 20250901

fid_input_date_2 (조회 종료일): 예) 20251011

fid_period_div_code (주기): D (일), W (주), M (월), Y (연)

✅ 파라미터 조합 예시

[해외 지수 - 나스닥]
fid_cond_mrkt_div_code=N
fid_input_iscd=IXIC
fid_input_date_1=20250901
fid_input_date_2=20251011
fid_period_div_code=D

[환율 - USD/KRW]
fid_cond_mrkt_div_code=X
fid_input_iscd=FX@KRW
fid_input_date_1=20250901
fid_input_date_2=20251011
fid_period_div_code=D

[국채 수익률]
fid_cond_mrkt_div_code=I
fid_input_iscd=Y0201
fid_input_date_1=20250901
fid_input_date_2=20251011
fid_period_div_code=D

[금선물]
fid_cond_mrkt_div_code=S
fid_input_iscd=M0101
fid_input_date_1=20250901
fid_input_date_2=20251011
fid_period_div_code=D

✅ Python Request 샘플

import requests
url = "https://openapi.koreainvestment.com:9443/uapi/overseas-stock/v1/quotations/price-periodic
"

headers = {
"Content-Type": "application/json; charset=utf-8",
"Accept": "application/json",
"authorization": "Bearer {ACCESS_TOKEN}",
"appkey": "{APP_KEY}",
"appsecret": "{APP_SECRET}",
"tr_id": "CTRP6504R",
"custtype": "P"
}

params = {
"fid_cond_mrkt_div_code": "X",
"fid_input_iscd": "FX@KRW",
"fid_input_date_1": "20250901",
"fid_input_date_2": "20251011",
"fid_period_div_code": "D"
}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.json())

✅ 응답 예시

{
"output": [
{
"stck_bsop_date": "20250901",
"opnprc": "1330.50",
"hgpr": "1334.70",
"lwpr": "1328.40",
"clos": "1331.20",
"acml_vol": "0"
},
{
"stck_bsop_date": "20250902",
"opnprc": "1331.00",
"hgpr": "1335.80",
"lwpr": "1327.60",
"clos": "1333.70",
"acml_vol": "0"
}
]
}

※ 주요 응답 필드

stck_bsop_date: 기준일자

opnprc: 시가

hgpr: 고가

lwpr: 저가

clos: 종가

acml_vol: 거래량 (환율/지수는 일반적으로 0)

✅ 주요 종목 코드 참고

분류	코드
나스닥 지수	IXIC
S&P500	SPX
USD/KRW 환율	FX@KRW
유로/원	FX@EUR
국채 2년	Y0201
금선물	M0101

※ 전체 코드는 KIS Developers 포럼 > 종목정보 다운로드(해외)에서 확인

✅ 주의 사항

본 API는 엑셀 문서에는 등재되지 않은 공식 비공개 제공 API입니다.

반드시 TR_ID는 CTRP6504R로 고정해야 합니다.

종목코드는 시장에 따라 다르므로 정확히 입력해야 정상 응답됩니다.

✅ 관련 문서

KIS 공식 Github: https://github.com/koreainvestment/open-trading-api

KIS Developers 포털: https://apiportal.koreainvestment.com