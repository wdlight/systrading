# 주식 자동매매 시스템 UI/UX 상세 설계 문서
**버전**: 1.0
**작성일**: 2025-09-24
**대상**: Frontend Developer

---

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [현재 상황 분석](#현재-상황-분석)
3. [설계 목표](#설계-목표)
4. [전체 아키텍처](#전체-아키텍처)
5. [컴포넌트 상세 설계](#컴포넌트-상세-설계)
6. [TypeScript 인터페이스](#typescript-인터페이스)
7. [스타일링 가이드](#스타일링-가이드)
8. [구현 순서](#구현-순서)
9. [파일 구조](#파일-구조)
10. [테스트 가이드](#테스트-가이드)

---

## 🎯 프로젝트 개요

### 목적
기존 주식 자동매매 시스템의 UI/UX를 개선하여 사용자 경험을 향상시키고, 복잡한 매매 기능을 직관적으로 사용할 수 있도록 재설계

### 기술 스택
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **State Management**: React Hooks (필요시 Zustand 고려)

---

## 🔍 현재 상황 분석

### 기존 구조의 문제점
1. **사이드바 과부하**: TradingConditions 컴포넌트에 너무 많은 기능 집중
2. **정보 계층구조 혼재**: 모니터링과 설정이 같은 영역에 배치
3. **액션 플로우 불명확**: 매매 실행 경로가 직관적이지 않음
4. **공간 활용 비효율**: 화면 우측 공간 활용도 낮음

### 개선 방향
- **기능 분리**: 모니터링 vs 매매 실행 vs 설정
- **정보 우선순위**: P0(핵심) → P1(중요) → P2(보조)
- **사용자 워크플로우 최적화**: 직관적인 매매 경로 제공

---

## 🎯 설계 목표

### 1. 사용성 개선
- 복잡한 기능을 단계적으로 노출
- 핵심 정보의 빠른 접근성 보장
- 매매 실행 플로우 단순화

### 2. 정보 아키텍처 최적화
- 실시간 모니터링 우선 배치
- 매매 액션을 별도 영역으로 분리
- 설정 기능의 독립적 접근

### 3. 반응형 디자인
- 데스크톱 우선 (트레이딩 특성상)
- 태블릿 호환성 유지
- 모바일 핵심 기능 접근

---

## 🏗️ 전체 아키텍처

### 레이아웃 구조
```
┌─────────────────────────────────────────────────────────┐
│                    Header (64px)                        │
├─────────────────────────────────────┬───────────────────┤
│                                     │                   │
│            Main Dashboard           │   Quick Action    │
│               (flex-1)              │   Panel (320px)   │
│                                     │                   │
│  ┌─────────────────────────────────┐│  ┌─────────────┐  │
│  │     Portfolio Summary           ││  │   Watch     │  │
│  └─────────────────────────────────┘│  │   Trade     │  │
│  ┌─────────────────────────────────┐│  │   Alerts    │  │
│  │        Watchlist Panel         ││  └─────────────┘  │
│  └─────────────────────────────────┘│                   │
│  ┌─────────────────────────────────┐│                   │
│  │      Recent Trades Panel       ││                   │
│  └─────────────────────────────────┘│                   │
├─────────────────────────────────────┴───────────────────┤
│              Development Status (dev only)              │
└─────────────────────────────────────────────────────────┘
```

### 페이지 구조
```
/                    → Main Dashboard
/trading             → Trading Interface (별도 페이지)
/trading/conditions  → Auto Trading Setup
/trading/backtest    → Backtest Results
/analytics          → Market Analytics
```

---

## 🧩 컴포넌트 상세 설계

### 1. QuickActionPanel 컴포넌트

**위치**: `src/components/layout/QuickActionPanel.tsx`

```typescript
interface QuickActionPanelProps {
  className?: string;
}

export function QuickActionPanel({ className }: QuickActionPanelProps) {
  const [activeTab, setActiveTab] = useState<'watch' | 'trade' | 'alerts'>('watch');

  return (
    <div className={cn('quick-panel', className)}>
      {/* 탭 네비게이션 */}
      <div className="tab-nav">
        <TabButton
          active={activeTab === 'watch'}
          onClick={() => setActiveTab('watch')}
          icon={Eye}
          label="감시"
        />
        <TabButton
          active={activeTab === 'trade'}
          onClick={() => setActiveTab('trade')}
          icon={Target}
          label="매매"
        />
        <TabButton
          active={activeTab === 'alerts'}
          onClick={() => setActiveTab('alerts')}
          icon={Bell}
          label="알림"
        />
      </div>

      {/* 탭 콘텐츠 */}
      <div className="flex-1 p-4 overflow-y-auto">
        {activeTab === 'watch' && <WatchlistQuick />}
        {activeTab === 'trade' && <TradingQuick />}
        {activeTab === 'alerts' && <AlertsPanel />}
      </div>
    </div>
  );
}
```

**스타일링**:
```css
.quick-panel {
  @apply w-80 bg-[#1a1a1b] border-l border-gray-700 h-full flex flex-col;
}

.tab-nav {
  @apply flex border-b border-gray-700;
}

.tab-button {
  @apply flex-1 flex items-center justify-center gap-2 p-3 text-sm font-medium transition-colors;
}

.tab-button-active {
  @apply text-blue-400 bg-blue-500/10 border-b-2 border-blue-400;
}

.tab-button-inactive {
  @apply text-gray-400 hover:text-gray-300 hover:bg-gray-800/50;
}
```

### 2. TradingQuick 컴포넌트

**위치**: `src/components/trading/TradingQuick.tsx`

```typescript
interface TradingQuickProps {
  selectedStock?: string;
}

export function TradingQuick({ selectedStock }: TradingQuickProps) {
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [quantity, setQuantity] = useState<number>(0);
  const [price, setPrice] = useState<number>(0);

  return (
    <div className="space-y-4">
      {/* 종목 선택 */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          종목 선택
        </label>
        <StockSearchInput
          value={selectedStock}
          onChange={setSelectedStock}
          placeholder="종목명 또는 코드 검색"
        />
      </div>

      {/* 주문 유형 */}
      <div className="grid grid-cols-2 gap-2">
        <Button
          variant={orderType === 'buy' ? 'default' : 'outline'}
          onClick={() => setOrderType('buy')}
          className="buy-button"
        >
          매수
        </Button>
        <Button
          variant={orderType === 'sell' ? 'default' : 'outline'}
          onClick={() => setOrderType('sell')}
          className="sell-button"
        >
          매도
        </Button>
      </div>

      {/* 수량 입력 */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          수량
        </label>
        <Input
          type="number"
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
          className="input-dark"
          placeholder="0"
        />
      </div>

      {/* 가격 입력 */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          가격
        </label>
        <Input
          type="number"
          value={price}
          onChange={(e) => setPrice(Number(e.target.value))}
          className="input-dark"
          placeholder="시장가"
        />
      </div>

      {/* 실행 버튼 */}
      <Button
        className={cn(
          'w-full font-semibold',
          orderType === 'buy' ? 'buy-button-primary' : 'sell-button-primary'
        )}
        onClick={handleQuickTrade}
      >
        {orderType === 'buy' ? '즉시 매수' : '즉시 매도'}
      </Button>

      {/* 자동매매 설정 링크 */}
      <Button
        variant="outline"
        className="w-full"
        onClick={() => router.push('/trading/conditions')}
      >
        자동매매 설정
      </Button>
    </div>
  );
}
```

### 3. DashboardGrid 컴포넌트

**위치**: `src/components/dashboard/DashboardGrid.tsx`

```typescript
export function DashboardGrid() {
  return (
    <div className="dashboard-grid">
      {/* 상단: 포트폴리오 요약 + 시장 상태 */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <div className="xl:col-span-3">
          <PortfolioSummary className="h-full" />
        </div>
        <div className="xl:col-span-1">
          <MarketStatusCard />
        </div>
      </div>

      {/* 중앙: 워치리스트 (확장 가능) */}
      <div className="min-h-0">
        <WatchlistPanel />
      </div>

      {/* 하단: 최근 거래 내역 */}
      <div className="h-48">
        <RecentTradesPanel />
      </div>
    </div>
  );
}
```

### 4. TradingInterface 페이지 컴포넌트

**위치**: `src/app/trading/page.tsx`

```typescript
export default function TradingPage() {
  const [tradingMode, setTradingMode] = useState<'manual' | 'auto'>('manual');
  const [selectedStock, setSelectedStock] = useState<string>('');

  return (
    <div className="min-h-screen bg-[#0a0a0b]">
      <Header />

      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white mb-2">매매 인터페이스</h1>
          <p className="text-gray-400">
            주식 매수/매도 및 자동매매 설정을 관리합니다.
          </p>
        </div>

        {/* 모드 스위치 */}
        <div className="mb-6">
          <TradingModeSwitch
            mode={tradingMode}
            onChange={setTradingMode}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 좌측: 매매 인터페이스 */}
          <div className="lg:col-span-2">
            {tradingMode === 'manual' ? (
              <ManualTradingInterface />
            ) : (
              <AutoTradingInterface />
            )}
          </div>

          {/* 우측: 보조 정보 */}
          <div className="space-y-6">
            <StockInfoCard stock={selectedStock} />
            <OrderHistoryCard />
            <RiskAssessmentCard />
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 📝 TypeScript 인터페이스

### 1. 기본 데이터 타입

**위치**: `src/lib/types/trading.ts`

```typescript
// 기본 주식 정보
export interface Stock {
  code: string;
  name: string;
  currentPrice: number;
  changeRate: number;
  changeAmount: number;
  volume: number;
  marketCap?: number;
}

// 주문 정보
export interface Order {
  id: string;
  stockCode: string;
  stockName: string;
  type: 'buy' | 'sell';
  orderType: 'market' | 'limit' | 'stop';
  quantity: number;
  price?: number;
  stopPrice?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
  timestamp: Date;
  filledQuantity?: number;
  filledPrice?: number;
}

// 포지션 정보
export interface Position {
  stockCode: string;
  stockName: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  totalValue: number;
  unrealizedPnL: number;
  unrealizedPnLRate: number;
}

// 자동매매 조건
export interface TradingCondition {
  id: string;
  name: string;
  stockCode: string;
  type: 'buy' | 'sell';
  conditions: {
    rsi?: { min?: number; max?: number };
    macd?: { signal: 'positive' | 'negative' | 'crossover' };
    price?: { min?: number; max?: number };
    volume?: { min?: number };
  };
  action: {
    quantity: number;
    priceType: 'market' | 'limit';
    limitPrice?: number;
  };
  isActive: boolean;
  createdAt: Date;
  lastTriggered?: Date;
}
```

### 2. 컴포넌트 Props 타입

**위치**: `src/lib/types/components.ts`

```typescript
// QuickActionPanel Props
export interface QuickActionPanelProps {
  className?: string;
  defaultTab?: 'watch' | 'trade' | 'alerts';
  onStockSelect?: (stock: Stock) => void;
}

// TradingQuick Props
export interface TradingQuickProps {
  selectedStock?: string;
  onOrderSubmit?: (order: Partial<Order>) => Promise<void>;
  className?: string;
}

// DashboardGrid Props
export interface DashboardGridProps {
  portfolioData?: Portfolio;
  watchlistData?: Stock[];
  recentTrades?: Order[];
  className?: string;
}

// TradingInterface Props
export interface TradingInterfaceProps {
  mode: 'manual' | 'auto';
  selectedStock?: Stock;
  onModeChange?: (mode: 'manual' | 'auto') => void;
  onStockChange?: (stock: Stock) => void;
}
```

### 3. 상태 관리 타입

**위치**: `src/lib/types/state.ts`

```typescript
// 전역 상태 타입
export interface AppState {
  user: {
    id: string;
    name: string;
    accountBalance: number;
  };
  portfolio: {
    positions: Position[];
    totalValue: number;
    dayPnL: number;
    dayPnLRate: number;
  };
  trading: {
    selectedStock: Stock | null;
    mode: 'manual' | 'auto';
    activeOrders: Order[];
    conditions: TradingCondition[];
  };
  ui: {
    sidebarOpen: boolean;
    quickActionTab: 'watch' | 'trade' | 'alerts';
    selectedTimeframe: '1D' | '1W' | '1M' | '3M' | '1Y';
  };
}

// 액션 타입
export type AppAction =
  | { type: 'SET_SELECTED_STOCK'; payload: Stock }
  | { type: 'SET_TRADING_MODE'; payload: 'manual' | 'auto' }
  | { type: 'ADD_ORDER'; payload: Order }
  | { type: 'UPDATE_POSITIONS'; payload: Position[] }
  | { type: 'SET_QUICK_ACTION_TAB'; payload: 'watch' | 'trade' | 'alerts' };
```

---

## 🎨 스타일링 가이드

### 1. Tailwind CSS 확장

**위치**: `src/app/globals.css`

```css
@layer utilities {
  /* Layout */
  .dashboard-grid {
    @apply grid grid-rows-[auto_1fr_auto] h-full gap-6;
  }

  .quick-panel {
    @apply w-80 bg-[#1a1a1b] border-l border-gray-700 h-full flex flex-col;
  }

  /* Navigation */
  .tab-nav {
    @apply flex border-b border-gray-700;
  }

  .tab-button {
    @apply flex-1 flex items-center justify-center gap-2 p-3 text-sm font-medium transition-colors;
  }

  .tab-button-active {
    @apply text-blue-400 bg-blue-500/10 border-b-2 border-blue-400;
  }

  .tab-button-inactive {
    @apply text-gray-400 hover:text-gray-300 hover:bg-gray-800/50;
  }

  /* Trading Components */
  .trading-card {
    @apply bg-[#2a2a2a] border border-gray-700 rounded-lg p-6 shadow-xl;
  }

  .input-dark {
    @apply bg-[#1a1a1a] border-gray-600 text-white placeholder:text-gray-500;
  }

  .buy-button {
    @apply bg-green-600 hover:bg-green-700 text-white border-green-600;
  }

  .sell-button {
    @apply bg-red-600 hover:bg-red-700 text-white border-red-600;
  }

  .buy-button-primary {
    @apply bg-green-600 hover:bg-green-700 text-white shadow-lg shadow-green-600/20;
  }

  .sell-button-primary {
    @apply bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/20;
  }

  /* Status Indicators */
  .status-positive {
    @apply text-green-400 bg-green-500/10 border-green-500/30;
  }

  .status-negative {
    @apply text-red-400 bg-red-500/10 border-red-500/30;
  }

  .status-neutral {
    @apply text-gray-400 bg-gray-500/10 border-gray-500/30;
  }

  /* Cards */
  .card-professional {
    @apply bg-[#2a2a2a] border border-gray-700 rounded-lg shadow-xl;
  }

  .card-professional-elevated {
    @apply bg-[#2a2a2a] border border-gray-600 rounded-lg shadow-2xl shadow-black/20;
  }
}
```

### 2. 색상 팔레트

```css
:root {
  /* Background Colors */
  --bg-primary: #0a0a0b;
  --bg-secondary: #1a1a1b;
  --bg-tertiary: #2a2a2a;

  /* Border Colors */
  --border-primary: #374151;
  --border-secondary: #4b5563;

  /* Text Colors */
  --text-primary: #ffffff;
  --text-secondary: #d1d5db;
  --text-tertiary: #9ca3af;

  /* Trading Colors */
  --color-buy: #10b981;
  --color-sell: #ef4444;
  --color-neutral: #6b7280;

  /* Accent Colors */
  --color-blue: #3b82f6;
  --color-purple: #8b5cf6;
  --color-amber: #f59e0b;
}
```

---

## 🚀 구현 순서

### Phase 1: 기본 구조 구현 (1-2일)

#### Day 1: 레이아웃 기반 작업
1. **QuickActionPanel 컴포넌트 생성**
   ```bash
   # 파일 생성
   touch src/components/layout/QuickActionPanel.tsx
   touch src/components/layout/TabButton.tsx
   ```

2. **기본 레이아웃 수정**
   - `src/app/page.tsx` 메인 레이아웃 업데이트
   - 우측 QuickActionPanel 영역 추가
   - 기존 사이드바 경량화

3. **CSS 스타일링 추가**
   - `globals.css`에 새로운 유틸리티 클래스 추가
   - 색상 변수 정의

#### Day 2: 탭 네비게이션 구현
1. **탭 기능 구현**
   ```typescript
   // TabButton 컴포넌트 구현
   // 상태 관리 로직 추가
   // 애니메이션 효과 추가
   ```

2. **기본 탭 콘텐츠 생성**
   ```bash
   touch src/components/trading/WatchlistQuick.tsx
   touch src/components/trading/TradingQuick.tsx
   touch src/components/trading/AlertsPanel.tsx
   ```

### Phase 2: 매매 기능 구현 (3-4일)

#### Day 3-4: TradingQuick 컴포넌트
1. **주문 폼 구현**
   - 종목 선택 인터페이스
   - 매수/매도 토글
   - 수량/가격 입력

2. **상태 관리 통합**
   - 선택된 주식 상태 관리
   - 주문 제출 로직 구현

#### Day 5-6: 별도 매매 페이지
1. **라우팅 설정**
   ```bash
   mkdir -p src/app/trading
   touch src/app/trading/page.tsx
   touch src/app/trading/layout.tsx
   ```

2. **TradingInterface 컴포넌트 구현**
   - 수동 매매 인터페이스
   - 자동 매매 설정 인터페이스

### Phase 3: 고급 기능 구현 (1주)

#### 자동매매 조건 설정
1. **조건 설정 UI**
   ```bash
   touch src/app/trading/conditions/page.tsx
   touch src/components/trading/ConditionBuilder.tsx
   ```

2. **백테스팅 결과**
   ```bash
   touch src/app/trading/backtest/page.tsx
   touch src/components/trading/BacktestResults.tsx
   ```

---

## 📁 파일 구조

### 새로 생성할 파일들

```
src/
├── app/
│   ├── trading/                    # 새로운 매매 페이지
│   │   ├── page.tsx               # 메인 매매 인터페이스
│   │   ├── layout.tsx             # 매매 섹션 레이아웃
│   │   ├── conditions/
│   │   │   └── page.tsx           # 자동매매 조건 설정
│   │   └── backtest/
│   │       └── page.tsx           # 백테스트 결과
│   └── analytics/
│       └── page.tsx               # 분석 페이지
├── components/
│   ├── layout/
│   │   ├── QuickActionPanel.tsx   # 우측 빠른 액션 패널
│   │   └── TabButton.tsx          # 탭 버튼 컴포넌트
│   ├── trading/
│   │   ├── TradingQuick.tsx       # 빠른 매매 인터페이스
│   │   ├── WatchlistQuick.tsx     # 빠른 관심종목
│   │   ├── AlertsPanel.tsx        # 알림 패널
│   │   ├── TradingInterface.tsx   # 메인 매매 인터페이스
│   │   ├── ManualTradingInterface.tsx  # 수동 매매
│   │   ├── AutoTradingInterface.tsx    # 자동 매매
│   │   ├── ConditionBuilder.tsx   # 조건 설정기
│   │   ├── BacktestResults.tsx    # 백테스트 결과
│   │   ├── OrderForm.tsx          # 주문 폼
│   │   ├── StockSearchInput.tsx   # 종목 검색
│   │   └── TradingModeSwitch.tsx  # 모드 스위치
│   ├── dashboard/
│   │   ├── DashboardGrid.tsx      # 개선된 대시보드 그리드
│   │   ├── MarketStatusCard.tsx   # 시장 상태 카드
│   │   └── RecentTradesPanel.tsx  # 최근 거래 패널
│   └── common/
│       ├── StockInfoCard.tsx      # 주식 정보 카드
│       ├── OrderHistoryCard.tsx   # 주문 내역 카드
│       └── RiskAssessmentCard.tsx # 리스크 평가 카드
├── lib/
│   ├── types/
│   │   ├── trading.ts             # 매매 관련 타입
│   │   ├── components.ts          # 컴포넌트 Props 타입
│   │   └── state.ts               # 상태 관리 타입
│   ├── hooks/
│   │   ├── useTrading.ts          # 매매 관련 훅
│   │   ├── useQuickAction.ts      # 빠른 액션 훅
│   │   └── useTradingConditions.ts # 자동매매 조건 훅
│   └── utils/
│       ├── trading.ts             # 매매 유틸리티
│       └── formatters.ts          # 데이터 포매터
```

### 수정할 기존 파일들

```
src/
├── app/
│   ├── page.tsx                   # 메인 레이아웃 수정
│   └── globals.css                # 새로운 CSS 유틸리티 추가
├── components/
│   ├── layout/
│   │   └── Header.tsx             # 네비게이션 메뉴 추가
│   └── trading/
│       └── TradingConditions.tsx  # 경량화 (일부 기능 이동)
```

---

## 🧪 테스트 가이드

### 1. 컴포넌트 테스트

각 컴포넌트 구현 후 다음 항목들을 확인:

#### QuickActionPanel
- [ ] 탭 전환이 정상적으로 작동하는가?
- [ ] 각 탭의 콘텐츠가 올바르게 렌더링되는가?
- [ ] 반응형 디자인이 적용되는가?

#### TradingQuick
- [ ] 종목 검색이 작동하는가?
- [ ] 매수/매도 토글이 작동하는가?
- [ ] 주문 제출이 정상적으로 처리되는가?
- [ ] 유효성 검사가 작동하는가?

### 2. 통합 테스트

#### 사용자 플로우 테스트
1. **빠른 매매 플로우**
   ```
   종목 검색 → 수량 입력 → 가격 설정 → 주문 제출 → 결과 확인
   ```

2. **자동매매 설정 플로우**
   ```
   매매 페이지 이동 → 자동 모드 선택 → 조건 설정 → 백테스트 실행 → 조건 활성화
   ```

### 3. 브라우저 테스트

#### 반응형 테스트
- **Desktop** (1920x1080): 전체 기능 사용
- **Laptop** (1366x768): QuickActionPanel 축소
- **Tablet** (768x1024): 사이드 패널 숨김
- **Mobile** (375x667): 모바일 최적화 확인

### 4. 성능 테스트

- 실시간 데이터 업데이트 시 렌더링 성능
- 많은 종목 목록 렌더링 성능
- 메모리 누수 검사

---

## ⚠️ 주의사항

### 1. 기존 코드 호환성
- 기존 TradingConditions 컴포넌트의 기능을 점진적으로 이동
- API 호출 로직은 최대한 재사용
- 기존 상태 관리와 충돌하지 않도록 주의

### 2. 성능 최적화
```typescript
// React.memo 사용으로 불필요한 렌더링 방지
export const TradingQuick = React.memo(function TradingQuick({ ... }) {
  // 컴포넌트 로직
});

// useMemo로 비싼 계산 최적화
const filteredStocks = useMemo(() => {
  return stocks.filter(stock => stock.name.includes(searchTerm));
}, [stocks, searchTerm]);
```

### 3. 타입 안전성
- 모든 Props에 대한 TypeScript 인터페이스 정의
- API 응답 타입 명시
- 상태 변경 시 타입 검사 활용

### 4. 에러 처리
```typescript
// 에러 바운더리 활용
export function TradingErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary fallback={<TradingErrorFallback />}>
      {children}
    </ErrorBoundary>
  );
}

// 로딩 상태 처리
{isLoading ? <TradingLoadingSkeleton /> : <TradingQuick />}
```

---

## ✅ 완료 체크리스트

### Phase 1 완료 확인
- [ ] QuickActionPanel 컴포넌트 생성 및 통합
- [ ] 탭 네비게이션 구현
- [ ] 기본 CSS 스타일링 적용
- [ ] 반응형 레이아웃 확인

### Phase 2 완료 확인
- [ ] TradingQuick 컴포넌트 구현
- [ ] 매매 페이지 라우팅 설정
- [ ] 기본 매매 인터페이스 구현
- [ ] 상태 관리 통합

### Phase 3 완료 확인
- [ ] 자동매매 조건 설정 UI
- [ ] 백테스팅 결과 표시
- [ ] 전체 사용자 플로우 테스트
- [ ] 성능 최적화 및 에러 처리

---

## 📞 지원 및 문의

구현 중 문제가 발생하거나 추가 설명이 필요한 경우:

1. **컴포넌트 구조 문의**: 각 컴포넌트의 역할과 Props 정의
2. **스타일링 가이드**: Tailwind CSS 클래스 사용법
3. **상태 관리**: React 상태와 API 연동 방법
4. **타입 정의**: TypeScript 인터페이스 활용

이 문서를 기반으로 단계별로 구현하면 사용자 친화적이고 직관적인 주식 자동매매 시스템 UI를 완성할 수 있습니다.