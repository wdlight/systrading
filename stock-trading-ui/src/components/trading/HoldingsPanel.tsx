'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAccountData } from '@/hooks/useAccountData';
import { cn, formatCurrency, formatNumber, formatPercentage } from '@/lib/utils';
import { Briefcase } from 'lucide-react';
import { Position } from '@/lib/types';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';

interface HoldingsCardProps {
  className?: string;
  positions: Position[];
  isLoading?: boolean;
  error?: string | null;
}

export function HoldingsPanel({ className }: { className?: string }) {
  const { accountBalance, isLoading, error } = useAccountData();

  const positions = useMemo(() => accountBalance?.positions ?? [], [accountBalance]);

  return (
    <HoldingsCard
      className={className}
      positions={positions}
      isLoading={isLoading}
      error={error}
    />
  );
}

export function HoldingsCard({ className, positions, isLoading, error }: HoldingsCardProps) {
  if (isLoading) {
    return (
      <Card className={cn('bg-[#2a2a2a] border-gray-700 gap-1 py-1', className)}>
        <CardHeader className="px-3 pb-1">
          <CardTitle>Loading Holdings...</CardTitle>
        </CardHeader>
        <CardContent className="px-3 py-1">
          <div className="h-40 animate-pulse rounded-lg bg-gray-700/50" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('bg-[#2a2a2a] border-gray-700 shadow-xl gap-1 py-1', className)}>
      <CardHeader className="px-3 pb-1">
        <div className="flex items-center gap-2">
          <div className="icon-bg-green">
            <Briefcase className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-heading-md text-white">My Holdings</h3>
            <p className="text-caption-md text-gray-400">{positions.length} stocks</p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="px-3 py-1">
        {error ? (
          <ErrorState description={error} />
        ) : positions.length === 0 ? (
          <EmptyState
            title="보유 중인 종목이 없습니다"
            description="첫 포지션을 추가하면 포트폴리오 요약 및 차트에서 실시간으로 반영됩니다."
          />
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-gray-600 text-xs">
                  <TableHead className="font-semibold text-gray-300">Stock</TableHead>
                  <TableHead className="text-right font-semibold text-gray-300">Quantity</TableHead>
                  <TableHead className="text-right font-semibold text-gray-300">Avg. Price</TableHead>
                  <TableHead className="text-right font-semibold text-gray-300">Current Price</TableHead>
                  <TableHead className="text-right font-semibold text-gray-300">P/L</TableHead>
                  <TableHead className="text-right font-semibold text-gray-300">Return %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {positions.map((position) => (
                  <HoldingRow key={position.stock_code} position={position} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function HoldingRow({ position }: { position: Position }) {
  const isProfit = position.profit_loss > 0;
  const isLoss = position.profit_loss < 0;
  const directionColor = isProfit ? 'text-profit-foreground' : isLoss ? 'text-loss-foreground' : 'text-gray-400';

  return (
    <TableRow className="text-xs hover:bg-gray-700/50 border-gray-700">
      <TableCell>
        <div className="font-medium text-gray-100">
          {position.stock_name}
          <span className="ml-1 font-mono text-[11px] text-gray-400">({position.stock_code})</span>
        </div>
      </TableCell>
      <TableCell className="text-right font-mono text-gray-200">{formatNumber(position.quantity)}</TableCell>
      <TableCell className="text-right font-mono text-gray-200">{formatCurrency(position.avg_price)}</TableCell>
      <TableCell className="text-right font-mono text-gray-200">{formatCurrency(position.current_price)}</TableCell>
      <TableCell className={cn("text-right font-mono", directionColor)}>
        {formatCurrency(position.profit_loss, { showSign: true })}
      </TableCell>
      <TableCell className={cn("text-right font-mono", directionColor)}>
        {formatPercentage(position.profit_rate)}
      </TableCell>
    </TableRow>
  );
}
