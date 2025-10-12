# 실행 기록 – KOSDAQ 지수 복구 (2025-10-08)

## 목표
KOSPI는 정상 표시되지만 KOSDAQ 지수가 항상 0으로 응답하는 현상을 해결하고, REST/WebSocket 경로를 모두 지원하도록 백엔드·프론트 구조를 개선한다.

## 수행 내용

1. **REST 응답 구조 보강**
   - `brokers/korea_investment/ki_api.py` → `get_index_current_price`가 `output/meta/ok`를 포함한 dict 반환.
   - `backend/app/core/korea_invest.py`
     - `last_raw_response`, `cached_indices` 캐시 추가.
     - RAW 메타 로그/캐시 업데이트 헬퍼 도입 (`update_cached_index`, `get_cached_index`).
   - `backend/tests/test_kosdaq_index_service.py`
     - 후보 코드(`J-1001`, `J-0201`, `J-1501`, `J-2001`, `U-1001`)를 순차 호출하고 RAW/메타를 출력.

2. **StockInfoService 후보 순회 + 캐시 fallback**
   - `backend/app/services/stock_info_service.py`
     - KOSDAQ 지수를 여러 코드로 호출 후 처음 0이 아닌 결과를 사용.
     - REST가 모두 실패하면 WebSocket 캐시(`KoreaInvestAPIService.cached_indices`)를 활용, 최종적으로 0 fallback.

3. **WebSocket 지수 처리 확장**
   - `backend/app/domestic_websocket.py`
     - 접속 시 `H0STISE0` + `tr_key=001/201` 자동 등록.
     - 수신한 지수 메시지를 `action_id='실시간지수'`로 큐에 전달, 메타 포함.
   - `backend/app/services/realtime_service.py`
     - `_extract_index_values`로 다양한 키(`bstp_nmix_prpr` 등)를 파싱.
     - `latest_market_indices` + `KoreaInvestAPIService.update_cached_index`로 실시간 값을 캐시.
     - 브로드캐스트 payload에 `raw/meta`를 추가.

4. **프론트엔드 fallback 표시**
   - `stock-trading-ui/src/lib/types.ts` → `MarketIndex`에 `raw/meta/timestamp` 필드 추가.
   - `useMarketData.ts` → WebSocket 수신 시 KOSDAQ 후보 코드 전체를 인식하고 raw/meta를 저장.
   - `MarketOverview.tsx` → 지수가 0일 경우 “실시간 데이터 수신 대기 중” 배지를 출력.

5. **문서/로그 기록**
   - `docs/plan/kosdaq-index-recovery-plan.md`에 구현 전략과 테스트 절차 정리.
   - `docs/bugfix/kospi-index-restoration-20251008.md`에 KOSPI 복구 내용과 Mermaid sequence 삽입.

## 테스트 & 확인

1. REST 후보 테스트
   ```bash
   cd backend
   ./vkis/bin/python tests/test_kosdaq_index_service.py -v
   ```
   - RAW 응답에 `rt_cd`, `msg_cd`, `msg1` 기록 확인.

2. 백엔드 실행
   ```bash
   cd backend
   scripts/start_backend.sh
   ```
   - `/api/stocks/overview` → `kospi.current`, `kosdaq.current` 확인 (캐시 값 사용 시 로그로 안내).

3. 프론트 확인
   ```bash
   cd stock-trading-ui
   npm run dev
   ```
   - http://localhost:9000 → Market Overview 카드에서 KOSDAQ 값(또는 “수신 대기”) 표시 확인.

4. WebSocket 로그
   - 백엔드 로그에서 `H0STISE0` 수신 및 `실시간지수` broadcast 기록 확인.

## 결과
- KOSPI는 REST로, KOSDAQ은 REST 실패 시 WebSocket 캐시를 활용하는 fallback 경로를 확보했다.
- 프론트는 데이터 유무에 따라 값을 표시하거나 “실시간 데이터 수신 대기 중” 메시지를 안내한다.
- 테스트/문서를 통해 향후 추가 코드 조합 실험이나 WebSocket 개선을 쉽게 이어갈 수 있다.

