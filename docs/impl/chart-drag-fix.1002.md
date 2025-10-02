# 차트 좌측 드래그 문제 수정 (2025-10-02)

## 🔍 문제 진단

### 증상
- 차트에서 좌측으로 드래그 시 2시간 이전 데이터의 캔들이 렌더링되지 않음
- 최근 120개 분봉만 표시되고 과거 데이터 조회 불가

### 원인 분석

#### 1. 데이터 흐름 확인
```
Backend Cache (kordata/005930/20251002.dat)
  ↓ 391개 분봉 (09:00~15:30 전체)
Backend API (/api/chart/{stock_code}/minute/full)
  ↓ 391개 분봉 반환
Frontend (useRealChartData hook)
  ↓ formattedData: 391개 저장
RechartsAdapter
  ✗ displayData: 120개만 슬라이싱하여 차트에 전달 ← **문제**
```

#### 2. 핵심 문제 코드

**RechartsAdapter.tsx Line 260-305:**
```typescript
// ❌ 문제: displayData가 최대 120개로 제한됨
const displayData = useMemo(() => {
  const defaultWindowSize = Math.min(120, formattedData.length);
  const defaultStart = Math.max(0, formattedData.length - defaultWindowSize);

  if (viewWindow) {
    // 마지막 120개만 슬라이싱
    result = formattedData.slice(defaultStart);
  }
  return result;
}, [formattedData, viewWindow, xDomain]);
```

**Line 397:**
```typescript
// ❌ 문제: 120개만 차트에 전달
<ComposedChart
  data={displayData}  // 최대 120개
  margin={{ top: 20, right: 80, left: 20, bottom: 20 }}
>
```

### 데이터 확인
- Backend 캐시 파일: 5,866 라인 (391개 분봉 × 15줄/분봉)
- 시간 범위: `09:00:00` ~ `15:30:00`
- Frontend가 받는 데이터: 391개 (전체)
- 차트에 전달된 데이터: 120개 (제한됨) ← **문제**

---

## ✅ 해결 방법

### 수정 사항

#### 1. 전체 데이터를 차트에 전달
```typescript
// ✅ 수정 전 (Line 397)
<ComposedChart
  data={displayData}  // ❌ 120개만
  margin={{ top: 20, right: 80, left: 20, bottom: 20 }}
>

// ✅ 수정 후
<ComposedChart
  data={formattedData}  // ✅ 전체 391개
  margin={{ top: 20, right: 80, left: 20, bottom: 20 }}
>
```

#### 2. Y축 domain을 현재 보이는 영역 기준으로 계산
```typescript
// ✅ 수정 전 (Line 352-365)
const yDomain = useMemo(() => {
  // displayData 기준으로 계산 (120개만)
  const prices = displayData.flatMap(d => [d.open, d.high, d.low, d.close]);
  // ...
}, [displayData]);

// ✅ 수정 후
const yDomain = useMemo(() => {
  // xDomain(현재 보이는 시간 범위)에 해당하는 데이터만 필터링
  const [xMin, xMax] = xDomain;
  const visibleData = formattedData.filter(d => d.time >= xMin && d.time <= xMax);

  // 보이는 영역의 가격 기준으로 Y축 범위 계산
  const prices = visibleData.flatMap(d => [d.open, d.high, d.low, d.close]);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1;

  return [Math.floor(minPrice - padding), Math.ceil(maxPrice + padding)];
}, [formattedData, xDomain]);
```

#### 3. displayData 로직 제거 및 디버그 로그 정리
```typescript
// ✅ displayData 계산 로직 제거하고 디버그용 로그만 유지
useEffect(() => {
  if (formattedData.length > 0 && viewWindow) {
    console.log('📊 Chart State:', {
      totalCandles: formattedData.length,
      viewWindow,
      xDomain: [new Date(xDomain[0]).toLocaleTimeString(), new Date(xDomain[1]).toLocaleTimeString()],
      firstCandle: new Date(formattedData[0].time).toLocaleTimeString(),
      lastCandle: new Date(formattedData[formattedData.length - 1].time).toLocaleTimeString(),
    });
  }
}, [formattedData.length, viewWindow, xDomain, formattedData]);
```

#### 4. Brush 컴포넌트 업데이트
```typescript
// ✅ Brush도 전체 데이터 기준으로 업데이트
<Brush
  data={formattedData}  // ✅ 전체 데이터
  dataKey="time"
  height={30}
  stroke={KOREAN_CHART_THEME.gridColor}
  fill={KOREAN_CHART_THEME.backgroundColor}
  startIndex={viewWindow?.startIndex ?? Math.max(0, formattedData.length - 120)}
  endIndex={viewWindow?.endIndex ?? formattedData.length - 1}
  onChange={(brushData: any) => {
    // Brush 변경 시 viewWindow 업데이트
    const { startIndex, endIndex } = brushData;
    onBrushChange({ startIndex: startIndex ?? 0, endIndex: endIndex ?? formattedData.length - 1 });
  }}
/>
```

---

## 🎯 동작 원리

### Before (문제 상황)
```
formattedData (391개)
  ↓ slice(271, 391)
displayData (120개)
  ↓
ComposedChart
  ↓
좌측 드래그 시: index 0 이전의 데이터 없음 → 캔들 안 그려짐
```

### After (수정 후)
```
formattedData (391개)
  ↓ (전체 전달)
ComposedChart
  ↓
xDomain으로 표시 영역 제어 (120분 영역)
  ↓
좌측 드래그 시:
  - viewWindow.startIndex -= deltaCandles
  - xDomain 업데이트 (시작 시간 = formattedData[startIndex].time)
  - index 0부터 모든 과거 데이터 접근 가능 ✅
```

---

## 📊 핵심 개념

### 1. 데이터 vs 뷰 영역 분리
- **전체 데이터**: `formattedData` (391개) → 차트에 모두 전달
- **표시 영역**: `xDomain` (120분 범위) → X축으로 제어
- **좌측 드래그**: `viewWindow.startIndex` 감소 → xDomain 이동

### 2. X축 Domain 기반 렌더링
```typescript
// X축 domain: 현재 보이는 시간 범위 (항상 120분)
const xDomain = useMemo(() => {
  if (viewWindow) {
    const startTime = new Date(formattedData[viewWindow.startIndex].time).getTime();
    const endTime = startTime + (120 * 60 * 1000); // 120분 후
    return [startTime, endTime];
  }

  // 기본: 마지막 120분
  const lastTime = new Date(formattedData[formattedData.length - 1].time).getTime();
  const startTime = lastTime - (120 * 60 * 1000);
  return [startTime, lastTime];
}, [formattedData, viewWindow]);
```

### 3. Y축 Dynamic Scaling
- 현재 보이는 영역(xDomain)의 가격만 기준으로 Y축 범위 계산
- 드래그 시 자동으로 적절한 Y축 스케일 조정
- 패딩 10% 추가로 여유 공간 확보

---

## 🧪 테스트 방법

### 1. 차트 초기 로드
- http://localhost:9000/test-chart 접속
- 마지막 120분봉 (최근 2시간) 표시 확인
- 총 391개 분봉 로드 확인 (콘솔 로그)

### 2. 좌측 드래그 테스트
```
초기 상태: 13:30 ~ 15:30 표시 (마지막 120분)
  ↓ 좌측 드래그
11:30 ~ 13:30 표시
  ↓ 좌측 드래그
09:30 ~ 11:30 표시
  ↓ 좌측 드래그
09:00 ~ 11:00 표시 (시작점 도달)
```

### 3. 브러시 스크롤 테스트
- 하단 브러시 바를 좌우로 드래그
- 전체 391개 분봉 범위에서 자유롭게 이동 가능
- 120분 영역이 브러시 위치에 따라 이동

### 4. Y축 스케일 테스트
- 드래그하며 가격 범위 변화 확인
- Y축이 현재 보이는 영역의 최고/최저가에 맞춰 자동 조정
- 패딩 10%로 캔들이 화면 상하단에 닿지 않음

---

## 📝 변경된 파일

### stock-trading-ui/src/components/trading/chart-adapters/RechartsAdapter.tsx
- Line 259-271: `displayData` 계산 로직 제거, 디버그 로그로 대체
- Line 352-378: `yDomain` 계산을 현재 보이는 영역 기준으로 변경
- Line 397: `data={displayData}` → `data={formattedData}` 변경
- Line 446: CandlestickDot에 `formattedData.length` 전달
- Line 453: Brush에 `formattedData` 전달
- Line 458-459: Brush의 startIndex/endIndex를 viewWindow 기준으로 업데이트

---

## ✨ 개선 효과

### Before
- ❌ 최근 120분만 조회 가능
- ❌ 좌측 드래그 시 빈 화면
- ❌ 전체 데이터 탐색 불가

### After
- ✅ 전체 391분봉 조회 가능 (09:00~15:30)
- ✅ 좌측 드래그로 과거 데이터 탐색
- ✅ 브러시로 빠른 구간 이동
- ✅ Y축 자동 스케일링으로 최적 가시성

---

## 🔮 추가 개선 가능 사항

### 1. 성능 최적화
- 현재: 391개 전체를 Recharts에 전달
- 개선: Virtual Scrolling으로 보이는 영역 ±20개만 렌더링

### 2. 키보드 네비게이션
- 좌우 화살표로 10분씩 이동
- PageUp/PageDown으로 1시간씩 이동
- Home/End로 시작/끝 이동

### 3. 줌 기능
- 마우스 휠로 줌 인/아웃
- 핀치 제스처 지원 (모바일)

### 4. 멀티 타임프레임 지원
- 현재: 120분 고정
- 개선: 30분/60분/120분/240분 선택 가능

---

## 📚 관련 문서
- [Full Day Chart Strategy](../arch/full-day-chart-strategy.md)
- [Chart Infinite Scroll Implementation](../arch/chart-infinite-scroll-implementation-summary.md)
- [Recharts Implementation](rechart.impl.drag.data.0930.md)

---

**수정일**: 2025-10-02
**작성자**: Claude Code (with Chrome MCP analysis)
