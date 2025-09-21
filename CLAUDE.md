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

## 🚫 Over-Engineering 방지 원칙

### 전체 프로젝트 규칙
1. **단순함 우선**: 가장 간단한 해결책부터 시작
2. **점진적 개선**: 동작하는 코드 먼저, 최적화는 나중에
3. **표준 패턴 사용**: 각 프레임워크의 Best Practice 준수
4. **최소 의존성**: 꼭 필요한 라이브러리만 설치
5. **문서화 우선**: 복잡한 코드보다 명확한 문서



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