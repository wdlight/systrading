'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LargePriceDisplay } from '@/components/common/PriceDisplay';
import { useAccountData } from '@/hooks/useAccountData';
import { cn, formatCurrency, formatPercentage } from '@/lib/utils';
import { TrendingUp, TrendingDown, DollarSign, Circle } from 'lucide-react';

interface PortfolioSummaryProps {
  className?: string;
}

export function PortfolioSummary({ className }: PortfolioSummaryProps) {
  const { accountBalance, portfolioStats, isLoading } = useAccountData();

  const summaryCards = useMemo(() => {
    if (!accountBalance || !portfolioStats) return [];

    return [
      {
        title: '총 자산',
        value: accountBalance.total_evaluation_amount,
        change: portfolioStats.daily_pnl,
        changeRate: portfolioStats.daily_pnl_rate,
        icon: DollarSign,
        description: '평가금액 기준',
      },
      {
        title: '일일 손익',
        value: portfolioStats.daily_pnl,
        change: portfolioStats.daily_pnl,
        changeRate: portfolioStats.daily_pnl_rate,
        icon: portfolioStats.daily_pnl >= 0 ? TrendingUp : TrendingDown,
        description: '오늘 수익률',
      },
      {
        title: '총 손익',
        value: accountBalance.total_profit_loss,
        change: accountBalance.total_profit_loss,
        changeRate: accountBalance.total_profit_loss_rate,
        icon: Circle,
        description: '누적 수익률',
      },
      {
        title: '가용 현금',
        value: accountBalance.available_cash,
        change: 0,
        changeRate: 0,
        icon: DollarSign,
        description: '투자 가능 금액',
      },
    ];
  }, [accountBalance, portfolioStats]);

  if (isLoading) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            포트폴리오 요약
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded-lg" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!accountBalance) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-5 w-5" />
            포트폴리오 요약
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            데이터를 불러올 수 없습니다.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn(className, "bg-[#2a2a2a] border-gray-700")}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <DollarSign className="h-5 w-5 text-blue-400" />
          포트폴리오 요약
        </CardTitle>
        <div className="text-sm text-gray-300">
          현재 평가금액: {formatCurrency(accountBalance.total_evaluation_amount)}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {summaryCards.map((card, index) => (
            <SummaryCard
              key={index}
              title={card.title}
              value={card.value}
              change={card.change}
              changeRate={card.changeRate}
              icon={card.icon}
              description={card.description}
            />
          ))}
        </div>

        {/* 포트폴리오 통계 */}
        {portfolioStats && (
          <div className="mt-6 pt-6 border-t border-gray-600">
            <h4 className="text-sm font-medium text-white mb-3">
              포트폴리오 지표
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatItem
                label="승률"
                value={`${portfolioStats.win_rate}%`}
                color={portfolioStats.win_rate >= 50 ? 'green' : 'red'}
              />
              <StatItem
                label="다각화 점수"
                value={`${portfolioStats.diversification_score}/100`}
                color={portfolioStats.diversification_score >= 70 ? 'green' : 'yellow'}
              />
              <StatItem
                label="위험 점수"
                value={`${portfolioStats.risk_score}/100`}
                color={portfolioStats.risk_score <= 30 ? 'green' : portfolioStats.risk_score <= 70 ? 'yellow' : 'red'}
              />
              <StatItem
                label="최대 낙폭"
                value={formatPercentage(portfolioStats.max_drawdown)}
                color={portfolioStats.max_drawdown >= -10 ? 'green' : 'red'}
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function SummaryCard({
  title,
  value,
  change,
  changeRate,
  icon: Icon,
  description,
}: {
  title: string;
  value: number;
  change: number;
  changeRate: number;
  icon: any;
  description: string;
}) {
  const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';

  const colorClasses = {
    up: 'text-green-400 bg-[#2a2a2a] border-green-500/30',
    down: 'text-red-400 bg-[#2a2a2a] border-red-500/30',
    neutral: 'text-gray-300 bg-[#2a2a2a] border-gray-600/30',
  };

  // 아이콘 색상 결정
  const getIconColor = () => {
    if (title === '총 자산' || title === '가용 현금') return 'text-blue-400';
    if (title === '일일 손익') return direction === 'up' ? 'text-green-400' : 'text-red-400';
    if (title === '총 손익') return 'text-purple-400';
    return 'text-gray-400';
  };

  return (
    <div className={cn(
      'p-3 rounded-lg border transition-all duration-300 hover:shadow-md',
      colorClasses[direction]
    )}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-300">
          {title}
        </span>
        <Icon className={cn("h-4 w-4", getIconColor())} />
      </div>

      <div className="space-y-1">
        <div className="text-lg font-bold text-white">
          {formatCurrency(value)}
        </div>

        {(change !== 0 || changeRate !== 0) && (
          <div className={cn('text-sm font-medium',
            direction === 'up' ? 'text-green-400' :
            direction === 'down' ? 'text-red-400' :
            'text-gray-300'
          )}>
            {change > 0 ? '+' : ''}{formatCurrency(change)} ({formatPercentage(changeRate, { showSign: false })})
          </div>
        )}

        <div className="text-xs text-gray-400">
          {description}
        </div>
      </div>
    </div>
  );
}

function StatItem({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: 'green' | 'yellow' | 'red';
}) {
  const colorClasses = {
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
  };

  return (
    <div className="text-center">
      <div className="text-xs text-gray-400 mb-1">
        {label}
      </div>
      <div className={cn('text-sm font-semibold', colorClasses[color])}>
        {value}
      </div>
    </div>
  );
}