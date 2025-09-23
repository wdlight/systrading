'use client';

import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SimpleConnectionStatus } from '@/components/common/ConnectionStatus';
import { useRealtimeData } from '@/hooks/useRealtimeData';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onMenuClick?: () => void;
  className?: string;
}

export function Header({ onMenuClick, className }: HeaderProps) {
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
              Portfolio Manager
            </h1>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Professional Trading Platform
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* 연결 상태 */}
        <SimpleConnectionStatus connectionState={connectionStatus} />

        {/* Add Position 버튼 */}
        <Button
          className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white"
          size="sm"
        >
          Add Position
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