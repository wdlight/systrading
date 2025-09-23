'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, BarChart3 } from 'lucide-react';

interface PortfolioPerformanceProps {
  className?: string;
}

export function PortfolioPerformance({ className }: PortfolioPerformanceProps) {
  return (
    <Card className={`${className} bg-[#2a2a2a] border-gray-700`}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <BarChart3 className="h-5 w-5 text-green-400" />
          Portfolio Performance
        </CardTitle>
        <div className="text-sm text-gray-400">
          6개월 수익률 추이
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 차트 플레이스홀더 */}
          <div className="h-64 bg-gray-800 rounded-lg border border-gray-600 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <BarChart3 className="h-12 w-12 mx-auto mb-2 text-gray-500" />
              <p className="text-sm">Portfolio Performance Chart</p>
              <p className="text-xs text-gray-500 mt-1">차트 라이브러리 연동 예정</p>
            </div>
          </div>

          {/* 성과 지표 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-1">1개월</div>
              <div className="text-sm font-semibold text-green-400">+2.4%</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-1">3개월</div>
              <div className="text-sm font-semibold text-green-400">+7.8%</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-1">6개월</div>
              <div className="text-sm font-semibold text-green-400">+15.2%</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-400 mb-1">1년</div>
              <div className="text-sm font-semibold text-green-400">+28.6%</div>
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