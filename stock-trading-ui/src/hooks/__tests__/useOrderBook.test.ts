import { renderHook, waitFor } from '@testing-library/react';
import { useOrderBook } from '../useOrderBook';

// Mock fetch
global.fetch = jest.fn();

// Mock WebSocket subscription
jest.mock('@/lib/websocket', () => ({
  subscribeToOrderBookUpdates: jest.fn(() => jest.fn()), // unsubscribe function
}));

describe('useOrderBook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Set up environment variable
    process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000';
  });

  it('초기 데이터를 로드해야 함', async () => {
    const mockData = {
      stock_code: '005930',
      asks: [
        { price: 50000, quantity: 100, order_count: 0 },
        { price: 50100, quantity: 200, order_count: 0 }
      ],
      bids: [
        { price: 49900, quantity: 150, order_count: 0 },
        { price: 49800, quantity: 250, order_count: 0 }
      ],
      timestamp: new Date().toISOString()
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockData
    });

    const { result } = renderHook(() =>
      useOrderBook({ stockCode: '005930', autoSubscribe: false })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.orderBook).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it('에러를 처리해야 함', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(
      new Error('Network error')
    );

    const { result } = renderHook(() =>
      useOrderBook({ stockCode: '005930', autoSubscribe: false })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.orderBook).toBeNull();
  });

  it('자동 구독이 활성화되어야 함', async () => {
    const mockData = {
      stock_code: '005930',
      asks: [],
      bids: [],
      timestamp: new Date().toISOString()
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });

    const { result } = renderHook(() =>
      useOrderBook({ stockCode: '005930', autoSubscribe: true })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // 구독 요청이 호출되었는지 확인
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/realtime/subscribe/orderbook?stock_code=005930',
      { method: 'POST' }
    );
  });

  it('수동 구독/해제가 작동해야 함', async () => {
    const mockData = {
      stock_code: '005930',
      asks: [],
      bids: [],
      timestamp: new Date().toISOString()
    };

    (global.fetch as jest.Mock)
      .mockResolvedValue({
        ok: true,
        json: async () => ({ success: true })
      });

    const { result } = renderHook(() =>
      useOrderBook({ stockCode: '005930', autoSubscribe: false })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // 수동 구독
    await result.current.subscribe();

    // 수동 해제
    await result.current.unsubscribe();

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/realtime/subscribe/orderbook?stock_code=005930',
      { method: 'POST' }
    );
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/realtime/unsubscribe/orderbook?stock_code=005930',
      { method: 'POST' }
    );
  });

  it('새로고침 기능이 작동해야 함', async () => {
    const mockData = {
      stock_code: '005930',
      asks: [],
      bids: [],
      timestamp: new Date().toISOString()
    };

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockData
    });

    const { result } = renderHook(() =>
      useOrderBook({ stockCode: '005930', autoSubscribe: false })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // 새로고침 호출
    await result.current.refresh();

    // fetch가 두 번 호출되었는지 확인 (초기 로드 + 새로고침)
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('구독 실패 시 에러를 처리해야 함', async () => {
    const mockData = {
      stock_code: '005930',
      asks: [],
      bids: [],
      timestamp: new Date().toISOString()
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockData
      })
      .mockRejectedValueOnce(new Error('Subscription failed'));

    const { result } = renderHook(() =>
      useOrderBook({ stockCode: '005930', autoSubscribe: true })
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
  });

  it('컴포넌트 언마운트 시 구독 해제가 호출되어야 함', async () => {
    const mockUnsubscribe = jest.fn();

    const { subscribeToOrderBookUpdates } = require('@/lib/websocket');
    subscribeToOrderBookUpdates.mockReturnValue(mockUnsubscribe);

    const { unmount } = renderHook(() =>
      useOrderBook({ stockCode: '005930', autoSubscribe: true })
    );

    unmount();

    // WebSocket 구독 해제 함수가 호출되었는지 확인
    expect(mockUnsubscribe).toHaveBeenCalled();
  });
});
