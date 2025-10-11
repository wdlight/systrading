'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, Bell, Settings, Home, TrendingUp } from 'lucide-react';
import { useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { SimpleConnectionStatus } from '@/components/common/ConnectionStatus';
import { useRealtimeData } from '@/hooks/useRealtimeData';
import { cn } from '@/lib/utils';
import { useLocalStorage } from '@/lib/hooks/useLocalStorage';
import { mockUserNotifications } from '@/lib/mock/userNotifications';
import { UserNotification } from '@/lib/types';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { UserNotificationDropdown } from '@/components/common/UserNotificationDropdown';

interface HeaderProps {
  onMenuClick?: () => void;
  className?: string;
}

function useUserNotifications() {
  return useLocalStorage<UserNotification[]>('user-notifications', mockUserNotifications);
}

export function Header({ onMenuClick, className }: HeaderProps) {
  const { connectionStatus } = useRealtimeData();
  const pathname = usePathname();
  const [notifications, setNotifications] = useUserNotifications();

  const unreadCount = useMemo(
    () => notifications.filter((notification) => !notification.read).length,
    [notifications],
  );

  const navItems = [
    { href: '/', label: '대시보드', icon: Home },
    { href: '/trview', label: '주식관리', icon: TrendingUp },
    { href: '/trading', label: '매매', icon: TrendingUp },
    { href: '/exchange', label: 'Exchange', icon: TrendingUp },
  ];

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
    <header
      className={cn(
        'bg-[#2a2a2a] border-b border-gray-700',
        'px-7 py-4 flex items-center justify-between',
        'sticky top-0 z-40 backdrop-blur-sm bg-[#2a2a2a]/95',
        'shadow-professional',
        className,
      )}
    >
      <div className="flex items-center gap-8">
        <Button
          variant="ghost"
          size="sm"
          className="text-gray-300 transition-colors duration-200 hover:bg-gray-700 hover:text-white lg:hidden"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        <Link href="/" className="flex items-center gap-5">
          <div className="relative">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-professional">
              <span className="text-lg font-bold text-white">🏛️</span>
            </div>
            <div className="absolute -right-1 -top-1 h-3.5 w-3.5 rounded-full border-2 border-[#2a2a2a] bg-green-500" />
          </div>
          <div className="space-y-0.5">
            <h1 className="text-heading-md text-white">Portfolio Manager</h1>
            <p className="text-caption-md text-gray-400">Professional Trading Platform</p>
          </div>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors duration-200',
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white',
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-4">
        <SimpleConnectionStatus connectionState={connectionStatus} />

        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              className="relative text-gray-300 hover:bg-gray-700 hover:text-white"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-5 min-w-[1.25rem] items-center justify-center rounded-full bg-red-500 px-1 text-[11px] font-semibold text-white">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="border-gray-700 bg-[#1f1f1f]">
            <UserNotificationDropdown
              notifications={notifications}
              onMarkAsRead={handleMarkNotification}
              onMarkAllAsRead={handleMarkAll}
            />
          </PopoverContent>
        </Popover>

        <Button className="button-professional bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-professional transition-transform hover:scale-105 hover:from-blue-600 hover:to-blue-700 hover:shadow-professional-lg">
          + Add Position
        </Button>
      </div>
    </header>
  );
}

export function MobileHeader({ onMenuClick, className }: HeaderProps) {
  const { connectionStatus } = useRealtimeData();
  const [notifications, setNotifications] = useUserNotifications();

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
    <header
      className={cn(
        'bg-[#2a2a2a] border-b border-gray-700',
        'flex items-center justify-between px-5 py-3.5',
        'sticky top-0 z-40 shadow-professional',
        className,
      )}
    >
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          className="button-professional-sm text-gray-300 hover:bg-gray-700 hover:text-white"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        <div className="flex items-center gap-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg">
            <span className="text-sm font-bold text-white">🏛️</span>
          </div>
          <span className="text-heading-sm text-white">Portfolio Manager</span>
          <SimpleConnectionStatus connectionState={connectionStatus} />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              className="relative text-gray-400 hover:bg-gray-700 hover:text-white"
            >
              <Bell className="h-4 w-4" />
              {unreadCount > 0 && (
                <span className="absolute -right-1 -top-1 flex h-4 min-w-[1.05rem] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold text-white">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent align="end" className="border-gray-700 bg-[#1f1f1f]">
            <UserNotificationDropdown
              notifications={notifications}
              onMarkAsRead={handleMarkNotification}
              onMarkAllAsRead={handleMarkAll}
            />
          </PopoverContent>
        </Popover>
        <Button
          variant="ghost"
          className="button-professional-sm text-gray-400 hover:bg-gray-700 hover:text-white"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
