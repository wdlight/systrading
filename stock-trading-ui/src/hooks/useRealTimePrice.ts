'use client';

import { useState, useEffect, useCallback } from 'react';

interface RealTimePriceData {
  success: boolean;
  stock_code: string;
  current_price: number;
  change_amount: number;
  change_rate: number;
  volume: number;
  trading_value: number;
  high_price: number;
  low_price: number;
  open_price: number;
  previous_close: number;
  market_cap: number;
  timestamp: string;
  market_status: string;
}

interface QuoteData extends RealTimePriceData {
  recent_candles: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  volatility: number;
  avg_volume_5d: number;
  price_range_5d: {
    high: number;
    low: number;
  };
  last_updated: string;
}

interface UseRealTimePriceOptions {
  enabled?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
  includeQuoteData?: boolean; // 상세 정보 포함 여부
}

interface UseRealTimePriceReturn {
  priceData: RealTimePriceData | null;
  quoteData: QuoteData | null;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
  retry: () => Promise<void>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useRealTimePrice(
  stockCode: string,
  options: UseRealTimePriceOptions = {}
): UseRealTimePriceReturn {
  const {
    enabled = true,
    autoRefresh = false,
    refreshInterval = 5000, // 5초마다 업데이트
    includeQuoteData = false
  } = options;

  const [priceData, setPriceData] = useState<RealTimePriceData | null>(null);
  const [quoteData, setQuoteData] = useState<QuoteData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchPriceData = useCallback(async (): Promise<void> => {
    if (!stockCode || !enabled) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log(`🔍 Fetching real-time price for ${stockCode}`);

      const endpoint = includeQuoteData ? 'quote' : 'price';
      const url = `${API_BASE_URL}/api/stocks/${stockCode}/${endpoint}`;

      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(10000), // 10초 타임아웃
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      if (result.success) {
        console.log(`✅ Price data loaded: ${result.current_price.toLocaleString()}원`);

        setPriceData(result);

        if (includeQuoteData) {
          setQuoteData(result as QuoteData);
        }

        setIsConnected(true);
        setLastUpdated(new Date());
        setError(null);
      } else {
        console.warn(`⚠️ API returned error: ${result.error}`);
        setError(result.error || 'Unknown error');
        setPriceData(null);
        setQuoteData(null);
        setIsConnected(false);
      }

    } catch (err) {
      console.error('❌ Price data fetch error:', err);

      let errorMessage = 'Unknown error occurred';

      if (err instanceof Error) {
        if (err.name === 'TimeoutError') {
          errorMessage = 'Request timeout - Backend server might be slow';
        } else if (err.message.includes('Failed to fetch')) {
          errorMessage = 'Cannot connect to backend server. Is it running on port 8000?';
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
      setPriceData(null);
      setQuoteData(null);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [stockCode, enabled, includeQuoteData]);

  const retry = useCallback(async (): Promise<void> => {
    console.log(`🔄 Retrying price data fetch for ${stockCode}`);
    await fetchPriceData();
  }, [fetchPriceData, stockCode]);

  // 초기 데이터 로드
  useEffect(() => {
    if (enabled && stockCode) {
      fetchPriceData();
    }
  }, [fetchPriceData, enabled, stockCode]);

  // 자동 새로고침
  useEffect(() => {
    if (!autoRefresh || !enabled || !stockCode) {
      return;
    }

    const intervalId = setInterval(() => {
      console.log(`🔄 Auto-refreshing price data for ${stockCode}`);
      fetchPriceData();
    }, refreshInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [autoRefresh, enabled, stockCode, refreshInterval, fetchPriceData]);

  return {
    priceData,
    quoteData,
    isLoading,
    error,
    isConnected,
    lastUpdated,
    refetch: fetchPriceData,
    retry
  };
}

// 삼성전자 실시간 가격 전용 Hook
export function useSamsungRealTimePrice(
  options: UseRealTimePriceOptions = {}
): UseRealTimePriceReturn {
  return useRealTimePrice('005930', {
    ...options,
    autoRefresh: options.autoRefresh ?? true,
    refreshInterval: options.refreshInterval ?? 1000, // 1초마다
    includeQuoteData: options.includeQuoteData ?? true // 상세 정보 포함
  });
}

// 가격 변화 방향 계산
export function getPriceDirection(changeAmount: number): 'up' | 'down' | 'neutral' {
  if (changeAmount > 0) return 'up';
  if (changeAmount < 0) return 'down';
  return 'neutral';
}

// 가격 변화율 색상 결정
export function getPriceColor(changeRate: number): string {
  if (changeRate > 0) return 'text-red-400'; // 상승 (빨간색)
  if (changeRate < 0) return 'text-blue-400'; // 하락 (파란색)
  return 'text-gray-400'; // 보합 (회색)
}

// 숫자 포맷팅
export function formatPrice(price: number): string {
  return price.toLocaleString();
}

export function formatVolume(volume: number): string {
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(1)}억`;
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(1)}만`;
  } else {
    return volume.toLocaleString();
  }
}

export function formatMarketCap(marketCap: number): string {
  if (marketCap >= 1000000000000) {
    return `${(marketCap / 1000000000000).toFixed(1)}조`;
  } else if (marketCap >= 100000000) {
    return `${(marketCap / 100000000).toFixed(1)}억`;
  } else {
    return marketCap.toLocaleString();
  }
}