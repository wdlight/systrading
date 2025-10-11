# 포트폴리오 프론트엔드 통합 가이드 (초보자용)

> **📌 이 가이드의 목적**: 백엔드에서 구현된 포트폴리오 이력 조회 API를 프론트엔드와 연결하여 실제 차트에 데이터를 표시하는 방법을 단계별로 배웁니다.

**작성일**: 2025-10-11
**난이도**: ⭐⭐☆☆☆ (초급)
**예상 소요 시간**: 30분

---

## 📚 목차

1. [소개](#1-소개)
2. [시스템 이해하기](#2-시스템-이해하기)
3. [시작하기 전 준비](#3-시작하기-전-준비)
4. [환경 설정](#4-환경-설정)
5. [백엔드 실행하기](#5-백엔드-실행하기)
6. [프론트엔드 실행하기](#6-프론트엔드-실행하기)
7. [통합 검증하기](#7-통합-검증하기)
8. [문제 해결](#8-문제-해결)
9. [다음 단계](#9-다음-단계)

---

## 1. 소개

### 1.1 이 가이드가 필요한 이유

현재 프론트엔드는 **Mock 데이터**(가짜 데이터)를 사용하여 포트폴리오 차트를 표시하고 있습니다. 하지만 백엔드에서 **실제 계좌 데이터**를 기반으로 한 API가 완성되었으므로, 이제 진짜 데이터로 차트를 보여줄 차례입니다!

**현재 상태**:
- ❌ 프론트엔드: Mock 데이터 사용 중 (⚠️ 샘플 데이터 경고 표시)
- ✅ 백엔드: 실제 API 구현 완료 (`/api/portfolio/history`)

**목표 상태**:
- ✅ 프론트엔드: 실제 데이터로 차트 표시
- ✅ 백엔드: API와 정상 연동
- ✅ 사용자: 실제 포트폴리오 성과 확인 가능

### 1.2 무엇을 배울 수 있나요?

이 가이드를 완료하면:
- 백엔드 API와 프론트엔드를 연결하는 방법
- API 응답 데이터를 차트에 표시하는 방법
- 네트워크 요청을 디버깅하는 방법
- 일반적인 통합 문제 해결 방법

### 1.3 준비물

- ✅ 코드 에디터 (VS Code 추천)
- ✅ 터미널 (WSL, Mac Terminal, Windows PowerShell 등)
- ✅ 웹 브라우저 (Chrome 추천)
- ✅ 기본적인 터미널 명령어 지식

---

## 2. 시스템 이해하기

### 2.1 전체 구조 다이어그램

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   사용자 브라우저  │         │  Frontend (Next.js)│         │ Backend (FastAPI)│
│  localhost:9000 │  <───>  │   localhost:9000   │  <───>  │ localhost:8000   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                      │                            │
                                      │                            │
                                      ▼                            ▼
                            ┌──────────────────┐         ┌─────────────────┐
                            │ PortfolioPerfor- │         │ Portfolio       │
                            │ mance Component  │         │ Analytics       │
                            │                  │         │ Service         │
                            │ - 차트 표시       │         │ - 데이터 계산    │
                            │ - 기간 선택       │         │ - 벤치마크       │
                            └──────────────────┘         └─────────────────┘
                                      │                            │
                                      │                            ▼
                                      │                   ┌─────────────────┐
                                      │                   │ Redis Cache     │
                                      │                   │ (5분 TTL)       │
                                      │                   └─────────────────┘
                                      ▼                            │
                            ┌──────────────────┐                  ▼
                            │ usePortfolio     │         ┌─────────────────┐
                            │ History Hook     │         │ Korea Invest    │
                            │                  │         │ API             │
                            │ - API 호출       │         │ (증권사 API)     │
                            │ - 데이터 변환     │         └─────────────────┘
                            └──────────────────┘
```

### 2.2 데이터 흐름 설명

1. **사용자 액션**: 사용자가 포트폴리오 페이지를 열거나 기간(1D, 1W, 1M 등)을 선택합니다.

2. **프론트엔드 처리**:
   - `usePortfolioHistory` 훅이 실행됩니다.
   - `apiClient.getPortfolioHistory(period)` 함수를 호출합니다.
   - `http://localhost:8000/api/portfolio/history?period=1M` 요청을 보냅니다.

3. **백엔드 처리**:
   - FastAPI가 요청을 받습니다.
   - Redis 캐시를 먼저 확인합니다 (있으면 바로 반환).
   - 캐시가 없으면:
     - 한국투자증권 API로 계좌 정보 조회
     - 거래 이력 재구성
     - KOSPI 벤치마크 데이터 가져오기
     - 시계열 데이터 계산
   - 결과를 Redis에 저장 (5분간 유효)
   - JSON 형식으로 응답

4. **프론트엔드 렌더링**:
   - 받은 데이터를 `PortfolioHistoryPoint[]` 형식으로 변환
   - Recharts 라이브러리로 차트 그리기
   - 벤치마크와 포트폴리오 성과를 비교 표시

### 2.3 주요 컴포넌트 설명

#### 프론트엔드 (Next.js)

| 파일 | 역할 |
|------|------|
| `src/components/trading/PortfolioPerformance.tsx` | 포트폴리오 카드 UI 컴포넌트 |
| `src/components/trading/PortfolioPerformanceChart.tsx` | Recharts 차트 컴포넌트 |
| `src/hooks/usePortfolioHistory.ts` | 데이터 가져오기 훅 |
| `src/lib/api-client.ts` | API 통신 클라이언트 |
| `src/lib/types.ts` | TypeScript 타입 정의 |

#### 백엔드 (FastAPI)

| 파일 | 역할 |
|------|------|
| `app/api/portfolio.py` | API 엔드포인트 |
| `app/services/portfolio_analytics_service.py` | 포트폴리오 계산 로직 |
| `app/services/benchmark_service.py` | 벤치마크 데이터 |
| `app/services/snapshot_manager.py` | 스냅샷 관리 |
| `app/core/cache.py` | Redis 캐시 서비스 |

---

## 3. 시작하기 전 준비

### 3.1 필수 프로그램 확인

다음 명령어로 필요한 프로그램이 설치되어 있는지 확인하세요:

```bash
# Node.js 확인 (14.0 이상 필요)
node --version
# 예상 출력: v18.x.x 또는 v20.x.x

# Python 확인 (3.12 필요)
python --version
# 예상 출력: Python 3.12.x

# npm 확인
npm --version
# 예상 출력: 9.x.x 또는 10.x.x
```

**설치되지 않았다면**:
- Node.js: https://nodejs.org/ 에서 다운로드
- Python: https://www.python.org/downloads/ 에서 다운로드

### 3.2 프로젝트 위치 확인

터미널을 열고 프로젝트 루트로 이동합니다:

```bash
# 프로젝트 디렉토리로 이동
cd /home/wide/projects/systrading

# 현재 위치 확인
pwd
# 예상 출력: /home/wide/projects/systrading

# 디렉토리 구조 확인
ls -la
# backend, stock-trading-ui, docs 등이 보여야 함
```

---

## 4. 환경 설정

### 4.1 환경 변수 확인

#### 백엔드 환경 변수

```bash
# .env 파일 확인
cat backend/.env
```

**필수 항목**:
```env
# 한국투자증권 API 키 (실제 값으로 교체)
KOREA_INVEST_APP_KEY=your_app_key_here
KOREA_INVEST_APP_SECRET=your_app_secret_here
KOREA_INVEST_ACCOUNT_NO=your_account_number

# Redis (선택사항, 없으면 캐시 없이 동작)
REDIS_URL=redis://localhost:6379/0
```

**파일이 없다면**:
```bash
# .env.example을 복사하여 생성
cp backend/.env.example backend/.env

# 에디터로 열어서 실제 값 입력
nano backend/.env  # 또는 code backend/.env
```

#### 프론트엔드 환경 변수

```bash
# .env.local 파일 확인
cat stock-trading-ui/.env.local
```

**필수 항목**:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

**파일이 없다면**:
```bash
# 파일 생성
cat > stock-trading-ui/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
EOF
```

### 4.2 의존성 설치

#### 백엔드 의존성

```bash
# 백엔드 디렉토리로 이동
cd backend

# 가상환경이 없으면 생성 (이미 있다면 생략)
python -m venv vkis

# 가상환경 활성화
source vkis/bin/activate  # Linux/Mac/WSL
# 또는
vkis\Scripts\activate     # Windows

# 활성화 확인 (프롬프트 앞에 (vkis) 표시됨)
# (vkis) user@machine:~/systrading/backend$

# 패키지 설치
pip install -r requirements.txt
```

#### 프론트엔드 의존성

```bash
# 프론트엔드 디렉토리로 이동
cd ../stock-trading-ui

# 패키지 설치
npm install

# 설치 확인
ls node_modules | wc -l
# 예상 출력: 1000+ (많은 패키지가 설치됨)
```

---

## 5. 백엔드 실행하기

### 5.1 터미널 1: 백엔드 서버 시작

**새 터미널을 열고** 다음 명령어를 실행합니다:

```bash
# 1. 백엔드 디렉토리로 이동
cd /home/wide/projects/systrading/backend

# 2. 가상환경 활성화 (매우 중요!)
source vkis/bin/activate

# 3. 가상환경 활성화 확인
which python
# 예상 출력: /home/wide/projects/systrading/backend/vkis/bin/python

# 4. 서버 실행
python app/main.py
```

### 5.2 정상 동작 확인

서버가 정상적으로 시작되면 다음과 같은 메시지가 표시됩니다:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**확인 포인트**:
- ✅ `Application startup complete` 메시지 확인
- ✅ `http://0.0.0.0:8000` 포트 확인
- ✅ 에러 메시지 없음

### 5.3 API 테스트하기

**새 터미널을 열고** (백엔드 서버는 계속 실행 중) API를 테스트합니다:

```bash
# Health Check
curl http://localhost:8000/health

# 예상 응답:
# {"status":"ok"}

# Portfolio History API 테스트
curl "http://localhost:8000/api/portfolio/history?period=1M"

# 예상 응답 (예시):
# [
#   {
#     "date": "2025-10-01T15:30:00+09:00",
#     "portfolio": 10000000,
#     "benchmark": 9800000
#   },
#   ...
# ]
```

**응답이 없거나 에러가 발생한다면**:
1. 백엔드 서버 로그 확인
2. `.env` 파일의 API 키 확인
3. 네트워크 연결 확인

### 5.4 브라우저에서 확인

브라우저를 열고 다음 URL로 접속:

```
http://localhost:8000/docs
```

**FastAPI 자동 문서**가 표시됩니다:
- `/api/portfolio/history` 엔드포인트 확인
- "Try it out" 버튼으로 직접 테스트 가능
- 응답 스키마 확인

---

## 6. 프론트엔드 실행하기

### 6.1 터미널 2: 프론트엔드 서버 시작

**새 터미널을 열고** (백엔드는 계속 실행):

```bash
# 1. 프론트엔드 디렉토리로 이동
cd /home/wide/projects/systrading/stock-trading-ui

# 2. 개발 서버 실행
npm run dev

# 또는 포트 9000으로 고정 실행
PORT=9000 npm run dev
```

### 6.2 정상 동작 확인

서버가 시작되면 다음 메시지가 표시됩니다:

```
   ▲ Next.js 15.x.x
   - Local:        http://localhost:9000
   - Network:      http://192.168.x.x:9000

 ✓ Ready in 3.2s
```

**확인 포인트**:
- ✅ `Ready` 메시지 확인
- ✅ `http://localhost:9000` 포트 확인
- ✅ 컴파일 에러 없음

### 6.3 브라우저에서 확인

브라우저를 열고 다음 URL로 접속:

```
http://localhost:9000
```

**포트폴리오 카드**를 찾습니다:
- "Portfolio Performance" 제목
- 시간 범위 버튼 (1D, 1W, 1M 등)
- 차트 영역

---

## 7. 통합 검증하기

### 7.1 Mock 데이터 확인

현재 상태에서 차트 아래에 다음 메시지가 보입니까?

```
⚠️ API 데이터가 준비되지 않아 샘플 데이터를 표시하고 있습니다.
```

**이 메시지가 보인다면**:
- 프론트엔드가 Mock 데이터를 사용 중
- API 연동이 아직 안 됨
- 다음 단계로 진행 필요

**이 메시지가 없다면**:
- 축하합니다! 이미 통합이 완료되었습니다! 🎉
- "8. 문제 해결" 섹션은 건너뛰어도 됩니다.

### 7.2 네트워크 탭으로 API 호출 확인

#### Chrome DevTools 열기

1. **F12** 키를 누르거나 **우클릭 > 검사**
2. **Network** 탭 선택
3. **Fetch/XHR** 필터 선택
4. 페이지 새로고침 (F5)

#### API 요청 확인

`portfolio/history` 요청을 찾아 클릭합니다:

**Headers 탭**:
```
Request URL: http://localhost:8000/api/portfolio/history?period=1M
Request Method: GET
Status Code: 200 OK
```

**Response 탭**:
```json
[
  {
    "date": "2025-10-01T15:30:00+09:00",
    "portfolio": 10000000,
    "benchmark": 9800000
  }
]
```

**Preview 탭**:
- 배열 형태의 데이터 확인
- 각 객체에 `date`, `portfolio`, `benchmark` 필드 있는지 확인

### 7.3 성공 기준 체크리스트

다음 항목을 모두 확인하세요:

- [ ] 백엔드 서버 정상 실행 중 (포트 8000)
- [ ] 프론트엔드 서버 정상 실행 중 (포트 9000)
- [ ] 브라우저에서 차트 표시됨
- [ ] Mock 데이터 경고 메시지 **없음**
- [ ] Network 탭에서 API 요청 200 OK
- [ ] Response 데이터가 배열 형태
- [ ] 기간 변경 시 차트 업데이트됨

**모든 항목이 체크되었다면**: ✅ **통합 완료!** 🎉

---

## 8. 문제 해결

### 8.1 자주 발생하는 오류 TOP 10

#### ❌ 오류 1: "Mock 데이터 경고가 계속 표시됨"

**증상**:
```
⚠️ API 데이터가 준비되지 않아 샘플 데이터를 표시하고 있습니다.
```

**원인**:
- API 호출 실패
- 백엔드 서버 미실행
- CORS 에러
- 응답 데이터 형식 불일치

**해결 방법**:

1. **백엔드 서버 확인**:
   ```bash
   # 백엔드가 실행 중인지 확인
   curl http://localhost:8000/health
   ```

2. **Network 탭 확인**:
   - F12 > Network 탭
   - `portfolio/history` 요청 찾기
   - Status Code 확인 (200이 아니면 문제)

3. **Console 탭 확인**:
   - F12 > Console 탭
   - 빨간색 에러 메시지 확인

4. **CORS 에러라면**:
   ```python
   # backend/app/main.py 확인
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:9000"],  # 이 줄 확인
       ...
   )
   ```

#### ❌ 오류 2: "CORS policy 에러"

**증상** (Console):
```
Access to fetch at 'http://localhost:8000/api/portfolio/history'
from origin 'http://localhost:9000' has been blocked by CORS policy
```

**해결 방법**:

1. **백엔드 설정 확인**:
   ```python
   # backend/app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:9000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **서버 재시작**:
   ```bash
   # 백엔드 터미널에서 Ctrl+C
   # 다시 실행
   python app/main.py
   ```

#### ❌ 오류 3: "Cannot read property of undefined"

**증상** (Console):
```
TypeError: Cannot read property 'date' of undefined
```

**원인**: 응답 데이터 구조가 예상과 다름

**해결 방법**:

1. **API 응답 확인**:
   ```bash
   curl http://localhost:8000/api/portfolio/history?period=1M | jq
   ```

2. **응답이 배열인지 확인**:
   ```json
   [  // ← 배열이어야 함
     { "date": "...", "portfolio": ..., "benchmark": ... }
   ]
   ```

3. **객체로 래핑되어 있다면**:
   ```json
   {
     "data": [...]  // ← 이런 경우
   }
   ```

   `api-client.ts` 수정:
   ```typescript
   const response = await fetch(...);
   const data = await response.json();
   return data.data || data;  // 래핑 처리
   ```

#### ❌ 오류 4: "Failed to fetch"

**증상** (Console):
```
TypeError: Failed to fetch
```

**원인**: 네트워크 연결 문제 또는 서버 미실행

**해결 방법**:

1. **백엔드 서버 실행 확인**:
   ```bash
   # 다른 터미널에서
   ps aux | grep python
   ```

2. **포트 확인**:
   ```bash
   netstat -tuln | grep 8000
   ```

3. **서버 로그 확인**:
   - 백엔드 터미널에서 에러 메시지 확인

#### ❌ 오류 5: "500 Internal Server Error"

**증상** (Network 탭):
```
Status Code: 500 Internal Server Error
```

**원인**: 백엔드 로직 오류

**해결 방법**:

1. **백엔드 로그 확인**:
   - 백엔드 터미널에서 상세 에러 확인
   - Traceback 메시지 읽기

2. **일반적인 원인**:
   - API 키 오류
   - 데이터베이스 연결 실패
   - 로직 버그

3. **API 키 확인**:
   ```bash
   cat backend/.env | grep KOREA_INVEST
   ```

#### ❌ 오류 6: "404 Not Found"

**증상** (Network 탭):
```
Status Code: 404 Not Found
```

**원인**: 엔드포인트 경로 오류

**해결 방법**:

1. **URL 확인**:
   - 요청: `http://localhost:8000/api/portfolio/history`
   - 올바른지 확인

2. **라우터 확인**:
   ```python
   # backend/app/main.py
   app.include_router(portfolio_router, prefix="/api/portfolio")
   ```

3. **FastAPI 문서 확인**:
   ```
   http://localhost:8000/docs
   ```

#### ❌ 오류 7: "차트가 빈 화면"

**증상**: 차트 영역이 비어있음

**원인**: 데이터는 있지만 렌더링 실패

**해결 방법**:

1. **Console 에러 확인**:
   - F12 > Console
   - React 에러 메시지 확인

2. **데이터 형식 확인**:
   ```javascript
   // Console에서 실행
   console.log(chartData);
   ```

3. **필수 필드 확인**:
   - `date` 필드 존재
   - `portfolio` 숫자형
   - `benchmark` 숫자형

#### ❌ 오류 8: "가상환경 활성화 안 됨"

**증상**:
```bash
python app/main.py
# ModuleNotFoundError: No module named 'fastapi'
```

**해결 방법**:

1. **가상환경 활성화 확인**:
   ```bash
   which python
   # /home/wide/projects/systrading/backend/vkis/bin/python 이어야 함
   ```

2. **활성화 안 되어 있다면**:
   ```bash
   source vkis/bin/activate
   ```

3. **프롬프트 확인**:
   ```
   (vkis) user@machine:~/backend$  # (vkis) 표시 확인
   ```

#### ❌ 오류 9: "Redis 연결 오류"

**증상** (백엔드 로그):
```
WARNING: Redis 연결 실패, 캐시 없이 동작합니다.
```

**해결 방법**:

1. **이 경고는 무시해도 됩니다**:
   - Redis 없이도 동작함
   - 단, 응답 속도가 느려질 수 있음

2. **Redis 사용하고 싶다면**:
   ```bash
   # Redis 설치 (Ubuntu/WSL)
   sudo apt-get install redis-server

   # Redis 시작
   sudo service redis-server start

   # 연결 테스트
   redis-cli ping
   # PONG 응답이 오면 정상
   ```

#### ❌ 오류 10: "npm 패키지 설치 실패"

**증상**:
```bash
npm install
# npm ERR! ...
```

**해결 방법**:

1. **node_modules 삭제 후 재설치**:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **npm 캐시 클리어**:
   ```bash
   npm cache clean --force
   npm install
   ```

3. **Node.js 버전 확인**:
   ```bash
   node --version
   # 14.0 이상이어야 함
   ```

### 8.2 로그 확인 방법

#### 백엔드 로그

**터미널 로그**:
- 백엔드가 실행 중인 터미널 확인
- 요청마다 로그 출력됨

**예시**:
```
INFO:     127.0.0.1:xxxxx - "GET /api/portfolio/history?period=1M HTTP/1.1" 200 OK
INFO:     📊 Portfolio History 요청: period=1M
INFO:     ✅ 캐시 사용: portfolio_history:1M
```

**로그 레벨**:
- `INFO`: 정상 동작
- `WARNING`: 경고 (동작은 함)
- `ERROR`: 오류 발생

#### 프론트엔드 로그

**브라우저 Console**:
- F12 > Console 탭
- React, API 에러 확인

**Network 탭**:
- F12 > Network 탭
- 모든 HTTP 요청 확인

### 8.3 디버깅 체크리스트

문제가 발생하면 이 순서대로 확인하세요:

1. [ ] 백엔드 서버 실행 중? (`ps aux | grep python`)
2. [ ] 프론트엔드 서버 실행 중? (`ps aux | grep node`)
3. [ ] 포트 확인? (8000, 9000)
4. [ ] 환경 변수 설정? (`.env` 파일)
5. [ ] API 키 유효? (한국투자증권 앱)
6. [ ] CORS 설정? (`allow_origins`)
7. [ ] Network 탭 확인? (요청/응답)
8. [ ] Console 에러? (F12)
9. [ ] 가상환경 활성화? (`which python`)
10. [ ] 의존성 설치? (`pip list`, `npm list`)

---

## 9. 다음 단계

### 9.1 커스터마이징

통합이 완료되었다면 다음을 시도해보세요:

1. **차트 스타일 변경**:
   ```typescript
   // PortfolioPerformanceChart.tsx
   <Line
     stroke="#3b82f6"  // 색상 변경
     strokeWidth={3}    // 두께 변경
   />
   ```

2. **기간 추가**:
   ```typescript
   // PortfolioPerformance.tsx
   const TIME_RANGES = ['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL', '2Y'];
   ```

3. **추가 지표 표시**:
   - 샤프 비율
   - 최대 낙폭
   - 승률

### 9.2 성능 개선

1. **Redis 캐시 활용**:
   - TTL 조정 (현재 5분)
   - 캐시 워밍업 전략

2. **API 응답 최적화**:
   - 데이터 압축
   - 페이지네이션

3. **프론트엔드 최적화**:
   - React.memo 사용
   - 가상 스크롤링

### 9.3 추가 기능 아이디어

- 📊 포트폴리오 비교 (여러 계좌)
- 📈 수익률 순위표
- 🔔 성과 알림
- 📥 CSV 다운로드
- 📱 모바일 최적화

### 9.4 학습 리소스

- **FastAPI 공식 문서**: https://fastapi.tiangolo.com/
- **Next.js 공식 문서**: https://nextjs.org/docs
- **Recharts 문서**: https://recharts.org/
- **TypeScript 핸드북**: https://www.typescriptlang.org/docs/

---

## 📝 요약

축하합니다! 이 가이드를 완료하셨습니다! 🎉

**배운 내용**:
- ✅ 백엔드 API와 프론트엔드 통합 방법
- ✅ 네트워크 디버깅 기술
- ✅ 일반적인 문제 해결 방법
- ✅ API 테스트 방법

**다음 단계**:
1. 다른 API 엔드포인트 통합해보기
2. 차트 커스터마이징
3. 추가 기능 구현

**질문이나 문제가 있다면**:
- 📚 [FAQ 문서](../troubleshooting/portfolio-integration-faq.md) 참고
- 📖 [API 명세서](../api/portfolio-history-api-spec.md) 참고
- 🚀 [빠른 시작 가이드](./portfolio-quick-start.md) 참고

---

**작성**: 2025-10-11
**버전**: 1.0.0
**최종 수정**: 2025-10-11
