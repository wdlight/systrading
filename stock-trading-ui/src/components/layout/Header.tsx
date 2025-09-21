'use client';

import { useState } from 'react';
import { Bell, Settings, User, Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SimpleConnectionStatus } from '@/components/common/ConnectionStatus';
import { useRealtimeData } from '@/hooks/useRealtimeData';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onMenuClick?: () => void;
  className?: string;
}

export function Header({ onMenuClick, className }: HeaderProps) {
  const [notificationCount] = useState(3); // 실제로는 알림 시스템에서 가져옴
  const { connectionStatus } = useRealtimeData();

  return (
    <header className={cn(
      'bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800',
      'px-4 py-3 flex items-center justify-between',
      'sticky top-0 z-40 backdrop-blur-sm bg-white/95 dark:bg-gray-900/95',
      className
    )}>
      <div className="flex items-center gap-4">
        {/* 모바일 메뉴 버튼 */}
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* 로고 및 제목 */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">🏛️</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Smart Trading Dashboard
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              한국투자증권 시스템트레이딩
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* 연결 상태 */}
        <SimpleConnectionStatus connectionState={connectionStatus} />

        {/* 알림 */}
        <Button
          variant="ghost"
          size="sm"
          className="relative"
        >
          <Bell className="h-5 w-5" />
          {notificationCount > 0 && (
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
              {notificationCount > 9 ? '9+' : notificationCount}
            </span>
          )}
        </Button>

        {/* 설정 */}
        <Button
          variant="ghost"
          size="sm"
        >
          <Settings className="h-5 w-5" />
        </Button>

        {/* 사용자 */}
        <Button
          variant="ghost"
          size="sm"
        >
          <User className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}

// 모바일용 간단한 헤더
export function MobileHeader({ onMenuClick, className }: HeaderProps) {
  const { connectionStatus } = useRealtimeData();

  return (
    <header className={cn(
      'bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800',
      'px-3 py-2 flex items-center justify-between',
      'sticky top-0 z-40',
      className
    )}>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            🏛️ Smart Trading
          </span>
          <SimpleConnectionStatus connectionState={connectionStatus} />
        </div>
      </div>

      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm">
          <Bell className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm">
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}