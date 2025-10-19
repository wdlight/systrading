'use client';

import React, { memo, useMemo } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { UniversalChart } from './chart-adapters';
import { useHistoricalChartData } from '@/hooks/useHistoricalChartData';
import { useRealtimeMinuteCandles } from '@/hooks/useRealtimeMinuteCandles';

interface RealtimeCandlestickChartProps {
  // ✅ Backward compatibility: chartData 또는 stockCode 둘 다 지원
  chartData?: ChartCandle[]; // 직접 데이터 전달 (기존 방식)
  stockCode?: string; // 자동 데이터 로딩 (새 방식)
  height?: number;
  timeframe: string;
  enableHistoricalLoad?: boolean; // 과거 데이터 자동 로딩 활성화 여부
  initialDays?: number; // 초기 프리로드 일수 (기본값: 3)
  onRangeChange?: (range: { startIndex: number; endIndex: number }) => void; // 드래그 시 과거 데이터 로드
}

const RealtimeCandlestickChart: React.FC<RealtimeCandlestickChartProps> = memo(({
  chartData: externalChartData,
  stockCode,
  height = 400,
  timeframe,
  enableHistoricalLoad = true,
  initialDays = 3,
  onRangeChange: externalOnRangeChange
}) => {
  // 🎯 과거 데이터 자동 로딩 훅 (stockCode가 제공된 경우만)
  const {
    chartData: autoChartData,
    isLoading,
    error,
    handleRangeChange
  } = useHistoricalChartData({
    stockCode: stockCode || '',
    enabled: !!stockCode && enableHistoricalLoad && !externalChartData,
    initialDays
  });

  // ✅ chartData 우선순위: externalChartData > autoChartData
  const baseChartData = externalChartData || autoChartData;

  const { currentCandle, finalizedCandles } = useRealtimeMinuteCandles(
    stockCode || '',
    timeframe === 'minute' && !!stockCode
  );

  const finalChartData = useMemo(() => {
    let mergedData = [...baseChartData];

    // 1. 완성된 분봉 병합 (finalize 이벤트로 받은 것들)
    if (finalizedCandles.length > 0) {
      finalizedCandles.forEach((finalizedCandle) => {
        const existingIndex = mergedData.findIndex(
          c => c.timestamp === finalizedCandle.timestamp
        );

        if (existingIndex >= 0) {
          // 기존 데이터 교체 (WebSocket이 더 최신)
          mergedData[existingIndex] = finalizedCandle;
        } else {
          // 새 분봉 추가
          mergedData.push(finalizedCandle);
        }
      });

      // 타임스탬프 정렬
      mergedData.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
    }

    // 2. 현재 진행 중인 분봉 병합 (update 이벤트)
    if (currentCandle && mergedData.length > 0) {
      const lastCandle = mergedData[mergedData.length - 1];
      const currentMinute = currentCandle.timestamp.substring(0, 16);
      const lastMinute = lastCandle?.timestamp.substring(0, 16);

      if (lastMinute === currentMinute) {
        // 같은 분봉: 마지막 항목 교체
        mergedData = [...mergedData.slice(0, -1), currentCandle];
      } else if (new Date(currentCandle.timestamp).getTime() > new Date(lastCandle.timestamp).getTime()) {
        // 새로운 분봉: 추가
        mergedData = [...mergedData, currentCandle];
      }
    }

    return mergedData;
  }, [baseChartData, currentCandle, finalizedCandles]);

  // 로딩 상태 표시 (자동 로딩 모드일 때만)
  if (stockCode && !externalChartData && isLoading && baseChartData.length === 0) {
    return (
      <div
        className="bg-[#0a0a0b] border border-gray-700 rounded-lg flex items-center justify-center"
        style={{ height }}
      >
        <div className="text-center text-gray-400">
          <div className="text-blue-400 mb-2">📊 차트 로딩 중...</div>
          <div className="text-xs">과거 {initialDays}일치 데이터 불러오는 중</div>
        </div>
      </div>
    );
  }

  // 에러 상태 표시 (자동 로딩 모드일 때만)
  if (stockCode && !externalChartData && error) {
    return (
      <div
        className="bg-[#0a0a0b] border border-red-700 rounded-lg flex items-center justify-center"
        style={{ height }}
      >
        <div className="text-center text-red-400">
          <div className="text-xl mb-2">⚠️ 오류 발생</div>
          <div className="text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <UniversalChart
      library="recharts"
      chartData={finalChartData}
      height={height}
      timeframe={timeframe}
      events={{
        // ✅ 외부 핸들러 우선, 없으면 내부 handleRangeChange (stockCode 모드일 때만)
        onRangeChange: externalOnRangeChange || (stockCode && !externalChartData ? handleRangeChange : undefined),
        onError: (error) => {
          console.error('차트 렌더링 오류:', error);
        }
      }}
    />
  );
}, (prevProps, nextProps) => {
  // ✅ Backward compatibility: chartData와 stockCode 모두 비교
  if (prevProps.chartData !== nextProps.chartData) {
    return false; // chartData가 변경되면 재렌더링
  }
  if (prevProps.stockCode !== nextProps.stockCode) {
    return false;
  }
  if (prevProps.height !== nextProps.height || prevProps.timeframe !== nextProps.timeframe) {
    return false;
  }
  if (prevProps.enableHistoricalLoad !== nextProps.enableHistoricalLoad) {
    return false;
  }
  if (prevProps.initialDays !== nextProps.initialDays) {
    return false;
  }

  // chartData가 배열인 경우 길이 비교
  if (Array.isArray(prevProps.chartData) && Array.isArray(nextProps.chartData)) {
    if (prevProps.chartData.length !== nextProps.chartData.length) {
      return false;
    }
  }

  return true;
});

RealtimeCandlestickChart.displayName = 'RealtimeCandlestickChart';

export default RealtimeCandlestickChart;
