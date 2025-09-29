'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  TrendingUp,
  BarChart3,
  Wallet,
  Star,
  Newspaper,
  Settings,
  Search,
  Bell,
  User,
  Globe,
  Activity
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { getMarketStatus, KOREAN_TRADING_HOURS } from '@/lib/types/korean-stocks';
import { useState, useEffect } from 'react';

interface KoreanTradingHeaderProps {
  className?: string;
}

export function KoreanTradingHeader({ className }: KoreanTradingHeaderProps) {
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState('');
  const [currentTime, setCurrentTime] = useState(''); // State for the time

  useEffect(() => {
    // Function to get formatted time
    const getFormattedTime = () => new Intl.DateTimeFormat('ko-KR', {
      timeZone: KOREAN_TRADING_HOURS.timezone,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(new Date());

    // Set the initial time
    setCurrentTime(getFormattedTime());

    // Update the time every second
    const timerId = setInterval(() => {
      setCurrentTime(getFormattedTime());
    }, 1000);

    // Cleanup interval on component unmount
    return () => clearInterval(timerId);
  }, []); // Empty dependency array means this effect runs only once on mount

  const marketStatus = getMarketStatus();

  const navItems = [
    {
      href: '/korean-trading',
      label: '시장현황',
      icon: TrendingUp,
      description: '실시간 주식 현황'
    },
    {
      href: '/korean-trading/portfolio',
      label: '내 포트폴리오',
      icon: Wallet,
      description: '보유 종목 관리'
    },
    {
      href: '/korean-trading/watchlist',
      label: '관심종목',
      icon: Star,
      description: '관심종목 모니터링'
    },
    {
      href: '/korean-trading/chart',
      label: '차트분석',
      icon: BarChart3,
      description: '기술적 분석 도구'
    },
    {
      href: '/korean-trading/news',
      label: '뉴스',
      icon: Newspaper,
      description: '시장 뉴스 및 분석'
    },
    {
      href: '/korean-trading/settings',
      label: '설정',
      icon: Settings,
      description: '거래 설정 관리'
    }
  ];

  const getMarketStatusBadge = () => {
    const statusConfig = {
      'OPEN': { text: '장중', color: 'bg-green-500', textColor: 'text-white' },
      'PRE_MARKET': { text: '장전', color: 'bg-yellow-500', textColor: 'text-white' },
      'AFTER_HOURS': { text: '장후', color: 'bg-orange-500', textColor: 'text-white' },
      'CLOSED': { text: '장마감', color: 'bg-gray-500', textColor: 'text-white' },
      'HOLIDAY': { text: '휴장', color: 'bg-red-500', textColor: 'text-white' }
    };

    const config = statusConfig[marketStatus];
    return (
      <Badge className={cn(config.color, config.textColor, 'text-xs font-medium')}>
        <Activity className="w-3 h-3 mr-1" />
        {config.text}
      </Badge>
    );
  };

  return (
    <header className={cn(
      'bg-[#1a1a1b] border-b border-gray-700',
      'sticky top-0 z-50 backdrop-blur-sm bg-[#1a1a1b]/95',
      'shadow-xl',
      className
    )}>
      {/* Top Bar with Logo and User Actions */}
      <div className="px-4 md:px-6 py-3 border-b border-gray-800">
        <div className="flex items-center justify-between max-w-[1600px] mx-auto">
          {/* Logo and Market Status */}
          <div className="flex items-center gap-6">
            <Link href="/korean-trading" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-lg">🇰🇷</span>
                </div>
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-[#1a1a1b]" />
              </div>
              <div className="space-y-0.5">
                <h1 className="text-lg font-bold text-white">
                  한국 증권거래소
                </h1>
                <p className="text-xs text-gray-400">
                  Professional Trading Platform
                </p>
              </div>
            </Link>

            {/* Market Status and Time */}
            <div className="hidden md:flex items-center gap-4">
              {getMarketStatusBadge()}
              <div className="text-xs text-gray-400">
                KST {currentTime || '--:--:--'}
              </div>
            </div>
          </div>

          {/* Search and User Actions */}
          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-500" />
              <Input
                placeholder="종목명 또는 종목코드 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-64 bg-[#2a2a2a] border-gray-600 text-white placeholder:text-gray-500 focus:border-blue-500"
              />
            </div>

            {/* User Actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-700 p-2"
              >
                <Bell className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-700 p-2"
              >
                <Globe className="w-5 h-5" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white hover:bg-gray-700 p-2"
              >
                <User className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <div className="px-4 md:px-6">
        <div className="flex items-center justify-between max-w-[1600px] mx-auto">
          <nav className="flex items-center">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    'group flex items-center gap-2 px-4 py-4 text-sm font-medium transition-all duration-200 relative',
                    'hover:bg-gray-800/50',
                    isActive
                      ? 'text-blue-400 bg-blue-500/5'
                      : 'text-gray-300 hover:text-white'
                  )}
                  title={item.description}
                >
                  <Icon className={cn(
                    'w-4 h-4 transition-colors',
                    isActive ? 'text-blue-400' : 'text-gray-400 group-hover:text-white'
                  )} />
                  <span>{item.label}</span>

                  {/* Active indicator */}
                  {isActive && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* Quick Actions */}
          <div className="flex items-center gap-3">
            {/* Market Status Mobile */}
            <div className="md:hidden">
              {getMarketStatusBadge()}
            </div>

            {/* Quick Buy Button */}
            <Button
              size="sm"
              className="bg-red-600 hover:bg-red-700 text-white shadow-lg hidden md:flex"
            >
              빠른 매수
            </Button>

            {/* Quick Sell Button */}
            <Button
              size="sm"
              variant="outline"
              className="border-blue-600 text-blue-400 hover:bg-blue-600 hover:text-white shadow-lg hidden md:flex"
            >
              빠른 매도
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}

// Mobile-optimized header
export function MobileKoreanTradingHeader({ className }: KoreanTradingHeaderProps) {
  const pathname = usePathname();
  const marketStatus = getMarketStatus();

  const getMarketStatusBadge = () => {
    const statusConfig = {
      'OPEN': { text: '장중', color: 'bg-green-500' },
      'PRE_MARKET': { text: '장전', color: 'bg-yellow-500' },
      'AFTER_HOURS': { text: '장후', color: 'bg-orange-500' },
      'CLOSED': { text: '장마감', color: 'bg-gray-500' },
      'HOLIDAY': { text: '휴장', color: 'bg-red-500' }
    };

    const config = statusConfig[marketStatus];
    return (
      <Badge className={cn(config.color, 'text-white text-xs')}>
        {config.text}
      </Badge>
    );
  };

  return (
    <header className={cn(
      'bg-[#1a1a1b] border-b border-gray-700',
      'sticky top-0 z-50',
      className
    )}>
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo and Status */}
          <div className="flex items-center gap-3">
            <Link href="/korean-trading" className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">🇰🇷</span>
              </div>
              <span className="text-white font-semibold text-sm">한국증권</span>
            </Link>
            {getMarketStatusBadge()}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white p-2"
            >
              <Search className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white p-2"
            >
              <Bell className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-gray-400 hover:text-white p-2"
            >
              <User className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}