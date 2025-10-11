"""Portfolio API 엔드포인트 v2.0"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Literal
from loguru import logger

from app.models.schemas import PortfolioHistoryPoint
from app.core.dependencies import get_korea_invest_service
from app.core.korea_invest import KoreaInvestAPIService
from app.services.benchmark_service import BenchmarkService
from app.services.portfolio_analytics_service import PortfolioAnalyticsService


from app.services.snapshot_manager import SnapshotManager


router = APIRouter(tags=["portfolio"])


snapshot_manager = SnapshotManager()

def get_analytics_service(
    korea_invest: KoreaInvestAPIService = Depends(get_korea_invest_service)
) -> PortfolioAnalyticsService:
    """서비스 의존성"""
    benchmark = BenchmarkService(korea_invest)
    return PortfolioAnalyticsService(
        korea_invest,
        benchmark,
        snapshot_manager=snapshot_manager
    )


from app.core.cache import CacheService

@router.get("/history", response_model=List[PortfolioHistoryPoint])
async def get_portfolio_history(
    period: Literal["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"] = Query("1W"),
    analytics: PortfolioAnalyticsService = Depends(get_analytics_service)
):
    """
    포트폴리오 성과 시계열 조회 (캐싱 적용)
    """
    logger.info(f"📊 Portfolio History 요청: period={period}")
    cache = CacheService()
    cache_key = f"portfolio_history:{period}"

    # 1. 캐시 확인
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.info(f"✅ 캐시 사용: {cache_key}")
        return [PortfolioHistoryPoint(**item) for item in cached_data]

    # 2. 캐시 없으면 계산
    logger.info(f"🔄 캐시 없음, 새로 계산: {cache_key}")
    try:
        data = await analytics.get_portfolio_history(period)

        if not data:
            raise HTTPException(status_code=204, detail="데이터 없음")

        # 3. 결과 캐시 저장 (5분 TTL)
        cache.set(cache_key, [p.dict() for p in data], ttl=300)

        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio history 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health Check"""
    return {"status": "ok", "version": "2.0.0"}
