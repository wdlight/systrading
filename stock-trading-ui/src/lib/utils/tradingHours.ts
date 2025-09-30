/**
 * 한국 주식시장 거래시간 관리 유틸리티
 *
 * 정규 장: 09:00 ~ 15:30
 * 시간외 종가: 08:30 ~ 09:00
 * 시간외 단일가: 15:30 ~ 16:00
 */

export enum TradingSession {
  PRE_MARKET = 'pre_market',      // 8:30 ~ 9:00 (시간외 종가)
  REGULAR = 'regular',             // 9:00 ~ 15:30 (정규 장)
  AFTER_MARKET = 'after_market',   // 15:30 ~ 16:00 (시간외 단일가)
  CLOSED = 'closed'                // 장 외 시간
}

export interface TimeRange {
  hour: number;
  minute: number;
}

export class TradingHoursManager {
  private static readonly REGULAR_MARKET_START: TimeRange = { hour: 9, minute: 0 };
  private static readonly REGULAR_MARKET_END: TimeRange = { hour: 15, minute: 30 };
  private static readonly PRE_MARKET_START: TimeRange = { hour: 8, minute: 30 };
  private static readonly AFTER_MARKET_END: TimeRange = { hour: 16, minute: 0 };

  /**
   * 주어진 시간의 거래 세션 반환
   */
  static getSession(date: Date): TradingSession {
    const hour = date.getHours();
    const minute = date.getMinutes();

    if (this.isTimeBetween(hour, minute, this.PRE_MARKET_START, this.REGULAR_MARKET_START)) {
      return TradingSession.PRE_MARKET;
    } else if (this.isTimeBetween(hour, minute, this.REGULAR_MARKET_START, this.REGULAR_MARKET_END)) {
      return TradingSession.REGULAR;
    } else if (this.isTimeBetween(hour, minute, this.REGULAR_MARKET_END, this.AFTER_MARKET_END)) {
      return TradingSession.AFTER_MARKET;
    } else {
      return TradingSession.CLOSED;
    }
  }

  /**
   * 정규 장 시간 여부
   */
  static isRegularHours(date: Date): boolean {
    return this.getSession(date) === TradingSession.REGULAR;
  }

  /**
   * 거래 시간 여부 (시간외 포함 옵션)
   */
  static isTradingHours(date: Date, includeExtended: boolean = false): boolean {
    const session = this.getSession(date);
    if (includeExtended) {
      return [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_MARKET].includes(session);
    }
    return session === TradingSession.REGULAR;
  }

  /**
   * 오늘 날짜인지 확인
   */
  static isToday(date: Date): boolean {
    const today = new Date();
    return date.toDateString() === today.toDateString();
  }

  /**
   * 다음 리셋 시간 (다음날 0시)
   */
  static getNextResetTime(): Date {
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    return tomorrow;
  }

  /**
   * 리셋까지 남은 시간 (밀리초)
   */
  static getTimeUntilReset(): number {
    const now = new Date();
    const nextReset = this.getNextResetTime();
    return nextReset.getTime() - now.getTime();
  }

  /**
   * 리셋까지 남은 시간 포맷팅
   */
  static formatTimeUntilReset(): string {
    const remaining = this.getTimeUntilReset();
    const hours = Math.floor(remaining / (1000 * 60 * 60));
    const minutes = Math.floor((remaining % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((remaining % (1000 * 60)) / 1000);
    return `${hours}시간 ${minutes}분 ${seconds}초`;
  }

  /**
   * 정규 장 시작/종료 시간
   */
  static getRegularMarketRange(date?: Date): { start: Date; end: Date } {
    const targetDate = date || new Date();
    const start = new Date(targetDate);
    start.setHours(this.REGULAR_MARKET_START.hour, this.REGULAR_MARKET_START.minute, 0, 0);

    const end = new Date(targetDate);
    end.setHours(this.REGULAR_MARKET_END.hour, this.REGULAR_MARKET_END.minute, 0, 0);

    return { start, end };
  }

  /**
   * 시간외 거래 포함 시간 범위
   */
  static getExtendedMarketRange(date?: Date): { start: Date; end: Date } {
    const targetDate = date || new Date();
    const start = new Date(targetDate);
    start.setHours(this.PRE_MARKET_START.hour, this.PRE_MARKET_START.minute, 0, 0);

    const end = new Date(targetDate);
    end.setHours(this.AFTER_MARKET_END.hour, this.AFTER_MARKET_END.minute, 0, 0);

    return { start, end };
  }

  /**
   * 거래 세션 표시명
   */
  static getSessionDisplayName(session: TradingSession): string {
    switch (session) {
      case TradingSession.PRE_MARKET:
        return '시간외 종가';
      case TradingSession.REGULAR:
        return '정규장';
      case TradingSession.AFTER_MARKET:
        return '시간외 단일가';
      case TradingSession.CLOSED:
        return '장 외 시간';
    }
  }

  /**
   * 시간 범위 체크 유틸리티
   */
  private static isTimeBetween(
    hour: number,
    minute: number,
    start: TimeRange,
    end: TimeRange
  ): boolean {
    const timeInMinutes = hour * 60 + minute;
    const startInMinutes = start.hour * 60 + start.minute;
    const endInMinutes = end.hour * 60 + end.minute;
    return timeInMinutes >= startInMinutes && timeInMinutes < endInMinutes;
  }
}