'use client';

import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useTradingStore, useSelectedSymbol, useCandlestickData } from '@/stores/tradingStore';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  ColorType,
  CrosshairMode,
  LineStyle,
  PriceScaleMode,
  Time,
  CandlestickSeries,
  HistogramSeries,
} from 'lightweight-charts';
import {
  BarChart3,
  TrendingUp,
  Clock,
  Maximize2,
  Settings,
  Volume2
} from 'lucide-react';

interface TradingChartProps {
  className?: string;
  height?: number;
}

export function TradingChart({ className, height = 400 }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const selectedSymbol = useSelectedSymbol();
  const candlestickData = useCandlestickData(selectedSymbol);
  const { chartType, timeframe, setChartType, setTimeframe } = useTradingStore();

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: {
          type: ColorType.Solid,
          color: '#1a1a1a'
        },
        textColor: '#d1d5db',
        fontSize: 12,
        fontFamily: 'Inter, system-ui, sans-serif',
      },
      grid: {
        vertLines: {
          color: 'rgba(255, 255, 255, 0.05)',
          style: LineStyle.Solid
        },
        horzLines: {
          color: 'rgba(255, 255, 255, 0.05)',
          style: LineStyle.Solid
        },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: 'rgba(59, 130, 246, 0.5)',
          width: 1,
          style: LineStyle.Dashed,
        },
        horzLine: {
          color: 'rgba(59, 130, 246, 0.5)',
          width: 1,
          style: LineStyle.Dashed,
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        mode: PriceScaleMode.Normal,
        autoScale: true,
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: true,
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true,
      },
    });

    // Add candlestick series
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderDownColor: '#ef4444',
      borderUpColor: '#10b981',
      wickDownColor: '#ef4444',
      wickUpColor: '#10b981',
      priceLineVisible: true,
      lastValueVisible: true,
      borderVisible: false,
    });

    // Add volume series
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: 'rgba(59, 130, 246, 0.3)',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: 'volume',
    });

    // Configure volume price scale
    chart.priceScale('volume').applyOptions({
      scaleMargins: {
        top: 0.7,
        bottom: 0,
      },
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;
    volumeSeriesRef.current = volumeSeries;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chart) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: isFullscreen ? window.innerHeight - 100 : height,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height, isFullscreen]);

  // Update chart data
  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || !candlestickData) return;

    const chartData = candlestickData.map(item => ({
      time: item.time as Time,
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    const volumeData = candlestickData.map(item => ({
      time: item.time as Time,
      value: item.volume,
      color: item.close >= item.open ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
    }));

    candlestickSeriesRef.current.setData(chartData);
    volumeSeriesRef.current.setData(volumeData);
  }, [candlestickData]);

  const timeframes = [
    { value: '1m', label: '1m' },
    { value: '5m', label: '5m' },
    { value: '15m', label: '15m' },
    { value: '1h', label: '1h' },
    { value: '4h', label: '4h' },
    { value: '1d', label: '1D' },
  ] as const;

  const chartTypes = [
    { value: 'candlestick', label: 'Candles', icon: BarChart3 },
    { value: 'line', label: 'Line', icon: TrendingUp },
  ] as const;

  return (
    <Card className={cn(
      "card-professional",
      isFullscreen && "fixed inset-4 z-50 h-[calc(100vh-2rem)]",
      className
    )}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-3 text-white">
            <div className="icon-bg-blue">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold">Price Chart</div>
              <div className="text-xs text-gray-400 font-normal">{selectedSymbol}</div>
            </div>
          </CardTitle>

          <div className="flex items-center gap-2">
            {/* Timeframe Selector */}
            <div className="flex bg-gray-800 rounded-lg p-1">
              {timeframes.map((tf) => (
                <Button
                  key={tf.value}
                  size="sm"
                  variant="ghost"
                  className={cn(
                    "h-7 px-2 text-xs font-medium transition-all",
                    timeframe === tf.value
                      ? "bg-blue-600 text-white shadow-sm"
                      : "text-gray-400 hover:text-white hover:bg-gray-700"
                  )}
                  onClick={() => setTimeframe(tf.value)}
                >
                  {tf.label}
                </Button>
              ))}
            </div>

            {/* Chart Type Selector */}
            <div className="flex bg-gray-800 rounded-lg p-1">
              {chartTypes.map((type) => {
                const Icon = type.icon;
                return (
                  <Button
                    key={type.value}
                    size="sm"
                    variant="ghost"
                    className={cn(
                      "h-7 px-2 text-xs font-medium transition-all",
                      chartType === type.value
                        ? "bg-blue-600 text-white shadow-sm"
                        : "text-gray-400 hover:text-white hover:bg-gray-700"
                    )}
                    onClick={() => setChartType(type.value)}
                  >
                    <Icon className="h-3 w-3 mr-1" />
                    {type.label}
                  </Button>
                );
              })}
            </div>

            {/* Chart Controls */}
            <div className="flex gap-1">
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0 text-gray-400 hover:text-white"
                onClick={() => setIsFullscreen(!isFullscreen)}
                title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
              >
                <Maximize2 className="h-3 w-3" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0 text-gray-400 hover:text-white"
                title="Chart settings"
              >
                <Settings className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div
          ref={chartContainerRef}
          className="w-full"
          style={{ height: isFullscreen ? window.innerHeight - 180 : height }}
        />

        {/* Chart Footer */}
        <div className="px-4 py-2 border-t border-gray-700 bg-gray-800/50">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1">
                <Volume2 className="h-3 w-3" />
                <span>Volume</span>
              </div>
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                <span>UTC</span>
              </div>
            </div>
            <div className="text-xs">
              Powered by TradingView
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Demo data generator for testing
export function useTradingChartDemo() {
  const updateCandlestickData = useTradingStore(state => state.updateCandlestickData);
  const selectedSymbol = useSelectedSymbol();

  useEffect(() => {
    const generateCandlestickData = () => {
      const data = [];
      const now = new Date();
      const basePrice = 50000;
      let currentPrice = basePrice;

      for (let i = 100; i > 0; i--) {
        const timestamp = new Date(now.getTime() - i * 15 * 60 * 1000);
        const change = (Math.random() - 0.5) * 1000;
        const open = currentPrice;
        const close = currentPrice + change;
        const high = Math.max(open, close) + Math.random() * 200;
        const low = Math.min(open, close) - Math.random() * 200;
        const volume = Math.random() * 1000000;

        data.push({
          time: timestamp.toISOString().split('T')[0],
          open,
          high,
          low,
          close,
          volume,
        });

        currentPrice = close;
      }

      updateCandlestickData(selectedSymbol, data);
    };

    generateCandlestickData();
  }, [selectedSymbol, updateCandlestickData]);
}
