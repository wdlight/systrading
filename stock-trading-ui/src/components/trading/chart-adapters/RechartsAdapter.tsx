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
import { ChartAdapterProps, KOREAN_CHART_THEME } from './ChartAdapter';
import { YAxisCalculatorFactory, YAxisCalculator } from './core/YAxisCalculator';

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

  const CandlestickDotComponent = (props: any) => {
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

  CandlestickDotComponent.displayName = 'CandlestickDot';

  return CandlestickDotComponent;
};

// 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length > 0) {
    const data = payload[0].payload;
    const date = new Date(data.time);
    const timeStr = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

    return (
      <div className="rounded-lg border border-gray-600 bg-gray-800 p-2 text-xs font-medium text-gray-100">
        <p className="mb-1 font-medium text-gray-200">
          {timeStr}
        </p>
        <div className="space-y-1 text-[11px]">
          <p><span className="text-gray-400">시가:</span> <span className="text-white">{data.open.toLocaleString()}</span></p>
          <p><span className="text-gray-400">고가:</span> <span className="text-rose-300">{data.high.toLocaleString()}</span></p>
          <p><span className="text-gray-400">저가:</span> <span className="text-blue-300">{data.low.toLocaleString()}</span></p>
          <p><span className="text-gray-400">종가:</span> <span className="text-white">{data.close.toLocaleString()}</span></p>
          {data.volume && (
            <p><span className="text-gray-400">거래량:</span> <span className="text-amber-300">{data.volume.toLocaleString()}</span></p>
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
  yAxisCalculator,
  events,
  config,
}) => {
  // Backward compatibility: onError, onBrushChange
  const onError = events?.onError;
  const onBrushChange = events?.onRangeChange;

  // Y축 계산기 가져오기
  const calculator = useMemo(() => {
    if (!yAxisCalculator) {
      return YAxisCalculatorFactory.get('daily-range'); // 기본값
    }
    if (typeof yAxisCalculator === 'string') {
      return YAxisCalculatorFactory.get(yAxisCalculator);
    }
    return yAxisCalculator;
  }, [yAxisCalculator]);
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
      }).map((candle, index) => ({
        ...candle,
        dataIndex: index,  // ✅ 인덱스 추가 (0, 1, 2, ...)
      }));

      // 🔍 디버그: 데이터 상세 로그 활성화
      console.log(`🔄 데이터 중복 제거: ${mapped.length}개 → ${uniqueData.length}개`);
      console.log('--- FRONTEND DATA VALIDATION ---');
      console.log(`Total candles for chart: ${uniqueData.length}`);
      if (uniqueData.length > 0) {
        const formatForLog = (d: any) => ({
          time: new Date(d.time).toISOString(),
          dataIndex: d.dataIndex,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        });
        console.log('First 10 candles:', JSON.stringify(uniqueData.slice(0, 10).map(formatForLog), null, 2));
        console.log('Last 10 candles:', JSON.stringify(uniqueData.slice(-10).map(formatForLog), null, 2));
      }
      console.log('---------------------------------');

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

  // ✅ 인덱스 기반 X축: xDomain 삭제됨 (더 이상 필요 없음)

  // ✅ 디버그 로그 (인덱스 기반)
  useEffect(() => {
    if (formattedData.length > 0 && viewWindow) {
      console.log('📊 Chart State (Index-based):', {
        totalCandles: formattedData.length,
        viewWindow,
        visibleRange: `Index ${viewWindow.startIndex} ~ ${viewWindow.endIndex}`,
        firstCandle: new Date(formattedData[0].time).toLocaleTimeString(),
        lastCandle: new Date(formattedData[formattedData.length - 1].time).toLocaleTimeString(),
      });
    }
  }, [formattedData.length, viewWindow, formattedData]);

  // React 합성 이벤트 핸들러들
  // Initialize viewWindow when data is available
  useEffect(() => {
    // Initialize viewWindow only when data is available AND chart width has been calculated
    if (formattedData.length > 0 && !viewWindow && chartWidth > 0 && chartWidth !== 1000) {
      const windowSize = Math.min(120, formattedData.length);

      // ✅ 데이터 중앙에 윈도우 배치 (균형있는 초기 화면)
      const centerIndex = Math.floor(formattedData.length / 2);
      const defaultStart = Math.max(0, centerIndex - Math.floor(windowSize / 2));
      const defaultEnd = Math.min(defaultStart + windowSize - 1, formattedData.length - 1);

      setViewWindow({
        startIndex: defaultStart,
        endIndex: defaultEnd
      });

      // 🔍 디버그: 초기 viewWindow 설정 로그
      console.log('🎬 Initial viewWindow (centered):', {
        startIndex: defaultStart,
        endIndex: defaultEnd,
        centerIndex,
        windowSize,
        totalData: formattedData.length,
        firstVisibleTime: new Date(formattedData[defaultStart].time).toISOString(),
        lastVisibleTime: new Date(formattedData[defaultEnd].time).toISOString(),
      });
    }
  }, [formattedData, viewWindow, chartWidth, formattedData.length]);

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

        // 성능 최적화: 드래그 중 console.log 제거
        // console.log('🖱️ Drag Update:', { ... });

        setViewWindow({ startIndex: newStartIndex, endIndex: newEndIndex });
    }

  }, [isDragging, dragStart, formattedData.length, viewWindow, chartWidth]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setDragStart(null);
  }, []);

  // 🎯 Y축 도메인 계산 (YAxisCalculator 사용)
  const yDomain = useMemo(() => {
    if (!chartData || chartData.length === 0) {
      return [0, 0] as [number, number];
    }

    // ✅ YAxisCalculator를 통한 Y축 계산
    const domain = calculator.calculate(chartData);

    // 성능 최적화: 초기 로딩 시에만 로그 출력
    // 📊 상세 디버깅: 날짜 범위 및 가격 범위 확인 (개발 중에만 활성화)
    // const timestamps = chartData.map(c => new Date(c.timestamp));
    // const minDate = new Date(Math.min(...timestamps.map(d => d.getTime())));
    // const maxDate = new Date(Math.max(...timestamps.map(d => d.getTime())));
    // const allPrices = chartData.flatMap(c => [c.high, c.low]);
    // const actualMin = Math.min(...allPrices);
    // const actualMax = Math.max(...allPrices);
    //
    // console.log(`📊 Y축 계산 (${calculator.name}):`, {
    //   range: `${domain[0].toLocaleString()} ~ ${domain[1].toLocaleString()}`,
    //   calculator: calculator.name,
    //   dataPoints: chartData.length,
    //   dateRange: `${minDate.toLocaleDateString('ko-KR')} ~ ${maxDate.toLocaleDateString('ko-KR')}`,
    //   actualPriceRange: `${actualMin.toLocaleString()} ~ ${actualMax.toLocaleString()}`,
    //   daysCovered: Math.ceil((maxDate.getTime() - minDate.getTime()) / (1000 * 60 * 60 * 24))
    // });

    return domain;
  }, [chartData, calculator]); // chartData 변경 시에만 재계산

  // ⚡ XAxis ticks 메모이제이션 (시간 기반, 30분 단위)
  const xAxisTicks = useMemo(() => {
    // 시간 기준으로 30분 단위 tick 생성 (9:00, 9:30, 10:00, ...)
    const ticks: number[] = [];

    formattedData.forEach((candle, index) => {
      const date = new Date(candle.time);
      const minutes = date.getMinutes();

      // 30분 단위 (00분, 30분)에만 tick 표시
      if (minutes === 0 || minutes === 30) {
        // viewWindow가 있으면 범위 내에서만
        if (viewWindow) {
          if (index >= viewWindow.startIndex && index <= viewWindow.endIndex) {
            ticks.push(candle.dataIndex);
          }
        } else {
          // viewWindow 없으면 마지막 120개 범위에서
          const start = Math.max(0, formattedData.length - 120);
          if (index >= start) {
            ticks.push(candle.dataIndex);
          }
        }
      }
    });

    return ticks;
  }, [formattedData, viewWindow]);

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
          data={formattedData} // ✅ 전체 데이터 사용 (Brush로 범위 제어)
          margin={{ top: 20, right: 80, left: 20, bottom: 20 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke={KOREAN_CHART_THEME.gridColor}
            opacity={0.3}
          />

          <XAxis
            dataKey="dataIndex"
            type="number"
            domain={['dataMin', 'dataMax']}
            allowDataOverflow={false}
            ticks={xAxisTicks}
            tickFormatter={(dataIndex) => {
              const candle = formattedData[dataIndex];
              if (!candle) return '';

              const date = new Date(candle.time);
              const hours = date.getHours();
              const minutes = date.getMinutes();

              // ✅ 9:00이면 날짜 경계 표시 (줄바꿈으로 날짜와 시간 구분)
              if (hours === 9 && minutes === 0) {
                const month = date.getMonth() + 1;
                const day = date.getDate();
                return `${month}/${day}\n9:00`;
              }

              return `${hours}:${minutes.toString().padStart(2, '0')}`;
            }}
            stroke={KOREAN_CHART_THEME.textColor}
            axisLine={false}
            tickLine={false}
            tick={{ fontSize: 11, fill: KOREAN_CHART_THEME.textColor, fontFamily: 'Inter, ui-sans-serif, system-ui' }}
          />

          <YAxis
            domain={yDomain}
            tickFormatter={(value) => {
              const tickUnit = getTickUnitByPrice(value);
              const roundedValue = Math.round(value / tickUnit) * tickUnit;
              return roundedValue.toLocaleString();
            }}
            stroke={KOREAN_CHART_THEME.textColor}
            axisLine={false}
            tickLine={false}
            orientation="right"
            tickCount={8}
            width={72}
            tick={{ fontSize: 11, fill: KOREAN_CHART_THEME.textColor, fontFamily: 'Inter, ui-sans-serif, system-ui' }}
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

          {/* Brush for infinite scroll (index-based) */}
          <Brush
            data={formattedData}
            dataKey="dataIndex"
            height={30}
            stroke={KOREAN_CHART_THEME.gridColor}
            fill={KOREAN_CHART_THEME.backgroundColor}
            startIndex={viewWindow?.startIndex ?? Math.max(0, formattedData.length - 120)}
            endIndex={viewWindow?.endIndex ?? formattedData.length - 1}
            onChange={(brushData: any) => {
              // 성능 최적화: console.log 제거
              // console.log('🔥 Brush onChange triggered:', brushData);
              if (onBrushChange && brushData) {
                const { startIndex, endIndex } = brushData;
                // console.log('[RechartsAdapter] Brush changed:', { startIndex, endIndex, totalData: formattedData.length });
                onBrushChange({ startIndex: startIndex ?? 0, endIndex: endIndex ?? formattedData.length - 1 });
              }
            }}
            tickFormatter={(dataIndex) => {
              const candle = formattedData[dataIndex];
              if (!candle) return '';

              const date = new Date(candle.time);
              const hours = date.getHours();
              const minutes = date.getMinutes();

              // ✅ 9:00이면 날짜 경계 표시 (Brush용 - 한 줄로 표시)
              if (hours === 9 && minutes === 0) {
                const month = date.getMonth() + 1;
                const day = date.getDate();
                return `${month}/${day} 9:00`;
              }

              return `${hours}:${minutes.toString().padStart(2, '0')}`;
            }}
            traveller={{width: 10}}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RechartsAdapter;
