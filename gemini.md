# Gemini 초기 Context - Stock Management App (최적화)

## 1. 프로젝트 개요
- **Next.js + FastAPI 기반** 주식 관리 앱 (모노레포 구조)
- **주요 기능**:
  - 실시간 주식 데이터 연동 및 시세 조회
  - 기술적 분석 지표(RSI, MACD 등) 기반 매수/매도 조건 판단
  - 자동 주문 실행 및 포트폴리오 관리
  - 코드 리뷰 및 기능 제안 지원

## 2. 전체 프로젝트 구조
- `stock-trading-ui/`: **Next.js 프론트엔드** 프로젝트
- `backend/`: **FastAPI 백엔드** 프로젝트
- `brokers/`: 증권사 API 연동 모듈 (한국투자증권, LS증권 등)
- `core/`: 주문 처리, 트레이딩 엔진 등 핵심 비즈니스 로직
- `services/`: 계좌, 주문 등 서비스 단위 로직 (백엔드와 분리)
- `utils/`: 로깅, 헬퍼 함수 등 공통 유틸리티
- `ui/`: QT, 모바일 등 추가 UI 관련 코드
- `legacy/`: 이전 버전 또는 테스트용 파이썬 스크립트
- **루트 폴더**: 단일 실행 스크립트, 설정 파일, 문서 등

## 3. 프론트엔드 (`stock-trading-ui`) 구조
- `src/app/`: Next.js 페이지 및 라우팅
- `src/components/`: 공통 및 UI 컴포넌트
- `src/hooks/`: 데이터 fetching, 상태 관리 등 커스텀 훅
- `src/lib/`: API 클라이언트, 타입 정의, 유틸리티 함수

## 4. 백엔드 (`backend/app`) 구조
- `main.py`: FastAPI 앱 진입점
- `api/`: HTTP API 엔드포인트 (계좌, 주문, 관심종목, 웹소켓)
- `core/`: 백엔드 설정, 의존성 주입, 증권사 API 래퍼
- `models/`: Pydantic 스키마 및 데이터 모델
- `services/`: 백엔드 비즈니스 로직 (계좌, 실시간 데이터, 기술 분석 등)
- `websocket/`: 웹소켓 연결 및 데이터 처리

## 5. 기술 스택
- **Backend**: FastAPI, Uvicorn, WebSockets
- **Frontend**: Next.js, React, TypeScript
- **Data Analysis**: pandas, numpy, talib-binary
- **API**: 한국투자증권 API (brokers/korea_investment)
- **Utilities**: pycryptodome, requests
- **Config**: pydantic, PyYAML, python-dotenv

## 6. 주요 프로세스
1. RSI + MACD 매수 조건 확인
2. 시장가 매수 주문 실행
3. 실시간 Watchlist 모니터링
4. 계좌조회 데이터 업데이트
5. 평균단가 기반 수익률 계산

## 7. 개발 주의사항
- 평균단가 `None` 값 예외 처리 필수
- API 응답 지연 및 비동기 처리 고려
- 실시간 데이터와 계좌조회 데이터 동기화 주의
- 로그 기반으로 데이터 흐름 및 오류 추적

## 8. 실행 기록 관리
- `docs/execution/impl[날짜][시간].md` 형식으로 작업 내용 기록
- **작업 유형**: 시스템 변경, API 연동, 버그 수정, 기능 추가, 인프라, 문제 해결
- Gemini가 자동 기록 작성을 지원

## 9. Gemini 사용 지침
- 프로젝트 구조 이해 기반 최적 지원
- 코드 리뷰, 기능 제안, 자동 실행 기록 작성
- **사용자 요청 예시**:
  - "Watchlist 실시간 동기화 문제 해결 방안 제시."
  - "TR 처리 속도 개선 방법 추천."
  - "새 API 엔드포인트 설계 리뷰."

## 10. 예시 질문 & 답변
**질문:** "Watchlist 실시간 동기화가 늦어."  
**답변:** 
```
- 원인: WebSocket 데이터와 REST 계좌 조회 타이밍 불일치
- 개선: 타이머별 처리 우선순위 조정, 미체결 데이터 캐싱
- 변경사항 docs/execution/impl[날짜][시간].md에 기록
```
**질문:** "새로운 매수 조건 추가할까?"  
**답변:**
```
- 기존: RSI + MACD
- 제안: 거래량 필터 + 이동평균 교차
- 코드 구조: services/trading_service.py
- 변경 후 실행 기록 docs/execution/impl[날짜][시간].md에 기록
```
