import { useEffect, useState } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { MinuteCandleUpdateMessage } from '@/lib/types';
import { subscribeToMinuteCandles } from '@/lib/websocket';

export function useRealtimeMinuteCandles(stockCode: string, enabled: boolean = true) {
  const [currentCandle, setCurrentCandle] = useState<ChartCandle | null>(null);

  useEffect(() => {
    if (!enabled || !stockCode) {
      return;
    }

    const unsubscribe = subscribeToMinuteCandles((message: MinuteCandleUpdateMessage) => {
      if (message.stock_code !== stockCode) {
        return;
      }

      const { data } = message;
      setCurrentCandle({
        timestamp: data.timestamp,
        open: data.open,
        high: data.high,
        low: data.low,
        close: data.close,
        volume: data.volume,
        tradingValue: null,
        foreignBuy: null,
        foreignSell: null,
        institutionalBuy: null,
        institutionalSell: null,
        individualBuy: null,
        individualSell: null,
      });
    });

    return () => {
      unsubscribe();
      setCurrentCandle(null);
    };
  }, [stockCode, enabled]);

  return currentCandle;
}
