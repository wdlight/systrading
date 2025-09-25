'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, Bell, Settings, Home, TrendingUp } from 'lucide-react';
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
  const pathname = usePathname();

  const navItems = [
    { href: '/', label: '대시보드', icon: Home },
    { href: '/trading', label: '매매', icon: TrendingUp },
  ];

  return (
    <header className={cn(
      'bg-[#2a2a2a] border-b border-gray-700',
      'px-7 py-4 flex items-center justify-between',
      'sticky top-0 z-40 backdrop-blur-sm bg-[#2a2a2a]/95',
      'shadow-professional',
      className
    )}>
      <div className="flex items-center gap-8">
        {/* 모바일 메뉴 버튼 */}
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden text-gray-300 hover:text-white hover:bg-gray-700 transition-colors duration-200"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Professional Logo & Title */}
        <Link href="/" className="flex items-center gap-5">
          <div className="relative">
            <div className="w-11 h-11 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-professional">
              <span className="text-white font-bold text-lg">🏛️</span>
            </div>
            <div className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-[#2a2a2a]" />
          </div>
          <div className="space-y-0.5">
            <h1 className="text-heading-md text-white">
              Portfolio Manager
            </h1>
            <p className="text-caption-md text-gray-400">
              Professional Trading Platform
            </p>
          </div>
        </Link>

        {/* Navigation Menu */}
        <nav className="hidden md:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200',
                  isActive
                    ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/20'
                    : 'text-gray-300 hover:text-white hover:bg-gray-700/50'
                )}
              >
                <Icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="flex items-center gap-5">
        {/* Connection Status */}
        <SimpleConnectionStatus connectionState={connectionStatus} />

        {/* Professional Add Position Button */}
        <Button
          className="button-professional bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white shadow-professional hover:shadow-professional-lg hover:scale-105"
        >
          + Add Position
        </Button>
      </div>
    </header>
  );
}

// Mobile Header with Professional Styling
export function MobileHeader({ onMenuClick, className }: HeaderProps) {
  const { connectionStatus } = useRealtimeData();

  return (
    <header className={cn(
      'bg-[#2a2a2a] border-b border-gray-700',
      'px-5 py-3.5 flex items-center justify-between',
      'sticky top-0 z-40 shadow-professional',
      className
    )}>
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          className="button-professional-sm text-gray-300 hover:text-white hover:bg-gray-700"
          onClick={onMenuClick}
        >
          <Menu className="h-5 w-5" />
        </Button>

        <div className="flex items-center gap-4">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-sm">🏛️</span>
          </div>
          <span className="text-heading-sm text-white">
            Portfolio Manager
          </span>
          <SimpleConnectionStatus connectionState={connectionStatus} />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          className="button-professional-sm text-gray-400 hover:text-white hover:bg-gray-700"
        >
          <Bell className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          className="button-professional-sm text-gray-400 hover:text-white hover:bg-gray-700"
        >
          <Settings className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}