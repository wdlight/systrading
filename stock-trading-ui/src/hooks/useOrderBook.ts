'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { OrderBookData, OrderBookUpdate } from '@/lib/types';
import { subscribeToOrderBookUpdates, wsManager } from '@/lib/websocket';
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
const SILENT_REFRESH_INTERVAL = 1000; // ✅ 1초로 변경 - 실시간 느낌 보장

export function useOrderBook({
  stockCode,
  autoSubscribe = true
}: UseOrderBookOptions): UseOrderBookReturn {
  const [orderBook, setOrderBook] = useState<OrderBookData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubscribed, setIsSubscribed] = useState(false);
  const lastUpdateRef = useRef<number>(0);

  const normalizeOrderBook = useCallback((raw: OrderBookData | null): OrderBookData | null => {
    if (!raw) return null;

    const normalizeRows = (rows: OrderBookData['asks'] | OrderBookData['bids']) =>
      (rows || []).map((row) => ({
        price: Number(row?.price) || 0,
        quantity: Number(row?.quantity) || 0,
      }));

    const resolveTimestamp = (input?: string) => {
      if (!input) return new Date().toISOString();
      const parsed = new Date(input);
      return Number.isNaN(parsed.getTime()) ? new Date().toISOString() : parsed.toISOString();
    };

    return {
      stock_code: raw.stock_code,
      current_price:
        typeof raw.current_price === 'number'
          ? raw.current_price
          : Number(raw.current_price) || undefined,
      asks: normalizeRows(raw.asks),
      bids: normalizeRows(raw.bids),
      timestamp: resolveTimestamp(raw.timestamp),
      market_status: raw.market_status,
      error: raw.error,
    };
  }, []);

  // 초기 데이터 로드 (REST API)
  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await apiClient.getCurrentOrderBook(stockCode);
      const normalized = normalizeOrderBook(data);
      lastUpdateRef.current = Date.now() - 1000;
      setOrderBook(normalized);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류');
      console.error('호가 데이터 로드 오류:', err);
    } finally {
      setIsLoading(false);
    }
  }, [stockCode, normalizeOrderBook]);

  const fetchLatestSilently = useCallback(async () => {
    try {
      const data = await apiClient.getCurrentOrderBook(stockCode);
      const normalized = normalizeOrderBook(data);
      if (normalized) {
        setOrderBook((prev) => ({ ...normalized, market_status: prev?.market_status ?? normalized.market_status }));
      }
    } catch (err) {
      console.error('호가 데이터 새로고침 오류:', err);
    }
  }, [stockCode, normalizeOrderBook]);

  // WebSocket 구독
  const subscribe = useCallback(async () => {
    if (isSubscribed) return;

    try {
      // REST API로 백엔드 KIS WebSocket 구독 요청
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/realtime/subscribe/orderbook?stock_code=${stockCode}`,
        { method: 'POST' }
      );

      if (!response.ok) {
        throw new Error('호가 구독 실패');
      }

      // WebSocket 연결 대기 및 구독
      const waitForConnection = async (maxWait = 5000) => {
        const startTime = Date.now();
        while (!wsManager.isConnected() && Date.now() - startTime < maxWait) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
        return wsManager.isConnected();
      };

      const isConnected = await waitForConnection();
      if (isConnected) {
        wsManager.send({
          type: 'subscribe',
          stock_code: stockCode
        });
        // 구독 성공 시 pending list에 추가
        wsManager.addPendingSubscription(stockCode);
        lastUpdateRef.current = Date.now() - 1000;
        setIsSubscribed(true);
        console.log(`✅ 호가 구독 시작: ${stockCode}`);
      } else {
        throw new Error('WebSocket 연결 타임아웃');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '구독 실패');
      console.error('호가 구독 오류:', err);
      throw err; // 호출 측에서 처리할 수 있도록 에러 재throw
    }
  }, [stockCode, isSubscribed]);

  // WebSocket 구독 해제
  const unsubscribe = useCallback(async () => {
    if (!isSubscribed) return;

    try {
      // # 임시 비활성화: 백엔드 지속 구독 테스트용
      // const response = await fetch(
      //   `${process.env.NEXT_PUBLIC_API_URL}/api/realtime/unsubscribe/orderbook?stock_code=${stockCode}`,
      //   { method: 'POST' }
      // );
      //
      // if (!response.ok) {
      //   throw new Error('호가 구독 해제 실패');
      // }
      //
      // // WebSocket 구독 해제
      // if (wsManager.isConnected()) {
      //   wsManager.send({
      //     type: 'unsubscribe',
      //     stock_code: stockCode
      //   });
      //   console.log(`❌ 호가 WebSocket 구독 해제: ${stockCode}`);
      // }
      //
      // // pending list에서 제거
      // wsManager.removePendingSubscription(stockCode);
      // setIsSubscribed(false);
      // console.log(`❌ 호가 구독 해제: ${stockCode}`);

      console.warn('⚠️ 호가 구독 해제 호출이 임시로 비활성화되었습니다. (백엔드 지속 구독 테스트)');
    } catch (err) {
      console.error('호가 구독 해제 오류:', err);
      throw err; // 호출 측에서 처리할 수 있도록 에러 재throw
    }
  }, [stockCode, isSubscribed]);

  // 데이터 새로고침
  const refresh = useCallback(async () => {
    await fetchLatestSilently();
  }, [fetchLatestSilently]);

  // WebSocket 연결 및 메시지 구독
  useEffect(() => {
    // WebSocket 연결 확인 및 시작
    if (!wsManager.isConnected()) {
      console.log('🔌 WebSocket 연결 시작...');
      wsManager.connect().catch((error) => {
        console.error('WebSocket 연결 실패:', error);
        setError('WebSocket 연결 실패');
      });
    }

    const unsubscribeWs = subscribeToOrderBookUpdates(stockCode, (update: OrderBookUpdate) => {
      // ✅ Throttling 완전 제거 - 모든 업데이트 즉시 반영
      const updateTime = Date.now();
      lastUpdateRef.current = updateTime;

      // ✅ 직접 정규화 - useCallback 메모이제이션 우회
      const normalizeRows = (rows: any[]) =>
        (rows || []).map((row: any) => ({
          price: Number(row?.price) || 0,
          quantity: Number(row?.quantity) || 0,
        }));

      // 🔥 디버깅: 백엔드에서 받은 원본 데이터 개수 확인
      console.log(`📦 백엔드 원본 데이터 - asks: ${update.data.asks?.length || 0}개, bids: ${update.data.bids?.length || 0}개`);
      console.log(`📦 asks 원본:`, update.data.asks);
      console.log(`📦 bids 원본:`, update.data.bids);

      const normalized: OrderBookData = {
        stock_code: update.stock_code,
        asks: normalizeRows(update.data.asks),
        bids: normalizeRows(update.data.bids),
        current_price: typeof update.data.current_price === 'number'
          ? update.data.current_price
          : Number(update.data.current_price) || undefined,
        timestamp: update.data.timestamp || new Date().toISOString(),
        market_status: undefined,
        error: undefined,
      };

      setOrderBook((prev) => {
        // ✅ 디버깅: 이전 vs 현재 비교
        const prevAsk1 = prev?.asks?.[0]?.price;
        const newAsk1 = normalized.asks?.[0]?.price;
        const prevBid1 = prev?.bids?.[0]?.price;
        const newBid1 = normalized.bids?.[0]?.price;

        console.log(`📊 [${new Date().toLocaleTimeString()}] 호가 실시간 업데이트: ${stockCode}`);
        console.log(`🔥 매도1: ${prevAsk1?.toLocaleString()} → ${newAsk1?.toLocaleString()} | 매수1: ${prevBid1?.toLocaleString()} → ${newBid1?.toLocaleString()}`);

        // ✅ 매번 완전히 새로운 객체 반환 - React 강제 렌더링
        const newState = {
          ...normalized,
          _updateId: updateTime, // 매번 다른 timestamp로 강제 렌더링
          market_status: prev?.market_status, // 이전 market_status 유지
        } as OrderBookData;

        console.log(`🆔 강제 렌더링 ID: ${updateTime}`);
        return newState;
      });
      setError(null);
    });

    return unsubscribeWs;
  }, [stockCode, normalizeOrderBook]);


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
      // # 임시 비활성화: 백엔드 지속 구독 모니터링을 위해 cleanup 시 구독 해제하지 않음
      // if (isSubscribed) {
      //   unsubscribe();
      // }
      //
      // if (wsManager.isConnected()) {
      //   wsManager.send({
      //     type: 'unsubscribe',
      //     stock_code: stockCode
      //   });
      // }
    };
  }, [autoSubscribe, isSubscribed, subscribe, unsubscribe, stockCode]);

  useEffect(() => {
    const timer = setInterval(() => {
      fetchLatestSilently();
    }, SILENT_REFRESH_INTERVAL);

    return () => clearInterval(timer);
  }, [fetchLatestSilently]);

  return {
    orderBook,
    isLoading,
    error,
    subscribe,
    unsubscribe,
    refresh,
  };
}
