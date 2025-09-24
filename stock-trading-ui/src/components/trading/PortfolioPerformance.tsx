'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, BarChart3 } from 'lucide-react';

interface PortfolioPerformanceProps {
  className?: string;
}

export function PortfolioPerformance({ className }: PortfolioPerformanceProps) {
  return (
    <Card className={`${className} bg-[#2a2a2a] border-gray-700 shadow-xl`}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-green-500/20 rounded-lg flex items-center justify-center">
            <BarChart3 className="h-4 w-4 text-green-400" />
          </div>
          <div>
            <CardTitle className="text-lg font-bold text-white">
              Performance Analytics
            </CardTitle>
            <p className="text-xs text-gray-400">
              Portfolio returns over time periods
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Professional Chart Placeholder */}
          <div className="h-48 lg:h-64 bg-gradient-to-br from-[#1a1a1a] to-[#2a2a2a] rounded-lg border border-gray-600 flex items-center justify-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-green-500/5 to-blue-500/5" />
            <div className="text-center text-gray-400 relative z-10">
              <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="h-8 w-8 text-green-400" />
              </div>
              <h4 className="text-sm font-semibold text-white mb-2">Interactive Chart</h4>
              <p className="text-xs text-gray-500">Chart library integration coming soon</p>
            </div>
          </div>

          {/* Professional Performance Metrics */}
          <div className="grid grid-cols-2 gap-2 lg:gap-4">
            <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600 text-center">
              <div className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2">1M Return</div>
              <div className="text-lg font-bold text-green-400">+2.4%</div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600 text-center">
              <div className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2">3M Return</div>
              <div className="text-lg font-bold text-green-400">+7.8%</div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600 text-center">
              <div className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2">6M Return</div>
              <div className="text-lg font-bold text-green-400">+15.2%</div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600 text-center">
              <div className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-2">1Y Return</div>
              <div className="text-lg font-bold text-green-400">+28.6%</div>
            </div>
          </div>

          {/* 최근 거래 */}
          <div className="border-t border-gray-600 pt-4">
            <h4 className="text-sm font-medium text-white mb-3">최근 거래</h4>
            <div className="space-y-2">
              {[
                { stock: 'AAPL', action: '매수', amount: '+10주', time: '09:30' },
                { stock: 'TSLA', action: '매도', amount: '-5주', time: '09:25' },
                { stock: 'MSFT', action: '매수', amount: '+15주', time: '09:20' },
              ].map((trade, index) => (
                <div key={index} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-3 w-3 text-blue-400" />
                    <span className="text-white">{trade.stock}</span>
                    <span className={trade.action === '매수' ? 'text-green-400' : 'text-red-400'}>
                      {trade.action}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-300">{trade.amount}</span>
                    <span className="text-gray-400">{trade.time}</span>
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