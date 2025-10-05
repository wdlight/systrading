// hooks/useTRViewChart.ts
'use client';

import { useState, useEffect, useCallback } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { chartAPI } from '@/lib/chart-api';

interface UseTRViewChartProps {
  stockCode: string;
  timeframe: 'minute' | 'day';
  enabled?: boolean;
}

// Helper to get YYYY-MM-DD format
const toYYYYMMDD = (date: Date) => date.toISOString().split('T')[0];

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

  const fetchInitialData = useCallback(async () => {
    if (!enabled || !stockCode) return;

    setIsLoading(true);
    setError(null);
    setChartData([]);
    setCanLoadMore(true);

    try {
      let data: ChartCandle[] = [];
      const today = new Date();
      const todayStr = toYYYYMMDD(today);

      if (timeframe === 'minute') {
        data = await chartAPI.getMinuteCandles(stockCode, { date: todayStr });
        if (data.length > 0) {
          setOldestDate(todayStr);
        }
      } else if (timeframe === 'day') {
        const oneYearAgo = new Date(today);
        oneYearAgo.setFullYear(today.getFullYear() - 1);
        const oneYearAgoStr = toYYYYMMDD(oneYearAgo);
        data = await chartAPI.getDayCandles(stockCode, oneYearAgoStr, todayStr);
        if (data.length > 0) {
          // The oldest date is the start of the fetched range
          setOldestDate(oneYearAgoStr);
        }
      }
      
      setChartData(data);
      if (data.length === 0) {
        setCanLoadMore(false);
      }

    } catch (err) {
      const message = err instanceof Error ? err.message : '차트 데이터 로드 실패';
      setError(message);
      console.error(`[${timeframe}] TRView 차트 데이터 로드 오류:`, err);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, stockCode, timeframe]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

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
            setChartData(currentData => {
                const newData = [...prevData, ...currentData];
                const uniqueData = Array.from(new Map(newData.map(item => [item.timestamp, item])).values())
                .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
                return uniqueData;
            });
        } else {
            setCanLoadMore(false);
        }
    } catch (err) {
      console.error(`[${timeframe}] Error loading previous data:`, err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [isLoadingMore, canLoadMore, oldestDate, stockCode, timeframe]);

  return { 
    chartData, 
    isLoading, 
    error, 
    refetch: fetchInitialData, 
    loadPrevious, // Renamed from loadPreviousDay
    isLoadingMore, 
    canLoadMore 
  };
}