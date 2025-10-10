'use client';

import { useMemo, useState } from 'react';
import { Eye, Target, Bell, X } from 'lucide-react';
import { TabButton } from './TabButton';
import { TradingQuick } from '@/components/trading/TradingQuick';
import { QuickActionPanelProps } from '@/lib/types/components';
import { cn } from '@/lib/utils';
import { TradingConditions } from '@/components/trading/TradingConditions';

// 임시 컴포넌트들 (실제 구현은 나중에)
function WatchlistQuick() {
  return (
    <div className="space-y-2 text-sm text-gray-300">
      <div>
        <h3 className="mb-2 font-semibold text-white">관심종목</h3>
        <div className="space-y-2">
          <div className="rounded-lg border border-gray-600 bg-[#1a1a1a] p-2">
            <div className="flex items-center justify-between gap-3">
              <div>
                <span className="text-white font-medium">삼성전자</span>
                <span className="ml-1 text-xs text-gray-400">005930</span>
              </div>
              <div className="text-right">
                <div className="text-xs font-medium text-white">73,000원</div>
                <div className="text-[11px] text-profit-foreground">+1.5%</div>
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-gray-600 bg-[#1a1a1a] p-2">
            <div className="flex items-center justify-between gap-3">
              <div>
                <span className="text-white font-medium">SK하이닉스</span>
                <span className="ml-1 text-xs text-gray-400">000660</span>
              </div>
              <div className="text-right">
                <div className="text-xs font-medium text-white">127,500원</div>
                <div className="text-[11px] text-loss-foreground">-2.1%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


function AlertsPanel() {
  const alerts = useMemo(
    () => [
      {
        id: 'alert-1',
        title: 'RSI 과매수',
        description: '삼성전자 • 5분 전',
        intent: 'warning' as const,
      },
      {
        id: 'alert-2',
        title: 'MACD 골든크로스',
        description: 'SK하이닉스 • 10분 전',
        intent: 'success' as const,
      },
      {
        id: 'alert-3',
        title: '가격 알림',
        description: 'NAVER 목표가 도달 • 30분 전',
        intent: 'info' as const,
      },
    ],
    [],
  );

  return (
    <div className="space-y-2 text-sm text-gray-300">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className="rounded-lg border border-gray-600 bg-[#1a1a1a] px-2 py-2"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold text-white">{alert.title}</p>
              <p className="mt-1 text-[11px] text-gray-400">{alert.description}</p>
            </div>
            <span
              className={cn(
                'mt-0.5 inline-flex h-2 w-2 rounded-full',
                alert.intent === 'warning' && 'bg-amber-400',
                alert.intent === 'success' && 'bg-emerald-400',
                alert.intent === 'info' && 'bg-blue-400',
              )}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export function QuickActionPanel({
  className,
  defaultTab = 'watch',
  onStockSelect,
  isSheet = false,
  onClose,
}: QuickActionPanelProps) {
  const [activeTab, setActiveTab] = useState<'watch' | 'trade' | 'alerts'>(defaultTab);

  return (
    <div className={cn(
      'flex h-full flex-col bg-[#1a1a1b]',
      isSheet
        ? 'w-full rounded-t-3xl border border-gray-700/60 border-b-0 shadow-[0_-10px_30px_rgba(15,15,15,0.5)]'
        : 'w-80 border-r border-gray-700',
      className
    )}>
      {isSheet && (
        <div className="flex items-center justify-between px-3 pb-2 pt-3">
          <div className="mx-auto h-1.5 w-12 rounded-full bg-gray-600" />
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              className="absolute right-6 top-5 text-gray-500 transition-colors hover:text-gray-300"
              aria-label="빠른 작업 패널 닫기"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      )}

      {/* 탭 네비게이션 */}
      <div className="flex border-b border-gray-700 px-1">
        <TabButton
          active={activeTab === 'watch'}
          onClick={() => setActiveTab('watch')}
          icon={Eye}
          label="감시"
        />
        <TabButton
          active={activeTab === 'trade'}
          onClick={() => setActiveTab('trade')}
          icon={Target}
          label="매매"
        />
        <TabButton
          active={activeTab === 'alerts'}
          onClick={() => setActiveTab('alerts')}
          icon={Bell}
          label="알림"
        />
      </div>

      {/* 탭 콘텐츠 */}
      <div className={cn('flex-1 overflow-y-auto px-2 py-2', isSheet && 'pb-6')}>
        {activeTab === 'watch' && <WatchlistQuick />}
        {activeTab === 'trade' && (
          <div className="space-y-2">
            <TradingQuick onStockSelect={onStockSelect} />
            <TradingConditions className="w-full shadow-none" />
          </div>
        )}
        {activeTab === 'alerts' && <AlertsPanel />}
      </div>
    </div>
  );
}
