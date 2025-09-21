import { 
  RealtimeMessage, 
  ConnectionState,
  AccountUpdate,
  WatchlistUpdate,
  PriceUpdate,
  TradingStatusUpdate,
  OrderUpdate,
  ConnectionStatus
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
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: RealtimeMessage = JSON.parse(event.data);
            console.log('📥 WebSocket 메시지 수신:', message.type, message);
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
            target: error.target?.url || 'unknown',
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

  /**
   * 메시지 처리
   */
  private handleMessage(message: RealtimeMessage): void {
    const { type, data } = message;
    
    // 타입별 특수 처리
    switch (type) {
      case WS_MESSAGE_TYPES.CONNECTION_STATUS:
        this.handleConnectionStatus(data);
        break;
      case WS_MESSAGE_TYPES.ACCOUNT_UPDATE:
        this.notifyListeners(type, data);
        break;
      case WS_MESSAGE_TYPES.WATCHLIST_UPDATE:
        this.notifyListeners(type, data);
        break;
      case WS_MESSAGE_TYPES.PRICE_UPDATE:
        this.notifyListeners(type, data);
        break;
      case WS_MESSAGE_TYPES.TRADING_STATUS:
        this.notifyListeners(type, data);
        break;
      case WS_MESSAGE_TYPES.ORDER_UPDATE:
        this.notifyListeners(type, data);
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
    console.log(`🔔 notifyListeners 호출: ${messageType}, 리스너 수: ${listeners?.size || 0}`, data);
    if (listeners) {
      listeners.forEach(callback => {
        try {
          console.log(`📤 리스너 실행: ${messageType}`);
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
    
    console.log(`${Math.round(delay/1000)}초 후 재연결 시도 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
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