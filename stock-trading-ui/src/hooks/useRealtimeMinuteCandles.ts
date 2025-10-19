import { useEffect, useState } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { MinuteCandleUpdateMessage, MinuteCandleFinalizeMessage } from '@/lib/types';
import { subscribeToMinuteCandles, subscribeToMinuteCandleFinalize } from '@/lib/websocket';

export function useRealtimeMinuteCandles(stockCode: string, enabled: boolean = true) {
  const [currentCandle, setCurrentCandle] = useState<ChartCandle | null>(null);
  const [finalizedCandles, setFinalizedCandles] = useState<ChartCandle[]>([]);

  useEffect(() => {
    if (!enabled || !stockCode) {
      setCurrentCandle(null);
      setFinalizedCandles([]);
      return;
    }

    // 1. 진행 중인 분봉 구독 (기존)
    const unsubscribeUpdate = subscribeToMinuteCandles((message: MinuteCandleUpdateMessage) => {
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

    // 2. 완성된 분봉 구독 (신규)
    const unsubscribeFinalize = subscribeToMinuteCandleFinalize((message: MinuteCandleFinalizeMessage) => {
      if (message.stock_code !== stockCode) {
        return;
      }

      const { data } = message;
      const finalizedCandle: ChartCandle = {
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
      };

      // 완성된 분봉을 배열에 추가 (중복 방지)
      setFinalizedCandles((prev) => {
        const exists = prev.some(c => c.timestamp === finalizedCandle.timestamp);
        if (exists) return prev;
        return [...prev, finalizedCandle];
      });

      // 현재 분봉이 완성된 것이면 초기화
      setCurrentCandle(null);
    });

    return () => {
      unsubscribeUpdate();
      unsubscribeFinalize();
    };
  }, [stockCode, enabled]);

  return { currentCandle, finalizedCandles };
}
