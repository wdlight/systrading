/**
 * 주문 관련 타입 정의
 * Backend order_models.py와 대응되는 TypeScript 타입
 */

/**
 * 주문 유형
 */
export enum OrderType {
  LIMIT = '00',        // 지정가
  MARKET = '01',       // 시장가
  CONDITIONAL = '02',  // 조건부지정가
  BEST = '03',        // 최유리지정가
  PRIORITY = '04'     // 최우선지정가
}

/**
 * 주문 방향
 */
export enum OrderSide {
  BUY = 'buy',   // 매수
  SELL = 'sell'  // 매도
}

/**
 * 주문 상태
 */
export enum OrderStatus {
  PENDING = 'pending',     // 접수 대기
  ACCEPTED = 'accepted',   // 접수 완료
  FILLED = 'filled',       // 체결 완료
  PARTIAL = 'partial',     // 부분 체결
  CANCELLED = 'cancelled', // 취소
  REJECTED = 'rejected'    // 거부
}

/**
 * 주문 요청
 */
export interface OrderRequest {
  stock_code: string;           // 종목 코드 (6자리)
  stock_name: string;           // 종목명
  order_type: OrderType;        // 주문 유형
  order_side: OrderSide;        // 매수/매도 구분
  quantity: number;             // 주문 수량
  price?: number;               // 주문 가격 (시장가는 0 또는 undefined)
}

/**
 * 주문 정정 요청
 */
export interface OrderModifyRequest {
  order_number: string;         // 원주문번호
  stock_code: string;           // 종목 코드
  order_type: OrderType;        // 정정 주문 유형
  quantity: number;             // 정정 수량
  price: number;                // 정정 가격
}

/**
 * 주문 취소 요청
 */
export interface OrderCancelRequest {
  order_number: string;         // 원주문번호
  stock_code: string;           // 종목 코드
  order_type: OrderType;        // 취소 주문 유형
  quantity: number;             // 취소 수량
  price: number;                // 취소 가격
}

/**
 * 주문 응답
 */
export interface OrderResponse {
  success: boolean;             // 성공 여부
  order_number?: string;        // 주문 번호
  status: string;               // 주문 상태
  message: string;              // 응답 메시지

  // 추가 정보
  stock_code?: string;          // 종목 코드
  stock_name?: string;          // 종목명
  order_side?: string;          // 매수/매도
  quantity?: number;            // 주문 수량
  price?: number;               // 주문 가격
  order_time?: string;          // 주문 시각
}

/**
 * 주문 상세 정보
 */
export interface OrderDetail {
  order_number: string;         // 주문 번호
  stock_code: string;           // 종목 코드
  stock_name: string;           // 종목명
  order_type: string;           // 주문 유형
  order_side: string;           // 매수/매도
  order_status: OrderStatus;    // 주문 상태

  // 수량 정보
  quantity: number;             // 주문 수량
  filled_quantity: number;      // 체결 수량
  remaining_quantity: number;   // 미체결 수량

  // 가격 정보
  order_price: number;          // 주문 가격
  filled_price?: number;        // 체결 가격

  // 시간 정보
  order_time: string;           // 주문 시각
  filled_time?: string;         // 체결 시각

  // 금액 정보
  order_amount: number;         // 주문 금액
  filled_amount: number;        // 체결 금액
  commission: number;           // 수수료
  tax: number;                  // 제세금

  // --- Gemini Modification Start ---
  // 디버깅을 위한 Raw 데이터 필드
  raw_filled_price?: string;
  raw_filled_quantity?: string;
  raw_filled_amount?: string;
  raw_commission?: string;
  raw_tax?: string;
  raw_filled_time?: string;
  // --- Gemini Modification End ---
}

/**
 * 미체결 주문 조회 응답
 */
export interface PendingOrdersResponse {
  success: boolean;             // 성공 여부
  message: string;              // 응답 메시지
  orders: OrderDetail[];        // 미체결 주문 목록
  total_count: number;          // 전체 미체결 주문 수
}

/**
 * 체결 내역 조회 응답
 */
export interface OrderHistoryResponse {
  success: boolean;             // 성공 여부
  message: string;              // 응답 메시지
  orders: OrderDetail[];        // 체결 내역 목록
  total_count: number;          // 전체 체결 내역 수

  // 통계 정보
  total_buy_amount: number;     // 총 매수 금액
  total_sell_amount: number;    // 총 매도 금액
  total_commission: number;     // 총 수수료
  total_tax: number;            // 총 제세금
}

/**
 * 호가 단위 정보
 */
export interface TickSize {
  min_price: number;            // 최소 가격
  max_price?: number;           // 최대 가격
  tick_size: number;            // 호가 단위
}

/**
 * 호가 단위 테이블
 */
export const TICK_SIZE_TABLE: TickSize[] = [
  { min_price: 0, max_price: 1000, tick_size: 1 },
  { min_price: 1000, max_price: 5000, tick_size: 5 },
  { min_price: 5000, max_price: 10000, tick_size: 10 },
  { min_price: 10000, max_price: 50000, tick_size: 50 },
  { min_price: 50000, max_price: 100000, tick_size: 100 },
  { min_price: 100000, max_price: 500000, tick_size: 500 },
  { min_price: 500000, max_price: undefined, tick_size: 1000 },
];

/**
 * 가격에 따른 호가 단위 반환
 */
export function getTickSize(price: number): number {
  for (const tick of TICK_SIZE_TABLE) {
    if (tick.max_price === undefined) {
      return tick.tick_size;
    }
    if (price >= tick.min_price && price < tick.max_price) {
      return tick.tick_size;
    }
  }
  return 1;
}

/**
 * 가격을 호가 단위에 맞게 조정
 */
export function adjustPriceToTick(price: number): number {
  const tickSize = getTickSize(price);
  return Math.floor(price / tickSize) * tickSize;
}

/**
 * 주문 유형 한글명
 */
export function getOrderTypeName(orderType: OrderType): string {
  switch (orderType) {
    case OrderType.LIMIT:
      return '지정가';
    case OrderType.MARKET:
      return '시장가';
    case OrderType.CONDITIONAL:
      return '조건부지정가';
    case OrderType.BEST:
      return '최유리지정가';
    case OrderType.PRIORITY:
      return '최우선지정가';
    default:
      return '알 수 없음';
  }
}

/**
 * 주문 상태 한글명
 */
export function getOrderStatusName(status: OrderStatus): string {
  switch (status) {
    case OrderStatus.PENDING:
      return '접수대기';
    case OrderStatus.ACCEPTED:
      return '접수';
    case OrderStatus.FILLED:
      return '체결';
    case OrderStatus.PARTIAL:
      return '부분체결';
    case OrderStatus.CANCELLED:
      return '취소';
    case OrderStatus.REJECTED:
      return '거부';
    default:
      return '알 수 없음';
  }
}

/**
 * 주문 금액 계산
 */
export function calculateOrderAmount(quantity: number, price: number): number {
  return quantity * price;
}

/**
 * 예상 수수료 계산 (약 0.015%)
 */
export function calculateCommission(amount: number): number {
  return Math.floor(amount * 0.00015);
}

/**
 * 매도 시 예상 제세금 계산 (약 0.23%)
 */
export function calculateTax(amount: number): number {
  return Math.floor(amount * 0.0023);
}

/**
 * 순 매수 금액 계산 (주문금액 + 수수료)
 */
export function calculateNetBuyAmount(quantity: number, price: number): number {
  const orderAmount = calculateOrderAmount(quantity, price);
  const commission = calculateCommission(orderAmount);
  return orderAmount + commission;
}

/**
 * 순 매도 금액 계산 (주문금액 - 수수료 - 제세금)
 */
export function calculateNetSellAmount(quantity: number, price: number): number {
  const orderAmount = calculateOrderAmount(quantity, price);
  const commission = calculateCommission(orderAmount);
  const tax = calculateTax(orderAmount);
  return orderAmount - commission - tax;
}
