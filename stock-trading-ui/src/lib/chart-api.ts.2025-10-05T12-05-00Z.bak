/**
 * 차트 데이터 API 클라이언트
 * 백엔드 캐시 기반 분봉 데이터 조회
 */

import { ChartCandle } from '@/lib/types/korean-stocks';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ChartAPIOptions {
  date?: string;  // YYYY-MM-DD 형식
  includeExtendedHours?: boolean;
  regularHoursOnly?: boolean;
}

export class ChartAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * 분봉 차트 데이터 조회 (캐시 기반)
   * @param stockCode 종목코드 (예: "005930")
   * @param options 조회 옵션
   * @returns 캔들 데이터 배열
   */
  async getMinuteCandles(
    stockCode: string,
    options: ChartAPIOptions = {}
  ): Promise<ChartCandle[]> {
    try {
      const params = new URLSearchParams();

      if (options.date) {
        params.append('date', options.date);
      }

      if (options.includeExtendedHours !== undefined) {
        params.append('include_extended_hours', String(options.includeExtendedHours));
      }

      if (options.regularHoursOnly !== undefined) {
        params.append('regular_hours_only', String(options.regularHoursOnly));
      }

      const queryString = params.toString();
      const url = `${this.baseUrl}/api/chart/${stockCode}/minute${queryString ? `?${queryString}` : ''}`;

      console.log('[ChartAPI] Fetching candles:', { stockCode, date: options.date, url });

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ChartCandle[] = await response.json();
      console.log(`[ChartAPI] Received ${data.length} candles for ${stockCode}, date: ${options.date || 'today'}`);

      return data;
    } catch (error) {
      console.error('[ChartAPI] Error fetching candles:', error);
      throw error;
    }
  }

  /**
   * 이전 거래일의 분봉 데이터 조회
   * @param stockCode 종목코드
   * @param currentDate 현재 날짜 (YYYY-MM-DD)
   * @returns 이전 거래일 캔들 데이터
   */
  async getPreviousDayCandles(
    stockCode: string,
    currentDate: string
  ): Promise<ChartCandle[]> {
    try {
      // 현재 날짜에서 1일 전 계산
      const date = new Date(currentDate);
      date.setDate(date.getDate() - 1);

      const previousDate = date.toISOString().split('T')[0]; // YYYY-MM-DD

      console.log('[ChartAPI] Fetching previous day:', { currentDate, previousDate });

      return await this.getMinuteCandles(stockCode, {
        date: previousDate,
        regularHoursOnly: true
      });
    } catch (error) {
      console.error('[ChartAPI] Error fetching previous day candles:', error);
      throw error;
    }
  }

  /**
   * 다음 거래일의 분봉 데이터 조회
   * @param stockCode 종목코드
   * @param currentDate 현재 날짜 (YYYY-MM-DD)
   * @returns 다음 거래일 캔들 데이터
   */
  async getNextDayCandles(
    stockCode: string,
    currentDate: string
  ): Promise<ChartCandle[]> {
    try {
      // 현재 날짜에서 1일 후 계산
      const date = new Date(currentDate);
      date.setDate(date.getDate() + 1);

      const nextDate = date.toISOString().split('T')[0]; // YYYY-MM-DD

      console.log('[ChartAPI] Fetching next day:', { currentDate, nextDate });

      return await this.getMinuteCandles(stockCode, {
        date: nextDate,
        regularHoursOnly: true
      });
    } catch (error) {
      console.error('[ChartAPI] Error fetching next day candles:', error);
      throw error;
    }
  }

  /**
   * 여러 날짜의 분봉 데이터를 일괄 조회
   * @param stockCode 종목코드
   * @param dates 날짜 배열 (YYYY-MM-DD)
   * @returns 날짜별 캔들 데이터 맵
   */
  async getMultipleDaysCandles(
    stockCode: string,
    dates: string[]
  ): Promise<Map<string, ChartCandle[]>> {
    try {
      console.log('[ChartAPI] Fetching multiple days:', { stockCode, dates });

      const results = new Map<string, ChartCandle[]>();

      // 병렬 요청으로 성능 향상
      const promises = dates.map(async (date) => {
        try {
          const candles = await this.getMinuteCandles(stockCode, { date });
          return { date, candles };
        } catch (error) {
          console.warn(`[ChartAPI] Failed to fetch data for ${date}:`, error);
          return { date, candles: [] };
        }
      });

      const responses = await Promise.all(promises);

      responses.forEach(({ date, candles }) => {
        results.set(date, candles);
      });

      console.log(`[ChartAPI] Fetched ${results.size} days of data`);
      return results;
    } catch (error) {
      console.error('[ChartAPI] Error fetching multiple days:', error);
      throw error;
    }
  }

  /**
   * 당일 전체 분봉 데이터 조회 (9:00~15:30)
   * @param stockCode 종목코드
   * @param date 조회 날짜 (YYYY-MM-DD). 미지정시 오늘
   * @returns 전체 거래시간 캔들 데이터 (391개)
   */
  async getFullDayCandles(
    stockCode: string,
    date?: string
  ): Promise<ChartCandle[]> {
    try {
      const params = new URLSearchParams();
      if (date) {
        params.append('date', date);
      }

      const queryString = params.toString();
      const url = `${this.baseUrl}/api/chart/${stockCode}/minute/full${queryString ? `?${queryString}` : ''}`;

      console.log('[ChartAPI] Fetching full day candles:', { stockCode, date, url });

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ChartCandle[] = await response.json();
      console.log(`[ChartAPI] Received ${data.length} full day candles for ${stockCode}, date: ${date || 'today'}`);

      return data;
    } catch (error) {
      console.error('[ChartAPI] Error fetching full day candles:', error);
      throw error;
    }
  }

  /**
   * 현재 분봉 데이터 조회 (실시간 업데이트용)
   * @param stockCode 종목코드
   * @returns 현재 분의 최신 캔들 데이터
   */
  async getCurrentMinuteCandle(stockCode: string): Promise<ChartCandle> {
    try {
      const url = `${this.baseUrl}/api/chart/${stockCode}/minute/current`;

      console.log('[ChartAPI] Fetching current minute candle:', { stockCode, url });

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const candle: ChartCandle = await response.json();
      console.log(`[ChartAPI] Current candle received:`, {
        timestamp: candle.timestamp,
        volume: candle.volume,
        close: candle.close
      });

      return candle;
    } catch (error) {
      console.error('[ChartAPI] Error fetching current minute candle:', error);
      throw error;
    }
  }

  /**
   * 캐시 통계 조회
   * @param stockCode 종목코드
   * @returns 캐시 통계 정보
   */
  async getCacheStats(stockCode: string): Promise<unknown> {
    try {
      const url = `${this.baseUrl}/api/chart/cache/stats/${stockCode}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[ChartAPI] Error fetching cache stats:', error);
      throw error;
    }
  }
}

// 싱글톤 인스턴스
export const chartAPI = new ChartAPI();