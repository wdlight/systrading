'use client';

import React, { useMemo } from 'react';
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

const RealtimeCandlestickChart: React.FC<RealtimeCandlestickChartProps> = ({
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

  console.log('📊 [RealtimeCandlestickChart] 실시간 분봉 상태:', {
    stockCode,
    timeframe,
    currentCandle: currentCandle?.timestamp || null,
    finalizedCount: finalizedCandles.length,
    baseDataLength: baseChartData.length
  });

  const finalChartData = useMemo(() => {
    console.log('🔄 [Chart] 차트 데이터 병합 시작:', {
      baseLength: baseChartData.length,
      finalizedLength: finalizedCandles.length,
      currentCandle: currentCandle?.timestamp || null
    });

    let mergedData = [...baseChartData];

    // 1. 완성된 분봉 병합 (finalize 이벤트로 받은 것들)
    if (finalizedCandles.length > 0) {
      console.log(`📥 [Chart] ${finalizedCandles.length}개 완성된 분봉 병합 중...`);

      finalizedCandles.forEach((finalizedCandle) => {
        const existingIndex = mergedData.findIndex(
          c => c.timestamp === finalizedCandle.timestamp
        );

        if (existingIndex >= 0) {
          // 기존 데이터 교체 (WebSocket이 더 최신)
          console.log(`🔄 [Chart] 기존 분봉 교체: ${finalizedCandle.timestamp} (index: ${existingIndex})`);
          mergedData[existingIndex] = finalizedCandle;
        } else {
          // 새 분봉 추가
          console.log(`✨ [Chart] 새 분봉 추가: ${finalizedCandle.timestamp}`);
          mergedData.push(finalizedCandle);
        }
      });

      // 타임스탬프 정렬
      mergedData.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
      console.log(`✅ [Chart] 완성된 분봉 병합 완료, 총 ${mergedData.length}개`);
    }

    // 2. 현재 진행 중인 분봉 병합 (update 이벤트)
    if (currentCandle && mergedData.length > 0) {
      const lastCandle = mergedData[mergedData.length - 1];
      const currentMinute = currentCandle.timestamp.substring(0, 16);
      const lastMinute = lastCandle?.timestamp.substring(0, 16);

      console.log('🔄 [Chart] 진행 중 분봉 병합:', {
        currentMinute,
        lastMinute,
        isSameMinute: lastMinute === currentMinute
      });

      if (lastMinute === currentMinute) {
        // 같은 분봉: 마지막 항목 교체
        console.log(`🔄 [Chart] 동일 분봉 업데이트: ${currentCandle.timestamp}`);
        mergedData = [...mergedData.slice(0, -1), currentCandle];
      } else if (new Date(currentCandle.timestamp).getTime() > new Date(lastCandle.timestamp).getTime()) {
        // 새로운 분봉: 추가
        console.log(`✨ [Chart] 새 진행 중 분봉 추가: ${currentCandle.timestamp}`);
        mergedData = [...mergedData, currentCandle];
      }
    }

    console.log(`✅ [Chart] 최종 차트 데이터: ${mergedData.length}개 분봉`);
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
};

RealtimeCandlestickChart.displayName = 'RealtimeCandlestickChart';

export default RealtimeCandlestickChart;
