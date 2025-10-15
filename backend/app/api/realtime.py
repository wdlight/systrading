"""
실시간 데이터 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, Any
from datetime import datetime
from loguru import logger
from app.dependencies import get_realtime_service
from app.services.realtime_service import RealtimeDataService

router = APIRouter(prefix="/realtime", tags=["realtime"])

@router.post("/subscribe/orderbook")
async def subscribe_orderbook(stock_code: str, request: Request):
    """
    특정 종목의 호가 데이터 구독
    
    Args:
        stock_code: 종목 코드 (예: "005930")
    
    Returns:
        구독 성공 메시지
    """
    import queue
    try:
        ws_req_queue = getattr(request.app.state, "ws_req_queue", None)
        
        logger.info(f"호가 구독 요청: {stock_code}")
        
        # Check if queue exists
        if ws_req_queue is None:
            logger.error("ws_req_queue가 초기화되지 않음")
            raise HTTPException(status_code=503, detail="WebSocket 서비스 초기화 중")
        
        logger.info(f"호가 구독 요청: {stock_code}, Queue 크기: {ws_req_queue.qsize()}")
        
        # Use timeout to prevent blocking
        ws_req_queue.put({
            "action_id": "실시간호가등록",
            "종목코드": stock_code
        }, timeout=1.0)
        
        logger.info(f"호가 구독 Queue 추가 성공: {stock_code}")
        
        return {
            "success": True,
            "message": f"종목 {stock_code} 호가 구독 시작",
            "stock_code": stock_code
        }
    except queue.Full:
        logger.error(f"호가 구독 Queue 가득 참: {stock_code}")
        raise HTTPException(status_code=503, detail="요청 대기열이 가득 찼습니다. 잠시 후 다시 시도하세요.")
    except Exception as e:
        logger.error(f"호가 구독 실패: {stock_code}, 에러: {str(e)}, 타입: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"호가 구독 실패: {str(e)}")

@router.post("/unsubscribe/orderbook")
async def unsubscribe_orderbook(
    stock_code: str,
    request: Request,
    realtime_service: RealtimeDataService = Depends(get_realtime_service)
):
    """
    특정 종목의 호가 데이터 구독 해제 (개선: 캐시 무효화 추가)
    """
    import queue
    try:
        ws_req_queue = getattr(request.app.state, "ws_req_queue", None)
        
        logger.info(f"호가 구독 해제 요청: {stock_code}")
        
        # Check if queue exists
        if ws_req_queue is None:
            logger.error("ws_req_queue가 초기화되지 않음")
            raise HTTPException(status_code=503, detail="WebSocket 서비스 초기화 중")
        
        # Use timeout to prevent blocking
        ws_req_queue.put({
            "action_id": "실시간호가해제",
            "tr_id": "H0STASP0", # KIS API TR_ID
            "tr_key": stock_code
        }, timeout=1.0)
        
        # 캐시 즉시 무효화 (stale 데이터 방지)
        realtime_service.invalidate_orderbook_cache(stock_code)
        logger.info(f"종목 {stock_code} 호가 구독 해제 및 캐시 무효화 완료")
        
        return {
            "success": True,
            "message": f"종목 {stock_code} 호가 구독 해제",
            "stock_code": stock_code
        }
    except queue.Full:
        logger.error(f"호가 구독 해제 Queue 가득 참: {stock_code}")
        raise HTTPException(status_code=503, detail="요청 대기열이 가득 찼습니다. 잠시 후 다시 시도하세요.")
    except Exception as e:
        logger.error(f"호가 구독 해제 실패: {stock_code}, 에러: {str(e)}, 타입: {type(e).__name__}")
        raise HTTPException(status_code=500, detail=f"호가 구독 해제 실패: {str(e)}")

@router.get("/orderbook/{stock_code}")
async def get_current_orderbook(
    stock_code: str,
    realtime_service: RealtimeDataService = Depends(get_realtime_service)
):
    """
    특정 종목의 현재 호가 데이터 조회 (REST API)
    
    1. 캐시된 데이터 우선 반환
    2. 캐시 없으면 장 시간 체크
    3. 장 시간 내: 더미 데이터 (KIS REST API 호출 가능)
    4. 장 시간 외: 빈 데이터 + market_status: "closed"
    """
    from app.utils.trading_hours import TradingHoursManager
    from datetime import datetime
    from loguru import logger
    
    try:
        # 1. 캐시 조회 (의존성 주입으로 받은 인스턴스 사용)
        cached_data = realtime_service.get_cached_orderbook(stock_code)
        
        if cached_data:
            logger.info(f"캐시된 호가 데이터 반환: {stock_code}")
            return cached_data
        
        # 2. 장 시간 체크
        now = datetime.now()
        is_open = TradingHoursManager.is_trading_hours(now)
        
        if is_open:
            # 3. 장 시간 내: 호가 데이터 없음 (WebSocket 구독 필요)
            logger.info(f"캐시 없음. 호가 데이터 없음 - WebSocket 구독 필요: {stock_code}")
            
            # KIS API는 호가 데이터를 REST API로 제공하지 않음
            # 실시간 호가 데이터는 WebSocket(H0STASP0)을 통해서만 제공됨
            # 따라서 캐시가 없으면 빈 데이터 반환하고 클라이언트에게 구독 요청 안내
            
            return {
                "stock_code": stock_code,
                "current_price": 0,
                "asks": [{"price": 0, "quantity": 0} for _ in range(10)],
                "bids": [{"price": 0, "quantity": 0} for _ in range(10)],
                "timestamp": now.isoformat(),
                "market_status": "open",
                "message": "호가 데이터를 받으려면 WebSocket 구독이 필요합니다. /api/realtime/subscribe/orderbook 엔드포인트를 호출하세요.",
                "subscription_required": True
            }
        else:
            # 4. 장 시간 외: 빈 데이터
            logger.info(f"장 시간 외. 빈 호가 데이터 반환: {stock_code}")
            return {
                "stock_code": stock_code,
                "current_price": 0,
                "asks": [{"price": 0, "quantity": 0} for _ in range(10)],
                "bids": [{"price": 0, "quantity": 0} for _ in range(10)],
                "timestamp": now.isoformat(),
                "market_status": "closed"
            }
    
    except Exception as e:
        logger.error(f"호가 데이터 조회 실패: {stock_code}, {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/queue-status")
async def get_queue_status(request: Request):
    """디버그: Queue 상태 조회"""
    ws_req_queue = getattr(request.app.state, "ws_req_queue", None)
    ws_result_queue = getattr(request.app.state, "ws_result_queue", None)
    return {
        "ws_req_queue_size": ws_req_queue.qsize() if ws_req_queue else None,
        "ws_result_queue_size": ws_result_queue.qsize() if ws_result_queue else None,
        "ws_req_queue_initialized": ws_req_queue is not None,
        "ws_result_queue_initialized": ws_result_queue is not None
    }

@router.get("/debug/cache-status")
async def get_cache_status(
    realtime_service: RealtimeDataService = Depends(get_realtime_service)
):
    """디버그: 호가 캐시 상태 조회"""
    cache_keys = list(realtime_service.orderbook_cache.keys())
    cache_details = {}
    for stock_code in cache_keys:
        cached_data = realtime_service.get_cached_orderbook(stock_code)
        if cached_data:
            cache_details[stock_code] = {
                "current_price": cached_data.get("current_price"),
                "timestamp": cached_data.get("timestamp"),
                "asks_count": len(cached_data.get("asks", [])),
                "bids_count": len(cached_data.get("bids", []))
            }
    
    return {
        "cached_stocks": cache_keys,
        "cache_size": len(cache_keys),
        "cache_details": cache_details
    }
