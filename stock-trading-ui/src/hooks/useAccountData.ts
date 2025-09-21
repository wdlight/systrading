import { useState, useEffect, useCallback, useMemo } from 'react';
import { AccountBalance, Position, PortfolioStats } from '@/lib/types';
import { apiClient, fetchWithErrorHandling } from '@/lib/api-client';
import { subscribeToAccountUpdates } from '@/lib/websocket';
import { calculateDiversificationScore, calculateRiskScore } from '@/lib/utils';

/**
 * 계좌 데이터와 포트폴리오 통계를 관리하는 훅
 */
export function useAccountData() {
  const [accountBalance, setAccountBalance] = useState<AccountBalance | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);

  // 계좌 정보 로드
  const loadAccountData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const { data, error } = await fetchWithErrorHandling(() => 
      apiClient.getAccountBalance()
    );

    if (data) {
      setAccountBalance(data);
      setLastUpdateTime(new Date());
    } else if (error) {
      setError(error);
    }

    setIsLoading(false);
  }, []);

  // 계좌 정보 새로고침
  const refreshAccount = useCallback(async () => {
    const { error } = await fetchWithErrorHandling(() => 
      apiClient.refreshAccountInfo()
    );

    if (error) {
      setError(error);
      return false;
    }

    // 새로고침 후 데이터 다시 로드
    await loadAccountData();
    return true;
  }, [loadAccountData]);

  // 포트폴리오 통계 계산
  const portfolioStats = useMemo((): PortfolioStats | null => {
    if (!accountBalance || !accountBalance.positions.length) {
      return null;
    }

    const positions = accountBalance.positions;
    const totalValue = accountBalance.total_evaluation_amount;
    const totalPnL = accountBalance.total_profit_loss;
    const totalPnLRate = accountBalance.total_profit_loss_rate;

    // 일일 손익 계산 (실제로는 API에서 받아와야 함)
    const dailyPnL = positions.reduce((sum, pos) => 
      sum + ((pos.current_price - pos.yesterday_price) * pos.quantity), 0);
    const dailyPnLRate = totalValue > 0 ? (dailyPnL / totalValue) * 100 : 0;

    // 승률 계산 (수익이 나는 포지션 비율)
    const profitablePositions = positions.filter(pos => pos.profit_rate > 0).length;
    const winRate = positions.length > 0 ? (profitablePositions / positions.length) * 100 : 0;

    // 다각화 점수
    const diversificationScore = calculateDiversificationScore(
      positions.map(pos => ({ evaluation_amount: pos.evaluation_amount }))
    );

    // 변동성 계산 (단순화된 버전)
    const priceChanges = positions.map(pos => Math.abs(pos.change_rate));
    const avgVolatility = priceChanges.length > 0 
      ? priceChanges.reduce((sum, change) => sum + change, 0) / priceChanges.length / 100
      : 0;

    // 최대 낙폭 (현재 포지션 중 가장 큰 손실률)
    const maxDrawdown = Math.min(...positions.map(pos => pos.profit_rate), 0);

    // 샤프 비율 (단순화된 계산)
    const riskFreeRate = 0.03; // 3% 가정
    const excessReturn = (totalPnLRate / 100) - riskFreeRate;
    const sharpeRatio = avgVolatility > 0 ? excessReturn / avgVolatility : 0;

    const stats: PortfolioStats = {
      total_value: totalValue,
      daily_pnl: dailyPnL,
      daily_pnl_rate: dailyPnLRate,
      total_pnl: totalPnL,
      total_pnl_rate: totalPnLRate,
      win_rate: winRate,
      sharpe_ratio: sharpeRatio,
      max_drawdown: maxDrawdown,
      volatility: avgVolatility,
      diversification_score: diversificationScore,
      risk_score: 0, // 아래에서 계산
    };

    // 위험 점수 계산
    const riskInfo = calculateRiskScore(stats);
    stats.risk_score = riskInfo.score;

    return stats;
  }, [accountBalance]);

  // 보유 종목별 가중치 계산
  const positionWeights = useMemo(() => {
    if (!accountBalance?.positions.length) return [];

    const totalValue = accountBalance.total_evaluation_amount;
    
    return accountBalance.positions.map(position => ({
      ...position,
      weight: totalValue > 0 ? (position.evaluation_amount / totalValue) * 100 : 0,
    }));
  }, [accountBalance]);

  // 상위 보유 종목 (가중치 기준)
  const topPositions = useMemo(() => {
    return positionWeights
      .sort((a, b) => b.weight - a.weight)
      .slice(0, 5);
  }, [positionWeights]);

  // 수익/손실 종목 분류
  const profitLossBreakdown = useMemo(() => {
    if (!accountBalance?.positions.length) {
      return { profitable: [], losing: [], neutral: [] };
    }

    const profitable = accountBalance.positions.filter(pos => pos.profit_rate > 0.1);
    const losing = accountBalance.positions.filter(pos => pos.profit_rate < -0.1);
    const neutral = accountBalance.positions.filter(pos => 
      pos.profit_rate >= -0.1 && pos.profit_rate <= 0.1
    );

    return { profitable, losing, neutral };
  }, [accountBalance]);

  // 초기 로드
  useEffect(() => {
    loadAccountData();
  }, [loadAccountData]);

  // WebSocket 계좌 업데이트 구독
  useEffect(() => {
    const unsubscribe = subscribeToAccountUpdates((data) => {
      setAccountBalance(data);
      setLastUpdateTime(new Date());
      setError(null);
    });

    return unsubscribe;
  }, []);

  // 정기적인 데이터 새로고침 (5분마다)
  useEffect(() => {
    const interval = setInterval(() => {
      loadAccountData();
    }, 5 * 60 * 1000); // 5분

    return () => clearInterval(interval);
  }, [loadAccountData]);

  return {
    accountBalance,
    portfolioStats,
    positionWeights,
    topPositions,
    profitLossBreakdown,
    isLoading,
    error,
    lastUpdateTime,
    loadAccountData,
    refreshAccount,
  };
}