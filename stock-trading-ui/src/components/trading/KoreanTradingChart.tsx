'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Activity,
  Settings,
  Maximize2,
  Volume2,
  Target,
  LineChart,
  CandlestickChart
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  KoreanStock,
  KoreanStockChart,
  formatStockPrice,
  formatPriceChange,
  getStockColorClass
} from '@/lib/types/korean-stocks';

interface KoreanTradingChartProps {
  className?: string;
  stock?: KoreanStock | null;
  height?: number;
  showIndicators?: boolean;
}

type ChartTimeframe = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y';
type ChartType = 'candlestick' | 'line' | 'area';

// Generate mock chart data
function generateMockChartData(stock: KoreanStock, timeframe: ChartTimeframe): KoreanStockChart[] {
  const data: KoreanStockChart[] = [];
  const points = timeframe === '1D' ? 390 : timeframe === '1W' ? 7 : timeframe === '1M' ? 30 : 90;
  let currentPrice = stock.currentPrice;
  const volatility = 0.02; // 2% volatility

  for (let i = points; i >= 0; i--) {
    const timestamp = new Date();
    timestamp.setMinutes(timestamp.getMinutes() - i);

    const change = (Math.random() - 0.5) * volatility * currentPrice;
    const open = currentPrice;
    const close = currentPrice + change;
    const high = Math.max(open, close) + Math.random() * 0.01 * currentPrice;
    const low = Math.min(open, close) - Math.random() * 0.01 * currentPrice;
    const volume = Math.floor(Math.random() * 1000000) + 100000;

    data.push({
      timestamp: timestamp.toISOString(),
      open,
      high,
      low,
      close,
      volume,
      tradingValue: volume * close,
      foreignBuy: Math.floor(volume * 0.3),
      foreignSell: Math.floor(volume * 0.25),
      institutionalBuy: Math.floor(volume * 0.4),
      institutionalSell: Math.floor(volume * 0.35),
      individualBuy: Math.floor(volume * 0.3),
      individualSell: Math.floor(volume * 0.4)
    });

    currentPrice = close;
  }

  return data;
}

// Technical indicators calculations
function calculateTechnicalIndicators(data: KoreanStockChart[]) {
  const prices = data.map(d => d.close);
  const volumes = data.map(d => d.volume);

  // RSI calculation (simplified)
  const rsi = calculateRSI(prices, 14);

  // MACD calculation (simplified)
  const ema12 = calculateEMA(prices, 12);
  const ema26 = calculateEMA(prices, 26);
  const macd = ema12[ema12.length - 1] - ema26[ema26.length - 1];
  const macdSignal = calculateEMA([macd], 9)[0];

  // Bollinger Bands
  const sma20 = calculateSMA(prices, 20);
  const stdDev = calculateStdDev(prices.slice(-20));
  const bollingerUpper = sma20[sma20.length - 1] + (2 * stdDev);
  const bollingerLower = sma20[sma20.length - 1] - (2 * stdDev);

  return {
    rsi: rsi[rsi.length - 1],
    macd,
    macdSignal,
    macdHistogram: macd - macdSignal,
    sma20: sma20[sma20.length - 1],
    sma60: calculateSMA(prices, 60)[0],
    bollingerUpper,
    bollingerLower,
    volume: volumes[volumes.length - 1],
    avgVolume: volumes.reduce((a, b) => a + b, 0) / volumes.length
  };
}

// Helper functions for technical analysis
function calculateRSI(prices: number[], period: number): number[] {
  const gains: number[] = [];
  const losses: number[] = [];

  for (let i = 1; i < prices.length; i++) {
    const change = prices[i] - prices[i - 1];
    gains.push(change > 0 ? change : 0);
    losses.push(change < 0 ? Math.abs(change) : 0);
  }

  const avgGain = gains.slice(-period).reduce((a, b) => a + b, 0) / period;
  const avgLoss = losses.slice(-period).reduce((a, b) => a + b, 0) / period;

  const rs = avgGain / avgLoss;
  const rsi = 100 - (100 / (1 + rs));

  return [rsi];
}

function calculateEMA(prices: number[], period: number): number[] {
  const k = 2 / (period + 1);
  let ema = prices[0];
  const emas = [ema];

  for (let i = 1; i < prices.length; i++) {
    ema = (prices[i] * k) + (ema * (1 - k));
    emas.push(ema);
  }

  return emas;
}

function calculateSMA(prices: number[], period: number): number[] {
  const smas: number[] = [];
  for (let i = period - 1; i < prices.length; i++) {
    const sum = prices.slice(i - period + 1, i + 1).reduce((a, b) => a + b, 0);
    smas.push(sum / period);
  }
  return smas;
}

function calculateStdDev(prices: number[]): number {
  const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
  const variance = prices.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / prices.length;
  return Math.sqrt(variance);
}

export function KoreanTradingChart({
  className,
  stock,
  height = 400,
  showIndicators = true
}: KoreanTradingChartProps) {
  const [timeframe, setTimeframe] = useState<ChartTimeframe>('1D');
  const [chartType, setChartType] = useState<ChartType>('candlestick');
  const [showVolume, setShowVolume] = useState(true);

  const chartData = useMemo(() => {
    if (!stock) return [];
    return generateMockChartData(stock, timeframe);
  }, [stock, timeframe]);

  const technicalIndicators = useMemo(() => {
    if (chartData.length === 0) return null;
    return calculateTechnicalIndicators(chartData);
  }, [chartData]);

  const timeframes: { value: ChartTimeframe; label: string }[] = [
    { value: '1D', label: '1일' },
    { value: '1W', label: '1주' },
    { value: '1M', label: '1개월' },
    { value: '3M', label: '3개월' },
    { value: '6M', label: '6개월' },
    { value: '1Y', label: '1년' }
  ];

  const getIndicatorColor = (value: number, type: 'rsi' | 'macd') => {
    if (type === 'rsi') {
      if (value > 70) return 'text-red-400';
      if (value < 30) return 'text-blue-400';
      return 'text-gray-400';
    } else {
      return value > 0 ? 'text-red-400' : 'text-blue-400';
    }
  };

  if (!stock) {
    return (
      <Card className={cn('bg-[#1a1a1b] border-gray-700', className)} style={{ height }}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-gray-400">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>종목을 선택하여 차트를 확인하세요</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const priceChange = formatPriceChange(stock.changeAmount, stock.changeRate);

  return (
    <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                {stock.name} ({stock.code})
              </CardTitle>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-2xl font-bold text-white">
                  {formatStockPrice(stock.currentPrice)}
                </span>
                <div className={cn('flex items-center gap-1', priceChange.color)}>
                  {stock.changeRate > 0 ? (
                    <TrendingUp className="w-4 h-4" />
                  ) : stock.changeRate < 0 ? (
                    <TrendingDown className="w-4 h-4" />
                  ) : (
                    <Activity className="w-4 h-4" />
                  )}
                  <span className="font-medium">
                    {stock.changeAmount > 0 ? '+' : ''}{stock.changeAmount.toLocaleString()}원
                  </span>
                  <span className="font-medium">
                    ({stock.changeRate > 0 ? '+' : ''}{stock.changeRate.toFixed(2)}%)
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
              <Settings className="w-4 h-4" />
            </Button>
            <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white">
              <Maximize2 className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center justify-between">
          {/* Timeframe Selection */}
          <div className="flex items-center gap-1">
            {timeframes.map((tf) => (
              <Button
                key={tf.value}
                variant={timeframe === tf.value ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setTimeframe(tf.value)}
                className="text-xs h-7"
              >
                {tf.label}
              </Button>
            ))}
          </div>

          {/* Chart Type */}
          <div className="flex items-center gap-1">
            <Button
              variant={chartType === 'candlestick' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setChartType('candlestick')}
              className="text-xs h-7"
            >
              <CandlestickChart className="w-3 h-3 mr-1" />
              캔들
            </Button>
            <Button
              variant={chartType === 'line' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setChartType('line')}
              className="text-xs h-7"
            >
              <LineChart className="w-3 h-3 mr-1" />
              선형
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowVolume(!showVolume)}
              className={cn('text-xs h-7', showVolume && 'text-blue-400')}
            >
              <Volume2 className="w-3 h-3 mr-1" />
              거래량
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Mock Chart Area */}
        <div
          className="bg-[#0a0a0b] border border-gray-700 rounded-lg relative overflow-hidden"
          style={{ height: height - 200 }}
        >
          {/* Chart Grid */}
          <div className="absolute inset-0 opacity-10">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="absolute w-full border-t border-gray-600"
                style={{ top: `${(i + 1) * 16.67}%` }}
              />
            ))}
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                className="absolute h-full border-l border-gray-600"
                style={{ left: `${(i + 1) * 10}%` }}
              />
            ))}
          </div>

          {/* Price Line Chart Simulation */}
          <svg className="absolute inset-0 w-full h-full">
            <defs>
              <linearGradient id="priceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style={{ stopColor: stock.changeRate >= 0 ? '#ef4444' : '#3b82f6', stopOpacity: 0.3 }} />
                <stop offset="100%" style={{ stopColor: stock.changeRate >= 0 ? '#ef4444' : '#3b82f6', stopOpacity: 0 }} />
              </linearGradient>
            </defs>
            <path
              d={`M 0 ${height - 250} ${chartData.map((_, i) =>
                `L ${(i / chartData.length) * 100}% ${Math.random() * (height - 300) + 50}`
              ).join(' ')}`}
              fill="url(#priceGradient)"
              stroke={stock.changeRate >= 0 ? '#ef4444' : '#3b82f6'}
              strokeWidth="2"
              fillOpacity="0.1"
            />
          </svg>

          {/* Current Price Indicator */}
          <div className="absolute right-0 top-1/2 transform -translate-y-1/2">
            <div className={cn(
              'px-2 py-1 text-xs font-medium rounded-l',
              stock.changeRate >= 0 ? 'bg-red-500 text-white' : 'bg-blue-500 text-white'
            )}>
              {formatStockPrice(stock.currentPrice)}
            </div>
          </div>

          {/* Trading Hours Indicator */}
          <div className="absolute top-2 left-2">
            <Badge className="bg-green-500 text-white text-xs">
              <Activity className="w-3 h-3 mr-1" />
              실시간
            </Badge>
          </div>
        </div>

        {/* Volume Chart */}
        {showVolume && (
          <div className="h-20 bg-[#0a0a0b] border border-gray-700 rounded-lg relative">
            <div className="absolute inset-2 flex items-end gap-px">
              {Array.from({ length: 50 }).map((_, i) => (
                <div
                  key={i}
                  className="flex-1 bg-gray-600 opacity-50"
                  style={{ height: `${Math.random() * 100}%` }}
                />
              ))}
            </div>
            <div className="absolute top-1 left-2 text-xs text-gray-400">
              거래량: {(stock.volume / 1000000).toFixed(1)}M
            </div>
          </div>
        )}

        {/* Technical Indicators */}
        {showIndicators && technicalIndicators && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#2a2a2a] rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">RSI (14)</div>
              <div className={cn('text-lg font-bold', getIndicatorColor(technicalIndicators.rsi, 'rsi'))}>
                {technicalIndicators.rsi.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500">
                {technicalIndicators.rsi > 70 ? '과매수' : technicalIndicators.rsi < 30 ? '과매도' : '중립'}
              </div>
            </div>

            <div className="bg-[#2a2a2a] rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">MACD</div>
              <div className={cn('text-lg font-bold', getIndicatorColor(technicalIndicators.macd, 'macd'))}>
                {technicalIndicators.macd.toFixed(2)}
              </div>
              <div className="text-xs text-gray-500">
                Signal: {technicalIndicators.macdSignal.toFixed(2)}
              </div>
            </div>

            <div className="bg-[#2a2a2a] rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">20일 이평선</div>
              <div className="text-lg font-bold text-white">
                {formatStockPrice(technicalIndicators.sma20)}
              </div>
              <div className="text-xs text-gray-500">
                {technicalIndicators.sma20 > stock.currentPrice ? '저항' : '지지'}
              </div>
            </div>

            <div className="bg-[#2a2a2a] rounded-lg p-3">
              <div className="text-xs text-gray-400 mb-1">거래량 비교</div>
              <div className={cn(
                'text-lg font-bold',
                technicalIndicators.volume > technicalIndicators.avgVolume ? 'text-red-400' : 'text-blue-400'
              )}>
                {((technicalIndicators.volume / technicalIndicators.avgVolume) * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-500">
                평균 대비
              </div>
            </div>
          </div>
        )}

        {/* Order Book Preview */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-[#2a2a2a] rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-2 flex items-center gap-2">
              <Target className="w-3 h-3" />
              매수 호가 (상위 3개)
            </div>
            <div className="space-y-1">
              {[0, 1, 2].map((i) => (
                <div key={i} className="flex justify-between text-xs">
                  <span className="text-red-400 font-medium">
                    {(stock.currentPrice + (i + 1) * 100).toLocaleString()}원
                  </span>
                  <span className="text-gray-300">
                    {Math.floor(Math.random() * 1000 + 100)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#2a2a2a] rounded-lg p-3">
            <div className="text-xs text-gray-400 mb-2 flex items-center gap-2">
              <Target className="w-3 h-3" />
              매도 호가 (상위 3개)
            </div>
            <div className="space-y-1">
              {[0, 1, 2].map((i) => (
                <div key={i} className="flex justify-between text-xs">
                  <span className="text-blue-400 font-medium">
                    {(stock.currentPrice - (i + 1) * 100).toLocaleString()}원
                  </span>
                  <span className="text-gray-300">
                    {Math.floor(Math.random() * 1000 + 100)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}