'use client';

import { Fragment } from 'react';
import { Bell, CheckCircle2, Circle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { EmptyState } from '@/components/common/EmptyState';
import { cn, formatDateTime, formatCurrency } from '@/lib/utils';
import { UserNotification } from '@/lib/types';

interface UserNotificationDropdownProps {
  notifications: UserNotification[];
  onMarkAsRead: (id: string) => void;
  onMarkAllAsRead: () => void;
}

export function UserNotificationDropdown({
  notifications,
  onMarkAsRead,
  onMarkAllAsRead,
}: UserNotificationDropdownProps) {
  if (notifications.length === 0) {
    return (
      <div className="w-80">
        <EmptyState
          title="새로운 알림이 없습니다"
          description="거래 내역이나 관제 신호가 발생하면 이곳에서 확인할 수 있습니다."
          icon={<Bell className="h-7 w-7 text-gray-500" />}
        />
      </div>
    );
  }

  return (
    <div className="flex w-80 flex-col gap-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-white">알림 센터</p>
          <p className="text-xs text-gray-400">
            최근 {notifications.length}개의 이벤트가 기록되었습니다.
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs text-gray-400 hover:text-white"
          onClick={onMarkAllAsRead}
        >
          모두 읽음 처리
        </Button>
      </div>

      <ScrollArea className="max-h-80 pr-2">
        <div className="space-y-2">
          {notifications.map((notification) => {
            const isUnread = !notification.read;
            const amountLabel =
              typeof notification.metadata?.amount === 'number'
                ? formatCurrency(notification.metadata.amount, { currency: 'KRW' })
                : undefined;

            return (
              <Fragment key={notification.id}>
                <button
                  type="button"
                  onClick={() => onMarkAsRead(notification.id)}
                  className={cn(
                    'w-full rounded-lg border border-gray-700 bg-[#1a1a1a] px-4 py-3 text-left transition-colors',
                    isUnread ? 'hover:border-blue-500/80' : 'hover:border-gray-600',
                  )}
                >
                  <div className="flex items-start gap-3">
                    <span
                      className={cn(
                        'mt-1 inline-flex h-2.5 w-2.5 flex-shrink-0 items-center justify-center rounded-full',
                        isUnread ? 'bg-blue-400' : 'bg-gray-600',
                      )}
                    >
                      {isUnread ? <Circle className="h-2 w-2 text-blue-900" /> : null}
                    </span>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-white">
                          {notification.title}
                        </p>
                        {notification.metadata?.orderType && (
                          <span
                            className={cn(
                              'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase',
                              notification.metadata.orderType === 'buy'
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : 'bg-red-500/20 text-red-300',
                            )}
                          >
                            {notification.metadata.orderType}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-300">{notification.message}</p>
                      <div className="flex items-center gap-2 text-[11px] text-gray-500">
                        <span>{formatDateTime(notification.timestamp)}</span>
                        {notification.metadata?.stockCode && (
                          <span className="font-mono text-gray-400">
                            {notification.metadata.stockCode}
                          </span>
                        )}
                        {amountLabel && <span>{amountLabel}</span>}
                      </div>
                    </div>
                    {!isUnread && (
                      <CheckCircle2 className="mt-1 h-4 w-4 flex-shrink-0 text-gray-500" />
                    )}
                  </div>
                </button>
              </Fragment>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
