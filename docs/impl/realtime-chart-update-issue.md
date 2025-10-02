# 실시간 차트 갱신 문제 진단

## 🔍 문제 현상
- **증상**: 차트가 매분 자동으로 갱신되지 않음
- **위치**: `/app/echart/page.tsx` (InfiniteScrollCandlestickChart 사용)
- **예상 동작**: 1분마다 새로운 캔들 데이터 자동 추가

---

## 🐛 근본 원인 분석

### 1. **`useInfiniteChartData` 훅 분석**

#### ❌ 실시간 갱신 로직 **부재**
```typescript
// hooks/useInfiniteChartData.ts
export function useInfiniteChartData(options: UseInfiniteChartDataOptions) {
  // ✅ 초기 데이터 로드: loadInitialData()
  // ✅ 이전 날짜 로드: loadPreviousDay()
  // ✅ 다음 날짜 로드: loadNextDay()
  
  // ❌ 실시간 폴링/WebSocket 로직 없음
  // ❌ setInterval 없음
  // ❌ auto-refresh 옵션 없음
}
```

**문제점**:
- 초기 로드 후 더 이상 데이터를 갱신하지 않음
- `refresh()` 함수는 있지만 **자동으로 호출되지 않음**
- Brush 드래그로만 이전 데이터 로드 (실시간 X)

### 2. **`useRealChartData` 훅과의 비교**

#### ✅ `useRealChartData` (실시간 갱신 O)
```typescript
// hooks/useRealChartData.ts:202-216
useEffect(() => {
  if (!autoRefresh || !enabled || !stockCode) {
    return;
  }

  const intervalId = setInterval(() => {
    console.log(`🔄 Auto-refreshing chart data for ${stockCode}`);
    fetchChartData();  // ✅ 자동 갱신
  }, refreshInterval);

  return () => {
    clearInterval(intervalId);
  };
}, [autoRefresh, enabled, stockCode, refreshInterval, fetchChartData]);
```

**특징**:
- ✅ `autoRefresh` 옵션 지원
- ✅ `refreshInterval` 설정 (기본 5초)
- ✅ setInterval로 자동 폴링

#### ❌ `useInfiniteChartData` (실시간 갱신 X)
```typescript
// hooks/useInfiniteChartData.ts
// ❌ autoRefresh 옵션 없음
// ❌ setInterval 로직 없음
// ❌ 자동 갱신 메커니즘 없음
```

### 3. **현재 페이지 사용 현황**

#### `/app/echart/page.tsx`
```typescript
<InfiniteScrollCandlestickChart
  stockCode="005930"
  height={500}
  timeframe="1m"
  chartLibrary="recharts"
  maxDays={5}
  loadThreshold={20}
/>
```

**분석**:
- ❌ `autoRefresh` prop 없음
- ❌ `refreshInterval` prop 없음
- ✅ `useInfiniteChartData` 사용 (실시간 갱신 기능 없음)

---

## 📊 데이터 흐름 분석

### 현재 흐름 (실시간 X)
```
1. [초기 마운트]
   └─> useInfiniteChartData.loadInitialData()
       └─> chartAPI.getFullDayCandles() 
           └─> 391개 캔들 (9:00~15:30 Full Day)

2. [Brush 드래그 (좌측)]
   └─> handleBrushChange()
       └─> useInfiniteChartData.loadPreviousDay()
           └─> 이전 날짜 데이터 로드

3. [실시간 갱신] 
   └─> ❌ 없음! 수동으로 새로고침해야 함
```

### 필요한 흐름 (실시간 O)
```
1. [초기 마운트]
   └─> Full Day 데이터 로드 (391개)

2. [1분 간격 폴링]
   └─> setInterval(() => {
         if (현재 시각이 장중) {
           fetchLatestCandles()  // 최신 1~2개 캔들만
           또는
           chartAPI.getFullDayCandles()  // 전체 재조회
         }
       }, 60000)  // 1분마다

3. [Gap 자동 채우기]
   └─> Backend Gap-fill 로직이 자동으로 처리
```

---

## 💡 해결 방안

### Option 1: `useInfiniteChartData`에 실시간 폴링 추가 (권장)
```typescript
// hooks/useInfiniteChartData.ts
export interface UseInfiniteChartDataOptions {
  // ... 기존 옵션
  autoRefresh?: boolean;        // 🆕 자동 갱신 활성화
  refreshInterval?: number;     // 🆕 갱신 간격 (ms)
}

export function useInfiniteChartData(options) {
  // ... 기존 로직

  // 🆕 실시간 폴링 로직
  useEffect(() => {
    if (!autoRefresh || !enabled) return;

    const intervalId = setInterval(async () => {
      console.log('[InfiniteScroll] Auto-refreshing latest candles');
      
      // 현재 날짜 데이터 재조회 (Gap-fill 자동 적용)
      const latestData = await chartAPI.getFullDayCandles(
        stockCode, 
        currentDateRange.end
      );
      
      // 캔들 업데이트 (기존 + 새 데이터 병합)
      setCandles(prev => mergeCandles(prev, latestData));
    }, refreshInterval);

    return () => clearInterval(intervalId);
  }, [autoRefresh, refreshInterval, stockCode, currentDateRange.end]);
}
```

### Option 2: `useRealChartData` 훅 사용
```typescript
// echart/page.tsx
// ❌ 현재
<InfiniteScrollCandlestickChart ... />

// ✅ 변경
const { chartData, refetch } = useRealChartData('005930', '1m', {
  autoRefresh: true,
  refreshInterval: 60000  // 1분
});

<RechartsAdapter data={chartData} ... />
```

### Option 3: 컴포넌트 레벨에서 폴링 추가
```typescript
// InfiniteScrollCandlestickChart.tsx
useEffect(() => {
  if (timeframe !== '1m') return;

  const intervalId = setInterval(() => {
    console.log('[InfiniteScroll] Refreshing chart data');
    refresh();  // useInfiniteChartData의 refresh 호출
  }, 60000);

  return () => clearInterval(intervalId);
}, [timeframe, refresh]);
```

---

## ✅ 추천 구현 계획

### Step 1: `useInfiniteChartData`에 실시간 폴링 추가
```typescript
// 1. Options 인터페이스에 추가
autoRefresh?: boolean;
refreshInterval?: number;  // 기본값: 60000 (1분)

// 2. useEffect로 폴링 로직 구현
useEffect(() => {
  if (!autoRefresh) return;
  
  const poll = setInterval(async () => {
    // 현재 날짜의 최신 데이터 재조회 (Backend Gap-fill 적용)
    const latest = await chartAPI.getFullDayCandles(
      stockCode, 
      currentDateRange.end
    );
    
    // 병합 (중복 제거 + 시간순 정렬)
    setCandles(prev => {
      const merged = [...prev, ...latest];
      const unique = Array.from(
        new Map(merged.map(c => [c.timestamp, c])).values()
      );
      return sortCandles(unique);
    });
  }, refreshInterval);

  return () => clearInterval(poll);
}, [autoRefresh, refreshInterval, stockCode, currentDateRange.end]);
```

### Step 2: 페이지에서 옵션 활성화
```typescript
// app/echart/page.tsx
<InfiniteScrollCandlestickChart
  stockCode="005930"
  height={500}
  timeframe="1m"
  chartLibrary="recharts"
  maxDays={5}
  loadThreshold={20}
  autoRefresh={true}          // 🆕
  refreshInterval={60000}     // 🆕 1분마다
/>
```

### Step 3: Backend Gap-fill 활용
- ✅ Backend가 자동으로 Gap 감지 및 채우기
- ✅ Frontend는 단순히 재조회만 하면 됨
- ✅ 중복 제거는 Frontend에서 처리 (timestamp 기준)

---

## 🎯 예상 효과

### Before (현재)
- ❌ 차트 정적 (새로고침 필요)
- ❌ Gap 발생 시 누락
- ❌ 실시간성 없음

### After (수정 후)
- ✅ 매분 자동 갱신
- ✅ Backend Gap-fill로 누락 방지
- ✅ 실시간 트레이딩 가능
- ✅ 51.9% API 효율화 (Gap-only query)

---

## 📋 구현 우선순위

1. **High**: `useInfiniteChartData`에 실시간 폴링 추가
2. **Medium**: 폴링 간격 최적화 (1분 → 30초?)
3. **Low**: WebSocket 실시간 스트리밍 (추후)

**다음 단계**: `useInfiniteChartData.ts` 수정 시작
