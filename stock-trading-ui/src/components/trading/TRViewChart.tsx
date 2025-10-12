// components/trading/TRViewChart.tsx
'use client';

import { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickSeries,
  HistogramSeries,
  LogicalRange
} from 'lightweight-charts';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { getTRViewChartOptions } from '@/lib/tradingview/chartConfig';
import {
  convertToTRViewCandles,
  convertToTRViewVolumes
} from '@/lib/tradingview/dataConverter';
import { CHART_COLORS } from '@/lib/tradingview/constants';

interface TRViewChartProps {
  chartData: ChartCandle[];
  height?: number;
  showVolume?: boolean;
  showGrid?: boolean;
  enableCrosshair?: boolean;
  className?: string;
  timeframe?: 'minute' | 'day';
  onReady?: (api: {
    updateCandle: (candle: ChartCandle) => void;
    chart: IChartApi;
  }) => void;
  onLoadPrevious?: () => void;
  isLoadingMore?: boolean;
  initialVisibleCandles?: number;
  hasExtendedRange?: boolean;
}

export function TRViewChart({
  chartData,
  height = 500,
  showVolume = true,
  showGrid = true,
  enableCrosshair = true,
  className = '',
  timeframe = 'minute',
  onReady,
  onLoadPrevious,
  isLoadingMore,
  initialVisibleCandles,
  hasExtendedRange = false,
}: TRViewChartProps) {
  const [legendData, setLegendData] = useState<any>(null);
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const lastCandleRef = useRef<ChartCandle | null>(null);
  const loadingIndicatorRef = useRef<HTMLDivElement>(null);

  const formatKST = useCallback(
    (
      date: Date,
      options: Intl.DateTimeFormatOptions
    ) =>
      new Intl.DateTimeFormat('ko-KR', {
        timeZone: 'Asia/Seoul',
        hour12: false,
        ...options,
      }).format(date),
    []
  );

  const onReadyRef = useRef(onReady);
  useEffect(() => {
    onReadyRef.current = onReady;
  }, [onReady]);

  const candleData = useMemo(() => convertToTRViewCandles(chartData), [chartData]);
  const volumeData = useMemo(() => convertToTRViewVolumes(chartData), [chartData]);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      ...getTRViewChartOptions(),
      width: chartContainerRef.current.clientWidth,
      height,
    });
    chartRef.current = chart;
    chart.applyOptions({
      localization: {
        timeFormatter: (timestamp: number) =>
          formatKST(new Date(timestamp * 1000), {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          }),
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: CHART_COLORS.CANDLE_UP,
      downColor: CHART_COLORS.CANDLE_DOWN,
      borderUpColor: CHART_COLORS.CANDLE_UP,
      borderDownColor: CHART_COLORS.CANDLE_DOWN,
      wickUpColor: CHART_COLORS.CANDLE_UP,
      wickDownColor: CHART_COLORS.CANDLE_DOWN,
    });
    candleSeriesRef.current = candleSeries;

    if (showVolume) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: { type: 'volume' },
        priceScaleId: 'volume',
      });
      volumeSeriesRef.current = volumeSeries;
      chart.priceScale('volume').applyOptions({
        scaleMargins: { top: 0.8, bottom: 0 },
      });
    }

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    if (onReadyRef.current) {
      onReadyRef.current({
        updateCandle: (candle: ChartCandle) => {
          const converted = convertToTRViewCandles([candle])[0];
          candleSeries.update(converted);

          if (volumeSeriesRef.current) {
            const prevClose = lastCandleRef.current?.close ?? candle.open;
            const isUp = candle.close >= prevClose;
            volumeSeriesRef.current.update({
              time: converted.time,
              value: candle.volume,
              color: isUp ? CHART_COLORS.VOLUME_UP : CHART_COLORS.VOLUME_DOWN,
            });
          }
          lastCandleRef.current = candle;
        },
        chart,
      });
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, showVolume, formatKST]);

  useEffect(() => {
    if (!chartRef.current) return;
    chartRef.current.applyOptions({
      grid: { vertLines: { visible: showGrid }, horzLines: { visible: showGrid } },
    });
  }, [showGrid]);

  useEffect(() => {
    if (!chartRef.current) return;
    chartRef.current.applyOptions({ crosshair: { mode: enableCrosshair ? 1 : 0 } });
  }, [enableCrosshair]);

  useEffect(() => {
    if (volumeSeriesRef.current) {
        volumeSeriesRef.current.applyOptions({ visible: showVolume });
    }
  }, [showVolume]);

  useEffect(() => {
    if (!chartRef.current) return;

    const isDay = timeframe === 'day';

    chartRef.current.timeScale().applyOptions({
      timeVisible: !isDay,
      secondsVisible: false,
      // tickMarkFormatter는 lightweight-charts 타입 정의에 없으므로 주석 처리
      // tickMarkFormatter: (time: number) => {
      //   const date = new Date(time * 1000);
      //
      //   if (isDay) {
      //     return formatKST(date, {
      //       year: 'numeric',
      //       month: '2-digit',
      //       day: '2-digit',
      //     });
      //   } else {
      //     return formatKST(date, {
      //       hour: '2-digit',
      //       minute: '2-digit',
      //     });
      //   }
      // },
    });
  }, [timeframe, formatKST]);

  useEffect(() => {
    const chart = chartRef.current;
    const candleSeries = candleSeriesRef.current;
    if (candleSeries && chart) {
      if (candleData && candleData.length > 0) {
        candleSeries.setData(candleData);
        lastCandleRef.current = chartData[chartData.length - 1];

        if (!hasExtendedRange) {
          const total = candleData.length;
          const targetCount = initialVisibleCandles ?? total;
          const visibleCount = Math.min(targetCount, total);
          const from = Math.max(0, total - visibleCount);
          const to = total;
          chart.timeScale().setVisibleLogicalRange({ from, to });
        }
      } else {
        candleSeries.setData([]);
      }
    }
    if (volumeSeriesRef.current) {
        if (volumeData && volumeData.length > 0) {
            volumeSeriesRef.current.setData(volumeData);
        }
        else {
            volumeSeriesRef.current.setData([]);
        }
    }
  }, [candleData, volumeData, chartData, hasExtendedRange, initialVisibleCandles]);

  useEffect(() => {
    if (!chartRef.current || !onLoadPrevious) return;

    const chart = chartRef.current;
    const timeScale = chart.timeScale();

    const handleRangeChange = (range: LogicalRange | null) => {
      if (range && range.from < 10 && !isLoadingMore) {
        onLoadPrevious();
      }
    };

    timeScale.subscribeVisibleLogicalRangeChange(handleRangeChange);

    return () => {
      timeScale.unsubscribeVisibleLogicalRangeChange(handleRangeChange);
    };
  }, [onLoadPrevious, isLoadingMore]);

  useEffect(() => {
    if (!loadingIndicatorRef.current) return;
    loadingIndicatorRef.current.style.display = isLoadingMore ? 'block' : 'none';
  }, [isLoadingMore]);

  // OHLC Legend Logic
  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current) {
      return;
    }
    const chart = chartRef.current;
    const candleSeries = candleSeriesRef.current;

    const handleCrosshairMove = (param: any) => {
      if (
        !param.time ||
        !param.seriesData.has(candleSeries)
      ) {
        setLegendData(null);
        return;
      }
      const candle = param.seriesData.get(candleSeries);
      const volume = volumeSeriesRef.current ? param.seriesData.get(volumeSeriesRef.current) : null;
      setLegendData({ ...candle, volume: volume?.value });
    };

    chart.subscribeCrosshairMove(handleCrosshairMove);

    return () => {
      chart.unsubscribeCrosshairMove(handleCrosshairMove);
    };
  }, [chartData]); // Re-run when data changes, ensuring subscription is on the correct series

  return (
    <div style={{ position: 'relative' }} className={className}>
      {/* 정보창(Legend) UI */}
      {legendData && (
        <div
          style={{
            position: 'absolute',
            top: '10px',
            left: '10px',
            zIndex: 20,
            padding: '8px',
            background: 'rgba(26, 26, 27, 0.8)',
            border: '1px solid #333',
            borderRadius: '4px',
            color: 'white',
            fontSize: '12px',
            pointerEvents: 'none',
          }}
        >
          <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>
            {formatKST(new Date(legendData.time * 1000), {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </div>
          <div>O: <span style={{ color: '#22c55e' }}>{legendData.open}</span></div>
          <div>H: <span style={{ color: '#ef4444' }}>{legendData.high}</span></div>
          <div>L: <span style={{ color: '#3b82f6' }}>{legendData.low}</span></div>
          <div>C: <span style={{ color: '#f97316' }}>{legendData.close}</span></div>
          {legendData.volume && <div>Vol: {legendData.volume.toLocaleString()}</div>}
        </div>
      )}

      <div
        ref={chartContainerRef}
        className="bg-[#0a0a0b] border border-gray-700 rounded-lg"
      />
      <div
        ref={loadingIndicatorRef}
        style={{
          position: 'absolute',
          top: '10px',
          left: '50px',
          display: 'none',
          color: 'white',
          background: 'rgba(0, 0, 0, 0.5)',
          padding: '5px 10px',
          borderRadius: '5px',
          zIndex: 10,
        }}
      >
        이전 데이터 로딩 중...
      </div>
    </div>
  );
}
