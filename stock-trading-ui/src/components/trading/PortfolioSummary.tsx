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
    <Card className={cn(className, "card-professional-elevated")}>
      <CardHeader className="pb-5">
        <CardTitle className="flex items-center gap-4 text-primary-pro">
          <div className="icon-bg-blue">
            <DollarSign className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <h2 className="text-heading-md">포트폴리오 요약</h2>
            <p className="text-caption-md text-secondary-pro">
              현재 평가금액: <span className="text-financial-xs font-bold">{formatCurrency(accountBalance.total_evaluation_amount)}</span>
            </p>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-section">
        <div className="grid grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-3 lg:gap-4">
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
          <div className="mt-8 pt-6 border-t border-professional">
            <h4 className="text-heading-sm text-primary-pro mb-5">
              포트폴리오 지표
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
              <StatItem
                label="승률"
                value={`${portfolioStats.win_rate}%`}
                color={portfolioStats.win_rate >= 50 ? 'profit' : 'loss'}
              />
              <StatItem
                label="다각화 점수"
                value={`${portfolioStats.diversification_score}/100`}
                color={portfolioStats.diversification_score >= 70 ? 'profit' : 'yellow'}
              />
              <StatItem
                label="위험 점수"
                value={`${portfolioStats.risk_score}/100`}
                color={portfolioStats.risk_score <= 30 ? 'profit' : portfolioStats.risk_score <= 70 ? 'yellow' : 'loss'}
              />
              <StatItem
                label="최대 낙폭"
                value={formatPercentage(portfolioStats.max_drawdown)}
                color={portfolioStats.max_drawdown >= -10 ? 'profit' : 'loss'}
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

  // Professional card styling based on type and direction
  const getCardClasses = () => {
    const baseClasses = 'card-professional-interactive p-4 rounded-xl transition-all duration-300';

    if (title === '총 자산' || title === '가용 현금') {
      return cn(baseClasses, 'metric-card-blue');
    }
    if (title === '일일 손익') {
      return cn(baseClasses, direction === 'up' ? 'metric-card-red' : 'metric-card-green');
    }
    if (title === '총 손익') {
      return cn(baseClasses, direction === 'up' ? 'metric-card-red' : direction === 'down' ? 'metric-card-green' : 'metric-card-purple');
    }
    return cn(baseClasses, 'metric-card-cyan');
  };

  // Professional icon background styling
  const getIconClasses = () => {
    if (title === '총 자산' || title === '가용 현금') return 'icon-bg-blue';
    if (title === '일일 손익') return direction === 'up' ? 'icon-bg-red' : 'icon-bg-green';
    if (title === '총 손익') return direction === 'up' ? 'icon-bg-red' : direction === 'down' ? 'icon-bg-green' : 'icon-bg-purple';
    return 'icon-bg-cyan';
  };

  // Professional text colors
  const getChangeTextColor = () => {
    if (direction === 'up') return 'text-profit-foreground';
    if (direction === 'down') return 'text-loss-foreground';
    return 'text-zinc-400';
  };

  return (
    <div className={getCardClasses()}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-secondary-pro truncate">
          {title}
        </span>
        <div className={getIconClasses()}>
          <Icon className="h-3 w-3 flex-shrink-0" />
        </div>
      </div>

      <div className="space-y-2">
        <div className="text-sm font-bold text-primary-pro truncate">
          {formatCurrency(value)}
        </div>

        {(change !== 0 || changeRate !== 0) && (
          <div className={cn('text-xs font-medium', getChangeTextColor())}>
            <div className="truncate">
              {change > 0 ? '+' : ''}{formatCurrency(change)}
            </div>
            <div className="text-xs opacity-75">
              ({formatPercentage(changeRate, { showSign: false })})
            </div>
          </div>
        )}

        <div className="text-xs text-muted-pro opacity-80 truncate">
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
  color: 'profit' | 'yellow' | 'loss';
}) {
  const colorClasses = {
    profit: 'text-profit-foreground',
    yellow: 'text-amber-400',
    loss: 'text-loss-foreground',
  };

  const bgClasses = {
    profit: 'bg-profit/10',
    yellow: 'bg-amber-500/10',
    loss: 'bg-loss/10',
  };

  return (
    <div className={cn('text-center p-4 rounded-lg border border-professional transition-all duration-300', bgClasses[color])}>
      <div className="text-caption-md text-muted-pro mb-3">
        {label}
      </div>
      <div className={cn('text-financial-sm', colorClasses[color])}>
        {value}
      </div>
    </div>
  );
}