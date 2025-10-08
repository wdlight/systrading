'use client';

import { useState, useEffect, useCallback } from 'react';
import { MarketOverview } from '@/lib/types';
import { apiClient } from '@/lib/api-client';
import { subscribeToMarketIndexUpdates, unsubscribeFromMarketIndexUpdates } from '@/lib/websocket';

export function useMarketData() {
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    try {
      const overview = await apiClient.getMarketOverview();
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
      unsubscribeFromMarketIndexUpdates(handleIndexUpdate);
    };
  }, [loadInitialData]);

  return { marketOverview, isLoading, error };
}
