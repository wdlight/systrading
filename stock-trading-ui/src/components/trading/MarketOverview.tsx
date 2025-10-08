'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMarketData } from '@/hooks/useMarketData';
import { cn, formatCurrency, formatNumber, formatPercentage } from '@/lib/utils';
import { Globe, TrendingUp, TrendingDown } from 'lucide-react';

interface MarketOverviewProps {
  className?: string;
}

export function MarketOverview({ className }: MarketOverviewProps) {
  const { marketOverview, isLoading, error } = useMarketData();

  if (isLoading) {
    return <Card className={cn(className, "bg-[#2a2a2a] border-gray-700")}><CardHeader><CardTitle>Loading Market Data...</CardTitle></CardHeader><CardContent><div className="animate-pulse h-40 bg-gray-700/50 rounded-lg" /></CardContent></Card>;
  }

  if (error || !marketOverview) {
    return <Card className={cn(className, "bg-[#2a2a2a] border-gray-700")}><CardHeader><CardTitle>Market Overview</CardTitle></CardHeader><CardContent><div className="text-center py-12 text-red-400">Failed to load market data: {error}</div></CardContent></Card>;
  }

  const marketData = [
    { name: 'KOSPI', value: marketOverview.kospi.current, change: marketOverview.kospi.change, changeRate: marketOverview.kospi.change_rate, trend: marketOverview.kospi.change >= 0 ? 'up' : 'down', waiting: marketOverview.kospi.current === 0 },
    { name: 'KOSDAQ', value: marketOverview.kosdaq.current, change: marketOverview.kosdaq.change, changeRate: marketOverview.kosdaq.change_rate, trend: marketOverview.kosdaq.change >= 0 ? 'up' : 'down', waiting: marketOverview.kosdaq.current === 0 },
    { name: 'USD/KRW', value: marketOverview.usd_krw.current, change: marketOverview.usd_krw.change, changeRate: marketOverview.usd_krw.change_rate, trend: marketOverview.usd_krw.change >= 0 ? 'up' : 'down', waiting: false },
  ];

  const topStocks = [
    ...(marketOverview.top_gainers || []).map(stock => ({ ...stock, trend: 'up' })),
    ...(marketOverview.top_losers || []).map(stock => ({ ...stock, trend: 'down' }))
  ];

  return (
    <Card className={`${className} bg-[#2a2a2a] border-gray-700 shadow-xl`}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center">
            <Globe className="h-4 w-4 text-blue-400" />
          </div>
          <div>
            <CardTitle className="text-lg font-bold text-white">
              Market Overview
            </CardTitle>
            <p className="text-xs text-gray-400">
              Real-time market data and trends
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wide">Major Indices</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-3">
                {marketData.map((market, index) => (
                  <div key={index} className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600 hover:border-gray-500 transition-all duration-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-gray-300 uppercase tracking-wide">{market.name}</span>
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                        market.trend === 'up' ? 'bg-profit/20' : 'bg-loss/20'
                      }`}>
                        {market.trend === 'up' ? (
                          <TrendingUp className="h-3 w-3 text-profit-foreground" />
                        ) : (
                          <TrendingDown className="h-3 w-3 text-loss-foreground" />
                        )}
                      </div>
                    </div>
                    <div className="text-lg font-bold text-white mb-1">{formatNumber(market.value, { precision: 2 })}</div>
                    <div className={`text-xs font-semibold ${
                      market.trend === 'up' ? 'text-profit-foreground' : 'text-loss-foreground'
                    }`}>
                      {market.change > 0 ? '+' : ''}{formatNumber(market.change, { precision: 2 })} ({formatPercentage(market.changeRate)})
                    </div>
                    {market.waiting && (
                      <div className="text-[11px] text-amber-400 mt-2">실시간 데이터 수신 대기 중</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wide">Top Movers</h4>
              <div className="space-y-2">
                {topStocks.map((stock, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-[#1a1a1a] rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-200">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        stock.trend === 'up' ? 'bg-profit/20' : 'bg-loss/20'
                      }`}>
                        {stock.trend === 'up' ? (
                          <TrendingUp className="h-3 w-3 text-profit-foreground" />
                        ) : (
                          <TrendingDown className="h-3 w-3 text-loss-foreground" />
                        )}
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-white">{stock.stock_name}</div>
                        <div className="text-xs text-gray-400 font-mono">{stock.stock_code}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-gray-200">{formatCurrency(stock.current_price)}</div>
                      <div className={`text-xs font-semibold ${
                        stock.trend === 'up' ? 'text-profit-foreground' : 'text-loss-foreground'
                      }`}>
                        {formatPercentage(stock.change_rate)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
