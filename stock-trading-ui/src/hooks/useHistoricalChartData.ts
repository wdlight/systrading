/**
 * 과거 차트 데이터 자동 로딩 훅
 *
 * 기능:
 * 1. 초기 로딩 시 과거 3일치 데이터 프리로드
 * 2. 좌측 드래그 시 추가 과거 데이터 자동 fetch
 * 3. 메모리 캐시로 중복 요청 방지
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { getKSTToday } from '@/lib/utils/datetime';

interface UseHistoricalChartDataProps {
  stockCode: string;
  enabled?: boolean; // 자동 로딩 활성화 여부
  initialDays?: number; // 초기 프리로드 일수
}

interface HistoricalDataCache {
  [dateKey: string]: ChartCandle[]; // 날짜별 캐시 (YYYYMMDD 키)
}

export function useHistoricalChartData({
  stockCode,
  enabled = true,
  initialDays = 3,
}: UseHistoricalChartDataProps) {
  const [allChartData, setAllChartData] = useState<ChartCandle[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 메모리 캐시 (날짜별)
  const cacheRef = useRef<HistoricalDataCache>({});
  const isInitializedRef = useRef(false);
  const loadingDatesRef = useRef<Set<string>>(new Set()); // 중복 요청 방지

  /**
   * 특정 날짜 범위의 데이터 fetch
   * 검증된 /minute API를 여러 번 호출하여 과거 데이터 수집
   */
  const fetchHistoricalRange = useCallback(
    async (endDate: Date, days: number): Promise<HistoricalDataCache> => {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const historicalData: HistoricalDataCache = {};

      try {
        console.log(`📥 과거 ${days}일 데이터 로드 시작...`);

        // 각 날짜별로 개별 API 호출
        for (let i = 0; i < days; i++) {
          const targetDate = new Date(endDate);
          targetDate.setDate(targetDate.getDate() - i);
          const dateStr = targetDate.toISOString().split('T')[0]; // YYYY-MM-DD
          const dateKey = dateStr.replace(/-/g, ''); // YYYYMMDD

          try {
            const response = await fetch(
              `${API_BASE_URL}/api/chart/${stockCode}/minute?date=${dateStr}`,
              { signal: AbortSignal.timeout(30000) }
            );

            if (!response.ok) {
              console.warn(`⚠️ ${dateStr} 데이터 로드 실패: ${response.status}`);
              continue; // 해당 날짜 스킵하고 계속 진행
            }

            const candles: ChartCandle[] = await response.json();

            // 유효한 데이터만 저장 (빈 배열 제외)
            if (Array.isArray(candles) && candles.length > 0) {
              historicalData[dateKey] = candles;
              console.log(`  ✅ ${dateStr}: ${candles.length}개 캔들 로드`);
            } else {
              console.warn(`  ⚠️ ${dateStr}: 데이터 없음 (거래일 아님)`);
            }
          } catch (err) {
            console.warn(`  ❌ ${dateStr} 로드 실패:`, err);
            // 개별 날짜 실패는 무시하고 계속 진행
            continue;
          }
        }

        console.log(`📥 과거 데이터 로드 완료:`, {
          requestedDays: days,
          receivedDates: Object.keys(historicalData).length,
          totalCandles: Object.values(historicalData).reduce((sum, candles) => sum + candles.length, 0),
        });

        return historicalData;
      } catch (err) {
        console.error('과거 데이터 로드 실패:', err);
        throw err;
      }
    },
    [stockCode]
  );

  /**
   * 초기 데이터 로드 (오늘 + 과거 N일)
   */
  useEffect(() => {
    if (!enabled || !stockCode || isInitializedRef.current) return;

    const loadInitialData = async () => {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      setIsLoading(true);
      setError(null);

      try {
        // 1. 오늘 데이터 로드 (명시적으로 오늘 날짜 전달)
        // ⚠️ 중요: 한국 표준시(KST) 기준 오늘 날짜 사용
        const todayKST = getKSTToday(); // KST 기준 YYYY-MM-DD
        const todayResponse = await fetch(
          `${API_BASE_URL}/api/chart/${stockCode}/minute?date=${todayKST}`,
          { signal: AbortSignal.timeout(30000) }
        );

        let todayData: ChartCandle[] = [];
        if (todayResponse.ok) {
          todayData = await todayResponse.json();
          console.log(`✅ 오늘 데이터 (KST ${todayKST}): ${todayData.length}개 캔들`);
        } else {
          console.warn(`⚠️ 오늘 데이터 로드 실패: ${todayResponse.status}`);
        }

        // 2. 과거 N일 데이터 로드
        // ⚠️ KST 기준으로 현재 시간 생성
        const kstNow = new Date();
        const kstOffset = 9 * 60 * 60 * 1000; // 9시간을 밀리초로
        const kstDate = new Date(kstNow.getTime() + kstOffset);
        const historicalData = await fetchHistoricalRange(kstDate, initialDays);

        // 3. 캐시에 저장 (오늘 데이터도 포함)
        const todayKey = todayKST.replace(/-/g, ''); // YYYYMMDD
        cacheRef.current = {
          ...historicalData,
          ...(todayData.length > 0 ? { [todayKey]: todayData } : {})
        };

        // 4. 모든 데이터 병합 (시간순 정렬)
        const allDates = Object.keys(historicalData).sort(); // YYYYMMDD 문자열 정렬
        const mergedData: ChartCandle[] = [];

        allDates.forEach(dateKey => {
          mergedData.push(...historicalData[dateKey]);
        });

        if (todayData.length > 0) {
          mergedData.push(...todayData);
        }

        // 5. 시간순 정렬 (중복 제거는 RechartsAdapter에서 수행)
        mergedData.sort((a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );

        setAllChartData(mergedData);
        isInitializedRef.current = true;

        console.log('✅ 초기 데이터 로드 완료:', {
          todayCandles: todayData.length,
          historicalDates: allDates.length,
          totalCandles: mergedData.length,
        });
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : '데이터 로드 실패';
        setError(errorMsg);
        console.error('초기 데이터 로드 오류:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialData();
  }, [enabled, stockCode, initialDays, fetchHistoricalRange]);

  /**
   * 특정 날짜의 데이터 추가 로드 (좌측 드래그 시)
   */
  const loadMoreData = useCallback(
    async (targetDate: Date) => {
      const dateKey = targetDate.toISOString().split('T')[0].replace(/-/g, ''); // YYYYMMDD

      // 이미 캐시에 있으면 스킵
      if (cacheRef.current[dateKey]) {
        console.log(`✅ 캐시된 데이터 사용: ${dateKey}`);
        return;
      }

      // 이미 로딩 중이면 스킵
      if (loadingDatesRef.current.has(dateKey)) {
        console.log(`⏳ 이미 로딩 중: ${dateKey}`);
        return;
      }

      loadingDatesRef.current.add(dateKey);
      setIsLoading(true);

      try {
        // 1일치 데이터만 로드
        const historicalData = await fetchHistoricalRange(targetDate, 1);

        if (Object.keys(historicalData).length === 0) {
          console.warn(`⚠️ 해당 날짜는 거래일이 아닙니다: ${dateKey}`);
          return;
        }

        // 캐시 업데이트
        cacheRef.current = { ...cacheRef.current, ...historicalData };

        // 기존 데이터 앞에 추가
        const newCandles = historicalData[dateKey] || [];
        setAllChartData(prev => {
          const merged = [...newCandles, ...prev];
          // 시간순 정렬
          merged.sort((a, b) =>
            new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
          );
          console.log(`📥 과거 데이터 추가: ${dateKey}, ${newCandles.length}개 캔들`);
          return merged;
        });
      } catch (err) {
        console.error('추가 데이터 로드 실패:', err);
      } finally {
        loadingDatesRef.current.delete(dateKey);
        setIsLoading(false);
      }
    },
    [fetchHistoricalRange]
  );

  /**
   * 범위 변경 이벤트 핸들러 (Brush/Drag)
   * startIndex가 0에 가까워지면 과거 데이터 자동 로드
   */
  const handleRangeChange = useCallback(
    (range: { startIndex: number; endIndex: number }) => {
      if (!enabled || allChartData.length === 0) return;

      // 좌측 끝에 도달하면 이전 날짜 데이터 로드
      if (range.startIndex < 10) {
        const firstCandle = allChartData[0];
        const firstDate = new Date(firstCandle.timestamp);

        // 하루 전 날짜 계산
        const previousDate = new Date(firstDate);
        previousDate.setDate(previousDate.getDate() - 1);

        console.log('🔍 좌측 드래그 감지 → 과거 데이터 로드:', {
          startIndex: range.startIndex,
          targetDate: previousDate.toISOString().split('T')[0],
        });

        loadMoreData(previousDate);
      }
    },
    [enabled, allChartData, loadMoreData]
  );

  return {
    chartData: allChartData,
    isLoading,
    error,
    handleRangeChange,
    loadMoreData,
  };
}
