# 주식 자동매매 시스템 프로젝트 구조

## 📁 프로젝트 개요
- **프로젝트명**: 주식 자동매매 시스템
- **아키텍처**: FastAPI Backend + Next.js Frontend
- **정리일**: 2025-09-20

---

## 🏗️ 현재 프로젝트 구조

### 📂 Core 디렉토리

#### `backend/` - FastAPI 백엔드
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── api/                 # API 라우터
│   ├── core/                # 핵심 설정 및 구성
│   ├── models/              # 데이터 모델
│   ├── services/            # 비즈니스 로직 서비스
│   └── websocket/           # WebSocket 핸들러
├── tests/                   # 백엔드 테스트
├── vkis/                    # 가상환경 (Python dependencies)
└── simple_server.py         # 간단한 개발 서버
```

#### `stock-trading-ui/` - Next.js 프론트엔드
```
stock-trading-ui/
├── src/
│   ├── components/          # React 컴포넌트
│   │   ├── common/          # 공통 컴포넌트
│   │   └── ui/              # UI 컴포넌트 (shadcn/ui)
│   ├── app/                 # Next.js App Router
│   └── lib/                 # 유틸리티 라이브러리
├── public/                  # 정적 파일
├── .next/                   # Next.js 빌드 파일
├── node_modules/            # Node.js 의존성
├── package.json
├── components.json          # shadcn/ui 설정
└── README.md
```

### 📂 Legacy 지원 디렉토리 (Backend 의존성)

#### `brokers/` - 브로커 API 인터페이스
```
brokers/
├── __init__.py
├── factory.py               # 브로커 팩토리
├── kore-investment/         # 한국투자증권
├── korea_investment/        # 한국투자증권 (다른 버전)
└── ls_securities/           # LS증권
```

#### `core/` - 핵심 비즈니스 로직
```
core/
├── __init__.py
├── interfaces/              # 인터페이스 정의
├── order_processor.py       # 주문 처리
└── trading_engine.py        # 매매 엔진
```

#### `services/` - 서비스 레이어
```
services/
├── __init__.py
├── account_service.py       # 계좌 서비스
└── trading_service.py       # 매매 서비스
```

#### `utils/` - 유틸리티 함수
```
utils/
├── __init__.py
├── helpers.py               # 헬퍼 함수
└── logger.py                # 로깅 설정
```

#### `data/` - 데이터 저장소
```
data/
└── realtime_watchlist_df.pkl  # 실시간 관심종목 데이터
```

#### `krxinfo/` - 한국거래소 정보
```
krxinfo/
├── kosdaq.py                # 코스닥 종목 정보
└── kospi.py                 # 코스피 종목 정보
```

### 📂 기타 디렉토리

#### `docs/` - 문서
```
docs/
├── project-structure.md     # 프로젝트 구조 문서 (이 파일)
└── execution/               # 실행 기록
```

#### `logs/` - 로그 파일
```
logs/
└── [날짜별 로그 파일들]
```

#### `tests/` - 테스트
```
tests/
└── [테스트 파일들]
```

#### `token_backup/` - 토큰 백업
```
token_backup/
└── [토큰 백업 파일들]
```

#### `PRD/` - 운영 관련
```
PRD/
└── [운영 관련 파일들]
```

### 📂 루트 파일들
```
├── .env                     # 환경 변수
├── .gitignore              # Git 무시 파일
├── .mcp.json               # MCP 설정
├── CLAUDE.md               # Claude 작업 지침
├── frontend-control.bat    # 프론트엔드 제어 스크립트
├── gemini.md               # Gemini 관련 문서
├── package.json            # Node.js 프로젝트 설정
├── package-lock.json       # Node.js 의존성 잠금
└── requirements.txt        # Python 의존성
```

---

## 🗂️ Backup 디렉토리

Legacy 파일들이 정리되어 backup 폴더로 이동되었습니다:

#### `backup/legacy-qt/` - Qt UI 관련 Legacy 파일
```
backup/legacy-qt/
├── qt-ui/                   # Qt 기반 UI 파일들
│   ├── debug_connection.py
│   ├── domestic_websocket.py
│   ├── rsimacd_trading.py   # 이전 Qt 기반 매매 시스템
│   ├── kismain.ui           # Qt UI 파일
│   └── [기타 Qt 관련 파일들]
└── legacy/                  # 이전 버전 파일들
    ├── kis_stock.py
    ├── rsimacd_trading.py
    └── utils.py
```

#### `backup/misc/` - 기타 Legacy 파일
```
backup/misc/
├── 주식현재가_시세.csv      # 이전 시세 데이터
├── capture1.png            # 스크린샷
├── access.tok              # 이전 액세스 토큰
└── config.yaml             # 이전 설정 파일
```

---

## 🔄 아키텍처 플로우

### 데이터 흐름
```
한국투자증권 API ↔ Backend (FastAPI) ↔ Frontend (Next.js)
                     ↕
            Legacy Services & Utils
```

### 주요 컴포넌트 관계
1. **Frontend** → API 호출 → **Backend**
2. **Backend** → 브로커 API 호출 → **brokers/**
3. **Backend** → 비즈니스 로직 → **core/, services/**
4. **Backend** → 데이터 저장 → **data/**
5. **Backend** → 로깅 → **logs/**

---

## 📋 정리 결과

### ✅ 완료된 작업
- Qt 기반 UI 파일들을 backup으로 이동
- Legacy Python 파일들을 backup으로 이동
- 기타 불필요한 파일들을 backup으로 이동
- 프로젝트 구조 문서 작성

### 🔄 현재 상태
- **Backend**: FastAPI 기반으로 정상 동작
- **Frontend**: Next.js 기반으로 정상 동작
- **Legacy 지원**: 기존 brokers, core, services 등은 backend 의존성으로 유지

### 📝 추후 작업 고려사항
1. Legacy 폴더들 (brokers, core, services, utils 등)의 backend 의존성 재검토
2. 필요 시 legacy 코드를 backend/app으로 통합
3. 불필요한 의존성 제거 및 코드 정리

---

## 🚀 실행 방법

### Backend 실행
```bash
cd backend
python app/main.py
```

### Frontend 실행
```bash
cd stock-trading-ui
npm run dev
```

### 통합 실행
```bash
# 루트 디렉토리에서
./frontend-control.bat
```

---

**마지막 업데이트**: 2025-09-20
**작성자**: Claude Code Assistant