'use client';

import React, { memo } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { UniversalChart } from './chart-adapters';

interface RealtimeCandlestickChartProps {
  chartData: ChartCandle[];
  height?: number;
  timeframe: string;
}

const RealtimeCandlestickChart: React.FC<RealtimeCandlestickChartProps> = memo(({ chartData, height = 400, timeframe }) => {
  return (
    <UniversalChart
      library="recharts" // 현재는 Recharts 사용, 향후 'tradingview', 'echarts' 등으로 쉽게 교체 가능
      chartData={chartData}
      height={height}
      timeframe={timeframe}
      onError={(error) => {
        console.error('차트 렌더링 오류:', error);
      }}
    />
  );
}, (prevProps, nextProps) => {
  // ✅ 커스텀 비교 함수: chartData 길이와 마지막 캔들의 timestamp를 비교
  if (prevProps.chartData.length !== nextProps.chartData.length) {
    return false; // 길이가 다르면 재렌더링
  }
  if (prevProps.height !== nextProps.height || prevProps.timeframe !== nextProps.timeframe) {
    return false; // height나 timeframe이 변경되면 재렌더링
  }
  // 마지막 캔들의 timestamp가 다르면 재렌더링
  const prevLast = prevProps.chartData[prevProps.chartData.length - 1];
  const nextLast = nextProps.chartData[nextProps.chartData.length - 1];
  if (prevLast?.timestamp !== nextLast?.timestamp) {
    return false;
  }
  // 마지막 캔들의 volume이 다르면 재렌더링 (실시간 업데이트 감지)
  if (prevLast?.volume !== nextLast?.volume) {
    return false;
  }
  return true; // 모두 같으면 재렌더링하지 않음
});

RealtimeCandlestickChart.displayName = 'RealtimeCandlestickChart';

export default RealtimeCandlestickChart;
