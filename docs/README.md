# 주식 자동매매 시스템 (Stock Trading System)

RSI/MACD 기반 한국 주식 자동매매 시스템 - 실시간 차트, 지수 모니터링, 자동 매매 전략 실행

**최종 업데이트**: 2025-10-08

---

## 📋 프로젝트 개요

한국투자증권 OpenAPI를 활용한 실시간 주식 트레이딩 시스템으로, 다음 기능을 제공합니다:

### 🎯 주요 기능

#### 1. 실시간 시장 데이터

- **국내 지수**: KOSPI, KOSDAQ 실시간 모니터링
- **해외 지수**: NASDAQ, S&P 500 조회 (2025-10-08 추가)
- **환율**: USD/KRW 실시간 환율 (2025-10-08 추가)
- **WebSocket 실시간 데이터**: REST API 실패 시 자동 fallback

#### 2. 고급 차트 기능

- **분봉 차트**: 1분봉 실시간 업데이트
- **일봉 차트**: 연도별 캐싱으로 빠른 로딩 (2025-10-05 추가)
- **드래그 & 로드**: 차트 드래그 시 과거 데이터 자동 로딩
- **기술적 지표**: RSI, MACD, 이동평균선

#### 3. 포트폴리오 관리

- **보유 종목**: 실시간 계좌 잔고 및 수익률
- **관심 종목**: 별도 워치리스트 관리 (2025-10-07 분리)
- **매매 조건**: RSI/MACD 기반 자동 매매 설정

#### 4. 안정성 & 성능

- **연도별 캐싱**: 일봉 데이터 효율적 관리
- **REST + WebSocket**: 이중화된 데이터 소스
- **에러 핸들링**: 자동 재시도 및 fallback 로직

---

## 서버 구성

이 프로젝트에는 **2개의 백엔드 서버**가 있습니다:

### 1. 메인 서버 (Full API - `backend/app/main.py`)

**실행 방법:**

```bash
# 프로젝트 루트에서
cd backend
python -m app.main

# 또는 uvicorn으로 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**기능:**

- 완전한 FastAPI 서버
- 한국투자증권 API 연동
- WebSocket 실시간 데이터
- 계좌/매매/워치리스트 API

### 2. 간단한 테스트 서버 (`backend/simple_server.py`)

**실행 방법:**

```bash
# 프로젝트 루트에서
cd backend  
python simple_server.py

# 또는 uvicorn으로 직접 실행
uvicorn simple_server:app --host 0.0.0.0 --port 8000 --reload
```

**기능:**

- 프론트엔드 테스트용
- 더미 데이터 제공
- WebSocket 연결 테스트

## 서버 종료 방법

### 1. 일반적인 종료

```bash
Ctrl + C
```

터미널에서 실행 중인 서버를 중단합니다.

### 2. 프로세스 직접 종료 (Windows)

```bash
# 포트 8000에서 실행 중인 프로세스 찾기
netstat -ano | findstr :8000

# PID로 프로세스 종료
taskkill /PID [PID번호] /F
```

## 서버 접속 URL

- **API 서버**: http://localhost:8000
- **헬스체크**: http://localhost:8000/health
- **Hello 엔드포인트**: http://localhost:8000/hello (simple_server만)
- **API 문서**: http://localhost:8000/docs (FastAPI 자동 생성)
- **WebSocket**: ws://localhost:8000/ws

## 사전 준비사항

### 1. Python 가상환경 활성화

```bash
# Windows
.\vkis\Scripts\activate

# Linux/Mac
source vkis/bin/activate
```

### 2. Dependencies 설치

```bash
pip install -r requirements.txt
```

### 3. 환경설정 (메인 서버용)

메인 서버(`backend/app/main.py`)를 사용하려면 한국투자증권 API 설정이 필요합니다.
환경설정 파일이 없는 경우 테스트 서버(`backend/simple_server.py`)를 사용하세요.

## 📡 API 엔드포인트

### 기본 엔드포인트

- `GET /` - 헬스체크
- `GET /hello` - 간단한 인사말
- `GET /health` - 상세 헬스체크

### 계좌 관련

- `GET /api/account/balance` - 계좌 잔고 조회
- `POST /api/account/refresh` - 계좌 정보 갱신

### 매매 관련

- `GET /api/trading/conditions` - 매매 조건 조회 *(수정: /api/conditions)*
- `PUT /api/trading/conditions` - 매매 조건 업데이트

### 종목 관리

- `GET /api/watchlist` - 관심 종목 조회
- `GET /api/stocks/list` - 종목 리스트 조회
- `GET /api/stocks/overview` - 시장 개요 (KOSPI/KOSDAQ/해외지수/환율 포함) ✨ *2025-10-08 업데이트*

### 차트 데이터 🆕

- `GET /api/chart/{stock_code}/minute` - 분봉 차트 데이터
  - Query: `start_date`, `end_date`
- `GET /api/chart/{stock_code}/day` - 일봉 차트 데이터 ✨ *2025-10-05 추가*
  - Query: `start_date`, `end_date`
  - 연도별 캐싱으로 빠른 응답

### WebSocket 실시간 데이터

- `WS /ws` - 실시간 데이터 스트림
  - **이벤트 타입**:
    - `market_index_update` - 지수 업데이트 (KOSPI/KOSDAQ)
    - `price_update` - 종목 가격 업데이트
    - `portfolio_update` - 포트폴리오 변경

## 트러블슈팅

### 포트 충돌 문제

다른 프로세스가 8000번 포트를 사용 중인 경우:

```bash
# 포트 사용 프로세스 확인
netstat -ano | findstr :8000

# 해당 프로세스 종료
taskkill /PID [PID번호] /F
```

### 모듈 import 오류

프로젝트 루트에서 실행하고 가상환경이 활성화되었는지 확인하세요.

### 환경설정 오류

메인 서버에서 설정 오류가 발생하면 테스트 서버를 사용하여 프론트엔드를 테스트할 수 있습니다.

## 개발 시 권장사항

1. **테스트 서버 우선 사용**: 프론트엔드 개발 시 `simple_server.py` 사용
2. **자동 리로드**: `--reload` 옵션으로 코드 변경 시 자동 재시작
3. **로그 확인**: 터미널에서 실시간 로그 모니터링
4. **API 문서 활용**: http://localhost:8000/docs 에서 API 테스트

---

## 📚 추가 문서

- **작업 로그**: `docs/work-log/` - 일일/주간 작업 내역
- **실행 기록**: `docs/execution/` - 주요 기능 구현 상세 로그
- **계획 문서**: `docs/plan/` - 기능 기획 및 설계 문서
- **버그 수정**: `docs/bugfix/` - 버그 분석 및 해결 과정
- **아키텍처**: `docs/arch/` - 시스템 설계 및 다이어그램
- **운영 가이드**: `docs/operations/` - 배포 및 모니터링 가이드
- **테스트 가이드**: `docs/testing/` - 테스트 절차 및 방법

---

## 🔄 최근 업데이트 (2025-10-03 ~ 2025-10-08)

### 2025-10-08

- ✅ NASDAQ, S&P 500, USD/KRW 환율 연동 완료
- ✅ KOSPI/KOSDAQ 지수 REST + WebSocket 이중화
- ✅ 해외 지수 후보 코드 순회 로직 구현

### 2025-10-07

- ✅ 대시보드 보유 종목/관심 종목 패널 분리
- ✅ API 경로 404 오류 전체 수정
- ✅ 계좌 잔고 필드 매핑 오류 해결

### 2025-10-05

- ✅ 일봉 차트 API 및 UI 구현 완료
- ✅ 연도별 캐싱 시스템 적용
- ✅ 분봉/일봉 동시 표시 기능

### 2025-10-04

- ✅ 차트 드래그 시 과거 데이터 자동 로딩
- ✅ X축 시간 표시 개선 (30분 단위)
- ✅ Props Passing 패턴으로 데이터 흐름 개선

### 2025-10-03

- ✅ 차트 렌더링 성능 최적화
- ✅ UTC 타임존 처리 로직 수정
- ✅ 휴장일 대응 로직 구현

---

## 🎯 향후 계획

### 단기 (1-2주)

- WebSocket 실시간 해외 지수 통합
- 다중 종목 차트 비교 기능
- 매매 전략 백테스팅 UI

### 중기 (1개월)

- 알림 시스템 (가격 알림, 조건 충족 알림)
- 포트폴리오 분석 대시보드
- 거래 히스토리 및 성과 분석

### 장기 (3개월)

- 머신러닝 기반 가격 예측
- 다중 계좌 지원
- 모바일 앱 개발

---

**문서 작성일**: 2025-10-08
**프로젝트 버전**: v0.9.0 (Beta)