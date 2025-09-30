from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.core.dependencies import get_trading_service
from app.services.trading_service import TradingService
from app.models.schemas import ChartCandle
from app.models.chart import ChartCandleResponse
from app.utils.trading_hours import TradingHoursManager
from loguru import logger

router = APIRouter(tags=["Chart"])

@router.get("/{stock_code}", response_model=ChartCandleResponse)
async def get_candlestick_data(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service)
) -> ChartCandleResponse:
    """
    특정 종목의 캔들스틱 데이터를 조회합니다.
    실제 분봉 데이터를 반환합니다.
    """
    try:
        chart_data = await trading_service.get_minute_chart_data(stock_code)
        if chart_data is None:
            raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다.")
        
        return ChartCandleResponse(
            data=chart_data,
            stock_code=stock_code,
            stock_name=f"Stock {stock_code}"
        )
    except Exception as e:
        logger.error(f"캔들스틱 데이터 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캔들스틱 데이터 조회 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/{stock_code}/minute",
    response_model=List[ChartCandle],
    summary="분봉 차트 데이터 조회",
    description="특정 종목의 분봉 차트 데이터를 조회합니다. 거래시간 필터링 옵션 제공."
)
async def get_minute_chart_data(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service),
    date: Optional[str] = Query(None, description="조회 날짜 (YYYY-MM-DD). 미지정시 오늘"),
    include_extended_hours: bool = Query(False, description="시간외 거래 포함 여부 (8:30~16:00)"),
    regular_hours_only: bool = Query(True, description="정규 장 시간만 (9:00~15:30)")
) -> List[ChartCandle]:
    """
    분봉 차트 데이터 조회

    - regular_hours_only=True: 9:00 ~ 15:30만 (기본값)
    - include_extended_hours=True: 8:30 ~ 16:00 (시간외 포함)
    - 둘 다 False: 모든 시간대 데이터

    거래시간 필터링:
    - 정규 장: 09:00 ~ 15:30
    - 시간외 종가: 08:30 ~ 09:00
    - 시간외 단일가: 15:30 ~ 16:00
    """
    try:
        # 날짜 파싱
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="잘못된 날짜 형식입니다. YYYY-MM-DD 형식을 사용하세요."
                )

        # 차트 데이터 조회 (거래시간 필터링 포함)
        chart_data = await trading_service.get_minute_chart_data(
            stock_code=stock_code,
            target_date=target_date,
            include_extended_hours=include_extended_hours,
            regular_hours_only=regular_hours_only
        )

        if chart_data is None:
            raise HTTPException(status_code=404, detail="차트 데이터를 찾을 수 없습니다.")

        logger.info(
            f"분봉 데이터 조회 완료: {stock_code}, {len(chart_data)}개 캔들 "
            f"(날짜: {date or '오늘'}, 정규장: {regular_hours_only}, 시간외: {include_extended_hours})"
        )
        return chart_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"분봉 차트 데이터 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"분봉 차트 데이터 조회 중 오류가 발생했습니다: {str(e)}"
        )