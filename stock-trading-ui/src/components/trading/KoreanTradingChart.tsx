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
  CandlestickChart,
  RefreshCw,
  Wifi,
  WifiOff,
  AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  KoreanStock,
  KoreanStockChart,
  formatStockPrice,
  formatPriceChange,
  getStockColorClass
} from '@/lib/types/korean-stocks';
import { useRealChartData } from '@/hooks/useRealChartData';
import RealtimeCandlestickChart from './RealtimeCandlestickChart';

interface KoreanTradingChartProps {
  className?: string;
  stock?: KoreanStock | null;
  height?: number;
  showIndicators?: boolean;
  useRealData?: boolean;
  autoRefresh?: boolean;
  timeframe: ChartTimeframe;
  setTimeframe: (tf: ChartTimeframe) => void;
}

type ChartTimeframe = '1m' | '1D' | '1W' | '1M' | '3M' | '6M' | '1Y';
type ChartType = 'candlestick' | 'line' | 'area';

// Generate mock chart data


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
  showIndicators = true,
  useRealData = false,
  autoRefresh = false,
  timeframe,
  setTimeframe
}: KoreanTradingChartProps) {
  const [chartType, setChartType] = useState<ChartType>('candlestick');
  const [showVolume, setShowVolume] = useState(true);

  // 실제 차트 데이터 Hook (useRealData가 true이고 stock이 있을 때만 활성화)
  const {
    chartData: realChartData,
    metadata,
    isLoading,
    error,
    isConnected,
    lastUpdated,
    refetch
  } = useRealChartData(
    stock?.code || '',
    timeframe,
    {
      enabled: useRealData && !!stock?.code,
      autoRefresh: autoRefresh,
      // refreshInterval은 useRealChartData 내부에서 timeframe에 따라 결정됨
    }
  );

  const technicalIndicators = useMemo(() => {
    if (realChartData.length === 0) return null;
    return calculateTechnicalIndicators(realChartData);
  }, [realChartData]);

  const timeframes: { value: ChartTimeframe; label: string }[] = [
    { value: '1m', label: '1분' },
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
            {/* 실제 데이터 사용 시 상태 표시 */}
            {useRealData && (
              <>
                {/* 연결 상태 */}
                <div className="flex items-center gap-1 px-2 py-1 rounded text-xs">
                  {isConnected ? (
                    <Wifi className="w-3 h-3 text-green-400" />
                  ) : (
                    <WifiOff className="w-3 h-3 text-red-400" />
                  )}
                  <span className={isConnected ? 'text-green-400' : 'text-red-400'}>
                    {isConnected ? 'Live' : 'Offline'}
                  </span>
                </div>

                {/* 새로고침 버튼 */}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={refetch}
                  disabled={isLoading}
                  className="text-gray-400 hover:text-white"
                >
                  <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                </Button>

                {/* 에러 표시 */}
                {error && (
                  <div className="flex items-center gap-1 px-2 py-1 rounded text-xs text-red-400">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Error</span>
                  </div>
                )}
              </>
            )}

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
        {useRealData && timeframe === '1m' ? (
          <RealtimeCandlestickChart chartData={realChartData} height={height - 100} timeframe={timeframe} />
        ) : (
          <div
            className="bg-[#0a0a0b] border border-gray-700 rounded-lg relative overflow-hidden flex items-center justify-center text-gray-400"
            style={{ height: height - 100 }}
          >
            {useRealData ? (
              <p>실시간 차트 데이터 준비 중...</p>
            ) : (
              <p>실시간 데이터가 아닙니다.</p>
            )}
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
                  <span className="text-gray-300">
                    100
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
                    0
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