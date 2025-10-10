type HistoryPoint = {
  date: string;
  portfolio: number;
  benchmark: number;
};

type HistoryBucket = '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | 'ALL';

function createDailyHistory(days: number, baseValue: number, volatility: number): HistoryPoint[] {
  return Array.from({ length: days }).map((_, index) => {
    const dayIndex = days - index - 1;
    const date = new Date(Date.now() - dayIndex * 24 * 60 * 60 * 1000);

    const perturbation = Math.sin(index / 7) * volatility * 0.6;
    const drift = (Math.random() - 0.5) * volatility;
    const portfolio = Math.max(baseValue + baseValue * (perturbation + drift / 100), baseValue * 0.75);
    const benchmark = Math.max(2500 + 50 * Math.sin(index / 10) + drift * 5, 2300);

    return {
      date: date.toISOString(),
      portfolio: Math.round(portfolio),
      benchmark: Math.round(benchmark),
    };
  });
}

function createIntradayHistory(hours: number, baseValue: number, volatility: number): HistoryPoint[] {
  return Array.from({ length: hours }).map((_, index) => {
    const hourIndex = hours - index - 1;
    const date = new Date(Date.now() - hourIndex * 60 * 60 * 1000);

    const sinus = Math.sin(index / 3) * volatility * 0.4;
    const drift = (Math.random() - 0.5) * volatility * 0.5;
    const portfolio = Math.max(baseValue + baseValue * (sinus + drift / 100), baseValue * 0.9);
    const benchmark = Math.max(2500 + 20 * Math.sin(index / 4) + drift * 3, 2400);

    return {
      date: date.toISOString(),
      portfolio: Math.round(portfolio),
      benchmark: Math.round(benchmark),
    };
  });
}

const baseValue = 125_000_000;

export const mockPortfolioHistory: Record<HistoryBucket, HistoryPoint[]> = {
  '1D': createIntradayHistory(24, baseValue, 0.6),
  '1W': createDailyHistory(7, baseValue, 0.8),
  '1M': createDailyHistory(30, baseValue, 1.3),
  '3M': createDailyHistory(90, baseValue, 1.8),
  '6M': createDailyHistory(180, baseValue, 2.1),
  '1Y': createDailyHistory(365, baseValue, 2.5),
  'ALL': createDailyHistory(730, baseValue, 2.8),
};

export type { HistoryBucket, HistoryPoint };
