import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import { Direction, PortfolioStats } from "./types"
import { TRADING_COLORS } from "./constants"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// 숫자 포맷팅 유틸리티
export function formatCurrency(
  amount: number | null | undefined,
  options: {
    currency?: string;
    compact?: boolean;
    showSign?: boolean;
  } = {}
): string {
  const { currency = 'KRW', compact = false, showSign = false } = options;
  
  // undefined, null, NaN 값 처리
  if (amount == null || isNaN(Number(amount))) {
    return currency === 'KRW' ? '₩0' : '0';
  }
  
  const numAmount = Number(amount);
  const formatter = new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency,
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: currency === 'KRW' ? 0 : 2,
  });
  
  const formatted = formatter.format(Math.abs(numAmount));
  
  if (showSign && numAmount !== 0) {
    return numAmount > 0 ? `+${formatted}` : `-${formatted}`;
  }
  
  return formatted;
}

export function formatNumber(
  value: number | null | undefined,
  options: {
    decimals?: number;
    compact?: boolean;
    showSign?: boolean;
  } = {}
): string {
  const { decimals = 2, compact = false, showSign = false } = options;
  
  // undefined, null, NaN 값 처리
  if (value == null || isNaN(Number(value))) {
    return '0';
  }
  
  const numValue = Number(value);
  const formatter = new Intl.NumberFormat('ko-KR', {
    notation: compact ? 'compact' : 'standard',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  
  const formatted = formatter.format(Math.abs(numValue));
  
  if (showSign && numValue !== 0) {
    return numValue > 0 ? `+${formatted}` : `-${formatted}`;
  }
  
  return `${formatted}`;
}

export function formatPercentage(
  value: number | null | undefined,
  options: {
    decimals?: number;
    showSign?: boolean;
  } = {}
): string {
  const { decimals = 2, showSign = true } = options;
  
  // undefined, null, NaN 값 처리
  if (value == null || isNaN(Number(value))) {
    return '0.00%';
  }
  
  const numValue = Number(value);
  const formatted = numValue.toFixed(decimals);
  
  if (showSign && numValue !== 0) {
    return numValue > 0 ? `+${formatted}%` : `${formatted}%`;
  }
  
  return `${formatted}%`;
}

// 가격 변동 방향 계산
export function getPriceDirection(current: number, previous: number): Direction {
  if (current > previous) return 'up';
  if (current < previous) return 'down';
  return 'neutral';
}

// 색상 유틸리티
export function getPriceColor(direction: Direction): string {
  switch (direction) {
    case 'up':
      return TRADING_COLORS.bullish;
    case 'down':
      return TRADING_COLORS.bearish;
    default:
      return TRADING_COLORS.neutral;
  }
}

export function getDirectionIcon(direction: Direction): string {
  switch (direction) {
    case 'up':
      return '▲';
    case 'down':
      return '▼';
    default:
      return '●';
  }
}

// RSI 색상 및 상태
export function getRSIStatus(rsi: number): {
  status: 'oversold' | 'normal' | 'overbought';
  color: string;
  description: string;
} {
  if (rsi <= 30) {
    return {
      status: 'oversold',
      color: TRADING_COLORS.bullish,
      description: '과매도',
    };
  } else if (rsi >= 70) {
    return {
      status: 'overbought',
      color: TRADING_COLORS.bearish,
      description: '과매수',
    };
  } else {
    return {
      status: 'normal',
      color: TRADING_COLORS.neutral,
      description: '보통',
    };
  }
}

// MACD 시그널 분석
export function getMACDSignal(macd: number, signal: number): {
  trend: 'bullish' | 'bearish' | 'neutral';
  strength: 'strong' | 'weak';
  description: string;
} {
  const diff = macd - signal;
  const absDiff = Math.abs(diff);
  
  let trend: 'bullish' | 'bearish' | 'neutral';
  
  if (diff > 0) {
    trend = 'bullish';
  } else if (diff < 0) {
    trend = 'bearish';
  } else {
    trend = 'neutral';
  }
  
  const strength = absDiff > 0.5 ? 'strong' : 'weak';
  
  const descriptions = {
    bullish: { strong: '강한 상승 신호', weak: '약한 상승 신호' },
    bearish: { strong: '강한 하락 신호', weak: '약한 하락 신호' },
    neutral: { strong: '중립', weak: '중립' },
  };
  
  return {
    trend,
    strength,
    description: descriptions[trend][strength],
  };
}

// 시간 포맷팅
export function formatTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function formatDateTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getRelativeTime(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  
  if (diffSec < 60) return `${diffSec}초 전`;
  if (diffMin < 60) return `${diffMin}분 전`;
  if (diffHour < 24) return `${diffHour}시간 전`;
  if (diffDay < 7) return `${diffDay}일 전`;
  
  return formatDateTime(d);
}

// 포트폴리오 위험도 계산
export function calculateRiskScore(stats: PortfolioStats): {
  score: number;
  level: 'low' | 'medium' | 'high';
  description: string;
} {
  // 변동성, 최대 낙폭, 다각화 점수를 종합하여 위험도 계산
  const volatilityScore = Math.min(stats.volatility * 100, 100);
  const drawdownScore = Math.min(Math.abs(stats.max_drawdown), 100);
  const diversificationScore = 100 - stats.diversification_score;
  
  const score = Math.round((volatilityScore + drawdownScore + diversificationScore) / 3);
  
  let level: 'low' | 'medium' | 'high';
  let description: string;
  
  if (score < 30) {
    level = 'low';
    description = '낮은 위험';
  } else if (score < 70) {
    level = 'medium';
    description = '중간 위험';
  } else {
    level = 'high';
    description = '높은 위험';
  }
  
  return { score, level, description };
}

// 다각화 점수 계산
export function calculateDiversificationScore(positions: any[]): number {
  if (positions.length === 0) return 0;
  
  const totalValue = positions.reduce((sum, pos) => sum + pos.evaluation_amount, 0);
  
  // Herfindahl-Hirschman Index 기반 계산
  const hhi = positions.reduce((sum, pos) => {
    const weight = pos.evaluation_amount / totalValue;
    return sum + (weight * weight);
  }, 0);
  
  // 0-100 스케일로 변환 (높을수록 다각화가 잘 됨)
  return Math.round((1 - hhi) * 100);
}

// 수익률 색상 클래스
export function getProfitColorClass(rate: number): string {
  if (rate > 0) return 'text-green-600 dark:text-green-400';
  if (rate < 0) return 'text-red-600 dark:text-red-400';
  return 'text-gray-600 dark:text-gray-400';
}

// 애니메이션 유틸리티
export function animateValue(
  start: number,
  end: number,
  duration: number,
  callback: (value: number) => void
): void {
  const startTime = Date.now();
  const diff = end - start;
  
  function update() {
    const elapsed = Date.now() - startTime;
    const progress = Math.min(elapsed / duration, 1);
    
    // easeOutQuart 이징 함수
    const easedProgress = 1 - Math.pow(1 - progress, 4);
    const currentValue = start + (diff * easedProgress);
    
    callback(currentValue);
    
    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }
  
  requestAnimationFrame(update);
}

// 디바운스 유틸리티
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

// 스로틀 유틸리티
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// 로컬 스토리지 유틸리티
export function getLocalStorage<T>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue;
  
  try {
    const item = localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error(`Error reading localStorage key "${key}":`, error);
    return defaultValue;
  }
}

export function setLocalStorage<T>(key: string, value: T): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error(`Error setting localStorage key "${key}":`, error);
  }
}

// 에러 메시지 표준화
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return '알 수 없는 오류가 발생했습니다.';
}
