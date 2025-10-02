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
            #regular_hours_only=False # 1002 임시 수정..
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


@router.get(
    "/{stock_code}/minute/full",
    response_model=List[ChartCandle],
    summary="당일 전체 분봉 데이터 (9:00~15:30)",
    description="당일 전체 거래시간 분봉 데이터. 미래 시간은 직전 종가로 채움 (volume=0). 총 391개 캔들."
)
async def get_full_day_minute_chart(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service),
    date: Optional[str] = Query(None, description="조회 날짜 (YYYY-MM-DD). 미지정시 오늘")
) -> List[ChartCandle]:
    """
    당일 전체 분봉 데이터 반환 (항상 9:00~15:30)
    
    - 실제 거래 시간: 실제 OHLCV 데이터
    - 미래 시간: 직전 종가로 채움 (volume=0)
    - 총 391개 캔들 반환
    
    **사용 시나리오:**
    - 11:00 접속 시 → 9:00~11:00 실제 데이터 + 11:00~15:30 채움 데이터
    - 양방향 스크롤 지원 (좌측: 전일, 우측: 당일 미래)
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
        
        # 전체 분봉 데이터 조회
        full_day_candles = await trading_service.get_full_day_candles(
            stock_code=stock_code,
            target_date=target_date
        )
        
        if not full_day_candles:
            raise HTTPException(
                status_code=404,
                detail=f"차트 데이터를 찾을 수 없습니다: {stock_code}"
            )
        
        logger.info(
            f"Full day 분봉 데이터 조회 완료: {stock_code}, {len(full_day_candles)}개 캔들 "
            f"(날짜: {date or '오늘'})"
        )
        
        return full_day_candles
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full day 분봉 데이터 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"전체 분봉 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get(
    "/{stock_code}/minute/current",
    response_model=ChartCandle,
    summary="현재 분봉 데이터 (실시간 업데이트용)",
    description="현재 분의 최신 캔들 데이터 반환. 매 분마다 호출 가능. Cache 자동 업데이트."
)
async def get_current_minute_candle(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service)
) -> ChartCandle:
    """
    현재 분의 최신 캔들 데이터 반환 (실시간 업데이트용)

    **동작:**
    1. 한투 API에서 최신 분봉 fetch
    2. Cache 파일 자동 업데이트
    3. 최신 캔들 반환

    **사용 시나리오:**
    - Frontend에서 매 1분마다 polling
    - 거래시간(9:00~15:30) 중에만 호출
    - 실시간 차트 업데이트

    **Side Effect:**
    - Cache 파일의 해당 분봉 자동 갱신
    """
    try:
        # 최신 분봉 조회
        current_candle = await trading_service.get_current_minute_candle(stock_code)

        if not current_candle:
            raise HTTPException(
                status_code=404,
                detail=f"현재 분봉 데이터를 찾을 수 없습니다: {stock_code}"
            )

        # Cache 자동 업데이트 (당일 데이터만)
        today = datetime.now()
        candle_date = datetime.fromisoformat(current_candle.timestamp).date()

        if candle_date == today.date():
            updated = await trading_service.update_minute_candle(
                stock_code=stock_code,
                target_date=today,
                candle_data=current_candle
            )

            if updated:
                logger.info(f"Cache 자동 업데이트 완료: {stock_code}, {current_candle.timestamp}")
            else:
                logger.warning(f"Cache 업데이트 실패: {stock_code}, {current_candle.timestamp}")

        return current_candle

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"현재 분봉 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"현재 분봉 조회 중 오류 발생: {str(e)}"
        )
