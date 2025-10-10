'use client';

import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TabButton } from '@/components/layout/TabButton';
import { HoldingsCard } from '@/components/trading/HoldingsPanel';
import { WatchlistCard } from '@/components/trading/WatchlistPanel';
import { UserNotificationDropdown } from '@/components/common/UserNotificationDropdown';
import { useLocalStorage } from '@/lib/hooks/useLocalStorage';
import { mockUserNotifications } from '@/lib/mock/userNotifications';
import type { Position, UserNotification, WatchlistItem } from '@/lib/types';
import { Briefcase, Eye, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';
import { EmptyState } from '@/components/common/EmptyState';

type AssetPanelTab = 'holdings' | 'watchlist' | 'alerts';

interface AssetPanelProps {
  className?: string;
  positions: Position[];
  watchlist: WatchlistItem[];
  holdingsLoading?: boolean;
  holdingsError?: string | null;
  watchlistLoading?: boolean;
  watchlistError?: string | null;
}

export function AssetPanel({
  className,
  positions,
  watchlist,
  holdingsLoading,
  holdingsError,
  watchlistLoading,
  watchlistError,
}: AssetPanelProps) {
  const [activeTab, setActiveTab] = useState<AssetPanelTab>('holdings');
  const [notifications, setNotifications] = useLocalStorage<UserNotification[]>
    ('user-notifications', mockUserNotifications);

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.read).length,
    [notifications],
  );

  const handleMarkNotification = (id: string) => {
    setNotifications((prev) =>
      prev.map((notification) =>
        notification.id === id ? { ...notification, read: true } : notification,
      ),
    );
  };

  const handleMarkAll = () => {
    setNotifications((prev) => prev.map((notification) => ({ ...notification, read: true })));
  };

  return (
    <Card className={cn('bg-[#2a2a2a] border-gray-700 shadow-xl gap-1 py-1', className)}>
      <CardHeader className="px-4 pb-1">
        <div className="flex flex-col gap-1 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <CardTitle className="text-lg font-bold text-white">자산 현황</CardTitle>
            <p className="text-xs text-gray-400">보유 종목과 워치리스트, 알림을 한 곳에서 관리하세요.</p>
          </div>
          <div className="flex w-full overflow-x-auto rounded-lg border border-gray-700 bg-[#1a1a1a] p-1 text-[11px] lg:w-auto">
            <TabButton
              active={activeTab === 'holdings'}
              onClick={() => setActiveTab('holdings')}
              icon={Briefcase}
              label={`보유 (${positions.length})`}
            />
            <TabButton
              active={activeTab === 'watchlist'}
              onClick={() => setActiveTab('watchlist')}
              icon={Eye}
              label={`관심 (${watchlist.length})`}
            />
            <TabButton
              active={activeTab === 'alerts'}
              onClick={() => setActiveTab('alerts')}
              icon={Bell}
              label={`알림 (${unreadCount})`}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="px-3 py-1">
        {activeTab === 'holdings' && (
          <HoldingsCard
            positions={positions}
            isLoading={holdingsLoading}
            error={holdingsError}
          />
        )}
        {activeTab === 'watchlist' && (
          <WatchlistCard items={watchlist} isLoading={watchlistLoading} error={watchlistError} />
        )}
        {activeTab === 'alerts' && (
          <div className="rounded-xl border border-gray-700 bg-[#1a1a1a] p-2">
            {notifications.length === 0 ? (
              <EmptyState
                title="새로운 알림이 없습니다"
                description="거래 체결, 기술적 시그널 등의 알림이 도착하면 이곳에서 확인할 수 있습니다."
                icon={<Bell className="h-7 w-7 text-gray-500" />}
              />
            ) : (
              <UserNotificationDropdown
                notifications={notifications}
                onMarkAsRead={handleMarkNotification}
                onMarkAllAsRead={handleMarkAll}
              />
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
