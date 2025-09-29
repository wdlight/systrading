from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.core.dependencies import get_trading_service
from app.services.trading_service import TradingService
from app.models.schemas import ChartCandle
from loguru import logger

router = APIRouter()

@router.get(
    "/{stock_code}/minute",
    response_model=List[ChartCandle],
    summary="분봉 차트 데이터 조회",
    description="특정 종목의 분봉 차트 데이터를 조회합니다."
)
async def get_minute_chart_data(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service)
) -> List[ChartCandle]:
    """분봉 차트 데이터 조회"""
    try:
        chart_data = await trading_service.get_minute_chart_data(stock_code)
        if chart_data is None:
            raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다.")
        return chart_data
    except Exception as e:
        logger.error(f"분봉 차트 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분봉 차트 데이터 조회 중 오류가 발생했습니다: {str(e)}")