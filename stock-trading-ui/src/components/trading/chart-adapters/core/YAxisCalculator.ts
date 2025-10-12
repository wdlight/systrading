/**
 * Y축 계산 추상화
 * 다양한 Y축 계산 전략을 지원하기 위한 Strategy Pattern
 */

import { ChartCandle } from '@/lib/types/korean-stocks';
import { getTickUnitByPrice } from '@/lib/utils';

/**
 * Y축 도메인 (최소값, 최대값)
 */
export type YAxisDomain = [number, number];

/**
 * Y축 계산 전략 인터페이스
 */
export interface YAxisCalculator {
  /**
   * 차트 데이터로부터 Y축 도메인 계산
   * @param data 차트 캔들 데이터
   * @returns [최소값, 최대값]
   */
  calculate(data: ChartCandle[]): YAxisDomain;

  /**
   * 계산 전략 이름
   */
  readonly name: string;
}

/**
 * 일별 최고/최저 기준 90% 범위 계산기
 * - 실제 가격 변동의 90%를 차지하도록 상하 5%씩 패딩 추가
 * - 호가 단위로 깔끔하게 정렬
 */
export class DailyRangeYAxisCalculator implements YAxisCalculator {
  readonly name = 'DailyRange90%';

  private readonly paddingRatio: number;

  constructor(paddingRatio: number = 0.05) {
    this.paddingRatio = paddingRatio;
  }

  calculate(data: ChartCandle[]): YAxisDomain {
    if (!data || data.length === 0) {
      return [0, 0];
    }

    // 실제 가격 범위 계산
    const actualPrices = data.flatMap(d => [d.high, d.low]);
    const actualMin = Math.min(...actualPrices);
    const actualMax = Math.max(...actualPrices);

    // 가격 범위
    const priceRange = actualMax - actualMin;

    // 패딩 계산 (기본 5%)
    const padding = priceRange * this.paddingRatio;
    const rawLowerLimit = actualMin - padding;
    const rawUpperLimit = actualMax + padding;

    // 호가 단위로 정렬
    const avgPrice = (actualMin + actualMax) / 2;
    const tickUnit = getTickUnitByPrice(avgPrice);

    const finalLowerLimit = Math.floor(rawLowerLimit / tickUnit) * tickUnit;
    const finalUpperLimit = Math.ceil(rawUpperLimit / tickUnit) * tickUnit;

    return [finalLowerLimit, finalUpperLimit];
  }
}

/**
 * 시초가 기준 ±30% 범위 계산기 (상한가/하한가)
 * - 한국 주식 시장의 가격 제한폭 반영
 * - 시초가 대비 ±30% 범위 고정
 */
export class PriceLimitYAxisCalculator implements YAxisCalculator {
  readonly name = 'PriceLimit±30%';

  private readonly limitRatio: number;

  constructor(limitRatio: number = 0.30) {
    this.limitRatio = limitRatio;
  }

  calculate(data: ChartCandle[]): YAxisDomain {
    if (!data || data.length === 0) {
      return [0, 0];
    }

    // 시초가 = 첫 캔들의 open
    const openingPrice = data[0].open;

    // ±30% 범위
    const rawLowerLimit = openingPrice * (1 - this.limitRatio);
    const rawUpperLimit = openingPrice * (1 + this.limitRatio);

    // 호가 단위로 정렬
    const tickUnit = getTickUnitByPrice(openingPrice);

    const finalLowerLimit = Math.floor(rawLowerLimit / tickUnit) * tickUnit;
    const finalUpperLimit = Math.ceil(rawUpperLimit / tickUnit) * tickUnit;

    return [finalLowerLimit, finalUpperLimit];
  }
}

/**
 * 보이는 영역 기반 동적 Y축 계산기
 * - 현재 화면에 보이는 데이터만 기준으로 Y축 계산
 * - Drag 시 Y축이 변경됨 (동적 확대/축소)
 */
export class VisibleRangeYAxisCalculator implements YAxisCalculator {
  readonly name = 'VisibleRange';

  private readonly paddingRatio: number;

  constructor(paddingRatio: number = 0.1) {
    this.paddingRatio = paddingRatio;
  }

  calculate(data: ChartCandle[]): YAxisDomain {
    if (!data || data.length === 0) {
      return [0, 0];
    }

    // 보이는 데이터의 가격 범위
    const prices = data.flatMap(d => [d.open, d.high, d.low, d.close]);
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);

    // 패딩 추가
    const range = maxPrice - minPrice;
    const padding = range * this.paddingRatio;

    // 호가 단위로 정렬
    const avgPrice = (minPrice + maxPrice) / 2;
    const tickUnit = getTickUnitByPrice(avgPrice);

    const finalLowerLimit = Math.floor((minPrice - padding) / tickUnit) * tickUnit;
    const finalUpperLimit = Math.ceil((maxPrice + padding) / tickUnit) * tickUnit;

    return [finalLowerLimit, finalUpperLimit];
  }
}

/**
 * Y축 계산기 팩토리
 */
export class YAxisCalculatorFactory {
  private static calculators: Map<string, YAxisCalculator> = new Map<string, YAxisCalculator>([
    ['daily-range', new DailyRangeYAxisCalculator() as YAxisCalculator],
    ['price-limit', new PriceLimitYAxisCalculator() as YAxisCalculator],
    ['visible-range', new VisibleRangeYAxisCalculator() as YAxisCalculator],
  ]);

  /**
   * 계산기 가져오기
   * @param type 계산기 타입
   * @returns Y축 계산기
   */
  static get(type: string = 'daily-range'): YAxisCalculator {
    const calculator = this.calculators.get(type);
    if (!calculator) {
      console.warn(`Unknown Y-axis calculator type: ${type}, using default`);
      return this.calculators.get('daily-range')!;
    }
    return calculator;
  }

  /**
   * 커스텀 계산기 등록
   * @param name 계산기 이름
   * @param calculator 계산기 인스턴스
   */
  static register(name: string, calculator: YAxisCalculator): void {
    this.calculators.set(name, calculator);
  }

  /**
   * 사용 가능한 계산기 목록
   */
  static getAvailableCalculators(): string[] {
    return Array.from(this.calculators.keys());
  }
}

/**
 * 기본 Y축 계산기 (일별 범위 90%)
 */
export const defaultYAxisCalculator = new DailyRangeYAxisCalculator();
