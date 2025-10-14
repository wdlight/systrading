'use client';

import { useState, useEffect, useCallback } from 'react';
import { OrderBookData } from '@/lib/types';
import { subscribeToOrderBookUpdates } from '@/lib/websocket';
import { apiClient } from '@/lib/api-client';

export interface UseOrderBookOptions {
  stockCode: string;
  autoSubscribe?: boolean;
}

export interface UseOrderBookReturn {
  orderBook: OrderBookData | null;
  isLoading: boolean;
  error: string | null;
  subscribe: () => Promise<void>;
  unsubscribe: () => Promise<void>;
  refresh: () => Promise<void>;
}

/**
 * 실시간 호가 데이터를 관리하는 훅
 * 
 * @example
 * ```tsx
 * const { orderBook, isLoading, error } = useOrderBook({
 *   stockCode: '005930',
 *   autoSubscribe: true
 * });
 * ```
 */
export function useOrderBook({
  stockCode,
  autoSubscribe = true
}: UseOrderBookOptions): UseOrderBookReturn {
  const [orderBook, setOrderBook] = useState<OrderBookData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);

  // 초기 데이터 로드 (REST API)
  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await apiClient.getCurrentOrderBook(stockCode);
      setOrderBook(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
      console.error('호가 데이터 로드 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, [stockCode]);

  // WebSocket 구독
  const subscribe = useCallback(async () => {
    if (isSubscribed) return;

    try {
      // 백엔드에 구독 요청
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/realtime/subscribe/orderbook?stock_code=${stockCode}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('호가 구독 실패');
      }

      setIsSubscribed(true);
      console.log(`✅ 호가 구독 시작: ${stockCode}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '구독 실패');
      console.error('호가 구독 오류:', err);
    }
  }, [stockCode, isSubscribed]);

  // WebSocket 구독 해제
  const unsubscribe = useCallback(async () => {
    if (!isSubscribed) return;

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/realtime/unsubscribe/orderbook?stock_code=${stockCode}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('호가 구독 해제 실패');
      }

      setIsSubscribed(false);
      console.log(`❌ 호가 구독 해제: ${stockCode}`);
    } catch (err) {
      console.error('호가 구독 해제 오류:', err);
    }
  }, [stockCode, isSubscribed]);

  // 데이터 새로고침
  const refresh = useCallback(async () => {
    await loadInitialData();
  }, [loadInitialData]);

  // WebSocket 메시지 구독
  useEffect(() => {
    const unsubscribeWs = subscribeToOrderBookUpdates(stockCode, (data) => {
      setOrderBook(data);
      setError(null);
    });

    return unsubscribeWs;
  }, [stockCode]);

  // 초기 데이터 로드
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  // 자동 구독
  useEffect(() => {
    if (autoSubscribe && !isSubscribed) {
      subscribe();
    }

    return () => {
      if (isSubscribed) {
        unsubscribe();
      }
    };
  }, [autoSubscribe, isSubscribed, subscribe, unsubscribe]);

  return {
    orderBook,
    isLoading,
    error,
    subscribe,
    unsubscribe,
    refresh,
  };
}
