"""
매매 관련 API 엔드포인트
자동매매 설정, 매매 조건, 매매 상태 등을 처리
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.models.watchlist_models import (
    TradingConditions,
    TradeExecutionResult,
    WatchlistItem
)

router = APIRouter(prefix="/trading")

@router.get(
    "/conditions",
    response_model=TradingConditions,
    summary="매매 조건 조회",
    description="현재 설정된 매수/매도 조건을 조회합니다."
)
async def get_trading_conditions(
    trading_service: TradingService = Depends(get_trading_service)
) -> TradingConditions:
    """매매 조건 조회"""
    try:
        conditions = await trading_service.get_trading_conditions()
        return conditions
    except Exception as e:
        logger.error(f"매매 조건 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매매 조건 조회 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/conditions",
    response_model=ApiResponse,
    summary="매매 조건 설정",
    description="매수/매도 조건을 설정합니다."
)
async def update_trading_conditions(
    conditions: TradingConditions,
    trading_service: TradingService = Depends(get_trading_service)
) -> ApiResponse:
    """매매 조건 설정"""
    try:
        await trading_service.update_trading_conditions(conditions)
        return ApiResponse(
            success=True,
            message="매매 조건이 성공적으로 업데이트되었습니다.",
            data=conditions.dict()
        )
    except Exception as e:
        logger.error(f"매매 조건 설정 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매매 조건 설정 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/start",
    response_model=ApiResponse,
    summary="자동매매 시작",
    description="설정된 조건에 따라 자동매매를 시작합니다."
)
async def start_trading(
    trading_service: TradingService = Depends(get_trading_service)
) -> ApiResponse:
    """자동매매 시작"""
    try:
        result = await trading_service.start_trading()
        if result["success"]:
            return ApiResponse(
                success=True,
                message="자동매매가 시작되었습니다."
            )
        else:
            return ApiResponse(
                success=False,
                message=f"자동매매 시작 실패: {result['message']}"
            )
    except Exception as e:
        logger.error(f"자동매매 시작 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자동매매 시작 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/stop",
    response_model=ApiResponse,
    summary="자동매매 중지",
    description="실행 중인 자동매매를 중지합니다."
)
async def stop_trading(
    trading_service: TradingService = Depends(get_trading_service)
) -> ApiResponse:
    """자동매매 중지"""
    try:
        result = await trading_service.stop_trading()
        return ApiResponse(
            success=True,
            message="자동매매가 중지되었습니다."
        )
    except Exception as e:
        logger.error(f"자동매매 중지 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"자동매매 중지 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/status",
    response_model=dict,
    summary="매매 상태 조회",
    description="현재 자동매매 실행 상태와 통계를 조회합니다."
)
async def get_trading_status(
    trading_service: TradingService = Depends(get_trading_service)
) -> dict:
    """매매 상태 조회"""
    try:
        status = await trading_service.get_trading_status()
        return status
    except Exception as e:
        logger.error(f"매매 상태 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매매 상태 조회 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/execute-buy/{stock_code}",
    response_model=TradeExecutionResult,
    summary="매수 주문 실행",
    description="PyQt5 로직에 따른 자동 매수 주문을 실행합니다."
)
async def execute_buy_order(
    stock_code: str,
    trading_service: TradingService = Depends(get_trading_service)
) -> TradeExecutionResult:
    """자동 매수 주문 실행"""
    try:
        # 가상의 분석 결과 (실제로는 워치리스트 서비스에서 가져와야 함)
        analysis_result = {
            "stock_code": stock_code,
            "current_price": 50000,  # 실제 가격 API에서 가져와야 함
            "current": {
                "macd": 1.5,
                "macd_signal": 1.2,
                "rsi": 35.0
            },
            "previous": {
                "macd": 1.0,
                "macd_signal": 1.3,
                "rsi": 32.0
            }
        }
        
        result = await trading_service.execute_buy_order(stock_code, analysis_result)
        return result
    except Exception as e:
        logger.error(f"매수 주문 실행 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매수 주문 실행 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/execute-sell/{stock_code}",
    response_model=TradeExecutionResult,
    summary="매도 주문 실행",
    description="PyQt5 로직에 따른 자동 매도 주문을 실행합니다."
)
async def execute_sell_order(
    stock_code: str,
    item: WatchlistItem,
    trading_service: TradingService = Depends(get_trading_service)
) -> TradeExecutionResult:
    """자동 매도 주문 실행"""
    try:
        result = await trading_service.execute_sell_order(stock_code, item)
        return result
    except Exception as e:
        logger.error(f"매도 주문 실행 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매도 주문 실행 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/execution-history",
    response_model=List[dict],
    summary="매매 실행 기록 조회",
    description="자동매매 실행 기록을 조회합니다."
)
async def get_execution_history(
    trading_service: TradingService = Depends(get_trading_service)
) -> List[dict]:
    """매매 실행 기록 조회"""
    try:
        history = await trading_service.get_execution_history()
        return history
    except Exception as e:
        logger.error(f"매매 실행 기록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매매 실행 기록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/statistics",
    response_model=dict,
    summary="매매 통계 조회",
    description="자동매매 성과 통계를 조회합니다."
)
async def get_trading_statistics(
    trading_service: TradingService = Depends(get_trading_service)
) -> dict:
    """매매 통계 조회"""
    try:
        statistics = await trading_service.get_trading_statistics()
        return statistics
    except Exception as e:
        logger.error(f"매매 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매매 통계 조회 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/clear-history",
    response_model=ApiResponse,
    summary="매매 기록 초기화",
    description="자동매매 실행 기록을 초기화합니다."
)
async def clear_execution_history(
    trading_service: TradingService = Depends(get_trading_service)
) -> ApiResponse:
    """매매 실행 기록 초기화"""
    try:
        result = await trading_service.clear_execution_history()
        if result["success"]:
            return ApiResponse(
                success=True,
                message=f"매매 실행 기록이 초기화되었습니다. (삭제된 기록: {result['cleared_count']}개)",
                data={"cleared_count": result['cleared_count']}
            )
        else:
            return ApiResponse(
                success=False,
                message="매매 실행 기록 초기화 실패"
            )
    except Exception as e:
        logger.error(f"매매 실행 기록 초기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매매 기록 초기화 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/performance",
    response_model=dict,
    summary="매매 성과 조회",
    description="자동매매의 성과 통계를 조회합니다."
)
async def get_trading_performance(
    days: int = 30,
    trading_service: TradingService = Depends(get_trading_service)
) -> dict:
    """매매 성과 조회"""
    try:
        performance = await trading_service.get_trading_performance(days)
        return performance
    except Exception as e:
        logger.error(f"매매 성과 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"매매 성과 조회 중 오류가 발생했습니다: {str(e)}")