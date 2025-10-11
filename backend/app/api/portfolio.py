"""Portfolio API 엔드포인트 v2.0"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Literal
from loguru import logger

from app.models.schemas import PortfolioHistoryPoint
from app.core.dependencies import get_korea_invest_service
from app.core.korea_invest import KoreaInvestAPIService
from app.services.benchmark_service import BenchmarkService
from app.services.portfolio_analytics_service import PortfolioAnalyticsService


router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


def get_analytics_service(
    korea_invest: KoreaInvestAPIService = Depends(get_korea_invest_service)
) -> PortfolioAnalyticsService:
    """서비스 의존성"""
    benchmark = BenchmarkService(korea_invest)
    return PortfolioAnalyticsService(korea_invest, benchmark)


@router.get("/history", response_model=List[PortfolioHistoryPoint])
async def get_portfolio_history(
    period: Literal["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"] = Query("1W"),
    analytics: PortfolioAnalyticsService = Depends(get_analytics_service)
):
    """
    포트폴리오 성과 시계열 조회

    ✅ v2.0:
    - List[PortfolioHistoryPoint] 직접 반환 (래핑 없음)
    - Frontend 타입과 100% 일치

    Returns:
        [{date: "...", portfolio: 10000, benchmark: 10000}, ...]
    """
    try:
        data = await analytics.get_portfolio_history(period)

        if not data:
            raise HTTPException(status_code=204, detail="데이터 없음")

        return data  # ✅ 배열 직접 반환

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Portfolio history 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health Check"""
    return {"status": "ok", "version": "2.0.0"}
