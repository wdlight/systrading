// 백엔드 API와 일치하는 TypeScript 타입 정의

// 기본 응답 타입
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
  timestamp: string;
}

// 계좌 관련 타입
export interface AccountBalance {
  total_value: number;
  available_cash: number;
  total_purchase_amount: number;
  total_evaluation_amount: number;
  total_profit_loss: number;
  total_profit_loss_rate: number;
  positions: Position[];
}

export interface Position {
  stock_code: string;
  stock_name: string;
  quantity: number;
  sellable_quantity: number;
  avg_price: number;
  current_price: number;
  profit_loss: number;
  profit_rate: number;
  evaluation_amount: number;
  yesterday_price: number;
  change_amount: number;
  change_rate: number;
}

export interface AccountSummary {
  account_number: string;
  total_asset: number;
  available_cash: number;
  total_profit_loss: number;
  daily_pnl: number;
  total_profit_loss_rate: number;
}

// 매매 조건 관련 타입
export type ConditionType = '상향돌파' | '하향돌파' | '이상' | '이하';

export interface BuyConditions {
  amount: number;
  macd_type: ConditionType;
  rsi_value: number;
  rsi_type: ConditionType;
  enabled: boolean;
}

export interface SellConditions {
  macd_type: ConditionType;
  rsi_value: number;
  rsi_type: ConditionType;
  stop_loss_rate?: number;
  take_profit_rate?: number;
  trailing_stop_enabled?: boolean;
  enabled: boolean;
}

export interface TradingConditions {
  buy_conditions: BuyConditions;
  sell_conditions: SellConditions;
  auto_trading_enabled: boolean;
  max_positions: number;
  risk_management: {
    max_loss_per_trade: number;
    max_daily_loss: number;
    position_sizing: 'fixed' | 'percentage' | 'volatility';
  };
}

// 워치리스트 관련 타입
export interface WatchlistItem {
  stock_code: string;
  stock_name?: string;
  current_price: number;
  profit_rate: number;
  avg_price: number | null;
  quantity: number;
  macd: number;
  macd_signal: number;
  rsi: number;
  trailing_stop_activated: boolean;
  trailing_stop_high: number;
  volume: number;
  change_amount: number;
  change_rate: number;
  yesterday_price: number;
  high_price: number;
  low_price: number;
  updated_at: string;
}

// 주문 관련 타입
export type OrderType = '00' | '01'; // 지정가 | 시장가
export type OrderSide = 'buy' | 'sell';
export type OrderStatus = 'pending' | 'filled' | 'cancelled' | 'failed';

export interface OrderRequest {
  stock_code: string;
  quantity: number;
  price?: number;
  order_type: OrderType;
  order_side: OrderSide;
}

export interface Order {
  order_id: string;
  stock_code: string;
  stock_name: string;
  order_side: OrderSide;
  order_type: OrderType;
  quantity: number;
  price: number;
  filled_quantity: number;
  remaining_quantity: number;
  status: OrderStatus;
  order_time: string;
  filled_time?: string;
  filled_price?: number;
  commission?: number;
}

// WebSocket 메시지 타입
export interface RealtimeMessage {
  type: 'account_update' | 'watchlist_update' | 'price_update' | 'trading_status' | 'order_update' | 'connection_status';
  timestamp: string;
  data: any;
}

export interface PriceUpdate {
  type: 'price_update';
  data: {
    stock_code: string;
    current_price: number;
    change_amount: number;
    change_rate: number;
    volume: number;
    timestamp: string;
  };
}

export interface AccountUpdate {
  type: 'account_update';
  data: AccountBalance;
}

export interface WatchlistUpdate {
  type: 'watchlist_update';
  data: WatchlistItem[];
}

export interface TradingStatusUpdate {
  type: 'trading_status';
  data: {
    is_active: boolean;
    current_positions: number;
    daily_pnl: number;
    total_trades: number;
    last_trade_time?: string;
  };
}

export interface OrderUpdate {
  type: 'order_update';
  data: Order;
}

export interface ConnectionStatus {
  type: 'connection_status';
  data: {
    status: 'connected' | 'disconnected' | 'reconnecting';
    last_update: string;
    error_message?: string;
  };
}

// 시장 정보 타입
export interface MarketIndex {
  name: string;
  code: string;
  current_value: number;
  change_amount: number;
  change_rate: number;
  volume: number;
  is_up: boolean;
}

export interface MarketOverview {
  kospi: MarketIndex;
  kosdaq: MarketIndex;
  usd_krw: MarketIndex;
  gold?: MarketIndex;
  bitcoin?: MarketIndex;
  updated_at: string;
}

// 기술적 지표 타입
export interface TechnicalIndicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  sma_20: number;
  sma_60: number;
  bollinger_upper: number;
  bollinger_lower: number;
  volume_sma: number;
}

// 차트 데이터 타입
export interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  indicators?: TechnicalIndicators;
}

// 포트폴리오 통계 타입
export interface PortfolioStats {
  total_value: number;
  daily_pnl: number;
  daily_pnl_rate: number;
  total_pnl: number;
  total_pnl_rate: number;
  win_rate: number;
  sharpe_ratio: number;
  max_drawdown: number;
  volatility: number;
  diversification_score: number;
  risk_score: number;
}

// UI 상태 관련 타입
export interface ConnectionState {
  status: 'connected' | 'disconnected' | 'connecting' | 'reconnecting';
  lastConnected?: Date;
  reconnectAttempts: number;
  error?: string;
}

export interface LoadingState {
  isLoading: boolean;
  error?: string;
  lastUpdated?: Date;
}

export interface UIState {
  activeTab: 'portfolio' | 'watchlist' | 'trading' | 'analytics';
  sidebarOpen: boolean;
  darkMode: boolean;
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actionable?: boolean;
  action?: () => void;
}

// 설정 타입
export interface UserSettings {
  notifications: {
    price_alerts: boolean;
    order_fills: boolean;
    technical_signals: boolean;
    system_status: boolean;
  };
  display: {
    theme: 'light' | 'dark' | 'auto';
    currency_format: 'KRW' | 'USD';
    number_format: 'compact' | 'full';
    refresh_interval: number;
  };
  trading: {
    confirm_orders: boolean;
    auto_refresh: boolean;
    sound_alerts: boolean;
    advanced_orders: boolean;
  };
}

// 에러 타입
export interface ApiError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// 유틸리티 타입
export type Direction = 'up' | 'down' | 'neutral';
export type TimeFrame = '1m' | '5m' | '15m' | '1h' | '4h' | '1d' | '1w';
export type ChartType = 'line' | 'candlestick' | 'area';

// Hook 반환 타입
export interface UseRealtimeDataReturn {
  accountBalance: AccountBalance | null;
  watchlist: WatchlistItem[];
  connectionStatus: ConnectionState;
  marketOverview: MarketOverview | null;
  isLoading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
}

export interface UseTradingConditionsReturn {
  conditions: TradingConditions | null;
  updateConditions: (conditions: Partial<TradingConditions>) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  connectionStatus: ConnectionState;
  sendMessage: (message: any) => void;
  lastMessage: RealtimeMessage | null;
}