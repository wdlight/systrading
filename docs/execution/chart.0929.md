# 차트 기능 구현 - 백엔드 API 개발 기록 (2025-09-29)

이 문서는 주식 차트 데이터 조회를 위한 백엔드 API 엔드포인트 개발 과정을 기록합니다.

## 1. 신규 서비스 생성 (`StockService`)

- **파일 경로**: `backend/app/services/stock_service.py`
- **목적**: 주식 관련 비즈니스 로직(차트 데이터 조회 등)을 처리하기 위한 서비스 레이어 추가.
- **주요 기능**: `get_chart_data` 메소드
  - KIS API의 '기간별 시세 조회' 기능을 호출합니다.
  - `stock_code`와 `period` (D, W, M)를 파라미터로 받아 조회 기간을 설정하고 `KoreaInvestAPIService`를 통해 데이터를 요청합니다.
  - 반환된 `DataFrame`을 프론트엔드에서 사용하기 용이한 JSON 형식으로 변환합니다. (`output2` 구조에 맞춤)

## 2. `KoreaInvestAPIService` 확장

- **파일 경로**: `backend/app/core/korea_invest.py`
- **변경 사항**: `get_daily_price_chart` 비동기 메소드 추가
  - 기존 `ki_api.py`에 존재하던 `get_daily_price_chart` 함수를 `KoreaInvestAPIService` 래퍼 클래스에서 비동기적으로 호출할 수 있도록 인터페이스를 추가했습니다.
  - `StockService`가 이 메소드를 통해 실제 KIS API를 호출하게 됩니다.

## 3. 의존성 주입 설정

- **파일 경로**: `backend/app/core/dependencies.py`
- **변경 사항**:
  - `get_stock_service` 팩토리 함수 추가: `StockService`의 싱글턴 인스턴스를 생성하고 제공합니다.
  - 전역 변수 `_stock_service`를 추가하고, 서비스 초기화를 위한 `reset_services` 함수에도 반영했습니다.

## 4. 신규 API 라우터 생성 (`stocks`)

- **파일 경로**: `backend/app/api/stocks.py`
- **목적**: 주식 데이터 관련 API 엔드포인트를 그룹화합니다.
- **주요 기능**: `GET /{stock_code}/chart` 엔드포인트
  - `stock_code`와 `period`를 파라미터로 받습니다.
  - `Depends(get_stock_service)`를 통해 `StockService`를 주입받습니다.
  - `stock_service.get_chart_data`를 호출하여 최종 데이터를 클라이언트에 반환합니다.

## 5. 메인 애플리케이션에 라우터 등록

- **파일 경로**: `backend/app/main.py`
- **변경 사항**:
  - `stocks_router`를 import 합니다.
  - `app.include_router(stocks_router, prefix="/api/stocks", tags=["stocks"])` 코드를 추가하여 FastAPI 앱에 신규 엔드포인트를 등록했습니다.
