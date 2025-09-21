'use client';

import { useState } from 'react';
import { Header } from '@/components/layout/Header';
import { PortfolioSummary } from '@/components/trading/PortfolioSummary';
import { TradingConditions } from '@/components/trading/TradingConditions';
import { WatchlistPanel } from '@/components/trading/WatchlistPanel';
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* 헤더 */}
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />

      {/* 메인 컨테이너 */}
      <div className="flex">
        {/* 사이드바 (매매 조건) */}
        <aside className={cn(
          'w-80 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700',
          'transform transition-transform duration-300 ease-in-out',
          'md:translate-x-0 md:static md:inset-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          'fixed inset-y-0 left-0 z-30 md:z-0',
          'pt-16 md:pt-0' // 헤더 높이만큼 패딩
        )}>
          <div className="h-full overflow-y-auto p-4">
            <TradingConditions />
          </div>
        </aside>

        {/* 오버레이 (모바일) */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 z-20 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* 메인 콘텐츠 */}
        <main className="flex-1 min-w-0">
          {/* 대시보드 그리드 */}
          <div className="p-4 space-y-6">
            {/* 상단: 포트폴리오 요약 + 연결 상태 */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
              <div className="lg:col-span-3">
                <PortfolioSummary />
              </div>
              <div className="lg:col-span-1">
                <DetailedConnectionStatus 
                  connectionState={connectionStatus}
                  className="h-full"
                />
              </div>
            </div>

            {/* 메인: 워치리스트 */}
            <div className="grid grid-cols-1 gap-6">
              <WatchlistPanel />
            </div>

            {/* 로딩 상태 표시 */}
            {isLoading && (
              <div className="fixed bottom-4 right-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 shadow-lg">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    데이터 로딩 중...
                  </span>
                </div>
              </div>
            )}

            {/* 개발 정보 (개발 환경에서만 표시) */}
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <h3 className="text-sm font-medium text-blue-900 dark:text-blue-400 mb-2">
                  🚀 개발 정보
                </h3>
                <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                  <p>• 실시간 WebSocket 연결: {connectionStatus.status}</p>
                  <p>• 백엔드 API: {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}</p>
                  <p>• 계좌 정보: {accountBalance ? '연결됨' : '연결 안됨'}</p>
                </div>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
