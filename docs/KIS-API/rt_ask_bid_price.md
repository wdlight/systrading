# 📘 실시간 매수/매도 호가 조회 가이드 (`realtime_ask_bid_price.md`)

한국투자증권 OpenAPI를 통해 **특정 종목의 실시간 매수/매도 호가**를 구독하는 방법에 대해 단계별로 설명합니다.  
웹소켓 기반 API를 활용하며, Python 예제와 함께 초보자를 위한 구성으로 안내드립니다.

---

## ✅ 1. 실시간 호가란?

> 호가란?
- 매수: 얼마에 사고 싶은지 제시한 가격
- 매도: 얼마에 팔고 싶은지 제시한 가격

실시간 호가 API를 통해 각 종목에 대해 **10단계까지의 매수/매도 호가와 잔량** 정보를 수신할 수 있습니다.

---

## ✅ 2. 주요 API 정보

| 항목 | 내용 |
|------|------|
| API 방식 | 웹소켓 (WebSocket) |
| 채널 ID | `H0STASP0` (국내주식 통합 호가) |
| 대상 종목 | KRX 및 NXT 통합 |
| 전송방식 | 실시간 Push (서버 → 클라이언트) |
| 통신주소 | `wss://openapi.koreainvestment.com:9443/websocket` |

---

## ✅ 3. 사전 준비 사항

1. **접근 토큰 발급 (`/oauth2/tokenP`)**
2. **웹소켓 접속키 발급 (`/oauth2/Approval`)**
3. **종목코드 확보**  
   예: 삼성전자 → `"005930"`

---

## ✅ 4. Python 예제 코드

```python
import websocket
import json
import threading

def on_message(ws, message):
    data = json.loads(message)
    print("📩 수신 데이터:", json.dumps(data, indent=2, ensure_ascii=False))

def on_error(ws, error):
    print("❌ 오류 발생:", error)

def on_close(ws, close_status_code, close_msg):
    print("🔌 연결 종료")

def on_open(ws):
    print("✅ 연결 성공")

    msg = {
        "header": {
            "approval_key": "발급받은_웹소켓_접속키를_입력하세요",
            "custtype": "P",
            "tr_type": "1",
            "content-type": "utf-8"
        },
        "body": {
            "input": {
                "tr_id": "H0STASP0",
                "tr_key": "005930"  # 예시: 삼성전자
            }
        }
    }

    ws.send(json.dumps(msg))

def run_websocket():
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        "wss://openapi.koreainvestment.com:9443/websocket",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

thread = threading.Thread(target=run_websocket)
thread.start()
```

---

## ✅ 5. 응답 데이터 예시

```json
{
  "askp1": "71200",      // 매도호가 1
  "askp_rsqn1": "450",   // 매도잔량 1
  "bidp1": "71100",      // 매수호가 1
  "bidp_rsqn1": "1200",  // 매수잔량 1
  ...
  "askp10": "72000",
  "bidp10": "70300"
}
```

---

## ✅ 6. 주의사항 및 팁

- **웹소켓 연결은 비동기 처리** 필요 (스레드/이벤트 기반 처리 권장)
- 종목코드는 반드시 **6자리** (`"005930"` 등)
- **인증정보 누락 시 수신 실패**
- **NXT 전용**, **체결가**, **예상체결** 등은 별도 채널 사용 필요

---

## 🔗 공식 샘플코드 (GitHub)

> 아래 GitHub에서 실시간 호가 샘플코드를 확인하실 수 있습니다:

- 국내주식 실시간 호가 (통합):  
  https://github.com/koreainvestment/open-trading-api/tree/main/examples_llm/domestic_stock/asking_price_total

---

## 🧩 관련 채널 요약

| 채널명 | 설명 | tr_id |
|--------|------|--------|
| 통합 호가 | KRX + NXT 자동 통합 | `H0STASP0` |
| KRX 호가 | 거래소(KRX) 전용 | `H0ASKP0` |
| NXT 호가 | 대체거래소(NEXTRADE) | `H0NTASP0` |

---

## 🧭 다음 추천 단계

- 실시간 체결가 API (`H0STCNT0`)
- 실시간 체결통보 (계좌 기반)
- 주문/정정/취소 연동

---

이 문서는 KIS Developers OpenAPI를 기반으로 작성되었습니다.
