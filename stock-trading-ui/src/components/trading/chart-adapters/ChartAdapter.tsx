// 차트 라이브러리 추상화 인터페이스
// 향후 TradingView, ECharts 등으로 쉽게 교체 가능

import { ChartCandle } from '@/lib/types/korean-stocks';

export interface ChartAdapterProps {
  chartData: ChartCandle[];
  height?: number;
  onError?: (error: string) => void;
}

export interface ChartTheme {
  backgroundColor: string;
  textColor: string;
  gridColor: string;
  upColor: string;
  downColor: string;
  borderColor: string;
}

export const KOREAN_CHART_THEME: ChartTheme = {
  backgroundColor: '#0a0a0b',
  textColor: '#D1D4DC',
  gridColor: '#2B2B43',
  upColor: '#EF5350', // 상승: 빨간색 (한국 증시)
  downColor: '#2196F3', // 하락: 파란색 (한국 증시)
  borderColor: '#374151',
};

export type ChartLibrary = 'recharts' | 'tradingview' | 'echarts' | 'lightweight-charts';

export interface ChartConfig {
  library: ChartLibrary;
  theme: ChartTheme;
  features: {
    volume?: boolean;
    indicators?: boolean;
    crosshair?: boolean;
    zoom?: boolean;
  };
}

// 기본 설정
export const DEFAULT_CHART_CONFIG: ChartConfig = {
  library: 'recharts',
  theme: KOREAN_CHART_THEME,
  features: {
    volume: true,
    indicators: false,
    crosshair: true,
    zoom: true,
  },
};