'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Globe, TrendingUp, TrendingDown } from 'lucide-react';

interface MarketOverviewProps {
  className?: string;
}

export function MarketOverview({ className }: MarketOverviewProps) {
  const marketData = [
    { name: 'KOSPI', value: '2,547.23', change: '+12.45', changeRate: '+0.49%', trend: 'up' },
    { name: 'KOSDAQ', value: '745.67', change: '-3.21', changeRate: '-0.43%', trend: 'down' },
    { name: 'USD/KRW', value: '1,335.50', change: '+2.30', changeRate: '+0.17%', trend: 'up' },
    { name: 'Bitcoin', value: '$43,250', change: '+1,234', changeRate: '+2.94%', trend: 'up' },
  ];

  const topStocks = [
    { symbol: '005930', name: '삼성전자', price: '71,400', change: '+1.42%', trend: 'up' },
    { symbol: '000660', name: 'SK하이닉스', price: '123,500', change: '-0.81%', trend: 'down' },
    { symbol: '035420', name: 'NAVER', price: '189,000', change: '+2.17%', trend: 'up' },
    { symbol: '005380', name: '현대차', price: '156,500', change: '+0.64%', trend: 'up' },
    { symbol: '051910', name: 'LG화학', price: '342,000', change: '-1.45%', trend: 'down' },
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
          {/* 2-Column Layout: Major Indices and Top Movers */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Major Indices */}
            <div>
              <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wide">Major Indices</h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2 gap-3">
                {marketData.map((market, index) => (
                  <div key={index} className="bg-[#1a1a1a] rounded-lg p-4 border border-gray-600 hover:border-gray-500 transition-all duration-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-gray-300 uppercase tracking-wide">{market.name}</span>
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                        market.trend === 'up' ? 'bg-green-500/20' : 'bg-red-500/20'
                      }`}>
                        {market.trend === 'up' ? (
                          <TrendingUp className="h-3 w-3 text-green-400" />
                        ) : (
                          <TrendingDown className="h-3 w-3 text-red-400" />
                        )}
                      </div>
                    </div>
                    <div className="text-lg font-bold text-white mb-1">{market.value}</div>
                    <div className={`text-xs font-semibold ${
                      market.trend === 'up' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {market.change} ({market.changeRate})
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Top Movers */}
            <div>
              <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wide">Top Movers</h4>
              <div className="space-y-2">
                {topStocks.map((stock, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-[#1a1a1a] rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-200">
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        stock.trend === 'up' ? 'bg-green-500/20' : 'bg-red-500/20'
                      }`}>
                        {stock.trend === 'up' ? (
                          <TrendingUp className="h-3 w-3 text-green-400" />
                        ) : (
                          <TrendingDown className="h-3 w-3 text-red-400" />
                        )}
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-white">{stock.name}</div>
                        <div className="text-xs text-gray-400 font-mono">{stock.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-bold text-gray-200">{stock.price}</div>
                      <div className={`text-xs font-semibold ${
                        stock.trend === 'up' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {stock.change}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Market News - Single Column Below */}
          <div className="border-t border-gray-600 pt-6">
            <h4 className="text-sm font-bold text-white mb-4 uppercase tracking-wide">Market News</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {[
                { title: 'Federal Reserve holds interest rates steady', time: '2 hours ago' },
                { title: 'Samsung Electronics Q3 earnings report', time: '4 hours ago' },
                { title: 'USD/KRW exchange rate surge', time: '6 hours ago' },
                { title: 'Tech stocks rally on AI optimism', time: '8 hours ago' },
                { title: 'Korean automotive exports increase', time: '10 hours ago' },
                { title: 'Crypto market shows volatility', time: '12 hours ago' },
              ].map((news, index) => (
                <div key={index} className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600 hover:border-gray-500 transition-all duration-200 cursor-pointer">
                  <div className="text-sm text-gray-200 leading-relaxed font-medium line-clamp-2">{news.title}</div>
                  <div className="text-xs text-gray-400 mt-2 flex items-center gap-1">
                    <div className="w-1 h-1 bg-blue-400 rounded-full" />
                    {news.time}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}