/**
 * datetime 유틸리티 함수 테스트
 */

import { getKSTToday, isKSTToday, formatKSTDate } from '../datetime';

describe('KST Datetime Utilities', () => {
  describe('getKSTToday', () => {
    it('한국 시간 자정 직후에도 정확한 날짜 반환', () => {
      // Mock: 2025-10-04 00:30 KST = 2025-10-03 15:30 UTC
      const mockDate = new Date('2025-10-03T15:30:00.000Z');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

      const result = getKSTToday();
      expect(result).toBe('2025-10-04'); // KST 기준 10월 4일

      (global.Date as any).mockRestore();
    });

    it('한국 시간 오후에도 정확한 날짜 반환', () => {
      // Mock: 2025-10-03 14:00 KST = 2025-10-03 05:00 UTC
      const mockDate = new Date('2025-10-03T05:00:00.000Z');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

      const result = getKSTToday();
      expect(result).toBe('2025-10-03'); // KST 기준 10월 3일

      (global.Date as any).mockRestore();
    });

    it('한국 시간 자정 직전에도 정확한 날짜 반환', () => {
      // Mock: 2025-10-03 23:59 KST = 2025-10-03 14:59 UTC
      const mockDate = new Date('2025-10-03T14:59:00.000Z');
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

      const result = getKSTToday();
      expect(result).toBe('2025-10-03'); // KST 기준 10월 3일

      (global.Date as any).mockRestore();
    });
  });

  describe('isKSTToday', () => {
    it('KST 기준 오늘 날짜면 true', () => {
      const mockDate = new Date('2025-10-03T15:30:00.000Z'); // KST 2025-10-04 00:30
      jest.spyOn(global, 'Date').mockImplementation(() => mockDate as any);

      expect(isKSTToday('2025-10-04')).toBe(true);
      expect(isKSTToday('2025-10-03')).toBe(false); // 어제

      (global.Date as any).mockRestore();
    });
  });

  describe('formatKSTDate', () => {
    it('Date 객체를 KST 기준 날짜로 변환', () => {
      // UTC 2025-10-03 15:30 = KST 2025-10-04 00:30
      const date = new Date('2025-10-03T15:30:00.000Z');
      const result = formatKSTDate(date);
      expect(result).toBe('2025-10-04');
    });

    it('Date 객체를 KST 기준 날짜로 변환 (오후)', () => {
      // UTC 2025-10-03 05:00 = KST 2025-10-03 14:00
      const date = new Date('2025-10-03T05:00:00.000Z');
      const result = formatKSTDate(date);
      expect(result).toBe('2025-10-03');
    });
  });
});
