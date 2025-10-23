📡 WebSocket 채널: H0STCNI0 (KRX 전용 체결가)

한국투자증권 OpenAPI에서 제공하는 `H0STCNI0`은 KRX 전용 체결가 실시간 수신 채널입니다.  
주식의 실시간 체결 데이터를 활용하여 분봉(OHLCV) 구성, 체결 분석, 보조지표 계산 등에 활용됩니다.

✅ 수신 메시지 형태

- 메시지는 ^ (캐럿) 구분자 구분의 문자열로 수신됩니다.
- 예시:
005930^093000^62200^100^2^200^0.32^62200^62100^300^200^1^50000^48000^1.12^1200000^74500000000^62000^62500^61800^109

📋 전체 필드 정의

순번 | 필드명             | 설명
-----|--------------------|-------------------------------
0    | symbol             | 종목코드
1    | tr_time            | 체결시간 (형식: HHMMSS)
2    | stck_prpr          | 체결가격 (현재가)
3    | stck_cntg_vol      | 체결수량
4    | prdy_vrss_sign     | 전일 대비 부호 (1:상한, 2:상승, 3:보합, 4:하한, 5:하락)
5    | prdy_vrss          | 전일 대비
6    | prdy_ctrt          | 전일 대비 등락률
7    | askp               | 매도호가
8    | bidp               | 매수호가
9    | askp_rsqn          | 매도호가 잔량
10   | bidp_rsqn          | 매수호가 잔량
11   | new_mkop_cls_code  | 장구분 코드
12   | total_askp_rsqn    | 총 매도호가 잔량
13   | total_bidp_rsqn    | 총 매수호가 잔량
14   | vol_tnrt           | 거래량 비율 (전일 대비)
15   | vol                | 누적 거래량
16   | value              | 누적 거래대금
17   | open               | 시가
18   | high               | 고가
19   | low                | 저가
20   | seq                | 수신번호 (체결 순번)

💡 활용 목적별 필드 요약

- 분봉 생성: tr_time, stck_prpr, stck_cntg_vol
- 보조지표 계산: vol, value
- 호가 분석: askp, bidp, askp_rsqn, bidp_rsqn
- 시장 상태 식별: new_mkop_cls_code

🧪 파싱 예시 (Python)

msg = "005930^093000^62200^100^2^200^0.32^62200^62100^300^200^1^50000^48000^1.12^1200000^74500000000^62000^62500^61800^109"
fields = msg.split("^")

parsed = {
    "symbol": fields[0],
    "tr_time": fields[1],
    "price": int(fields[2]),
    "volume": int(fields[3]),
    "diff_sign": fields[4],
    "diff": int(fields[5]),
    "diff_rate": float(fields[6]),
    "ask": int(fields[7]),
    "bid": int(fields[8]),
    "ask_qty": int(fields[9]),
    "bid_qty": int(fields[10]),
    "market_code": fields[11],
    "total_ask_qty": int(fields[12]),
    "total_bid_qty": int(fields[13]),
    "vol_ratio": float(fields[14]),
    "total_volume": int(fields[15]),
    "total_value": int(fields[16]),
    "open": int(fields[17]),
    "high": int(fields[18]),
    "low": int(fields[19]),
    "seq": int(fields[20]),
}

⏰ 수신 가능 시간 (KRX 기준)

- 정규장 체결 시간대만 수신 가능 (09:00 ~ 15:30)
- 시간외/프리장에서는 미수신
- NXT (넥스트레이드) 종목은 수신 불가 → H0TCNT0 사용 필요

🔚 요약

- 채널 ID: H0STCNI0
- 구분: KRX 전용 실시간 체결가
- 수신 형태: 문자열, ^ 구분
- 전체 필드 수: 21개
- 분봉 구성: 가능 (OHLCV 계산에 충분)
- 장점: 체결 단위 실시간 데이터 처리 가능
