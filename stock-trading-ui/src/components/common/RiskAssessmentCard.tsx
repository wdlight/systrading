'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Shield, AlertTriangle, TrendingUp, DollarSign } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RiskAssessmentCardProps {
  className?: string;
}

export function RiskAssessmentCard({ className }: RiskAssessmentCardProps) {
  // 모의 리스크 데이터
  const riskData = {
    totalPortfolioValue: 15000000, // 1,500만원
    availableCash: 3000000, // 300만원
    dayPnL: 250000, // +25만원
    dayPnLRate: 1.7, // +1.7%
    riskScore: 65, // 100점 만점 중 65점 (중간 위험)
    diversificationScore: 75, // 분산 투자 점수
    leverageRatio: 0.3, // 레버리지 비율
    maxDrawdown: -5.2, // 최대 낙폭
    positions: [
      { name: '삼성전자', weight: 35, risk: 'medium' },
      { name: 'SK하이닉스', weight: 25, risk: 'high' },
      { name: 'NAVER', weight: 20, risk: 'medium' },
      { name: '기타', weight: 20, risk: 'low' }
    ]
  };

  const getRiskBadge = (score: number) => {
    if (score >= 80) {
      return <Badge variant="destructive" className="bg-loss">고위험</Badge>;
    } else if (score >= 60) {
      return <Badge className="bg-yellow-600 hover:bg-yellow-700">중위험</Badge>;
    } else {
      return <Badge className="bg-profit hover:bg-profit/90">저위험</Badge>;
    }
  };

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'text-loss-foreground';
    if (score >= 60) return 'text-yellow-400';
    return 'text-profit-foreground';
  };

  const getPositionRiskColor = (risk: string) => {
    switch (risk) {
      case 'high': return 'bg-loss';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-profit';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Card className={cn('bg-[#2a2a2a] border-gray-700', className)}>
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Shield className="w-5 h-5" />
          리스크 관리
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 포트폴리오 현황 */}
        <div className="space-y-3">
          <h4 className="font-medium text-white flex items-center gap-2">
            <DollarSign className="w-4 h-4" />
            포트폴리오 현황
          </h4>
          <div className="grid grid-cols-1 gap-3">
            <div className="p-3 bg-[#1a1a1a] rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">총 자산</span>
                <span className="font-medium text-white">
                  {riskData.totalPortfolioValue.toLocaleString()}원
                </span>
              </div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">가용 현금</span>
                <span className="font-medium text-white">
                  {riskData.availableCash.toLocaleString()}원
                </span>
              </div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-400">일일 손익</span>
                <span className={cn("font-medium",
                  riskData.dayPnL > 0 ? "text-profit-foreground" : "text-loss-foreground"
                )}>
                  {riskData.dayPnL > 0 ? '+' : ''}{riskData.dayPnL.toLocaleString()}원
                  ({riskData.dayPnL > 0 ? '+' : ''}{riskData.dayPnLRate}%)
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 리스크 지표 */}
        <div className="space-y-3">
          <h4 className="font-medium text-white flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            리스크 지표
          </h4>

          {/* 종합 리스크 점수 */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">종합 리스크</span>
              <div className="flex items-center gap-2">
                <span className={cn("font-medium", getRiskColor(riskData.riskScore))}>
                  {riskData.riskScore}점
                </span>
                {getRiskBadge(riskData.riskScore)}
              </div>
            </div>
            <Progress
              value={riskData.riskScore}
              className="h-2"
            />
          </div>

          {/* 분산 투자 점수 */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-400">분산 투자</span>
              <span className="font-medium text-profit-foreground">
                {riskData.diversificationScore}점
              </span>
            </div>
            <Progress
              value={riskData.diversificationScore}
              className="h-2"
            />
          </div>

          {/* 기타 지표 */}
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">레버리지 비율:</span>
              <span className="text-white">{(riskData.leverageRatio * 100).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">최대 낙폭:</span>
              <span className="text-loss-foreground">{riskData.maxDrawdown}%</span>
            </div>
          </div>
        </div>

        {/* 포지션 비중 */}
        <div className="space-y-3">
          <h4 className="font-medium text-white flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            포지션 비중
          </h4>
          <div className="space-y-2">
            {riskData.positions.map((position, index) => (
              <div key={index} className="space-y-1">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className={cn("w-2 h-2 rounded-full", getPositionRiskColor(position.risk))} />
                    <span className="text-sm text-white">{position.name}</span>
                  </div>
                  <span className="text-sm text-gray-400">{position.weight}%</span>
                </div>
                <Progress
                  value={position.weight}
                  className="h-1"
                />
              </div>
            ))}
          </div>
        </div>

        {/* 리스크 권고사항 */}
        <div className="space-y-3">
          <h4 className="font-medium text-white">권고사항</h4>
          <div className="space-y-2">
            <div className="p-3 bg-[#1a1a1a] rounded-lg border-l-4 border-yellow-500">
              <div className="text-sm text-yellow-400 font-medium mb-1">
                ⚠️ 주의
              </div>
              <div className="text-sm text-gray-300">
                반도체 업종 집중도가 높습니다. 분산 투자를 고려해보세요.
              </div>
            </div>
            <div className="p-3 bg-[#1a1a1a] rounded-lg border-l-4 border-blue-500">
              <div className="text-sm text-blue-400 font-medium mb-1">
                💡 제안
              </div>
              <div className="text-sm text-gray-300">
                현금 비중이 적정 수준입니다. 추가 투자 기회를 모색해보세요.
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}