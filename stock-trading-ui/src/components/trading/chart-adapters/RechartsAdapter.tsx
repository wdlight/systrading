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

    const { open, high, low, close, timestamp, volume } = payload;

    // Calculate Y positions using our custom scale
    const yHigh = yScale(high);
    const yLow = yScale(low);
    const yOpen = yScale(open);
    const yClose = yScale(close);

    const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1);
    const bodyY = Math.min(yOpen, yClose);
    // 캔들 너비 계산: 고정 4픽셀 두께 (기존 6px에서 2px 감소)
    const candleWidth = 4;

    // 미래 데이터 판단: volume=0 또는 timestamp가 현재 시각 이후
    const now = new Date().getTime();
    const candleTime = new Date(timestamp).getTime();
    const isFutureData = volume === 0 || candleTime > now;

    // Korean style: red=up, blue=down
    const isRising = close >= open;

    // 미래 데이터는 회색/투명, 실제 데이터는 정상 색상
    let fillColor = isRising ? '#ef4444' : '#3b82f6';
    let strokeColor = isRising ? '#dc2626' : '#2563eb';
    let opacity = 1.0;

    if (isFutureData) {
      fillColor = '#6b7280';  // gray-500
      strokeColor = '#4b5563'; // gray-600
      opacity = 0.3;
    }

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
      <g key={uniqueKey} opacity={opacity}>
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

        {/* 미래 데이터 표시: 점선 테두리 */}
        {isFutureData && (
          <rect
            x={cx - candleWidth / 2}
            y={bodyY}
            width={candleWidth}
            height={bodyHeight}
            fill="none"
            stroke={strokeColor}
            strokeWidth={1}
            strokeDasharray="2,2"
          />
        )}
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
  onError,
  onBrushChange
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

  // X축 시간 domain 계산 (viewWindow 기준)
  const xDomain = useMemo(() => {
    if (formattedData.length === 0) {
      return [0, 0];
    }

    // ✅ 수정: viewWindow의 실제 시간 범위 사용
    if (viewWindow) {
      const startTime = new Date(formattedData[viewWindow.startIndex].time).getTime();
      // endIndex의 실제 시간 사용 (120분 고정이 아닌 실제 데이터 범위)
      const endTime = new Date(formattedData[viewWindow.endIndex].time).getTime();
      return [startTime, endTime];
    }

    // 기본: 마지막 120개 데이터 범위
    const defaultWindowSize = Math.min(120, formattedData.length);
    const defaultStart = Math.max(0, formattedData.length - defaultWindowSize);
    const startTime = new Date(formattedData[defaultStart].time).getTime();
    const lastTime = new Date(formattedData[formattedData.length - 1].time).getTime();
    return [startTime, lastTime];
  }, [formattedData, viewWindow]);

  // ✅ displayData는 더 이상 사용하지 않음 (전체 데이터를 차트에 전달)
  // 디버그용 로그만 유지
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

  // React 합성 이벤트 핸들러들
  // Initialize viewWindow when data is available
  useEffect(() => {
    if (formattedData.length > 0 && !viewWindow) {
      const windowSize = Math.min(120, formattedData.length);
      const defaultStart = Math.max(0, formattedData.length - windowSize);
      // ✅ 수정: endIndex가 배열 범위를 벗어나지 않도록 보장
      const defaultEnd = Math.min(defaultStart + windowSize - 1, formattedData.length - 1);
      setViewWindow({
        startIndex: defaultStart,
        endIndex: defaultEnd
      });

      console.log('🎬 Initial viewWindow:', {
        startIndex: defaultStart,
        endIndex: defaultEnd,
        windowSize: defaultEnd - defaultStart + 1,
        startTime: new Date(formattedData[defaultStart].time).toLocaleTimeString(),
        endTime: new Date(formattedData[defaultEnd].time).toLocaleTimeString(),
      });
    }
  }, [formattedData.length, viewWindow, formattedData]);

  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    if (event.button !== 0 || !viewWindow) return;

    setIsDragging(true);
    setDragStart({ x: event.clientX, startIndex: viewWindow.startIndex });
    event.preventDefault();
  }, [viewWindow]);

  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (!isDragging || !dragStart || formattedData.length === 0 || !viewWindow) return;

    const deltaX = event.clientX - dragStart.x;
    const candlesPerPixel = (viewWindow.endIndex - viewWindow.startIndex) / chartWidth;
    const deltaCandles = Math.round(deltaX * candlesPerPixel);

    const windowSize = viewWindow.endIndex - viewWindow.startIndex;
    // ✅ 수정: 드래그 방향 반전 (좌측 드래그 시 startIndex 감소)
    const newStartIndex = Math.max(0, Math.min(
      dragStart.startIndex - deltaCandles,  // 좌측(-) 드래그 → startIndex 감소
      formattedData.length - windowSize - 1
    ));

    if (newStartIndex !== viewWindow.startIndex) {
        // ✅ 수정: endIndex가 데이터 범위를 벗어나지 않도록 제한
        const newEndIndex = Math.min(newStartIndex + windowSize, formattedData.length - 1);

        console.log('🖱️ Drag Update:', {
          deltaX,
          deltaCandles,
          oldStart: viewWindow.startIndex,
          newStart: newStartIndex,
          newEnd: newEndIndex,
          oldTime: new Date(formattedData[viewWindow.startIndex].time).toLocaleTimeString(),
          newTime: new Date(formattedData[newStartIndex].time).toLocaleTimeString(),
        });

        setViewWindow({ startIndex: newStartIndex, endIndex: newEndIndex });
    }

  }, [isDragging, dragStart, formattedData.length, viewWindow, chartWidth]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setDragStart(null);
  }, []);

  // 🎯 Y축 고정: 일별 최고/최저점 기준 90% 범위
  const yDomain = useMemo(() => {
    if (!formattedData || formattedData.length === 0) {
      return [0, 0] as [number, number];
    }

    // ✅ 당일 전체 데이터의 실제 가격 범위 계산
    const actualPrices = formattedData.flatMap(d => [d.high, d.low]);
    const actualMin = Math.min(...actualPrices);
    const actualMax = Math.max(...actualPrices);

    // 가격 범위 계산
    const priceRange = actualMax - actualMin;

    // 90% 범위로 여유 공간 확보 (상하 각 5% 패딩)
    // 실제 범위의 상하에 5%씩 여유를 둠
    const padding = priceRange * 0.05;
    const rawLowerLimit = actualMin - padding;
    const rawUpperLimit = actualMax + padding;

    // 호가 단위 기준으로 Y축 범위를 깔끔하게 정렬
    const avgPrice = (actualMin + actualMax) / 2;
    const tickUnit = getTickUnitByPrice(avgPrice);

    const finalLowerLimit = Math.floor(rawLowerLimit / tickUnit) * tickUnit;
    const finalUpperLimit = Math.ceil(rawUpperLimit / tickUnit) * tickUnit;

    console.log('📊 Y축 고정 (일별 최고/최저 기준 90% 범위):', {
      actualMin: actualMin.toLocaleString(),
      actualMax: actualMax.toLocaleString(),
      priceRange: priceRange.toLocaleString(),
      padding: `${(padding).toFixed(0)} (5%)`,
      tickUnit,
      finalRange: `${finalLowerLimit.toLocaleString()} ~ ${finalUpperLimit.toLocaleString()}`,
      rangeRatio: ((finalUpperLimit - finalLowerLimit) / priceRange).toFixed(2)
    });

    return [finalLowerLimit, finalUpperLimit] as [number, number];
  }, [formattedData]); // ❌ xDomain 의존성 제거 → drag해도 Y축 불변

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
          data={formattedData} // ✅ 전체 데이터 사용 (좌측 드래그로 과거 데이터 조회 가능)
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
            domain={xDomain}
            scale="time"
            ticks={
              // 15분 간격으로만 tick 표시 (120분 영역 기준)
              (() => {
                const ticks = [];
                const [start, end] = xDomain;
                const startDate = new Date(start);

                // 시작 시간을 15분 단위로 올림
                const startMinutes = startDate.getMinutes();
                const nextQuarter = Math.ceil(startMinutes / 15) * 15;
                startDate.setMinutes(nextQuarter, 0, 0);

                let currentTime = startDate.getTime();
                while (currentTime <= end) {
                  ticks.push(currentTime);
                  currentTime += 15 * 60 * 1000; // 15분씩 증가
                }

                return ticks;
              })()
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
            dot={createCandlestickDot(yDomain, height, formattedData.length, chartWidth)}
            isAnimationActive={false}
            yAxisId={0}
          />

          {/* Brush for infinite scroll */}
          <Brush
            data={formattedData}
            dataKey="time"
            height={30}
            stroke={KOREAN_CHART_THEME.gridColor}
            fill={KOREAN_CHART_THEME.backgroundColor}
            startIndex={viewWindow?.startIndex ?? Math.max(0, formattedData.length - 120)}
            endIndex={viewWindow?.endIndex ?? formattedData.length - 1}
            onChange={(brushData: any) => {
              console.log('🔥 Brush onChange triggered:', brushData);
              if (onBrushChange && brushData) {
                const { startIndex, endIndex } = brushData;
                console.log('[RechartsAdapter] Brush changed:', { startIndex, endIndex, totalData: formattedData.length });
                onBrushChange({ startIndex: startIndex ?? 0, endIndex: endIndex ?? formattedData.length - 1 });
              } else {
                console.log('⚠️ Brush onChange called but no data:', { onBrushChange: !!onBrushChange, brushData });
              }
            }}
            tickFormatter={(time) => {
              const date = new Date(time);
              return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
            }}
            traveller={{width: 10}}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RechartsAdapter;