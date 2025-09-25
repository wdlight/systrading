'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Activity, BarChart3 } from 'lucide-react';
import { Stock } from '@/lib/types/trading';
import { cn } from '@/lib/utils';

interface StockInfoCardProps {
  stock?: Stock | null;
  className?: string;
}

export function StockInfoCard({ stock, className }: StockInfoCardProps) {
  if (!stock) {
    return (
      <Card className={cn('bg-[#2a2a2a] border-gray-700', className)}>
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            종목 정보
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-400">
            <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>종목을 선택해주세요</p>
            <p className="text-sm">선택된 종목의 상세 정보가 여기에 표시됩니다.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const isPositive = stock.changeRate > 0;
  const isNeutral = stock.changeRate === 0;

  return (
    <Card className={cn('bg-[#2a2a2a] border-gray-700', className)}>
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          종목 정보
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* 기본 정보 */}
        <div className="space-y-3">
          <div>
            <h3 className="text-lg font-semibold text-white">{stock.name}</h3>
            <p className="text-sm text-gray-400">{stock.code}</p>
          </div>

          {/* 현재가 및 변동 */}
          <div className="p-4 bg-[#1a1a1a] rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">
                  {stock.currentPrice.toLocaleString()}원
                </div>
                <div className="flex items-center gap-2 mt-1">
                  {isPositive ? (
                    <TrendingUp className="w-4 h-4 text-profit-foreground" />
                  ) : isNeutral ? (
                    <Activity className="w-4 h-4 text-gray-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-loss-foreground" />
                  )}
                  <span className={cn("text-sm font-medium",
                    isPositive ? "text-profit-foreground" : isNeutral ? "text-gray-400" : "text-loss-foreground"
                  )}>
                </div>
              </div>
              <div className="text-right">
                <Badge
                  variant={isPositive ? "destructive" : isNeutral ? "secondary" : "default"}
                  className={cn(
                    "text-sm",
                    isPositive && "bg-profit hover:bg-profit/90",
                    isNeutral && "bg-gray-600"
                  )}>

              </div>
            </div>
          </div>
        </div>

        {/* 상세 정보 */}
        <div className="space-y-3">
          <h4 className="font-medium text-white">상세 정보</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">거래량:</span>
              <span className="text-white">
                {stock.volume?.toLocaleString() || '0'}
              </span>
            </div>
            {stock.marketCap && (
              <div className="flex justify-between">
                <span className="text-gray-400">시가총액:</span>
                <span className="text-white">
                  {(stock.marketCap / 100000000).toFixed(0)}억원
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 기술적 지표 (모의 데이터) */}
        <div className="space-y-3">
          <h4 className="font-medium text-white">기술적 지표</h4>
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-[#1a1a1a] rounded-lg text-center">
              <div className="text-xs text-gray-400 mb-1">RSI</div>
              <div className="font-medium text-white">45.6</div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg text-center">
              <div className="text-xs text-gray-400 mb-1">MACD</div>
              <div className="font-medium text-profit-foreground">+0.82</div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg text-center">
              <div className="text-xs text-gray-400 mb-1">이평선</div>
              <div className="font-medium text-white">상향</div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg text-center">
              <div className="text-xs text-gray-400 mb-1">볼린저</div>
              <div className="font-medium text-blue-400">중간</div>
            </div>
          </div>
        </div>

        {/* 매매 신호 */}
        <div className="space-y-3">
          <h4 className="font-medium text-white">매매 신호</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-[#1a1a1a] rounded-lg">
              <span className="text-sm text-gray-400">종합 신호</span>
              <Badge variant="default" className="bg-profit">
                매수
              </Badge>
            </div>
            <div className="flex items-center justify-between p-2 bg-[#1a1a1a] rounded-lg">
              <span className="text-sm text-gray-400">단기 추세</span>
              <Badge variant="secondary">
                중립
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}