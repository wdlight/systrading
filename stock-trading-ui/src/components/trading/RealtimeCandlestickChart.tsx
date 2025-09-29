'use client';

import React, { memo } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { UniversalChart } from './chart-adapters';

interface RealtimeCandlestickChartProps {
  chartData: ChartCandle[];
  height?: number;
}

const RealtimeCandlestickChart: React.FC<RealtimeCandlestickChartProps> = memo(({ chartData, height = 400 }) => {
  return (
    <UniversalChart
      library="recharts" // 현재는 Recharts 사용, 향후 'tradingview', 'echarts' 등으로 쉽게 교체 가능
      chartData={chartData}
      height={height}
      onError={(error) => {
        console.error('차트 렌더링 오류:', error);
      }}
    />
  );
});

RealtimeCandlestickChart.displayName = 'RealtimeCandlestickChart';

export default RealtimeCandlestickChart;
