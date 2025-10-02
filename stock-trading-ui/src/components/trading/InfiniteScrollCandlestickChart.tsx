/**
 * 무한 스크롤 캔들스틱 차트
 * useInfiniteChartData 훅을 사용하여 자동으로 이전/다음 날짜 데이터 로드
 */

'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { UniversalChart } from './chart-adapters';
import { useInfiniteChartData } from '@/hooks/useInfiniteChartData';

export interface InfiniteScrollCandlestickChartProps {
  stockCode: string;
  height?: number;
  timeframe?: string;
  initialDate?: string;  // YYYY-MM-DD 형식
  maxDays?: number;  // 최대 로드할 날짜 수 (기본값: 5일)
  loadThreshold?: number;  // 이전 데이터 로드 트리거 인덱스 (기본값: 20)
  chartLibrary?: 'recharts' | 'tradingview' | 'echarts' | 'lightweight-charts';
  autoRefresh?: boolean;  // 🆕 자동 갱신 활성화 (기본값: true)
  refreshInterval?: number;  // 🆕 갱신 간격 ms (기본값: 60000 = 1분)
}

export default function InfiniteScrollCandlestickChart({
  stockCode,
  height = 400,
  timeframe = '1m',
  initialDate,
  maxDays = 5,
  loadThreshold = 20,
  chartLibrary = 'recharts',
  autoRefresh = true,  // 기본값: 자동 갱신 활성화
  refreshInterval = 60000  // 기본값: 1분
}: InfiniteScrollCandlestickChartProps) {
  const {
    candles,
    isLoading,
    error,
    loadPreviousDay,
    loadNextDay,
    currentDateRange,
    hasMore
  } = useInfiniteChartData({
    stockCode,
    initialDate,
    loadThreshold,
    maxDays,
    autoRefresh,
    refreshInterval
  });

  const [brushIndices, setBrushIndices] = useState<{ startIndex: number; endIndex: number } | null>(null);
  const [isAutoLoading, setIsAutoLoading] = useState(false);

  /**
   * Brush 변경 핸들러
   * 사용자가 차트를 드래그하여 viewWindow를 변경할 때 호출
   */
  const handleBrushChange = useCallback((indices: { startIndex: number; endIndex: number }) => {
    setBrushIndices(indices);
  }, []);

  /**
   * 자동 이전 날짜 로드
   * startIndex가 loadThreshold보다 작으면 자동으로 이전 날짜 로드
   */
  useEffect(() => {
    const autoLoadPrevious = async () => {
      if (
        brushIndices &&
        brushIndices.startIndex < loadThreshold &&
        !isLoading &&
        !isAutoLoading &&
        hasMore
      ) {
        console.log('[InfiniteScroll] Auto-loading previous day, startIndex:', brushIndices.startIndex);
        setIsAutoLoading(true);

        try {
          await loadPreviousDay();
        } catch (err) {
          console.error('[InfiniteScroll] Failed to load previous day:', err);
        } finally {
          setIsAutoLoading(false);
        }
      }
    };

    autoLoadPrevious();
  }, [brushIndices, loadThreshold, isLoading, isAutoLoading, hasMore, loadPreviousDay]);

  /**
   * 에러 핸들러
   */
  const handleError = useCallback((errorMessage: string) => {
    console.error('[InfiniteScroll] Chart error:', errorMessage);
  }, []);

  // 로딩 상태 표시
  if (isLoading && candles.length === 0) {
    return (
      <div
        className="bg-[#0a0a0b] border border-gray-700 rounded-lg flex items-center justify-center"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-3 text-gray-400">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="text-sm">차트 데이터 로딩 중...</p>
        </div>
      </div>
    );
  }

  // 에러 상태 표시
  if (error) {
    return (
      <div
        className="bg-[#0a0a0b] border border-red-900/50 rounded-lg flex items-center justify-center"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-3 text-red-400">
          <svg
            className="w-12 h-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p className="text-sm font-medium">차트 데이터 로드 실패</p>
          <p className="text-xs text-gray-500">{error.message}</p>
        </div>
      </div>
    );
  }

  // 데이터 없음 상태
  if (candles.length === 0) {
    return (
      <div
        className="bg-[#0a0a0b] border border-gray-700 rounded-lg flex items-center justify-center"
        style={{ height }}
      >
        <div className="flex flex-col items-center gap-3 text-gray-400">
          <svg
            className="w-12 h-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p className="text-sm">차트 데이터가 없습니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* 로딩 인디케이터 (추가 데이터 로드 중) */}
      {isLoading && candles.length > 0 && (
        <div className="absolute top-2 right-2 z-10 bg-gray-800/90 backdrop-blur-sm border border-gray-700 rounded-lg px-3 py-2 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          <span className="text-xs text-gray-300">이전 데이터 로딩 중...</span>
        </div>
      )}

      {/* 날짜 범위 표시 */}
      <div className="absolute top-2 left-2 z-10 bg-gray-800/90 backdrop-blur-sm border border-gray-700 rounded-lg px-3 py-1.5">
        <div className="flex items-center gap-2 text-xs text-gray-300">
          <span className="font-medium">{currentDateRange.start}</span>
          {currentDateRange.start !== currentDateRange.end && (
            <>
              <span className="text-gray-500">~</span>
              <span className="font-medium">{currentDateRange.end}</span>
            </>
          )}
          <span className="text-gray-500">|</span>
          <span className="text-gray-400">{candles.length}개 캔들</span>
        </div>
      </div>

      {/* 무한 스크롤 안내 (더 로드 가능한 경우) */}
      {hasMore && (
        <div className="absolute bottom-2 left-2 z-10 bg-blue-900/20 backdrop-blur-sm border border-blue-700/50 rounded-lg px-3 py-1.5">
          <div className="flex items-center gap-2 text-xs text-blue-300">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
            <span>좌측으로 드래그하면 이전 데이터 로드</span>
          </div>
        </div>
      )}

      {/* 차트 렌더링 */}
      <UniversalChart
        library={chartLibrary}
        chartData={candles}
        height={height}
        timeframe={timeframe}
        onError={handleError}
        onBrushChange={handleBrushChange}
      />
    </div>
  );
}