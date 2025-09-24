'use client';

import { useMemo } from 'react';
import { cn, formatCurrency, formatPercentage, getPriceDirection, getDirectionIcon } from '@/lib/utils';
import { TRADING_COLORS } from '@/lib/constants';

interface PriceDisplayProps {
  current: number;
  previous?: number;
  change?: number;
  changeRate?: number;
  currency?: string;
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  showChange?: boolean;
  animate?: boolean;
  className?: string;
}

export function PriceDisplay({
  current,
  previous,
  change,
  changeRate,
  currency = 'KRW',
  size = 'md',
  showIcon = true,
  showChange = true,
  animate = true,
  className,
}: PriceDisplayProps) {
  const direction = useMemo(() => {
    if (change !== undefined) {
      return change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';
    }
    if (previous !== undefined) {
      return getPriceDirection(current, previous);
    }
    return 'neutral';
  }, [current, previous, change]);

  const actualChange = change ?? (previous ? current - previous : 0);
  const actualChangeRate = changeRate ?? (previous && previous !== 0 ? ((current - previous) / previous) * 100 : 0);

  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
  };

  const colorClasses = {
    up: 'text-green-600 dark:text-green-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-gray-700 dark:text-gray-300',
  };

  const bgColorClasses = {
    up: 'bg-green-50 dark:bg-green-900/20',
    down: 'bg-red-50 dark:bg-red-900/20',
    neutral: 'bg-gray-50 dark:bg-gray-900/20',
  };

  return (
    <div className={cn(
      'inline-flex items-center gap-1 px-2 py-1 rounded-md transition-all duration-300',
      bgColorClasses[direction],
      animate && 'animate-pulse-once',
      className
    )}>
      {/* 현재가 */}
      <span className={cn(
        'font-mono font-semibold',
        sizeClasses[size],
        colorClasses[direction]
      )}>
        {formatCurrency(current, { currency })}
      </span>

      {/* 변동 표시 */}
      {showChange && (actualChange !== 0 || actualChangeRate !== 0) && (
        <div className={cn(
          'flex items-center gap-1 text-xs',
          colorClasses[direction]
        )}>
          {/* 방향 아이콘 */}
          {showIcon && (
            <span className={cn(
              'text-xs',
              animate && direction !== 'neutral' && 'animate-bounce-once'
            )}>
              {getDirectionIcon(direction)}
            </span>
          )}

          {/* 변동량 */}
          <span className="font-mono">
            {formatCurrency(Math.abs(actualChange), { 
              currency, 
              showSign: false 
            })}
          </span>

          {/* 변동률 */}
          <span className="font-mono">
            ({formatPercentage(actualChangeRate, { showSign: false })})
          </span>
        </div>
      )}
    </div>
  );
}

// 컴팩트 버전 (테이블용)
export function CompactPriceDisplay({
  current,
  changeRate,
  size = 'sm',
  className,
}: {
  current: number;
  changeRate: number;
  size?: 'sm' | 'md';
  className?: string;
}) {
  const direction = changeRate > 0 ? 'up' : changeRate < 0 ? 'down' : 'neutral';

  const sizeClasses = {
    sm: 'text-xs',
    md: 'text-sm',
  };

  const colorClasses = {
    up: 'text-green-500 dark:text-green-400',
    down: 'text-red-500 dark:text-red-400',
    neutral: 'text-gray-700 dark:text-gray-300',
  };

  return (
    <div className={cn('flex flex-col items-center gap-0.5', className)}>
      {/* 현재가 */}
      <span className={cn(
        'font-mono font-medium',
        sizeClasses[size],
        'text-gray-100'
      )}>
        {formatCurrency(current, { currency: 'KRW', compact: false })}
      </span>

      {/* 변동률 */}
      <div className={cn(
        'flex items-center gap-1',
        sizeClasses[size],
        colorClasses[direction]
      )}>
        <span className="text-xs">
          {getDirectionIcon(direction)}
        </span>
        <span className="font-mono">
          {formatPercentage(changeRate, { showSign: false })}
        </span>
      </div>
    </div>
  );
}

// 대형 가격 표시 (대시보드용)
export function LargePriceDisplay({
  current,
  change,
  changeRate,
  label,
  currency = 'KRW',
  className,
}: {
  current: number;
  change: number;
  changeRate: number;
  label?: string;
  currency?: string;
  className?: string;
}) {
  const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'neutral';

  const colorClasses = {
    up: 'text-green-600 dark:text-green-400',
    down: 'text-red-600 dark:text-red-400',
    neutral: 'text-gray-700 dark:text-gray-300',
  };

  const bgColorClasses = {
    up: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    down: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800',
    neutral: 'bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800',
  };

  return (
    <div className={cn(
      'p-4 rounded-lg border-2 transition-all duration-300',
      bgColorClasses[direction],
      className
    )}>
      {label && (
        <div className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          {label}
        </div>
      )}
      
      <div className="flex items-baseline gap-3">
        {/* 현재가 */}
        <span className="text-2xl font-mono font-bold text-gray-900 dark:text-gray-100">
          {formatCurrency(current, { currency })}
        </span>

        {/* 변동 정보 */}
        <div className={cn(
          'flex items-center gap-2 text-lg',
          colorClasses[direction]
        )}>
          <span className="animate-bounce-once">
            {getDirectionIcon(direction)}
          </span>
          <span className="font-mono font-semibold">
            {formatCurrency(Math.abs(change), { currency, showSign: false })}
          </span>
          <span className="font-mono">
            ({formatPercentage(changeRate, { showSign: false })})
          </span>
        </div>
      </div>
    </div>
  );
}