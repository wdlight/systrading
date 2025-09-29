'use client';

import { useEffect } from 'react';
import { MarketTicker, useMarketTickerDemo } from '@/components/trading/MarketTicker';
import { TradingChart, useTradingChartDemo } from '@/components/trading/TradingChart';
import { OrderBook, useOrderBookDemo } from '@/components/trading/OrderBook';
import { TradingForm } from '@/components/trading/TradingForm';
import { TradingHistory } from '@/components/trading/TradingHistory';
import { useTradingStore } from '@/stores/tradingStore';
import { TradingErrorBoundary } from '@/components/common/ErrorBoundary';

export default function ExchangePage() {
  // Initialize demo data
  useMarketTickerDemo();
  useTradingChartDemo();
  useOrderBookDemo();

  // Initialize some demo portfolio data
  const updatePortfolio = useTradingStore(state => state.updatePortfolio);

  useEffect(() => {
    updatePortfolio({
      totalValue: 125430.50,
      availableCash: 25430.50,
      totalPnL: 12543.25,
      dailyPnL: 543.12,
      positions: [
        {
          symbol: 'BTCUSDT',
          quantity: 2.5,
          avgPrice: 48000,
          currentPrice: 52000,
          pnl: 10000,
          pnlPercent: 8.33,
        },
        {
          symbol: 'ETHUSDT',
          quantity: 15,
          avgPrice: 3200,
          currentPrice: 3350,
          pnl: 2250,
          pnlPercent: 4.69,
        },
      ],
    });
  }, [updatePortfolio]);

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      {/* Professional Trading Layout */}
      <div className="h-screen flex flex-col">
        {/* Top Market Ticker */}
        <div className="border-b border-gray-800">
          <TradingErrorBoundary title="Market Ticker">
            <MarketTicker compact />
          </TradingErrorBoundary>
        </div>

        {/* Main Trading Interface - Responsive */}
        <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
          {/* Left Panel - Chart */}
          <div className="flex-1 flex flex-col min-w-0 order-1">
            {/* Chart */}
            <div className="flex-1 p-2 md:p-4">
              <TradingErrorBoundary title="Trading Chart">
                <TradingChart height={400} className="md:h-[500px]" />
              </TradingErrorBoundary>
            </div>

            {/* Trading History - Hidden on mobile, shown on tablet+ */}
            <div className="hidden md:block h-80 p-4 pt-0">
              <TradingErrorBoundary title="Trading History">
                <TradingHistory maxRows={8} />
              </TradingErrorBoundary>
            </div>
          </div>

          {/* Center Panel - Order Book (Hidden on mobile, shown on lg+) */}
          <div className="hidden lg:flex w-80 border-l border-r border-gray-800 flex-col order-2">
            <div className="flex-1 p-4">
              <TradingErrorBoundary title="Order Book">
                <OrderBook className="h-full" />
              </TradingErrorBoundary>
            </div>
          </div>

          {/* Right Panel - Trading Form */}
          <div className="w-full lg:w-80 flex flex-col order-3 lg:order-3">
            <div className="flex-1 p-2 md:p-4">
              <TradingErrorBoundary title="Trading Form">
                <TradingForm />
              </TradingErrorBoundary>
            </div>
          </div>

          {/* Mobile Order Book - Shown only on mobile */}
          <div className="lg:hidden w-full border-t border-gray-800 order-4">
            <div className="h-80 p-2 md:p-4">
              <TradingErrorBoundary title="Order Book">
                <OrderBook />
              </TradingErrorBoundary>
            </div>
          </div>

          {/* Mobile Trading History - Shown only on mobile */}
          <div className="md:hidden w-full border-t border-gray-800 order-5">
            <div className="h-80 p-2">
              <TradingErrorBoundary title="Trading History">
                <TradingHistory maxRows={6} />
              </TradingErrorBoundary>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}