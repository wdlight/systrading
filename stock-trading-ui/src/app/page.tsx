'use client';

import FocusTrap from 'focus-trap-react';
import { useEffect, useMemo, useState } from 'react';
import { QuickActionPanel } from '@/components/layout/QuickActionPanel';
import { PortfolioPerformance } from '@/components/trading/PortfolioPerformance';
import { MarketOverview } from '@/components/trading/MarketOverview';
import { useRealtimeData } from '@/hooks/useRealtimeData';
import { useAccountData } from '@/hooks/useAccountData';
import { Target } from 'lucide-react';
import { useLocalStorage } from '@/lib/hooks/useLocalStorage';
import { mockUserNotifications } from '@/lib/mock/userNotifications';
import { UserNotification } from '@/lib/types';
import { AssetPanel } from '@/components/trading/AssetPanel';

export default function Home() {
  const [bottomSheetOpen, setBottomSheetOpen] = useState(false);
  const {
    connectionStatus,
    watchlist,
    isLoading: realtimeLoading,
    error: realtimeError,
  } = useRealtimeData();
  const {
    accountBalance,
    portfolioStats,
    isLoading: accountLoading,
    error: accountError,
  } = useAccountData();
  const [userNotifications] = useLocalStorage<UserNotification[]>(
    'user-notifications',
    mockUserNotifications,
  );

  const unreadNotifications = useMemo(
    () => userNotifications.filter((notification) => !notification.read).length,
    [userNotifications],
  );

  const isLoading = realtimeLoading || accountLoading;

  useEffect(() => {
    if (!bottomSheetOpen) {
      document.body.style.overflow = '';
      return;
    }

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [bottomSheetOpen]);

  useEffect(() => {
    if (!bottomSheetOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setBottomSheetOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [bottomSheetOpen]);

  return (
    <div className="flex overflow-hidden bg-[#1a1a1a]">
        <QuickActionPanel className="hidden xl:flex" />

        <main className="flex-1 overflow-hidden bg-[#1a1a1a]">
          <div className="flex h-full overflow-hidden">
            <div className="flex-1 overflow-y-auto">
              <div className="mx-auto max-w-[1280px] space-y-2 px-3 py-3 md:space-y-3 md:px-4 md:py-4 animate-in fade-in duration-500">
                <MarketOverview compact className="w-full" />

                <PortfolioPerformance
                  accountBalance={accountBalance}
                  stats={portfolioStats}
                />

                <AssetPanel
                  positions={accountBalance?.positions ?? []}
                  watchlist={watchlist}
                  holdingsLoading={accountLoading}
                  holdingsError={accountError}
                  watchlistLoading={realtimeLoading}
                  watchlistError={realtimeError}
                />

                {isLoading && (
                  <div className="fixed bottom-4 right-4 z-50 rounded-lg border border-gray-600 bg-[#2a2a2a] p-3 shadow-2xl">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
                      <span className="text-xs font-medium text-gray-300">데이터 로딩 중...</span>
                    </div>
                  </div>
                )}

                {process.env.NODE_ENV === 'development' && (
                  <div className="pt-2">
                    <div className="rounded-lg border border-blue-500/30 bg-[#2a2a2a] p-3">
                      <h3 className="mb-2 flex items-center gap-2 text-xs font-medium text-blue-400">
                        🚀 Development Status & 실시간 연결 활성
                      </h3>
                      <div className="space-y-2 text-[11px] text-gray-300">
                        <div className="mb-2 border-b border-gray-700 pb-2">
                          <div className="mb-2 flex items-center justify-between gap-2">
                            <span className="font-medium">실시간 연결 상태:</span>
                            <div className="flex items-center gap-2">
                              <div
                                className={`h-2 w-2 rounded-full ${
                                  connectionStatus.status === 'connected' ? 'bg-profit' : 'bg-loss'
                                }`}
                              />
                              <span
                                className={
                                  connectionStatus.status === 'connected'
                                    ? 'text-profit-foreground'
                                    : 'text-loss-foreground'
                                }
                              >
                                {connectionStatus.status === 'connected' ? '연결됨' : '연결 끊김'}
                              </span>
                            </div>
                          </div>
                          {connectionStatus.lastConnected && (
                            <div className="flex items-center justify-between text-[11px]">
                              <span>마지막 연결:</span>
                              <span className="text-gray-400">
                                {new Date(connectionStatus.lastConnected).toLocaleTimeString('ko-KR')}
                              </span>
                            </div>
                          )}
                          {connectionStatus.reconnectAttempts > 0 && (
                            <div className="flex items-center justify-between text-[11px]">
                              <span>재연결 시도:</span>
                              <span className="text-amber-400">
                                {connectionStatus.reconnectAttempts}회
                              </span>
                            </div>
                          )}
                        </div>

                        <div className="flex flex-wrap items-center gap-2 text-[11px] text-gray-300">
                          <div className="flex items-center gap-1">
                            <span className="font-medium text-gray-400">WebSocket:</span>
                            <span
                              className={
                                connectionStatus.status === 'connected'
                                  ? 'text-profit-foreground'
                                  : 'text-loss-foreground'
                              }
                            >
                              {connectionStatus.status}
                            </span>
                          </div>
                          <span className="text-gray-600">|</span>
                          <div className="flex items-center gap-1">
                            <span className="font-medium text-gray-400">Backend API:</span>
                            <span className="text-blue-400">
                              {process.env.NEXT_PUBLIC_API_URL || 'localhost:8000'}
                            </span>
                          </div>
                          <span className="text-gray-600">|</span>
                          <div className="flex items-center gap-1">
                            <span className="font-medium text-gray-400">Account Info:</span>
                            <span className={accountBalance ? 'text-profit-foreground' : 'text-amber-400'}>
                              {accountBalance ? 'Connected' : 'Pending'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div className="pb-4" />
              </div>
            </div>
          </div>
        </main>

      {/* Mobile Quick Action FAB */}
      <div className="fixed bottom-6 right-6 z-50 xl:hidden">
        <button
          type="button"
          onClick={() => setBottomSheetOpen(true)}
          className="relative flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-[0_20px_40px_rgba(37,99,235,0.35)] transition-transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-[#1a1a1a]"
          aria-label="빠른 작업 열기"
        >
          <Target className="h-6 w-6" />
          {unreadNotifications > 0 && (
            <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.1rem] items-center justify-center rounded-full bg-red-500 px-1 text-[11px] font-semibold text-white">
              {unreadNotifications > 9 ? '9+' : unreadNotifications}
            </span>
          )}
        </button>
      </div>

      {bottomSheetOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/55 backdrop-blur-[2px] xl:hidden"
            onClick={() => setBottomSheetOpen(false)}
          />
          <FocusTrap
            active={bottomSheetOpen}
            focusTrapOptions={{ clickOutsideDeactivates: true, escapeDeactivates: true }}
          >
            <div
              role="dialog"
              aria-modal="true"
              aria-label="빠른 작업 패널"
              className="fixed inset-x-0 bottom-0 z-50 max-h-[82vh] xl:hidden"
            >
              <div className="flex h-full flex-col overflow-hidden rounded-t-3xl bg-[#1c1c1c] pb-[calc(env(safe-area-inset-bottom)+1rem)] shadow-[0_-18px_32px_rgba(0,0,0,0.45)]">
                <QuickActionPanel isSheet onClose={() => setBottomSheetOpen(false)} />
              </div>
            </div>
          </FocusTrap>
        </>
      )}
    </div>
  );
}
