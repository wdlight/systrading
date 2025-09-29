'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Target,
  TrendingUp,
  TrendingDown,
  ArrowUpDown,
  Volume2,
  Clock,
  Users,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  KoreanStock,
  KoreanOrderBook as KoreanOrderBookType, // Renamed to avoid conflict with component name
  OrderBookEntry,
  formatStockPrice
} from '@/lib/types/korean-stocks';

interface KoreanOrderBookProps {
  className?: string;
  stock?: KoreanStock | null;
  compact?: boolean;
}

// Generate mock order book data
function generateMockOrderBook(stock: KoreanStock): KoreanOrderBookType {
  const basePrice = stock.currentPrice;
  const asks: OrderBookEntry[] = [];
  const bids: OrderBookEntry[] = [];

  // Generate ask orders (매도 호가) - above current price
  for (let i = 1; i <= 10; i++) {
    const price = basePrice + (i * 100);
    const quantity = Math.floor(Math.random() * 5000 + 500);
    const orders = Math.floor(Math.random() * 50 + 10);
    asks.push({
      price,
      quantity,
      total: price * quantity,
      ratio: Math.random() * 100,
      orders
    });
  }

  // Generate bid orders (매수 호가) - below current price
  for (let i = 1; i <= 10; i++) {
    const price = basePrice - (i * 100);
    const quantity = Math.floor(Math.random() * 5000 + 500);
    const orders = Math.floor(Math.random() * 50 + 10);
    bids.push({
      price,
      quantity,
      total: price * quantity,
      ratio: Math.random() * 100,
      orders
    });
  }

  const totalAskQuantity = asks.reduce((sum, ask) => sum + ask.quantity, 0);
  const totalBidQuantity = bids.reduce((sum, bid) => sum + bid.quantity, 0);

  return {
    stockCode: stock.code,
    stockName: stock.name,
    timestamp: new Date().toISOString(),
    asks: asks.reverse(), // Higher prices first
    bids, // Lower prices first (already in correct order)
    totalAskQuantity,
    totalBidQuantity,
    spread: asks[asks.length - 1].price - bids[0].price,
    spreadPercent: ((asks[asks.length - 1].price - bids[0].price) / basePrice) * 100,
    lastTradePrice: basePrice,
    lastTradeQuantity: Math.floor(Math.random() * 1000 + 100),
    lastTradeTime: new Date().toISOString()
  };
}

export function KoreanOrderBook({ className, stock, compact = false }: KoreanOrderBookProps) {
  const [showDepth, setShowDepth] = useState(5);
  const [viewMode, setViewMode] = useState<'combined' | 'asks' | 'bids'>('combined');

  const orderBook = useMemo(() => {
    if (!stock) return null;
    return generateMockOrderBook(stock);
  }, [stock]);

  if (!stock || !orderBook) {
    return (
      <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
        <CardContent className="flex items-center justify-center h-64">
          <div className="text-center text-gray-400">
            <Target className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>종목을 선택하여</p>
            <p>호가창을 확인하세요</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const maxQuantity = Math.max(
    ...orderBook.asks.slice(0, showDepth).map(ask => ask.quantity),
    ...orderBook.bids.slice(0, showDepth).map(bid => bid.quantity)
  );

  const formatQuantity = (quantity: number) => {
    if (quantity >= 10000) {
      return `${(quantity / 10000).toFixed(1)}만`;
    }
    return quantity.toLocaleString();
  };

  const getQuantityBarWidth = (quantity: number) => {
    return (quantity / maxQuantity) * 100;
  };

  if (compact) {
    return (
      <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white text-sm flex items-center gap-2">
              <Target className="w-4 h-4" />
              호가창
            </CardTitle>
            <Badge className="bg-green-500 text-white text-xs">
              <Zap className="w-3 h-3 mr-1" />
              실시간
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          {/* Asks (매도) - Top 3 */}
          <div className="space-y-1">
            {orderBook.asks.slice(0, 3).reverse().map((ask, index) => (
              <div key={index} className="flex items-center justify-between text-xs">
                <span className="text-blue-400 font-medium">
                  {formatStockPrice(ask.price)}
                </span>
                <span className="text-gray-300">
                  {formatQuantity(ask.quantity)}
                </span>
              </div>
            ))}
          </div>

          {/* Current Price */}
          <div className="py-2 border-y border-gray-700">
            <div className="text-center">
              <div className="text-white font-bold text-sm">
                {formatStockPrice(orderBook.lastTradePrice)}
              </div>
              <div className="text-xs text-gray-400">
                스프레드: {orderBook.spread.toLocaleString()}원
              </div>
            </div>
          </div>

          {/* Bids (매수) - Top 3 */}
          <div className="space-y-1">
            {orderBook.bids.slice(0, 3).map((bid, index) => (
              <div key={index} className="flex items-center justify-between text-xs">
                <span className="text-red-400 font-medium">
                  {formatStockPrice(bid.price)}
                </span>
                <span className="text-gray-300">
                  {formatQuantity(bid.quantity)}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-white flex items-center gap-2">
            <Target className="w-5 h-5" />
            호가창
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge className="bg-green-500 text-white text-xs">
              <Zap className="w-3 h-3 mr-1" />
              실시간
            </Badge>
          </div>
        </div>

        {/* Stock Info */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-white font-medium">{stock.name}</h3>
              <p className="text-gray-400 text-sm">{stock.code}</p>
            </div>
            <div className="text-right">
              <div className="text-white font-bold">
                {formatStockPrice(orderBook.lastTradePrice)}
              </div>
              <div className="text-xs text-gray-400">
                <Clock className="w-3 h-3 inline mr-1" />
                {new Date().toLocaleTimeString('ko-KR', { hour12: false })}
              </div>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <Button
                variant={viewMode === 'combined' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('combined')}
                className="text-xs h-7"
              >
                전체
              </Button>
              <Button
                variant={viewMode === 'asks' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('asks')}
                className="text-xs h-7"
              >
                매도
              </Button>
              <Button
                variant={viewMode === 'bids' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewMode('bids')}
                className="text-xs h-7"
              >
                매수
              </Button>
            </div>
            <div className="flex items-center gap-1">
              {[5, 10, 15].map((depth) => (
                <Button
                  key={depth}
                  variant={showDepth === depth ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setShowDepth(depth)}
                  className="text-xs h-7 w-8"
                >
                  {depth}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-1">
        {/* Header */}
        <div className="grid grid-cols-4 gap-2 px-2 py-1 text-xs text-gray-400 font-medium border-b border-gray-700">
          <div className="text-left">호가</div>
          <div className="text-right">수량</div>
          <div className="text-right">건수</div>
          <div className="text-right">비율</div>
        </div>

        {/* Asks (매도 호가) */}
        {(viewMode === 'combined' || viewMode === 'asks') && (
          <div className="space-y-px">
            {orderBook.asks.slice(0, showDepth).reverse().map((ask, index) => (
              <div
                key={`ask-${index}`}
                className="relative grid grid-cols-4 gap-2 px-2 py-1 hover:bg-blue-500/10 cursor-pointer transition-colors"
              >
                {/* Quantity Bar Background */}
                <div
                  className="absolute right-0 top-0 bottom-0 bg-blue-500/10 border-r-2 border-blue-500/30"
                  style={{ width: `${getQuantityBarWidth(ask.quantity)}%` }}
                />
                
                <div className="relative z-10 text-blue-400 font-medium text-sm">
                  {formatStockPrice(ask.price)}
                </div>
                <div className="relative z-10 text-right text-white text-sm">
                  {formatQuantity(ask.quantity)}
                </div>
                <div className="relative z-10 text-right text-gray-400 text-xs">
                  {ask.orders}
                </div>
                <div className="relative z-10 text-right text-gray-400 text-xs">
                  {ask.ratio.toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Current Price and Spread */}
        {viewMode === 'combined' && (
          <div className="py-3 border-y border-gray-700">
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2">
                <ArrowUpDown className="w-4 h-4 text-gray-400" />
                <span className="text-gray-400 text-sm">스프레드</span>
              </div>
              <div className="text-right">
                <div className="text-white font-bold">
                  {orderBook.spread.toLocaleString()}원
                </div>
                <div className="text-gray-400 text-xs">
                  {orderBook.spreadPercent.toFixed(2)}%
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Bids (매수 호가) */}
        {(viewMode === 'combined' || viewMode === 'bids') && (
          <div className="space-y-px">
            {orderBook.bids.slice(0, showDepth).map((bid, index) => (
              <div
                key={`bid-${index}`}
                className="relative grid grid-cols-4 gap-2 px-2 py-1 hover:bg-red-500/10 cursor-pointer transition-colors"
              >
                {/* Quantity Bar Background */}
                <div
                  className="absolute right-0 top-0 bottom-0 bg-red-500/10 border-r-2 border-red-500/30"
                  style={{ width: `${getQuantityBarWidth(bid.quantity)}%` }}
                />
                
                <div className="relative z-10 text-red-400 font-medium text-sm">
                  {formatStockPrice(bid.price)}
                </div>
                <div className="relative z-10 text-right text-white text-sm">
                  {formatQuantity(bid.quantity)}
                </div>
                <div className="relative z-10 text-right text-gray-400 text-xs">
                  {bid.orders}
                </div>
                <div className="relative z-10 text-right text-gray-400 text-xs">
                  {bid.ratio.toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Summary */}
        <div className="pt-3 border-t border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-400">매도 총량:</span>
                <span className="text-blue-400 font-medium">
                  {formatQuantity(orderBook.totalAskQuantity)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">매수 총량:</span>
                <span className="text-red-400 font-medium">
                  {formatQuantity(orderBook.totalBidQuantity)}
                </span>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-gray-400">최종 거래:</span>
                <span className="text-white font-medium">
                  {formatQuantity(orderBook.lastTradeQuantity)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">거래 시각:</span>
                <span className="text-gray-300">
                  {new Date(orderBook.lastTradeTime).toLocaleTimeString('ko-KR', { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false 
                  })}
                </span>
              </div>
            </div>
          </div>

          {/* Market Depth Indicator */}
          <div className="mt-3 flex items-center justify-center">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Volume2 className="w-3 h-3" />
              <span>시장 깊이:</span>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                <span>매수 {((orderBook.totalBidQuantity / (orderBook.totalBidQuantity + orderBook.totalAskQuantity)) * 100).toFixed(1)}%</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span>매도 {((orderBook.totalAskQuantity / (orderBook.totalBidQuantity + orderBook.totalAskQuantity)) * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
