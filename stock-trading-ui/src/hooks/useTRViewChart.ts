// hooks/useTRViewChart.ts
'use client';

import { useState, useEffect, useCallback } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { chartAPI } from '@/lib/chart-api';

interface UseTRViewChartProps {
  stockCode: string;
  date?: string;  // YYYY-MM-DD
  enabled?: boolean;
}

export function useTRViewChart({
  stockCode,
  date,
  enabled = true,
}: UseTRViewChartProps) {
  const [chartData, setChartData] = useState<ChartCandle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChartData = useCallback(async () => {
    if (!enabled || !stockCode) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await chartAPI.getMinuteCandles(stockCode, { date });
      setChartData(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : '차트 데이터 로드 실패';
      setError(message);
      console.error('TRView 차트 데이터 로드 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, [enabled, stockCode, date]);

  useEffect(() => {
    fetchChartData();
  }, [fetchChartData]);

  return { chartData, isLoading, error, refetch: fetchChartData };
}
