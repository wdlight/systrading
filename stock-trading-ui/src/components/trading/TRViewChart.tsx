// components/trading/TRViewChart.tsx
'use client';

import { useEffect, useRef, useMemo } from 'react';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickSeries,
  HistogramSeries
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
  const lastCandleRef = useRef<ChartCandle | null>(null);

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
  }, [height, showVolume]);

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
    if (candleSeriesRef.current) {
      if (candleData && candleData.length > 0) {
        candleSeriesRef.current.setData(candleData);
        chartRef.current?.timeScale().fitContent();
        lastCandleRef.current = chartData[chartData.length - 1];
      } else {
        candleSeriesRef.current.setData([]);
      }
    }
    if (volumeSeriesRef.current) {
        if (volumeData && volumeData.length > 0) {
            volumeSeriesRef.current.setData(volumeData);
        } else {
            volumeSeriesRef.current.setData([]);
        }
    }
  }, [candleData, volumeData, chartData]);

  return (
    <div
      ref={chartContainerRef}
      className={`bg-[#0a0a0b] border border-gray-700 rounded-lg ${className}`}
    />
  );
}
