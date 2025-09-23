# 주식 자동매매 시스템

## 📁 프로젝트 개요
- **프로젝트명**: 주식 자동매매 시스템
- **아키텍처**: FastAPI Backend + Next.js Frontend
- **주요 기술**: RSI/MACD 기반 자동매매, 한국투자증권 API 연동
- **정리일**: 2025-09-20

---

## 🏗️ 프로젝트 구조

```
systrading/
├── backend/              # FastAPI 백엔드
│   └── CLAUDE.md        # 백엔드 개발 가이드
├── stock-trading-ui/     # Next.js 프론트엔드
│   └── CLAUDE.md        # 프론트엔드 개발 가이드
├── docs/                 # 프로젝트 문서
│   └── project-structure.md
├── backup/               # Legacy 파일들
└── [지원 폴더들]
```

### 하위 모듈 참조
- **Frontend 개발**: `stock-trading-ui/CLAUDE.md` 참조
- **Backend 개발**: `backend/CLAUDE.md` 참조
- **전체 구조**: `docs/project-structure.md` 참조

---

## 🔄 실행 방법

### Backend 시작
```bash
cd backend
source vkis/bin/activate  # 가상환경 활성화
python app/main.py        # FastAPI 서버 (포트 8000)
```

### Frontend 시작
```bash
cd stock-trading-ui
npm run dev              # Next.js 개발 서버 (포트 3000)
```

### 통합 실행
```bash
./frontend-control.bat   # Windows 환경
```

---

## 📊 핵심 데이터 구조

### realtime_watchlist_df 컬럼
```python
columns = [
    '현재가',           # 실시간 가격
    '수익률',           # 계산된 수익률 (%)
    '평균단가',         # API에서 받은 매입단가
    '보유수량',         # 보유 주식 수량
    'MACD',            # MACD 지표
    'MACD시그널',      # MACD 시그널
    'RSI',             # RSI 지표
    '트레일링스탑발동여부',
    '트레일링스탑발동후고가'
]
```

### account_info_df 컬럼 (API에서 받아옴)
```python
columns = [
    '종목코드', '종목명', '보유수량', '매도가능수량',
    '매입단가', '수익률', '현재가', '전일대비', '등락'
]
```

---

## 🔧 환경 설정

### Backend 환경 변수 (.env)
```bash
KOREA_INVEST_API_KEY=your_api_key
KOREA_INVEST_SECRET_KEY=your_secret_key
```

### Frontend 환경 변수 (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## 🤖 Claude Code Agent 활용 가이드

### 프로젝트별 전문 Agent 목록

#### **Frontend 개발**
- **`frontend-developer`**: React 컴포넌트, 반응형 레이아웃, 상태 관리
- **`ui-ux-designer`**: 인터페이스 디자인, 와이어프레임, 디자인 시스템
- **`ui-visual-validator`**: UI 수정 후 시각적 검증, 스크린샷 분석
- **`typescript-pro`**: 고급 타입 시스템, 제네릭, 타입 안전성

#### **Backend 개발**
- **`backend-architect`**: RESTful API, 마이크로서비스, 데이터베이스 스키마
- **`python-pro`**: FastAPI 최적화, 비동기 프로그래밍, 디자인 패턴
- **`database-admin`**: 데이터베이스 운영, 백업, 복제, 모니터링

#### **Trading 시스템 전문**
- **`trading-engine-specialist`**: 자동매매 엔진, 주문 실행, 실시간 트레이딩
- **`quantitative-analyst`**: RSI/MACD 최적화, 백테스팅, 매매 전략
- **`market-data-engineer`**: 시장 데이터 수집, API 연동, 실시간 데이터 처리
- **`risk-manager`**: 리스크 관리, 포지션 관리, 손실 제한
- **`performance-monitor`**: 매매 성과 분석, 모니터링, 리포팅
- **`korean-stock-api-debugger`**: 한국투자증권 API 연동 및 디버깅

#### **개발 지원**
- **`debugger`**: 에러 디버깅, 테스트 실패, 예상치 못한 동작
- **`context-manager`**: 복잡한 멀티 에이전트 워크플로우, 대규모 프로젝트

### Agent 활용 패턴

#### **1. 단일 작업 위임**
```bash
# ❌ 직접 처리
여러 파일 읽고 → 분석 → 수정 → 테스트

# ✅ Agent 활용
Task: frontend-developer
"TradingConditions 컴포넌트를 다크 테마로 업데이트"
```

#### **2. 복합 작업 분할**
```bash
# 대규모 UI 리팩토링
1. Task: ui-ux-designer → 디자인 시스템 분석
2. Task: frontend-developer → 컴포넌트 구현
3. Task: ui-visual-validator → 결과 검증
```

#### **3. 도메인별 전문가 활용**
```bash
# 매매 로직 개선
1. Task: quantitative-analyst → RSI 전략 최적화
2. Task: trading-engine-specialist → 실행 엔진 구현
3. Task: risk-manager → 리스크 검증
4. Task: performance-monitor → 성과 측정
```

#### **4. 문제 해결 워크플로우**
```bash
# API 연동 문제 발생 시
1. Task: korean-stock-api-debugger → 문제 진단
2. Task: backend-architect → 아키텍처 개선
3. Task: debugger → 최종 검증
```

### Agent 사용 시기

#### **⚡ 즉시 Agent 사용**
- 3개 이상 파일 수정이 필요한 작업
- 도메인 전문 지식이 필요한 작업 (매매 로직, API 연동)
- 복잡한 UI/UX 작업
- 성능 최적화 작업
- 에러 디버깅

#### **📝 직접 처리**
- 단순 텍스트 수정
- 1-2줄 코드 변경
- 파일 읽기/검색
- 문서 작성

### 효율적 Agent 활용 팁

#### **1. 구체적인 Task 작성**
```bash
# ❌ 모호한 요청
"UI를 개선해줘"

# ✅ 구체적 요청
"TradingConditions 사이드바의 모든 Input과 Select 컴포넌트를
다크 테마(bg-gray-800, border-gray-600)로 업데이트하고,
호버/포커스 상태도 일관되게 적용해줘"
```

#### **2. 병렬 Agent 실행**
```bash
# 동시에 여러 Agent 실행으로 시간 단축
Task: frontend-developer + Task: backend-architect
```

#### **3. 컨텍스트 효율성**
- Agent에게 위임하면 토큰 사용량 50-75% 절약
- 복잡한 작업일수록 더 큰 절약 효과

## 🚫 Over-Engineering 방지 원칙

### 전체 프로젝트 규칙
1. **Agent 우선 활용**: 복잡한 작업은 전문 Agent에게 위임
2. **단순함 우선**: 가장 간단한 해결책부터 시작
3. **점진적 개선**: 동작하는 코드 먼저, 최적화는 나중에
4. **표준 패턴 사용**: 각 프레임워크의 Best Practice 준수
5. **최소 의존성**: 꼭 필요한 라이브러리만 설치
6. **문서화 우선**: 복잡한 코드보다 명확한 문서



## 🔄 작업 진행 기록 규칙

### 실행 기록 관리
모든 주요 작업 완료 후 `docs/execution/` 디렉토리에 진행 내역을 기록합니다.

#### 파일명 규칙
```
docs/execution/impl[날짜][시간].md
```

**예시**:
- `impl0910_2218.md` - 2025년 9월 10일 22시 18분 작업
- `impl0911_1430.md` - 2025년 9월 11일 14시 30분 작업

#### 기록 대상 작업
1. **시스템 설정 변경**: 서버 설정, 환경 변수, 설정 파일 수정
2. **API 연동**: 새로운 API 엔드포인트 추가, 기존 API 수정
3. **버그 수정**: 코드 오류 수정, 로직 개선
4. **기능 추가**: 새로운 기능 구현, 모듈 추가
5. **인프라 작업**: 배포, 서버 설정, 데이터베이스 변경
6. **문제 해결**: 오류 진단 및 해결 과정

#### 기록 템플릿
```markdown
# 실행 기록 - [날짜] [시간]

## 작업 개요

#### 자동 기록 트리거
매 작업 완료 시 Claude가 자동으로 해당 형식으로 기록을 생성하여 `docs/execution/` 디렉토리에 저장합니다.

### 최근 작업 기록
- `exec0910_01.md`: CORS 문제 해결 및 실제 API 데이터 연동 (2025-09-10 22:18)