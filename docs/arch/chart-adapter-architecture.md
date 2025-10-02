# 차트 어댑터 아키텍처 문서

**작성일**: 2025-10-02
**버전**: 2.0.0
**목적**: 확장 가능한 차트 라이브러리 추상화 아키텍처

---

## 📐 아키텍처 개요

### 설계 원칙
1. **Adapter Pattern**: 다양한 차트 라이브러리를 통일된 인터페이스로 추상화
2. **Strategy Pattern**: Y축 계산, 데이터 변환 등의 전략을 교체 가능하게 설계
3. **Factory Pattern**: 차트 라이브러리 선택을 런타임에 결정
4. **SOLID 원칙**: 확장에 열려있고 수정에 닫혀있는 구조

### 핵심 컴포넌트
```
UniversalChart (Factory)
    ↓
ChartAdapter (Interface)
    ↓
RechartsAdapter / EChartsAdapter / TradingViewAdapter (Implementations)
    ↓
YAxisCalculator (Strategy)
```

---

## 🎨 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│                   UniversalChart                         │
│              (Factory Component)                         │
│  - library prop으로 차트 라이브러리 선택                  │
│  - Dynamic import로 코드 스플리팅                         │
└───────────────┬─────────────────────────────────────────┘
                │
                │ ChartAdapterProps
                ├───────────┬───────────┬──────────────┐
                ↓           ↓           ↓              ↓
        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
        │Recharts  │ │ ECharts  │ │TradingView│ │Lightweight│
        │ Adapter  │ │ Adapter  │ │  Adapter  │ │  Charts   │
        └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │            │
             └────────────┴────────────┴────────────┘
                          │
                 Shared Components
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
 ┌──────────┐     ┌──────────┐     ┌──────────┐
 │  YAxis   │     │  Data    │     │  Theme   │
 │Calculator│     │Transformer│    │ Provider │
 └──────────┘     └──────────┘     └──────────┘
```

---

## 📦 파일 구조

```
stock-trading-ui/src/components/trading/chart-adapters/
├── ChartAdapter.tsx               # 인터페이스 정의
│   ├── ChartAdapterProps         # 공통 Props 인터페이스
│   ├── ChartEvents               # 이벤트 추상화
│   ├── ChartTheme                # 테마 정의
│   └── ChartConfig               # 차트 설정
│
├── index.tsx                      # UniversalChart (Factory)
│   ├── CHART_ADAPTERS            # 어댑터 맵
│   └── Dynamic import            # 코드 스플리팅
│
├── RechartsAdapter.tsx            # Recharts 구현체
├── EChartsAdapter.tsx             # ECharts 구현체 (TODO)
├── TradingViewAdapter.tsx         # TradingView 구현체 (TODO)
│
└── core/                          # 공통 로직
    ├── YAxisCalculator.ts         # Y축 계산 전략
    │   ├── YAxisCalculator        # 인터페이스
    │   ├── DailyRangeYAxisCalculator    # 일별 범위 90%
    │   ├── PriceLimitYAxisCalculator    # 시초가 ±30%
    │   ├── VisibleRangeYAxisCalculator  # 보이는 영역 기반
    │   └── YAxisCalculatorFactory       # 팩토리
    │
    ├── DataTransformer.ts         # 데이터 변환 (TODO)
    ├── ThemeProvider.ts           # 테마 관리 (TODO)
    └── EventMapper.ts             # 이벤트 매핑 (TODO)
```

---

## 🔌 인터페이스 정의

### 1. ChartAdapterProps (공통 Props)

```typescript
export interface ChartAdapterProps {
  /** 차트에 표시할 캔들 데이터 */
  chartData: ChartCandle[];

  /** 차트 높이 (픽셀) */
  height?: number;

  /** 시간 프레임 (1m, 5m, 1D 등) */
  timeframe: string;

  /** Y축 계산 전략 (기본: daily-range) */
  yAxisCalculator?: YAxisCalculator | string;

  /** 차트 이벤트 핸들러 */
  events?: ChartEvents;

  /** 차트 설정 */
  config?: Partial<ChartConfig>;
}
```

**특징**:
- 모든 어댑터가 준수해야 하는 공통 인터페이스
- 차트 라이브러리 특화 Props 제외
- 확장 가능한 설계

### 2. ChartEvents (이벤트 추상화)

```typescript
export interface ChartEvents {
  /** 표시 범위 변경 (Brush, Zoom, Pan) */
  onRangeChange?: (range: { startIndex: number; endIndex: number }) => void;

  /** 십자선 이동 */
  onCrosshairMove?: (data: ChartCandle | null) => void;

  /** 줌 레벨 변경 */
  onZoom?: (zoomLevel: number) => void;

  /** 캔들 클릭 */
  onClick?: (candle: ChartCandle) => void;

  /** 에러 발생 */
  onError?: (error: string) => void;
}
```

**특징**:
- 차트 라이브러리별 이벤트 시스템 통합
- Recharts의 `onBrushChange` → `onRangeChange`로 일반화
- TradingView, ECharts도 동일한 인터페이스 사용

### 3. YAxisCalculator (Y축 계산 전략)

```typescript
export interface YAxisCalculator {
  calculate(data: ChartCandle[]): YAxisDomain;
  readonly name: string;
}
```

**구현체**:
1. **DailyRangeYAxisCalculator**: 일별 최고/최저 기준 90% 범위
2. **PriceLimitYAxisCalculator**: 시초가 기준 ±30% (상한가/하한가)
3. **VisibleRangeYAxisCalculator**: 보이는 영역 기반 동적 범위

**사용법**:
```typescript
// 방법 1: 문자열로 지정
<UniversalChart yAxisCalculator="daily-range" />

// 방법 2: 객체로 지정
<UniversalChart yAxisCalculator={new DailyRangeYAxisCalculator(0.05)} />

// 방법 3: 팩토리 사용
const calc = YAxisCalculatorFactory.get('price-limit');
<UniversalChart yAxisCalculator={calc} />
```

---

## 🎯 사용 예시

### 기본 사용

```typescript
import { UniversalChart } from '@/components/trading/chart-adapters';

function MyChart() {
  const chartData = [...]; // ChartCandle[]

  return (
    <UniversalChart
      library="recharts"
      chartData={chartData}
      height={600}
      timeframe="1m"
    />
  );
}
```

### 이벤트 핸들러

```typescript
<UniversalChart
  library="recharts"
  chartData={chartData}
  events={{
    onRangeChange: (range) => {
      console.log('Range changed:', range);
    },
    onCrosshairMove: (candle) => {
      console.log('Crosshair on:', candle);
    },
    onError: (error) => {
      console.error('Chart error:', error);
    }
  }}
/>
```

### Y축 계산 전략 선택

```typescript
// 일별 범위 90% (기본값)
<UniversalChart yAxisCalculator="daily-range" chartData={data} />

// 시초가 ±30%
<UniversalChart yAxisCalculator="price-limit" chartData={data} />

// 보이는 영역 기반 (동적)
<UniversalChart yAxisCalculator="visible-range" chartData={data} />

// 커스텀 패딩
<UniversalChart
  yAxisCalculator={new DailyRangeYAxisCalculator(0.10)}
  chartData={data}
/>
```

---

## 🔧 새로운 차트 라이브러리 추가 방법

### Step 1: Adapter 구현

```typescript
// chart-adapters/TradingViewAdapter.tsx
import React from 'react';
import { ChartAdapterProps } from './ChartAdapter';
import { YAxisCalculatorFactory } from './core/YAxisCalculator';

const TradingViewAdapter: React.FC<ChartAdapterProps> = ({
  chartData,
  height,
  timeframe,
  yAxisCalculator,
  events,
  config,
}) => {
  // 1. Y축 계산기 가져오기
  const calculator = yAxisCalculator
    ? typeof yAxisCalculator === 'string'
      ? YAxisCalculatorFactory.get(yAxisCalculator)
      : yAxisCalculator
    : YAxisCalculatorFactory.get('daily-range');

  // 2. Y축 도메인 계산
  const yDomain = calculator.calculate(chartData);

  // 3. TradingView 차트 렌더링
  return (
    <div>
      {/* TradingView 구현 */}
    </div>
  );
};

export default TradingViewAdapter;
```

### Step 2: Factory에 등록

```typescript
// chart-adapters/index.tsx
import dynamic from 'next/dynamic';

const TradingViewAdapter = dynamic(() => import('./TradingViewAdapter'), {
  ssr: false,
});

const CHART_ADAPTERS = {
  recharts: RechartsAdapter,
  tradingview: TradingViewAdapter, // 추가
  echarts: EChartsAdapter,
  'lightweight-charts': LightweightChartsAdapter,
};
```

### Step 3: 타입 정의 업데이트

```typescript
// chart-adapters/ChartAdapter.tsx
export type ChartLibrary =
  | 'recharts'
  | 'tradingview'  // 추가
  | 'echarts'
  | 'lightweight-charts';
```

**완료!** 이제 `<UniversalChart library="tradingview" />`로 사용 가능

---

## 🎨 커스텀 Y축 계산기 추가

### Step 1: YAxisCalculator 구현

```typescript
// core/YAxisCalculator.ts
export class CustomYAxisCalculator implements YAxisCalculator {
  readonly name = 'Custom';

  calculate(data: ChartCandle[]): YAxisDomain {
    // 커스텀 로직
    const min = ...;
    const max = ...;
    return [min, max];
  }
}
```

### Step 2: Factory에 등록

```typescript
YAxisCalculatorFactory.register('custom', new CustomYAxisCalculator());
```

### Step 3: 사용

```typescript
<UniversalChart yAxisCalculator="custom" chartData={data} />
```

---

## 🔄 마이그레이션 가이드

### Before (기존 코드)

```typescript
import RealtimeCandlestickChart from './RealtimeCandlestickChart';

<RealtimeCandlestickChart
  chartData={data}
  height={400}
  timeframe="1m"
/>
```

### After (리팩토링 후)

```typescript
import { UniversalChart } from './chart-adapters';

<UniversalChart
  library="recharts"
  chartData={data}
  height={400}
  timeframe="1m"
  yAxisCalculator="daily-range"
/>
```

**변경 사항**:
- `RealtimeCandlestickChart` → `UniversalChart`
- `library` prop 추가 (기본값: 'recharts')
- `yAxisCalculator` prop으로 Y축 전략 선택 가능

---

## 🏆 아키텍처 장점

### 1. 확장성
- **새 차트 라이브러리**: 100-150 lines로 추가 가능
- **새 Y축 전략**: 20-30 lines로 추가 가능
- **인터페이스 유지**: 기존 코드 수정 불필요

### 2. 유지보수성
- **중앙 집중화**: Y축 로직 한 곳에서 관리
- **일관성**: 모든 차트에서 동일한 Y축 전략 적용
- **테스트 용이**: 각 전략을 독립적으로 테스트

### 3. 유연성
- **런타임 전환**: 차트 라이브러리 동적 선택
- **전략 교체**: Y축 계산 전략 쉽게 변경
- **설정 가능**: 패딩 비율, 제한 비율 등 커스터마이징

### 4. 성능
- **코드 스플리팅**: Dynamic import로 필요한 라이브러리만 로드
- **메모이제이션**: useMemo로 불필요한 재계산 방지
- **최적화**: 각 어댑터별 최적화 독립적으로 적용

---

## 📊 비교표

| 항목 | Before | After |
|------|--------|-------|
| **Y축 로직** | 각 Adapter에 중복 | YAxisCalculator로 공통화 |
| **이벤트 시스템** | 차트별로 상이 | ChartEvents로 통합 |
| **차트 추가** | 500+ lines | 100-150 lines |
| **전략 변경** | 모든 Adapter 수정 | YAxisCalculator만 수정 |
| **테마 변경** | 하드코딩 | ThemeProvider (TODO) |

---

## 🚀 향후 계획 (Phase 2, 3)

### Phase 2: 공통 로직 분리

1. **DataTransformer** (Priority: High)
   ```typescript
   ChartDataTransformer.toRecharts(data)
   ChartDataTransformer.toECharts(data)
   ChartDataTransformer.toTradingView(data)
   ```

2. **ThemeProvider** (Priority: Medium)
   ```typescript
   ThemeProvider.setTheme('dark' | 'light')
   ThemeProvider.getTheme()
   ```

3. **EventMapper** (Priority: Medium)
   ```typescript
   EventMapper.mapRechartsEvents(events)
   EventMapper.mapTradingViewEvents(events)
   ```

### Phase 3: ECharts 통합

1. `EChartsCandlestickChart.tsx`를 `EChartsAdapter.tsx`로 변환
2. `UniversalChart`에 통합
3. 기존 EChartsAdapter 더미 제거

---

## 🎓 디자인 패턴 적용

### Adapter Pattern
- **목적**: 서로 다른 차트 라이브러리를 통일된 인터페이스로 사용
- **적용**: `ChartAdapterProps` → 각 Adapter 구현체

### Strategy Pattern
- **목적**: Y축 계산 알고리즘을 교체 가능하게 만듦
- **적용**: `YAxisCalculator` → 다양한 구현체

### Factory Pattern
- **목적**: 객체 생성 로직을 캡슐화
- **적용**: `UniversalChart`, `YAxisCalculatorFactory`

### SOLID 원칙
- **S**: 각 클래스는 단일 책임 (Y축 계산, 데이터 변환 등)
- **O**: 확장에 열려있고 수정에 닫혀있음 (새 어댑터 추가 용이)
- **L**: 모든 어댑터는 `ChartAdapterProps` 준수
- **I**: 인터페이스 분리 (ChartEvents, YAxisCalculator 등)
- **D**: 추상화에 의존 (구체적 구현체가 아닌 인터페이스에 의존)

---

## 📝 관련 문서

- **구현 문서**: `docs/impl/y-axis-daily-range-strategy.md`
- **테스트 가이드**: `docs/test/y-axis-fixed-range-test-guide.md`
- **코드 위치**: `stock-trading-ui/src/components/trading/chart-adapters/`

---

## 💡 Best Practices

1. **새 어댑터 구현 시**:
   - `ChartAdapterProps` 인터페이스 준수
   - `YAxisCalculatorFactory.get()` 사용
   - `ChartEvents`로 이벤트 매핑

2. **Y축 전략 추가 시**:
   - `YAxisCalculator` 인터페이스 구현
   - `YAxisCalculatorFactory.register()` 등록
   - 명확한 `name` 속성 제공

3. **테마 적용 시** (TODO):
   - `ThemeProvider` 사용
   - 하드코딩 금지
   - 런타임 변경 가능하도록

---

**버전 이력**:
- v1.0.0 (2025-10-01): 초기 Adapter 패턴 구현
- v2.0.0 (2025-10-02): Y축 계산 추상화, 이벤트 시스템 통합
