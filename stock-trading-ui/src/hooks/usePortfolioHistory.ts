'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { mockPortfolioHistory, HistoryPoint } from '@/lib/mock/portfolioHistory';
import {
  PortfolioHistoryPoint,
  PortfolioPerformanceMetrics,
  PortfolioTimeRange,
} from '@/lib/types';

const PERIOD_FALLBACK_MAP: Record<PortfolioTimeRange, keyof typeof mockPortfolioHistory> = {
  '1D': '1D',
  '1W': '1W',
  '1M': '1M',
  '3M': '3M',
  '6M': '6M',
  '1Y': '1Y',
  ALL: 'ALL',
};

function mapHistoryPoint(point: HistoryPoint): PortfolioHistoryPoint {
  return {
    date: point.date,
    portfolio: point.portfolio,
    benchmark: point.benchmark,
  };
}

function calculateMetrics(history: PortfolioHistoryPoint[]): PortfolioPerformanceMetrics {
  if (history.length < 2) {
    return {
      totalReturn: 0,
      maxDrawdown: 0,
      volatility: 0,
    };
  }

  const values = history.map((point) => point.portfolio);
  const first = values[0];
  const last = values[values.length - 1];

  const totalReturn = first > 0 ? ((last - first) / first) * 100 : 0;

  let peak = values[0];
  let maxDrawdown = 0;

  values.forEach((value) => {
    if (value > peak) {
      peak = value;
    }
    const drawdown = peak > 0 ? ((value - peak) / peak) * 100 : 0;
    if (drawdown < maxDrawdown) {
      maxDrawdown = drawdown;
    }
  });

  const dailyReturns: number[] = [];
  for (let i = 1; i < values.length; i += 1) {
    const prev = values[i - 1];
    const current = values[i];
    if (prev > 0) {
      dailyReturns.push((current - prev) / prev);
    }
  }

  const meanReturn =
    dailyReturns.reduce((acc, value) => acc + value, 0) / (dailyReturns.length || 1);
  const variance =
    dailyReturns.reduce((acc, value) => acc + (value - meanReturn) ** 2, 0) /
    (dailyReturns.length || 1);
  const volatility = Math.sqrt(variance) * Math.sqrt(252) * 100; // 연율화

  return {
    totalReturn,
    maxDrawdown,
    volatility,
  };
}

export interface UsePortfolioHistoryResult {
  history: PortfolioHistoryPoint[];
  metrics: PortfolioPerformanceMetrics;
  isLoading: boolean;
  error: string | null;
  usingMock: boolean;
  refresh: () => Promise<void>;
}

export function usePortfolioHistory(range: PortfolioTimeRange): UsePortfolioHistoryResult {
  const [history, setHistory] = useState<PortfolioHistoryPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingMock, setUsingMock] = useState(false);

  const loadHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const apiData = await apiClient.getPortfolioHistory(range);
      if (Array.isArray(apiData) && apiData.length) {
        setHistory(apiData);
        setUsingMock(false);
      } else {
        const fallback = mockPortfolioHistory[PERIOD_FALLBACK_MAP[range]].map(mapHistoryPoint);
        setHistory(fallback);
        setUsingMock(true);
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : '포트폴리오 이력을 불러오는 중 문제가 발생했습니다.';
      setError(message);
      const fallback = mockPortfolioHistory[PERIOD_FALLBACK_MAP[range]].map(mapHistoryPoint);
      setHistory(fallback);
      setUsingMock(true);
    } finally {
      setIsLoading(false);
    }
  }, [range]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const metrics = useMemo(() => calculateMetrics(history), [history]);

  return {
    history,
    metrics,
    isLoading,
    error,
    usingMock,
    refresh: loadHistory,
  };
}
