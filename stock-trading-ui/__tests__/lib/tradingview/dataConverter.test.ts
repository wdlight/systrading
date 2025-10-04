
import { describe, it, expect } from '@jest/globals';
import { convertToTRViewCandles, convertToTRViewVolumes } from '../../../src/lib/tradingview/dataConverter';
import { ChartCandle } from '../../../src/lib/types/korean-stocks';

describe('TradingView Data Converter', () => {
  const mockChartData: ChartCandle[] = [
    {
      timestamp: '2025-01-04T09:00:00',
      open: 75000,
      high: 75500,
      low: 74800,
      close: 75200,
      volume: 123456,
    },
    {
      timestamp: '2025-01-04T09:01:00',
      open: 75200,
      high: 75800,
      low: 75100,
      close: 75600,
      volume: 234567,
    },
  ];

  describe('convertToTRViewCandles', () => {
    it('should convert ChartCandle to TRViewCandleData with Unix timestamp', () => {
      const result = convertToTRViewCandles(mockChartData);

      expect(result).toHaveLength(2);

      // 첫 번째 캔들 검증
      expect(result[0].time).toBe(new Date('2025-01-04T09:00:00').getTime() / 1000);
      expect(result[0].open).toBe(75000);
      expect(result[0].high).toBe(75500);
      expect(result[0].low).toBe(74800);
      expect(result[0].close).toBe(75200);

      // 두 번째 캔들 검증
      expect(result[1].time).toBe(new Date('2025-01-04T09:01:00').getTime() / 1000);
      expect(result[1].close).toBe(75600);
    });

    it('should preserve data order', () => {
      const result = convertToTRViewCandles(mockChartData);

      expect(result[0].time).toBeLessThan(result[1].time);
    });
  });

  describe('convertToTRViewVolumes', () => {
    it('should convert ChartCandle to TRViewVolumeData with colors', () => {
      const result = convertToTRViewVolumes(mockChartData);

      expect(result).toHaveLength(2);

      // 첫 번째 거래량 (상승 - 빨강)
      expect(result[0].value).toBe(123456);
      expect(result[0].color).toBe('rgba(239, 68, 68, 0.5)');

      // 두 번째 거래량 (상승 - 빨강)
      expect(result[1].value).toBe(234567);
      expect(result[1].color).toBe('rgba(239, 68, 68, 0.5)');
    });

    it('should use blue color for declining candles', () => {
      const decliningData: ChartCandle[] = [
        { ...mockChartData[0], close: 75000 },
        { ...mockChartData[1], close: 74500 }, // 하락
      ];

      const result = convertToTRViewVolumes(decliningData);

      expect(result[1].color).toBe('rgba(59, 130, 246, 0.5)'); // 파랑
    });
  });
});
