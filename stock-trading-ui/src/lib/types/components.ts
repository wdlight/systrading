import { Stock, Order, Portfolio, WatchlistItem } from './trading';

// QuickActionPanel Props
export interface QuickActionPanelProps {
  className?: string;
  defaultTab?: 'watch' | 'trade' | 'alerts';
  onStockSelect?: (stock: Stock) => void;
}

// TradingQuick Props
export interface TradingQuickProps {
  selectedStock?: string;
  onOrderSubmit?: (order: Partial<Order>) => Promise<void>;
  className?: string;
}

// DashboardGrid Props
export interface DashboardGridProps {
  portfolioData?: Portfolio;
  watchlistData?: Stock[];
  recentTrades?: Order[];
  className?: string;
}

// TradingInterface Props
export interface TradingInterfaceProps {
  mode: 'manual' | 'auto';
  selectedStock?: Stock;
  onModeChange?: (mode: 'manual' | 'auto') => void;
  onStockChange?: (stock: Stock) => void;
}

// TabButton Props
export interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  className?: string;
}

// WatchlistQuick Props
export interface WatchlistQuickProps {
  stocks?: WatchlistItem[];
  onStockSelect?: (stockCode: string) => void;
  className?: string;
}

// AlertsPanel Props
export interface AlertsPanelProps {
  alerts?: Alert[];
  onAlertToggle?: (alertId: string, enabled: boolean) => void;
  className?: string;
}

// Alert 타입
export interface Alert {
  id: string;
  stockCode: string;
  stockName: string;
  condition: string;
  enabled: boolean;
  createdAt: Date;
  lastTriggered?: Date;
}

// Common component props
export interface CommonComponentProps {
  className?: string;
  children?: React.ReactNode;
}