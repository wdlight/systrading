/**
 * 주문 관련 커스텀 훅
 * 주문 실행, 조회, 정정, 취소 API 연동
 */

import { useState, useCallback, useEffect } from 'react';
import {
  OrderRequest,
  OrderModifyRequest,
  OrderCancelRequest,
  OrderResponse,
  PendingOrdersResponse,
  OrderHistoryResponse,
  OrderSide,
} from '@/lib/types/order';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * useOrders 훅
 */
export function useOrders() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * API 호출 헬퍼 함수
   */
  const fetchAPI = useCallback(async <T,>(
    url: string,
    options?: RequestInit
  ): Promise<T> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API 오류: ${response.status}`);
      }

      const data = await response.json();
      return data as T;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 매수 주문 실행
   */
  const placeBuyOrder = useCallback(
    async (request: Omit<OrderRequest, 'order_side'>): Promise<OrderResponse> => {
      return fetchAPI<OrderResponse>('/api/orders/buy', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },
    [fetchAPI]
  );

  /**
   * 매도 주문 실행
   */
  const placeSellOrder = useCallback(
    async (request: Omit<OrderRequest, 'order_side'>): Promise<OrderResponse> => {
      return fetchAPI<OrderResponse>('/api/orders/sell', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },
    [fetchAPI]
  );

  /**
   * 주문 정정
   */
  const modifyOrder = useCallback(
    async (request: OrderModifyRequest): Promise<OrderResponse> => {
      return fetchAPI<OrderResponse>('/api/orders/modify', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    },
    [fetchAPI]
  );

  /**
   * 주문 취소
   */
  const cancelOrder = useCallback(
    async (request: OrderCancelRequest): Promise<OrderResponse> => {
      return fetchAPI<OrderResponse>('/api/orders/cancel', {
        method: 'DELETE',
        body: JSON.stringify(request),
      });
    },
    [fetchAPI]
  );

  /**
   * 미체결 주문 조회
   */
  const getPendingOrders = useCallback(
    async (stockCode?: string): Promise<PendingOrdersResponse> => {
      const url = stockCode
        ? `/api/orders/pending?stock_code=${stockCode}`
        : '/api/orders/pending';

      return fetchAPI<PendingOrdersResponse>(url, {
        method: 'GET',
      });
    },
    [fetchAPI]
  );

  /**
   * 체결 내역 조회
   */
  const getOrderHistory = useCallback(
    async (
      stockCode?: string,
      startDate?: string,
      endDate?: string
    ): Promise<OrderHistoryResponse> => {
      const params = new URLSearchParams();
      if (stockCode) params.append('stock_code', stockCode);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const url = params.toString()
        ? `/api/orders/history?${params.toString()}`
        : '/api/orders/history';

      return fetchAPI<OrderHistoryResponse>(url, {
        method: 'GET',
      });
    },
    [fetchAPI]
  );

  return {
    // 상태
    isLoading,
    error,

    // 주문 실행
    placeBuyOrder,
    placeSellOrder,

    // 주문 관리
    modifyOrder,
    cancelOrder,

    // 주문 조회
    getPendingOrders,
    getOrderHistory,
  };
}

/**
 * 주문 폴링 훅 (실시간 업데이트용)
 * 미체결 주문과 체결 내역을 주기적으로 조회
 */
export function useOrdersPolling(interval: number = 5000) {
  const [pendingOrders, setPendingOrders] = useState<PendingOrdersResponse | null>(null);
  const [orderHistory, setOrderHistory] = useState<OrderHistoryResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  const { getPendingOrders, getOrderHistory } = useOrders();

  const startPolling = useCallback(() => {
    setIsPolling(true);
  }, []);

  const stopPolling = useCallback(() => {
    setIsPolling(false);
  }, []);

  const refreshOrders = useCallback(async () => {
    try {
      const [pending, history] = await Promise.all([
        getPendingOrders(),
        getOrderHistory(),
      ]);

      setPendingOrders(pending);
      setOrderHistory(history);
    } catch (error) {
      console.error('주문 조회 실패:', error);
    }
  }, [getPendingOrders, getOrderHistory]);

  // 폴링 효과
  useEffect(() => {
    if (typeof window === 'undefined' || !isPolling) return;

    // 즉시 실행
    refreshOrders();

    // 주기적 실행
    const intervalId = setInterval(refreshOrders, interval);

    return () => {
      clearInterval(intervalId);
    };
  }, [isPolling, interval, refreshOrders]);

  return {
    pendingOrders,
    orderHistory,
    isPolling,
    startPolling,
    stopPolling,
    refreshOrders,
  };
}
