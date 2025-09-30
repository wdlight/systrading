'use client';

import React, { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  Bar,
  ReferenceLine,
  Brush,
  Line,
} from 'recharts';
import { getTickUnitByPrice } from '@/lib/utils';
import { TradingHoursManager } from '@/lib/utils/tradingHours';
import { TIMEFRAME_CONFIG, generateTimeTicks, isIntraday } from '@/lib/chart-config';
import { ChartAdapterProps, KOREAN_CHART_THEME } from './ChartAdapter';

// Create a scale function factory
const createYScale = (yDomain: [number, number], chartHeight: number, margin: number = 10) => {
  const [min, max] = yDomain;
  const range = max - min;
  const effectiveHeight = chartHeight - 2 * margin;

  return (value: number) => {
    // Linear scale: map value from domain [min, max] to range [chartHeight - margin, margin]
    // Note: Y axis in SVG goes from top (0) to bottom (chartHeight)
    const normalized = (value - min) / range; // 0 to 1
    return chartHeight - margin - (normalized * effectiveHeight); // Flip Y axis
  };
};

// Factory function to create CandlestickDot with yDomain, height and dataCount
const createCandlestickDot = (yDomain: [number, number], chartHeight: number, dataCount: number, chartWidth: number = 950) => {
  const yScale = createYScale(yDomain, chartHeight);

  return (props: any) => {
    const { cx, cy, payload, index, height, width } = props;

    if (!payload) {
      return null;
    }

    const { open, high, low, close, timestamp } = payload;

    // Calculate Y positions using our custom scale
    const yHigh = yScale(high);
    const yLow = yScale(low);
    const yOpen = yScale(open);
    const yClose = yScale(close);

    const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1);
    const bodyY = Math.min(yOpen, yClose);
    // 캔들 너비 계산: 고정 4픽셀 두께 (기존 6px에서 2px 감소)
    const candleWidth = 4;

    // Korean style: red=up, blue=down
    const isRising = close >= open;
    const fillColor = isRising ? '#ef4444' : '#3b82f6';
    const strokeColor = isRising ? '#dc2626' : '#2563eb';

    if (index === 0) {
      console.log('✅ CandlestickDot rendering:', {
        payload: { open, high, low, close },
        positions: { yHigh, yLow, yOpen, yClose },
        bodyHeight,
        dataCount,
        chartWidth,
        calculatedCandleWidth: candleWidth
      });
    }

    // Use timestamp or index as unique key
    const uniqueKey = timestamp || `candle-${index}`;

    return (
      <g key={uniqueKey}>
        {/* Wick (High-Low line) */}
        <line
          x1={cx}
          y1={yHigh}
          x2={cx}
          y2={yLow}
          stroke={strokeColor}
          strokeWidth={1}
        />

        {/* Candle body (Open-Close box) */}
        <rect
          x={cx - candleWidth / 2}
          y={bodyY}
          width={candleWidth}
          height={bodyHeight}
          fill={fillColor}
          stroke={strokeColor}
          strokeWidth={1}
        />
      </g>
    );
  };
};

// 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length > 0) {
    const data = payload[0].payload;
    const date = new Date(data.time);
    const timeStr = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

    return (
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 text-sm">
        <p className="text-gray-300 mb-2">
          {timeStr}
        </p>
        <div className="space-y-1">
          <p><span className="text-gray-400">시가:</span> <span className="text-white">{data.open.toLocaleString()}</span></p>
          <p><span className="text-gray-400">고가:</span> <span className="text-red-400">{data.high.toLocaleString()}</span></p>
          <p><span className="text-gray-400">저가:</span> <span className="text-blue-400">{data.low.toLocaleString()}</span></p>
          <p><span className="text-gray-400">종가:</span> <span className="text-white">{data.close.toLocaleString()}</span></p>
          {data.volume && (
            <p><span className="text-gray-400">거래량:</span> <span className="text-yellow-400">{data.volume.toLocaleString()}</span></p>
          )}
        </div>
      </div>
    );
  }
  return null;
};

const RechartsAdapter: React.FC<ChartAdapterProps> = ({
  chartData,
  height = 400,
  timeframe,
  onError
}) => {
  // 차트 스크롤 상태 관리
  const [viewWindow, setViewWindow] = useState<{ startIndex: number; endIndex: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; startIndex: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [chartWidth, setChartWidth] = useState<number>(1000);

  // 차트 컨테이너 너비 감지
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth - 100; // 좌우 마진 제외
        setChartWidth(width);
      }
    };

    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  // 항상 모든 훅을 같은 순서로 호출
  const formattedData = useMemo(() => {
    try {
      if (!chartData || chartData.length === 0) {
        return [];
      }

      const mapped = chartData.map(candle => ({
        time: new Date(candle.timestamp).getTime(),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume || 0,
      })).sort((a, b) => a.time - b.time);

      // 중복 제거: 같은 시간(분 단위)의 데이터는 첫 번째것만 유지
      const uniqueData = mapped.filter((candle, index, array) => {
        if (index === 0) return true;
        const prevTime = new Date(array[index - 1].time);
        const currTime = new Date(candle.time);
        // 년-월-일-시-분이 모두 같으면 중복으로 간주
        return !(
          prevTime.getFullYear() === currTime.getFullYear() &&
          prevTime.getMonth() === currTime.getMonth() &&
          prevTime.getDate() === currTime.getDate() &&
          prevTime.getHours() === currTime.getHours() &&
          prevTime.getMinutes() === currTime.getMinutes()
        );
      });

      console.log(`🔄 데이터 중복 제거: ${mapped.length}개 → ${uniqueData.length}개`);

      return uniqueData;
    } catch (error) {
      console.error('Failed to format chart data:', error);
      onError?.('차트 데이터 포맷 변환 실패');
      return [];
    }
  }, [chartData, onError]);

  useEffect(() => {
    if (formattedData.length > 0) {
      console.log('🔬 Data Validation:', {
        count: formattedData.length,
        first5: formattedData.slice(0, 5).map(d => new Date(d.time).toLocaleString()),
        last5: formattedData.slice(-5).map(d => new Date(d.time).toLocaleString()),
      });
    }
  }, [formattedData]);

  // 표시할 데이터 범위 계산
  const displayData = useMemo(() => {
    if (formattedData.length === 0) {
      return [];
    }

    // 기본적으로 마지막 120개 캔들 표시
    const defaultWindowSize = Math.min(120, formattedData.length);
    const defaultStart = Math.max(0, formattedData.length - defaultWindowSize);

    let result;
    if (viewWindow) {
      result = formattedData.slice(viewWindow.startIndex, viewWindow.endIndex + 1);
    } else {
      result = formattedData.slice(defaultStart);
    }

    console.log('📊 Chart Debug:', {
      formattedDataLength: formattedData.length,
      defaultWindowSize,
      defaultStart,
      viewWindow,
      displayDataLength: result.length,
    });

    // 처음 10개 데이터 상세 출력
    const first10 = result.slice(0, 10).map((d, idx) => ({
      index: idx,
      time: new Date(d.time).toLocaleTimeString('ko-KR'),
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close
    }));
    console.log('📊 처음 10개 데이터:', JSON.stringify(first10, null, 2));

    return result;
  }, [formattedData, viewWindow]);

  // React 합성 이벤트 핸들러들
  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    if (event.button !== 0) return;

    setIsDragging(true);
    const currentStart = viewWindow?.startIndex ?? Math.max(0, formattedData.length - 120);
    setDragStart({ x: event.clientX, startIndex: currentStart });

    if (!viewWindow && formattedData.length > 0) {
      const windowSize = Math.min(120, formattedData.length);
      const defaultStart = Math.max(0, formattedData.length - windowSize);
      setViewWindow({
        startIndex: defaultStart,
        endIndex: defaultStart + windowSize - 1
      });
    }
    event.preventDefault();
  }, [viewWindow, formattedData.length]);

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (!isDragging || !dragStart || formattedData.length === 0) return;

    const deltaX = event.clientX - dragStart.x;
    const candlesPerPixel = (viewWindow.endIndex - viewWindow.startIndex) / chartWidth;
    const deltaCandles = Math.round(deltaX * candlesPerPixel);

    const windowSize = viewWindow.endIndex - viewWindow.startIndex;
    const newStartIndex = Math.max(0, Math.min(
      dragStart.startIndex - deltaCandles,
      formattedData.length - windowSize
    ));
    
    if (newStartIndex !== viewWindow.startIndex) {
        setViewWindow({ startIndex: newStartIndex, endIndex: newStartIndex + windowSize });
    }

  }, [isDragging, dragStart, formattedData.length, viewWindow, chartWidth]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setDragStart(null);
  }, []);

  const yDomain = useMemo(() => {
    if (!displayData || displayData.length === 0) {
      return [0, 0] as [number, number];
    }

    // Y-domain is based on visible data's prices
    const prices = displayData.flatMap(d => [d.open, d.high, d.low, d.close]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const padding = (maxPrice - minPrice) * 0.1;
    const calculatedYDomain: [number, number] = [Math.floor(minPrice - padding), Math.ceil(maxPrice + padding)];

    return calculatedYDomain;
  }, [displayData]);

  // 조건부 렌더링은 훅 호출 후에
  if (formattedData.length === 0) {
    return (
      <div
        className="bg-[#0a0a0b] border border-gray-700 rounded-lg flex items-center justify-center"
        style={{ height }}
      >
        <div className="text-center text-gray-400">
          <div className="text-yellow-400 mb-2">📊 데이터 없음</div>
          <div className="text-xs">표시할 차트 데이터가 없습니다</div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="bg-[#0a0a0b] border border-gray-700 rounded-lg p-2"
      style={{
        height,
        cursor: isDragging ? 'grabbing' : 'grab',
        userSelect: 'none'
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={displayData} // 표시할 데이터만 사용
          margin={{ top: 20, right: 80, left: 20, bottom: 20 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={KOREAN_CHART_THEME.gridColor}
            opacity={0.3}
          />

          <XAxis
            dataKey="time"
            ticks={
              // 15분 간격으로만 tick 표시
              displayData
                .filter((_, idx) => {
                  const date = new Date(displayData[idx].time);
                  const minutes = date.getMinutes();
                  // 0, 15, 30, 45분만 표시
                  return minutes % 15 === 0;
                })
                .map(d => d.time)
            }
            tickFormatter={(time) => {
              const date = new Date(time);
              return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
            }}
            stroke={KOREAN_CHART_THEME.textColor}
            fontSize={12}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 10 }}
          />

          <YAxis
            domain={yDomain}
            tickFormatter={(value) => {
              const tickUnit = getTickUnitByPrice(value);
              const roundedValue = Math.round(value / tickUnit) * tickUnit;
              return roundedValue.toLocaleString();
            }}
            stroke={KOREAN_CHART_THEME.textColor}
            fontSize={12}
            axisLine={false}
            tickLine={false}
            orientation="right"
            tickCount={8}
            width={80}
          />

          <Tooltip
            content={<CustomTooltip />}
            cursor={{ stroke: KOREAN_CHART_THEME.textColor, strokeWidth: 1, strokeDasharray: '3 3' }}
          />

          <Line
            dataKey="close"
            stroke="none"
            dot={createCandlestickDot(yDomain, height, displayData.length, chartWidth)}
            isAnimationActive={false}
            yAxisId={0}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RechartsAdapter;