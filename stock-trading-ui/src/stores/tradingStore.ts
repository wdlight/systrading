'use client';

import { create } from 'zustand';
import { devtools, subscribeWithSelector } from 'zustand/middleware';

// Trading Data Types
export interface OrderBookEntry {
  price: number;
  quantity: number;
  total: number;
}

export interface OrderBook {
  symbol: string;
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  lastUpdate: number;
}

export interface CandlestickData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketTicker {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  high24h: number;
  low24h: number;
  lastUpdate: number;
}

export interface TradingOrder {
  id: string;
  symbol: string;
  type: 'buy' | 'sell';
  orderType: 'market' | 'limit';
  quantity: number;
  price?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'partial';
  timestamp: number;
  filled?: number;
  fee?: number;
}

export interface Portfolio {
  totalValue: number;
  availableCash: number;
  totalPnL: number;
  dailyPnL: number;
  positions: Position[];
}

export interface Position {
  symbol: string;
  quantity: number;
  avgPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
}

// Trading Store State
interface TradingState {
  // Market Data
  selectedSymbol: string;
  marketTickers: Map<string, MarketTicker>;
  orderBooks: Map<string, OrderBook>;
  candlestickData: Map<string, CandlestickData[]>;

  // Trading
  orders: TradingOrder[];
  portfolio: Portfolio | null;

  // UI State
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;

  // Chart Settings
  chartType: 'candlestick' | 'line';
  timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

  // Actions
  setSelectedSymbol: (symbol: string) => void;
  updateMarketTicker: (ticker: MarketTicker) => void;
  updateOrderBook: (orderBook: OrderBook) => void;
  updateCandlestickData: (symbol: string, data: CandlestickData[]) => void;
  addOrder: (order: Omit<TradingOrder, 'id' | 'timestamp'>) => void;
  updateOrder: (orderId: string, updates: Partial<TradingOrder>) => void;
  updatePortfolio: (portfolio: Portfolio) => void;
  setChartType: (type: 'candlestick' | 'line') => void;
  setTimeframe: (timeframe: '1m' | '5m' | '15m' | '1h' | '4h' | '1d') => void;
  setConnectionStatus: (connected: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // WebSocket connection management
  connect: () => void;
  disconnect: () => void;

  // Computed values
  getOrderBookSpread: (symbol: string) => number | null;
  getCurrentPrice: (symbol: string) => number | null;
  getTotalPortfolioValue: () => number;
}

export const useTradingStore = create<TradingState>()(
  devtools(
    subscribeWithSelector((set, get) => ({
      // Initial State
      selectedSymbol: 'BTCUSDT',
      marketTickers: new Map(),
      orderBooks: new Map(),
      candlestickData: new Map(),
      orders: [],
      portfolio: null,
      isConnected: false,
      isLoading: false,
      error: null,
      chartType: 'candlestick',
      timeframe: '15m',

      // Actions
      setSelectedSymbol: (symbol: string) => {
        set({ selectedSymbol: symbol });
      },

      updateMarketTicker: (ticker: MarketTicker) => {
        set((state) => {
          const newTickers = new Map(state.marketTickers);
          newTickers.set(ticker.symbol, ticker);
          return { marketTickers: newTickers };
        });
      },

      updateOrderBook: (orderBook: OrderBook) => {
        set((state) => {
          const newOrderBooks = new Map(state.orderBooks);
          newOrderBooks.set(orderBook.symbol, orderBook);
          return { orderBooks: newOrderBooks };
        });
      },

      updateCandlestickData: (symbol: string, data: CandlestickData[]) => {
        set((state) => {
          const newCandlestickData = new Map(state.candlestickData);
          newCandlestickData.set(symbol, data);
          return { candlestickData: newCandlestickData };
        });
      },

      addOrder: (orderData) => {
        set((state) => {
          const newOrder: TradingOrder = {
            ...orderData,
            id: Date.now().toString(),
            timestamp: Date.now(),
          };
          return { orders: [newOrder, ...state.orders] };
        });
      },

      updateOrder: (orderId: string, updates: Partial<TradingOrder>) => {
        set((state) => ({
          orders: state.orders.map(order =>
            order.id === orderId ? { ...order, ...updates } : order
          ),
        }));
      },

      updatePortfolio: (portfolio: Portfolio) => {
        set({ portfolio });
      },

      setChartType: (type) => set({ chartType: type }),
      setTimeframe: (timeframe) => set({ timeframe }),
      setConnectionStatus: (connected) => set({ isConnected: connected }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      connect: () => {
        // WebSocket connection logic will be implemented here
        set({ isConnected: true, error: null });
      },

      disconnect: () => {
        set({ isConnected: false });
      },

      // Computed values
      getOrderBookSpread: (symbol: string) => {
        const orderBook = get().orderBooks.get(symbol);
        if (!orderBook || orderBook.asks.length === 0 || orderBook.bids.length === 0) {
          return null;
        }
        const bestAsk = orderBook.asks[0].price;
        const bestBid = orderBook.bids[0].price;
        return bestAsk - bestBid;
      },

      getCurrentPrice: (symbol: string) => {
        const ticker = get().marketTickers.get(symbol);
        return ticker?.price || null;
      },

      getTotalPortfolioValue: () => {
        const portfolio = get().portfolio;
        return portfolio?.totalValue || 0;
      },
    })),
    {
      name: 'trading-store',
    }
  )
);

// Selectors for optimized re-renders
export const useSelectedSymbol = () => useTradingStore(state => state.selectedSymbol);
export const useMarketTicker = (symbol: string) => useTradingStore(state => state.marketTickers.get(symbol));
export const useOrderBook = (symbol: string) => useTradingStore(state => state.orderBooks.get(symbol));
export const useCandlestickData = (symbol: string) => useTradingStore(state => state.candlestickData.get(symbol));
export const usePortfolio = () => useTradingStore(state => state.portfolio);
export const useOrders = () => useTradingStore(state => state.orders);
export const useConnectionStatus = () => useTradingStore(state => state.isConnected);