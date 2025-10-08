# KOSDAQ 지수 수신 복구 계획

한국투자증권 REST API가 KOSDAQ 지수를 0으로 반환하는 현상을 해결하기 위한 단계별 대책입니다. 초보 개발자도 따라 할 수 있도록 **변경 파일, 수정 포인트, 테스트 명령**을 구체적으로 정리했습니다.

---

## 1. REST 조회 개선

### 1-1. 후보 코드 확장 실험
- **파일**: `backend/tests/test_kosdaq_index_service.py`
- **목표**: 여러 `fid_input_iscd` 후보를 순차 호출하고 원본 응답(`rt_cd`, `msg_cd`, `msg1`)을 모두 로그로 남깁니다.
- **수정 예시**:
  ```python
  candidate_codes = [
      ("J", "1001"),  # 코스닥 기본 지수 (현재 0 응답)
      ("J", "0201"),  # 시장 누적 등락률 지수
      ("J", "1501"),  # KOSDAQ 150
      ("J", "2001"),  # 기타 업계에서 보고된 코드
      ("U", "1001"),  # 시장 코드 변경 실험
  ]

  raw_response = service.get_last_raw_response()
  print("rt_cd:", raw_response.get("rt_cd"))
  print("msg_cd:", raw_response.get("msg_cd"))
  print("msg1:", raw_response.get("msg1"))
  ```
- **테스트 명령**:
  ```bash
  cd backend
  ./vkis/bin/python tests/test_kosdaq_index_service.py -v
  ```

### 1-2. 서비스 레이어에서 후보 코드 순회
- **파일**: `backend/app/services/stock_info_service.py`
- **목표**: `get_market_indices()`에서 KOSDAQ 지수를 요청할 때 후보 리스트를 순회하여 처음으로 0이 아닌 값을 반환하는 조합을 사용합니다. 모든 후보가 0이면 마지막 응답과 `last_error`를 warning 로그로 남깁니다.
- **수정 개요**:
  ```python
  kosdaq_candidates = [("J", "1001"), ("J", "0201"), ("J", "1501"), ("J", "2001"), ("U", "1001")]

  for market_code, index_code in kosdaq_candidates:
      result = await self.korea_invest_service.get_index_current_price(index_code, market_code)
      if result and any([result.current, result.change, result.change_rate]):
          indices["kosdaq"] = ...
          break
  ````

### 1-3. 원본 응답 저장 메서드 추가
- **파일**: `backend/app/core/korea_invest.py`
- **목표**: `KoreaInvestAPIService`가 마지막 REST 호출의 원본 JSON을 저장해 테스트/서비스가 확인할 수 있게 합니다.
- **수정 포인트**:
  - `self.last_raw_response` 필드 추가
  - `_parse_index_response` 전후에 `self.last_raw_response = raw_result` 저장
  - `get_last_raw_response()` 헬퍼 메서드 제공

---

## 2. WebSocket 지수 수신 경로 구축

### 2-1. WebSocket 구독 등록
- **파일**: `backend/app/domestic_websocket.py`
- **작업**:
  - `cmd=...` 호출 리스트에 `H0STISE0` 구독을 추가 (`tr_key='201'` → KOSDAQ 지수).
  - 등록 직후 수신되는 메시지를 `ws_result_queue`에 `action_id='실시간지수'`, `index_code='201'` 형태로 push.

### 2-2. 실시간 서비스에서 KOSDAQ 처리
- **파일**: `backend/app/services/realtime_service.py`
- **작업**:
  - `action_id == '실시간지수'` 분기에서 `index_code in ('001','0001','201','1001')` 등을 모두 수용.
  - 브로드캐스트 payload에 `raw` 필드(전체 메시지)도 포함해 디버깅 지원.
  - `connection_manager.broadcast`의 `data.index_code`가 `'201'`인 경우 프론트에서 KOSDAQ 상태로 반영.

### 2-3. 백엔드 폴백 로직
- `StockInfoService.get_market_indices()`에서 REST 값이 0일 경우 WebSocket에서 최근 수신한 데이터를 캐시(`RealtimeDataService`가 보관하는 최신 지수 값)를 조회해 대체.
- REST + WebSocket 모두 실패 시 0 값 유지 + `warning` 로그.

---

## 3. 프론트엔드 측 대응

### 3-1. MarketOverview 훅 보강
- **파일**: `stock-trading-ui/src/hooks/useMarketData.ts`
- REST 응답이 0이거나 누락된 경우 “데이터 대기” 메시지를 보여주고, WebSocket으로 값이 들어오면 즉시 교체하도록 조건 분기 추가.

### 3-2. 상태 표시
- **파일**: `stock-trading-ui/src/components/trading/MarketOverview.tsx`
- KOSDAQ `current === 0`일 때 카드 하단에 “실시간 데이터 수신 대기 중” 배지 출력.

---

## 4. 테스트 및 검증 절차

1. **REST 후보 코드 테스트**
   ```bash
   cd backend
   ./vkis/bin/python tests/test_kosdaq_index_service.py -v
   ```
   - 로그에서 어떤 코드가 0이 아닌 값을 주었는지 확인
   - `logs/API_YYYYMMDD.log` 파일도 동시에 점검

2. **백엔드 서버 실행**
   ```bash
   cd backend
   scripts/start_backend.sh
   ```
   - `/api/stocks/overview` 응답의 `kosdaq.current`가 0 이상인지 확인
   - 로그에 `market_code`/`index_code` 및 `rt_cd`가 함께 찍히는지 체크

3. **프론트엔드 확인**
   ```bash
   cd stock-trading-ui
   npm run dev
   ```
   - http://localhost:9000 에서 Market Overview 카드가 KOSDAQ 값을 표시하는지 확인
   - 표시가 0이면 “데이터 대기” 배지가 보이는지 확인

4. **WebSocket 확인 (선택)**
   - 백엔드 로그에 `H0STISE0` 수신 메시지가 기록되는지 확인
   - 프론트 콘솔에서 WebSocket 메시지(`market_index_update`, `index_code: '201'`)가 도착하는지 점검

---

## 5. 현 상태 요약
- REST API는 `fid_cond_mrkt_div_code='J', fid_input_iscd='1001'` 조합에 대해 `rt_cd=0`이면서 값은 0으로 내려보냄 → 대체 코드, WebSocket 등 추가 시도가 필요.
- 본 계획은 REST 후보 탐색 + WebSocket 대체 + 프론트 fallback까지 포함한 통합 대책입니다.

---

## 6. 참조 자료
- 한국투자증권 공식 GitHub: <https://github.com/koreainvestment/open-trading-api>
- KIS API 문서 (업종/지수 조회 파라미터)

