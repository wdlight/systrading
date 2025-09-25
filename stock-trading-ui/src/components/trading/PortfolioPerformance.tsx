'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, BarChart3 } from 'lucide-react';

interface PortfolioPerformanceProps {
  className?: string;
}

export function PortfolioPerformance({ className }: PortfolioPerformanceProps) {
  return (
    <Card className={`${className} bg-[#2a2a2a] border-gray-700 shadow-xl flex flex-col`}>
      {/* Header */}
      <CardHeader className="pb-4 flex-shrink-0">
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

      <CardContent className="flex-1">
        {/* 2-Column Layout: Chart (70%) + Stats & Trades (30%) */}
        {/* Mobile: Stacked layout, Desktop: Side-by-side layout */}
        <div className="grid grid-cols-1 lg:grid-cols-10 gap-4 h-full min-h-[400px]">

          {/* Left Column: Chart Area (70%) */}
          <div className="lg:col-span-7 flex flex-col">
            <div className="flex-1 bg-gradient-to-br from-[#1a1a1a] to-[#2a2a2a] rounded-lg border border-gray-600 flex items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-green-500/5 to-blue-500/5" />
              <div className="text-center text-gray-400 relative z-10">
                <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <TrendingUp className="h-8 w-8 text-green-400" />
                </div>
                <h4 className="text-sm font-semibold text-white mb-2">Interactive Chart</h4>
                <p className="text-xs text-gray-500">Chart library integration coming soon</p>
              </div>
            </div>
          </div>

          {/* Right Column: Return Stats + Recent Trades (30%) */}
          <div className="lg:col-span-3 flex flex-col space-y-4">

            {/* Compact Return Stats - Mobile: Horizontal, Desktop: Vertical */}
            <div className="bg-[#1a1a1a] rounded-lg border border-gray-600 p-3 flex-shrink-0">
              <h5 className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-3">Return Stats</h5>

              {/* Mobile Layout: Horizontal */}
              <div className="lg:hidden grid grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-xs text-gray-300 mb-1">일간</div>
                  <div className="text-sm font-bold text-green-400">+2.3%</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-300 mb-1">월간</div>
                  <div className="text-sm font-bold text-green-400">+15.2%</div>
                </div>
                <div className="text-center">
                  <div className="text-xs text-gray-300 mb-1">연간</div>
                  <div className="text-sm font-bold text-green-400">+24.8%</div>
                </div>
              </div>

              {/* Desktop Layout: Vertical */}
              <div className="hidden lg:block space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-300">일간</span>
                  <span className="text-sm font-bold text-green-400">+2.3%</span>
                </div>
                <div className="w-full h-px bg-gray-600"></div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-300">월간</span>
                  <span className="text-sm font-bold text-green-400">+15.2%</span>
                </div>
                <div className="w-full h-px bg-gray-600"></div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-300">연간</span>
                  <span className="text-sm font-bold text-green-400">+24.8%</span>
                </div>
              </div>
            </div>

            {/* Recent Trades Section - Scrollable */}
            <div className="flex-1 bg-[#1a1a1a] rounded-lg border border-gray-600 p-3 overflow-hidden flex flex-col">
              <h5 className="text-xs font-semibold text-gray-300 uppercase tracking-wide mb-3 flex-shrink-0">최근 거래</h5>
              <div className="flex-1 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800">
                {[
                  { stock: 'AAPL', action: '매수', amount: '+150', change: '+2.3%', time: '09:30' },
                  { stock: 'TSLA', action: '매도', amount: '-50', change: '-1.8%', time: '09:25' },
                  { stock: 'MSFT', action: '매수', amount: '+80', change: '+1.5%', time: '09:20' },
                  { stock: 'GOOGL', action: '매수', amount: '+25', change: '+1.1%', time: '09:15' },
                  { stock: 'NVDA', action: '매도', amount: '-30', change: '-0.8%', time: '09:10' },
                ].map((trade, index) => (
                  <div key={index} className="bg-[#2a2a2a]/50 rounded-lg p-2 border border-gray-700 hover:border-gray-600 transition-colors">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <TrendingUp className="h-3 w-3 text-blue-400 flex-shrink-0" />
                        <span className="text-white font-medium text-xs">{trade.stock}</span>
                        <span className={`text-xs ${trade.action === '매수' ? 'text-green-400' : 'text-red-400'}`}>
                          {trade.action}
                        </span>
                      </div>
                      <span className="text-xs text-gray-400">{trade.time}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-300">{trade.amount}</span>
                      <span className={`text-xs font-semibold ${trade.change.startsWith('+') ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.change}
                      </span>
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