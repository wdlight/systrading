import { useEffect, useState } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { MinuteCandleUpdateMessage, MinuteCandleFinalizeMessage } from '@/lib/types';
import { subscribeToMinuteCandles, subscribeToMinuteCandleFinalize, wsManager } from '@/lib/websocket';

export function useRealtimeMinuteCandles(stockCode: string, enabled: boolean = true) {
  const [currentCandle, setCurrentCandle] = useState<ChartCandle | null>(null);
  const [finalizedCandles, setFinalizedCandles] = useState<ChartCandle[]>([]);

  useEffect(() => {
    // ✅ 종목 전환 시 상태 즉시 초기화 (데이터 오염 방지)
    console.log(`🔄 [useRealtimeMinuteCandles] 훅 초기화: stockCode=${stockCode}, enabled=${enabled}`);
    setCurrentCandle(null);
    setFinalizedCandles([]);

    if (!enabled || !stockCode) {
      console.log('⚠️ [useRealtimeMinuteCandles] 비활성화 또는 종목 코드 없음');
      return;
    }

    console.log(`✅ [useRealtimeMinuteCandles] 분봉 구독 시작: ${stockCode}`);

    // 🔥 중요: WebSocket에 종목 구독 요청 전송
    const subscribeToStock = async () => {
      // WebSocket 연결 대기
      const waitForConnection = () => {
        return new Promise<boolean>((resolve) => {
          const checkInterval = setInterval(() => {
            if (wsManager.isConnected()) {
              clearInterval(checkInterval);
              resolve(true);
            }
          }, 100);

          // 10초 타임아웃
          setTimeout(() => {
            clearInterval(checkInterval);
            resolve(false);
          }, 10000);
        });
      };

      const isConnected = await waitForConnection();
      if (isConnected) {
        console.log(`📤 [useRealtimeMinuteCandles] 종목 구독 요청 전송: ${stockCode}`);
        wsManager.send({
          type: 'subscribe',
          stock_code: stockCode
        });
        wsManager.addPendingSubscription(stockCode);
        console.log(`✅ [useRealtimeMinuteCandles] 종목 구독 완료: ${stockCode}`);
      } else {
        console.error(`❌ [useRealtimeMinuteCandles] WebSocket 연결 타임아웃: ${stockCode}`);
      }
    };

    subscribeToStock();

    // 1. 진행 중인 분봉 구독 (기존)
    const unsubscribeUpdate = subscribeToMinuteCandles((message: MinuteCandleUpdateMessage) => {
      console.log('🔄 [UPDATE] 분봉 업데이트 메시지 수신:', message);

      if (message.stock_code !== stockCode) {
        console.log(`⚠️ [UPDATE] 종목 코드 불일치: ${message.stock_code} !== ${stockCode}`);
        return;
      }

      console.log(`✅ [UPDATE] 분봉 업데이트 처리: ${message.stock_code} ${message.data.timestamp}`);
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
      console.log('🎉 [FINALIZE] 분봉 완성 메시지 수신:', message);

      if (message.stock_code !== stockCode) {
        console.log(`⚠️ [FINALIZE] 종목 코드 불일치: ${message.stock_code} !== ${stockCode}`);
        return;
      }

      console.log(`✅ [FINALIZE] 완성된 분봉 처리 시작: ${message.stock_code} ${message.data.timestamp}`);
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

      console.log('📊 [FINALIZE] 생성된 ChartCandle:', finalizedCandle);

      // 완성된 분봉을 배열에 추가 (중복 방지)
      setFinalizedCandles((prev) => {
        const exists = prev.some(c => c.timestamp === finalizedCandle.timestamp);
        if (exists) {
          console.log(`⚠️ [FINALIZE] 중복 분봉 감지, 무시: ${finalizedCandle.timestamp}`);
          return prev;
        }
        console.log(`✅ [FINALIZE] finalizedCandles 배열에 추가: ${finalizedCandle.timestamp} (기존 ${prev.length}개 → ${prev.length + 1}개)`);
        return [...prev, finalizedCandle];
      });

      // 현재 분봉이 완성된 것이면 초기화
      setCurrentCandle(null);
      console.log('✅ [FINALIZE] currentCandle 초기화 완료');
    });

    return () => {
      console.log(`🔚 [useRealtimeMinuteCandles] 구독 해제: ${stockCode}`);

      // WebSocket 리스너 해제
      unsubscribeUpdate();
      unsubscribeFinalize();

      // 종목 구독 해제
      if (wsManager.isConnected() && stockCode) {
        console.log(`📤 [useRealtimeMinuteCandles] 종목 구독 해제 요청: ${stockCode}`);
        wsManager.send({
          type: 'unsubscribe',
          stock_code: stockCode
        });
        wsManager.removePendingSubscription(stockCode);
      }
    };
  }, [stockCode, enabled]);

  return { currentCandle, finalizedCandles };
}
