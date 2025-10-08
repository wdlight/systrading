# 2025-10-08 해외 지수/환율 연동 작업 로그

## 개요
- 한국투자증권 OpenAPI의 `inquire-daily-chartprice` 엔드포인트를 이용해 NASDAQ, S&P 500, USD/KRW 환율을 백엔드/프론트에 통합.
- 기존 `price-periodic` 호출에서 발생한 404 오류를 확인하고, 문서에 명시된 정확한 REST 경로로 보완.
- Market Overview UI에 해외 지표 타일을 추가하고, WebSocket 이벤트가 동작하도록 타입/훅을 확장.

## 주요 변경 사항
### Backend
- `brokers/korea_investment/ki_api.py`
  - `get_overseas_daily_chartprice` 신규 추가 (TR_ID: FHKST03030100, URL: `/uapi/overseas-price/v1/quotations/inquire-daily-chartprice`).
  - 기존 `get_overseas_price_periodic`는 유지하여 호환성 보장.
- `app/core/korea_invest.py`
  - `get_overseas_index_price`가 `inquire-daily-chartprice`를 우선 호출 후 필요 시 `price-periodic`로 폴백.
  - 파싱 유틸(`_extract_float`, `_parse_overseas_index_response`)로 응답 값을 안전하게 정규화.
- `app/services/stock_info_service.py`
  - 인덱스 맵에 `nasdaq`, `sp500`, `usd_krw` 후보 코드 추가.
  - WebSocket 캐시/기본값과 함께 REST 결과를 통합.
- `app/models/schemas.py`
  - `MarketOverview` 모델에 NASDAQ, S&P500 필드를 추가.
- 새로운 테스트/스크립트
  - `tests/test_overseas_index_service.py`: 후보 코드 순회 및 유효성 검증.
  - `scripts/check_overseas_indices.py`: CLI에서 수동 확인 가능.

### Frontend (`stock-trading-ui`)
- `useMarketData` 훅: 해외 지수 코드와 WebSocket 이벤트 매핑 추가, 타입 안전성을 위한 payload 정의.
- `MarketOverview` 컴포넌트: NASDAQ/S&P500/USD-KRW 타일 및 “실시간 데이터 수신 대기” 메시지 추가.
- `lib/types.ts`: `MarketOverview`, `MarketIndex` 타입 확장.

## 검증 내역
- CLI: `python scripts/check_overseas_indices.py --target nasdaq|sp500|usd_krw` → 모두 정상 응답(`rt_cd=0`).
- 테스트: `./vkis/bin/python -m pytest tests/test_overseas_index_service.py -v` → 3 케이스 통과.
- 프런트 수동 확인: 백엔드/프런트 기동 후 http://localhost:9000 → Market Overview 섹션에 해외 지표 값 표시.

## 추후 작업/주의사항
- WebSocket 실시간 채널이 상시 가동 중인지 모니터링, 필요 시 실시간 캐시 확장.
- `npm run lint`는 기존 코드 전반의 경고/에러 때문에 실패하므로 별도 리팩터링 계획 필요.
- 운영환경 배포 전, AppKey에 해외 시세 권한 및 계좌 설정이 정확한지 재확인.
- 해외 지수/환율 외 추가 지표(다우존스, 다른 환율) 확장을 고려할 때 동일 패턴을 재활용 가능.
