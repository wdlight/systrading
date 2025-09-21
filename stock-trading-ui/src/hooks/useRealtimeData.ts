import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  AccountBalance, 
  WatchlistItem, 
  MarketOverview,
  ConnectionState,
  UseRealtimeDataReturn
} from '@/lib/types';
import { apiClient, fetchWithErrorHandling } from '@/lib/api-client';
import { 
  subscribeToAccountUpdates,
  subscribeToWatchlistUpdates,
  subscribeToConnectionStatus
} from '@/lib/websocket';
import { useWebSocket } from './useWebSocket';

/**
 * 실시간 데이터를 관리하는 훅
 */
export function useRealtimeData(): UseRealtimeDataReturn {
  const [accountBalance, setAccountBalance] = useState<AccountBalance | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [marketOverview, setMarketOverview] = useState<MarketOverview | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionState>({
    status: 'disconnected',
    reconnectAttempts: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { isConnected } = useWebSocket();
  const lastRefreshTime = useRef<Date>(new Date());

  // 초기 데이터 로드
  const loadInitialData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // 병렬로 초기 데이터 로드
      const [accountResult, watchlistResult, marketResult] = await Promise.allSettled([
        fetchWithErrorHandling(() => apiClient.getAccountBalance()),
        fetchWithErrorHandling(() => apiClient.getWatchlist()),
        fetchWithErrorHandling(() => apiClient.getMarketOverview()),
      ]);

      // 계좌 정보 설정
      if (accountResult.status === 'fulfilled' && accountResult.value.data) {
        setAccountBalance(accountResult.value.data);
      } else if (accountResult.status === 'fulfilled' && accountResult.value.error) {
        console.error('계좌 정보 로드 실패:', accountResult.value.error);
      }

      // 워치리스트 설정
      if (watchlistResult.status === 'fulfilled' && watchlistResult.value.data) {
        setWatchlist(watchlistResult.value.data);
      } else if (watchlistResult.status === 'fulfilled' && watchlistResult.value.error) {
        console.error('워치리스트 로드 실패:', watchlistResult.value.error);
      }

      // 시장 현황 설정
      if (marketResult.status === 'fulfilled' && marketResult.value.data) {
        setMarketOverview(marketResult.value.data);
      } else if (marketResult.status === 'fulfilled' && marketResult.value.error) {
        console.error('시장 현황 로드 실패:', marketResult.value.error);
      }

      lastRefreshTime.current = new Date();
    } catch (error) {
      console.error('초기 데이터 로드 오류:', error);
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 데이터 새로고침
  const refreshData = useCallback(async () => {
    await loadInitialData();
  }, [loadInitialData]);

  // WebSocket 연결 상태 변경 구독
  useEffect(() => {
    const unsubscribe = subscribeToConnectionStatus(setConnectionStatus);
    return unsubscribe;
  }, []);

  // 초기 데이터 로드
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // 계좌 업데이트 구독
  useEffect(() => {
    const unsubscribe = subscribeToAccountUpdates((data) => {
      setAccountBalance(data);
      setError(null); // 성공적인 업데이트 시 에러 클리어
    });

    return unsubscribe;
  }, []);

  // 워치리스트 업데이트 구독
  useEffect(() => {
    const unsubscribe = subscribeToWatchlistUpdates((data) => {
      console.log('🔄 워치리스트 업데이트 수신:', data);
      setWatchlist([...data]); // 새로운 배열을 생성하여 상태 업데이트
      setError(null); // 성공적인 업데이트 시 에러 클리어
    });

    return unsubscribe;
  }, []);

  // 연결 재설정 시 데이터 새로고침
  useEffect(() => {
    if (isConnected && connectionStatus.status === 'connected') {
      const timeSinceLastRefresh = Date.now() - lastRefreshTime.current.getTime();
      
      // 1분 이상 지났거나 에러가 있는 경우 새로고침
      if (timeSinceLastRefresh > 60000 || error) {
        refreshData();
      }
    }
  }, [isConnected, connectionStatus.status, error, refreshData]);

  // 정기적인 데이터 새로고침 (WebSocket 연결이 끊어진 경우 대비)
  useEffect(() => {
    if (!isConnected) {
      const interval = setInterval(() => {
        refreshData();
      }, 30000); // 30초마다 새로고침

      return () => clearInterval(interval);
    }
  }, [isConnected, refreshData]);

  return {
    accountBalance,
    watchlist,
    connectionStatus,
    marketOverview,
    isLoading,
    error,
    refreshData,
  };
}