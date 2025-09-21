"""
WebSocket 연결 관리
실시간 데이터 전송을 위한 WebSocket 연결을 관리
"""

from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import json
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._connection_info: Dict[WebSocket, Dict[str, Any]] = {}
        
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