import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  ConnectionState, 
  UseWebSocketReturn,
  RealtimeMessage
} from '@/lib/types';
import { wsManager, subscribeToConnectionStatus } from '@/lib/websocket';

/**
 * WebSocket 연결을 관리하는 훅
 */
export function useWebSocket(): UseWebSocketReturn {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionState>({
    status: 'disconnected',
    reconnectAttempts: 0,
  });
  const [lastMessage, setLastMessage] = useState<RealtimeMessage | null>(null);
  const isInitialized = useRef(false);

  // 연결 상태 변경 구독
  useEffect(() => {
    const unsubscribe = subscribeToConnectionStatus(setConnectionStatus);
    return unsubscribe;
  }, []);

  // WebSocket 초기 연결
  useEffect(() => {
    if (!isInitialized.current) {
      isInitialized.current = true;
      console.log('🚀 WebSocket 연결 시도 시작');
      wsManager.connect().catch(error => {
        console.error('❌ WebSocket 초기 연결 실패:', error);
      });
    }

    // ⚠️ 중요: 언마운트 시 연결 해제하지 않음
    // WebSocket은 싱글톤으로 앱 전체에서 공유되므로
    // 컴포넌트 언마운트 시 연결을 끊으면 안 됨
    // (React Strict Mode의 double render 문제 방지)
    return () => {
      // wsManager.disconnect(); // 제거됨
    };
  }, []);

  // 메시지 전송 함수
  const sendMessage = useCallback((message: any) => {
    wsManager.send(message);
  }, []);

  const isConnected = connectionStatus.status === 'connected';

  return {
    isConnected,
    connectionStatus,
    sendMessage,
    lastMessage,
  };
}