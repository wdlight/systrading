import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { OrderBook } from '../OrderBook';

// Mock useOrderBook hook
jest.mock('@/hooks/useOrderBook', () => ({
  useOrderBook: jest.fn(),
}));

describe('OrderBook', () => {
  const mockUseOrderBook = require('@/hooks/useOrderBook').useOrderBook;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('로딩 상태를 올바르게 표시해야 함', () => {
    mockUseOrderBook.mockReturnValue({
      orderBook: null,
      isLoading: true,
      error: null,
    });

    render(<OrderBook stockCode="005930" currentPrice={50000} />);

    expect(screen.getByText('호가 로딩 중...')).toBeInTheDocument();
  });

  it('에러 상태를 올바르게 표시해야 함', () => {
    mockUseOrderBook.mockReturnValue({
      orderBook: null,
      isLoading: false,
      error: 'Network error',
    });

    render(<OrderBook stockCode="005930" currentPrice={50000} />);

    expect(screen.getByText('Network error')).toBeInTheDocument();
    expect(screen.getByText('호가 데이터를 불러올 수 없습니다')).toBeInTheDocument();
  });

  it('데이터가 없을 때 올바른 메시지를 표시해야 함', () => {
    mockUseOrderBook.mockReturnValue({
      orderBook: null,
      isLoading: false,
      error: null,
    });

    render(<OrderBook stockCode="005930" currentPrice={50000} />);

    expect(screen.getByText('호가 데이터가 없습니다')).toBeInTheDocument();
  });

  it('호가 데이터를 올바르게 렌더링해야 함', () => {
    const mockOrderBook = {
      stock_code: '005930',
      asks: [
        { price: 50000, quantity: 100, order_count: 0 },
        { price: 50100, quantity: 200, order_count: 0 },
        { price: 50200, quantity: 300, order_count: 0 },
        { price: 50300, quantity: 400, order_count: 0 },
        { price: 50400, quantity: 500, order_count: 0 },
      ],
      bids: [
        { price: 49900, quantity: 150, order_count: 0 },
        { price: 49800, quantity: 250, order_count: 0 },
        { price: 49700, quantity: 350, order_count: 0 },
        { price: 49600, quantity: 450, order_count: 0 },
        { price: 49500, quantity: 550, order_count: 0 },
      ],
      timestamp: new Date().toISOString(),
    };

    mockUseOrderBook.mockReturnValue({
      orderBook: mockOrderBook,
      isLoading: false,
      error: null,
    });

    render(<OrderBook stockCode="005930" currentPrice={50000} />);

    // 헤더 확인
    expect(screen.getByText('가격')).toBeInTheDocument();
    expect(screen.getByText('수량')).toBeInTheDocument();
    expect(screen.getByText('건수')).toBeInTheDocument();

    // 매도호가 확인 (역순으로 표시되므로 50400부터)
    expect(screen.getByText('50,400')).toBeInTheDocument();
    expect(screen.getByText('500')).toBeInTheDocument();

    // 매수호가 확인
    expect(screen.getByText('49,900')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();

    // 현재가 확인 (매도1호가와 매수1호가의 중간값)
    expect(screen.getByText('49,950')).toBeInTheDocument();
  });

  it('props로 전달된 현재가를 우선 사용해야 함', () => {
    const mockOrderBook = {
      stock_code: '005930',
      asks: [{ price: 50000, quantity: 100, order_count: 0 }],
      bids: [{ price: 49900, quantity: 150, order_count: 0 }],
      timestamp: new Date().toISOString(),
    };

    mockUseOrderBook.mockReturnValue({
      orderBook: mockOrderBook,
      isLoading: false,
      error: null,
    });

    render(<OrderBook stockCode="005930" currentPrice={51000} />);

    // props로 전달된 현재가가 표시되어야 함
    expect(screen.getByText('51,000')).toBeInTheDocument();
  });

  it('호가 데이터가 5개 미만일 때도 올바르게 렌더링해야 함', () => {
    const mockOrderBook = {
      stock_code: '005930',
      asks: [
        { price: 50000, quantity: 100, order_count: 0 },
        { price: 50100, quantity: 200, order_count: 0 },
      ],
      bids: [
        { price: 49900, quantity: 150, order_count: 0 },
      ],
      timestamp: new Date().toISOString(),
    };

    mockUseOrderBook.mockReturnValue({
      orderBook: mockOrderBook,
      isLoading: false,
      error: null,
    });

    render(<OrderBook stockCode="005930" />);

    // 사용 가능한 데이터만 표시되어야 함
    expect(screen.getByText('50,100')).toBeInTheDocument();
    expect(screen.getByText('50,000')).toBeInTheDocument();
    expect(screen.getByText('49,900')).toBeInTheDocument();
  });

  it('빈 수량 데이터를 안전하게 처리해야 함', () => {
    const mockOrderBook = {
      stock_code: '005930',
      asks: [
        { price: 50000, quantity: 0, order_count: 0 },
        { price: 50100, quantity: 100, order_count: 0 },
      ],
      bids: [
        { price: 49900, quantity: 0, order_count: 0 },
        { price: 49800, quantity: 200, order_count: 0 },
      ],
      timestamp: new Date().toISOString(),
    };

    mockUseOrderBook.mockReturnValue({
      orderBook: mockOrderBook,
      isLoading: false,
      error: null,
    });

    render(<OrderBook stockCode="005930" />);

    // 빈 수량도 표시되어야 함
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('200')).toBeInTheDocument();
  });

  it('useOrderBook 훅을 올바른 파라미터로 호출해야 함', () => {
    mockUseOrderBook.mockReturnValue({
      orderBook: null,
      isLoading: false,
      error: null,
    });

    render(<OrderBook stockCode="005930" currentPrice={50000} />);

    expect(mockUseOrderBook).toHaveBeenCalledWith({
      stockCode: '005930',
      autoSubscribe: true,
    });
  });
});
