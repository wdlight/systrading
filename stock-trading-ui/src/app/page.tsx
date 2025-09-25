'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { QuickActionPanel } from '@/components/layout/QuickActionPanel';
import { PortfolioSummary } from '@/components/trading/PortfolioSummary';
import { TradingConditions } from '@/components/trading/TradingConditions';
import { WatchlistPanel } from '@/components/trading/WatchlistPanel';
import { PortfolioPerformance } from '@/components/trading/PortfolioPerformance';
import { MarketOverview } from '@/components/trading/MarketOverview';
import { DetailedConnectionStatus } from '@/components/common/ConnectionStatus';
import { useRealtimeData } from '@/hooks/useRealtimeData';
import { useAccountData } from '@/hooks/useAccountData';
import { cn } from '@/lib/utils';

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { connectionStatus, isLoading: realtimeLoading } = useRealtimeData();
  const { accountBalance, isLoading: accountLoading } = useAccountData();

  const isLoading = realtimeLoading || accountLoading;

  return (
    <div className="min-h-screen bg-[#1a1a1a]">
      {/* Enhanced Professional Header */}
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      {/* Main Container - New Layout: Sidebar + Main + QuickAction Panel */}
      <div className="flex min-h-[calc(100vh-64px)]">
        {/* Left Sidebar - Trading Conditions (Compact) */}
        <aside className={cn(
          'w-72 bg-[#2a2a2a] border-r border-gray-700',
          'transform transition-transform duration-300 ease-in-out',
          'lg:translate-x-0 lg:static lg:inset-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          'fixed inset-y-0 left-0 z-30 lg:z-0',
          'lg:relative'
        )}>
          <div className="h-screen lg:h-auto overflow-y-auto scrollbar-hide p-2">
            <TradingConditions />
          </div>
        </aside>

        {/* 오버레이 (모바일) */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main Dashboard Area */}
        <main className="flex-1 min-w-0 bg-[#1a1a1a] overflow-y-auto">
          <div className="min-h-full">
            {/* Enhanced Dashboard Grid Layout */}
            <div className="p-4 md:p-6 space-y-4 md:space-y-6 max-w-[1400px] mx-auto animate-in fade-in duration-500">
              {/* Top Section: Portfolio Summary + Performance Analytics (50:50) */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
                <div>
                  <PortfolioSummary />
                </div>
                <div>
                  <PortfolioPerformance className="h-full" />
                </div>
              </div>

              {/* Main Section: Watchlist Panel */}
              <div className="space-y-6">
                <WatchlistPanel />
              </div>

              {/* Bottom Section: Market Overview */}
              <div className="space-y-4 lg:space-y-6">
                <MarketOverview />
              </div>

              {/* Professional Loading Indicator */}
              {isLoading && (
                <div className="fixed bottom-6 right-6 bg-[#2a2a2a] border border-gray-600 rounded-lg p-4 shadow-2xl z-50">
                  <div className="flex items-center gap-3">
                    <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                    <span className="text-sm text-gray-300 font-medium">
                      데이터 로딩 중...
                    </span>
                  </div>
                </div>
              )}

              {/* Development Info Panel with Integrated Connection Status */}
              {process.env.NODE_ENV === 'development' && (
                <div className="mt-8">
                  {/* Integrated Development Status with Real-time Connection */}
                  <div className="p-4 bg-[#2a2a2a] border border-blue-500/30 rounded-lg">
                    <h3 className="text-sm font-medium text-blue-400 mb-4 flex items-center gap-2">
                      🚀 Development Status & 실시간 연결 활성
                    </h3>
                    <div className="text-xs text-gray-300 space-y-3">
                      {/* Real-time Connection Status */}
                      <div className="border-b border-gray-700 pb-3 mb-3">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-medium">실시간 연결 상태:</span>
                          <div className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${
                              connectionStatus.status === 'connected' ? 'bg-profit' : 'bg-loss'
                            }`} />
                            <span className={connectionStatus.status === 'connected' ? 'text-profit-foreground' : 'text-loss-foreground'}>
                              {connectionStatus.status === 'connected' ? '연결됨' : '연결 끊김'}
                            </span>
                          </div>
                        </div>
                        {connectionStatus.lastUpdate && (
                          <div className="flex justify-between items-center">
                            <span>마지막 업데이트:</span>
                            <span className="text-gray-400">
                              {new Date(connectionStatus.lastUpdate).toLocaleTimeString('ko-KR')}
                            </span>
                          </div>
                        )}
                        {connectionStatus.reconnectAttempts > 0 && (
                          <div className="flex justify-between items-center">
                            <span>재연결 시도:</span>
                            <span className="text-amber-400">
                              {connectionStatus.reconnectAttempts}회
                            </span>
                          </div>
                        )}
                      </div>

                      {/* System Status */}
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span>WebSocket:</span>
                          <span className={connectionStatus.status === 'connected' ? 'text-profit-foreground' : 'text-loss-foreground'}>
                            {connectionStatus.status}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span>Backend API:</span>
                          <span className="text-blue-400">
                            {process.env.NEXT_PUBLIC_API_URL || 'localhost:8000'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span>Account Info:</span>
                          <span className={accountBalance ? 'text-profit-foreground' : 'text-amber-400'}>
                            {accountBalance ? 'Connected' : 'Pending'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 하단 패딩 추가 - 모든 내용이 완전히 보이도록 */}
              <div className="pb-8"></div>
            </div>
          </div>
        </main>

        {/* Right Panel - Quick Action Panel */}
        <QuickActionPanel className="hidden xl:flex" />
      </div>
    </div>
  );
}
