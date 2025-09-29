# ECharts를 이용한 차트 구현 방안

## 1. 개요

현재 `lightweight-charts` 라이브러리 사용 시 발생하는 지속적인 렌더링 오류(`addCandlestickSeries is not a function`)를 해결하기 위한 대안으로, Apache ECharts 라이브러리 도입을 제안합니다.

ECharts는 다양한 차트를 지원하고, 대규모 데이터 처리 성능이 뛰어나며, React 환경과 안정적으로 통합할 수 있는 공식 래퍼 라이브러리(`echarts-for-react`)를 제공하여 현재 겪고 있는 문제를 해결할 수 있습니다.

## 2. 필요 라이브러리 설치

프론트엔드 프로젝트(`stock-trading-ui`)에 다음 두 가지 라이브러리를 설치해야 합니다.

```bash
npm install echarts echarts-for-react
```

## 3. 구현 설계

### 3.1. 신규 차트 컴포넌트 생성

기존 `RealtimeCandlestickChart.tsx`를 대체할 `EChartsCandlestickChart.tsx` 컴포넌트를 새로 생성합니다. 이 컴포넌트는 `echarts-for-react`의 `ReactECharts` 컴포넌트를 사용하여 차트를 렌더링합니다.

### 3.2. 데이터 변환

ECharts의 캔들스틱 차트는 `[시가, 종가, 저가, 고가]` 순서의 숫자 배열로 데이터를 받습니다. 따라서 부모 컴포넌트로부터 받은 `chartData` prop을 ECharts 형식에 맞게 변환하는 로직이 필요합니다.

**원본 데이터 형식 (`ChartCandle`):**
```typescript
{
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
```

**ECharts 필요 형식:**
```typescript
[
  [open, close, low, high], // 예: [20, 34, 10, 38]
  ...
]
```

### 3.3. ECharts 옵션 객체 구성

ECharts의 모든 시각적 요소와 동작은 하나의 거대한 `option` 객체를 통해 제어됩니다. 이 객체 안에 다음 내용을 설정합니다.

- **`xAxis`**: 시간 축을 설정합니다. (타임스탬프 데이터)
- **`yAxis`**: 가격 축을 설정합니다.
- **`series`**: 차트의 종류를 `candlestick`으로 지정하고, 변환된 데이터를 할당합니다.
- **`grid`**: 차트의 위치와 크기를 조정합니다.
- **`tooltip`**: 마우스를 올렸을 때 표시될 정보 창을 설정합니다.
- **`dataZoom`**: 차트를 확대/축소할 수 있는 슬라이더를 추가합니다.
- **스타일링**: 애플리케이션의 다크 테마에 맞게 배경색, 폰트 색상, 캔들 색상 등을 설정합니다.

## 4. 예제 코드 (`EChartsCandlestickChart.tsx`)

아래는 `echarts-for-react`를 사용하여 작성할 차트 컴포넌트의 하이레벨 예제 코드입니다.

```typescript
// src/components/trading/EChartsCandlestickChart.tsx

'use client';

import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { ChartCandle } from '@/lib/types/korean-stocks';

interface EChartsCandlestickChartProps {
  chartData: ChartCandle[];
  height?: number;
}

const EChartsCandlestickChart: React.FC<EChartsCandlestickChartProps> = ({ chartData, height = 400 }) => {

  const echartOptions = useMemo(() => {
    // 1. 데이터 변환
    const data = chartData.map(candle => [
      candle.open,
      candle.close,
      candle.low,
      candle.high,
    ]);

    const timestamps = chartData.map(candle => {
        const d = new Date(candle.timestamp);
        return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`;
    });

    // 2. ECharts 옵션 객체 생성
    return {
      backgroundColor: '#1a1a1b', // 다크 테마 배경색
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: '#2a2a2a',
        borderColor: '#555',
        textStyle: { color: '#D1D4DC' },
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLine: { lineStyle: { color: '#555' } },
        axisLabel: { color: '#D1D4DC' },
      },
      yAxis: {
        scale: true,
        axisLine: { show: false },
        axisLabel: { color: '#D1D4DC' },
        splitLine: { lineStyle: { color: '#2B2B43' } },
      },
      grid: {
        left: '50px',
        right: '20px',
        top: '20px',
        bottom: '50px',
      },
      dataZoom: [
        {
          type: 'inside',
          start: 50,
          end: 100,
        },
        {
          show: true,
          type: 'slider',
          bottom: 10,
          start: 50,
          end: 100,
          backgroundColor: '#2a2a2a',
          borderColor: '#555',
          dataBackground: {
              lineStyle: {color: '#D1D4DC'},
              areaStyle: {color: '#555'}
          },
          selectedDataBackground: {
              lineStyle: {color: '#26A69A'},
              areaStyle: {color: '#26A69A'}
          },
          textStyle: { color: '#D1D4DC' },
        },
      ],
      series: [
        {
          type: 'candlestick',
          data: data,
          itemStyle: {
            color: '#EF5350', // 상승 (Red)
            color0: '#26A69A', // 하락 (Green/Blue)
            borderColor: '#EF5350',
            borderColor0: '#26A69A',
          },
        },
      ],
    };
  }, [chartData]);

  return (
    <ReactECharts
      option={echartOptions}
      style={{ height: height, width: '100%' }}
      notMerge={true}
      lazyUpdate={true}
      theme={"dark"}
    />
  );
};

export default EChartsCandlestickChart;
```

## 5. 기존 코드 수정

위 `EChartsCandlestickChart` 컴포넌트를 구현한 후, `KoreanTradingChart.tsx` 파일에서 기존 `RealtimeCandlestickChart`를 호출하던 부분을 새로운 `EChartsCandlestickChart`로 교체해야 합니다.

```typescript
// KoreanTradingChart.tsx 에서의 변경 예시

// import RealtimeCandlestickChart from './RealtimeCandlestickChart';
import EChartsCandlestickChart from './EChartsCandlestickChart';

// ... 컴포넌트 내부 ...

{useRealData && timeframe === '1m' ? (
  // <RealtimeCandlestickChart chartData={realChartData} height={height - 100} />
  <EChartsCandlestickChart chartData={realChartData} height={height - 100} />
) : (
  // ...
)}
```
