'use client';

import { useOrderBook } from '@/hooks/useOrderBook';
import { Loader2, Clock, AlertTriangle } from 'lucide-react';
import { useState, useEffect } from 'react';
import { subscribeToMarketStatusUpdates } from '@/lib/websocket';
import { MarketStatusUpdate } from '@/lib/types';

interface OrderBookProps {
  stockCode: string;
  currentPrice?: number;
}

export function OrderBook({ stockCode, currentPrice }: OrderBookProps) {
  const { orderBook, isLoading, error } = useOrderBook({
    stockCode,
    autoSubscribe: true
  });

  const [marketStatus, setMarketStatus] = useState<MarketStatusUpdate['data'] | null>(null);

  // 장 시간 체크 함수
  const isMarketOpen = () => {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const time = hour * 60 + minute;

    // 한국 주식시장 시간: 09:00-15:30 (KST)
    const marketOpen = 9 * 60; // 09:00
    const marketClose = 15 * 60 + 30; // 15:30

    return time >= marketOpen && time <= marketClose;
  };

  useEffect(() => {
    const unsubscribe = subscribeToMarketStatusUpdates((data) => {
      setMarketStatus(data);
    });

    // 장 시간 외 상태 설정 (WebSocket 메시지가 없을 때)
    if (!marketStatus) {
      const isOpen = isMarketOpen();
      setMarketStatus({
        status: isOpen ? 'open' : 'closed',
        session: isOpen ? 'regular' : 'closed',
        message: isOpen ? '정규 장 시간입니다.' : '장 시간 외입니다. 다음 거래일 09:00에 다시 시작됩니다.',
        next_open: null,
        last_data_timestamp: null
      });
    }

    return unsubscribe;
  }, [marketStatus]);

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        <span className="ml-2 text-sm text-gray-400">호가 로딩 중...</span>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm text-red-400">{error}</p>
          <p className="text-xs text-gray-500 mt-2">호가 데이터를 불러올 수 없습니다</p>
        </div>
      </div>
    );
  }

  // 장 시간 외 상태 표시 (API 응답 또는 프론트엔드 체크)
  const isMarketClosed = (marketStatus && marketStatus.status === 'closed') ||
    (orderBook && orderBook.market_status === 'closed') ||
    !isMarketOpen();

  if (isMarketClosed) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <div className="text-center space-y-2">
          <Clock className="w-8 h-8 text-orange-400 mx-auto" />
          <div>
            <p className="text-sm text-orange-400 font-medium">{marketStatus.message}</p>
            <p className="text-xs text-gray-500 mt-1">실시간 호가 데이터가 제공되지 않습니다</p>
          </div>
        </div>
      </div>
    );
  }

  // 데이터 없음
  if (!orderBook || !orderBook.asks || !orderBook.bids) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <p className="text-sm text-gray-400">호가 데이터가 없습니다</p>
      </div>
    );
  }

  const asks = orderBook.asks.slice(0, 5).reverse(); // 상위 5개, 역순
  const bids = orderBook.bids.slice(0, 5); // 상위 5개

  const maxQuantity = Math.max(
    ...asks.map(a => a.quantity),
    ...bids.map(b => b.quantity)
  );

  // 현재가는 orderBook에서 계산 (매도1호가와 매수1호가의 중간)
  const displayPrice = currentPrice ||
    (orderBook.asks[0]?.price + orderBook.bids[0]?.price) / 2 || 0;

  return (
    <div className="w-full">
      {/* Header */}
      <div className="grid grid-cols-3 text-[10px] text-gray-400 pb-1 border-b border-gray-700">
        <div className="text-right">가격</div>
        <div className="text-right">수량</div>
        <div className="text-right">건수</div>
      </div>

      {/* Sell Orders (Red) */}
      <div className="space-y-0.5 py-1">
        {asks.map((ask, idx) => {
          const widthPercent = maxQuantity > 0 ? (ask.quantity / maxQuantity) * 100 : 0;
          return (
            <div key={`ask-${idx}`} className="relative">
              <div
                className="absolute right-0 top-0 h-full bg-red-900/20"
                style={{ width: `${widthPercent}%` }}
              />
              <div className="relative grid grid-cols-3 text-[11px] py-0.5">
                <div className="text-right text-red-400 font-medium">
                  {ask.price.toLocaleString()}
                </div>
                <div className="text-right text-gray-300">
                  {ask.quantity.toLocaleString()}
                </div>
                <div className="text-right text-gray-500 text-[10px]">
                  {ask.order_count || '-'}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Current Price Separator */}
      <div className="py-1 border-y border-gray-600 my-1">
        <div className="text-center text-sm font-bold text-white">
          {displayPrice.toLocaleString()}
        </div>
      </div>

      {/* Buy Orders (Blue) */}
      <div className="space-y-0.5 py-1">
        {bids.map((bid, idx) => {
          const widthPercent = maxQuantity > 0 ? (bid.quantity / maxQuantity) * 100 : 0;
          return (
            <div key={`bid-${idx}`} className="relative">
              <div
                className="absolute right-0 top-0 h-full bg-blue-900/20"
                style={{ width: `${widthPercent}%` }}
              />
              <div className="relative grid grid-cols-3 text-[11px] py-0.5">
                <div className="text-right text-blue-400 font-medium">
                  {bid.price.toLocaleString()}
                </div>
                <div className="text-right text-gray-300">
                  {bid.quantity.toLocaleString()}
                </div>
                <div className="text-right text-gray-500 text-[10px]">
                  {bid.order_count || '-'}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}