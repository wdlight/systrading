'use client';

import { useState } from 'react';
import { Eye, Target, Bell } from 'lucide-react';
import { TabButton } from './TabButton';
import { TradingQuick } from '@/components/trading/TradingQuick';
import { QuickActionPanelProps } from '@/lib/types/components';
import { cn } from '@/lib/utils';

// 임시 컴포넌트들 (실제 구현은 나중에)
function WatchlistQuick() {
  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-300">
        <h3 className="font-semibold text-white mb-3">관심종목</h3>
        <div className="space-y-2">
          <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-white font-medium">삼성전자</span>
                <span className="text-gray-400 text-xs ml-2">005930</span>
              </div>
              <div className="text-right">
                <div className="text-white font-medium">73,000원</div>
                <div className="text-profit-foreground text-xs">+1.5%</div>
              </div>
            </div>
          </div>
          <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-white font-medium">SK하이닉스</span>
                <span className="text-gray-400 text-xs ml-2">000660</span>
              </div>
              <div className="text-right">
                <div className="text-white font-medium">127,500원</div>
                <div className="text-loss-foreground text-xs">-2.1%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


function AlertsPanel() {
  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-300">
        <h3 className="font-semibold text-white mb-3">알림</h3>
        <div className="space-y-2">
          <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium text-xs">RSI 과매수</div>
                <div className="text-gray-400 text-xs">삼성전자 • 5분 전</div>
              </div>
              <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
            </div>
          </div>
          <div className="p-3 bg-[#1a1a1a] rounded-lg border border-gray-600">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium text-xs">MACD 골든크로스</div>
                <div className="text-gray-400 text-xs">SK하이닉스 • 10분 전</div>
              </div>
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function QuickActionPanel({
  className,
  defaultTab = 'watch',
  onStockSelect
}: QuickActionPanelProps) {
  const [activeTab, setActiveTab] = useState<'watch' | 'trade' | 'alerts'>(defaultTab);

  return (
    <div className={cn(
      'w-80 bg-[#1a1a1b] border-l border-gray-700 h-full flex flex-col',
      className
    )}>
      {/* 탭 네비게이션 */}
      <div className="flex border-b border-gray-700">
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
      <div className="flex-1 p-4 overflow-y-auto">
        {activeTab === 'watch' && <WatchlistQuick />}
        {activeTab === 'trade' && <TradingQuick onStockSelect={onStockSelect} />}
        {activeTab === 'alerts' && <AlertsPanel />}
      </div>
    </div>
  );
}