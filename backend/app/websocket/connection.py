"""
WebSocket 연결 관리
실시간 데이터 전송을 위한 WebSocket 연결을 관리
"""

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
from typing import List, Dict, Any, Set, Optional
from loguru import logger
from datetime import datetime
from app.utils.websocket_logger import websocket_logger



class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
        # 선택적 브로드캐스트를 위한 구독 관리
        self.stock_subscribers: Dict[str, Set[WebSocket]] = {}  # 종목별 구독자
        self.index_subscribers: Dict[str, Set[WebSocket]] = {}  # 지수별 구독자
        self.market_subscribers: Dict[str, Set[WebSocket]] = {}  # 시장별 구독자
        
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """새로운 WebSocket 연결을 수락하고 관리"""
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            
            # 연결 정보 저장
            self._connection_info[websocket] = {
                "client_id": client_id,
                "connected_at": datetime.now(),
                "last_message": None
            }
            
            logger.info(f"새로운 WebSocket 연결: {client_id or 'Anonymous'}")
            logger.info(f"총 활성 연결 수: {len(self.active_connections)}")
            
            # 연결 성공 메시지 전송
            await self.send_personal_message(websocket, {
                "type": "connection_status",
                "data": {
                    "status": "connected",
                    "client_id": client_id,
                    "server_time": datetime.now().isoformat()
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"WebSocket 연결 실패: {str(e)}")
            raise
    
    async def disconnect(self, websocket: WebSocket):
        """WebSocket 연결을 안전하게 해제"""
        try:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                
                # 연결 정보 정리
                client_info = self._connection_info.pop(websocket, {})
                client_id = client_info.get("client_id", "Unknown")
                
                # 모든 구독에서 제거
                self._unsubscribe_from_all(websocket)
                
                logger.info(f"WebSocket 연결 해제: {client_id}")
                logger.info(f"남은 활성 연결 수: {len(self.active_connections)}")
                
        except Exception as e:
            logger.error(f"WebSocket 연결 해제 중 오류: {str(e)}")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """특정 연결에 개인 메시지 전송"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            
            # 마지막 메시지 시간 업데이트
            if websocket in self._connection_info:
                self._connection_info[websocket]["last_message"] = datetime.now()
                
        except WebSocketDisconnect:
            await self.disconnect(websocket)
        except Exception as e:
            logger.error(f"개인 메시지 전송 실패: {str(e)}")
            await self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """모든 연결된 클라이언트에 메시지 브로드캐스트"""
        if not self.active_connections:
            return
        
        # WebSocket 로깅
        message_type = message.get('type', 'unknown')
        websocket_logger.log_message(message_type, message, 'backend')
        
        disconnected_connections = []
        message_json = json.dumps(message, ensure_ascii=False)
        
        # 모든 연결에 동시에 메시지 전송
        send_tasks = []
        for connection in self.active_connections:
            send_tasks.append(self._safe_send(connection, message_json))
        
        # 모든 전송 작업을 병렬로 실행
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        # 실패한 연결들 정리
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                disconnected_connections.append(self.active_connections[i])
        
        # 실패한 연결들 제거
        for connection in disconnected_connections:
            await self.disconnect(connection)
        
        if disconnected_connections:
            logger.warning(f"{len(disconnected_connections)}개 연결이 끊어져 제거되었습니다.")
    
    async def _safe_send(self, websocket: WebSocket, message: str):
        """안전한 메시지 전송 (예외 처리 포함)"""
        try:
            await websocket.send_text(message)
            
            # 마지막 메시지 시간 업데이트
            if websocket in self._connection_info:
                self._connection_info[websocket]["last_message"] = datetime.now()
                
        except WebSocketDisconnect:
            raise  # 연결 끊김은 상위에서 처리
        except Exception as e:
            logger.error(f"메시지 전송 실패: {str(e)}")
            raise
    
    async def broadcast_to_clients(self, client_ids: List[str], message: Dict[str, Any]):
        """특정 클라이언트들에게만 메시지 전송"""
        if not client_ids:
            return
        
        target_connections = []
        for websocket, info in self._connection_info.items():
            if info.get("client_id") in client_ids:
                target_connections.append(websocket)
        
        if not target_connections:
            return
        
        message_json = json.dumps(message, ensure_ascii=False)
        send_tasks = [self._safe_send(conn, message_json) for conn in target_connections]
        
        results = await asyncio.gather(*send_tasks, return_exceptions=True)
        
        # 실패한 연결들 정리
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                await self.disconnect(target_connections[i])
    
    def get_connection_count(self) -> int:
        """현재 활성 연결 수 반환"""
        return len(self.active_connections)
    
    def get_connection_info(self) -> List[Dict[str, Any]]:
        """모든 연결의 정보 반환"""
        info_list = []
        for websocket, info in self._connection_info.items():
            connection_info = {
                "client_id": info.get("client_id"),
                "connected_at": info.get("connected_at").isoformat() if info.get("connected_at") else None,
                "last_message": info.get("last_message").isoformat() if info.get("last_message") else None,
                "is_active": websocket in self.active_connections
            }
            info_list.append(connection_info)
        return info_list
    
    async def ping_all_connections(self):
        """모든 연결에 ping 메시지 전송 (연결 상태 확인)"""
        ping_message = {
            "type": "ping",
            "data": {"server_time": datetime.now().isoformat()},
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(ping_message)
    
    async def send_heartbeat(self):
        """주기적인 하트비트 메시지 전송"""
        heartbeat_message = {
            "type": "heartbeat",
            "data": {
                "server_time": datetime.now().isoformat(),
                "active_connections": len(self.active_connections)
            },
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(heartbeat_message)
    
    # 선택적 브로드캐스트 메서드들
    
    async def subscribe_stock(self, websocket: WebSocket, stock_code: str):
        """종목 구독"""
        if websocket not in self.active_connections:
            logger.warning(f"비활성 연결에서 종목 구독 시도: {stock_code}")
            return
        
        if stock_code not in self.stock_subscribers:
            self.stock_subscribers[stock_code] = set()
        
        self.stock_subscribers[stock_code].add(websocket)
        logger.debug(f"종목 구독: {stock_code} (구독자 수: {len(self.stock_subscribers[stock_code])})")
    
    async def unsubscribe_stock(self, websocket: WebSocket, stock_code: str):
        """종목 구독 해제"""
        if stock_code in self.stock_subscribers:
            self.stock_subscribers[stock_code].discard(websocket)
            if not self.stock_subscribers[stock_code]:
                del self.stock_subscribers[stock_code]
            logger.debug(f"종목 구독 해제: {stock_code}")
    
    async def subscribe_index(self, websocket: WebSocket, index_code: str):
        """지수 구독"""
        if websocket not in self.active_connections:
            logger.warning(f"비활성 연결에서 지수 구독 시도: {index_code}")
            return
        
        if index_code not in self.index_subscribers:
            self.index_subscribers[index_code] = set()
        
        self.index_subscribers[index_code].add(websocket)
        logger.debug(f"지수 구독: {index_code} (구독자 수: {len(self.index_subscribers[index_code])})")
    
    async def unsubscribe_index(self, websocket: WebSocket, index_code: str):
        """지수 구독 해제"""
        if index_code in self.index_subscribers:
            self.index_subscribers[index_code].discard(websocket)
            if not self.index_subscribers[index_code]:
                del self.index_subscribers[index_code]
            logger.debug(f"지수 구독 해제: {index_code}")
    
    async def subscribe_market(self, websocket: WebSocket, market_code: str):
        """시장 구독"""
        if websocket not in self.active_connections:
            logger.warning(f"비활성 연결에서 시장 구독 시도: {market_code}")
            return
        
        if market_code not in self.market_subscribers:
            self.market_subscribers[market_code] = set()
        
        self.market_subscribers[market_code].add(websocket)
        logger.debug(f"시장 구독: {market_code} (구독자 수: {len(self.market_subscribers[market_code])})")
    
    async def unsubscribe_market(self, websocket: WebSocket, market_code: str):
        """시장 구독 해제"""
        if market_code in self.market_subscribers:
            self.market_subscribers[market_code].discard(websocket)
            if not self.market_subscribers[market_code]:
                del self.market_subscribers[market_code]
            logger.debug(f"시장 구독 해제: {market_code}")
    
    async def broadcast_to_stock_subscribers(self, stock_code: str, message: Dict[str, Any]):
        """특정 종목 구독자에게만 전송"""
        subscribers = self.stock_subscribers.get(stock_code, set())
        
        if not subscribers:
            return
        
        # WebSocket 로깅 (종목별)
        message_type = message.get('type', 'unknown')
        log_data = {**message, 'stock_code': stock_code, 'subscriber_count': len(subscribers)}
        websocket_logger.log_message(f"{message_type}_stock", log_data, 'backend')
        
        # 활성 연결만 필터링
        active_subscribers = [ws for ws in subscribers if ws in self.active_connections]
        
        if not active_subscribers:
            # 비활성 구독자 정리
            self.stock_subscribers[stock_code] = set()
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        
        # 병렬 전송
        tasks = [self._safe_send(ws, message_str) for ws in active_subscribers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_index_subscribers(self, index_code: str, message: Dict[str, Any]):
        """특정 지수 구독자에게만 전송"""
        subscribers = self.index_subscribers.get(index_code, set())
        
        if not subscribers:
            return
        
        # 활성 연결만 필터링
        active_subscribers = [ws for ws in subscribers if ws in self.active_connections]
        
        if not active_subscribers:
            # 비활성 구독자 정리
            self.index_subscribers[index_code] = set()
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        
        # 병렬 전송
        tasks = [self._safe_send(ws, message_str) for ws in active_subscribers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_market_subscribers(self, market_code: str, message: Dict[str, Any]):
        """특정 시장 구독자에게만 전송"""
        subscribers = self.market_subscribers.get(market_code, set())
        
        if not subscribers:
            return
        
        # 활성 연결만 필터링
        active_subscribers = [ws for ws in subscribers if ws in self.active_connections]
        
        if not active_subscribers:
            # 비활성 구독자 정리
            self.market_subscribers[market_code] = set()
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        
        # 병렬 전송
        tasks = [self._safe_send(ws, message_str) for ws in active_subscribers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def _unsubscribe_from_all(self, websocket: WebSocket):
        """모든 구독에서 제거"""
        # 종목 구독에서 제거
        for stock_code in list(self.stock_subscribers.keys()):
            self.stock_subscribers[stock_code].discard(websocket)
            if not self.stock_subscribers[stock_code]:
                del self.stock_subscribers[stock_code]
        
        # 지수 구독에서 제거
        for index_code in list(self.index_subscribers.keys()):
            self.index_subscribers[index_code].discard(websocket)
            if not self.index_subscribers[index_code]:
                del self.index_subscribers[index_code]
        
        # 시장 구독에서 제거
        for market_code in list(self.market_subscribers.keys()):
            self.market_subscribers[market_code].discard(websocket)
            if not self.market_subscribers[market_code]:
                del self.market_subscribers[market_code]
    
    def get_subscription_stats(self) -> Dict[str, Any]:
        """구독 통계 반환"""
        return {
            "stock_subscriptions": {code: len(subscribers) for code, subscribers in self.stock_subscribers.items()},
            "index_subscriptions": {code: len(subscribers) for code, subscribers in self.index_subscribers.items()},
            "market_subscriptions": {code: len(subscribers) for code, subscribers in self.market_subscribers.items()},
            "total_stock_subscribers": sum(len(subscribers) for subscribers in self.stock_subscribers.values()),
            "total_index_subscribers": sum(len(subscribers) for subscribers in self.index_subscribers.values()),
            "total_market_subscribers": sum(len(subscribers) for subscribers in self.market_subscribers.values()),
        }