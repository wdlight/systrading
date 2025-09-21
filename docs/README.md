# Backend 서버 실행 및 종료 가이드

RSI/MACD 기반 주식 자동매매 시스템의 백엔드 서버 운영 가이드입니다.

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

## API 엔드포인트 (테스트 서버)

### 기본 엔드포인트
- `GET /` - 헬스체크
- `GET /hello` - 간단한 인사말
- `GET /health` - 상세 헬스체크

### 계좌 관련
- `GET /api/account/balance` - 더미 계좌 잔고
- `POST /api/account/refresh` - 계좌 정보 갱신

### 매매 관련
- `GET /api/trading/conditions` - 매매 조건 조회
- `PUT /api/trading/conditions` - 매매 조건 업데이트

### 워치리스트
- `GET /api/watchlist` - 워치리스트 조회

### 시장 정보
- `GET /api/market/overview` - 시장 개요

### WebSocket
- `WS /ws` - 실시간 데이터 스트림

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