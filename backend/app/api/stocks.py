from fastapi import APIRouter, Depends
from typing import List, Dict

from app.core.dependencies import get_stock_info_service
from app.services.stock_info_service import StockInfoService

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
