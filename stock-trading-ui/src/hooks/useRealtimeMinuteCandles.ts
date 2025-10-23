import { useEffect, useState } from 'react';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { MinuteCandleUpdateMessage, MinuteCandleFinalizedMessage } from '@/lib/types';  // ✅ Finalize → Finalized
import { subscribeToMinuteCandles, subscribeToMinuteCandleFinalized, wsManager } from '@/lib/websocket';  // ✅ Finalize → Finalized

const MAX_FINALIZED_CANDLES = 600; // 약 10시간 분량의 캐시

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
    console.log('⚙️ [useRealtimeMinuteCandles] minute_candle_update 리스너 등록 시도');
    const unsubscribeUpdate = subscribeToMinuteCandles((message: MinuteCandleUpdateMessage) => {
      console.log('🔄 [UPDATE] 분봉 업데이트 메시지 수신:', message);

      if (message.stock_code !== stockCode) {
        console.log(`⚠️ [UPDATE] 종목 코드 불일치: ${message.stock_code} !== ${stockCode}`);
        return;
      }

      console.log(`✅ [UPDATE] 분봉 업데이트 처리: ${message.stock_code} ${message.candle.timestamp}`);
      const { candle, is_final } = message;  // ✅ data → candle, is_final 추가

      // ✅ is_final 플래그 로깅 (디버깅용)
      if (is_final) {
        console.log(`🔥 [UPDATE] 완료된 분봉 수신 (is_final=true): ${candle.timestamp}`);
      }

      setCurrentCandle({
        timestamp: candle.timestamp,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume,
        tradingValue: null,
        foreignBuy: null,
        foreignSell: null,
        institutionalBuy: null,
        institutionalSell: null,
        individualBuy: null,
        individualSell: null,
      });
    });
    console.log('📡 [useRealtimeMinuteCandles] minute_candle_update 리스너 등록 완료');

    // 2. 완성된 분봉 구독 (신규)
    console.log('⚙️ [useRealtimeMinuteCandles] minute_candle_finalized 리스너 등록 시도');  // ✅ finalize → finalized
    const unsubscribeFinalize = subscribeToMinuteCandleFinalized((message: MinuteCandleFinalizedMessage) => {  // ✅ Finalize → Finalized
      console.log('🎉 [FINALIZED] 분봉 완성 메시지 수신:', message);

      if (message.stock_code !== stockCode) {
        console.log(`⚠️ [FINALIZED] 종목 코드 불일치: ${message.stock_code} !== ${stockCode}`);
        return;
      }

      console.log(`✅ [FINALIZED] 완성된 분봉 처리 시작: ${message.stock_code} ${message.candle.timestamp}`);  // ✅ data → candle
      const { candle } = message;  // ✅ data → candle
      const finalizedCandle: ChartCandle = {
        timestamp: candle.timestamp,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume,
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
          console.log(`⚠️ [FINALIZED] 중복 분봉 감지, 무시: ${finalizedCandle.timestamp}`);
          return prev;
        }
        console.log(`✅ [FINALIZED] finalizedCandles 배열에 추가: ${finalizedCandle.timestamp} (기존 ${prev.length}개 → ${prev.length + 1}개)`);
        const next = [...prev, finalizedCandle];
        if (next.length > MAX_FINALIZED_CANDLES) {
          console.log(`♻️ [FINALIZED] finalizedCandles 사이즈 제한 적용: ${next.length} → ${MAX_FINALIZED_CANDLES}`);
          return next.slice(-MAX_FINALIZED_CANDLES);
        }
        return next;
      });

      // 현재 분봉이 완성된 것이면 초기화
      setCurrentCandle(null);
      console.log('✅ [FINALIZED] currentCandle 초기화 완료');
    });
    console.log('📡 [useRealtimeMinuteCandles] minute_candle_finalized 리스너 등록 완료');  // ✅ finalize → finalized

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
