# lightweight-charts SSR 호환성 문제 해결 기록

**작업 일시**: 2025-09-29
**작업자**: Claude
**이슈**: Next.js 15에서 lightweight-charts 라이브러리 SSR 충돌

---

## 🚨 발생한 문제

### 증상
- **URL**: http://localhost:9000/test-chart
- **에러 메시지**:
  ```
  Runtime TypeError: chart.addCandlestickSeries is not a function
  ```
- **발생 위치**: `src/components/trading/RealtimeCandlestickChart.tsx:41:37`

### 원인 분석
1. **lightweight-charts@5.0.8**은 브라우저 전용 라이브러리
2. Next.js의 **Server-Side Rendering(SSR)** 과정에서 서버에서 차트 라이브러리 로드 시도
3. 서버 환경에서는 `createChart` 함수가 존재하지 않아 `undefined` 반환
4. `chart.addCandlestickSeries()` 호출 시 함수가 아니므로 에러 발생

---

## 🔧 해결 방법

### 전략: Next.js Dynamic Import + SSR 비활성화

Next.js의 `dynamic()` 함수를 사용하여 클라이언트에서만 차트 라이브러리를 로드하도록 변경

### 구현 내용

#### 1. 기존 컴포넌트 분리
- **래퍼 컴포넌트**: `RealtimeCandlestickChart.tsx` (SSR 안전)
- **핵심 로직**: `LightweightChartCore.tsx` (클라이언트 전용)

#### 2. 동적 임포트 적용
```typescript
const LightweightChart = dynamic(
  () => import('./LightweightChartCore'),
  {
    ssr: false,  // 서버사이드 렌더링 비활성화
    loading: () => <ChartLoadingFallback height={400} />,
  }
);
```

#### 3. 사용자 경험 개선
- **로딩 상태**: 차트 로드 중 스피너와 안내 메시지 표시
- **에러 처리**: 차트 로드 실패 시 사용자 친화적 메시지 표시
- **반응형**: 화면 크기에 따른 차트 리사이징

---

## 📁 수정된 파일들

### 1. `/src/components/trading/RealtimeCandlestickChart.tsx` (수정)
```typescript
'use client';

import React, { memo } from 'react';
import dynamic from 'next/dynamic';

// 로딩 화면 컴포넌트
const ChartLoadingFallback = ({ height }) => (
  <div className="bg-[#0a0a0b] border border-gray-700 rounded-lg flex items-center justify-center" style={{ height }}>
    <div className="flex items-center gap-2 text-gray-400">
      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
      <span>차트 로딩 중...</span>
    </div>
  </div>
);

// 동적 임포트 (SSR 비활성화)
const LightweightChart = dynamic(
  () => import('./LightweightChartCore'),
  { ssr: false, loading: () => <ChartLoadingFallback height={400} /> }
);

const RealtimeCandlestickChart = memo(({ chartData, height = 400 }) => {
  const [hasError, setHasError] = useState(false);

  if (hasError) {
    return <ChartErrorFallback height={height} />;
  }

  return (
    <React.Suspense fallback={<ChartLoadingFallback height={height} />}>
      <LightweightChart
        chartData={chartData}
        height={height}
        onError={setHasError}
      />
    </React.Suspense>
  );
});
```

### 2. `/src/components/trading/LightweightChartCore.tsx` (신규 생성)
- 기존 차트 로직을 클라이언트 전용 컴포넌트로 분리
- 라이브러리 동적 로딩 및 에러 처리
- 한국 증시 색상 규칙 적용 (상승: 빨강, 하락: 파랑)

---

## ✅ 해결 결과

### Before (문제 상황)
- ❌ 서버 시작 시 SSR 에러 발생
- ❌ 차트 페이지 접근 불가
- ❌ `addCandlestickSeries is not a function` 에러

### After (해결 후)
- ✅ 서버 정상 시작 (SSR 에러 없음)
- ✅ 차트 페이지 정상 접근 가능
- ✅ 차트 정상 렌더링
- ✅ 로딩 상태 표시
- ✅ 에러 상황 처리

---

## 📚 학습 포인트

### 1. Next.js에서 브라우저 전용 라이브러리 사용법
```typescript
// ❌ 잘못된 방법
import { createChart } from 'lightweight-charts';

// ✅ 올바른 방법
const Chart = dynamic(() => import('./ChartComponent'), { ssr: false });
```

### 2. 유사한 문제가 발생할 수 있는 라이브러리들
- Chart.js
- D3.js
- Plotly.js
- Three.js
- 기타 DOM/Canvas 조작 라이브러리들

### 3. 사용자 경험 고려사항
- 로딩 상태 표시
- 에러 상황 처리
- 반응형 디자인
- 접근성 고려

---

## 🔍 향후 개선 사항

1. **차트 데이터 캐싱**: 불필요한 리렌더링 방지
2. **차트 테마 시스템**: 다크/라이트 모드 지원
3. **성능 최적화**: 대용량 데이터 처리 개선
4. **접근성**: 스크린 리더 지원

---

## 📞 참고 자료

- [Next.js Dynamic Imports](https://nextjs.org/docs/advanced-features/dynamic-import)
- [lightweight-charts Documentation](https://tradingview.github.io/lightweight-charts/)
- [React Suspense](https://react.dev/reference/react/Suspense)

---

**종료 시간**: 2025-09-29 12:14
**테스트 결과**: ✅ 정상 작동 확인