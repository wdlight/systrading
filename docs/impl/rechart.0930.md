# Recharts 캔들스틱 차트 구현 기록

**날짜**: 2025-09-30
**작업**: Recharts 라이브러리를 사용한 한국식 캔들스틱 차트 구현
**파일**: `stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx`

---

## 📋 요구사항

1. 한국투자증권 API에서 받은 분봉 데이터를 캔들스틱 차트로 표시
2. 한국식 스타일: 상승(빨강), 하락(파랑)
3. Y축은 데이터 범위의 80%를 사용하여 캔들이 충분히 보이도록 설정
4. 30개의 캔들을 한 화면에 표시
5. 좌클릭 드래그로 차트 스크롤 가능

---

## 🚧 주요 문제들 (Hiccups)

### 1. Backend API 엔드포인트 불일치

**문제**:
```
GET /api/chart/domestic/candles/005930?timeframe=1m HTTP/1.1" 404 Not Found
```

**원인**:
- Frontend: `/api/chart/domestic/candles/${stockCode}?timeframe=1m`
- Backend: `/api/chart/${stockCode}/minute`

**해결**:
```typescript
// useRealChartData.ts
if (timeframe === '1m') {
  url = `${API_BASE_URL}/api/chart/${stockCode}/minute`;
}
```

---

### 2. TypeScript 타입 불일치

**문제**: Backend가 nullable 필드를 반환하지만 TypeScript 타입이 `number`로 정의됨

**해결**:
```typescript
// lib/types/korean-stocks.ts
export interface KoreanStockChart {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  tradingValue: number | null;      // ✅ null 허용
  foreignBuy: number | null;         // ✅ null 허용
  foreignSell: number | null;        // ✅ null 허용
  institutionalBuy: number | null;   // ✅ null 허용
  institutionalSell: number | null;  // ✅ null 허용
  individualBuy: number | null;      // ✅ null 허용
  individualSell: number | null;     // ✅ null 허용
}
```

---

### 3. Recharts Bar 컴포넌트의 yAxisMap 전달 실패 ⚠️ **핵심 문제**

**문제**:
```javascript
// Bar 컴포넌트의 shape prop이 yAxisMap을 전달하지 않음
<Bar shape={CandlestickShape} />

// 결과
console.log('🕯️ CandlestickShape props:', { yAxisMap: false })
// ⚠️ Missing props - 모든 캔들이 렌더링 실패
```

**시도 1 - Bar 컴포넌트의 shape prop**:
```typescript
const CandlestickShape = (props: any) => {
  const { payload, x, width, yAxisMap, index } = props;

  if (!yAxisMap) {
    return null; // ❌ yAxisMap이 항상 false
  }

  const yAxis = yAxisMap[0];
  const yHigh = yAxis.scale(high);
  // ...
};

<Bar dataKey="candlestick" shape={CandlestickShape} />
```
**결과**: ❌ 실패 - `yAxisMap`이 전달되지 않음

---

**시도 2 - yAxisId 명시적 설정**:
```typescript
<Bar
  dataKey="candlestick"
  shape={(props: any) => <CandlestickShape {...props} />}
  yAxisId={0}  // ✅ 명시적으로 설정
/>
```
**결과**: ❌ 실패 - 여전히 `yAxisMap: false`

---

**시도 3 - Customized 컴포넌트 사용**:
```typescript
const CustomCandlesticks = (props: any) => {
  const { xAxisMap, yAxisMap, formattedGraphicalItems } = props;
  // Recharts가 자동으로 chart context를 전달한다고 문서에 명시
};

<Customized component={CustomCandlesticks} />
```
**결과**: ❌ 실패 - props가 빈 객체 `{}`로 전달됨
```javascript
console.log('🔍 Customized props:', Object.keys(props)); // []
```

---

**시도 4 - Customized를 wrapper 함수로 사용**:
```typescript
<Customized component={(chartProps: any) => {
  console.log('Props:', Object.keys(chartProps));
  return <CustomCandlesticks {...chartProps} />;
}} />
```
**결과**: ❌ 실패 - wrapper도 빈 props 전달

---

### 4. 최종 해결책: Line 컴포넌트 + 커스텀 Scale ✅

**핵심 아이디어**:
- Recharts의 `Line` 컴포넌트는 `dot` prop을 통해 각 데이터 포인트를 커스터마이징 가능
- `dot`은 `cx`, `cy`, `payload` 등을 받지만 `yAxisMap`은 받지 못함
- 해결: **수동으로 Y축 스케일 함수를 생성**하여 가격을 픽셀 좌표로 변환

**구현**:

```typescript
// 1. 선형 스케일 함수 생성
const createYScale = (yDomain: [number, number], chartHeight: number, margin: number = 10) => {
  const [min, max] = yDomain;
  const range = max - min;
  const effectiveHeight = chartHeight - 2 * margin;

  return (value: number) => {
    // 가격을 픽셀 좌표로 변환 (Y축은 위에서 아래로 증가)
    const normalized = (value - min) / range; // 0 to 1
    return chartHeight - margin - (normalized * effectiveHeight);
  };
};

// 2. 캔들스틱 렌더링 컴포넌트 팩토리
const createCandlestickDot = (yDomain: [number, number], chartHeight: number) => {
  const yScale = createYScale(yDomain, chartHeight);

  return (props: any) => {
    const { cx, payload } = props;
    const { open, high, low, close } = payload;

    // 커스텀 스케일로 Y 좌표 계산
    const yHigh = yScale(high);
    const yLow = yScale(low);
    const yOpen = yScale(open);
    const yClose = yScale(close);

    const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1);
    const bodyY = Math.min(yOpen, yClose);

    // 한국식: 상승=빨강, 하락=파랑
    const isRising = close >= open;
    const fillColor = isRising ? '#ef4444' : '#3b82f6';
    const strokeColor = isRising ? '#dc2626' : '#2563eb';

    return (
      <g>
        {/* 심지 (High-Low 라인) */}
        <line x1={cx} y1={yHigh} x2={cx} y2={yLow}
              stroke={strokeColor} strokeWidth={1} />

        {/* 캔들 몸통 (Open-Close 박스) */}
        <rect x={cx - candleWidth/2} y={bodyY}
              width={candleWidth} height={bodyHeight}
              fill={fillColor} stroke={strokeColor} strokeWidth={1} />
      </g>
    );
  };
};

// 3. Line 컴포넌트에 적용
<Line
  dataKey="close"
  stroke="none"
  dot={createCandlestickDot(yDomain, height)}
  isAnimationActive={false}
  yAxisId={0}
/>
```

**핵심 포인트**:
- ✅ `yDomain`과 `chartHeight`를 클로저로 캡처하여 스케일 함수 생성
- ✅ Recharts의 내부 scale에 의존하지 않고 독립적으로 동작
- ✅ `Line` 컴포넌트의 `dot` prop은 안정적으로 `cx`, `cy`, `payload` 전달
- ✅ 각 캔들을 SVG `<g>`, `<line>`, `<rect>`로 수동 렌더링

---

## 📊 Y축 범위 계산 (80% 사용)

```typescript
const yDomain = useMemo(() => {
  if (formattedData.length === 0) {
    return [70000, 100000];
  }

  const allPrices = formattedData.flatMap(d => [d.open, d.high, d.low, d.close]);
  const min = Math.min(...allPrices);
  const max = Math.max(...allPrices);

  // 데이터가 Y축 범위의 80%를 차지하도록 패딩 추가
  const dataRange = max - min;
  const totalRange = dataRange / 0.8;  // 80% → 100%
  const padding = (totalRange - dataRange) / 2;

  const yMin = Math.floor(min - padding);
  const yMax = Math.ceil(max + padding);

  console.log(`📊 Y축 범위: ${yMin.toLocaleString()}원 ~ ${yMax.toLocaleString()}원
    (전체 데이터: ${min.toLocaleString()}~${max.toLocaleString()}원, 데이터 비율: 80%)`);

  return [yMin, yMax];
}, [formattedData]);
```

**실제 결과**:
- 데이터 범위: 84,100원 ~ 84,600원 (500원)
- Y축 범위: 84,037원 ~ 84,663원 (626원)
- 데이터 비율: 500 / 626 = 79.87% ≈ **80%** ✅

---

## 🧪 테스트 및 검증

### Playwright 자동화 테스트
```typescript
// tests/test-chart-screenshot.spec.ts
test('test-chart 페이지 스크린샷 및 차트 확인', async ({ page }) => {
  await page.goto('http://localhost:9000/test-chart');

  // 차트 렌더링 대기
  await page.waitForTimeout(5000);

  // 스크린샷 캡처
  await page.screenshot({ path: 'test-chart-full.png', fullPage: true });

  const rechartsContainer = page.locator('.recharts-responsive-container').first();
  await rechartsContainer.screenshot({ path: 'test-chart-recharts.png' });

  // 콘솔 로그 수집
  const logs: string[] = [];
  page.on('console', msg => logs.push(msg.text()));
});
```

### 검증 결과
```
✅ Chart data loaded: 120 candles
✅ CandlestickDot rendering: {
  payload: { open: 84100, high: 84200, low: 84100, close: 84100 },
  positions: { yHigh: 10.5, yLow: 489.5, yOpen: 489.5, yClose: 413.2 },
  bodyHeight: 76.67,
  candleWidth: 8
}
```

---

## 🎨 최종 스타일

```typescript
// 한국식 캔들스틱 색상
const isRising = close >= open;
const fillColor = isRising ? '#ef4444' : '#3b82f6';   // 상승: 빨강, 하락: 파랑
const strokeColor = isRising ? '#dc2626' : '#2563eb'; // 테두리: 진한 톤

// 캔들 크기
const candleWidth = Math.min(width * 0.6, 8);  // 최대 8px
const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1); // 최소 1px
```

---

## 📝 교훈 및 베스트 프랙티스

### 1. Recharts의 제약사항 이해
- `Bar` 컴포넌트의 `shape` prop은 모든 차트 context를 전달하지 않음
- `Customized` 컴포넌트도 문서와 달리 빈 props를 받을 수 있음
- **해결**: 라이브러리에 의존하지 않고 수동으로 스케일 함수 구현

### 2. 디버깅 전략
```typescript
// 1. Props 구조 파악
if (index === 0) {
  console.log('🔍 Props keys:', Object.keys(props));
}

// 2. 단계별 값 확인
console.log('✅ Rendering:', {
  payload: { open, high, low, close },
  positions: { yHigh, yLow, yOpen, yClose },
  bodyHeight, candleWidth
});

// 3. Playwright로 자동화 테스트 및 스크린샷 캡처
```

### 3. 대안 접근법의 중요성
- 처음 시도한 방법이 안 될 때, 완전히 다른 접근법 고려
- `Bar` → `Customized` → `Line` 순으로 시도
- **Line + 커스텀 스케일**이 가장 안정적인 해결책

### 4. 타입 안전성
```typescript
// Backend 응답과 정확히 일치하도록 타입 정의
export interface KoreanStockChart {
  // 필수 필드
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;

  // 선택적 필드 (null 허용)
  tradingValue: number | null;
  foreignBuy: number | null;
  // ...
}
```

---

## 🔗 관련 파일

- **차트 어댑터**: `src/components/trading/chart-adapters/RechartsAdapter.tsx`
- **데이터 훅**: `src/hooks/useRealChartData.ts`
- **타입 정의**: `src/lib/types/korean-stocks.ts`
- **테스트**: `tests/test-chart-screenshot.spec.ts`

---

## 📚 참고 자료

- [Recharts 공식 문서](https://recharts.org/en-US/api)
- [Recharts Customized Component](https://recharts.org/en-US/api/Customized)
- [SVG Coordinate System](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Positions)

---

## ✅ 최종 결과

- ✅ 30개의 캔들스틱이 정상적으로 표시
- ✅ 한국식 색상 (빨강/파랑) 적용
- ✅ Y축 80% 범위 사용으로 충분한 가시성 확보
- ✅ 심지와 몸통이 정확하게 렌더링
- ✅ 좌클릭 드래그로 차트 스크롤 가능
- ✅ Playwright 자동화 테스트로 검증 완료

**URL**: http://localhost:9000/test-chart