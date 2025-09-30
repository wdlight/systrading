'use client';

import { useState, useEffect } from 'react';
import { TradingHoursManager, TradingSession } from '@/lib/utils/tradingHours';

export interface UseTradingHoursReturn {
  currentSession: TradingSession;
  timeUntilReset: number;
  isMarketOpen: boolean;
  formatTimeUntilReset: () => string;
  sessionDisplayName: string;
}

/**
 * 한국 주식시장 거래시간 관리 Hook
 *
 * @returns 현재 거래 세션, 리셋까지 남은 시간, 장 개장 여부 등
 */
export function useTradingHours(): UseTradingHoursReturn {
  const [currentSession, setCurrentSession] = useState<TradingSession>(TradingSession.CLOSED);
  const [timeUntilReset, setTimeUntilReset] = useState<number>(0);
  const [isMarketOpen, setIsMarketOpen] = useState<boolean>(false);

  useEffect(() => {
    const updateStatus = () => {
      const now = new Date();
      const session = TradingHoursManager.getSession(now);
      setCurrentSession(session);
      setTimeUntilReset(TradingHoursManager.getTimeUntilReset());
      setIsMarketOpen(TradingHoursManager.isRegularHours(now));
    };

    // 초기 업데이트
    updateStatus();

    // 1초마다 업데이트
    const interval = setInterval(updateStatus, 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTimeUntilReset = (): string => {
    const hours = Math.floor(timeUntilReset / (1000 * 60 * 60));
    const minutes = Math.floor((timeUntilReset % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeUntilReset % (1000 * 60)) / 1000);
    return `${hours}시간 ${minutes}분 ${seconds}초`;
  };

  const sessionDisplayName = TradingHoursManager.getSessionDisplayName(currentSession);

  return {
    currentSession,
    timeUntilReset,
    isMarketOpen,
    formatTimeUntilReset,
    sessionDisplayName
  };
}