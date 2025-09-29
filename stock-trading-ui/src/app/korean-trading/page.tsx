'use client';

import { useState, useEffect } from 'react';
import { KoreanTradingHeader } from '@/components/layout/KoreanTradingHeader';
import { KoreanStockWatchlist } from '@/components/trading/KoreanStockWatchlist';
import { KoreanTradingChart } from '@/components/trading/KoreanTradingChart';
import { KoreanOrderBook } from '@/components/trading/KoreanOrderBook';
import { KoreanTradingForm } from '@/components/trading/KoreanTradingForm';
import { ResponsiveTradingLayout, DenseInfoCard, CompactDataRow } from '@/components/layout/ResponsiveTradingLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  Globe,
  BarChart3,
  Maximize2,
  Minimize2,
  PanelLeft,
  PanelRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  KoreanStock,
  KoreanTradingOrder,
  POPULAR_KOREAN_STOCKS,
  formatStockPrice,
  formatKoreanWon,
  getMarketStatus
} from '@/lib/types/korean-stocks';

export default function KoreanTradingPage() {
  const [selectedStock, setSelectedStock] = useState<KoreanStock | null>(POPULAR_KOREAN_STOCKS[0]);
  const [orders, setOrders] = useState<KoreanTradingOrder[]>([]);
  const [currentTime, setCurrentTime] = useState<Date | null>(null);

  // Update current time every second, only on the client
  useEffect(() => {
    setCurrentTime(new Date()); // Set initial time on mount
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleStockSelect = (stock: KoreanStock) => {
    setSelectedStock(stock);
  };

  const handleOrder = (order: Partial<KoreanTradingOrder>) => {
    const fullOrder: KoreanTradingOrder = {
      orderNumber: `ORD${Date.now()}`,
      stockCode: order.stockCode!,
      stockName: order.stockName!,
      orderType: order.orderType!,
      orderSide: order.orderSide!,
      quantity: order.quantity!,
      price: order.price!,
      filledQuantity: 0,
      remainingQuantity: order.quantity!,
      orderStatus: '접수',
      orderTime: order.orderTime!,
      commission: 0,
      tax: 0,
      netAmount: 0
    };

    setOrders(prev => [fullOrder, ...prev]);
  };

  // Mock market data
  const marketData = {
    kospi: {
      value: 2485.67,
      change: 15.32,
      changeRate: 0.62,
      isUp: true
    },
    kosdaq: {
      value: 745.23,
      change: -3.45,
      changeRate: -0.46,
      isUp: false
    },
    usdKrw: {
      value: 1328.50,
      change: 2.30,
      changeRate: 0.17,
      isUp: true
    }
  };

  const marketStatus = getMarketStatus();
  const timeDisplay = currentTime ? currentTime.toLocaleTimeString('ko-KR', { hour12: false }) : '--:--:--';

  return (
    <div className="min-h-screen bg-[#0a0a0b]">
      {/* Professional Korean Trading Header */}
      <KoreanTradingHeader />

      {/* Market Status Bar */}
      <div className="bg-[#1a1a1b] border-b border-gray-700 px-4 md:px-6 py-2">
        <div className="flex items-center justify-between max-w-[1600px] mx-auto">
          {/* Market Indices */}
          <div className="flex items-center gap-6 overflow-x-auto">
            <div className="flex items-center gap-3">
              <span className="text-gray-400 text-sm">KOSPI</span>
              <span className="text-white font-medium">
                {marketData.kospi.value.toLocaleString()}
              </span>
              <span className={cn(
                'text-sm font-medium flex items-center gap-1',
                marketData.kospi.isUp ? 'text-red-400' : 'text-blue-400'
              )}>
                {marketData.kospi.isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {marketData.kospi.change > 0 ? '+' : ''}{marketData.kospi.change} ({marketData.kospi.changeRate > 0 ? '+' : ''}{marketData.kospi.changeRate}%)
              </span>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-gray-400 text-sm">KOSDAQ</span>
              <span className="text-white font-medium">
                {marketData.kosdaq.value.toLocaleString()}
              </span>
              <span className={cn(
                'text-sm font-medium flex items-center gap-1',
                marketData.kosdaq.isUp ? 'text-red-400' : 'text-blue-400'
              )}>
                {marketData.kosdaq.isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {marketData.kosdaq.change > 0 ? '+' : ''}{marketData.kosdaq.change} ({marketData.kosdaq.changeRate > 0 ? '+' : ''}{marketData.kosdaq.changeRate}%)
              </span>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-gray-400 text-sm">USD/KRW</span>
              <span className="text-white font-medium">
                {marketData.usdKrw.value.toLocaleString()}
              </span>
              <span className={cn(
                'text-sm font-medium flex items-center gap-1',
                marketData.usdKrw.isUp ? 'text-red-400' : 'text-blue-400'
              )}>
                {marketData.usdKrw.isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {marketData.usdKrw.change > 0 ? '+' : ''}{marketData.usdKrw.change} ({marketData.usdKrw.changeRate > 0 ? '+' : ''}{marketData.usdKrw.changeRate}%)
              </span>
            </div>
          </div>

          {/* Market Status and Time */}
          <div className="flex items-center gap-4">
            <Badge className={cn(
              'text-xs',
              marketStatus === 'OPEN' ? 'bg-green-500' :
              marketStatus === 'PRE_MARKET' ? 'bg-yellow-500' :
              marketStatus === 'AFTER_HOURS' ? 'bg-orange-500' :
              'bg-gray-500'
            )}>
              <Activity className="w-3 h-3 mr-1" />
              {marketStatus === 'OPEN' ? '장중' :
               marketStatus === 'PRE_MARKET' ? '장전' :
               marketStatus === 'AFTER_HOURS' ? '장후' :
               '장마감'}
            </Badge>
            <span className="text-gray-400 text-sm">
              KST {timeDisplay}
            </span>
          </div>
        </div>
      </div>

      {/* Main Trading Layout - Responsive 3-Panel Design */}
      <div className="h-[calc(100vh-140px)]">
        <ResponsiveTradingLayout
          leftPanelTitle="관심종목"
          rightPanelTitle="거래하기"
          leftPanel={
            <KoreanStockWatchlist
              onStockSelect={handleStockSelect}
              selectedStock={selectedStock}
              className="h-full border-0 rounded-none"
            />
          }
          centerPanel={
            <div className="flex flex-col h-full">
              {/* Chart Section */}
              <div className="flex-1 p-4">
                <KoreanTradingChart
                  stock={selectedStock}
                  height={500}
                  showIndicators={true}
                  className="h-full"
                />
              </div>

              {/* Recent Orders - Optimized for Information Density */}
              <div className="h-48 border-t border-gray-700 p-4">
                <DenseInfoCard
                  title="최근 주문 내역"
                  compact={true}
                  className="h-full"
                >
                  <div className="space-y-1 overflow-y-auto max-h-32">
                    {orders.length === 0 ? (
                      <div className="text-center text-gray-400 py-4">
                        <p className="text-xs">주문 내역이 없습니다</p>
                      </div>
                    ) : (
                      orders.slice(0, 6).map((order) => (
                        <div
                          key={order.orderNumber}
                          className="flex items-center justify-between p-1.5 bg-[#2a2a2a] rounded text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <Badge className={cn(
                              'text-xs px-1.5 py-0.5',
                              order.orderSide === '매수' ? 'bg-red-500' : 'bg-blue-500'
                            )}>
                              {order.orderSide}
                            </Badge>
                            <span className="text-white font-medium">
                              {order.stockName}
                            </span>
                            <span className="text-gray-400">
                              {order.quantity.toLocaleString()}주
                            </span>
                          </div>
                          <div className="text-right">
                            <div className="text-white">
                              {formatStockPrice(order.price)}
                            </div>
                            <div className="text-gray-400 text-xs">
                              {new Date(order.orderTime).toLocaleTimeString('ko-KR', {
                                hour: '2-digit',
                                minute: '2-digit',
                                hour12: false
                              })}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </DenseInfoCard>
              </div>
            </div>
          }
          rightPanel={
            <div className="flex flex-col h-full">
              {/* Order Book - Top Half */}
              <div className="flex-1 min-h-0">
                <KoreanOrderBook
                  stock={selectedStock}
                  className="h-full border-0 rounded-none"
                />
              </div>

              {/* Trading Form - Bottom Half */}
              <div className="flex-1 border-t border-gray-700">
                <KoreanTradingForm
                  stock={selectedStock}
                  onOrder={handleOrder}
                  className="h-full border-0 rounded-none"
                />
              </div>
            </div>
          }
        />
      </div>

      {/* Development Status */}
      {process.env.NODE_ENV === 'development' && (
        <div className="fixed bottom-4 right-4 bg-[#2a2a2a] border border-gray-600 rounded-lg p-3 text-xs text-gray-300 max-w-sm">
          <div className="font-medium text-blue-400 mb-2">🇰🇷 Korean Trading Interface</div>
          <div className="space-y-1">
            <div>Selected: {selectedStock?.name || 'None'}</div>
            <div>Market Status: {marketStatus}</div>
            <div>Active Orders: {orders.length}</div>
            <div>Current Time: {timeDisplay}</div>
            <div>Stocks Available: {POPULAR_KOREAN_STOCKS.length}</div>
          </div>
        </div>
      )}
    </div>
  );
}