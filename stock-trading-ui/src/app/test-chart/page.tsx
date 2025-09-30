'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Activity,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  BarChart3,
  TrendingUp,
  Clock,
  Database,
  Wifi,
  WifiOff
} from 'lucide-react';
import { useSamsungChartData, useChartApiTest, validateChartData } from '@/hooks/useRealChartData';
import { useSamsungRealTimePrice, getPriceDirection, getPriceColor, formatPrice, formatVolume, formatMarketCap } from '@/hooks/useRealTimePrice';
import { KoreanTradingChart } from '@/components/trading/KoreanTradingChart';
import { POPULAR_KOREAN_STOCKS } from '@/lib/types/korean-stocks';
import { useTradingHours } from '@/hooks/useTradingHours';
import { TradingSession } from '@/lib/utils/tradingHours';

export default function TestChartPage() {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [showRawData, setShowRawData] = useState(false);
  const [timeframe, setTimeframe] = useState<'1m' | '1D' | '1W' | '1M' | '3M' | '6M' | '1Y'>('1m');
  const [includeExtendedHours, setIncludeExtendedHours] = useState(false);
  const [regularHoursOnly, setRegularHoursOnly] = useState(true);

  // 거래시간 Hook
  const { currentSession, isMarketOpen, formatTimeUntilReset, sessionDisplayName } = useTradingHours();

  // 삼성전자 차트 데이터 Hook (시간 필터링 옵션 추가)
  const {
    chartData,
    metadata,
    isLoading,
    error,
    isConnected,
    lastUpdated,
    refetch,
    retry
  } = useSamsungChartData(timeframe, {
    enabled: true,
    autoRefresh: autoRefresh && (timeframe === '1m' ? isMarketOpen : true), // 분봉일 때만 장 시간에 자동 새로고침
    includeExtendedHours,
    regularHoursOnly
  });

  // API 테스트 Hook
  const {
    testResult,
    isLoading: isTestLoading,
    error: testError,
    runTest
  } = useChartApiTest('005930');

  // 실시간 가격 Hook
  const {
    priceData,
    quoteData,
    isLoading: isPriceLoading,
    error: priceError,
    isConnected: isPriceConnected,
    lastUpdated: priceLastUpdated,
    refetch: refetchPrice,
    retry: retryPrice
  } = useSamsungRealTimePrice({
    enabled: true,
    autoRefresh: autoRefresh,
    refreshInterval: 5000, // 5초마다
    includeQuoteData: true
  });

  // 차트 데이터 검증
  const validation = chartData.length > 0 ? validateChartData(chartData) : null;

  // 삼성전자 종목 정보 (실시간 가격 데이터와 결합)
  const samsungStock = POPULAR_KOREAN_STOCKS.find(stock => stock.code === '005930');

  const displayStock = useMemo(() => {
    if (!samsungStock) return null;
    if (!priceData) return samsungStock;

    return {
      ...samsungStock,
      currentPrice: priceData.current_price,
      changeAmount: priceData.change_amount,
      changeRate: priceData.change_rate,
      volume: priceData.volume,
      // 필요한 다른 실시간 데이터 필드 추가
    };
  }, [samsungStock, priceData]);

  useEffect(() => {
    // 페이지 로드 시 API 테스트 실행
    runTest();
  }, [runTest]);

  // 자동 리셋 메커니즘 (매일 0시)
  useEffect(() => {
    const setupAutoReset = () => {
      const now = new Date();
      const tomorrow = new Date(now);
      tomorrow.setDate(tomorrow.getDate() + 1);
      tomorrow.setHours(0, 0, 0, 0);
      const msUntilMidnight = tomorrow.getTime() - now.getTime();

      // 자정에 한 번 실행
      const midnightTimeout = setTimeout(() => {
        console.log('🔄 자동 리셋: 새로운 거래일 시작');
        refetch(); // 차트 데이터 다시 가져오기

        // 그 다음부터는 24시간마다 반복
        const dailyInterval = setInterval(() => {
          console.log('🔄 일일 자동 리셋');
          refetch();
        }, 24 * 60 * 60 * 1000);

        return () => clearInterval(dailyInterval);
      }, msUntilMidnight);

      return () => clearTimeout(midnightTimeout);
    };

    const cleanup = setupAutoReset();
    return cleanup;
  }, [refetch]);

  const formatDateTime = (date: Date | null): string => {
    if (!date) return 'Never';
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getStatusColor = (isConnected: boolean, hasError: boolean, isLoading: boolean) => {
    if (isLoading) return 'bg-yellow-500';
    if (hasError) return 'bg-red-500';
    if (isConnected) return 'bg-green-500';
    return 'bg-gray-500';
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-blue-400" />
              삼성전자 차트 데이터 테스트
            </h1>
            <p className="text-gray-400 mt-2">실제 한국투자증권 API 데이터 연동 확인</p>
          </div>

          <div className="flex flex-col gap-3">
            {/* 상태 및 컨트롤 */}
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(isConnected, !!error, isLoading)}`} />
                <span className="text-gray-300 text-sm">
                  {isLoading ? 'Loading...' : isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* 거래시간 상태 표시 */}
              <Badge variant={isMarketOpen ? "default" : "outline"} className={isMarketOpen ? "bg-green-600" : ""}>
                {isMarketOpen ? "장 진행 중" : "장 마감"}
              </Badge>
              <span className="text-sm text-gray-400">{sessionDisplayName}</span>

              <Button
                variant="outline"
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={autoRefresh ? 'border-green-500 text-green-400' : ''}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                Auto Refresh
              </Button>

              <div className="ml-auto text-sm text-gray-400">
                다음 리셋: {formatTimeUntilReset()}
              </div>
            </div>

            {/* 타임프레임 선택 */}
            <div className="flex items-center gap-1">
              {[ '1m', '1D', '1W', '1M', '3M', '6M', '1Y' ].map((tf) => (
                <Button
                  key={tf}
                  variant={timeframe === tf ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setTimeframe(tf as any)}
                  className="text-xs h-7"
                >
                  {tf === '1m' ? '1분' : tf === '1D' ? '1일' : tf === '1W' ? '1주' : tf === '1M' ? '1개월' : tf === '3M' ? '3개월' : tf === '6M' ? '6개월' : '1년'}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* 시간 필터링 옵션 (분봉일 때만 표시) */}
        {timeframe === '1m' && (
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <CardTitle className="text-white text-sm flex items-center gap-2">
                <Clock className="w-4 h-4" />
                거래시간 설정
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={regularHoursOnly}
                    onChange={(e) => {
                      setRegularHoursOnly(e.target.checked);
                      if (e.target.checked) setIncludeExtendedHours(false);
                    }}
                    className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-white text-sm">정규장만 (9:00~15:30)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeExtendedHours}
                    onChange={(e) => {
                      setIncludeExtendedHours(e.target.checked);
                      if (e.target.checked) setRegularHoursOnly(false);
                    }}
                    className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-white text-sm">시간외 포함 (8:30~16:00)</span>
                </label>

                <div className="ml-auto">
                  <Badge variant="outline" className="text-gray-400">
                    {regularHoursOnly ? "정규장만" : includeExtendedHours ? "시간외 포함" : "전체"}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 상태 카드들 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* 연결 상태 */}
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                {isConnected ? (
                  <Wifi className="w-6 h-6 text-green-400" />
                ) : (
                  <WifiOff className="w-6 h-6 text-red-400" />
                )}
                <div>
                  <p className="text-sm text-gray-400">API Connection</p>
                  <p className="text-lg font-semibold text-white">
                    {isConnected ? 'Connected' : 'Disconnected'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 데이터 개수 */}
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Database className="w-6 h-6 text-blue-400" />
                <div>
                  <p className="text-sm text-gray-400">Chart Data</p>
                  <p className="text-lg font-semibold text-white">
                    {chartData.length.toLocaleString()} candles
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 마지막 업데이트 */}
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <Clock className="w-6 h-6 text-yellow-400" />
                <div>
                  <p className="text-sm text-gray-400">Last Updated</p>
                  <p className="text-sm font-semibold text-white">
                    {formatDateTime(lastUpdated)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* 데이터 유효성 */}
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                {validation?.isValid ? (
                  <CheckCircle className="w-6 h-6 text-green-400" />
                ) : validation ? (
                  <XCircle className="w-6 h-6 text-red-400" />
                ) : (
                  <AlertTriangle className="w-6 h-6 text-gray-400" />
                )}
                <div>
                  <p className="text-sm text-gray-400">Data Validity</p>
                  <p className="text-lg font-semibold text-white">
                    {validation ? (validation.isValid ? 'Valid' : 'Invalid') : 'N/A'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 실시간 가격 정보 */}
        {priceData && (
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  삼성전자 (005930) - 실시간 시세
                </CardTitle>
                <div className="flex items-center gap-2">
                  <div className={`w-3 h-3 rounded-full ${isPriceConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-sm text-gray-300">
                    {isPriceConnected ? 'Live' : 'Offline'}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={refetchPrice}
                    disabled={isPriceLoading}
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${isPriceLoading ? 'animate-spin' : ''}`} />
                    새로고침
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* 현재가 */}
                <div className="space-y-2">
                  <p className="text-sm text-gray-400">현재가</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-2xl font-bold text-white">
                      {formatPrice(priceData.current_price)}원
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-sm font-medium ${getPriceColor(priceData.change_rate)}`}>
                      {priceData.change_amount > 0 ? '+' : ''}{formatPrice(priceData.change_amount)}원
                    </span>
                    <span className={`text-sm font-medium ${getPriceColor(priceData.change_rate)}`}>
                      ({priceData.change_rate > 0 ? '+' : ''}{priceData.change_rate.toFixed(2)}%)
                    </span>
                  </div>
                </div>

                {/* 거래량 */}
                <div className="space-y-2">
                  <p className="text-sm text-gray-400">거래량</p>
                  <p className="text-xl font-semibold text-white">
                    {formatVolume(priceData.volume)}
                  </p>
                  <p className="text-sm text-gray-500">
                    거래대금: {formatMarketCap(priceData.trading_value)}원
                  </p>
                </div>

                {/* 가격 범위 */}
                <div className="space-y-2">
                  <p className="text-sm text-gray-400">당일 가격 범위</p>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">고가:</span>
                      <span className="text-sm text-red-400">{formatPrice(priceData.high_price)}원</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">저가:</span>
                      <span className="text-sm text-blue-400">{formatPrice(priceData.low_price)}원</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">시가:</span>
                      <span className="text-sm text-white">{formatPrice(priceData.open_price)}원</span>
                    </div>
                  </div>
                </div>

                {/* 시장 정보 */}
                <div className="space-y-2">
                  <p className="text-sm text-gray-400">시장 정보</p>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">전일종가:</span>
                      <span className="text-sm text-white">{formatPrice(priceData.previous_close)}원</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">시가총액:</span>
                      <span className="text-sm text-white">{formatMarketCap(priceData.market_cap)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-500">업데이트:</span>
                      <span className="text-xs text-gray-400">
                        {priceLastUpdated?.toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 최근 5일 데이터 (quoteData가 있을 때만) */}
              {quoteData && quoteData.recent_candles && quoteData.recent_candles.length > 0 && (
                <div className="mt-6 pt-4 border-t border-gray-700">
                  <h4 className="text-sm font-medium text-gray-400 mb-3">최근 5일 데이터</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-gray-500 mb-2">5일 평균 거래량</p>
                      <p className="text-sm text-white">{formatVolume(quoteData.avg_volume_5d)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-2">5일 가격 범위</p>
                      <div className="flex gap-4">
                        <span className="text-sm text-red-400">
                          고: {formatPrice(quoteData.price_range_5d.high)}원
                        </span>
                        <span className="text-sm text-blue-400">
                          저: {formatPrice(quoteData.price_range_5d.low)}원
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* 실시간 가격 에러 표시 */}
        {priceError && (
          <Card className="bg-red-900/20 border-red-500/50">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-400 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-red-400 font-medium">Real-time Price Error</h3>
                  <p className="text-red-300 text-sm mt-1">{priceError}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={retryPrice}
                    className="mt-3 border-red-500 text-red-400 hover:bg-red-500/10"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Retry Price
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 차트 데이터 에러 표시 */}
        {error && (
          <Card className="bg-red-900/20 border-red-500/50">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-400 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-red-400 font-medium">Connection Error</h3>
                  <p className="text-red-300 text-sm mt-1">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={retry}
                    className="mt-3 border-red-500 text-red-400 hover:bg-red-500/10"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Retry
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 메타데이터 */}
        {metadata && (
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Chart Metadata
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-gray-400">Stock Code</p>
                  <p className="text-white font-medium">{metadata.stock_code}</p>
                </div>
                <div>
                  <p className="text-gray-400">Period</p>
                  <p className="text-white font-medium">{metadata.period}</p>
                </div>
                <div>
                  <p className="text-gray-400">Total Volume</p>
                  <p className="text-white font-medium">{metadata.total_volume?.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-400">Average Price</p>
                  <p className="text-white font-medium">{metadata.average_price?.toLocaleString()}원</p>
                </div>
                <div>
                  <p className="text-gray-400">Date Range</p>
                  <p className="text-white font-medium text-xs">
                    {metadata.date_range?.start} ~ {metadata.date_range?.end}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400">Count</p>
                  <p className="text-white font-medium">{metadata.count}</p>
                </div>
                <div className="col-span-2">
                  <p className="text-gray-400">Last Updated</p>
                  <p className="text-white font-medium text-xs">{metadata.last_updated}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* 차트 */}
        <Card className="bg-[#1a1a1b] border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-white">Live Chart - Samsung Electronics (005930)</CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={refetch}
                  disabled={isLoading}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowRawData(!showRawData)}
                >
                  Raw Data
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {displayStock && (
              <KoreanTradingChart
                stock={displayStock}
                height={600}
                showIndicators={true}
                className="w-full"
                useRealData={true}
                autoRefresh={autoRefresh}
                timeframe={timeframe}
                setTimeframe={setTimeframe}
              />
            )}

            {/* 차트 상태 표시 */}
            <div className="flex items-center gap-4 mt-4 text-sm">
              <Badge variant="outline" className="text-gray-300">
                <Activity className="w-3 h-3 mr-1" />
                {isLoading ? 'Loading...' : `${chartData.length} candles`}
              </Badge>
              {lastUpdated && (
                <Badge variant="outline" className="text-gray-300">
                  <Clock className="w-3 h-3 mr-1" />
                  Updated: {lastUpdated.toLocaleTimeString()}
                </Badge>
              )}
              {validation && (
                <Badge
                  variant="outline"
                  className={validation.isValid ? 'text-green-400' : 'text-red-400'}
                >
                  {validation.isValid ? (
                    <CheckCircle className="w-3 h-3 mr-1" />
                  ) : (
                    <XCircle className="w-3 h-3 mr-1" />
                  )}
                  {validation.isValid ? 'Valid' : `${validation.errors.length} errors`}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 검증 결과 */}
        {validation && (
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Data Validation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {validation.errors.length > 0 && (
                  <div>
                    <h4 className="text-red-400 font-medium mb-2">Errors:</h4>
                    <ul className="text-red-300 text-sm space-y-1">
                      {validation.errors.map((error, index) => (
                        <li key={index}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {validation.warnings.length > 0 && (
                  <div>
                    <h4 className="text-yellow-400 font-medium mb-2">Warnings:</h4>
                    <ul className="text-yellow-300 text-sm space-y-1">
                      {validation.warnings.map((warning, index) => (
                        <li key={index}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {validation.isValid && validation.errors.length === 0 && validation.warnings.length === 0 && (
                  <div className="text-green-400">
                    ✅ All chart data is valid!
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* API 테스트 결과 */}
        {testResult && (
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">API Test Results</CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={runTest}
                  disabled={isTestLoading}
                >
                  <RefreshCw className={`w-4 h-4 mr-2 ${isTestLoading ? 'animate-spin' : ''}`} />
                  Re-test
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <pre className="bg-[#0a0a0b] p-4 rounded-lg text-sm text-gray-300 overflow-auto">
                {JSON.stringify(testResult, null, 2)}
              </pre>
            </CardContent>
          </Card>
        )}

        {/* Raw 데이터 표시 */}
        {showRawData && chartData.length > 0 && (
          <Card className="bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Raw Chart Data (First 10 records)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-600">
                      <th className="text-left p-2 text-gray-400">Date</th>
                      <th className="text-right p-2 text-gray-400">Open</th>
                      <th className="text-right p-2 text-gray-400">High</th>
                      <th className="text-right p-2 text-gray-400">Low</th>
                      <th className="text-right p-2 text-gray-400">Close</th>
                      <th className="text-right p-2 text-gray-400">Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {chartData.slice(0, 10).map((candle, index) => (
                      <tr key={index} className="border-b border-gray-700">
                        <td className="p-2 text-white">{candle.timestamp.split('T')[0]}</td>
                        <td className="p-2 text-right text-white">{candle.open.toLocaleString()}</td>
                        <td className="p-2 text-right text-white">{candle.high.toLocaleString()}</td>
                        <td className="p-2 text-right text-white">{candle.low.toLocaleString()}</td>
                        <td className="p-2 text-right text-white">{candle.close.toLocaleString()}</td>
                        <td className="p-2 text-right text-white">{candle.volume.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}