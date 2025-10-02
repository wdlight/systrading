'use client';

import { useState, useEffect, useCallback } from 'react';
import { KoreanStockChart } from '@/lib/types/korean-stocks';

interface ChartApiResponse {
  success: boolean;
  message: string;
  data: KoreanStockChart[];
  metadata: {
    stock_code: string;
    period: string;
    count: number;
    total_volume: number;
    average_price: number;
    date_range: {
      start: string | null;
      end: string | null;
    };
    last_updated: string;
  };
}

interface UseRealChartDataOptions {
  enabled?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number; // milliseconds
  includeExtendedHours?: boolean;  // 🆕 시간외 거래 포함 (8:30~16:00)
  regularHoursOnly?: boolean;      // 🆕 정규장만 (9:00~15:30)
  targetDate?: string;             // 🆕 대상 날짜 (YYYY-MM-DD)
}

interface UseRealChartDataReturn {
  chartData: KoreanStockChart[];
  metadata: ChartApiResponse['metadata'] | null;
  isLoading: boolean;
  error: string | null;
  isConnected: boolean;
  lastUpdated: Date | null;
  refetch: () => Promise<void>;
  retry: () => Promise<void>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useRealChartData(
  stockCode: string,
  timeframe: string = 'D',
  options: UseRealChartDataOptions = {}
): UseRealChartDataReturn {
  const {
    enabled = true,
    autoRefresh = false,
    refreshInterval = timeframe === '1m' ? 5000 : 60000, // 1분봉은 5초마다, 그 외는 1분마다
    includeExtendedHours = false,    // 기본값: 시간외 미포함
    regularHoursOnly = true,          // 기본값: 정규장만
    targetDate = undefined            // 기본값: 오늘
  } = options;

  const [chartData, setChartData] = useState<KoreanStockChart[]>([]);
  const [metadata, setMetadata] = useState<ChartApiResponse['metadata'] | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchChartData = useCallback(async (): Promise<void> => {
    if (!stockCode || !enabled) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      console.log(`🔍 Fetching chart data for ${stockCode} (${timeframe})`);

      let url = '';
      if (timeframe === '1m') {
        // ✅ 백엔드의 Full Day 분봉 API 엔드포인트 사용 (Gap-fill 지원)
        const params = new URLSearchParams();
        if (targetDate) params.append('date', targetDate);

        // Full Day 엔드포인트는 항상 9:00~15:30 전체 데이터 반환
        url = `${API_BASE_URL}/api/chart/${stockCode}/minute/full?${params.toString()}`;
        console.log(`🔍 Using Full Day API: ${url}`);
      } else {
        url = `${API_BASE_URL}/api/stocks/${stockCode}/chart?period=${timeframe}&format=frontend`;
      }
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // 타임아웃 설정
        signal: AbortSignal.timeout(30000), // 30초 타임아웃
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const responseData = await response.json();
      let chartData: KoreanStockChart[] = [];

      if (timeframe === '1m') {
        // 분봉 API는 직접 배열 반환 - 이미 KoreanStockChart 형식
        if (Array.isArray(responseData)) {
          chartData = responseData;
          console.log(`📊 분봉 데이터 수신: ${chartData.length}개`);
        } else {
          console.error('❌ 분봉 API 응답이 배열이 아닙니다:', responseData);
        }
      } else {
        // 일봉 API는 {output1, output2} 구조 반환
        const result = responseData as any;
        if (result.output2 && Array.isArray(result.output2)) {
          // 한국투자증권 API 형식을 KoreanStockChart로 변환
          chartData = result.output2.map((item: any) => ({
            timestamp: `${item.stck_bsop_date.substring(0, 4)}-${item.stck_bsop_date.substring(4, 6)}-${item.stck_bsop_date.substring(6, 8)}T00:00:00`,
            open: parseFloat(item.stck_oprc),
            high: parseFloat(item.stck_hgpr),
            low: parseFloat(item.stck_lwpr),
            close: parseFloat(item.stck_clpr),
            volume: parseInt(item.acml_vol),
            tradingValue: null,
            foreignBuy: null,
            foreignSell: null,
            institutionalBuy: null,
            institutionalSell: null,
            individualBuy: null,
            individualSell: null,
          }));
          console.log(`📊 일봉 데이터 수신: ${chartData.length}개`);
        }
      }

      if (chartData && chartData.length > 0) {
        console.log(`✅ Chart data loaded: ${chartData.length} candles`);
        console.log(`📊 First candle:`, chartData[0]);
        console.log(`📊 Last candle:`, chartData[chartData.length - 1]);
        setChartData(chartData);
        setMetadata({
          stock_code: stockCode,
          period: timeframe,
          count: chartData.length,
          total_volume: chartData.reduce((sum, candle) => sum + (candle.volume || 0), 0),
          average_price: chartData.reduce((sum, candle) => sum + candle.close, 0) / chartData.length,
          date_range: {
            start: chartData[0]?.timestamp || null,
            end: chartData[chartData.length - 1]?.timestamp || null,
          },
          last_updated: new Date().toISOString(),
        });
        setIsConnected(true);
        setLastUpdated(new Date());
        setError(null);
      } else {
        console.warn(`⚠️ API returned empty or invalid data`);
        setError('No chart data available');
        setChartData([]);
        setMetadata(null);
        setIsConnected(false);
      }

    } catch (err) {
      console.error('❌ Chart data fetch error:', err);

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
      setChartData([]);
      setMetadata(null);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [stockCode, timeframe, enabled, includeExtendedHours, regularHoursOnly, targetDate]);

  const retry = useCallback(async (): Promise<void> => {
    console.log(`🔄 Retrying chart data fetch for ${stockCode}`);
    await fetchChartData();
  }, [fetchChartData, stockCode]);

  // 초기 데이터 로드
  useEffect(() => {
    if (enabled && stockCode) {
      fetchChartData();
    }
  }, [fetchChartData, enabled, stockCode]);

  // 자동 새로고침
  useEffect(() => {
    if (!autoRefresh || !enabled || !stockCode) {
      return;
    }

    const intervalId = setInterval(() => {
      console.log(`🔄 Auto-refreshing chart data for ${stockCode}`);
      fetchChartData();
    }, refreshInterval);

    return () => {
      clearInterval(intervalId);
    };
  }, [autoRefresh, enabled, stockCode, refreshInterval, fetchChartData]);

  return {
    chartData,
    metadata,
    isLoading,
    error,
    isConnected,
    lastUpdated,
    refetch: fetchChartData,
    retry
  };
}

// 테스트용 Hook - 삼성전자 고정
export function useSamsungChartData(
  timeframe: string = 'D',
  options: UseRealChartDataOptions = {}
): UseRealChartDataReturn {
  return useRealChartData('005930', timeframe, {
    ...options,
    autoRefresh: options.autoRefresh ?? true,
  });
}

// API 연결 테스트용 Hook
export function useChartApiTest(stockCode: string) {
  const [testResult, setTestResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const runTest = useCallback(async () => {
    if (!stockCode) return;

    setIsLoading(true);
    setError(null);

    try {
      const url = `${API_BASE_URL}/api/stocks/${stockCode}/chart/test`;
      const response = await fetch(url, {
        signal: AbortSignal.timeout(30000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setTestResult(result);
      console.log('🧪 API Test Result:', result);

    } catch (err) {
      console.error('❌ API Test Error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, [stockCode]);

  return {
    testResult,
    isLoading,
    error,
    runTest
  };
}

// 차트 데이터 유효성 검증 함수
export function validateChartData(data: KoreanStockChart[]): {
  isValid: boolean;
  errors: string[];
  warnings: string[];
} {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!Array.isArray(data)) {
    errors.push('Chart data is not an array');
    return { isValid: false, errors, warnings };
  }

  if (data.length === 0) {
    warnings.push('Chart data is empty');
    return { isValid: true, errors, warnings };
  }

  data.forEach((candle, index) => {
    // 필수 필드 확인
    if (!candle.timestamp) {
      errors.push(`Candle ${index}: missing timestamp`);
    }

    // OHLCV 값 확인
    const { open, high, low, close, volume } = candle;

    if (typeof open !== 'number' || open <= 0) {
      errors.push(`Candle ${index}: invalid open price`);
    }
    if (typeof high !== 'number' || high <= 0) {
      errors.push(`Candle ${index}: invalid high price`);
    }
    if (typeof low !== 'number' || low <= 0) {
      errors.push(`Candle ${index}: invalid low price`);
    }
    if (typeof close !== 'number' || close <= 0) {
      errors.push(`Candle ${index}: invalid close price`);
    }
    if (typeof volume !== 'number' || volume < 0) {
      errors.push(`Candle ${index}: invalid volume`);
    }

    // OHLC 관계 확인
    if (low > high) {
      errors.push(`Candle ${index}: low > high`);
    }
    if (low > open || open > high) {
      errors.push(`Candle ${index}: open price out of range`);
    }
    if (low > close || close > high) {
      errors.push(`Candle ${index}: close price out of range`);
    }

    // 경고 사항
    if (volume === 0) {
      warnings.push(`Candle ${index}: zero volume`);
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  };
}