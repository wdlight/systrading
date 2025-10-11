'use client';

import dynamic from 'next/dynamic';
import { useMemo, useState } from 'react';
import { Card } from '@/components/ui/card';
import { BarChart3 } from 'lucide-react';
import { TabButton } from '@/components/layout/TabButton';
import { usePortfolioHistory } from '@/hooks/usePortfolioHistory';
import type {
  AccountBalance,
  PortfolioPerformanceMetrics,
  PortfolioStats,
  PortfolioTimeRange,
} from '@/lib/types';
import { cn, formatCurrency, formatPercentage } from '@/lib/utils';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';

const PerformanceChart = dynamic(() => import('./PortfolioPerformanceChart'), {
  ssr: false,
  loading: () => (
    <div className="flex h-[320px] w-full items-center justify-center rounded-xl border border-gray-700 bg-[#1a1a1a]">
      <div className="h-12 w-12 animate-spin rounded-full border-2 border-blue-500/60 border-t-transparent" />
    </div>
  ),
});

const TIME_RANGES: PortfolioTimeRange[] = ['1D', '1W', '1M', '3M', '6M', '1Y', 'ALL'];
const NoIcon = () => null;

interface PortfolioPerformanceProps {
  className?: string;
  stats?: PortfolioStats | null;
  accountBalance?: AccountBalance | null;
}

interface KpiItem {
  label: string;
  value: string;
  intent: 'positive' | 'negative' | 'info' | 'neutral';
}

function formatMetric(
  value: number | null | undefined,
  options: { suffix?: string; sign?: boolean } = {},
): string {
  const { suffix = '', sign = true } = options;

  if (value == null || Number.isNaN(value)) {
    return '-';
  }

  const signPrefix = sign && value > 0 ? '+' : '';
  return `${signPrefix}${value.toFixed(2)}${suffix}`;
}

function buildKpiItems(
  metrics: PortfolioPerformanceMetrics,
  stats?: PortfolioStats | null,
): KpiItem[] {
  const totalReturn = stats?.total_pnl_rate ?? metrics.totalReturn;
  const maxDrawdown = stats?.max_drawdown ?? metrics.maxDrawdown;
  const volatility = stats?.volatility ?? metrics.volatility;
  const winRate = stats?.win_rate ?? null;

  const items: KpiItem[] = [
    {
      label: '총 수익률',
      value: formatMetric(totalReturn, { suffix: '%', sign: true }),
      intent: totalReturn != null && totalReturn >= 0 ? 'positive' : 'negative',
    },
    {
      label: '최대 낙폭',
      value: formatMetric(maxDrawdown, { suffix: '%', sign: true }),
      intent: 'neutral',
    },
    {
      label: '연환산 변동성',
      value: formatMetric(volatility, { suffix: '%', sign: false }),
      intent: 'info',
    },
  ];

  if (winRate != null) {
    items.push({
      label: '승률',
      value: formatMetric(winRate, { suffix: '%', sign: false }),
      intent: 'positive',
    });
  }

  return items;
}

function SummaryDivider() {
  return <div className="hidden h-4 w-px bg-gray-700/80 sm:block" />;
}

export function PortfolioPerformance({ className, stats, accountBalance }: PortfolioPerformanceProps) {
  const [timeRange, setTimeRange] = useState<PortfolioTimeRange>('6M');
  const { history, metrics, isLoading, error, usingMock } = usePortfolioHistory(timeRange);

  const chartData = useMemo(() => history, [history]);
  const kpis = useMemo(() => buildKpiItems(metrics, stats), [metrics, stats]);

  const totalValue = accountBalance?.total_evaluation_amount ?? stats?.total_value ?? null;
  const totalReturnRate = accountBalance?.total_profit_loss_rate ?? stats?.total_pnl_rate ?? null;
  const dailyPnl = stats?.daily_pnl ?? null;
  const dailyPnlRate = stats?.daily_pnl_rate ?? null;
  const availableCash = accountBalance?.available_cash ?? null;
  const positionCount = accountBalance?.positions?.length ?? null;
  const summaryAvailable = accountBalance != null || stats != null;

  return (
    <Card className={cn('bg-[#1a1a1b] border-gray-700 shadow-xl overflow-hidden gap-2 py-1', className)}>
      <div className="border-b border-gray-800/60 px-3 py-2 sm:px-4">
        {summaryAvailable ? (
          <div className="flex flex-col gap-2.5 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap items-center gap-3 sm:gap-5">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">총자산</span>
                <span className="text-base font-semibold text-white">
                  {totalValue != null ? formatCurrency(totalValue) : '-'}
                </span>
              </div>
              <SummaryDivider />
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">총 수익률</span>
                <span
                  className={cn(
                    'text-xs font-semibold',
                    (totalReturnRate ?? 0) >= 0 ? 'text-profit-foreground' : 'text-loss-foreground',
                  )}
                >
                  {totalReturnRate != null ? formatPercentage(totalReturnRate) : '-'}
                </span>
              </div>
              <SummaryDivider />
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">일일 손익</span>
                <span
                  className={cn(
                    'text-xs font-semibold',
                    (dailyPnl ?? 0) >= 0 ? 'text-profit-foreground' : 'text-loss-foreground',
                  )}
                >
                  {dailyPnl != null ? formatCurrency(dailyPnl, { showSign: true }) : '-'}
                </span>
                {dailyPnlRate != null && (
                  <span className="text-[11px] text-gray-500">({formatPercentage(dailyPnlRate)})</span>
                )}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3 text-[11px] text-gray-400">
              <div>
                가용 자금:
                <span className="ml-1 text-xs font-medium text-white">
                  {availableCash != null ? formatCurrency(availableCash) : '-'}
                </span>
              </div>
              <div>
                보유 종목:
                <span className="ml-1 text-xs font-medium text-white">
                  {positionCount != null ? `${positionCount}개` : '-'}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-400">포트폴리오 데이터를 불러오는 중...</div>
        )}
      </div>

      <div className="space-y-3.5 px-3 py-3 sm:px-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/15">
              <BarChart3 className="h-3 w-3 text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Portfolio Performance</p>
              <p className="text-[11px] text-gray-400">벤치마크 대비 누적 성과 추적</p>
            </div>
          </div>

          <div className="flex items-center gap-1 overflow-x-auto rounded-full border border-gray-700 bg-[#111827] p-1 text-[11px] font-semibold uppercase scrollbar-hide">
            {TIME_RANGES.map((range) => (
              <TabButton
                key={range}
                active={timeRange === range}
                onClick={() => setTimeRange(range)}
                icon={NoIcon}
                label={range}
                className="px-2.5 py-1"
              />
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-gray-700 bg-[#111827] p-3">
          {error && !chartData.length ? (
            <ErrorState description={error} />
          ) : !chartData.length && !isLoading ? (
            <EmptyState
              title="차트 데이터를 찾을 수 없습니다"
              description="기간을 변경하거나 잠시 후 다시 시도하세요."
            />
          ) : (
            <PerformanceChart data={chartData} timeRange={timeRange} />
          )}
          {usingMock && chartData.length > 0 && (
            <p className="mt-2 text-right text-[10px] text-amber-400">
              ⚠️ API 데이터가 준비되지 않아 샘플 데이터를 표시하고 있습니다.
            </p>
          )}
        </div>
      </div>

      <div className="border-t border-gray-800/60 bg-[#141414] px-3 py-2.5 sm:px-4">
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {kpis.map((item) => (
            <KpiCard key={item.label} label={item.label} value={item.value} intent={item.intent} />
          ))}
        </div>
      </div>
    </Card>
  );
}

function KpiCard({
  label,
  value,
  intent,
}: {
  label: string;
  value: string;
  intent: 'positive' | 'negative' | 'info' | 'neutral';
}) {
  return (
    <div className="rounded-lg border border-gray-700 bg-[#1a1a1a] p-2.5">
      <p className="text-[11px] font-medium uppercase tracking-wide text-gray-400">{label}</p>
      <p
        className={cn(
          'mt-1.5 text-base font-semibold text-white',
          intent === 'positive' && 'text-profit-foreground',
          intent === 'negative' && 'text-loss-foreground',
          intent === 'info' && 'text-blue-300',
        )}
      >
        {value}
      </p>
    </div>
  );
}
