# 주식 캔들 차트 구현 가이드

이 문서는 프론트엔드 개발자가 한국투자증권 API(`KIS-05: 기간별 시세 조회`)를 사용하여 웹 애플리케이션에 주식 캔들 차트를 구현하는 방법을 단계별로 안내합니다.

## 최종 목표

- **API 연동**: 백엔드에서 제공하는 `KIS-05` API를 호출하여 특정 종목의 기간별 시세 데이터를 가져옵니다.
- **데이터 변환**: API 응답 데이터를 차트 라이브러리가 요구하는 형식으로 변환합니다.
- **차트 시각화**: 변환된 데이터를 사용하여 캔들스틱 차트와 거래량 차트를 화면에 렌더링합니다.

---

## Step 1: 차트 라이브러리 선정 및 설치

금융 데이터 시각화에는 전문 라이브러리를 사용하는 것이 효율적입니다. **[TradingView Lightweight Charts™](https://www.tradingview.com/lightweight-charts/)**는 실시간 금융 차트에 최적화되어 있으며, 가볍고 강력한 기능을 제공합니다.

### 설치
Next.js 또는 React 프로젝트에서 아래 명령어로 라이브러리를 설치합니다.

```bash
npm install lightweight-charts
```

---

## Step 2: 백엔드 API 분석 (`KIS-05`)

`docs/KIS-API/api-list.md`에 명시된 **KIS-05: 기간별 시세 조회** API를 사용하여 차트 데이터를 가져옵니다.

- **URL**: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`
- **핵심 요청 파라미터**:
  - `FID_INPUT_ISCD`: 종목 코드 (예: "005930")
  - `FID_INPUT_DATE_1`: 조회 시작일 (예: "20240101")
  - `FID_INPUT_DATE_2`: 조회 종료일 (예: "20240331")
  - `FID_PERIOD_DIV_CODE`: 기간 구분 (D: 일, W: 주, M: 월)
- **핵심 응답 데이터**: API 응답의 `output2` 배열에 차트 데이터가 포함됩니다.

```json
// API 응답 예시 (output2 부분)
"output2": [
    {
        "stck_bsop_date": "20240329", // 영업일자 (Y-축)
        "stck_oprc": "79800",      // 시가 (Open)
        "stck_hgpr": "80800",      // 고가 (High)
        "stck_lwpr": "79500",      // 저가 (Low)
        "stck_clpr": "80800",      // 종가 (Close)
        "acml_vol": "14789123"     // 누적 거래량 (Volume)
    },
    // ... more data
]
```

---

## Step 3: 데이터 형식 변환

`Lightweight Charts` 라이브러리는 특정 데이터 형식을 요구합니다. API 응답(`output2`)을 아래와 같은 형식의 배열로 변환해야 합니다.

- **캔들스틱 데이터**: `{ time, open, high, low, close }`
- **거래량 데이터**: `{ time, value }`

### 변환 함수 예시 (TypeScript)

```typescript
// API 원본 데이터 타입 (예시)
interface KisChartItem {
  stck_bsop_date: string; // "20240329"
  stck_oprc: string;
  stck_hgpr: string;
  stck_lwpr: string;
  stck_clpr: string;
  acml_vol: string;
}

// Lightweight Charts가 요구하는 데이터 타입
export interface CandlestickData {
  time: string; // "2024-03-29"
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface VolumeData {
  time: string; // "2024-03-29"
  value: number;
}

// 변환 로직
export const transformKisData = (items: KisChartItem[]) => {
  const candlestickData: CandlestickData[] = [];
  const volumeData: VolumeData[] = [];

  // KIS API는 과거 데이터가 배열의 뒤에 오므로, 오름차순으로 정렬합니다.
  const sortedItems = items.sort((a, b) => parseInt(a.stck_bsop_date, 10) - parseInt(b.stck_bsop_date, 10));

  sortedItems.forEach(item => {
    const date = item.stck_bsop_date;
    const formattedDate = `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;

    candlestickData.push({
      time: formattedDate,
      open: Number(item.stck_oprc),
      high: Number(item.stck_hgpr),
      low: Number(item.stck_lwpr),
      close: Number(item.stck_clpr),
    });

    volumeData.push({
      time: formattedDate,
      value: Number(item.acml_vol),
    });
  });

  return { candlestickData, volumeData };
};
```

---

## Step 4: 차트 컴포넌트 구현 (React / Next.js)

이제 데이터를 시각화할 React 컴포넌트를 작성합니다.

- **SSR 방지**: 차트 라이브러리는 `window` 객체를 사용하므로, Next.js 환경에서는 클라이언트 사이드에서만 렌더링되어야 합니다. `useEffect`를 사용하여 컴포넌트가 마운트된 후에 차트를 초기화합니다.
- **컴포넌트 구조**:
  1. `useRef`를 사용하여 차트가 렌더링될 DOM 컨테이너를 참조합니다.
  2. `useEffect` 내에서 차트를 생성하고, 시리즈(캔들스틱, 거래량)를 추가합니다.
  3. 컴포넌트가 언마운트될 때 차트 리소스를 정리하는 `cleanup` 함수를 반환합니다.

### `StockChart.tsx` 컴포넌트 예시 (개선)

차트 초기화는 한 번만 실행하고, 데이터가 변경될 때마다 업데이트하는 것이 효율적입니다.

```tsx
'use client';

import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData as LightweightCandlestickData,
  HistogramData,
} from 'lightweight-charts';
import React, { useEffect, useRef } from 'react';

// Props 타입 정의
interface StockChartProps {
  candlestickData: LightweightCandlestickData[];
  volumeData: HistogramData[];
  chartLayout?: {
    backgroundColor?: string;
    textColor?: string;
  };
}

export function StockChart({
  candlestickData,
  volumeData,
  chartLayout = { backgroundColor: '#ffffff', textColor: '#333' },
}: StockChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // 차트 초기화 (최초 1회 실행)
  useEffect(() => {
    if (!chartContainerRef.current) return;

    chartRef.current = createChart(chartContainerRef.current, {
      layout: {
        background: { color: chartLayout.backgroundColor },
        textColor: chartLayout.textColor,
      },
      width: chartContainerRef.current.clientWidth,
      height: 500,
      grid: { vertLines: { color: '#e1e1e1' }, horzLines: { color: '#e1e1e1' } },
      timeScale: { timeVisible: true, secondsVisible: false },
    });

    candlestickSeriesRef.current = chartRef.current.addCandlestickSeries({
      upColor: '#ef5350',
      downColor: '#26a69a',
      borderDownColor: '#26a69a',
      borderUpColor: '#ef5350',
      wickDownColor: '#26a69a',
      wickUpColor: '#ef5350',
    });

    volumeSeriesRef.current = chartRef.current.addHistogramSeries({
      color: '#26a69a',
      priceFormat: { type: 'volume' },
      priceScaleId: '',
    });
    
    const handleResize = () => {
      if (chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current!.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartRef.current?.remove();
      chartRef.current = null;
    };
  }, [chartLayout]); // 레이아웃 변경 시 차트 재생성

  // 데이터 업데이트
  useEffect(() => {
    if (candlestickSeriesRef.current) {
      candlestickSeriesRef.current.setData(candlestickData);
    }
    if (volumeSeriesRef.current) {
      volumeSeriesRef.current.setData(volumeData);
    }
    // 데이터가 로드된 후 차트 뷰를 조정
    if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
    }
  }, [candlestickData, volumeData]);

  return <div ref={chartContainerRef} />;
}
```

---

## Step 5: 페이지에 차트 컴포넌트 및 기간 변경 버튼 적용

이제 `StockChart` 컴포넌트를 페이지에서 사용하고, '일/주/월' 버튼을 추가하여 기간(Period)을 변경하는 기능을 구현합니다.

1.  **기간 상태 관리**: `useState`를 사용하여 현재 선택된 기간(`'D'`, `'W'`, `'M'`)을 저장합니다.
2.  **버튼 UI 추가**: '일', '주', '월' 버튼을 만들고 `onClick` 이벤트에 `setPeriod` 함수를 연결합니다.
3.  **데이터 호출 로직 수정**: `useEffect`의 의존성 배열에 `period`를 추가하여, 기간이 변경될 때마다 API를 다시 호출하도록 합니다. API 호출 URL에 현재 `period` 값을 동적으로 포함시킵니다.

### 페이지 컴포넌트 예시 (`app/stocks/[code]/page.tsx`)

```tsx
'use client';

import { useEffect, useState } from 'react';
import { StockChart } from '@/components/StockChart'; // 위에서 만든 컴포넌트
import { transformKisData, CandlestickData, VolumeData } from '@/lib/dataTransformer'; // 변환 함수

// KIS API 응답 타입
interface KisChartItem {
  stck_bsop_date: string;
  stck_oprc: string;
  stck_hgpr: string;
  stck_lwpr: string;
  stck_clpr: string;
  acml_vol: string;
}

type Period = 'D' | 'W' | 'M';

export default function StockDetailPage({ params }: { params: { code: string } }) {
  const [chartData, setChartData] = useState<{
    candlestickData: CandlestickData[];
    volumeData: VolumeData[];
  }>({ candlestickData: [], volumeData: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState<Period>('D'); // 기간 상태 추가

  useEffect(() => {
    const fetchChartData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // 백엔드 API 엔드포인트를 호출, period 쿼리 파라미터 추가
        const response = await fetch(`/api/stocks/${params.code}/chart?period=${period}`);
        if (!response.ok) {
          throw new Error('Failed to fetch chart data');
        }
        const data = await response.json();
        
        const rawItems: KisChartItem[] = data.output2 || [];
        if (rawItems.length === 0) {
            setChartData({ candlestickData: [], volumeData: [] });
            return;
        }
        
        const { candlestickData, volumeData } = transformKisData(rawItems);
        setChartData({ candlestickData, volumeData });

      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchChartData();
  }, [params.code, period]); // period가 변경될 때마다 API 재호출

  const PeriodButton = ({ p, label }: { p: Period; label: string }) => (
    <button
      onClick={() => setPeriod(p)}
      style={{
        padding: '8px 12px',
        margin: '0 4px',
        backgroundColor: period === p ? '#007bff' : '#f0f0f0',
        color: period === p ? 'white' : 'black',
        border: '1px solid #ccc',
        borderRadius: '4px',
        cursor: 'pointer',
      }}
    >
      {label}
    </button>
  );

  return (
    <div>
      <h1>{params.code} 주식 차트</h1>
      <div style={{ marginBottom: '16px' }}>
        <PeriodButton p="D" label="일봉" />
        <PeriodButton p="W" label="주봉" />
        <PeriodButton p="M" label="월봉" />
      </div>
      
      {isLoading && <div>차트 데이터를 불러오는 중입니다...</div>}
      {error && <div style={{ color: 'red' }}>오류: {error}</div>}
      {!isLoading && !error && (
        <StockChart
          candlestickData={chartData.candlestickData}
          volumeData={chartData.volumeData}
        />
      )}
    </div>
  );
}
```

---

## 추가 개선 사항

- **실시간 업데이트**: WebSocket을 연동하여 실시간 시세(`stck_prpr`)를 받아 차트의 마지막 캔들을 업데이트할 수 있습니다.
- **기술적 지표**: 이동평균선(Moving Average), RSI 등 기술적 지표를 계산하여 차트에 오버레이할 수 있습니다.
- **다크 모드**: `chartLayout` props를 통해 테마에 맞는 차트 색상을 동적으로 적용할 수 있습니다.
- **날짜 범위 선택**: 사용자가 직접 차트의 조회 기간을 선택할 수 있는 Date Picker UI를 추가할 수 있습니다.
