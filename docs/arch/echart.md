# ECharts를 이용한 차트 구현 방안

## 1. 개요

Apache ECharts 라이브러리 도입을 제안합니다.
기존의 ReChart이외에 추가로 제공을 하게 합니다.

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

위 `EChartsCandlestickChart` 컴포넌트를 구현한 후, `KoreanTradingChart.tsx` 파일에서 기존 `RealtimeCandlestickChart`를 호출하던 부분을 새로운 `EChartsCandlestickChart`로 추가해야 합니다.

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

---

# ECharts 캔들스틱 차트 데이터 연동 및 구현 가이드

## 1. 개요

이 문서는 FastAPI 백엔드에서 제공하는 주식 시세 데이터를 Next.js 프론트엔드에서 ECharts 라이브러리를 사용하여 캔들스틱 차트로 시각화하는 방법을 설명합니다. 백엔드 데이터 구조 정의부터 프론트엔드에서의 데이터 매핑 및 컴포넌트 구현까지 단계별로 안내합니다.

## 2. 데이터 정의

### 2.1. 백엔드 API 응답 데이터 (`ChartCandleResponse`)

백엔드 API는 특정 종목의 과거 캔들스틱 데이터를 리스트 형태로 제공해야 합니다. 각 캔들 데이터는 다음 구조를 가집니다.

**Pydantic Model (Python - `backend/app/models/chart.py` 또는 유사 경로)**

```python
# backend/app/models/chart.py
from pydantic import BaseModel
from typing import List

class ChartCandle(BaseModel):
    timestamp: str  # ISO 8601 형식의 날짜/시간 문자열 (예: "2023-01-01T09:00:00Z")
    open: float     # 시가
    high: float     # 고가
    low: float      # 저가
    close: float    # 종가
    volume: float   # 거래량

class ChartCandleResponse(BaseModel):
    data: List[ChartCandle]
    stock_code: str
    stock_name: str
    # 필요한 경우 추가 메타데이터 포함 가능
```

### 2.2. 프론트엔드 중간 데이터 타입 (`ChartCandle`)

백엔드에서 받은 데이터를 프론트엔드에서 사용할 TypeScript 인터페이스로 정의합니다. 이는 `docs/arch/echart.md`에 명시된 `ChartCandle` 타입과 동일합니다.

**TypeScript Interface (TypeScript - `stock-trading-ui/types/trading.ts` 또는 `types/korean-stocks.ts`)**

```typescript
// stock-trading-ui/types/korean-stocks.ts (or trading.ts)
export interface ChartCandle {
  timestamp: string; // ISO 8601 format (e.g., "2023-01-01T09:00:00Z")
  open: number;      // 시가
  high: number;      // 고가
  low: number;       // 저가
  close: number;     // 종가
  volume: number;    // 거래량
}
```

### 2.3. ECharts 캔들스틱 차트 요구 데이터 형식

ECharts의 캔들스틱 차트는 `series.data`에 `[시가, 종가, 저가, 고가]` 순서의 숫자 배열을, `xAxis.data`에 해당 캔들의 타임스탬프 배열을 요구합니다.

-   **`series.data` 형식:** `[[open, close, low, high], [open, close, low, high], ...]`
-   **`xAxis.data` 형식:** `[timestamp1, timestamp2, ...]` (날짜 문자열)

## 3. 백엔드 API 매핑 전략

백엔드 API는 프론트엔드 `ChartCandle` 인터페이스와 1:1 매핑되는 `ChartCandle` Pydantic 모델의 리스트를 반환하도록 설계합니다. 이렇게 하면 프론트엔드에서 별도의 복잡한 데이터 변환 없이 바로 사용할 수 있습니다.

### 3.1. 백엔드 API 엔드포인트 설계

특정 종목 코드에 대한 과거 캔들스틱 데이터를 조회하는 엔드포인트를 추가합니다.

-   **HTTP Method:** `GET`
-   **URL:** `/api/chart/candlestick/{stock_code}`
-   **Query Parameters (선택 사항):**
    -   `start_date`: 조회 시작일 (예: `2023-01-01`)
    -   `end_date`: 조회 종료일 (예: `2023-12-31`)
    -   `interval`: 캔들 주기 (예: `day`, `week`, `month`, `minute`)
-   **Response:** `ChartCandleResponse` (JSON 형식)

## 4. 단계별 구현 가이드 (Step-by-Step Implementation)

### 4.1. 1단계: 백엔드 API 구현 (FastAPI)

**목표:** 특정 종목의 가상 캔들스틱 데이터를 반환하는 API 엔드포인트를 생성합니다. 실제 데이터 연동은 이후에 진행하고, 여기서는 목업 데이터를 사용합니다.

**Pseudo Code:**

```python
# backend/app/api/chart.py (새로운 라우터 파일 생성)

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timedelta
import random

# 2.1에서 정의한 Pydantic 모델 import
from app.models.chart import ChartCandle, ChartCandleResponse

router = APIRouter(prefix="/chart", tags=["Chart"])

# 가상 캔들스틱 데이터 생성 함수 (실제 데이터 연동 시 대체)
def generate_mock_candlestick_data(stock_code: str, days: int = 30) -> List[ChartCandle]:
    data = []
    current_date = datetime.now() - timedelta(days=days)
    
    # 초기 가격 설정
    last_close = 10000.0
    
    for i in range(days):
        timestamp = (current_date + timedelta(days=i)).isoformat() + "Z"
        
        # 시가, 종가, 고가, 저가, 거래량 생성 로직 (단순화)
        open_price = last_close + random.uniform(-500, 500)
        close_price = open_price + random.uniform(-1000, 1000)
        high_price = max(open_price, close_price) + random.uniform(0, 200)
        low_price = min(open_price, close_price) - random.uniform(0, 200)
        volume = random.randint(100000, 1000000)
        
        data.append(ChartCandle(
            timestamp=timestamp,
            open=round(open_price, 2),
            high=round(high_price, 2),
            low=round(low_price, 2),
            close=round(close_price, 2),
            volume=volume
        ))
        last_close = close_price # 다음 캔들의 시가를 위해 종가 저장
        
    return data

@router.get("/{stock_code}", response_model=ChartCandleResponse)
async def get_candlestick_data(stock_code: str):
    """
    특정 종목의 캔들스틱 데이터를 조회합니다.
    현재는 목업 데이터를 반환합니다.
    """
    mock_data = generate_mock_candlestick_data(stock_code)
    return ChartCandleResponse(
        data=mock_data,
        stock_code=stock_code,
        stock_name=f"Mock Stock {stock_code}"
    )

# backend/app/main.py (메인 애플리케이션에 라우터 포함)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# ... 다른 라우터 import
from app.api import chart # 새로 생성한 chart 라우터 import

app = FastAPI(title="주식 매매 시스템 API")

# CORS 설정 (기존 설정 유지)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:9000"], # Frontend URL 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 주요 라우터 포함 (chart 라우터 추가)
# ... 기존 라우터
app.include_router(chart.router, prefix="/api") # /api/chart/{stock_code} 경로로 접근
```

### 4.2. 2단계: 프론트엔드 API 클라이언트 구현 (Next.js/TypeScript)

**목표:** 백엔드에서 정의한 캔들스틱 데이터를 가져오는 함수를 생성합니다.

**Pseudo Code:**

```typescript
// stock-trading-ui/lib/api/chart.ts (새로운 API 클라이언트 파일 생성)

import { ChartCandle } from '@/types/korean-stocks'; // 2.2에서 정의한 타입 import

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ChartDataResponse {
  data: ChartCandle[];
  stock_code: string;
  stock_name: string;
}

export async function fetchCandlestickData(stockCode: string): Promise<ChartCandle[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/chart/${stockCode}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const result: ChartDataResponse = await response.json();
    return result.data;
  } catch (error) {
    console.error("Failed to fetch candlestick data:", error);
    return []; // 에러 발생 시 빈 배열 반환
  }
}
```

### 4.3. 3단계: ECharts 캔들스틱 컴포넌트 구현 (`EChartsCandlestickChart.tsx`)

**목표:** `docs/arch/echart.md`에 제시된 코드를 사용하여 ECharts 캔들스틱 차트 컴포넌트를 생성합니다. 이 컴포넌트는 `ChartCandle` 배열을 입력으로 받아 ECharts 형식으로 변환하여 렌더링합니다.

**Pseudo Code:**

```typescript
// stock-trading-ui/src/components/trading/EChartsCandlestickChart.tsx

'use client';

import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import { ChartCandle } from '@/types/korean-stocks'; // 2.2에서 정의한 타입 import

interface EChartsCandlestickChartProps {
  chartData: ChartCandle[];
  height?: number;
}

const EChartsCandlestickChart: React.FC<EChartsCandlestickChartProps> = ({ chartData, height = 400 }) => {

  const echartOptions = useMemo(() => {
    // 1. 데이터 변환: ECharts 캔들스틱 형식 [open, close, low, high]
    const data = chartData.map(candle => [
      candle.open,
      candle.close,
      candle.low,
      candle.high,
    ]);

    // 2. 타임스탬프 변환: X축 레이블용
    const timestamps = chartData.map(candle => {
        const d = new Date(candle.timestamp);
        // YYYY-MM-DD 형식으로 변환
        return `${d.getFullYear()}-${(d.getMonth()+1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')}`;
    });

    // 3. ECharts 옵션 객체 생성 (docs/arch/echart.md 내용 그대로 사용)
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

### 4.4. 4단계: 테스트 페이지 구현 (`src/app/echart/page.tsx`)

**목표:** 백엔드 API에서 데이터를 가져와 `EChartsCandlestickChart` 컴포넌트를 렌더링하는 테스트 페이지를 생성합니다.

**Pseudo Code:**

```typescript
// stock-trading-ui/src/app/echart/page.tsx

'use client';

import React, { useEffect, useState } from 'react';
import EChartsCandlestickChart from '@/components/trading/EChartsCandlestickChart';
import { fetchCandlestickData } from '@/lib/api/chart'; // 4.2에서 생성한 API 클라이언트 import
import { ChartCandle } from '@/types/korean-stocks'; // 2.2에서 정의한 타입 import
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"; // shadcn/ui 컴포넌트 활용

export default function EChartTestPage() {
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadChartData() {
      try {
        setLoading(true);
        setError(null);
        // 테스트를 위한 임시 종목 코드 (예: "005930" 삼성전자)
        const data = await fetchCandlestickData("005930"); 
        setChartData(data);
      } catch (err) {
        setError("차트 데이터를 불러오는 데 실패했습니다.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    loadChartData();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6 text-white">ECharts 캔들스틱 차트 테스트</h1>
      <Card className="bg-gray-800 border-gray-700 text-white">
        <CardHeader>
          <CardTitle className="text-xl">삼성전자 (005930) 캔들 차트</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-center py-8">차트 데이터를 불러오는 중...</p>}
          {error && <p className="text-center py-8 text-red-500">{error}</p>}
          {!loading && !error && chartData.length > 0 && (
            <EChartsCandlestickChart chartData={chartData} height={500} />
          )}
          {!loading && !error && chartData.length === 0 && (
            <p className="text-center py-8 text-gray-400">표시할 차트 데이터가 없습니다.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

## 5. 개발 워크플로우

1.  **백엔드 가상환경 활성화:** `cd backend` 후 `source vkis/bin/activate`
2.  **백엔드 서버 실행:** `python app/main.py`
3.  **프론트엔드 의존성 설치:** `cd stock-trading-ui` 후 `npm install echarts echarts-for-react`
4.  **프론트엔드 개발 서버 실행:** `npm run dev`
5.  **브라우저 확인:** `http://localhost:9000/echart` 에 접속하여 차트가 정상적으로 렌더링되는지 확인합니다.

## 6. 고려 사항

-   **실제 데이터 연동:** 백엔드의 `generate_mock_candlestick_data` 함수를 한국투자증권 API 또는 다른 데이터 소스에서 실제 캔들스틱 데이터를 가져오는 로직으로 대체해야 합니다.
-   **에러 핸들링:** 프론트엔드와 백엔드 모두에서 API 호출 실패, 데이터 파싱 오류 등에 대한 견고한 에러 핸들링을 추가해야 합니다.
-   **성능 최적화:** 대량의 데이터를 처리할 경우, 백엔드에서 데이터 필터링(날짜 범위, 주기) 및 프론트엔드에서 가상화(Virtualization) 또는 데이터 압축 기법을 고려할 수 있습니다.
-   **스타일링:** ECharts 옵션 객체 내의 스타일링(`backgroundColor`, `itemStyle` 등)은 `docs/arch/echart.md`에 제시된 다크 테마를 따르도록 이미 설정되어 있습니다. 필요에 따라 추가적인 커스터마이징이 가능합니다.
-   **타입 정의 위치:** `ChartCandle` 타입은 `stock-trading-ui/types/korean-stocks.ts` 또는 `stock-trading-ui/types/trading.ts` 중 프로젝트의 컨벤션에 맞는 곳에 정의합니다.

---