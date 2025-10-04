# 📊 TradingView Lightweight Charts 샘플 페이지 구현 설계서 (Updated v2)

## 🎯 프로젝트 개요

### 목적
- TradingView Lightweight Charts 라이브러리를 활용한 주식 차트 샘플 페이지 구현
- `/trview` 엔드포인트로 독립적인 차트 데모 제공
- Backend API와 연계하여 실제 주식 데이터 표시

### 핵심 요구사항
1. ✅ **명명 규칙**: "LightweightChart" 대신 "TRViewChart" 사용하여 TradingView 기반임을 명확히 표시
2. ✅ **Backend 연동**: 기존 Chart API (`/api/chart/{stock_code}/minute`) 활용
3. ✅ **데이터 타입**: `ChartCandle` 타입 호환성 유지
4. ✅ **재사용성**: 다른 페이지에서도 사용 가능한 컴포넌트 설계
5. ✅ **실시간 업데이트**: WebSocket 연동 대비 설계

---

## 🏗️ Architecture

### 1. 파일 구조
```
stock-trading-ui/
├── src/
│   ├── app/
│   │   └── trview/
│   │       └── page.tsx                          # 메인 샘플 페이지
│   │
│   ├── components/
│   │   └── trading/
│   │       ├── TRViewChart.tsx                   # TradingView 차트 래퍼 컴포넌트
│   │       └── TRViewChartControls.tsx           # 차트 컨트롤 UI
│   │
│   ├── lib/
│   │   └── tradingview/
│   │       ├── chartConfig.ts                    # 차트 설정 & 스타일
│   │       ├── dataConverter.ts                  # ChartCandle → Lightweight Charts 변환
│   │       └── types.ts                          # TradingView 타입 정의
│   │
│   └── hooks/
│       └── useTRViewChart.ts                     # 차트 데이터 로딩 훅
│
└── __tests__/
    └── lib/
        └── tradingview/
            └── dataConverter.test.ts             # 데이터 변환 유닛 테스트
```

### 2. 기술 스택
- **Chart Library**: `lightweight-charts` v5.0.8 ✅ (이미 설치됨)
- **Framework**: Next.js 15 App Router
- **Styling**: Tailwind CSS + Dark Theme
- **Language**: TypeScript
- **Backend API**: FastAPI (`http://localhost:8000`)

---

## 📦 데이터 흐름 (Backend → Frontend)

### Backend API 구조
```python
# 이미 구축된 API 엔드포인트
GET /api/chart/{stock_code}/minute?date={YYYY-MM-DD}

# 응답 형식 (ChartCandle[])
[
  {
    "timestamp": "2025-01-04T09:00:00",
    "open": 75000,
    "high": 75500,
    "low": 74800,
    "close": 75200,
    "volume": 123456
  },
  ...
]
```

### Frontend 데이터 타입
```typescript
// 기존 타입 활용 (src/lib/types/korean-stocks.ts)
export interface ChartCandle {
  timestamp: string;      // ISO 8601 형식
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// TradingView Lightweight Charts 형식
import { UTCTimestamp } from 'lightweight-charts';

interface TRViewCandleData {
  time: UTCTimestamp;    // Unix timestamp (초 단위)
  open: number;
  high: number;
  low: number;
  close: number;
}

interface TRViewVolumeData {
  time: UTCTimestamp;
  value: number;
  color?: string;        // 거래량 색상 (매수/매도 구분)
}
```

### 데이터 변환 로직 (⚠️ 중요: 시간 형식 수정)
```typescript
// lib/tradingview/dataConverter.ts
import { UTCTimestamp } from 'lightweight-charts';
import { ChartCandle } from '@/lib/types/korean-stocks';

/**
 * ChartCandle을 TradingView Candlestick 형식으로 변환
 *
 * ⚠️ 중요: 분봉 데이터이므로 Unix timestamp(초 단위)를 사용해야 합니다.
 * 날짜만 추출하면 모든 캔들이 하나의 시간에 겹쳐 그려지는 문제가 발생합니다.
 */
export function convertToTRViewCandles(
  chartData: ChartCandle[]
): TRViewCandleData[] {
  return chartData.map(candle => ({
    // ISO 8601 → Unix timestamp (초 단위)
    time: (new Date(candle.timestamp).getTime() / 1000) as UTCTimestamp,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
  }));
}

/**
 * ChartCandle을 TradingView Volume 형식으로 변환
 */
export function convertToTRViewVolumes(
  chartData: ChartCandle[]
): TRViewVolumeData[] {
  return chartData.map((candle, index) => {
    const prevClose = index > 0 ? chartData[index - 1].close : candle.open;
    const isUp = candle.close >= prevClose;

    return {
      // ISO 8601 → Unix timestamp (초 단위)
      time: (new Date(candle.timestamp).getTime() / 1000) as UTCTimestamp,
      value: candle.volume,
      color: isUp ? 'rgba(239, 68, 68, 0.5)' : 'rgba(59, 130, 246, 0.5)'
    };
  });
}
```

---

## 🎨 컴포넌트 설계

### 1. TRViewChart 컴포넌트 (핵심) - 성능 최적화 버전
```typescript
// components/trading/TRViewChart.tsx
'use client';

import { useEffect, useRef, useMemo } from 'react';
import { createChart, IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { getTRViewChartOptions } from '@/lib/tradingview/chartConfig';
import {
  convertToTRViewCandles,
  convertToTRViewVolumes
} from '@/lib/tradingview/dataConverter';

interface TRViewChartProps {
  chartData: ChartCandle[];
  height?: number;
  showVolume?: boolean;
  showGrid?: boolean;
  enableCrosshair?: boolean;
  className?: string;
  // 실시간 업데이트용 (선택사항)
  onReady?: (api: {
    updateCandle: (candle: ChartCandle) => void;
    chart: IChartApi;
  }) => void;
}

export function TRViewChart({
  chartData,
  height = 500,
  showVolume = true,
  showGrid = true,
  enableCrosshair = true,
  className = '',
  onReady
}: TRViewChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // ✅ 성능 최적화: 데이터 변환을 메모이제이션
  const candleData = useMemo(() => convertToTRViewCandles(chartData), [chartData]);
  const volumeData = useMemo(() => convertToTRViewVolumes(chartData), [chartData]);

  // ✅ 차트 초기화 (한 번만 실행)
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      ...getTRViewChartOptions(),
      width: chartContainerRef.current.clientWidth,
      height,
    });

    chartRef.current = chart;

    // 캔들스틱 시리즈 추가
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#ef4444',        // 상승 (빨강)
      downColor: '#3b82f6',      // 하락 (파랑)
      borderUpColor: '#ef4444',
      borderDownColor: '#3b82f6',
      wickUpColor: '#ef4444',
      wickDownColor: '#3b82f6',
    });

    candleSeriesRef.current = candleSeries;

    // 거래량 히스토그램 추가
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    });

    volumeSeriesRef.current = volumeSeries;

    // 거래량 Y축 설정
    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // 반응형 크기 조정
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // 실시간 업데이트 API 제공
    if (onReady) {
      onReady({
        updateCandle: (candle: ChartCandle) => {
          const converted = convertToTRViewCandles([candle])[0];
          candleSeries.update(converted);

          if (volumeSeriesRef.current) {
            const volumeConverted = convertToTRViewVolumes([candle])[0];
            volumeSeriesRef.current.update(volumeConverted);
          }
        },
        chart
      });
    }

    // 정리
    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, onReady]); // ⚠️ 의존성 최소화

  // ✅ 그리드 옵션 동적 업데이트 (차트 재생성 없이)
  useEffect(() => {
    if (!chartRef.current) return;

    chartRef.current.applyOptions({
      grid: {
        vertLines: { visible: showGrid },
        horzLines: { visible: showGrid },
      },
    });
  }, [showGrid]);

  // ✅ Crosshair 옵션 동적 업데이트
  useEffect(() => {
    if (!chartRef.current) return;

    chartRef.current.applyOptions({
      crosshair: {
        mode: enableCrosshair ? 1 : 0,
      },
    });
  }, [enableCrosshair]);

  // ✅ 거래량 표시 토글
  useEffect(() => {
    if (!volumeSeriesRef.current) return;

    volumeSeriesRef.current.applyOptions({
      visible: showVolume,
    });
  }, [showVolume]);

  // ✅ 데이터 업데이트 (전체 데이터 교체 시)
  useEffect(() => {
    if (!candleData || candleData.length === 0) return;
    if (!candleSeriesRef.current) return;

    // 캔들 데이터 설정
    candleSeriesRef.current.setData(candleData);

    // 거래량 데이터 설정
    if (volumeSeriesRef.current && showVolume) {
      volumeSeriesRef.current.setData(volumeData);
    }

    // 차트 범위 자동 조정
    chartRef.current?.timeScale().fitContent();
  }, [candleData, volumeData, showVolume]);

  return (
    <div
      ref={chartContainerRef}
      className={`bg-[#0a0a0b] border border-gray-700 rounded-lg ${className}`}
    />
  );
}
```

### 2. TRViewChartControls 컴포넌트 (재사용 가능)
```typescript
// components/trading/TRViewChartControls.tsx
'use client';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3, TrendingUp } from 'lucide-react';

interface Stock {
  code: string;
  name: string;
}

interface TRViewChartControlsProps {
  selectedStockCode: string;
  onStockChange: (code: string) => void;
  stocks: Stock[];
  showVolume: boolean;
  onVolumeToggle: () => void;
  showGrid: boolean;
  onGridToggle: () => void;
  dataCount?: number;
}

export function TRViewChartControls({
  selectedStockCode,
  onStockChange,
  stocks,
  showVolume,
  onVolumeToggle,
  showGrid,
  onGridToggle,
  dataCount = 0
}: TRViewChartControlsProps) {
  return (
    <Card className="bg-[#1a1a1b] border-gray-700">
      <CardHeader>
        <CardTitle className="text-white">차트 설정</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 종목 선택 */}
        <div>
          <label className="text-sm text-gray-400 mb-2 block">
            종목 선택
          </label>
          <div className="space-y-2">
            {stocks.map((stock) => (
              <Button
                key={stock.code}
                variant={selectedStockCode === stock.code ? 'default' : 'outline'}
                className="w-full justify-start"
                onClick={() => onStockChange(stock.code)}
              >
                {stock.name} ({stock.code})
              </Button>
            ))}
          </div>
        </div>

        {/* 표시 옵션 */}
        <div>
          <label className="text-sm text-gray-400 mb-2 block">
            표시 옵션
          </label>
          <div className="space-y-2">
            <Button
              variant={showVolume ? 'default' : 'outline'}
              className="w-full justify-start"
              onClick={onVolumeToggle}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              거래량 표시
            </Button>
            <Button
              variant={showGrid ? 'default' : 'outline'}
              className="w-full justify-start"
              onClick={onGridToggle}
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              그리드 표시
            </Button>
          </div>
        </div>

        {/* 정보 */}
        <div className="pt-4 border-t border-gray-700">
          <p className="text-xs text-gray-500">
            Backend API: http://localhost:8000
          </p>
          <p className="text-xs text-gray-500">
            데이터: {dataCount}개 캔들
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 3. 차트 설정 파일
```typescript
// lib/tradingview/chartConfig.ts
import { ChartOptions, DeepPartial } from 'lightweight-charts';

export function getTRViewChartOptions(): DeepPartial<ChartOptions> {
  return {
    layout: {
      background: {
        type: 'solid' as const,
        color: '#0a0a0b'  // 다크 배경
      },
      textColor: '#d1d5db',  // 텍스트 색상
      fontSize: 12,
    },
    grid: {
      vertLines: {
        color: '#1f2937',
        style: 1,  // 실선
        visible: true,
      },
      horzLines: {
        color: '#1f2937',
        style: 1,
        visible: true,
      },
    },
    crosshair: {
      mode: 1,  // Normal mode
      vertLine: {
        color: '#6b7280',
        width: 1,
        style: 3,  // 점선
        labelBackgroundColor: '#374151',
      },
      horzLine: {
        color: '#6b7280',
        width: 1,
        style: 3,
        labelBackgroundColor: '#374151',
      },
    },
    timeScale: {
      borderColor: '#374151',
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: '#374151',
      scaleMargins: {
        top: 0.1,
        bottom: 0.2,
      },
    },
  };
}
```

### 4. 타입 정의 파일
```typescript
// lib/tradingview/types.ts
import { UTCTimestamp } from 'lightweight-charts';

export interface TRViewCandleData {
  time: UTCTimestamp;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface TRViewVolumeData {
  time: UTCTimestamp;
  value: number;
  color?: string;
}
```

### 5. 데이터 로딩 훅
```typescript
// hooks/useTRViewChart.ts
'use client';

import { useState, useEffect } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { chartAPI } from '@/lib/chart-api';

interface UseTRViewChartProps {
  stockCode: string;
  date?: string;  // YYYY-MM-DD
  enabled?: boolean;
}

export function useTRViewChart({
  stockCode,
  date,
  enabled = true,
}: UseTRViewChartProps) {
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !stockCode) return;

    const fetchChartData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const data = await chartAPI.getMinuteCandles(stockCode, { date });
        setChartData(data);
      } catch (err) {
        const message = err instanceof Error ? err.message : '차트 데이터 로드 실패';
        setError(message);
        console.error('TRView 차트 데이터 로드 오류:', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchChartData();
  }, [stockCode, date, enabled]);

  return { chartData, isLoading, error };
}
```

### 6. 샘플 페이지 (TRViewChartControls 사용)
```typescript
// app/trview/page.tsx
'use client';

import { useState } from 'react';
import { TRViewChart } from '@/components/trading/TRViewChart';
import { TRViewChartControls } from '@/components/trading/TRViewChartControls';
import { useTRViewChart } from '@/hooks/useTRViewChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CandlestickChart,
  RefreshCw,
  Github
} from 'lucide-react';

const SAMPLE_STOCKS = [
  { code: '005930', name: '삼성전자' },
  { code: '000660', name: 'SK하이닉스' },
  { code: '035420', name: 'NAVER' },
  { code: '051910', name: 'LG화학' },
];

export default function TRViewPage() {
  const [stockCode, setStockCode] = useState('005930');
  const [showVolume, setShowVolume] = useState(true);
  const [showGrid, setShowGrid] = useState(true);

  const { chartData, isLoading, error } = useTRViewChart({
    stockCode,
    enabled: true,
  });

  return (
    <div className="min-h-screen bg-[#0a0a0b]">
      {/* Header */}
      <div className="bg-[#1a1a1b] border-b border-gray-700 px-6 py-4">
        <div className="max-w-[1600px] mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CandlestickChart className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-xl font-bold text-white">
                  TradingView Lightweight Charts Demo
                </h1>
                <p className="text-sm text-gray-400">
                  실시간 주식 차트 샘플 페이지
                </p>
              </div>
            </div>
            <Badge className="bg-blue-500">
              <Github className="w-3 h-3 mr-1" />
              TradingView
            </Badge>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1600px] mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Controls Panel */}
          <TRViewChartControls
            selectedStockCode={stockCode}
            onStockChange={setStockCode}
            stocks={SAMPLE_STOCKS}
            showVolume={showVolume}
            onVolumeToggle={() => setShowVolume(!showVolume)}
            showGrid={showGrid}
            onGridToggle={() => setShowGrid(!showGrid)}
            dataCount={chartData.length}
          />

          {/* Chart Panel */}
          <Card className="lg:col-span-3 bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">
                  {SAMPLE_STOCKS.find(s => s.code === stockCode)?.name} 차트
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.location.reload()}
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading && (
                <div className="h-[500px] flex items-center justify-center">
                  <div className="text-gray-400">차트 로딩 중...</div>
                </div>
              )}

              {error && (
                <div className="h-[500px] flex items-center justify-center">
                  <div className="text-red-400">오류: {error}</div>
                </div>
              )}

              {!isLoading && !error && chartData.length > 0 && (
                <TRViewChart
                  chartData={chartData}
                  height={500}
                  showVolume={showVolume}
                  showGrid={showGrid}
                  enableCrosshair={true}
                />
              )}

              {!isLoading && !error && chartData.length === 0 && (
                <div className="h-[500px] flex items-center justify-center">
                  <div className="text-gray-400">차트 데이터 없음</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
```

### 7. 데이터 변환 유닛 테스트
```typescript
// __tests__/lib/tradingview/dataConverter.test.ts
import { describe, it, expect } from '@jest/globals';
import { convertToTRViewCandles, convertToTRViewVolumes } from '@/lib/tradingview/dataConverter';
import { ChartCandle } from '@/lib/types/korean-stocks';

describe('TradingView Data Converter', () => {
  const mockChartData: ChartCandle[] = [
    {
      timestamp: '2025-01-04T09:00:00',
      open: 75000,
      high: 75500,
      low: 74800,
      close: 75200,
      volume: 123456,
    },
    {
      timestamp: '2025-01-04T09:01:00',
      open: 75200,
      high: 75800,
      low: 75100,
      close: 75600,
      volume: 234567,
    },
  ];

  describe('convertToTRViewCandles', () => {
    it('should convert ChartCandle to TRViewCandleData with Unix timestamp', () => {
      const result = convertToTRViewCandles(mockChartData);

      expect(result).toHaveLength(2);

      // 첫 번째 캔들 검증
      expect(result[0].time).toBe(new Date('2025-01-04T09:00:00').getTime() / 1000);
      expect(result[0].open).toBe(75000);
      expect(result[0].high).toBe(75500);
      expect(result[0].low).toBe(74800);
      expect(result[0].close).toBe(75200);

      // 두 번째 캔들 검증
      expect(result[1].time).toBe(new Date('2025-01-04T09:01:00').getTime() / 1000);
      expect(result[1].close).toBe(75600);
    });

    it('should preserve data order', () => {
      const result = convertToTRViewCandles(mockChartData);

      expect(result[0].time).toBeLessThan(result[1].time);
    });
  });

  describe('convertToTRViewVolumes', () => {
    it('should convert ChartCandle to TRViewVolumeData with colors', () => {
      const result = convertToTRViewVolumes(mockChartData);

      expect(result).toHaveLength(2);

      // 첫 번째 거래량 (상승 - 빨강)
      expect(result[0].value).toBe(123456);
      expect(result[0].color).toBe('rgba(239, 68, 68, 0.5)');

      // 두 번째 거래량 (상승 - 빨강)
      expect(result[1].value).toBe(234567);
      expect(result[1].color).toBe('rgba(239, 68, 68, 0.5)');
    });

    it('should use blue color for declining candles', () => {
      const decliningData: ChartCandle[] = [
        { ...mockChartData[0], close: 75000 },
        { ...mockChartData[1], close: 74500 }, // 하락
      ];

      const result = convertToTRViewVolumes(decliningData);

      expect(result[1].color).toBe('rgba(59, 130, 246, 0.5)'); // 파랑
    });
  });
});
```

---

## 🔄 구현 단계 (Implementation Phases)

### Phase 1: 기본 구조 생성
**목표**: 파일 구조 및 기본 컴포넌트 생성

1. ✅ `/trview/page.tsx` 생성 (샘플 페이지)
2. ✅ `TRViewChart.tsx` 컴포넌트 생성 (성능 최적화 버전)
3. ✅ `TRViewChartControls.tsx` 컴포넌트 생성 (분리)
4. ✅ `chartConfig.ts` 설정 파일 생성
5. ✅ `dataConverter.ts` 유틸리티 생성 (⚠️ Unix timestamp 사용)
6. ✅ `types.ts` 타입 정의 생성
7. ✅ `useTRViewChart.ts` 훅 생성

**예상 소요**: 1.5시간

### Phase 2: TradingView 차트 통합
**목표**: Lightweight Charts 라이브러리 통합 및 기본 표시

8. ✅ Candlestick 시리즈 초기화
9. ✅ 다크 테마 스타일 적용
10. ✅ 반응형 크기 조정 구현
11. ✅ ChartCandle → TRView 데이터 변환 (Unix timestamp)
12. ✅ 차트 데이터 바인딩
13. ✅ 옵션별 동적 업데이트 (applyOptions 사용)

**예상 소요**: 2시간

### Phase 3: Backend API 연동
**목표**: 실제 주식 데이터 표시

14. ✅ 기존 `chartAPI` 활용하여 데이터 로드
15. ✅ 종목 코드별 데이터 fetch
16. ✅ 로딩/에러 상태 처리
17. ✅ 데이터 캐싱 (선택사항)

**예상 소요**: 1시간

### Phase 4: UX 개선
**목표**: 사용자 경험 최적화

18. ✅ TRViewChartControls 컴포넌트 분리
19. ✅ 종목 선택 UI
20. ✅ 차트 옵션 토글 (거래량, 그리드 등)
21. ✅ Crosshair 및 툴팁 커스터마이징
22. ✅ 반응형 레이아웃

**예상 소요**: 1.5시간

### Phase 5: 테스팅
**목표**: 안정성 확보

23. ✅ dataConverter.test.ts 유닛 테스트 작성
24. ✅ 시간 형식 변환 검증
25. ✅ 거래량 색상 로직 검증
26. ✅ 엣지 케이스 테스트

**예상 소요**: 1시간

### Phase 6: 선택적 고급 기능
**목표**: 실시간 업데이트 지원

27. 🔄 실시간 데이터 업데이트 (`update()` API)
28. 🔄 WebSocket 연동 준비
29. 🔄 기술적 지표 오버레이 (SMA, EMA 등)
30. 🔄 Multiple timeframe 지원 (1분, 5분, 일봉 등)

**예상 소요**: 2-3시간 (필요시)

---

## 🔍 추가 검토 항목

### 1. 성능 최적화
- ✅ **메모이제이션**: `useMemo`로 데이터 변환 최적화
- ✅ **차트 재생성 방지**: `applyOptions()`로 동적 업데이트
- **가상화**: 대량 데이터 처리 시 고려
- **Lazy Loading**: 초기 로딩 속도 개선

### 2. 타입 안전성
- ✅ TradingView `UTCTimestamp` 타입 사용
- ✅ Backend API 응답 타입 검증
- **Runtime 타입 체킹**: Zod 등 (선택사항)

### 3. 에러 처리
- ✅ Network 오류 처리
- ✅ 잘못된 데이터 형식 처리
- ✅ Fallback UI 제공
- **에러 바운더리**: React Error Boundary 추가

### 4. 접근성
- 키보드 네비게이션
- 스크린 리더 지원
- 색상 대비 검증

### 5. 테스팅
- ✅ Unit Test: 데이터 변환 함수
- Integration Test: API 연동
- E2E Test: 전체 차트 렌더링 (Playwright)

### 6. 문서화
- ✅ 컴포넌트 Props 문서화 (JSDoc)
- 사용 예시 작성
- Storybook 통합 (선택사항)

---

## 🚨 주요 개선 사항 요약

### 1. ⚠️ 치명적 오류 수정: 시간 형식
**문제**: 분봉 데이터인데 날짜만 추출하여 모든 캔들이 겹침
**해결**: Unix timestamp (초 단위) 사용
```typescript
// ❌ 잘못된 방법
time: candle.timestamp.split('T')[0]  // 'YYYY-MM-DD'

// ✅ 올바른 방법
time: (new Date(candle.timestamp).getTime() / 1000) as UTCTimestamp
```

### 2. ⚡ 성능 최적화: 차트 재생성 방지
**문제**: 옵션 변경 시 차트 전체 재생성 (깜빡임)
**해결**: `applyOptions()`로 동적 업데이트
```typescript
// ❌ 잘못된 방법
useEffect(() => {
  // 전체 재생성
}, [showGrid, showVolume, ...])

// ✅ 올바른 방법
useEffect(() => {
  chartRef.current?.applyOptions({ grid: { ... } })
}, [showGrid])
```

### 3. 🔄 실시간 업데이트 지원
**추가**: `onReady` prop으로 `update()` API 제공
```typescript
<TRViewChart
  chartData={data}
  onReady={({ updateCandle }) => {
    // WebSocket으로 받은 새 캔들 업데이트
    ws.onmessage = (msg) => {
      updateCandle(msg.data);
    };
  }}
/>
```

### 4. 🧩 컴포넌트 분리
**추가**: `TRViewChartControls` 별도 컴포넌트로 재사용성 향상

### 5. 🧪 테스팅 강화
**추가**: `dataConverter.test.ts` 유닛 테스트

---

## 📚 참고 자료

### TradingView Lightweight Charts
- **공식 문서**: https://tradingview.github.io/lightweight-charts/docs
- **React 튜토리얼**: https://tradingview.github.io/lightweight-charts/tutorials/react/simple
- **API 레퍼런스**: https://tradingview.github.io/lightweight-charts/docs/api
- **Time Format**: https://tradingview.github.io/lightweight-charts/docs/api/interfaces/Time

### Backend API
- **Chart API**: `/api/chart/{stock_code}/minute`
- **데이터 형식**: `ChartCandle[]`
- **옵션**: `date`, `include_extended_hours`, `regular_hours_only`

### 기존 프로젝트 코드
- **ChartAPI 클라이언트**: `src/lib/chart-api.ts`
- **데이터 타입**: `src/lib/types/korean-stocks.ts`
- **차트 훅**: `src/hooks/useHistoricalChartData.ts`

---

## ✅ 구현 체크리스트

### Agent 실행 전 확인사항
- [ ] `lightweight-charts` v5.0.8 설치 확인
- [ ] Backend 서버 실행 (http://localhost:8000)
- [ ] Frontend 서버 실행 (http://localhost:9000)
- [ ] API 엔드포인트 동작 확인

### 구현 중 확인사항
- [ ] TypeScript 타입 에러 없음
- [ ] ESLint 경고 없음
- [ ] ⚠️ **시간 형식이 Unix timestamp인지 확인**
- [ ] ⚠️ **차트 옵션 변경 시 재생성되지 않는지 확인**
- [ ] 다크 테마 일관성 유지
- [ ] 반응형 레이아웃 동작 확인

### 완료 후 테스트
- [ ] `/trview` 페이지 접속 가능
- [ ] 차트 정상 렌더링
- [ ] ⚠️ **분봉이 시간 순서대로 표시되는지 확인**
- [ ] 종목 변경 시 데이터 업데이트
- [ ] 거래량 토글 동작 (차트 재생성 없이)
- [ ] 그리드 토글 동작 (차트 재생성 없이)
- [ ] 브라우저 콘솔 에러 없음
- [ ] `npm test` 유닛 테스트 통과

---

## 🎯 최종 결과물

### 접속 URL
- **샘플 페이지**: http://localhost:9000/trview

### 주요 기능
1. ✅ TradingView Lightweight Charts 캔들스틱 차트
2. ✅ 실시간 Backend API 데이터 연동
3. ✅ 종목 선택 UI (삼성전자, SK하이닉스, NAVER, LG화학)
4. ✅ 거래량 히스토그램 (동적 토글)
5. ✅ 그리드 및 Crosshair 토글 (차트 재생성 없음)
6. ✅ 다크 테마 일관성
7. ✅ 반응형 레이아웃
8. ✅ 실시간 업데이트 준비 (`onReady` API)
9. ✅ 유닛 테스트 포함

### 재사용성
- `TRViewChart` 컴포넌트는 다른 페이지에서 import하여 사용 가능
- `TRViewChartControls` 컴포넌트로 UI 재사용
- `useTRViewChart` 훅으로 데이터 로딩 추상화
- `chartConfig.ts`에서 스타일 중앙 관리
- `dataConverter.ts` 유닛 테스트로 안정성 보장

---

## 🚀 Agent 실행 가이드

### 추천 Agent
1. **frontend-developer**: 컴포넌트 구현 및 UI 작업
2. **typescript-pro**: 타입 정의 및 안전성 검증
3. **debugger**: 에러 발생 시 문제 해결

### 실행 명령 예시
```bash
Task: frontend-developer
"TradingView Lightweight Charts를 활용한 /trview 샘플 페이지 구현 (v2 개선 버전).
설계서에 따라:
1. TRViewChart 컴포넌트 (성능 최적화 버전, applyOptions 사용)
2. TRViewChartControls 컴포넌트 (재사용 가능)
3. dataConverter (Unix timestamp 사용)
4. 유닛 테스트 (dataConverter.test.ts)
를 순차적으로 구현.
Backend API 연동 및 다크 테마 스타일 적용."
```

---

## 🔬 추가 개선 제안 (Optional)

### 1. WebSocket 실시간 연동 예시
```typescript
// app/trview/page.tsx에 추가
const [chartAPI, setChartAPI] = useState<any>(null);

useEffect(() => {
  if (!chartAPI) return;

  const ws = new WebSocket('ws://localhost:8000/ws/price');

  ws.onmessage = (event) => {
    const newCandle = JSON.parse(event.data);
    chartAPI.updateCandle(newCandle);
  };

  return () => ws.close();
}, [chartAPI]);

// TRViewChart에 onReady 전달
<TRViewChart
  onReady={setChartAPI}
  ...
/>
```

### 2. 기술적 지표 추가
```typescript
// lib/tradingview/indicators.ts
export function calculateSMA(data: ChartCandle[], period: number) {
  // Simple Moving Average 계산
}

// TRViewChart에 Line Series 추가
const smaSeries = chart.addLineSeries({ color: '#FFA500' });
```

---

**핵심 설계 원칙**:
- ✅ Simple & Clean (최소한의 복잡성)
- ✅ Performance First (차트 재생성 방지)
- ✅ Backend Integration (기존 API 활용)
- ✅ Reusable Components (재사용 가능한 구조)
- ✅ TradingView Best Practices (공식 패턴 준수)
- ✅ Test Coverage (유닛 테스트 포함)
