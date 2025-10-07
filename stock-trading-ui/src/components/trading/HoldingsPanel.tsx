'use client';

import { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useAccountData } from '@/hooks/useAccountData';
import { cn, formatCurrency, formatNumber, formatPercentage } from '@/lib/utils';
import { Briefcase } from 'lucide-react';
import { Position } from '@/lib/types';

export function HoldingsPanel({ className }: { className?: string }) {
  const { accountBalance, isLoading, error } = useAccountData();

  const holdings = useMemo(() => {
    const positions = accountBalance?.positions || [];
    return positions;
  }, [accountBalance]);

  if (isLoading) {
    return <Card className={cn(className, "bg-[#2a2a2a] border-gray-700")}><CardHeader><CardTitle>Loading Holdings...</CardTitle></CardHeader><CardContent><div className="animate-pulse h-40 bg-gray-700/50 rounded-lg" /></CardContent></Card>;
  }

  return (
    <Card className={cn(className, "bg-[#2a2a2a] border-gray-700 shadow-xl")}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="icon-bg-green">
              <Briefcase className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-heading-md text-white">My Holdings</h3>
              <p className="text-caption-md text-gray-400">{holdings.length} stocks</p>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && <div className="text-red-400">Error: {error}</div>}
        {holdings.length === 0 ? (
          <div className="text-center py-12 text-gray-500">No holdings to display.</div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="text-xs border-gray-600">
                  <TableHead className="text-gray-300 font-semibold">Stock</TableHead>
                  <TableHead className="text-right text-gray-300 font-semibold">Quantity</TableHead>
                  <TableHead className="text-right text-gray-300 font-semibold">Avg. Price</TableHead>
                  <TableHead className="text-right text-gray-300 font-semibold">Current Price</TableHead>
                  <TableHead className="text-right text-gray-300 font-semibold">P/L</TableHead>
                  <TableHead className="text-right text-gray-300 font-semibold">Return %</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {holdings.map((pos) => (
                  <HoldingRow key={pos.stock_code} position={pos} />
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
        <div className="font-medium text-gray-100">{position.stock_name}</div>
        <div className="font-mono text-gray-400">{position.stock_code}</div>
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
