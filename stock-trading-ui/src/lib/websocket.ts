import {
  RealtimeMessage,
  ConnectionState,
  AccountUpdate,
  WatchlistUpdate,
  PriceUpdate,
  TradingStatusUpdate,
  OrderUpdate,
  ConnectionStatus,
  OrderBookUpdate,
  MarketStatusUpdate,
  MarketIndexUpdate,  // ✅ 추가
  MinuteCandleUpdateMessage,
  MinuteCandleFinalizedMessage  // ✅ Finalize → Finalized
} from './types';
import { API_CONFIG, WS_MESSAGE_TYPES } from './constants';

/**
 * WebSocket 연결 관리 클래스
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectDelay: number = 2000;
  private isManualClose: boolean = false;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();
  private connectionStateListeners: Set<(state: ConnectionState) => void> = new Set();
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private pendingSubscriptions: Set<string> = new Set();
  private connectionState: ConnectionState = {
    status: 'disconnected',
    reconnectAttempts: 0,
  };

  constructor() {
    this.url = API_CONFIG.WS_URL;
    console.log('🔧 WebSocketManager 생성됨:', this.url);
  }

  /**
   * WebSocket 연결
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // 이미 연결되어 있으면 재연결 스킵
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          console.log('✅ WebSocket 이미 연결됨, 재연결 스킵');
          resolve();
          return;
        }

        // 연결 시도 중이면 스킵
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          console.log('⏳ WebSocket 연결 중, 재연결 스킵');
          resolve();
          return;
        }

        // 실제 WebSocket 연결 수행
        console.log('🚀 WebSocket 연결 시도:', this.url);
        this.isManualClose = false;
        this.updateConnectionState({ status: 'connecting' });

        this.ws = new WebSocket(this.url);
        console.log('📡 WebSocket 객체 생성됨');

        this.ws.onopen = () => {
          console.log('WebSocket 연결됨');
          this.reconnectAttempts = 0;
          this.updateConnectionState({
            status: 'connected',
            lastConnected: new Date(),
            reconnectAttempts: 0,
            error: undefined,
          });
          this.startHeartbeat();

          // 재연결 시 구독 복원
          this.restorePendingSubscriptions();

          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: RealtimeMessage = JSON.parse(event.data);

            // WebSocket 로깅 (샘플링)
            this.logWebSocketMessage(message, 'received');

            this.handleMessage(message);
          } catch (error) {
          console.error('WebSocket 메시지 파싱 오류:', error, event.data);
        }
      };

        this.ws.onclose = (event) => {
          console.log('WebSocket 연결 해제:', {
            code: event.code,
            reason: event.reason || '알 수 없는 이유',
            wasClean: event.wasClean,
            url: this.url
          });
          this.stopHeartbeat();

          if (!this.isManualClose) {
            // 정상 종료가 아닌 경우만 재연결 시도
            if (event.code !== 1000 && event.code !== 1001) {
              this.updateConnectionState({ status: 'disconnected' });
              this.scheduleReconnect();
            } else {
              this.updateConnectionState({
                status: 'disconnected',
                error: '서버에 의해 연결이 정상 종료되었습니다.'
              });
            }
          }
        };

        this.ws.onerror = (error) => {
          console.error('❌ WebSocket 오류 발생:', error);
          console.error('에러 이벤트:', {
            type: error.type,
            readyState: this.ws?.readyState,
            url: this.url
          });

          let errorMessage = 'WebSocket 연결 오류가 발생했습니다.';
          if (this.ws?.readyState === WebSocket.CLOSED) {
            errorMessage = '서버와의 연결이 끊어졌습니다.';
          } else if (this.ws?.readyState === WebSocket.CLOSING) {
            errorMessage = '연결을 종료하는 중입니다.';
          }

          this.updateConnectionState({
            status: 'disconnected',
            error: errorMessage,
          });
          reject(new Error(`WebSocket 연결 실패: ${errorMessage}`));
        };

        // 연결 타임아웃 (10초)
        setTimeout(() => {
          if (this.ws?.readyState === WebSocket.CONNECTING) {
            this.ws.close();
            reject(new Error('WebSocket 연결 시간 초과'));
          }
        }, 10000);

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * WebSocket 연결 해제
   */
  disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.updateConnectionState({ status: 'disconnected' });
  }

  /**
   * 메시지 전송
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket이 연결되지 않음. 메시지 전송 실패:', message);
    }
  }

  /**
   * 특정 메시지 타입에 대한 리스너 등록
   */
  on<T>(messageType: string, callback: (data: T) => void): void {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, new Set());
    }
    this.listeners.get(messageType)!.add(callback);
  }

  /**
   * 리스너 제거
   */
  off(messageType: string, callback: (data: any) => void): void {
    const listeners = this.listeners.get(messageType);
    if (listeners) {
      listeners.delete(callback);
      if (listeners.size === 0) {
        this.listeners.delete(messageType);
      }
    }
  }

  /**
   * 연결 상태 변경 리스너 등록
   */
  onConnectionStateChange(callback: (state: ConnectionState) => void): void {
    this.connectionStateListeners.add(callback);
  }

  /**
   * 연결 상태 변경 리스너 제거
   */
  offConnectionStateChange(callback: (state: ConnectionState) => void): void {
    this.connectionStateListeners.delete(callback);
  }

  /**
   * 현재 연결 상태 반환
   */
  getConnectionState(): ConnectionState {
    return { ...this.connectionState };
  }

  /**
   * 연결 여부 확인
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  addPendingSubscription(stockCode: string): void {
    this.pendingSubscriptions.add(stockCode);
    console.log(`📝 구독 대기 목록에 추가: ${stockCode}`);
  }

  removePendingSubscription(stockCode: string): void {
    this.pendingSubscriptions.delete(stockCode);
    console.log(`📝 구독 대기 목록에서 제거: ${stockCode}`);
  }

  private restorePendingSubscriptions(): void {
    if (this.pendingSubscriptions.size === 0) {
      return;
    }
    console.log(`🔄 ${this.pendingSubscriptions.size}개 구독 복원 중...`);
    this.pendingSubscriptions.forEach((stockCode) => {
      this.send({
        type: 'subscribe',
        stock_code: stockCode,
      });
      console.log(`🔄 구독 복원: ${stockCode}`);
    });
  }

  /**
   * 메시지 처리
   */
  private handleMessage(message: RealtimeMessage): void {
    const { type } = message;

    // 디버그: 모든 메시지 로그
    // console.log('🔍 WebSocket 메시지 수신:', { type, message });

    // 타입별 특수 처리
    switch (type) {
      case WS_MESSAGE_TYPES.CONNECTION_STATUS:
        this.handleConnectionStatus((message as ConnectionStatus).data);
        break;
      case WS_MESSAGE_TYPES.ACCOUNT_UPDATE:
        this.notifyListeners(type, (message as AccountUpdate).data);
        break;
      case WS_MESSAGE_TYPES.WATCHLIST_UPDATE:
        this.notifyListeners(type, (message as WatchlistUpdate).data);
        break;
      case WS_MESSAGE_TYPES.PRICE_UPDATE:
        this.notifyListeners(type, (message as PriceUpdate).data);
        break;
      case WS_MESSAGE_TYPES.TRADING_STATUS:
        this.notifyListeners(type, (message as TradingStatusUpdate).data);
        break;
      case WS_MESSAGE_TYPES.ORDER_UPDATE:
        this.notifyListeners(type, (message as OrderUpdate).data);
        break;
      case WS_MESSAGE_TYPES.MARKET_INDEX_UPDATE:
        this.notifyListeners(type, (message as MarketIndexUpdate).data);
        break;
      case WS_MESSAGE_TYPES.MINUTE_CANDLE_UPDATE:
        // ✅ 분봉 업데이트 메시지는 전체 메시지 객체를 전달 (candle 필드 포함)
        this.notifyListeners(type, message as MinuteCandleUpdateMessage);
        console.log('🔍 WebSocket 메시지 MINUTE_CANDLE_UPDATE :', { type, candle: (message as MinuteCandleUpdateMessage).candle });
        break;
      case WS_MESSAGE_TYPES.MINUTE_CANDLE_FINALIZED:  // ✅ FINALIZE → FINALIZED
        // ✅ 분봉 완료 메시지는 전체 메시지 객체를 전달 (candle 필드 포함)
        this.notifyListeners(type, message as MinuteCandleFinalizedMessage);
        console.log('🔍 WebSocket 메시지 MINUTE_CANDLE_FINALIZED :', { type, candle: (message as MinuteCandleFinalizedMessage).candle });
        break;
      case 'orderbook_update':
        // console.log('📊 호가 업데이트 메시지 수신:', data);
        this.notifyListeners(type, (message as OrderBookUpdate).data);
        break;
      case 'market_status_update':
        this.notifyListeners(type, (message as MarketStatusUpdate).data);
        break;
      case WS_MESSAGE_TYPES.HEARTBEAT:
        // 서버 하트비트 - 연결 유지 메시지 (조용히 처리)
        break;
      case WS_MESSAGE_TYPES.PONG:
        // ping 응답 - 연결 상태 확인 (조용히 처리)
        break;
      default:
        console.warn('알 수 없는 메시지 타입:', type);
    }
  }

  /**
   * 연결 상태 메시지 처리
   */
  private handleConnectionStatus(data: ConnectionStatus['data']): void {
    this.updateConnectionState({
      status: data.status,
      error: data.error_message,
    });
  }

  /**
   * 리스너들에게 메시지 전달
   */
  private notifyListeners(messageType: string, data: any): void {
    const listeners = this.listeners.get(messageType);
    // console.log(`🔔 notifyListeners 호출: ${messageType}, 리스너 수: ${listeners?.size || 0}`, data);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          // console.log(`📤 리스너 실행: ${messageType}`);
          callback(data);
        } catch (error) {
          console.error(`리스너 실행 오류 (${messageType}):`, error);
        }
      });
    } else {
      console.warn(`⚠️ ${messageType}에 대한 리스너가 없습니다`);
    }
  }

  /**
   * 연결 상태 업데이트
   */
  private updateConnectionState(updates: Partial<ConnectionState>): void {
    this.connectionState = { ...this.connectionState, ...updates };
    this.connectionStateListeners.forEach(callback => {
      try {
        callback(this.connectionState);
      } catch (error) {
        console.error('연결 상태 리스너 실행 오류:', error);
      }
    });
  }

  /**
   * 재연결 스케줄링
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(`최대 재연결 횟수 초과 (${this.maxReconnectAttempts}회)`);
      this.updateConnectionState({
        status: 'disconnected',
        error: `최대 재연결 횟수를 초과했습니다. (${this.maxReconnectAttempts}회)`,
      });
      return;
    }

    this.reconnectAttempts++;
    // 최대 30초까지만 지연
    const delay = Math.min(this.reconnectDelay * Math.pow(1.5, this.reconnectAttempts - 1), 30000);

    console.log(`${Math.round(delay / 1000)}초 후 재연결 시도 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    this.updateConnectionState({
      status: 'reconnecting',
      reconnectAttempts: this.reconnectAttempts,
      error: `재연결 시도 중... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
    });

    setTimeout(() => {
      if (!this.isManualClose && this.reconnectAttempts <= this.maxReconnectAttempts) {
        console.log(`재연결 시도 시작: ${this.url}`);
        this.connect().catch(error => {
          console.error(`재연결 실패 (${this.reconnectAttempts}회):`, error.message);
        });
      }
    }, delay);
  }

  /**
   * 하트비트 시작
   */
  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping', timestamp: Date.now() });
      }
    }, 30000); // 30초마다 ping
  }

  /**
   * 하트비트 중지
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 메시지 타입별 리스너 등록
   */
  subscribe(messageType: string, listener: (data: any) => void): void {
    if (!this.listeners.has(messageType)) {
      this.listeners.set(messageType, new Set());
    }
    this.listeners.get(messageType)!.add(listener);
  }

  /**
   * 메시지 타입별 리스너 해제
   */
  unsubscribe(messageType: string, listener: (data: any) => void): void {
    if (this.listeners.has(messageType)) {
      this.listeners.get(messageType)!.delete(listener);
    }
  }

  /**
   * WebSocket 메시지 로깅 (샘플링)
   */
  private messageCounts: Map<string, number> = new Map();
  private lastLogTimes: Map<string, number> = new Map();
  private readonly LOG_INTERVAL_MS = 60000; // 1분
  private readonly LOG_COUNT_THRESHOLD = 100; // 100개마다

  private logWebSocketMessage(message: any, direction: 'received' | 'sent'): void {
    const messageType = message.type || 'unknown';
    const currentTime = Date.now();
    const currentCount = (this.messageCounts.get(messageType) || 0) + 1;

    this.messageCounts.set(messageType, currentCount);

    // 로깅 조건 체크
    const shouldLog = this.shouldLogMessage(messageType, currentTime, currentCount);

    if (shouldLog) {
      const logData = {
        type: messageType,
        direction,
        count: currentCount,
        timestamp: new Date().toISOString(),
        data: this.truncateData(message)
      };

      console.log(`📡 WebSocket [${direction}] ${messageType} (${currentCount}번째):`, logData);

      this.lastLogTimes.set(messageType, currentTime);
    }
  }

  private shouldLogMessage(messageType: string, currentTime: number, currentCount: number): boolean {
    // 첫 번째 메시지는 항상 로깅
    if (currentCount === 1) {
      return true;
    }

    // 시간 기반 샘플링 (1분마다)
    const lastLogTime = this.lastLogTimes.get(messageType) || 0;
    if (currentTime - lastLogTime >= this.LOG_INTERVAL_MS) {
      return true;
    }

    // 카운트 기반 샘플링 (100개마다)
    if (currentCount % this.LOG_COUNT_THRESHOLD === 0) {
      return true;
    }

    return false;
  }

  private truncateData(data: any, maxLength: number = 500): any {
    const jsonStr = JSON.stringify(data);
    if (jsonStr.length <= maxLength) {
      return data;
    }

    return {
      ...data,
      _truncated: true,
      _original_length: jsonStr.length
    };
  }

}

// 싱글톤 인스턴스
export const wsManager = new WebSocketManager();

/**
 * WebSocket 헬퍼 함수들
 */

// 계좌 업데이트 구독
export function subscribeToAccountUpdates(callback: (data: AccountUpdate['data']) => void): () => void {
  wsManager.on(WS_MESSAGE_TYPES.ACCOUNT_UPDATE, callback);
  return () => wsManager.off(WS_MESSAGE_TYPES.ACCOUNT_UPDATE, callback);
}

// 워치리스트 업데이트 구독
export function subscribeToWatchlistUpdates(callback: (data: WatchlistUpdate['data']) => void): () => void {
  wsManager.on(WS_MESSAGE_TYPES.WATCHLIST_UPDATE, callback);
  return () => wsManager.off(WS_MESSAGE_TYPES.WATCHLIST_UPDATE, callback);
}

// 가격 업데이트 구독
export function subscribeToPriceUpdates(callback: (data: PriceUpdate['data']) => void): () => void {
  wsManager.on(WS_MESSAGE_TYPES.PRICE_UPDATE, callback);
  return () => wsManager.off(WS_MESSAGE_TYPES.PRICE_UPDATE, callback);
}

// 매매 상태 업데이트 구독
export function subscribeToTradingStatus(callback: (data: TradingStatusUpdate['data']) => void): () => void {
  wsManager.on(WS_MESSAGE_TYPES.TRADING_STATUS, callback);
  return () => wsManager.off(WS_MESSAGE_TYPES.TRADING_STATUS, callback);
}

// 주문 업데이트 구독
export function subscribeToOrderUpdates(callback: (data: OrderUpdate['data']) => void): () => void {
  wsManager.on(WS_MESSAGE_TYPES.ORDER_UPDATE, callback);
  return () => wsManager.off(WS_MESSAGE_TYPES.ORDER_UPDATE, callback);
}

// 연결 상태 구독
export function subscribeToConnectionStatus(callback: (state: ConnectionState) => void): () => void {
  wsManager.onConnectionStateChange(callback);
  return () => wsManager.offConnectionStateChange(callback);
}

// 시장 지수 업데이트 구독
export function subscribeToMarketIndexUpdates(callback: (data: any) => void): void {
  wsManager.on(WS_MESSAGE_TYPES.MARKET_INDEX_UPDATE, callback);
}

// 분봉 실시간 업데이트 구독
export function subscribeToMinuteCandles(callback: (message: MinuteCandleUpdateMessage) => void): () => void {
  console.log('📝 [WS] minute_candle_update 리스너 등록');
  const listener = (message: MinuteCandleUpdateMessage) => {
    console.log('📨 [WS] minute_candle_update 리스너 실행:', message);
    callback(message);
  };
  wsManager.on(WS_MESSAGE_TYPES.MINUTE_CANDLE_UPDATE, listener);
  return () => {
    console.log('🔚 [WS] minute_candle_update 리스너 해제');
    wsManager.off(WS_MESSAGE_TYPES.MINUTE_CANDLE_UPDATE, listener);
  };
}

export function subscribeToMinuteCandleFinalized(callback: (message: MinuteCandleFinalizedMessage) => void): () => void {  // ✅ Finalize → Finalized
  console.log('📝 [WS] minute_candle_finalized 리스너 등록');  // ✅ finalize → finalized
  const listener = (message: MinuteCandleFinalizedMessage) => {  // ✅ Finalize → Finalized
    console.log('📨 [WS] minute_candle_finalized 리스너 실행:', message);  // ✅ finalize → finalized
    callback(message);
  };
  wsManager.on(WS_MESSAGE_TYPES.MINUTE_CANDLE_FINALIZED, listener);  // ✅ FINALIZE → FINALIZED
  return () => {
    console.log('🔚 [WS] minute_candle_finalized 리스너 해제');  // ✅ finalize → finalized
    wsManager.off(WS_MESSAGE_TYPES.MINUTE_CANDLE_FINALIZED, listener);  // ✅ FINALIZE → FINALIZED
  };
}

/**
 * 호가 데이터 업데이트 구독
 */
export function subscribeToOrderBookUpdates(
  stockCode: string,
  callback: (data: OrderBookUpdate) => void
): () => void {
  const listener = (data: any) => {
    // data는 이미 notifyListeners에서 전달된 데이터
    // 백엔드에서 보내는 메시지 구조: { stock_code, data: { asks, bids, current_price, timestamp } }
    if (data && data.stock_code === stockCode) {
      console.log(`📊 호가 데이터 수신: ${stockCode}`, data);
      callback(data as OrderBookUpdate);
    }
  };

  wsManager.subscribe('orderbook_update', listener);

  return () => {
    wsManager.unsubscribe('orderbook_update', listener);
  };
}

export function subscribeToMarketStatusUpdates(
  callback: (data: MarketStatusUpdate['data']) => void
): () => void {
  const listener = (message: RealtimeMessage) => {
    if (message.type === 'market_status_update') {
      callback(message.data as MarketStatusUpdate['data']);
    }
  };

  wsManager.subscribe('market_status_update', listener);

  return () => {
    wsManager.unsubscribe('market_status_update', listener);
  };
}

export function unsubscribeFromMarketIndexUpdates(callback: (data: any) => void): void {
  wsManager.off(WS_MESSAGE_TYPES.MARKET_INDEX_UPDATE, callback);
}
