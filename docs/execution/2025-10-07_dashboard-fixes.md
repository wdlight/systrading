# 작업 일지: 2025-10-07

## 주제: 대시보드 데이터 표시 오류 해결 및 컴포넌트 리팩토링

### 1. 초기 문제 진단
- **증상**: `localhost:9000` 대시보드 접속 시, 콘솔에 다수의 HTTP 404 (Not Found) 에러가 발생하며 데이터가 정상적으로 표시되지 않음.
- **원인**: 프론트엔드에서 호출하는 API 주소와 실제 백엔드의 API 주소가 일치하지 않음.
    - `/api/trading/conditions` -> `/api/conditions` 로 변경 필요.
    - `/api/market/overview` 엔드포인트가 백엔드에 존재하지 않음.

### 2. 백엔드 수정 및 복구
- **`/api/market/overview` API 구현**:
    - `app/services/stock_info_service.py`에 `pykrx`를 이용해 시장 지수를 조회하고, 주요 종목 정보를 포함하는 `get_market_overview` 서비스 로직 추가.
    - `app/api/stocks.py`에 `/api/stocks/overview` 엔드포인트 추가.
- **`ImportError` 해결**:
    - 위 과정에서 `MarketOverview` Pydantic 모델이 누락되어 `ImportError` 발생.
    - `app/models/schemas.py`에 `MarketOverview`, `MarketIndex`, `TopStock` 모델을 추가하여 해결.
- **API 라우팅 버그 수정**:
    - `/api/stocks/list` 경로에 404 오류가 추가로 발생.
    - `api/stocks.py`의 `APIRouter`에 `prefix`가 중복으로 잘못 추가된 것을 발견하고 제거하여 해결.
- **계좌 잔고 데이터 매핑 오류 수정**:
    - 보유 종목이 화면에 표시되지 않는 문제의 근본 원인.
    - `brokers/korea_investment/ki_api.py`에서 API 원본 데이터(영문 약어 필드)를 내부용 DataFrame(한글 필드)으로 변환하는 로직에 오류 발견.
    - `pchs_amt` -> `pchs_avg_pric` (매입단가), `evlu_erng_rt` -> `evlu_pfls_rt` (수익률) 등으로 필드 매핑을 수정하여 데이터가 올바르게 가공되도록 함.

### 3. 프론트엔드 수정 및 리팩토링
- **API 클라이언트 수정**:
    - `stock-trading-ui/src/lib/api-client.ts`에서 잘못된 API 경로들을 수정.
- **"보유 종목" 및 "관심 종목" 컴포넌트 분리**:
    - 기존 `WatchlistPanel`이 "Portfolio Holdings"라는 이름으로 잘못 사용되고 있던 문제 해결.
    - **`HoldingsPanel.tsx` 신규 생성**: `useAccountData` 훅을 사용하여 실제 계좌의 보유 종목(`positions`)을 표시하는 전용 컴포넌트.
    - **`WatchlistPanel.tsx` 역할 복원**: 제목을 "Watchlist"로 다시 변경하고, `useRealtimeData` 훅을 통해 관심 종목을 표시하는 원래 기능으로 역할을 명확히 함.
    - **`page.tsx` 레이아웃 수정**: 메인 페이지에 `HoldingsPanel`과 `WatchlistPanel`을 별개의 섹션으로 분리하여 배치.

### 최종 결과
- 백엔드 API 경로 및 데이터 처리 로직 정상화.
- 프론트엔드 대시보드에서 발생하는 모든 404 오류 해결.
- 보유 종목과 관심 종목이 명확히 분리된 두 개의 패널로 정상적으로 표시됨.
