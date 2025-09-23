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
    <Card className={`${className} bg-[#2a2a2a] border-gray-700`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Globe className="h-5 w-5 text-blue-400" />
          Market Overview
        </CardTitle>
        <div className="text-sm text-gray-400">
          실시간 시장 현황
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {/* 주요 지수 */}
          <div>
            <h4 className="text-sm font-medium text-white mb-3">주요 지수</h4>
            <div className="grid grid-cols-2 gap-3">
              {marketData.map((market, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-3 border border-gray-600">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-300">{market.name}</span>
                    {market.trend === 'up' ? (
                      <TrendingUp className="h-3 w-3 text-green-400" />
                    ) : (
                      <TrendingDown className="h-3 w-3 text-red-400" />
                    )}
                  </div>
                  <div className="text-sm font-bold text-white">{market.value}</div>
                  <div className={`text-xs ${
                    market.trend === 'up' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {market.change} ({market.changeRate})
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 인기 종목 */}
          <div>
            <h4 className="text-sm font-medium text-white mb-3">인기 종목</h4>
            <div className="space-y-2">
              {topStocks.map((stock, index) => (
                <div key={index} className="flex items-center justify-between p-2 bg-gray-800 rounded border border-gray-600">
                  <div className="flex items-center gap-2">
                    <div className="flex-shrink-0">
                      {stock.trend === 'up' ? (
                        <TrendingUp className="h-3 w-3 text-green-400" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-red-400" />
                      )}
                    </div>
                    <div>
                      <div className="text-xs font-medium text-white">{stock.name}</div>
                      <div className="text-xs text-gray-400">{stock.symbol}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-medium text-gray-300">{stock.price}</div>
                    <div className={`text-xs ${
                      stock.trend === 'up' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {stock.change}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 시장 뉴스 */}
          <div>
            <h4 className="text-sm font-medium text-white mb-3">시장 뉴스</h4>
            <div className="space-y-2">
              {[
                { title: 'Fed 기준금리 동결 결정', time: '2시간 전' },
                { title: '삼성전자 3분기 실적 발표', time: '4시간 전' },
                { title: '원/달러 환율 급등', time: '6시간 전' },
              ].map((news, index) => (
                <div key={index} className="p-2 bg-gray-800 rounded border border-gray-600">
                  <div className="text-xs text-gray-300 leading-relaxed">{news.title}</div>
                  <div className="text-xs text-gray-500 mt-1">{news.time}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}