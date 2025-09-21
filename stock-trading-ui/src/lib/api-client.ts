import { 
  AccountBalance, 
  TradingConditions, 
  WatchlistItem, 
  OrderRequest, 
  Order, 
  ApiResponse,
  MarketOverview,
  ApiError
} from './types';
import { API_CONFIG } from './constants';
import { getErrorMessage } from './utils';

/**
 * FastAPI 백엔드와 통신하는 API 클라이언트
 */
export class TradingAPIClient {
  private baseURL: string;
  private timeout: number;
  private retryAttempts: number;
  private retryDelay: number;

  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
    this.retryAttempts = API_CONFIG.RETRY_ATTEMPTS;
    this.retryDelay = API_CONFIG.RETRY_DELAY;
  }

  /**
   * HTTP 요청 헬퍼 메서드
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // AbortController로 타임아웃 구현
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      const data = await response.json();
      return data.data || data; // API 응답 구조에 맞게 조정
    } catch (error) {
      clearTimeout(timeoutId);
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error('요청 시간이 초과되었습니다.');
      }
      
      throw new Error(getErrorMessage(error));
    }
  }

  /**
   * 재시도 로직이 포함된 요청 메서드
   */
  private async requestWithRetry<T>(
    endpoint: string,
    options: RequestInit = {},
    attempt: number = 1
  ): Promise<T> {
    try {
      return await this.request<T>(endpoint, options);
    } catch (error) {
      if (attempt < this.retryAttempts) {
        await new Promise(resolve => 
          setTimeout(resolve, this.retryDelay * attempt)
        );
        return this.requestWithRetry<T>(endpoint, options, attempt + 1);
      }
      throw error;
    }
  }

  // ===================
  // 계좌 관련 API
  // ===================

  /**
   * 계좌 잔고 조회
   */
  async getAccountBalance(): Promise<AccountBalance> {
    return this.requestWithRetry<AccountBalance>('/api/account/balance');
  }

  /**
   * 계좌 요약 정보 조회
   */
  async getAccountSummary(): Promise<any> {
    return this.requestWithRetry('/api/account/summary');
  }

  /**
   * 보유 종목 목록 조회
   */
  async getPositions(): Promise<any[]> {
    return this.requestWithRetry('/api/account/positions');
  }

  /**
   * 계좌 정보 갱신
   */
  async refreshAccountInfo(): Promise<void> {
    return this.requestWithRetry('/api/account/refresh', {
      method: 'POST',
    });
  }

  // ===================
  // 매매 조건 관련 API
  // ===================

  /**
   * 매매 조건 조회
   */
  async getTradingConditions(): Promise<TradingConditions> {
    return this.requestWithRetry<TradingConditions>('/api/trading/conditions');
  }

  /**
   * 매매 조건 설정
   */
  async updateTradingConditions(
    conditions: Partial<TradingConditions>
  ): Promise<void> {
    return this.requestWithRetry('/api/trading/conditions', {
      method: 'POST',
      body: JSON.stringify(conditions),
    });
  }

  /**
   * 자동매매 시작
   */
  async startTrading(): Promise<void> {
    return this.requestWithRetry('/api/trading/start', {
      method: 'POST',
    });
  }

  /**
   * 자동매매 중지
   */
  async stopTrading(): Promise<void> {
    return this.requestWithRetry('/api/trading/stop', {
      method: 'POST',
    });
  }

  /**
   * 매매 상태 조회
   */
  async getTradingStatus(): Promise<any> {
    return this.requestWithRetry('/api/trading/status');
  }

  // ===================
  // 워치리스트 관련 API
  // ===================

  /**
   * 워치리스트 조회
   */
  async getWatchlist(): Promise<WatchlistItem[]> {
    return this.requestWithRetry<WatchlistItem[]>('/api/watchlist');
  }

  /**
   * 워치리스트에 종목 추가
   */
  async addToWatchlist(stockCode: string): Promise<void> {
    return this.requestWithRetry(`/api/watchlist/add/${stockCode}`, {
      method: 'POST',
    });
  }

  /**
   * 워치리스트에서 종목 제거
   */
  async removeFromWatchlist(stockCode: string): Promise<void> {
    return this.requestWithRetry(`/api/watchlist/${stockCode}`, {
      method: 'DELETE',
    });
  }

  /**
   * 특정 종목의 기술적 지표 조회
   */
  async getStockIndicators(stockCode: string): Promise<any> {
    return this.requestWithRetry(`/api/watchlist/${stockCode}/indicators`);
  }

  // ===================
  // 주문 관련 API
  // ===================

  /**
   * 매수 주문
   */
  async buyOrder(orderRequest: OrderRequest): Promise<Order> {
    return this.requestWithRetry<Order>('/api/trading/orders/buy', {
      method: 'POST',
      body: JSON.stringify(orderRequest),
    });
  }

  /**
   * 매도 주문
   */
  async sellOrder(orderRequest: OrderRequest): Promise<Order> {
    return this.requestWithRetry<Order>('/api/trading/orders/sell', {
      method: 'POST',
      body: JSON.stringify(orderRequest),
    });
  }

  /**
   * 주문 내역 조회
   */
  async getOrderHistory(): Promise<Order[]> {
    return this.requestWithRetry<Order[]>('/api/orders/history');
  }

  /**
   * 미체결 주문 조회
   */
  async getPendingOrders(): Promise<Order[]> {
    return this.requestWithRetry<Order[]>('/api/orders/pending');
  }

  /**
   * 주문 취소
   */
  async cancelOrder(orderId: string): Promise<void> {
    return this.requestWithRetry(`/api/orders/${orderId}/cancel`, {
      method: 'POST',
    });
  }

  // ===================
  // 시장 정보 API
  // ===================

  /**
   * 시장 현황 조회
   */
  async getMarketOverview(): Promise<MarketOverview> {
    return this.requestWithRetry<MarketOverview>('/api/market/overview');
  }

  /**
   * 상위 급등주 조회
   */
  async getTopGainers(): Promise<any[]> {
    return this.requestWithRetry('/api/market/top-gainers');
  }

  /**
   * 거래량 상위 조회
   */
  async getMostActive(): Promise<any[]> {
    return this.requestWithRetry('/api/market/most-active');
  }

  // ===================
  // 헬스체크
  // ===================

  /**
   * 서버 상태 확인
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health');
  }

  /**
   * API 연결 테스트
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch {
      return false;
    }
  }
}

// 싱글톤 인스턴스 생성
export const apiClient = new TradingAPIClient();

// React 컴포넌트에서 사용할 수 있는 헬퍼 함수들
export async function fetchWithErrorHandling<T>(
  apiCall: () => Promise<T>
): Promise<{ data: T | null; error: string | null }> {
  try {
    const data = await apiCall();
    return { data, error: null };
  } catch (error) {
    console.error('API 호출 오류:', error);
    return { data: null, error: getErrorMessage(error) };
  }
}