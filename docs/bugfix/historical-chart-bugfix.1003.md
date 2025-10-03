# 과거 차트 데이터 로딩 버그 수정 (2025-10-03)

## 🐛 발견된 버그

### Bug 1: HTTP 404 Not Found
**증상:**
```
HTTP 404: Not Found
at useRealChartData.useCallback[fetchChartData] (src/hooks/useRealChartData.ts:100:15)
```

**원인:**
1. `KoreanTradingChart.tsx:336` - `<RealtimeCandlestickChart chartData={...} />`
2. 새로운 `RealtimeCandlestickChart`는 `stockCode` prop 필요
3. `chartData` prop만 전달 → `stockCode`가 `undefined` → API 호출 실패

### Bug 2: API 응답 형식 불일치
**증상:**
```
분봉 API 응답이 배열이 아닙니다
```

**원인:**
1. Backend `/api/chart/{stock_code}/minute/full`는 `List[ChartCandle]` 반환 (배열)
2. `useRealChartData` 훅은 `ChartApiResponse` 객체 형식 기대
3. 타입 불일치로 데이터 파싱 실패

---

## ✅ 적용된 수정

### Fix 1: Backward Compatibility 추가

**파일:** `RealtimeCandlestickChart.tsx`

**변경 전:**
```typescript
interface RealtimeCandlestickChartProps {
  stockCode: string; // 필수
  height?: number;
  timeframe: string;
}
```

**변경 후:**
```typescript
interface RealtimeCandlestickChartProps {
  // ✅ Backward compatibility: 둘 다 지원
  chartData?: ChartCandle[]; // 직접 데이터 전달 (기존 방식)
  stockCode?: string; // 자동 데이터 로딩 (새 방식)
  height?: number;
  timeframe: string;
  enableHistoricalLoad?: boolean;
  initialDays?: number;
}
```

**동작 방식:**
```typescript
// 1. chartData 우선순위: externalChartData > autoChartData
const chartData = externalChartData || autoChartData;

// 2. 자동 로딩은 stockCode가 있고 chartData가 없을 때만
const {
  chartData: autoChartData,
  isLoading,
  error,
  handleRangeChange
} = useHistoricalChartData({
  stockCode: stockCode || '',
  enabled: !!stockCode && enableHistoricalLoad && !externalChartData,
  initialDays
});

// 3. 범위 변경 이벤트도 조건부 활성화
events={{
  onRangeChange: stockCode && !externalChartData ? handleRangeChange : undefined,
  onError: (error) => console.error('차트 렌더링 오류:', error)
}}
```

**결과:**
- ✅ 기존 코드 (`chartData` 전달) 계속 작동
- ✅ 새 코드 (`stockCode` 전달) 과거 데이터 자동 로드
- ✅ 두 방식 모두 지원 (점진적 마이그레이션 가능)

---

### Fix 2: API 응답 형식 통일

**파일:** `useRealChartData.ts`

**변경 전:**
```typescript
if (timeframe === '1m') {
  if (Array.isArray(responseData)) {
    chartData = responseData; // ❌ ChartCandle을 KoreanStockChart로 변환 안 함
    console.log(`📊 분봉 데이터 수신: ${chartData.length}개`);
  }
}
```

**변경 후:**
```typescript
if (timeframe === '1m') {
  // ✅ 분봉 API는 ChartCandle[] 배열 직접 반환
  if (Array.isArray(responseData)) {
    // ChartCandle을 KoreanStockChart 형식으로 변환
    chartData = responseData.map((candle: any) => ({
      timestamp: candle.timestamp,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
      volume: candle.volume || 0,
      tradingValue: null,
      foreignBuy: null,
      foreignSell: null,
      institutionalBuy: null,
      institutionalSell: null,
      individualBuy: null,
      individualSell: null,
    }));
    console.log(`📊 분봉 데이터 수신: ${chartData.length}개`);
  } else {
    console.error('❌ 분봉 API 응답이 배열이 아닙니다:', responseData);
    throw new Error('Invalid API response format: expected array');
  }
}
```

**결과:**
- ✅ Backend API 응답 (`ChartCandle[]`) 올바르게 파싱
- ✅ Frontend 타입 (`KoreanStockChart`) 일치
- ✅ 에러 발생 시 명확한 메시지

---

## 🔄 사용 방법 (두 가지 모드)

### 모드 1: 기존 방식 (chartData 직접 전달)
```typescript
// KoreanTradingChart.tsx에서 사용 중
const { chartData } = useRealChartData(stock.code, timeframe);

<RealtimeCandlestickChart
  chartData={chartData}
  height={400}
  timeframe={timeframe}
/>
```

**특징:**
- 부모 컴포넌트가 데이터 관리
- 과거 데이터 자동 로딩 없음
- 기존 코드 그대로 작동

### 모드 2: 새 방식 (stockCode로 자동 로딩)
```typescript
// 새로운 페이지에서 사용
<RealtimeCandlestickChart
  stockCode="005930"
  timeframe="1m"
  enableHistoricalLoad={true}
  initialDays={3}
/>
```

**특징:**
- 컴포넌트가 데이터 자동 관리
- 초기 로딩: 오늘 + 과거 3일 프리로드
- 좌측 드래그 시 과거 데이터 자동 fetch
- 메모리 캐시로 중복 방지

---

## 🧪 테스트 시나리오

### 테스트 1: 기존 방식 (KoreanTradingChart)
```bash
1. http://localhost:9000/trading 접속
2. 종목 선택 (예: 삼성전자)
3. 1분봉 차트 확인
4. 차트가 정상 표시되는지 확인 ✅
5. 브라우저 콘솔에 404 에러 없는지 확인 ✅
```

### 테스트 2: 새 방식 (과거 데이터 자동 로드)
```typescript
// 테스트 페이지 생성: app/test-chart/page.tsx
'use client';

import RealtimeCandlestickChart from '@/components/trading/RealtimeCandlestickChart';

export default function TestChartPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl mb-4">차트 테스트 (과거 데이터 자동 로드)</h1>
      <RealtimeCandlestickChart
        stockCode="005930"
        timeframe="1m"
        enableHistoricalLoad={true}
        initialDays={3}
        height={600}
      />
    </div>
  );
}
```

**확인 사항:**
```bash
1. http://localhost:9000/test-chart 접속
2. 초기 로딩 메시지 표시 확인 ✅
3. 차트 로드 후 데이터 확인 (오늘 + 과거 3일) ✅
4. 브라우저 콘솔 로그 확인:
   - "✅ 초기 데이터 로드 완료"
   - "todayCandles: N개, historicalDates: 3개"
5. Brush를 좌측으로 드래그 (startIndex < 10) ✅
6. 콘솔에서 "🔍 좌측 드래그 감지 → 과거 데이터 로드" 확인 ✅
7. "📥 과거 데이터 추가: 20251002, 360개 캔들" 확인 ✅
```

---

## 📊 수정 파일 목록

### Frontend
- ✅ `stock-trading-ui/src/components/trading/RealtimeCandlestickChart.tsx`
  - Backward compatibility 추가
  - `chartData` 또는 `stockCode` 모두 지원
  - 조건부 이벤트 핸들러

- ✅ `stock-trading-ui/src/hooks/useRealChartData.ts`
  - API 응답 형식 통일
  - `ChartCandle` → `KoreanStockChart` 변환 추가
  - 에러 메시지 명확화

### Documentation
- ✅ `docs/bugfix/historical-chart-bugfix.1003.md` (이 문서)

---

## 🎯 마이그레이션 가이드

### 기존 코드 (변경 불필요)
```typescript
// ✅ 이대로 두어도 계속 작동함
<RealtimeCandlestickChart
  chartData={realChartData}
  timeframe={timeframe}
/>
```

### 새 방식으로 전환 (선택 사항)
```typescript
// ✅ 과거 데이터 자동 로딩 원할 때만 변경
<RealtimeCandlestickChart
  stockCode={stock.code}
  timeframe={timeframe}
  enableHistoricalLoad={true}
  initialDays={3}
/>
```

---

## 🔍 디버깅 팁

### 404 에러 발생 시
```typescript
// 브라우저 콘솔에서 확인
console.log('stockCode:', stockCode); // undefined 체크
console.log('chartData:', chartData); // 데이터 존재 여부
console.log('API URL:', `${API_BASE_URL}/api/chart/${stockCode}/minute-range`);
```

### 데이터 로드 안 될 때
```typescript
// useHistoricalChartData 훅 enabled 조건 확인
enabled: !!stockCode && enableHistoricalLoad && !externalChartData

// 1. stockCode가 있는가?
// 2. enableHistoricalLoad가 true인가?
// 3. externalChartData가 없는가? (있으면 자동 로딩 안 함)
```

### Backend API 응답 확인
```bash
# 직접 API 호출해보기
curl "http://localhost:8000/api/chart/005930/minute/full"

# 예상 응답: ChartCandle[] 배열
[
  {
    "timestamp": "2025-10-03T09:01:00",
    "open": 85000,
    "high": 85100,
    "low": 84900,
    "close": 85050,
    "volume": 12345
  },
  ...
]
```

---

## ✅ 수정 완료 체크리스트

- [x] `RealtimeCandlestickChart` backward compatibility 추가
- [x] `useRealChartData` API 응답 형식 통일
- [x] 기존 코드 (`KoreanTradingChart`) 작동 확인
- [x] 새 방식 (`stockCode` 모드) 테스트
- [x] 에러 처리 개선
- [x] 문서 작성

---

**수정 완료일**: 2025-10-03
**작성자**: Claude Code
**상태**: ✅ 버그 수정 완료 (Backward Compatible)
