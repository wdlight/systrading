/**
 * 무한 스크롤 차트 데이터 훅
 * 좌측 드래그 시 이전 날짜 데이터 자동 로드
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { chartAPI } from '@/lib/chart-api';

export interface UseInfiniteChartDataOptions {
  stockCode: string;
  initialDate?: string;  // YYYY-MM-DD, 미지정 시 오늘
  loadThreshold?: number;  // 이전 데이터 로드 트리거 인덱스 (기본값: 20)
  maxDays?: number;  // 최대 로드할 날짜 수 (기본값: 5일)
  autoRefresh?: boolean;  // 🆕 자동 갱신 활성화 (기본값: true)
  refreshInterval?: number;  // 🆕 갱신 간격 ms (기본값: 60000 = 1분)
}

export interface UseInfiniteChartDataReturn {
  candles: ChartCandle[];
  isLoading: boolean;
  error: Error | null;
  loadPreviousDay: () => Promise<void>;
  loadNextDay: () => Promise<void>;
  refresh: () => Promise<void>;
  currentDateRange: { start: string; end: string };
  hasMore: boolean;
}

export function useInfiniteChartData(
  options: UseInfiniteChartDataOptions
): UseInfiniteChartDataReturn {
  const {
    stockCode,
    initialDate,
    loadThreshold = 20,
    maxDays = 5,
    autoRefresh = true,  // 기본값: 자동 갱신 활성화
    refreshInterval = 60000  // 기본값: 1분
  } = options;

  // 상태 관리
  const [candles, setCandles] = useState<ChartCandle[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [loadedDates, setLoadedDates] = useState<Set<string>>(new Set());
  const [currentDateRange, setCurrentDateRange] = useState<{ start: string; end: string }>({
    start: initialDate || new Date().toISOString().split('T')[0],
    end: initialDate || new Date().toISOString().split('T')[0]
  });

  // 중복 요청 방지
  const loadingRef = useRef<boolean>(false);
  const loadedDatesRef = useRef<Set<string>>(new Set());

  /**
   * 날짜 문자열에서 Date 객체 생성
   */
  const parseDate = (dateStr: string): Date => {
    return new Date(dateStr + 'T00:00:00');
  };

  /**
   * Date 객체를 YYYY-MM-DD 형식으로 변환
   */
  const formatDate = (date: Date): string => {
    return date.toISOString().split('T')[0];
  };

  /**
   * 캔들 데이터를 시간순으로 정렬
   */
  const sortCandles = (candles: ChartCandle[]): ChartCandle[] => {
    return [...candles].sort((a, b) =>
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );
  };

  /**
   * 초기 데이터 로드 (Full Day 전략)
   * - 항상 당일 전체 거래시간(9:00~15:30) 데이터 로드
   * - 실제 거래시간: 실제 OHLCV 데이터
   * - 미래 시간: 직전 종가로 채워진 데이터 (volume=0)
   */
  const loadInitialData = useCallback(async () => {
    if (loadingRef.current) return;

    setIsLoading(true);
    setError(null);
    loadingRef.current = true;

    try {
      console.log('[useInfiniteChartData] Loading full day candles:', { stockCode, initialDate });

      // Full Day 전략: 항상 9:00~15:30 전체 데이터 로드
      const data = await chartAPI.getFullDayCandles(stockCode, initialDate);

      // 🔍 VALIDATION: 데이터 검증
      if (data.length !== 391) {
        console.error(`❌ VALIDATION ERROR: Expected 391 candles, received ${data.length}`);
      }

      const volumeZero = data.filter(d => d.volume === 0).length;
      const volumeActual = data.length - volumeZero;
      console.log(`✅ VALIDATION: Received ${data.length} candles | ${volumeZero} filled | ${volumeActual} actual`);

      const targetDate = initialDate || formatDate(new Date());

      setCandles(sortCandles(data));
      setLoadedDates(new Set([targetDate]));
      loadedDatesRef.current = new Set([targetDate]);

      setCurrentDateRange({
        start: targetDate,
        end: targetDate
      });

      console.log(`[useInfiniteChartData] Full day data loaded: ${data.length} candles (9:00~15:30)`);
    } catch (err) {
      console.error('[useInfiniteChartData] Error loading full day data:', err);
      setError(err as Error);
    } finally {
      setIsLoading(false);
      loadingRef.current = false;
    }
  }, [stockCode, initialDate]);

  /**
   * 이전 날짜 데이터 로드
   */
  const loadPreviousDay = useCallback(async () => {
    if (loadingRef.current) {
      console.log('[useInfiniteChartData] Already loading, skipping...');
      return;
    }

    // 최대 날짜 수 제한
    if (loadedDatesRef.current.size >= maxDays) {
      console.log('[useInfiniteChartData] Max days limit reached:', maxDays);
      return;
    }

    setIsLoading(true);
    loadingRef.current = true;

    try {
      const currentStart = parseDate(currentDateRange.start);
      const previousDate = new Date(currentStart);
      previousDate.setDate(previousDate.getDate() - 1);
      const previousDateStr = formatDate(previousDate);

      // 이미 로드된 날짜는 스킵
      if (loadedDatesRef.current.has(previousDateStr)) {
        console.log('[useInfiniteChartData] Date already loaded:', previousDateStr);
        return;
      }

      console.log('[useInfiniteChartData] Loading previous day:', previousDateStr);

      const data = await chartAPI.getPreviousDayCandles(stockCode, currentDateRange.start);

      if (data.length > 0) {
        // 새로운 데이터를 기존 데이터 앞에 추가
        setCandles((prev) => sortCandles([...data, ...prev]));

        const newLoadedDates = new Set(loadedDatesRef.current);
        newLoadedDates.add(previousDateStr);
        setLoadedDates(newLoadedDates);
        loadedDatesRef.current = newLoadedDates;

        setCurrentDateRange((prev) => ({
          start: previousDateStr,
          end: prev.end
        }));

        console.log(`[useInfiniteChartData] Previous day loaded: ${data.length} candles`);
      } else {
        console.log('[useInfiniteChartData] No data for previous day');
      }
    } catch (err) {
      console.error('[useInfiniteChartData] Error loading previous day:', err);
      setError(err as Error);
    } finally {
      setIsLoading(false);
      loadingRef.current = false;
    }
  }, [stockCode, currentDateRange.start, maxDays]);

  /**
   * 다음 날짜 데이터 로드
   */
  const loadNextDay = useCallback(async () => {
    if (loadingRef.current) {
      console.log('[useInfiniteChartData] Already loading, skipping...');
      return;
    }

    setIsLoading(true);
    loadingRef.current = true;

    try {
      const currentEnd = parseDate(currentDateRange.end);
      const nextDate = new Date(currentEnd);
      nextDate.setDate(nextDate.getDate() + 1);
      const nextDateStr = formatDate(nextDate);

      // 이미 로드된 날짜는 스킵
      if (loadedDatesRef.current.has(nextDateStr)) {
        console.log('[useInfiniteChartData] Date already loaded:', nextDateStr);
        return;
      }

      console.log('[useInfiniteChartData] Loading next day:', nextDateStr);

      const data = await chartAPI.getNextDayCandles(stockCode, currentDateRange.end);

      if (data.length > 0) {
        // 새로운 데이터를 기존 데이터 뒤에 추가
        setCandles((prev) => sortCandles([...prev, ...data]));

        const newLoadedDates = new Set(loadedDatesRef.current);
        newLoadedDates.add(nextDateStr);
        setLoadedDates(newLoadedDates);
        loadedDatesRef.current = newLoadedDates;

        setCurrentDateRange((prev) => ({
          start: prev.start,
          end: nextDateStr
        }));

        console.log(`[useInfiniteChartData] Next day loaded: ${data.length} candles`);
      } else {
        console.log('[useInfiniteChartData] No data for next day');
      }
    } catch (err) {
      console.error('[useInfiniteChartData] Error loading next day:', err);
      setError(err as Error);
    } finally {
      setIsLoading(false);
      loadingRef.current = false;
    }
  }, [stockCode, currentDateRange.end]);

  /**
   * 데이터 새로고침
   */
  const refresh = useCallback(async () => {
    setCandles([]);
    setLoadedDates(new Set());
    loadedDatesRef.current = new Set();
    await loadInitialData();
  }, [loadInitialData]);

  /**
   * 초기 로드
   */
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  /**
   * 실시간 차트 업데이트 (Polling with Gap-fill)
   * - Backend Gap-fill 로직 활용하여 자동으로 누락 구간 채움
   * - 당일 데이터만 실시간 업데이트
   * - 거래시간(9:00~15:30) 중에만 동작
   * - 설정된 interval마다 전체 데이터 재조회 (Gap 자동 채워짐)
   */
  useEffect(() => {
    // autoRefresh 비활성화 시 스킵
    if (!autoRefresh) {
      console.log('[useInfiniteChartData] Auto-refresh disabled');
      return;
    }

    // 오늘 날짜가 아니면 실시간 업데이트 불필요
    const isToday = initialDate === formatDate(new Date()) || !initialDate;
    if (!isToday) {
      console.log('[useInfiniteChartData] Not today, skipping real-time updates');
      return;
    }

    console.log(`[useInfiniteChartData] Starting real-time polling for ${stockCode} (interval: ${refreshInterval}ms)`);

    const pollingInterval = setInterval(async () => {
      const now = new Date();

      // 거래시간 체크 (9:00~15:30)
      const hour = now.getHours();
      const minute = now.getMinutes();
      const isTradingHours = (hour === 9 && minute >= 0) ||
                             (hour > 9 && hour < 15) ||
                             (hour === 15 && minute <= 30);

      if (!isTradingHours) {
        console.log('[useInfiniteChartData] Outside trading hours, skipping update');
        return;
      }

      if (loadingRef.current) {
        console.log('[useInfiniteChartData] Already loading, skipping real-time update');
        return;
      }

      try {
        console.log(`🔄 [Real-time Update] Fetching latest data for ${stockCode} at ${now.toLocaleTimeString()}`);

        // Backend Gap-fill 활용: 전체 Full Day 데이터 재조회
        // - Cache가 있으면 Cache 반환
        // - Gap이 있으면 자동으로 Gap 구간만 API 호출하여 채움
        const latestData = await chartAPI.getFullDayCandles(stockCode, currentDateRange.end);

        // 기존 데이터와 병합 (중복 제거)
        setCandles(prev => {
          // timestamp를 key로 Map 생성 (최신 데이터 우선)
          const candleMap = new Map<string, ChartCandle>();

          // 기존 데이터 추가
          prev.forEach(c => candleMap.set(c.timestamp, c));

          // 최신 데이터로 덮어쓰기 (업데이트된 volume/close 반영)
          latestData.forEach(c => candleMap.set(c.timestamp, c));

          // 배열로 변환 후 시간순 정렬
          const merged = Array.from(candleMap.values());
          const sorted = sortCandles(merged);

          // 업데이트 로그
          const newCandles = sorted.length - prev.length;
          if (newCandles > 0) {
            console.log(`✅ [Real-time Update] Added ${newCandles} new candles (total: ${sorted.length})`);
          } else {
            console.log(`✅ [Real-time Update] Data refreshed (no new candles, total: ${sorted.length})`);
          }

          return sorted;
        });

      } catch (err) {
        console.error('[useInfiniteChartData] Real-time update failed:', err);
        // 에러 무시하고 다음 interval에 재시도
      }
    }, refreshInterval);

    // Cleanup
    return () => {
      console.log('[useInfiniteChartData] Stopping real-time polling');
      clearInterval(pollingInterval);
    };
  }, [stockCode, initialDate, autoRefresh, refreshInterval, currentDateRange.end, sortCandles]);

  return {
    candles,
    isLoading,
    error,
    loadPreviousDay,
    loadNextDay,
    refresh,
    currentDateRange,
    hasMore: loadedDates.size < maxDays
  };
}