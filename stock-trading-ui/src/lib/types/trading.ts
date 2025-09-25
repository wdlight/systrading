// 기본 주식 정보
export interface Stock {
  code: string;
  name: string;
  currentPrice: number;
  changeRate: number;
  changeAmount: number;
  volume: number;
  marketCap?: number;
}

// 주문 정보
export interface Order {
  id: string;
  stockCode: string;
  stockName: string;
  type: 'buy' | 'sell';
  orderType: 'market' | 'limit' | 'stop';
  quantity: number;
  price?: number;
  stopPrice?: number;
  status: 'pending' | 'filled' | 'cancelled' | 'rejected';
  timestamp: Date;
  filledQuantity?: number;
  filledPrice?: number;
}

// 포지션 정보
export interface Position {
  stockCode: string;
  stockName: string;
  quantity: number;
  averagePrice: number;
  currentPrice: number;
  totalValue: number;
  unrealizedPnL: number;
  unrealizedPnLRate: number;
}

// 자동매매 조건
export interface TradingCondition {
  id: string;
  name: string;
  stockCode: string;
  type: 'buy' | 'sell';
  conditions: {
    rsi?: { min?: number; max?: number };
    macd?: { signal: 'positive' | 'negative' | 'crossover' };
    price?: { min?: number; max?: number };
    volume?: { min?: number };
  };
  action: {
    quantity: number;
    priceType: 'market' | 'limit';
    limitPrice?: number;
  };
  isActive: boolean;
  createdAt: Date;
  lastTriggered?: Date;
}

// 포트폴리오 정보
export interface Portfolio {
  positions: Position[];
  totalValue: number;
  dayPnL: number;
  dayPnLRate: number;
  cash: number;
}

// 기존 WatchlistItem과 호환성을 위한 타입
export interface WatchlistItem {
  종목코드: string;
  종목명: string;
  현재가: number;
  수익률: number;
  평균단가: number;
  보유수량: number;
  MACD: number;
  MACD시그널: number;
  RSI: number;
  트레일링스탑발동여부?: boolean;
  트레일링스탑발동후고가?: number;
}

// 계좌 정보 (기존과 호환)
export interface AccountInfo {
  종목코드: string;
  종목명: string;
  보유수량: number;
  매도가능수량: number;
  매입단가: number;
  수익률: number;
  현재가: number;
  전일대비: number;
  등락: string;
}