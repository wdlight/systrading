'use client';

import { useOrderBook } from '@/hooks/useOrderBook';
import { Loader2, Clock } from 'lucide-react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { subscribeToMarketStatusUpdates } from '@/lib/websocket';
import { MarketStatusUpdate } from '@/lib/types';
import clsx from 'clsx';

interface OrderBookProps {
  stockCode: string;
  currentPrice?: number;
  onSelectPrice?: (price: number, side: 'ask' | 'bid') => void;
}

interface OrderLevel {
  price: number;
  quantity: number;
}

interface OrderLevelDiffResult {
  priceChanged: number[];
  quantityChanged: number[];
  rowChanged: number[];
  logs: string[];
}

function diffOrderLevels(
  previous: OrderLevel[],
  next: OrderLevel[],
  side: 'ask' | 'bid'
): OrderLevelDiffResult {
  const priceChanged: number[] = [];
  const quantityChanged: number[] = [];
  const rowChangedSet = new Set<number>();
  const logs: string[] = [];
  const levelLabel = side === 'ask' ? '매도' : '매수';

  const maxLength = Math.max(previous.length, next.length);
  for (let idx = 0; idx < maxLength; idx++) {
    const prevLevel = previous[idx];
    const nextLevel = next[idx];

    if (!prevLevel || !nextLevel) {
      continue;
    }

    if (prevLevel.price !== nextLevel.price) {
      priceChanged.push(idx);
      rowChangedSet.add(idx);
      // logs.push(
      //   `📈 호가 변경 - ${levelLabel} ${idx + 1}호가 가격: ${prevLevel.price.toLocaleString()} → ${nextLevel.price.toLocaleString()}`
      // );
    }

    if (prevLevel.quantity !== nextLevel.quantity) {
      quantityChanged.push(idx);
      rowChangedSet.add(idx);
      // logs.push(
      //   `📊 호가 변경 - ${levelLabel} ${idx + 1}호가 수량: ${prevLevel.quantity.toLocaleString()} → ${nextLevel.quantity.toLocaleString()}`
      // );
    }
  }

  return {
    priceChanged,
    quantityChanged,
    rowChanged: Array.from(rowChangedSet.values()),
    logs,
  };
}

export function OrderBook({ stockCode, currentPrice, onSelectPrice }: OrderBookProps) {
  // 🔥 최상단 로그 - 컴포넌트가 렌더링되는지 확인
  // console.log(`🔄 [${new Date().toLocaleTimeString()}] OrderBook 컴포넌트 렌더 시작 - stockCode: ${stockCode}`);

  // ✅ 모든 Hook을 컴포넌트 최상단에 선언 (조건문보다 위에)
  const { orderBook, isLoading, error } = useOrderBook({
    stockCode,
    autoSubscribe: true,
  });

  // 🔥 Hook 직후 로그 - orderBook 상태 확인
  // console.log(`📦 orderBook 상태:`, {
  //   exists: !!orderBook,
  //   timestamp: orderBook?.timestamp,
  //   asksCount: orderBook?.asks?.length,
  //   bidsCount: orderBook?.bids?.length,
  //   ask1Price: orderBook?.asks?.[0]?.price,
  //   bid1Price: orderBook?.bids?.[0]?.price,
  // });

  const [highlightedKeys, setHighlightedKeys] = useState<Record<string, boolean>>({});
  const [marketStatus, setMarketStatus] = useState<MarketStatusUpdate['data'] | null>(null);

  const previousAsksRef = useRef<OrderLevel[]>([]);
  const previousBidsRef = useRef<OrderLevel[]>([]);
  const highlightTimeouts = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  // ✅ useCallback을 조건문보다 위에 선언
  const clearHighlight = useCallback((key: string) => {
    setHighlightedKeys((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
    if (highlightTimeouts.current[key]) {
      clearTimeout(highlightTimeouts.current[key]);
      delete highlightTimeouts.current[key];
    }
  }, []);

  const triggerHighlight = useCallback(
    (key: string) => {
      setHighlightedKeys((prev) => ({ ...prev, [key]: true }));
      if (highlightTimeouts.current[key]) {
        clearTimeout(highlightTimeouts.current[key]);
      }
      // ✅ 하이라이트 지속 시간 증가: 120ms → 500ms (더 잘 보이도록)
      highlightTimeouts.current[key] = setTimeout(() => {
        clearHighlight(key);
      }, 500);
    },
    [clearHighlight]
  );

  const isMarketOpen = () => {
    const now = new Date();
    const hour = now.getHours();
    const minute = now.getMinutes();
    const time = hour * 60 + minute;

    const marketOpen = 9 * 60;
    const marketClose = 15 * 60 + 30;

    return time >= marketOpen && time <= marketClose;
  };

  // ✅ useEffect도 모두 컴포넌트 최상단 (조건문보다 위)
  useEffect(() => {
    const unsubscribe = subscribeToMarketStatusUpdates((data) => {
      setMarketStatus(data);
    });

    if (!marketStatus) {
      const isOpen = isMarketOpen();
      setMarketStatus({
        status: isOpen ? 'open' : 'closed',
        session: isOpen ? 'regular' : 'closed',
        message: isOpen ? '정규 장 시간입니다.' : '장 시간 외입니다. 다음 거래일 09:00에 다시 시작됩니다.',
        next_open: '',
        last_data_timestamp: '',
      });
    }

    return unsubscribe;
  }, [marketStatus]);

  // ✅ 개선: 실시간 업데이트 감지 강화 + 상세 로깅
  useEffect(() => {
    // console.log(`⚡ useEffect 실행됨 - orderBook 존재: ${!!orderBook}, timestamp: ${orderBook?.timestamp}`);

    // orderBook이 없으면 아무것도 하지 않음
    if (!orderBook?.asks || !orderBook?.bids) {
      console.log('⚠️ orderBook 데이터 없음, 스킵');
      return;
    }

    // useEffect 내부에서 직접 계산 (초기화 순서 문제 해결)
    const currentAsks = [...(orderBook.asks ?? [])]
      .filter(item => item.price > 0)
      .sort((a, b) => b.price - a.price);
    const currentBids = [...(orderBook.bids ?? [])]
      .filter(item => item.price > 0)
      .sort((a, b) => b.price - a.price);

    // console.log(`⚡ useEffect 트리거 - timestamp: ${orderBook?.timestamp}, asks: ${currentAsks.length}개, bids: ${currentBids.length}개`);

    const hadAsksBefore = previousAsksRef.current.length > 0;
    const hadBidsBefore = previousBidsRef.current.length > 0;

    // console.log(`📋 이전 상태 - asks: ${hadAsksBefore ? previousAsksRef.current.length : 0}개, bids: ${hadBidsBefore ? previousBidsRef.current.length : 0}개`);

    // 매도 호가 변경 감지
    if (hadAsksBefore && currentAsks.length > 0) {
      const diff = diffOrderLevels(previousAsksRef.current, currentAsks, 'ask');
      // console.log(`🔴 매도 호가 diff 결과 - 가격변경: ${diff.priceChanged.length}, 수량변경: ${diff.quantityChanged.length}, 행변경: ${diff.rowChanged.length}`);

      if (diff.logs.length > 0) {
        // console.log('🔴 매도 호가 변경:', diff.logs.length, '건');
        diff.logs.forEach((log) => console.log(log));
      }

      if (diff.rowChanged.length > 0) {
        // console.log(`✨ 하이라이트 트리거 - 매도 ${diff.rowChanged.length}개 행`);
        diff.priceChanged.forEach((idx) => {
          console.log(`  → ask-${idx}-price 하이라이트`);
          triggerHighlight(`ask-${idx}-price`);
        });
        diff.quantityChanged.forEach((idx) => {
          // console.log(`  → ask-${idx}-quantity 하이라이트`);
          triggerHighlight(`ask-${idx}-quantity`);
        });
        diff.rowChanged.forEach((idx) => {
          // console.log(`  → ask-${idx}-bar 하이라이트`);
          triggerHighlight(`ask-${idx}-bar`);
        });
      } else {
        // console.log('ℹ️ 매도 호가 변경 없음');
      }
    } else {
      // console.log('ℹ️ 매도 호가 첫 로드 또는 데이터 없음');
    }

    // 매수 호가 변경 감지
    if (hadBidsBefore && currentBids.length > 0) {
      const diff = diffOrderLevels(previousBidsRef.current, currentBids, 'bid');
      // console.log(`🔵 매수 호가 diff 결과 - 가격변경: ${diff.priceChanged.length}, 수량변경: ${diff.quantityChanged.length}, 행변경: ${diff.rowChanged.length}`);

      if (diff.logs.length > 0) {
        console.log('🔵 매수 호가 변경:', diff.logs.length, '건');
        diff.logs.forEach((log) => console.log(log));
      }

      if (diff.rowChanged.length > 0) {
        // console.log(`✨ 하이라이트 트리거 - 매수 ${diff.rowChanged.length}개 행`);
        diff.priceChanged.forEach((idx) => {
          // console.log(`  → bid-${idx}-price 하이라이트`);
          triggerHighlight(`bid-${idx}-price`);
        });
        diff.quantityChanged.forEach((idx) => {
          // console.log(`  → bid-${idx}-quantity 하이라이트`);
          triggerHighlight(`bid-${idx}-quantity`);
        });
        diff.rowChanged.forEach((idx) => {
          // console.log(`  → bid-${idx}-bar 하이라이트`);
          triggerHighlight(`bid-${idx}-bar`);
        });
      } else {
        // console.log('ℹ️ 매수 호가 변경 없음');
      }
    } else {
      // console.log('ℹ️ 매수 호가 첫 로드 또는 데이터 없음');
    }

    // 이전 값 업데이트
    if (currentAsks.length > 0) {
      previousAsksRef.current = currentAsks.map((item) => ({ price: item.price, quantity: item.quantity }));
      // console.log(`💾 이전 asks 업데이트 완료 - ${currentAsks.length}개`);
    }
    if (currentBids.length > 0) {
      previousBidsRef.current = currentBids.map((item) => ({ price: item.price, quantity: item.quantity }));
      // console.log(`💾 이전 bids 업데이트 완료 - ${currentBids.length}개`);
    }

    // console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  }, [orderBook, triggerHighlight]);

  useEffect(() => {
    return () => {
      Object.keys(highlightTimeouts.current).forEach((key) => {
        clearTimeout(highlightTimeouts.current[key]);
      });
      highlightTimeouts.current = {};
    };
  }, []);

  // ✅ 모든 Hook 선언 후에 조건문 처리
  if (isLoading) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
        <span className="ml-2 text-sm text-gray-400">호가 로딩 중...</span>
      </div>
    );
  }

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

  if (!orderBook || !orderBook.asks || !orderBook.bids) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <p className="text-sm text-gray-400">호가 데이터가 없습니다</p>
      </div>
    );
  }

  // ✅ 조건부 리턴 이후 - 데이터가 확실히 있을 때만 실행됨
  const asks = [...(orderBook.asks ?? [])]
    .filter(item => item.price > 0)
    .sort((a, b) => b.price - a.price);
  const bids = [...(orderBook.bids ?? [])]
    .filter(item => item.price > 0)
    .sort((a, b) => b.price - a.price);

  // console.log(`🔄 [${new Date().toLocaleTimeString()}] 호가 배열 생성 - asks: ${asks.length}개 (매도1: ${asks[0]?.price?.toLocaleString()}), bids: ${bids.length}개 (매수1: ${bids[0]?.price?.toLocaleString()})`);

  // ✅ 데이터가 있으면 시간 상관없이 표시 (시간외 거래 지원)
  const hasValidData = asks.length > 0 || bids.length > 0;
  const isMarketClosed = !hasValidData && (
    (marketStatus && marketStatus.status === 'closed') ||
    (orderBook && orderBook.market_status === 'closed') ||
    !isMarketOpen()
  );

  if (isMarketClosed) {
    return (
      <div className="w-full h-64 flex items-center justify-center">
        <div className="text-center space-y-2">
          <Clock className="w-8 h-8 text-orange-400 mx-auto" />
          <div>
            <p className="text-sm text-orange-400 font-medium">{marketStatus?.message}</p>
            <p className="text-xs text-gray-500 mt-1">실시간 호가 데이터가 제공되지 않습니다</p>
          </div>
        </div>
      </div>
    );
  }

  const quantities = [...asks, ...bids].map((row) => row.quantity || 0);
  const maxQuantity = quantities.length ? Math.max(...quantities) : 0;

  const deriveMidPrice = () => {
    const topAsk = orderBook.asks[0];
    const topBid = orderBook.bids[0];
    if (topAsk && topBid) {
      return Math.round((topAsk.price + topBid.price) / 2);
    }
    return topAsk?.price ?? topBid?.price ?? 0;
  };

  const displayPrice =
    typeof currentPrice === 'number'
      ? currentPrice
      : typeof orderBook.current_price === 'number'
      ? orderBook.current_price
      : deriveMidPrice();

  const formattedTimestamp = (() => {
    if (!orderBook.timestamp) return '--:--:--';
    const parsed = new Date(orderBook.timestamp);
    if (Number.isNaN(parsed.getTime())) return '--:--:--';
    return parsed.toLocaleTimeString('ko-KR', { hour12: false });
  })();

  return (
    <div className="w-full">
      <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
        <div className="flex items-center w-full text-sm text-white font-semibold">
          <span className="text-green-400 text-[9px]">호가창</span>
          <span className="flex-1 text-center text-[11px] text-gray-400">
            [{formattedTimestamp}]
            {!isMarketOpen() && hasValidData && (
              <span className="ml-2 text-orange-400 text-[9px]">⏰ 시간외</span>
            )}
          </span>
          <span className="text-green-400 text-[9px]">실시간</span>
        </div>
      </div>

      <div className="grid grid-cols-2 text-[10px] text-gray-400 pb-1 border-b border-gray-700">
        <div className="text-right">가격</div>
        <div className="text-right">수량</div>
      </div>

      <div className="space-y-0.5 py-1">
        {asks.map((ask, idx) => {
          const widthPercent = maxQuantity > 0 ? (ask.quantity / maxQuantity) * 100 : 0;
          const priceKey = `ask-${idx}-price`;
          const quantityKey = `ask-${idx}-quantity`;
          const barKey = `ask-${idx}-bar`;

          return (
            <button
              key={`ask-${idx}`}
              type="button"
              onClick={() => onSelectPrice?.(ask.price, 'ask')}
              className="relative w-full text-left focus:outline-none"
            >
              <div
                className={clsx(
                  'absolute right-0 top-0 h-full bg-red-900/20 transition-colors duration-150',
                  highlightedKeys[barKey] && 'bg-red-400/30'
                )}
                style={{ width: `${widthPercent}%` }}
              />
              <div className="relative grid grid-cols-2 text-[11px] py-0.5 gap-1">
                <div
                  className={clsx(
                    'relative z-10 text-right text-red-400 font-medium px-1 rounded-sm transition-colors duration-150',
                    highlightedKeys[priceKey] && 'bg-red-500/40'
                  )}
                >
                  {ask.price.toLocaleString()}
                </div>
                <div
                  className={clsx(
                    'relative z-10 text-right text-gray-300 px-1 rounded-sm transition-colors duration-150',
                    highlightedKeys[quantityKey] && 'bg-red-500/25'
                  )}
                >
                  {ask.quantity.toLocaleString()}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      <div className="py-1 border-y border-gray-600 my-1">
        <div className="text-center text-sm font-bold text-white">
          {displayPrice.toLocaleString()}
        </div>
      </div>

      <div className="space-y-0.5 py-1">
        {bids.map((bid, idx) => {
          const widthPercent = maxQuantity > 0 ? (bid.quantity / maxQuantity) * 100 : 0;
          const priceKey = `bid-${idx}-price`;
          const quantityKey = `bid-${idx}-quantity`;
          const barKey = `bid-${idx}-bar`;

          return (
            <button
              key={`bid-${idx}`}
              type="button"
              onClick={() => onSelectPrice?.(bid.price, 'bid')}
              className="relative w-full text-left focus:outline-none"
            >
              <div
                className={clsx(
                  'absolute right-0 top-0 h-full bg-blue-900/20 transition-colors duration-150',
                  highlightedKeys[barKey] && 'bg-blue-400/30'
                )}
                style={{ width: `${widthPercent}%` }}
              />
              <div className="relative grid grid-cols-2 text-[11px] py-0.5 gap-1">
                <div
                  className={clsx(
                    'relative z-10 text-right text-blue-400 font-medium px-1 rounded-sm transition-colors.duration-150',
                    highlightedKeys[priceKey] && 'bg-blue-500/40'
                  )}
                >
                  {bid.price.toLocaleString()}
                </div>
                <div
                  className={clsx(
                    'relative z-10 text-right text-gray-300 px-1 rounded-sm transition-colors.duration-150',
                    highlightedKeys[quantityKey] && 'bg-blue-500/25'
                  )}
                >
                  {bid.quantity.toLocaleString()}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
