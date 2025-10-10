// hooks/useTRViewChart.ts
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { chartAPI } from '@/lib/chart-api';

interface UseTRViewChartProps {
  stockCode: string;
  timeframe: 'minute' | 'day';
  enabled?: boolean;
}

// Helper to get YYYY-MM-DD format
const toYYYYMMDD = (date: Date) => date.toISOString().split('T')[0];
const MAX_INITIAL_CANDLES = 100;

const mergeCandles = (existing: ChartCandle[], incoming: ChartCandle[]) => {
  const map = new Map<string, ChartCandle>();
  for (const candle of existing) {
    map.set(candle.timestamp, candle);
  }
  for (const candle of incoming) {
    map.set(candle.timestamp, candle);
  }
  return Array.from(map.values()).sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );
};

export function useTRViewChart({
  stockCode,
  timeframe,
  enabled = true,
}: UseTRViewChartProps) {
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [oldestDate, setOldestDate] = useState<string | null>(null);
  const [canLoadMore, setCanLoadMore] = useState(true);
  const [hasExtendedRange, setHasExtendedRange] = useState(false);

  const chartDataRef = useRef<ChartCandle[]>([]);
  const hasExtendedRef = useRef(false);

  useEffect(() => {
    chartDataRef.current = chartData;
  }, [chartData]);

  useEffect(() => {
    hasExtendedRef.current = hasExtendedRange;
  }, [hasExtendedRange]);

  useEffect(() => {
    setHasExtendedRange(false);
    hasExtendedRef.current = false;
  }, [stockCode, timeframe]);

  const fetchData = useCallback(async ({ silent = false } = {}) => {
    if (!enabled || !stockCode) return;

    if (!silent) {
      setIsLoading(true);
    }
    setError(null);
    // ✅ 수정: setChartData([]) 제거 - 기존 데이터 유지하여 깜빡임 방지
    setCanLoadMore(true);

    try {
      let data: ChartCandle[] = [];
      const today = new Date();
      const todayStr = toYYYYMMDD(today);

      if (timeframe === 'minute') {
        data = await chartAPI.getMinuteCandles(stockCode, { date: todayStr });
      } else if (timeframe === 'day') {
        const oneYearAgo = new Date(today);
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        const oneYearAgoStr = toYYYYMMDD(oneYearAgo);
        data = await chartAPI.getDayCandles(stockCode, oneYearAgoStr, todayStr);
      }

      let nextData = hasExtendedRef.current
        ? mergeCandles(chartDataRef.current, data)
        : data;

      if (!hasExtendedRef.current && nextData.length > MAX_INITIAL_CANDLES) {
        nextData = nextData.slice(-MAX_INITIAL_CANDLES);
      }

      chartDataRef.current = nextData;
      setChartData(nextData);

      if (nextData.length > 0) {
        const firstTimestamp = nextData[0].timestamp;
        setOldestDate(firstTimestamp.slice(0, 10));
        setCanLoadMore(true);
      } else {
        setOldestDate(null);
        setCanLoadMore(false);
      }

    } catch (err) {
      const message = err instanceof Error ? err.message : '차트 데이터 로드 실패';
      setError(message);
      console.error(`[${timeframe}] TRView 차트 데이터 로드 오류:`, err);
    } finally {
      if (!silent) {
        setIsLoading(false);
      }
    }
  }, [enabled, stockCode, timeframe]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!enabled || timeframe !== 'day') return;

    const intervalId = setInterval(() => {
      fetchData({ silent: true });
    }, 60000);

    return () => clearInterval(intervalId);
  }, [enabled, timeframe, fetchData]);

  const loadPrevious = useCallback(async () => {
    if (isLoadingMore || !canLoadMore || !oldestDate) return;

    setIsLoadingMore(true);
    
    try {
        let prevData: ChartCandle[] = [];
        const oldestDateObj = new Date(oldestDate);

        if (timeframe === 'minute') {
            // Load previous day
            const targetDate = new Date(oldestDateObj);
            targetDate.setDate(targetDate.getDate() - 1);
            const prevDateStr = toYYYYMMDD(targetDate);
            
            // Simple load, can be improved with holiday checks later
            prevData = await chartAPI.getMinuteCandles(stockCode, { date: prevDateStr });
            if (prevData.length > 0) {
                setOldestDate(prevDateStr);
            }
        } else if (timeframe === 'day') {
            // Load previous year
            const endDateObj = new Date(oldestDateObj);
            endDateObj.setDate(endDateObj.getDate() - 1);
            const startDateObj = new Date(endDateObj);
            startDateObj.setFullYear(startDateObj.getFullYear() - 1);

            const endDateStr = toYYYYMMDD(endDateObj);
            const startDateStr = toYYYYMMDD(startDateObj);

            prevData = await chartAPI.getDayCandles(stockCode, startDateStr, endDateStr);
            if (prevData.length > 0) {
                setOldestDate(startDateStr);
            }
        }

        if (prevData.length > 0) {
            const combined = mergeCandles(prevData, chartDataRef.current);
            chartDataRef.current = combined;
            setChartData(combined);
            setHasExtendedRange(true);
            hasExtendedRef.current = true;
            const earliest = combined[0]?.timestamp;
            if (earliest) {
              setOldestDate(earliest.slice(0, 10));
            }
            setCanLoadMore(true);
        } else {
            setCanLoadMore(false);
        }
    } catch (err) {
      console.error(`[${timeframe}] Error loading previous data:`, err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [isLoadingMore, canLoadMore, oldestDate, stockCode, timeframe]);

  const refetch = useCallback(() => fetchData(), [fetchData]);

  return { 
    chartData, 
    isLoading, 
    error, 
    refetch, 
    loadPrevious, // Renamed from loadPreviousDay
    isLoadingMore, 
    canLoadMore,
    hasExtendedRange
  };
}
