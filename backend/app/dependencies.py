from fastapi import Request
from app.services.realtime_service import RealtimeDataService

def get_realtime_service(request: Request) -> RealtimeDataService:
    """
    FastAPI 의존성 주입을 통한 RealtimeDataService 조회
    
    Usage:
        @router.get("/some-endpoint")
        async def some_endpoint(
            realtime_service: RealtimeDataService = Depends(get_realtime_service)
        ):
            data = realtime_service.get_cached_orderbook("005930")
            ...
    """
    return request.app.state.realtime_service
