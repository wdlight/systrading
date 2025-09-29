// Korean Stock Trading Types

export interface KoreanStock {
  code: string;
  name: string;
  currentPrice: number;
  changeAmount: number;
  changeRate: number;
  volume: number;
  marketCap: number;
  high: number;
  low: number;
  open: number;
  previousClose: number;
  sector: string;
  listedShares: number;
  foreignRatio: number;
  per: number;
  pbr: number;
  eps: number;
  dividend: number;
  dividendYield: number;
  updatedAt: string;
}

export interface KoreanStockWithIndicators extends KoreanStock {
  indicators: {
    rsi: number;
    macd: number;
    macdSignal: number;
    macdHistogram: number;
    sma20: number;
    sma60: number;
    ema12: number;
    ema26: number;
    bollingerUpper: number;
    bollingerMiddle: number;
    bollingerLower: number;
    stochasticK: number;
    stochasticD: number;
    adx: number;
    cci: number;
    williams: number;
  };
}

export interface OrderBookEntry {
  price: number;
  quantity: number;
  total: number;
  ratio: number;
  orders: number;
}

export interface KoreanOrderBook {
  stockCode: string;
  stockName: string;
  timestamp: string;
  asks: OrderBookEntry[]; // 매도 호가
  bids: OrderBookEntry[]; // 매수 호가
  totalAskQuantity: number;
  totalBidQuantity: number;
  spread: number;
  spreadPercent: number;
  lastTradePrice: number;
  lastTradeQuantity: number;
  lastTradeTime: string;
}

export interface KoreanTradingOrder {
  orderNumber: string;
  stockCode: string;
  stockName: string;
  orderType: '지정가' | '시장가' | '조건부지정가' | 'IOC' | 'FOK';
  orderSide: '매수' | '매도';
  quantity: number;
  price: number;
  filledQuantity: number;
  remainingQuantity: number;
  orderStatus: '접수' | '체결' | '일부체결' | '취소' | '거부';
  orderTime: string;
  filledTime?: string;
  filledPrice?: number;
  commission: number;
  tax: number;
  netAmount: number;
}

export interface KoreanMarketIndex {
  name: string;
  code: string;
  currentValue: number;
  changeAmount: number;
  changeRate: number;
  volume: number;
  tradingValue: number;
  marketCap: number;
  isUp: boolean;
  timestamp: string;
}

export interface KoreanMarketOverview {
  kospi: KoreanMarketIndex;
  kosdaq: KoreanMarketIndex;
  kospi200: KoreanMarketIndex;
  sectors: {
    technology: KoreanMarketIndex;
    finance: KoreanMarketIndex;
    chemical: KoreanMarketIndex;
    automotive: KoreanMarketIndex;
    shipbuilding: KoreanMarketIndex;
    construction: KoreanMarketIndex;
  };
  currency: {
    usdKrw: number;
    usdKrwChange: number;
    usdKrwChangeRate: number;
  };
  foreignInvestment: {
    net: number;
    buy: number;
    sell: number;
  };
  institutionalInvestment: {
    net: number;
    buy: number;
    sell: number;
  };
  individualInvestment: {
    net: number;
    buy: number;
    sell: number;
  };
  updatedAt: string;
}

export interface KoreanStockChart {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  tradingValue: number | null;
  foreignBuy: number | null;
  foreignSell: number | null;
  institutionalBuy: number | null;
  institutionalSell: number | null;
  individualBuy: number | null;
  individualSell: number | null;
}

// Chart data type alias for compatibility
export type ChartCandle = KoreanStockChart;

export interface KoreanPortfolioPosition {
  stockCode: string;
  stockName: string;
  quantity: number;
  sellableQuantity: number;
  avgPrice: number;
  currentPrice: number;
  evaluationAmount: number;
  profitLoss: number;
  profitRate: number;
  weight: number;
  sector: string;
  purchaseAmount: number;
  fees: number;
  tax: number;
}

export interface KoreanPortfolioSummary {
  totalAsset: number;
  totalStock: number;
  availableCash: number;
  depositAmount: number;
  totalPurchaseAmount: number;
  totalEvaluationAmount: number;
  totalProfitLoss: number;
  totalProfitRate: number;
  dailyProfitLoss: number;
  dailyProfitRate: number;
  positions: KoreanPortfolioPosition[];
  positionCount: number;
  diversificationRatio: number;
  leverage: number;
  marginRequirement: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'VERY_HIGH';
}

// Popular Korean Stocks Data
export const POPULAR_KOREAN_STOCKS: KoreanStock[] = [
  {
    code: '005930',
    name: '삼성전자',
    currentPrice: 71400,
    changeAmount: 1200,
    changeRate: 1.71,
    volume: 15234567,
    marketCap: 4280000000000,
    high: 72000,
    low: 70500,
    open: 70800,
    previousClose: 70200,
    sector: '반도체',
    listedShares: 5969782550,
    foreignRatio: 51.8,
    per: 12.4,
    pbr: 1.2,
    eps: 5761,
    dividend: 1444,
    dividendYield: 2.02,
    updatedAt: new Date().toISOString()
  },
  {
    code: '000660',
    name: 'SK하이닉스',
    currentPrice: 139500,
    changeAmount: -2500,
    changeRate: -1.76,
    volume: 8234567,
    marketCap: 1015000000000,
    high: 142000,
    low: 138000,
    open: 141000,
    previousClose: 142000,
    sector: '반도체',
    listedShares: 728002365,
    foreignRatio: 49.2,
    per: 15.8,
    pbr: 1.8,
    eps: 8829,
    dividend: 1000,
    dividendYield: 0.72,
    updatedAt: new Date().toISOString()
  },
  {
    code: '035420',
    name: 'NAVER',
    currentPrice: 196500,
    changeAmount: 3500,
    changeRate: 1.81,
    volume: 1234567,
    marketCap: 320000000000,
    high: 198000,
    low: 194000,
    open: 194500,
    previousClose: 193000,
    sector: '인터넷',
    listedShares: 164130829,
    foreignRatio: 38.5,
    per: 18.2,
    pbr: 2.1,
    eps: 10789,
    dividend: 344,
    dividendYield: 0.18,
    updatedAt: new Date().toISOString()
  },
  {
    code: '005380',
    name: '현대차',
    currentPrice: 186500,
    changeAmount: 4500,
    changeRate: 2.47,
    volume: 2345678,
    marketCap: 400000000000,
    high: 187000,
    low: 183000,
    open: 183500,
    previousClose: 182000,
    sector: '자동차',
    listedShares: 213669970,
    foreignRatio: 33.8,
    per: 8.9,
    pbr: 0.7,
    eps: 20935,
    dividend: 3000,
    dividendYield: 1.61,
    updatedAt: new Date().toISOString()
  },
  {
    code: '066570',
    name: 'LG전자',
    currentPrice: 89400,
    changeAmount: 800,
    changeRate: 0.90,
    volume: 1845672,
    marketCap: 210000000000,
    high: 90200,
    low: 88600,
    open: 89000,
    previousClose: 88600,
    sector: '가전',
    listedShares: 236869365,
    foreignRatio: 26.4,
    per: 11.2,
    pbr: 0.9,
    eps: 7982,
    dividend: 1300,
    dividendYield: 1.45,
    updatedAt: new Date().toISOString()
  },
  {
    code: '122630',
    name: 'KODEX KOSPI',
    currentPrice: 28950,
    changeAmount: 150,
    changeRate: 0.52,
    volume: 5234567,
    marketCap: 15000000000,
    high: 29100,
    low: 28800,
    open: 28850,
    previousClose: 28800,
    sector: 'ETF',
    listedShares: 520000000,
    foreignRatio: 15.2,
    per: 0,
    pbr: 0,
    eps: 0,
    dividend: 450,
    dividendYield: 1.55,
    updatedAt: new Date().toISOString()
  },
  {
    code: '051910',
    name: 'LG화학',
    currentPrice: 425000,
    changeAmount: -8000,
    changeRate: -1.85,
    volume: 456789,
    marketCap: 300000000000,
    high: 435000,
    low: 422000,
    open: 430000,
    previousClose: 433000,
    sector: '화학',
    listedShares: 70592343,
    foreignRatio: 42.1,
    per: 13.5,
    pbr: 1.4,
    eps: 31481,
    dividend: 4000,
    dividendYield: 0.94,
    updatedAt: new Date().toISOString()
  },
  {
    code: '003550',
    name: 'LG',
    currentPrice: 78600,
    changeAmount: 1200,
    changeRate: 1.55,
    volume: 892345,
    marketCap: 105000000000,
    high: 79000,
    low: 77400,
    open: 77800,
    previousClose: 77400,
    sector: '지주회사',
    listedShares: 133836325,
    foreignRatio: 29.8,
    per: 9.2,
    pbr: 0.6,
    eps: 8543,
    dividend: 1600,
    dividendYield: 2.04,
    updatedAt: new Date().toISOString()
  }
];

// Stock Sectors
export const STOCK_SECTORS = {
  '반도체': { color: 'blue', count: 2 },
  '인터넷': { color: 'purple', count: 1 },
  '자동차': { color: 'green', count: 1 },
  '가전': { color: 'orange', count: 1 },
  'ETF': { color: 'gray', count: 1 },
  '화학': { color: 'red', count: 1 },
  '지주회사': { color: 'cyan', count: 1 }
} as const;

export type StockSector = keyof typeof STOCK_SECTORS;

// Trading Hours
export const KOREAN_TRADING_HOURS = {
  preMarket: { start: '08:00', end: '09:00' },
  regular: { start: '09:00', end: '15:30' },
  afterHours: { start: '15:30', end: '18:00' },
  timezone: 'Asia/Seoul'
};

// Market Status
export type MarketStatus = 'PRE_MARKET' | 'OPEN' | 'CLOSED' | 'AFTER_HOURS' | 'HOLIDAY';

export function getMarketStatus(): MarketStatus {
  const now = new Date();
  const kstTime = new Intl.DateTimeFormat('en-US', {
    timeZone: KOREAN_TRADING_HOURS.timezone,
    hour12: false,
    hour: '2-digit',
    minute: '2-digit'
  }).format(now);
  
  const [hours, minutes] = kstTime.split(':').map(Number);
  const currentTime = hours * 100 + minutes;
  
  // Weekend check
  const dayOfWeek = new Date().getDay();
  if (dayOfWeek === 0 || dayOfWeek === 6) {
    return 'CLOSED';
  }
  
  if (currentTime >= 800 && currentTime < 900) {
    return 'PRE_MARKET';
  } else if (currentTime >= 900 && currentTime < 1530) {
    return 'OPEN';
  } else if (currentTime >= 1530 && currentTime < 1800) {
    return 'AFTER_HOURS';
  } else {
    return 'CLOSED';
  }
}

export function formatKoreanWon(amount: number, compact: boolean = false, withUnit: boolean = true): string {
  if (compact) {
    if (amount >= 100000000) {
      const value = (amount / 100000000).toFixed(1);
      return withUnit ? `${value}억원` : value;
    } else if (amount >= 10000) {
      const value = (amount / 10000).toFixed(1);
      return withUnit ? `${value}만원` : value;
    }
  }
  const value = amount.toLocaleString('ko-KR');
  return withUnit ? `${value}원` : value;
}

export function formatStockPrice(price: number, withUnit: boolean = true): string {
  const value = price.toLocaleString('ko-KR');
  return withUnit ? `${value}원` : value;
}

export function formatPriceChange(change: number, rate: number): { text: string; color: string } {
  const isPositive = change > 0;
  const isNeutral = change === 0;
  
  const text = isPositive 
    ? `+${change.toLocaleString('ko-KR')} (+${rate.toFixed(2)}%)`
    : isNeutral 
    ? `0 (0.00%)`
    : `${change.toLocaleString('ko-KR')} (${rate.toFixed(2)}%)`;
    
  const color = isPositive ? 'text-red-400' : isNeutral ? 'text-gray-400' : 'text-blue-400';
  
  return { text, color };
}

export function getStockColorClass(changeRate: number): string {
  if (changeRate > 0) return 'text-red-400 bg-red-500/10';
  if (changeRate < 0) return 'text-blue-400 bg-blue-500/10';
  return 'text-gray-400 bg-gray-500/10';
}

export function getStockTrendIcon(changeRate: number): string {
  if (changeRate > 0) return '▲';
  if (changeRate < 0) return '▼';
  return '━';
}