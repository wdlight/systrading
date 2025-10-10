'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useMarketData } from '@/hooks/useMarketData';
import { cn, formatCurrency, formatNumber, formatPercentage } from '@/lib/utils';
import { Globe, TrendingDown, TrendingUp } from 'lucide-react';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';

interface MarketOverviewProps {
  className?: string;
  compact?: boolean;
}

interface MarketDatum {
  name: string;
  value: number;
  change: number;
  changeRate: number;
  waiting: boolean;
}

export function MarketOverview({ className, compact = false }: MarketOverviewProps) {
  const { marketOverview, isLoading, error } = useMarketData();

  const marketData: MarketDatum[] = marketOverview
    ? [
        {
          name: 'KOSPI',
          value: marketOverview.kospi.current,
          change: marketOverview.kospi.change,
          changeRate: marketOverview.kospi.change_rate,
          waiting: marketOverview.kospi.current === 0,
        },
        {
          name: 'KOSDAQ',
          value: marketOverview.kosdaq.current,
          change: marketOverview.kosdaq.change,
          changeRate: marketOverview.kosdaq.change_rate,
          waiting: marketOverview.kosdaq.current === 0,
        },
        {
          name: 'NASDAQ',
          value: marketOverview.nasdaq.current,
          change: marketOverview.nasdaq.change,
          changeRate: marketOverview.nasdaq.change_rate,
          waiting: marketOverview.nasdaq.current === 0,
        },
        {
          name: 'S&P 500',
          value: marketOverview.sp500.current,
          change: marketOverview.sp500.change,
          changeRate: marketOverview.sp500.change_rate,
          waiting: marketOverview.sp500.current === 0,
        },
        {
          name: 'USD/KRW',
          value: marketOverview.usd_krw.current,
          change: marketOverview.usd_krw.change,
          changeRate: marketOverview.usd_krw.change_rate,
          waiting: marketOverview.usd_krw.current === 0,
        },
      ]
    : [];

  const topStocks = marketOverview
    ? [
        ...(marketOverview.top_gainers || []).map((stock) => ({ ...stock, trend: 'up' as const })),
        ...(marketOverview.top_losers || []).map((stock) => ({ ...stock, trend: 'down' as const })),
      ]
    : [];

  if (compact) {
    if (isLoading) {
      return (
        <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
          <CardContent className="flex items-center gap-3 overflow-hidden px-3 py-2.5">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-8 w-20 animate-pulse rounded-md bg-gray-700/60" />
            ))}
          </CardContent>
        </Card>
      );
    }

    if (error || !marketOverview) {
      return (
        <Card className={cn('bg-[#1a1a1b] border-gray-700', className)}>
          <CardContent className="px-3 py-2.5">
            <p className="text-[11px] text-gray-400">
              {error ?? '시장 데이터를 불러올 수 없습니다. 잠시 후 다시 시도해주세요.'}
            </p>
          </CardContent>
        </Card>
      );
    }

    return (
      <Card className={cn('bg-[#1a1a1b] border-gray-700 gap-2 py-1', className)}>
        <CardContent className="flex items-center gap-3 overflow-x-auto px-3 py-1 scrollbar-hide">
          {marketData.map((market) => (
            <CompactIndexCard
              key={market.name}
              name={market.name}
              value={market.value}
              change={market.change}
              changeRate={market.changeRate}
            />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={cn('bg-[#2a2a2a] border-gray-700', className)}>
        <CardHeader>
          <CardTitle>Loading Market Data...</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-40 animate-pulse rounded-lg bg-gray-700/50" />
        </CardContent>
      </Card>
    );
  }

  if (error || !marketOverview) {
    return (
      <Card className={cn('bg-[#2a2a2a] border-gray-700', className)}>
        <CardHeader>
          <CardTitle>Market Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <ErrorState description={error ?? '시장 데이터가 비어 있습니다.'} />
        </CardContent>
      </Card>
    );
  }

  const hasTopStocks = topStocks.length > 0;

  return (
    <Card className={cn('bg-[#2a2a2a] border-gray-700 shadow-xl gap-2 py-1', className)}>
      <CardHeader className="px-3 pb-2">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20">
            <Globe className="h-4 w-4 text-blue-400" />
          </div>
          <div>
            <CardTitle className="text-lg font-bold text-white">Market Overview</CardTitle>
            <p className="text-xs text-gray-400">Real-time market data and trends</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4 px-3 py-1">
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div>
            <h4 className="mb-3 flex items-center gap-2 border-b border-blue-500/70 pb-2 text-sm font-bold uppercase tracking-wide text-white">
              📈 Major Indices
            </h4>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              {marketData.map((market) => (
                <div
                  key={market.name}
                  className="rounded-lg border border-gray-600 bg-[#1a1a1a] p-3 transition-all duration-200 hover:border-gray-500"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wide text-gray-300">
                      {market.name}
                    </span>
                    <div
                      className={cn(
                        'flex h-6 w-6 items-center justify-center rounded-full',
                        market.change >= 0 ? 'bg-profit/20' : 'bg-loss/20',
                      )}
                    >
                      {market.change >= 0 ? (
                        <TrendingUp className="h-3 w-3 text-profit-foreground" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-loss-foreground" />
                      )}
                    </div>
                  </div>
                  <div className="mb-0.5 text-base font-semibold text-white">
                    {formatNumber(market.value, { decimals: 2 })}
                  </div>
                  <div
                    className={cn(
                      'text-xs font-semibold',
                      market.change >= 0 ? 'text-profit-foreground' : 'text-loss-foreground',
                    )}
                  >
                    {market.change > 0 ? '+' : ''}
                    {formatNumber(market.change, { decimals: 2 })} ({formatPercentage(market.changeRate)})
                  </div>
                  {market.waiting && (
                    <div className="mt-1 text-[11px] text-amber-400">실시간 데이터 수신 대기 중</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="mb-3 flex items-center gap-2 border-b border-amber-500/70 pb-2 text-sm font-bold uppercase tracking-wide text-white">
              🚀 Top Movers
            </h4>
            {hasTopStocks ? (
              <div className="space-y-1.5">
                {topStocks.map((stock, index) => (
                  <div
                    key={`${stock.stock_code}-${stock.trend}`}
                    className="flex items-center justify-between rounded-lg border border-gray-600 bg-[#1a1a1a] p-2.5 transition-all duration-200 hover:border-gray-500"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={cn(
                          'flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white',
                          index < 3 ? 'bg-amber-500/90' : 'bg-gray-600/70',
                        )}
                      >
                        {index + 1}
                      </div>
                      <div
                        className={cn(
                          'flex h-8 w-8 items-center justify-center rounded-full',
                          stock.trend === 'up' ? 'bg-profit/20' : 'bg-loss/20',
                        )}
                      >
                        {stock.trend === 'up' ? (
                          <TrendingUp className="h-3 w-3 text-profit-foreground" />
                        ) : (
                          <TrendingDown className="h-3 w-3 text-loss-foreground" />
                        )}
                      </div>
                      <div>
                        <div className="text-sm font-semibold text-white">{stock.stock_name}</div>
                        <div className="font-mono text-xs text-gray-400">{stock.stock_code}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-semibold text-gray-200">
                        {formatCurrency(stock.current_price)}
                      </div>
                      <div
                        className={cn(
                          'text-xs font-semibold',
                          stock.trend === 'up'
                            ? 'text-profit-foreground'
                            : 'text-loss-foreground',
                        )}
                      >
                        {formatPercentage(stock.change_rate)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="상위 변동 종목이 없습니다"
                description="시장 데이터가 새로 업데이트되면 변동성이 높은 종목을 우선적으로 보여드립니다."
              />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function CompactIndexCard({
  name,
  value,
  change,
  changeRate,
}: {
  name: string;
  value: number;
  change: number;
  changeRate: number;
}) {
  const isUp = change >= 0;

  return (
    <div className="flex min-w-[108px] items-center gap-2.5 whitespace-nowrap">
      <div className="text-[11px] font-medium text-gray-400">{name}</div>
      <div className="text-xs font-semibold text-white">
        {formatNumber(value, { decimals: 2 })}
      </div>
      <div
        className={cn(
          'text-[11px] font-semibold',
          isUp ? 'text-profit-foreground' : 'text-loss-foreground',
        )}
      >
        {formatPercentage(changeRate)}
      </div>
    </div>
  );
}
