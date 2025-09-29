'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn, formatNumber } from '@/lib/utils';
import { useTradingStore, useOrderBook, useSelectedSymbol } from '@/stores/tradingStore';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

interface OrderBookProps {
  className?: string;
  maxEntries?: number;
}

export function OrderBook({ className, maxEntries = 15 }: OrderBookProps) {
  const selectedSymbol = useSelectedSymbol();
  const orderBook = useOrderBook(selectedSymbol);
  const [spreadAnimation, setSpreadAnimation] = useState(false);

  // Calculate spread and mid price
  const { spread, midPrice, spreadPercent } = useMemo(() => {
    if (!orderBook || orderBook.asks.length === 0 || orderBook.bids.length === 0) {
      return { spread: 0, midPrice: 0, spreadPercent: 0 };
    }

    const bestAsk = orderBook.asks[0].price;
    const bestBid = orderBook.bids[0].price;
    const spread = bestAsk - bestBid;
    const midPrice = (bestAsk + bestBid) / 2;
    const spreadPercent = (spread / midPrice) * 100;

    return { spread, midPrice, spreadPercent };
  }, [orderBook]);

  // Animate spread changes
  useEffect(() => {
    if (spread > 0) {
      setSpreadAnimation(true);
      const timer = setTimeout(() => setSpreadAnimation(false), 500);
      return () => clearTimeout(timer);
    }
  }, [spread]);

  // Get visible entries
  const visibleAsks = orderBook?.asks.slice(0, maxEntries).reverse() || [];
  const visibleBids = orderBook?.bids.slice(0, maxEntries) || [];

  // Calculate max quantity for bar visualization
  const maxQuantity = useMemo(() => {
    const allEntries = [...(orderBook?.asks || []), ...(orderBook?.bids || [])];
    return Math.max(...allEntries.map(entry => entry.quantity), 1);
  }, [orderBook]);

  if (!orderBook) {
    return (
      <Card className={cn("card-professional", className)}>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3 text-white">
            <div className="icon-bg-blue">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold">Order Book</div>
              <div className="text-xs text-gray-400 font-normal">{selectedSymbol}</div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <div className="w-12 h-12 bg-gray-700/50 rounded-full flex items-center justify-center mx-auto mb-3">
              <BarChart3 className="h-6 w-6 text-gray-500" />
            </div>
            <p className="text-sm text-gray-400">No order book data</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn("card-professional", className)}>
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center justify-between text-white">
          <div className="flex items-center gap-3">
            <div className="icon-bg-blue">
              <BarChart3 className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-bold">Order Book</div>
              <div className="text-xs text-gray-400 font-normal">{selectedSymbol}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400">Spread</div>
            <div className={cn(
              "text-xs font-mono transition-all duration-500",
              spreadAnimation ? "scale-110" : "scale-100",
              spreadPercent < 0.1 ? "text-green-400" :
              spreadPercent < 0.5 ? "text-yellow-400" : "text-red-400"
            )}>
              {formatNumber(spread, { decimals: 2 })} ({spreadPercent.toFixed(3)}%)
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="px-0">
        {/* Table Headers */}
        <div className="grid grid-cols-3 gap-2 px-4 pb-2 text-xs font-medium text-gray-400 border-b border-gray-700">
          <div className="text-left">Price</div>
          <div className="text-center">Quantity</div>
          <div className="text-right">Total</div>
        </div>

        <div className="space-y-0">
          {/* Sell Orders (Asks) */}
          <div className="py-2">
            {visibleAsks.map((ask, index) => (
              <OrderBookRow
                key={`ask-${ask.price}-${index}`}
                entry={ask}
                type="sell"
                maxQuantity={maxQuantity}
              />
            ))}
          </div>

          {/* Price Spread Display */}
          <div className="px-4 py-3 bg-gray-800/50 border-y border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-3 w-3 text-red-400" />
                <span className="text-xs text-gray-400">Best Ask</span>
                <span className="text-xs font-mono text-red-400">
                  {orderBook.asks[0] ? formatNumber(orderBook.asks[0].price, { decimals: 2 }) : '-'}
                </span>
              </div>
              <div className="text-xs font-bold text-white">
                {formatNumber(midPrice, { decimals: 2 })}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono text-blue-400">
                  {orderBook.bids[0] ? formatNumber(orderBook.bids[0].price, { decimals: 2 }) : '-'}
                </span>
                <span className="text-xs text-gray-400">Best Bid</span>
                <TrendingDown className="h-3 w-3 text-blue-400" />
              </div>
            </div>
          </div>

          {/* Buy Orders (Bids) */}
          <div className="py-2">
            {visibleBids.map((bid, index) => (
              <OrderBookRow
                key={`bid-${bid.price}-${index}`}
                entry={bid}
                type="buy"
                maxQuantity={maxQuantity}
              />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface OrderBookRowProps {
  entry: { price: number; quantity: number; total: number };
  type: 'buy' | 'sell';
  maxQuantity: number;
}

function OrderBookRow({ entry, type, maxQuantity }: OrderBookRowProps) {
  const [isFlashing, setIsFlashing] = useState(false);
  const quantityPercent = (entry.quantity / maxQuantity) * 100;

  // Flash animation for updates
  useEffect(() => {
    setIsFlashing(true);
    const timer = setTimeout(() => setIsFlashing(false), 200);
    return () => clearTimeout(timer);
  }, [entry.price, entry.quantity]);

  return (
    <div className={cn(
      "relative px-4 py-1 hover:bg-gray-700/30 transition-colors duration-150 cursor-pointer",
      isFlashing && "bg-white/10"
    )}>
      {/* Quantity Bar Background */}
      <div
        className={cn(
          "absolute right-0 top-0 bottom-0 transition-all duration-300",
          type === 'buy'
            ? "bg-blue-500/10 border-r-2 border-blue-500/30"
            : "bg-red-500/10 border-r-2 border-red-500/30"
        )}
        style={{ width: `${quantityPercent}%` }}
      />

      {/* Order Data */}
      <div className="relative grid grid-cols-3 gap-2 text-xs font-mono">
        <div className={cn(
          "text-left font-bold",
          type === 'buy' ? "text-blue-400" : "text-red-400"
        )}>
          {formatNumber(entry.price, { decimals: 2 })}
        </div>
        <div className="text-center text-gray-200">
          {formatNumber(entry.quantity, { compact: true })}
        </div>
        <div className="text-right text-gray-300">
          {formatNumber(entry.total, { compact: true })}
        </div>
      </div>
    </div>
  );
}

// Demo data generator for testing
export function useOrderBookDemo() {
  const updateOrderBook = useTradingStore(state => state.updateOrderBook);
  const selectedSymbol = useSelectedSymbol();

  useEffect(() => {
    const generateOrderBook = () => {
      const basePrice = 50000 + Math.random() * 10000;
      const spread = 10 + Math.random() * 50;

      const asks = Array.from({ length: 20 }, (_, i) => {
        const price = basePrice + spread/2 + i * (Math.random() * 20 + 5);
        const quantity = Math.random() * 10 + 0.1;
        return {
          price,
          quantity,
          total: price * quantity
        };
      }).sort((a, b) => a.price - b.price);

      const bids = Array.from({ length: 20 }, (_, i) => {
        const price = basePrice - spread/2 - i * (Math.random() * 20 + 5);
        const quantity = Math.random() * 10 + 0.1;
        return {
          price,
          quantity,
          total: price * quantity
        };
      }).sort((a, b) => b.price - a.price);

      updateOrderBook({
        symbol: selectedSymbol,
        bids,
        asks,
        lastUpdate: Date.now()
      });
    };

    // Initial data
    generateOrderBook();

    // Update every 2 seconds
    const interval = setInterval(generateOrderBook, 2000);
    return () => clearInterval(interval);
  }, [selectedSymbol, updateOrderBook]);
}