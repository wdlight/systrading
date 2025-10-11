"""
FastAPI 메인 애플리케이션
RSI/MACD 트레이딩 시스템의 백엔드 API 서버
"""

import sys
import os

# 현재 파일의 부모 디렉토리(backend)를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from contextlib import asynccontextmanager
from multiprocessing import Process, Queue

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.websocket.connection import ConnectionManager
from app.services.realtime_service import RealtimeDataService
from app.core.config import get_settings
from app.core.korea_invest import KoreaInvestAPIService
from app.domestic_websocket import run_websocket

from app.core.logging_config import setup_logging
from loguru import logger

# --- 로거 설정 ---
# 애플리케이션 시작 시 로깅 설정 적용
setup_logging()
# --- 로거 설정 끝 ---

from app.api.account import router as account_router
from app.api.trading import router as trading_router
from app.api.watchlist import router as watchlist_router
from app.api.stocks import router as stocks_router
from app.api.chart import router as chart_router
from app.api.portfolio import router as portfolio_router

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.scheduler.portfolio_snapshot import save_portfolio_snapshot

# 전역 변수
connection_manager = ConnectionManager()
realtime_service = None
korea_invest_service = None
websocket_process = None
ws_result_queue = None
ws_req_queue = None
scheduler = AsyncIOScheduler()



# 추가적인 CORS 헤더 설정을 위한 미들웨어
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 컨텍스트 매니저"""
    global realtime_service, korea_invest_service, websocket_process, ws_result_queue, ws_req_queue
    
    logger.info("FastAPI 애플리케이션 초기화를 시작합니다.")
    settings = get_settings()
    
    korea_invest_service = KoreaInvestAPIService(settings)
    
    ws_result_queue = Queue()
    ws_req_queue = Queue()
    
    realtime_service = RealtimeDataService(korea_invest_service, connection_manager, ws_result_queue)
    
    if korea_invest_service.api_instance:
        ws_url = settings.KI_WEBSOCKET_URL
        websocket_process = Process(
            target=run_websocket,
            args=(korea_invest_service.api_instance, ws_url, ws_req_queue, ws_result_queue),
            daemon=True
        )
        websocket_process.start()
        logger.info(f"domestic_websocket 프로세스를 시작했습니다 (PID: {websocket_process.pid}).")
    else:
        logger.error("KoreaInvestAPI 인스턴스가 없어 domestic_websocket 프로세스를 시작할 수 없습니다.")

    asyncio.create_task(realtime_service.start())

    # 스케줄러 시작 (5분마다 스냅샷 저장)
    scheduler.add_job(save_portfolio_snapshot, 'interval', minutes=5, id='portfolio_snapshot_job')
    scheduler.start()
    logger.info("✅ 스케줄러 시작: 5분마다 포트폴리오 스냅샷을 저장합니다.")
    
    logger.info("FastAPI 애플리케이션이 성공적으로 시작되었습니다.")
    
    yield
    
    logger.info("FastAPI 애플리케이션 종료를 시작합니다.")
    if scheduler.running:
        scheduler.shutdown()
        logger.info("스케줄러가 중지되었습니다.")

    if realtime_service:
        await realtime_service.stop()
        logger.info("RealtimeDataService가 중지되었습니다.")
        
    if websocket_process and websocket_process.is_alive():
        ws_req_queue.put({"action_id": "종료"})
        websocket_process.join(timeout=5)
        if websocket_process.is_alive():
            websocket_process.terminate()
            logger.warning("domestic_websocket 프로세스가 정상적으로 종료되지 않아 강제 종료했습니다.")
        else:
            logger.info("domestic_websocket 프로세스가 정상적으로 종료되었습니다.")
    
    logger.info("FastAPI 애플리케이션이 종료되었습니다.")

# FastAPI 앱 생성
app = FastAPI(
    title="Stock Trading API",
    description="RSI/MACD 기반 주식 자동매매 시스템 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(CustomCORSMiddleware)

# API 라우터 등록
app.include_router(account_router, prefix="/api", tags=["account"])
app.include_router(trading_router, prefix="/api", tags=["trading"])
app.include_router(watchlist_router, prefix="/api", tags=["watchlist"])
app.include_router(stocks_router, prefix="/api/stocks", tags=["stocks"])
app.include_router(chart_router, prefix="/api/chart", tags=["chart"])
app.include_router(portfolio_router, prefix="/api/portfolio", tags=["portfolio"])

logger.debug(f"chart_router routes: {chart_router.routes}")

@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "message": "Stock Trading API Server",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """상세 헬스체크"""
    global korea_invest_service, realtime_service, websocket_process
    
    return {
        "status": "healthy",
        "korea_invest_connected": korea_invest_service.is_connected if korea_invest_service else False,
        "realtime_service_running": realtime_service.is_running if realtime_service else False,
        "websocket_process_alive": websocket_process.is_alive() if websocket_process else False,
        "active_web_clients": connection_manager.get_connection_count()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결 엔드포인트"""
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket 메시지 수신: {data}")
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        logger.info("WebSocket 클라이언트 연결이 해제되었습니다.")

if __name__ == "__main__":
    import multiprocessing
    if sys.platform.startswith('win'):
        multiprocessing.freeze_support()
    
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
        log_config=None
    )
