// 디자인 토큰 및 상수 정의
export const TRADING_COLORS = {
  // Primary Brand
  primary: '#3B82F6',
  secondary: '#8B5CF6',
  
  // Trading Colors
  bullish: '#EF4444',      // 상승 (빨간색)
  bearish: '#3B82F6',      // 하락 (파란색)
  neutral: '#6B7280',      // 변화없음 (회색)
  warning: '#F59E0B',      // 경고 (주황색)
  
  // Background
  background: '#F8FAFC',
  surface: '#FFFFFF',
  surfaceAlt: '#F1F5F9',
  
  // Text
  textPrimary: '#0F172A',
  textSecondary: '#475569',
  textMuted: '#94A3B8',
} as const;

export const FONT_SIZES = {
  xs: '0.75rem',    // 12px - 보조 정보
  sm: '0.875rem',   // 14px - 데이터 테이블
  base: '1rem',     // 16px - 기본 텍스트
  lg: '1.125rem',   // 18px - 카드 제목
  xl: '1.25rem',    // 20px - 섹션 헤더
  '2xl': '1.5rem',  // 24px - 페이지 제목
} as const;

export const SPACING = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
} as const;

export const BORDER_RADIUS = {
  sm: '0.25rem',
  md: '0.375rem',
  lg: '0.5rem',
  xl: '0.75rem',
} as const;

export const SHADOWS = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  glow: '0 0 20px rgba(59, 130, 246, 0.15)',
} as const;

// API 관련 상수
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
} as const;

// WebSocket 메시지 타입
export const WS_MESSAGE_TYPES = {
  ACCOUNT_UPDATE: 'account_update',
  WATCHLIST_UPDATE: 'watchlist_update',
  PRICE_UPDATE: 'price_update',
  TRADING_STATUS: 'trading_status',
  CONNECTION_STATUS: 'connection_status',
  ORDER_UPDATE: 'order_update',
} as const;

// 매매 조건 타입
export const CONDITION_TYPES = {
  MACD: {
    UP_CROSS: '상향돌파',
    DOWN_CROSS: '하향돌파',
    ABOVE: '이상',
    BELOW: '이하',
  },
  RSI: {
    UP_CROSS: '상향돌파',
    DOWN_CROSS: '하향돌파',
    ABOVE: '이상',
    BELOW: '이하',
  },
} as const;

// 기본 설정값
export const DEFAULTS = {
  BUY_AMOUNT: 100000,
  RSI_BUY_THRESHOLD: 30,
  RSI_SELL_THRESHOLD: 70,
  STOP_LOSS_PERCENT: 5,
  TAKE_PROFIT_PERCENT: 10,
  REFRESH_INTERVAL: 2000,
  CHART_UPDATE_INTERVAL: 1000,
} as const;

// 애니메이션 duration
export const ANIMATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  COUNTER: 1000,
} as const;