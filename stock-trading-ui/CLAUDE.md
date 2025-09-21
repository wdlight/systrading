# Frontend - Next.js 주식 매매 시스템

## 📁 프로젝트 개요
- **프레임워크**: Next.js 15 (App Router)
- **UI**: shadcn/ui + Tailwind CSS
- **언어**: TypeScript

---

## 🏗️ 핵심 구조

```
src/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # 루트 레이아웃
│   ├── page.tsx           # 홈페이지
│   └── globals.css        # 전역 스타일
├── components/             # React 컴포넌트
│   ├── common/            # 공통 컴포넌트
│   └── ui/                # shadcn/ui 컴포넌트
├── lib/                   # 유틸리티
└── types/                 # TypeScript 타입 정의
```

---

## 🔧 개발 명령어

```bash
npm run dev     # 개발 서버 (localhost:3000)
npm run build   # 프로덕션 빌드
npm run lint    # ESLint 검사
npm run type-check  # TypeScript 타입 검사
```

---

## 📡 API 연동

### Backend 연결
```typescript
// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'

// 환경변수 설정 (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### 핵심 데이터 타입
```typescript
// types/trading.ts
export interface WatchlistItem {
  종목코드: string
  종목명: string
  현재가: number
  수익률: number
  평균단가: number
  보유수량: number
  MACD: number
  RSI: number
}

export interface AccountInfo {
  종목코드: string
  종목명: string
  보유수량: number
  매입단가: number
  수익률: number
  현재가: number
}
```

---

## 🎨 UI 컴포넌트

### shadcn/ui 기본 설정
```bash
# 필요한 컴포넌트만 설치
npx shadcn@latest add button card table input
```

### 컴포넌트 작성 패턴
```typescript
// components/common/StockTable.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface StockTableProps {
  stocks: WatchlistItem[]
  onSelect?: (code: string) => void
}

export function StockTable({ stocks, onSelect }: StockTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>보유 종목</CardTitle>
      </CardHeader>
      <CardContent>
        {/* 테이블 내용 */}
      </CardContent>
    </Card>
  )
}
```

---

## ⚡ Next.js Best Practices

### 1. **서버/클라이언트 컴포넌트 구분**
```typescript
// 서버 컴포넌트 (기본값) - 데이터 fetching
export default async function StockPage() {
  const data = await fetch('/api/stocks')
  return <StockList data={data} />
}

// 클라이언트 컴포넌트 - 상호작용 필요시만
'use client'
export function InteractiveChart() {
  const [data, setData] = useState()
  // 상태 관리, 이벤트 핸들러
}
```

### 2. **데이터 페칭 패턴**
```typescript
// app/stocks/page.tsx - 서버에서 초기 데이터
export default async function StocksPage() {
  const initialData = await getStockData()
  return <StockDashboard initialData={initialData} />
}

// 클라이언트에서 실시간 업데이트
'use client'
export function StockDashboard({ initialData }) {
  const [stocks, setStocks] = useState(initialData)

  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    ws.onmessage = (event) => {
      setStocks(JSON.parse(event.data))
    }
    return () => ws.close()
  }, [])
}
```

### 3. **라우팅 구조**
```
app/
├── page.tsx              # / (홈)
├── stocks/
│   ├── page.tsx         # /stocks (종목 목록)
│   └── [code]/
│       └── page.tsx     # /stocks/005930 (개별 종목)
└── trading/
    ├── page.tsx         # /trading (매매 화면)
    └── history/
        └── page.tsx     # /trading/history
```

### 4. **성능 최적화**
- **이미지**: `next/image` 사용
- **폰트**: `next/font` 사용
- **번들 크기**: 필요한 라이브러리만 import
- **코드 분할**: 동적 import로 lazy loading

---

## 🚫 Over-Engineering 방지 규칙

### ❌ 피해야 할 것들
1. **과도한 추상화**: 간단한 컴포넌트를 복잡하게 만들지 말 것
2. **불필요한 상태 관리**: Redux/Zustand 등은 정말 필요할 때만
3. **과도한 폴더 구조**: 파일이 적으면 단순하게 유지
4. **조기 최적화**: 성능 문제가 실제로 발생할 때 최적화
5. **복잡한 훅**: useCallback, useMemo 남용 금지

### ✅ 권장 사항
1. **단순함 우선**: 가장 간단한 해결책부터 시작
2. **점진적 개선**: 필요에 따라 단계적으로 복잡성 추가
3. **표준 패턴 사용**: Next.js 공식 패턴 우선 적용
4. **최소 의존성**: 꼭 필요한 라이브러리만 설치

---

## 🔍 개발 워크플로우

### 1. **새 기능 개발**
```bash
# 1. 브랜치 생성
git checkout -b feature/stock-chart

# 2. 컴포넌트 작성 (가장 단순한 형태부터)
# 3. 타입 추가
# 4. 테스트 (수동 확인)
# 5. 린트 검사
npm run lint

# 6. 커밋
git commit -m "feat: 주식 차트 컴포넌트 추가"
```

### 2. **컴포넌트 작성 순서**
1. 기본 JSX 구조 작성
2. Props 타입 정의
3. 스타일링 (Tailwind)
4. 상태 관리 (필요시)
5. 이벤트 핸들러 추가

### 3. **파일 명명 규칙**
- 컴포넌트: `PascalCase.tsx`
- 페이지: `page.tsx` (App Router)
- 훅: `use*.ts`
- 유틸리티: `camelCase.ts`
- 타입: `*.types.ts`

---

## 🐛 일반적인 문제 해결

### Hydration Mismatch
```typescript
const [isMounted, setIsMounted] = useState(false)
useEffect(() => setIsMounted(true), [])
if (!isMounted) return null
```

### WebSocket 연결 관리
```typescript
useEffect(() => {
  const ws = new WebSocket(WS_URL)
  return () => ws.close() // 정리 함수 필수
}, [])
```

### 환경 변수 타입 안전성
```typescript
// lib/env.ts
export const env = {
  API_URL: process.env.NEXT_PUBLIC_API_URL!,
  WS_URL: process.env.NEXT_PUBLIC_WS_URL!,
} as const
```

---

## 📋 체크리스트

### 개발 전
- [ ] 요구사항 명확히 정의
- [ ] 가장 단순한 구현 방법 선택
- [ ] 필요한 라이브러리만 설치

### 개발 중
- [ ] 컴포넌트는 단일 책임 원칙 준수
- [ ] 타입 정의 완료
- [ ] 에러 핸들링 구현

### 개발 후
- [ ] 린트 에러 없음
- [ ] 타입 에러 없음
- [ ] 기본 기능 동작 확인

---

**핵심 원칙**: 간단하게 시작하고, 필요에 따라 개선하기