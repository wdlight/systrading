'use client';

import { useState } from 'react';
import dynamic from 'next/dynamic';
import { TRViewChartControls } from '@/components/trading/TRViewChartControls';
import { OrderForm } from '@/components/trading/OrderForm';
import { OrdersList } from '@/components/trading/OrdersList';
import { useTRViewChart } from '@/hooks/useTRViewChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CandlestickChart,
  RefreshCw,
  TrendingUp
} from 'lucide-react';
import { useStockList } from '@/hooks/useStockList';

const TRViewChart = dynamic(
  () => import('@/components/trading/TRViewChart').then(mod => mod.TRViewChart),
  {
    ssr: false, // 서버 사이드 렌더링 비활성화 (가장 중요)
    loading: () => (
      <div className="h-[400px] flex items-center justify-center">
        <div className="text-gray-400">차트 로딩 중...</div>
      </div>
    )
  }
);

const SAMPLE_STOCKS = [
  { code: '005930', name: '삼성전자' },
  { code: '000660', name: 'SK하이닉스' },
  { code: '035420', name: 'NAVER' },
  { code: '051910', name: 'LG화학' },
];

export default function TRViewPage() {
  const [stockCode, setStockCode] = useState('005930');
  const [showVolume, setShowVolume] = useState(true);
  const [showGrid, setShowGrid] = useState(true);

  // 1. Minute Chart Data Hook
  const {
    chartData: minuteChartData,
    isLoading: isLoadingMinute,
    error: errorMinute,
    refetch: refetchMinute,
    loadPrevious: loadPreviousMinute,
    isLoadingMore: isLoadingMoreMinute,
    hasExtendedRange: hasExtendedRangeMinute,
  } = useTRViewChart({
    stockCode,
    timeframe: 'minute',
    enabled: true,
  });

  // 2. Daily Chart Data Hook
  const {
    chartData: dayChartData,
    isLoading: isLoadingDay,
    error: errorDay,
    refetch: refetchDay,
    loadPrevious: loadPreviousDay,
    isLoadingMore: isLoadingMoreDay,
    hasExtendedRange: hasExtendedRangeDay,
  } = useTRViewChart({
    stockCode,
    timeframe: 'day',
    enabled: true,
  });

  const { stockList } = useStockList();
  const selectedStockName = stockList.find(s => s.value === stockCode)?.label || stockCode;

  // 주문 성공 시 차트 새로고침
  const handleOrderSuccess = () => {
    refetchMinute();
    refetchDay();
  };

  return (
    <div className="bg-[#1a1a1a] p-6 min-h-screen">
      <div className="max-w-[1800px] mx-auto">
        {/* Page Title Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <TrendingUp className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-xl font-bold text-white">
                  주식 관리
                </h1>
                <p className="text-sm text-gray-400">
                  차트 분석 및 매매
                </p>
              </div>
            </div>
            <Badge className="bg-green-500">
              실시간 매매
            </Badge>
          </div>
        </div>

        {/* Main Content - 3단 레이아웃 */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls Panel */}
          <div className="lg:col-span-2">
            <TRViewChartControls
              selectedStockCode={stockCode}
              onStockChange={setStockCode}
              stocks={SAMPLE_STOCKS}
              showVolume={showVolume}
              onVolumeToggle={() => setShowVolume(!showVolume)}
              showGrid={showGrid}
              onGridToggle={() => setShowGrid(!showGrid)}
              dataCount={minuteChartData.length + dayChartData.length}
            />
          </div>

          {/* Center Panel - Chart (6 cols) */}
          <div className="lg:col-span-6 flex flex-col gap-6">
            {/* Minute Chart */}
            <Card className="bg-[#1a1a1b] border-gray-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">
                    {selectedStockName} 분봉 차트
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={refetchMinute}
                    disabled={isLoadingMinute}
                  >
                    <RefreshCw className={`w-4 h-4 ${isLoadingMinute ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingMinute && <div className="h-[400px] flex items-center justify-center text-gray-400">분봉 차트 로딩 중...</div>}
                {errorMinute && <div className="h-[400px] flex items-center justify-center text-red-400">오류: {String(errorMinute)}</div>}
                {!isLoadingMinute && !errorMinute && (
                  <TRViewChart
                    chartData={minuteChartData}
                    height={400}
                    showVolume={showVolume}
                    showGrid={showGrid}
                    enableCrosshair={true}
                    onLoadPrevious={loadPreviousMinute}
                    isLoadingMore={isLoadingMoreMinute}
                    timeframe="minute"
                    initialVisibleCandles={100}
                    hasExtendedRange={hasExtendedRangeMinute}
                  />
                )}
              </CardContent>
            </Card>

            {/* Daily Chart */}
            <Card className="bg-[#1a1a1b] border-gray-700">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white">
                    {selectedStockName} 일봉 차트
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={refetchDay}
                    disabled={isLoadingDay}
                  >
                    <RefreshCw className={`w-4 h-4 ${isLoadingDay ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingDay && <div className="h-[400px] flex items-center justify-center text-gray-400">일봉 차트 로딩 중...</div>}
                {errorDay && <div className="h-[400px] flex items-center justify-center text-red-400">오류: {String(errorDay)}</div>}
                {!isLoadingDay && !errorDay && (
                  <TRViewChart
                    chartData={dayChartData}
                    height={400}
                    showVolume={showVolume}
                    showGrid={showGrid}
                    enableCrosshair={true}
                    onLoadPrevious={loadPreviousDay}
                    isLoadingMore={isLoadingMoreDay}
                    timeframe="day"
                    initialVisibleCandles={100}
                    hasExtendedRange={hasExtendedRangeDay}
                  />
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Trading (4 cols) */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            {/* Order Form */}
            <OrderForm
              stockCode={stockCode}
              stockName={selectedStockName}
              currentPrice={
                minuteChartData.length > 0
                  ? minuteChartData[minuteChartData.length - 1].close
                  : 0
              }
              availableCash={10000000} // TODO: 실제 계좌 잔고 연동
              availableQuantity={0}     // TODO: 실제 보유 수량 연동
              onOrderSuccess={handleOrderSuccess}
            />

            {/* Orders List */}
            <OrdersList
              stockCode={stockCode}
              autoRefresh={true}
              refreshInterval={5000}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
