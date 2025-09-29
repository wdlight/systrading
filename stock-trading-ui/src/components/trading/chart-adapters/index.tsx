// 차트 어댑터 팩토리
// 향후 다른 차트 라이브러리 추가 시 여기에 등록

import React from 'react';
import dynamic from 'next/dynamic';
import { ChartLibrary, ChartAdapterProps } from './ChartAdapter';

// 동적 임포트로 각 차트 라이브러리 로드
const RechartsAdapter = dynamic(() => import('./RechartsAdapter'), {
  ssr: false,
  loading: () => (
    <div className="bg-[#0a0a0b] border border-gray-700 rounded-lg flex items-center justify-center h-96">
      <div className="flex items-center gap-2 text-gray-400">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
        <span>차트 로딩 중...</span>
      </div>
    </div>
  ),
});

// 임시 더미 컴포넌트들 - 향후 구현 예정
const TradingViewAdapter = () => <div>TradingView 준비 중...</div>;
const EChartsAdapter = () => <div>ECharts 준비 중...</div>;
const LightweightChartsAdapter = () => <div>Lightweight Charts 준비 중...</div>;

// 차트 어댑터 맵
const CHART_ADAPTERS = {
  recharts: RechartsAdapter,
  tradingview: TradingViewAdapter,
  echarts: EChartsAdapter,
  'lightweight-charts': LightweightChartsAdapter,
} as const;

export interface UniversalChartProps extends ChartAdapterProps {
  library?: ChartLibrary;
}

// 범용 차트 컴포넌트
export const UniversalChart: React.FC<UniversalChartProps> = ({
  library = 'recharts',
  ...props
}) => {
  const ChartComponent = CHART_ADAPTERS[library];

  if (!ChartComponent) {
    return (
      <div className="bg-[#0a0a0b] border border-gray-700 rounded-lg flex items-center justify-center h-96">
        <div className="text-center text-red-400">
          <div className="mb-2">⚠️ 지원하지 않는 차트 라이브러리</div>
          <div className="text-xs">라이브러리: {library}</div>
        </div>
      </div>
    );
  }

  return <ChartComponent {...props} />;
};

// 개별 어댑터 내보내기
export { RechartsAdapter };

// 타입 및 설정 내보내기
export * from './ChartAdapter';