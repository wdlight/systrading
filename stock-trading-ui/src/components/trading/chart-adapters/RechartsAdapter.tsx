'use client';

import React, { useMemo, useState, useCallback, useRef } from 'react';
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

// Factory function to create CandlestickDot with yDomain and height
const createCandlestickDot = (yDomain: [number, number], chartHeight: number) => {
  const yScale = createYScale(yDomain, chartHeight);

  return (props: any) => {
    const { cx, cy, payload, index, height, width } = props;

    if (!payload) {
      return null;
    }

    const { open, high, low, close } = payload;

    // Calculate Y positions using our custom scale
    const yHigh = yScale(high);
    const yLow = yScale(low);
    const yOpen = yScale(open);
    const yClose = yScale(close);

    const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1);
    const bodyY = Math.min(yOpen, yClose);
    const candleWidth = Math.min(width * 0.6, 8);

    // Korean style: red=up, blue=down
    const isRising = close >= open;
    const fillColor = isRising ? '#ef4444' : '#3b82f6';
    const strokeColor = isRising ? '#dc2626' : '#2563eb';

    if (index === 0) {
      console.log('✅ CandlestickDot rendering:', {
        payload: { open, high, low, close },
        positions: { yHigh, yLow, yOpen, yClose },
        bodyHeight,
        candleWidth
      });
    }

    return (
      <g>
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
    return (
      <div className="bg-gray-800 border border-gray-600 rounded-lg p-3 text-sm">
        <p className="text-gray-300 mb-2">
          {new Date(data.time * 1000).toLocaleDateString('ko-KR')} {new Date(data.time * 1000).toLocaleTimeString('ko-KR')}
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
  onError
}) => {
  // 차트 스크롤 상태 관리
  const [viewWindow, setViewWindow] = useState<{ startIndex: number; endIndex: number } | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState<{ x: number; startIndex: number } | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 항상 모든 훅을 같은 순서로 호출
  const formattedData = useMemo(() => {
    try {
      if (!chartData || chartData.length === 0) {
        return [];
      }
      return chartData.map(candle => ({
        time: Math.floor(new Date(candle.timestamp).getTime() / 1000),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume || 0,
        // Recharts Bar 컴포넌트용 더미 값
        candlestick: candle.high - candle.low, // 심지 높이
      })).sort((a, b) => a.time - b.time);
    } catch (error) {
      console.error('Failed to format chart data:', error);
      onError?.('차트 데이터 포맷 변환 실패');
      return [];
    }
  }, [chartData, onError]);

  // 표시할 데이터 범위 계산
  const displayData = useMemo(() => {
    if (formattedData.length === 0) {
      console.log('⚠️ formattedData is empty');
      return [];
    }

    // 기본적으로 마지막 120개 캔들 표시 (전체 데이터)
    const defaultWindowSize = Math.min(120, formattedData.length);
    const defaultStart = Math.max(0, formattedData.length - defaultWindowSize);
    const defaultEnd = formattedData.length - 1;

    let result;
    if (viewWindow) {
      const start = Math.max(0, Math.min(viewWindow.startIndex, formattedData.length - 1));
      const end = Math.max(start, Math.min(viewWindow.endIndex, formattedData.length - 1));
      result = formattedData.slice(start, end + 1);
    } else {
      result = formattedData.slice(defaultStart, defaultEnd + 1);
    }

    console.log('📊 formattedData 전체 개수:', formattedData.length);
    console.log('📊 표시할 데이터 범위:', { defaultStart, defaultEnd });
    console.log('📊 표시할 데이터 개수:', result.length);
    console.log('📊 표시할 데이터 샘플 (첫 2개):', result.slice(0, 2));
    console.log('📊 표시할 데이터 가격 범위:', {
      minPrice: Math.min(...result.map(d => d.low)),
      maxPrice: Math.max(...result.map(d => d.high))
    });

    return result;
  }, [formattedData, viewWindow]);

  // React 합성 이벤트 핸들러들
  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    if (event.button !== 0) return; // 좌클릭만

    console.log('🖱️ 마우스 다운 시작');

    setIsDragging(true);
    const currentStart = viewWindow?.startIndex ?? Math.max(0, formattedData.length - 30);
    setDragStart({ x: event.clientX, startIndex: currentStart });

    // 뷰윈도우가 없으면 초기 설정 (120개로 변경)
    if (!viewWindow && formattedData.length > 0) {
      const windowSize = Math.min(120, formattedData.length);
      const defaultStart = Math.max(0, formattedData.length - windowSize);
      console.log('🔧 초기 뷰윈도우 설정:', { defaultStart, windowSize });
      setViewWindow({
        startIndex: defaultStart,
        endIndex: defaultStart + windowSize - 1
      });
    }

    console.log('🖱️ 마우스 다운:', {
      currentStart,
      formattedDataLength: formattedData.length,
      viewWindow: viewWindow
    });
    event.preventDefault();
  }, [viewWindow, formattedData.length]);

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (!isDragging || !dragStart || formattedData.length === 0) return;

    const deltaX = event.clientX - dragStart.x;
    const chartWidth = 1000; // 차트 너비 추정
    const candlesPerPixel = formattedData.length / chartWidth;
    const deltaCandles = Math.round(deltaX * candlesPerPixel * 0.3); // 감도 조정

    const windowSize = viewWindow ? (viewWindow.endIndex - viewWindow.startIndex + 1) : 120;
    // 오른쪽 드래그(+) → 인덱스 증가(오른쪽으로 이동)
    const newStartIndex = Math.max(0, Math.min(
      dragStart.startIndex + deltaCandles,
      formattedData.length - windowSize
    ));
    const newEndIndex = Math.min(newStartIndex + windowSize - 1, formattedData.length - 1);

    console.log('🖱️ 드래그 중:', {
      deltaX,
      deltaCandles,
      newStartIndex,
      newEndIndex,
      windowSize,
      totalLength: formattedData.length
    });

    setViewWindow({ startIndex: newStartIndex, endIndex: newEndIndex });
  }, [isDragging, dragStart, formattedData.length, viewWindow]);

  const handleMouseUp = useCallback(() => {
    console.log('🖱️ 마우스 업');
    setIsDragging(false);
    setDragStart(null);
  }, []);

  // 전역 mousemove와 mouseup 이벤트 리스너 (드래그 중에만)
  React.useEffect(() => {
    if (!isDragging) return;

    const handleGlobalMouseMove = (event: MouseEvent) => {
      if (!dragStart || formattedData.length === 0) return;

      const deltaX = event.clientX - dragStart.x;
      const chartWidth = 1000;
      const candlesPerPixel = formattedData.length / chartWidth;
      const deltaCandles = Math.round(deltaX * candlesPerPixel * 0.3);

      const windowSize = viewWindow ? (viewWindow.endIndex - viewWindow.startIndex + 1) : 120;
      // 오른쪽 드래그(+) → 인덱스 증가(오른쪽으로 이동)
      const newStartIndex = Math.max(0, Math.min(
        dragStart.startIndex + deltaCandles,
        formattedData.length - windowSize
      ));
      const newEndIndex = Math.min(newStartIndex + windowSize - 1, formattedData.length - 1);

      console.log('🖱️ 전역 드래그:', { deltaX, deltaCandles, newStartIndex, newEndIndex });
      setViewWindow({ startIndex: newStartIndex, endIndex: newEndIndex });
    };

    const handleGlobalMouseUp = () => {
      console.log('🖱️ 전역 마우스 업');
      setIsDragging(false);
      setDragStart(null);
    };

    document.addEventListener('mousemove', handleGlobalMouseMove);
    document.addEventListener('mouseup', handleGlobalMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [isDragging, dragStart, formattedData.length, viewWindow]);

  // Y축 도메인 계산 - 전체 데이터 기준으로 동적 설정
  const yDomain = useMemo(() => {
    if (formattedData.length === 0) {
      return [70000, 100000]; // 기본값
    }
    const allPrices = formattedData.flatMap(d => [d.open, d.high, d.low, d.close]);
    const min = Math.min(...allPrices);
    const max = Math.max(...allPrices);

    // 데이터 범위가 전체 차트의 80%를 차지하도록 계산
    // 실제 데이터 범위를 0.8로 나누면 전체 범위가 됨
    const dataRange = max - min;
    const totalRange = dataRange / 0.8; // 데이터가 80% 차지하도록
    const padding = (totalRange - dataRange) / 2; // 위아래 각각 10% 패딩

    const yMin = Math.floor(min - padding);
    const yMax = Math.ceil(max + padding);

    console.log(`📊 Y축 범위: ${yMin.toLocaleString()}원 ~ ${yMax.toLocaleString()}원 (전체 데이터: ${min.toLocaleString()}~${max.toLocaleString()}원, 데이터 비율: 80%)`);

    return [yMin, yMax];
  }, [formattedData]);

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

  console.log('🎨 Rendering RechartsAdapter with:', {
    dataLength: displayData.length,
    height,
    yDomain
  });

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
      <ResponsiveContainer width="100%" height="90%">
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
            type="number"
            scale="time"
            domain={['dataMin', 'dataMax']}
            ticks={
              // 10분 단위로만 tick 표시
              displayData.filter((_, idx) => {
                const date = new Date(displayData[idx].time * 1000);
                return date.getMinutes() % 10 === 0;
              }).map(d => d.time)
            }
            tickFormatter={(time) => {
              const date = new Date(time * 1000);
              const timeframe = chartData?.[0]?.timestamp ?
                (chartData[0].timestamp.includes('T') && chartData[0].timestamp.includes(':') ? '1m' : 'D') : 'D';

              if (timeframe === '1m') {
                // 분봉: 시간만 표시 (9:00, 9:10, 9:20, ...)
                return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
              } else {
                // 일봉: 날짜 표시
                return `${date.getMonth() + 1}/${date.getDate()}`;
              }
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
              // 천원 단위로 반올림하여 표시
              const roundedValue = Math.round(value / 1000) * 1000;
              return roundedValue.toLocaleString();
            }}
            stroke={KOREAN_CHART_THEME.textColor}
            fontSize={12}
            axisLine={false}
            tickLine={false}
            orientation="right"
            tickCount={6}
            width={80}
          />

          <Tooltip
            content={<CustomTooltip />}
            cursor={{ stroke: KOREAN_CHART_THEME.textColor, strokeWidth: 1, strokeDasharray: '3 3' }}
          />

          {/* 캔들스틱 렌더링 - Line 컴포넌트의 dot prop 사용 */}
          <Line
            dataKey="close"
            stroke="none"
            dot={createCandlestickDot(yDomain, height)}
            isAnimationActive={false}
            yAxisId={0}
          />
        </ComposedChart>
      </ResponsiveContainer>

      {/* 현재 보기 범위를 표시하는 고정 indicator */}
      <div className="relative mt-2 h-5 bg-gray-800 border border-gray-600 rounded">
        {/* 전체 데이터 대비 현재 표시 범위 표시 */}
        {viewWindow && formattedData.length > 0 && (
          <div
            className="absolute top-0 h-full bg-red-500 opacity-60 rounded"
            style={{
              left: `${(viewWindow.startIndex / formattedData.length) * 100}%`,
              width: `${Math.max(((viewWindow.endIndex - viewWindow.startIndex + 1) / formattedData.length) * 100, 1)}%`
            }}
          />
        )}
        <div className="text-xs text-gray-400 text-center leading-5">
          {viewWindow ?
            `${viewWindow.startIndex + 1}-${viewWindow.endIndex + 1} / ${formattedData.length}` :
            `${Math.max(0, formattedData.length - 30) + 1}-${formattedData.length} / ${formattedData.length}`
          }
        </div>
      </div>

      {/* 차트 라이브러리 표시 */}
      <div className="text-xs text-gray-500 text-right mt-1">
        Powered by Recharts | 좌클릭 드래그로 스크롤
      </div>
    </div>
  );
};

export default RechartsAdapter;