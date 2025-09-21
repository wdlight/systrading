"""
WebSocket 실시간 데이터 스트리밍
워치리스트 데이터의 실시간 업데이트를 클라이언트에 전송
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import List, Dict, Set
import asyncio
import json
from utils.logger import logger
from datetime import datetime

from app.models.watchlist_models import WatchlistItem, PriceUpdateEvent
from app.services.watchlist_service import WatchlistService
from app.services.trading_service import TradingService
from app.core.dependencies import get_watchlist_service, get_trading_service


router = APIRouter()

class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}  # 클라이언트별 구독 종목
        
    async def connect(self, websocket: WebSocket):
        """클라이언트 연결"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket 클라이언트 연결: {len(self.active_connections)}개 연결")
    
    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 해제"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket 클라이언트 연결 해제: {len(self.active_connections)}개 연결")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """개별 클라이언트에게 메시지 전송"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"개별 메시지 전송 실패: {str(e)}")
    
    async def broadcast(self, message: str):
        """모든 연결된 클라이언트에게 브로드캐스트"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"브로드캐스트 전송 실패: {str(e)}")
                disconnected.append(connection)
        
        # 연결이 끊어진 클라이언트 정리
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_subscribers(self, stock_code: str, message: str):
        """특정 종목을 구독하는 클라이언트에게만 전송"""
        disconnected = []
        for websocket, subscribed_stocks in self.subscriptions.items():
            if stock_code in subscribed_stocks:
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"구독자 메시지 전송 실패: {str(e)}")
                    disconnected.append(websocket)
        
        # 연결이 끊어진 클라이언트 정리
        for conn in disconnected:
            self.disconnect(conn)
    
    def subscribe_stock(self, websocket: WebSocket, stock_code: str):
        """종목 구독 추가"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(stock_code)
            logger.info(f"종목 구독 추가: {stock_code}")
    
    def unsubscribe_stock(self, websocket: WebSocket, stock_code: str):
        """종목 구독 해제"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(stock_code)
            logger.info(f"종목 구독 해제: {stock_code}")


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """메인 WebSocket 엔드포인트"""
    await manager.connect(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_websocket_message(websocket, message)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "message": "잘못된 JSON 형식입니다."
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"WebSocket 메시지 처리 오류: {str(e)}")
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error", 
                        "message": f"메시지 처리 중 오류가 발생했습니다: {str(e)}"
                    }),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, message: Dict):
    """WebSocket 메시지 처리"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # 종목 구독
        stock_code = message.get("stock_code")
        if stock_code:
            manager.subscribe_stock(websocket, stock_code)
            await manager.send_personal_message(
                json.dumps({
                    "type": "subscribed",
                    "stock_code": stock_code,
                    "message": f"종목 {stock_code} 구독이 시작되었습니다."
                }),
                websocket
            )
    
    elif message_type == "unsubscribe":
        # 종목 구독 해제
        stock_code = message.get("stock_code")
        if stock_code:
            manager.unsubscribe_stock(websocket, stock_code)
            await manager.send_personal_message(
                json.dumps({
                    "type": "unsubscribed",
                    "stock_code": stock_code,
                    "message": f"종목 {stock_code} 구독이 해제되었습니다."
                }),
                websocket
            )
    
    elif message_type == "ping":
        # 연결 상태 확인
        await manager.send_personal_message(
            json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
    
    elif message_type == "get_watchlist":
        # 워치리스트 조회 요청
        try:
            watchlist_service = get_watchlist_service()
            items = await watchlist_service.get_watchlist()
            
            await manager.send_personal_message(
                json.dumps({
                    "type": "watchlist_data",
                    "data": [item.dict() for item in items],
                    "timestamp": datetime.now().isoformat()
                }, default=str),
                websocket
            )
        except Exception as e:
            await manager.send_personal_message(
                json.dumps({
                    "type": "error",
                    "message": f"워치리스트 조회 실패: {str(e)}"
                }),
                websocket
            )
    
    else:
        await manager.send_personal_message(
            json.dumps({
                "type": "error",
                "message": f"알 수 없는 메시지 타입: {message_type}"
            }),
            websocket
        )


async def broadcast_price_update(stock_code: str, price_data: PriceUpdateEvent):
    """가격 업데이트 브로드캐스트"""
    message = json.dumps({
        "type": "price_update",
        "stock_code": stock_code,
        "data": price_data.dict(),
        "timestamp": datetime.now().isoformat()
    }, default=str)
    
    await manager.broadcast_to_subscribers(stock_code, message)


async def broadcast_watchlist_update(event_type: str, stock_code: str, data: Dict):
    """워치리스트 업데이트 브로드캐스트"""
    message = json.dumps({
        "type": "watchlist_update",
        "event_type": event_type,  # added, removed, updated
        "stock_code": stock_code,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }, default=str)
    
    await manager.broadcast(message)


async def broadcast_trading_signal(stock_code: str, signal_type: str, signal_data: Dict):
    """매매 신호 브로드캐스트"""
    message = json.dumps({
        "type": "trading_signal",
        "stock_code": stock_code,
        "signal_type": signal_type,  # buy_signal, sell_signal
        "data": signal_data,
        "timestamp": datetime.now().isoformat()
    }, default=str)
    
    await manager.broadcast_to_subscribers(stock_code, message)


async def broadcast_trading_execution(execution_result: Dict):
    """매매 실행 결과 브로드캐스트"""
    message = json.dumps({
        "type": "trading_execution",
        "data": execution_result,
        "timestamp": datetime.now().isoformat()
    }, default=str)
    
    await manager.broadcast(message)


# 실시간 데이터 업데이트 백그라운드 태스크
async def start_realtime_data_stream():
    """실시간 데이터 스트림 시작"""
    watchlist_service = get_watchlist_service()
    trading_service = get_trading_service()
    
    while True:
        try:
            # 워치리스트 갱신
            await watchlist_service.refresh_all_data()
            
            # 워치리스트 데이터 브로드캐스트
            items = await watchlist_service.get_watchlist()
            if items:
                message = json.dumps({
                    "type": "watchlist_full_update",
                    "data": [item.dict() for item in items],
                    "timestamp": datetime.now().isoformat()
                }, default=str)
                
                await manager.broadcast(message)
            
            # 매매 상태 브로드캐스트
            trading_status = await trading_service.get_trading_status()
            message = json.dumps({
                "type": "trading_status",
                "data": trading_status,
                "timestamp": datetime.now().isoformat()
            }, default=str)
            
            await manager.broadcast(message)
            
        except Exception as e:
            logger.error(f"실시간 데이터 스트림 오류: {str(e)}")
        
        # 2초마다 업데이트 (PyQt5와 동일한 주기)
        await asyncio.sleep(2)


# WebSocket 유틸리티 함수들
def get_connection_count() -> int:
    """현재 연결된 클라이언트 수 반환"""
    return len(manager.active_connections)


def get_subscriptions_info() -> Dict[str, int]:
    """종목별 구독자 수 정보 반환"""
    stock_subscribers = {}
    
    for subscriptions in manager.subscriptions.values():
        for stock_code in subscriptions:
            stock_subscribers[stock_code] = stock_subscribers.get(stock_code, 0) + 1
    
    return stock_subscribers