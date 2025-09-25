import { Stock, Order, Position, TradingCondition } from './trading';

// 전역 상태 타입
export interface AppState {
  user: {
    id: string;
    name: string;
    accountBalance: number;
  };
  portfolio: {
    positions: Position[];
    totalValue: number;
    dayPnL: number;
    dayPnLRate: number;
  };
  trading: {
    selectedStock: Stock | null;
    mode: 'manual' | 'auto';
    activeOrders: Order[];
    conditions: TradingCondition[];
  };
  ui: {
    sidebarOpen: boolean;
    quickActionTab: 'watch' | 'trade' | 'alerts';
    selectedTimeframe: '1D' | '1W' | '1M' | '3M' | '1Y';
  };
}

// 액션 타입
export type AppAction =
  | { type: 'SET_SELECTED_STOCK'; payload: Stock }
  | { type: 'SET_TRADING_MODE'; payload: 'manual' | 'auto' }
  | { type: 'ADD_ORDER'; payload: Order }
  | { type: 'UPDATE_POSITIONS'; payload: Position[] }
  | { type: 'SET_QUICK_ACTION_TAB'; payload: 'watch' | 'trade' | 'alerts' }
  | { type: 'SET_SIDEBAR_OPEN'; payload: boolean }
  | { type: 'SET_TIMEFRAME'; payload: '1D' | '1W' | '1M' | '3M' | '1Y' };

// 연결 상태 타입
export interface ConnectionStatus {
  status: 'connected' | 'disconnected' | 'connecting' | 'error';
  lastUpdate?: string;
  reconnectAttempts: number;
  error?: string;
}