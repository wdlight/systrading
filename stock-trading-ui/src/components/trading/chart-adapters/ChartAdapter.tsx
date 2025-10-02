// 차트 라이브러리 추상화 인터페이스
// 향후 TradingView, ECharts 등으로 쉽게 교체 가능

import { ChartCandle } from '@/lib/types/korean-stocks';
import { YAxisCalculator } from './core/YAxisCalculator';

/**
 * 차트 이벤트 통합 인터페이스
 * 모든 차트 라이브러리에서 공통으로 사용할 수 있는 이벤트 추상화
 */
export interface ChartEvents {
  /**
   * 표시 범위 변경 이벤트 (Brush, Zoom, Pan 등)
   * @param range 시작/끝 인덱스 또는 timestamp
   */
  onRangeChange?: (range: { startIndex: number; endIndex: number }) => void;

  /**
   * 십자선(Crosshair) 이동 이벤트
   * @param data 현재 포커스된 캔들 데이터 (null이면 차트 밖)
   */
  onCrosshairMove?: (data: ChartCandle | null) => void;

  /**
   * 줌 레벨 변경 이벤트
   * @param zoomLevel 줌 레벨 (1.0 = 100%)
   */
  onZoom?: (zoomLevel: number) => void;

  /**
   * 캔들 클릭 이벤트
   * @param candle 클릭된 캔들 데이터
   */
  onClick?: (candle: ChartCandle) => void;

  /**
   * 에러 발생 이벤트
   * @param error 에러 메시지
   */
  onError?: (error: string) => void;
}

/**
 * 차트 어댑터 Props
 * 모든 차트 라이브러리 어댑터가 준수해야 하는 공통 인터페이스
 */
export interface ChartAdapterProps {
  /** 차트에 표시할 캔들 데이터 */
  chartData: ChartCandle[];

  /** 차트 높이 (픽셀) */
  height?: number;

  /** 시간 프레임 (1m, 5m, 1D 등) */
  timeframe: string;

  /** Y축 계산 전략 (기본: daily-range) */
  yAxisCalculator?: YAxisCalculator | string;

  /** 차트 이벤트 핸들러 */
  events?: ChartEvents;

  /** 차트 설정 */
  config?: Partial<ChartConfig>;
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