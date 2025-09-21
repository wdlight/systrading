# 주식 매매 시스템 UI 아키텍처 문서

## 프로젝트 개요
- **프로젝트명**: stock-trading-ui
- **기술 스택**: Next.js 15.5.2 + React 19 + TypeScript + Tailwind CSS 4 + shadcn/ui
- **아키텍처**: App Router (Next.js 13+ 스타일)
- **목적**: 한국 주식 매매 시스템의 웹 기반 인터페이스 구현

---

## 프로젝트 구조

```
stock-trading-ui/
├── src/
│   ├── app/                    # App Router 디렉토리
│   │   ├── layout.tsx         # 루트 레이아웃 컴포넌트
│   │   ├── page.tsx           # 메인 페이지 (주식 매매 대시보드)
│   │   └── globals.css        # 글로벌 CSS 스타일
│   ├── components/
│   │   └── ui/                # shadcn/ui 컴포넌트들
│   │       ├── button.tsx     # 버튼 컴포넌트
│   │       ├── card.tsx       # 카드 컴포넌트
│   │       ├── input.tsx      # 입력 필드 컴포넌트
│   │       ├── label.tsx      # 레이블 컴포넌트
│   │       ├── select.tsx     # 셀렉트 드롭다운 컴포넌트
│   │       ├── separator.tsx  # 구분선 컴포넌트
│   │       └── table.tsx      # 테이블 컴포넌트
│   └── lib/
│       └── utils.ts           # 유틸리티 함수들 (cn 클래스명 병합)
├── components.json            # shadcn/ui 설정 파일
├── next.config.ts             # Next.js 설정
├── package.json              # 프로젝트 의존성 및 스크립트
├── tsconfig.json             # TypeScript 설정
└── tailwind.config.ts        # Tailwind CSS 설정
```

---

## 핵심 파일별 역할

### 1. 설정 파일들

#### `package.json`
- **역할**: 프로젝트 메타데이터, 의존성 관리, 스크립트 정의
- **주요 의존성**:
  - `next`: 15.5.2 - React 프레임워크
  - `react`: 19.1.0 - UI 라이브러리
  - `typescript`: ^5 - 타입 시스템
  - `tailwindcss`: ^4 - 유틸리티 CSS 프레임워크
  - `@radix-ui/*`: Radix UI 컴포넌트들 (shadcn/ui 기반)

#### `components.json`
- **역할**: shadcn/ui CLI 설정 파일
- **설정 내용**:
  - `style`: "new-york" - UI 컴포넌트 스타일 테마
  - `baseColor`: "neutral" - 기본 색상 팔레트
  - `aliases`: 파일 경로 단축키 설정 (@/components, @/lib 등)

#### `tsconfig.json`
- **역할**: TypeScript 컴파일러 설정
- **주요 설정**: 경로 별칭(@/* -> src/*), 스트릭트 모드, 모듈 해석 옵션

### 2. 레이아웃 및 페이지

#### `src/app/layout.tsx`
- **역할**: 루트 레이아웃 컴포넌트
- **기능**:
  - HTML 기본 구조 정의
  - 글로벌 폰트 설정 (Geist, Geist_Mono)
  - 메타데이터 설정
  - 모든 페이지에 공통으로 적용되는 레이아웃

#### `src/app/page.tsx`
- **역할**: 메인 대시보드 페이지
- **구현 내용**:
  - **헤더**: "한국투자증권 시스템트레이딩" 타이틀
  - **좌측 사이드바**: 매수/매도 조건 설정 UI
    - 매수 금액 입력
    - MACD Signal Line 조건
    - RSI 조건 설정 (상향돌파/하향돌파/UP/DOWN 옵션)
  - **메인 영역**: 계좌 정보 및 보유 종목 테이블
  - **하단 영역**: Watch List 테이블

### 3. UI 컴포넌트들 (shadcn/ui 기반)

#### `src/components/ui/card.tsx`
- **역할**: 카드 레이아웃 컴포넌트
- **사용처**: 매수/매도 조건 섹션, 계좌 정보 섹션, Watch List 섹션

#### `src/components/ui/table.tsx`
- **역할**: 테이블 컴포넌트
- **사용처**: 계좌 정보 테이블, Watch List 테이블
- **구성 요소**: Table, TableHeader, TableBody, TableRow, TableHead, TableCell

#### `src/components/ui/select.tsx`
- **역할**: 드롭다운 선택 컴포넌트
- **사용처**: MACD/RSI 조건 선택 (상향돌파/하향돌파/UP/DOWN)

#### `src/components/ui/input.tsx`
- **역할**: 텍스트 입력 필드
- **사용처**: 매수 금액 입력, RSI 수치 입력

#### `src/components/ui/label.tsx`
- **역할**: 폼 레이블 컴포넌트
- **사용처**: 입력 필드들의 라벨

#### `src/components/ui/button.tsx`
- **역할**: 버튼 컴포넌트 (현재 미사용, 향후 확장용)

#### `src/components/ui/separator.tsx`
- **역할**: 구분선 컴포넌트 (현재 미사용, 향후 확장용)

### 4. 유틸리티

#### `src/lib/utils.ts`
- **역할**: 공통 유틸리티 함수
- **주요 함수**: `cn()` - Tailwind CSS 클래스명 조건부 병합

---

## 기술적 특징

### 1. Next.js App Router
- **장점**: 파일 시스템 기반 라우팅, 서버 컴포넌트 지원
- **구조**: `app/` 디렉토리 내 파일들이 자동으로 라우트가 됨

### 2. shadcn/ui 컴포넌트 시스템
- **특징**: Radix UI + Tailwind CSS 기반의 재사용 가능한 컴포넌트
- **장점**: 접근성 준수, 커스터마이징 용이, 일관된 디자인 시스템

### 3. TypeScript
- **타입 안정성**: 컴파일 시점 오류 검출
- **개발 효율성**: IDE 자동완성 및 리팩토링 지원

### 4. Tailwind CSS
- **유틸리티 기반**: 빠른 스타일링 및 일관된 디자인
- **반응형**: 모바일-퍼스트 반응형 디자인 지원

---

## 개발 환경

### 스크립트
- `npm run dev`: 개발 서버 실행 (http://localhost:3000)
- `npm run build`: 프로덕션 빌드
- `npm run start`: 프로덕션 서버 실행
- `npm run lint`: ESLint를 통한 코드 검사

### 개발 서버 특징
- **Hot Reload**: 코드 변경 시 자동 리로드
- **Turbopack**: 빠른 번들링 (Next.js 13+ 실험적 기능)
- **TypeScript 지원**: 실시간 타입 검사

---

## UI 레이아웃 구성

### 메인 대시보드 레이아웃
```
┌─────────────────────────────────────────────────────────────────┐
│ 한국투자증권 시스템트레이딩                                        │
├─────────────┬───────────────────────────────────────────────────┤
│   매수 조건   │                                                 │
│  ┌─────────┐ │              계좌 정보                            │
│  │매수 금액 │ │   ┌─────────────────────────────────────────┐     │
│  └─────────┘ │   │ 현재 평가 금액: 101,922원                │     │
│  ┌─────────┐ │   │ 종목코드│종목명│보유수량│...              │     │
│  │MACD기   │ │   │ 005360 │모나미│  1   │...              │     │
│  └─────────┘ │   └─────────────────────────────────────────┘     │
│  ┌─────────┐ │                                                 │
│  │RSI 간이  │ ├─────────────────────────────────────────────────┤
│  └─────────┘ │                                                 │
│             │              Watch List                         │
│   매도 조건   │   ┌─────────────────────────────────────────┐     │
│  ┌─────────┐ │   │ 현재가│수익률│평균단가│MACD│RSI│...       │     │
│  │MACD기   │ │   │   -  │  -  │   -   │ -  │- │...       │     │
│  └─────────┘ │   └─────────────────────────────────────────┘     │
│  ┌─────────┐ │                                                 │
│  │RSI 간이  │ │                                                 │
│  └─────────┘ │                                                 │
└─────────────┴───────────────────────────────────────────────────┘
```

### 컴포넌트 계층 구조
```
App (layout.tsx)
└── Home Page (page.tsx)
    ├── Title Bar
    ├── Left Sidebar
    │   ├── Buy Conditions (Card)
    │   │   ├── Amount Input
    │   │   ├── MACD Select
    │   │   └── RSI Input + Select
    │   └── Sell Conditions (Card)
    │       ├── MACD Select
    │       └── RSI Input + Select
    └── Main Content
        ├── Account Info (Card + Table)
        └── Watch List (Card + Table)
```

---

## 확장 계획

### 1. 추가 예정 기능
- 실시간 주식 데이터 연동
- WebSocket을 통한 실시간 업데이트
- 차트 컴포넌트 (MACD, RSI 시각화)
- 알림 시스템
- 설정 관리 페이지

### 2. 추가 예정 컴포넌트
- Chart 컴포넌트 (Chart.js 또는 Recharts)
- Modal/Dialog 컴포넌트
- Alert/Notification 컴포넌트
- Loading/Spinner 컴포넌트
- Form validation 컴포넌트

### 3. 상태 관리
- 향후 Zustand 또는 Redux Toolkit 도입 예정
- 실시간 데이터 상태 관리
- 사용자 설정 상태 관리

---

## 주요 의존성 버전

| 패키지 | 버전 | 역할 |
|--------|------|------|
| next | 15.5.2 | React 프레임워크 |
| react | 19.1.0 | UI 라이브러리 |
| typescript | ^5 | 타입 시스템 |
| tailwindcss | ^4 | CSS 프레임워크 |
| @radix-ui/* | 다양 | UI 컴포넌트 기반 |
| lucide-react | ^0.542.0 | 아이콘 라이브러리 |

---

## 성능 최적화

### 1. 현재 적용된 최적화
- **Server Components**: 기본적으로 서버 컴포넌트 사용
- **Font Optimization**: next/font를 통한 폰트 최적화
- **CSS-in-JS 없음**: Tailwind CSS로 번들 크기 최소화

### 2. 향후 적용 예정
- **Code Splitting**: 페이지별 코드 분할
- **Image Optimization**: next/image 활용
- **Bundle Analyzer**: 번들 크기 분석 및 최적화
- **Memoization**: React.memo, useMemo 활용

---

## 배포 고려사항

### 1. 빌드 최적화
- Static Generation 활용 가능
- API Routes를 통한 백엔드 통합
- 환경변수를 통한 설정 관리

### 2. 보안
- CSP (Content Security Policy) 설정
- 환경변수를 통한 민감정보 관리
- API 키 보호

---

## 개발 현황

### 완성된 기능
- ✅ 기본 프로젝트 구조 설정
- ✅ shadcn/ui 컴포넌트 시스템 구축
- ✅ 메인 대시보드 레이아웃 구현
- ✅ 매수/매도 조건 설정 UI
- ✅ 계좌 정보 테이블
- ✅ Watch List 테이블 구조

### 진행 중/예정 작업
- 🔄 실시간 데이터 연동
- 🔄 백엔드 API 연결
- 🔄 차트 시각화 컴포넌트
- 🔄 알림 및 상태 관리 시스템

---

이 아키텍처는 확장 가능하고 유지보수가 용이한 구조로 설계되었으며, 향후 실제 주식 매매 기능 구현 시 쉽게 확장할 수 있는 기반을 제공합니다.