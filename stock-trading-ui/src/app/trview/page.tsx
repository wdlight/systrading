import { useState } from 'react';
import dynamic from 'next/dynamic';
import { TRViewChartControls } from '@/components/trading/TRViewChartControls';
import { useTRViewChart } from '@/hooks/useTRViewChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  CandlestickChart,
  RefreshCw,
  Github
} from 'lucide-react';
import { useStockList } from '@/hooks/useStockList';

const TRViewChart = dynamic(
  () => import('@/components/trading/TRViewChart').then(mod => mod.TRViewChart),
  {
    ssr: false, // 서버 사이드 렌더링 비활성화 (가장 중요)
    loading: () => (
      <div className="h-[500px] flex items-center justify-center">
        <div className="text-gray-400">차트 로딩 중...</div>
      </div>
    )
  }
);

export default function TRViewPage() {
  const [stockCode, setStockCode] = useState('005930');
  const [showVolume, setShowVolume] = useState(true);
  const [showGrid, setShowGrid] = useState(true);

  const { chartData, isLoading, error, refetch } = useTRViewChart({
    stockCode,
    enabled: true,
  });

  const { stockList } = useStockList();
  const selectedStockName = stockList.find(s => s.value === stockCode)?.label || stockCode;

  return (
    <div className="min-h-screen bg-[#0a0a0b]">
      {/* Header */}
      <div className="bg-[#1a1a1b] border-b border-gray-700 px-6 py-4">
        <div className="max-w-[1600px] mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CandlestickChart className="w-8 h-8 text-blue-400" />
              <div>
                <h1 className="text-xl font-bold text-white">
                  TradingView Lightweight Charts Demo
                </h1>
                <p className="text-sm text-gray-400">
                  실시간 주식 차트 샘플 페이지
                </p>
              </div>
            </div>
            <Badge className="bg-blue-500">
              <Github className="w-3 h-3 mr-1" />
              TradingView
            </Badge>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1600px] mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Controls Panel */}
          <TRViewChartControls
            selectedStockCode={stockCode}
            onStockChange={setStockCode}
            showVolume={showVolume}
            onVolumeToggle={() => setShowVolume(!showVolume)}
            showGrid={showGrid}
            onGridToggle={() => setShowGrid(!showGrid)}
            dataCount={chartData.length}
          />

          {/* Chart Panel */}
          <Card className="lg:col-span-3 bg-[#1a1a1b] border-gray-700">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">
                  {selectedStockName} 차트
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={refetch}
                >
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isLoading && (
                <div className="h-[500px] flex items-center justify-center">
                  <div className="text-gray-400">차트 로딩 중...</div>
                </div>
              )}

              {/* ✅ 수정된 부분 */}
              {error && (
                <div className="h-[500px] flex items-center justify-center">
                  <div className="text-red-400">
                    오류: {String(error.message || error)}
                  </div>
                </div>
              )}

              {!isLoading && !error && chartData.length > 0 && (
                <TRViewChart
                  chartData={chartData}
                  height={500}
                  showVolume={showVolume}
                  showGrid={showGrid}
                  enableCrosshair={true}
                />
              )}

              {!isLoading && !error && chartData.length === 0 && (
                <div className="h-[500px] flex items-center justify-center">
                  <div className="text-gray-400">차트 데이터 없음</div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}