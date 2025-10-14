'use client';

import { useState, useEffect } from 'react';
import { subscribeToMarketStatusUpdates } from '@/lib/websocket';
import { MarketStatusUpdate } from '@/lib/types';
import { Clock, AlertCircle, Info } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MarketStatusBannerProps {
  className?: string;
}

export function MarketStatusBanner({ className }: MarketStatusBannerProps) {
  const [marketStatus, setMarketStatus] = useState<MarketStatusUpdate['data'] | null>(null);
  const [isVisible, setIsVisible] = useState(false);
  const [lastMessageId, setLastMessageId] = useState<string>('');

  useEffect(() => {
    const unsubscribe = subscribeToMarketStatusUpdates((data) => {
      // 중복 메시지 방지
      const messageId = `${data.status}_${data.session}_${data.message}`;
      if (messageId === lastMessageId) {
        return;
      }

      setLastMessageId(messageId);
      setMarketStatus(data);
      // 장이 닫혀있을 때만 배너 표시
      setIsVisible(data.status === 'closed');
    });

    return unsubscribe;
  }, [lastMessageId]);

  if (!isVisible || !marketStatus) {
    return null;
  }

  const getStatusIcon = () => {
    switch (marketStatus.session) {
      case 'closed':
        return <AlertCircle className="w-4 h-4 text-orange-400" />;
      case 'pre_market':
        return <Clock className="w-4 h-4 text-blue-400" />;
      case 'after_market':
        return <Clock className="w-4 h-4 text-purple-400" />;
      default:
        return <Info className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (marketStatus.session) {
      case 'closed':
        return 'bg-orange-900/20 border-orange-800 text-orange-200';
      case 'pre_market':
        return 'bg-blue-900/20 border-blue-800 text-blue-200';
      case 'after_market':
        return 'bg-purple-900/20 border-purple-800 text-purple-200';
      default:
        return 'bg-gray-900/20 border-gray-800 text-gray-200';
    }
  };

  const formatNextOpenTime = (nextOpen: string) => {
    try {
      const date = new Date(nextOpen);
      const now = new Date();
      const diffMs = date.getTime() - now.getTime();

      if (diffMs <= 0) {
        return '곧 시작됩니다';
      }

      const hours = Math.floor(diffMs / (1000 * 60 * 60));
      const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `${hours}시간 ${minutes}분 후`;
      } else {
        return `${minutes}분 후`;
      }
    } catch {
      return '시간 정보 없음';
    }
  };

  return (
    <div className={cn(
      'fixed top-16 left-1/2 transform -translate-x-1/2 z-50',
      'px-4 py-2 rounded-lg border backdrop-blur-sm',
      'flex items-center gap-2 text-sm font-medium',
      'animate-in slide-in-from-top-2 duration-300',
      getStatusColor(),
      className
    )}>
      {getStatusIcon()}
      <span>{marketStatus.message}</span>
      {marketStatus.next_open && (
        <span className="text-xs opacity-75">
          (다음 시작: {formatNextOpenTime(marketStatus.next_open)})
        </span>
      )}
      {marketStatus.last_data_timestamp && (
        <span className="text-xs opacity-50">
          마지막 업데이트: {new Date(marketStatus.last_data_timestamp).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
}
