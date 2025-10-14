'use client';

import { useState, useEffect, useCallback } from 'react';
import { MarketOverview, RegionalMarketData, MarketRegion } from '@/lib/types';
import { apiClient } from '@/lib/api-client';
import { subscribeToMarketIndexUpdates, unsubscribeFromMarketIndexUpdates } from '@/lib/websocket';

export function useMarketData() {
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    try {
      // 환경변수로 yfinance 사용 여부 제어
      const useYFinance = process.env.NEXT_PUBLIC_USE_YFINANCE === 'true';

      let overview: MarketOverview;
      if (useYFinance) {
        // yfinance API 사용 (추가 지수 포함)
        overview = await apiClient.getYFinanceMarketOverview();
      } else {
        // 기존 한투 API 사용 (기본 5개 지수만)
        overview = await apiClient.getMarketOverview();
      }

      setMarketOverview(overview);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch market data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialData();

    // 60초마다 데이터 새로고침
    const interval = setInterval(loadInitialData, 60000);

    type IndexUpdatePayload = {
      index_code?: string;
      code?: string;
      current?: number | string;
      change?: number | string;
      change_rate?: number | string;
      raw?: Record<string, unknown>;
      meta?: Record<string, unknown>;
      timestamp?: string;
    };

    const handleIndexUpdate = (data: IndexUpdatePayload) => {
      setMarketOverview(prev => {
        if (!prev) return null;

        const newOverview = { ...prev };
        const rawCode = data.index_code ?? data.code;
        const code = typeof rawCode === 'string' ? rawCode.toUpperCase() : String(rawCode ?? '');

        const indexKey =
          code === '001' || code === '0001' ? 'kospi'
            : code === '201' || code === '1001' || code === '0201' || code === '1501' || code === '2001' ? 'kosdaq'
              : code === 'NDX' || code === 'IXIC' ? 'nasdaq'
                : code === 'US500' || code === 'SPX' ? 'sp500'
                  : code === 'FX@KRW' || code === 'USDKRW' ? 'usd_krw'
                    : null;

        if (indexKey && newOverview[indexKey]) {
          const current = Number(data.current);
          const change = Number(data.change);
          const changeRate = Number(data.change_rate);

          newOverview[indexKey] = {
            ...newOverview[indexKey],
            current: Number.isFinite(current) ? current : newOverview[indexKey].current,
            change: Number.isFinite(change) ? change : newOverview[indexKey].change,
            change_rate: Number.isFinite(changeRate) ? changeRate : newOverview[indexKey].change_rate,
            raw: data.raw ?? newOverview[indexKey].raw,
            meta: data.meta ?? newOverview[indexKey].meta,
            timestamp: data.timestamp ?? newOverview[indexKey].timestamp,
          };
        }
        return newOverview;
      });
    };

    subscribeToMarketIndexUpdates(handleIndexUpdate);

    return () => {
      clearInterval(interval);
      unsubscribeFromMarketIndexUpdates(handleIndexUpdate);
    };
  }, [loadInitialData]);

  return { marketOverview, isLoading, error, refetch: loadInitialData };
}

// 추가 지수 표시용 훅
export function useRegionalMarketData(region: MarketRegion) {
  const [data, setData] = useState<RegionalMarketData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiClient.getRegionalMarketData(region);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load regional data');
    } finally {
      setLoading(false);
    }
  }, [region]);

  useEffect(() => {
    loadData();

    // 60초마다 데이터 새로고침
    const interval = setInterval(loadData, 60000);

    return () => clearInterval(interval);
  }, [loadData]);

  return { data, loading, error, refetch: loadData };
}
