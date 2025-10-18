// lib/tradingview/chartConfig.ts
import { ChartOptions, DeepPartial, UTCTimestamp } from 'lightweight-charts';

export function getTRViewChartOptions(
  timeframe: 'minute' | 'day' = 'minute'
): DeepPartial<ChartOptions> {
  return {
    layout: {
      background: {
        color: '#0a0a0b'  // 다크 배경
      },
      textColor: '#d1d5db',  // 텍스트 색상
      fontSize: 12,
    },
    grid: {
      vertLines: {
        color: '#1f2937',
        style: 1,  // 실선
        visible: true,
      },
      horzLines: {
        color: '#1f2937',
        style: 1,
        visible: true,
      },
    },
    crosshair: {
      mode: 1,  // Normal mode
      vertLine: {
        color: '#6b7280',
        width: 1,
        style: 3,  // 점선
        labelBackgroundColor: '#374151',
      },
      horzLine: {
        color: '#6b7280',
        width: 1,
        style: 3,
        labelBackgroundColor: '#374151',
      },
    },
    timeScale: {
      borderColor: '#374151',
      timeVisible: true,
      secondsVisible: false,
      tickMarkFormatter: (time: UTCTimestamp) => {
        const date = new Date(time * 1000);

        if (timeframe === 'day') {
          // 일봉: MM/DD 형식
          return new Intl.DateTimeFormat('ko-KR', {
            month: '2-digit',
            day: '2-digit',
            timeZone: 'Asia/Seoul',
          }).format(date).replace('. ', '/').replace('.', '');
          // "10. 15." → "10/15"
        } else {
          // 분봉: HH:MM 형식
          return new Intl.DateTimeFormat('ko-KR', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
            timeZone: 'Asia/Seoul',
          }).format(date);
        }
      },
    },
    rightPriceScale: {
      borderColor: '#374151',
      scaleMargins: {
        top: 0.1,
        bottom: 0.2,
      },
    },
  };
}
