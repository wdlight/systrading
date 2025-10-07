from fastapi import APIRouter, Depends
from typing import List, Dict, Any

from app.core.dependencies import get_stock_info_service
from app.services.stock_info_service import StockInfoService
from app.models.schemas import MarketOverview

router = APIRouter(tags=["Stocks"])

@router.get("/list", response_model=List[Dict[str, str]])
async def get_all_stocks(
    stock_info_service: StockInfoService = Depends(get_stock_info_service)
) -> List[Dict[str, str]]:
    """
    모든 KOSPI 및 KOSDAQ 종목의 코드와 이름을 반환합니다.
    캐싱 전략이 적용되어 빠른 응답을 제공합니다.
    """
    return await stock_info_service.get_all_stocks()

@router.get("/overview", response_model=MarketOverview, summary="시장 현황 조회")
async def get_market_overview(
    stock_info_service: StockInfoService = Depends(get_stock_info_service)
) -> Dict[str, Any]:
    """
    KOSPI, KOSDAQ 지수 및 주요 종목 정보를 포함한 시장 현황을 반환합니다.
    """
    return await stock_info_service.get_market_overview()
