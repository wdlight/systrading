// lib/tradingview/dataConverter.ts
import { UTCTimestamp } from 'lightweight-charts';
import { ChartCandle } from '@/lib/types/korean-stocks';
import { TRViewCandleData, TRViewVolumeData } from './types';
import { CHART_COLORS } from './constants';

/**
 * ChartCandle을 TradingView Candlestick 형식으로 변환
 *
 * ⚠️ 중요: 분봉 데이터이므로 Unix timestamp(초 단위)를 사용해야 합니다.
 * 날짜만 추출하면 모든 캔들이 하나의 시간에 겹쳐 그려지는 문제가 발생합니다.
 */
export function convertToTRViewCandles(
  chartData: ChartCandle[]
): TRViewCandleData[] {
  return chartData.map(candle => {
    // Backend가 KST 기준이면 명시적으로 +09:00 추가하여 UTC로 변환
    const kstTimestamp = candle.timestamp.includes('+') || candle.timestamp.endsWith('Z')
      ? candle.timestamp
      : candle.timestamp + '+09:00';

    return {
      time: (new Date(kstTimestamp).getTime() / 1000) as UTCTimestamp,
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
    };
  });
}

/**
 * ChartCandle을 TradingView Volume 형식으로 변환
 */
export function convertToTRViewVolumes(
  chartData: ChartCandle[]
): TRViewVolumeData[] {
  return chartData.map((candle, index) => {
    const prevClose = index > 0 ? chartData[index - 1].close : candle.open;
    const isUp = candle.close >= prevClose;

    // Backend가 KST 기준이면 명시적으로 +09:00 추가하여 UTC로 변환
    const kstTimestamp = candle.timestamp.includes('+') || candle.timestamp.endsWith('Z')
      ? candle.timestamp
      : candle.timestamp + '+09:00';

    return {
      time: (new Date(kstTimestamp).getTime() / 1000) as UTCTimestamp,
      value: candle.volume,
      color: isUp ? CHART_COLORS.VOLUME_UP : CHART_COLORS.VOLUME_DOWN
    };
  });
}
