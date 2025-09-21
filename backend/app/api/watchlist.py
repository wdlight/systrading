"""
워치리스트 관련 API 엔드포인트
실시간 모니터링 중인 종목들의 정보를 처리
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from utils.logger import logger

from app.models.watchlist_models import (
    WatchlistItem,
    TechnicalIndicators,
    AddStockRequest,
    RemoveStockRequest,
    MarketDataSnapshot,
    PriceUpdateEvent,
    WatchlistUpdateEvent
)
from app.models.schemas import ApiResponse
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.watchlist_service import WatchlistService
from app.core.dependencies import get_watchlist_service


router = APIRouter(prefix="/watchlist")

@router.get(
    "",
    response_model=List[WatchlistItem],
    summary="워치리스트 조회",
    description="현재 모니터링 중인 모든 종목의 실시간 정보를 조회합니다."
)
async def get_watchlist(
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> List[WatchlistItem]:
    """워치리스트 조회"""
    try:
        watchlist = await watchlist_service.get_watchlist()
        return watchlist
    except Exception as e:
        logger.error(f"워치리스트 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워치리스트 조회 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/{stock_code}",
    response_model=WatchlistItem,
    summary="특정 종목 정보 조회",
    description="워치리스트에서 특정 종목의 상세 정보를 조회합니다."
)
async def get_watchlist_item(
    stock_code: str,
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> WatchlistItem:
    """특정 종목 정보 조회"""
    try:
        item = await watchlist_service.get_watchlist_item(stock_code)
        if not item:
            raise HTTPException(status_code=404, detail=f"종목 {stock_code}이 워치리스트에 없습니다.")
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 {stock_code} 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"종목 정보 조회 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/add",
    response_model=ApiResponse,
    summary="종목 추가",
    description="워치리스트에 새로운 종목을 추가합니다."
)
async def add_to_watchlist(
    request: AddStockRequest,
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> ApiResponse:
    """워치리스트에 종목 추가"""
    try:
        result = await watchlist_service.add_stock(request.stock_code)
        if result["success"]:
            return ApiResponse(
                success=True,
                message=f"종목 {request.stock_code}이 워치리스트에 추가되었습니다.",
                data={"stock_code": request.stock_code}
            )
        else:
            return ApiResponse(
                success=False,
                message=f"종목 추가 실패: {result['message']}"
            )
    except Exception as e:
        logger.error(f"종목 {request.stock_code} 추가 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"종목 추가 중 오류가 발생했습니다: {str(e)}")

@router.delete(
    "/{stock_code}",
    response_model=ApiResponse,
    summary="종목 제거",
    description="워치리스트에서 종목을 제거합니다."
)
async def remove_from_watchlist(
    stock_code: str,
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> ApiResponse:
    """워치리스트에서 종목 제거"""
    try:
        result = await watchlist_service.remove_stock(stock_code)
        if result["success"]:
            return ApiResponse(
                success=True,
                message=f"종목 {stock_code}이 워치리스트에서 제거되었습니다.",
                data={"stock_code": stock_code}
            )
        else:
            return ApiResponse(
                success=False,
                message=f"종목 제거 실패: {result['message']}"
            )
    except Exception as e:
        logger.error(f"종목 {stock_code} 제거 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"종목 제거 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/{stock_code}/indicators",
    response_model=TechnicalIndicators,
    summary="기술적 지표 조회",
    description="특정 종목의 RSI, MACD 등 기술적 지표를 조회합니다."
)
async def get_technical_indicators(
    stock_code: str,
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> TechnicalIndicators:
    """기술적 지표 조회"""
    try:
        indicators = await watchlist_service.get_technical_indicators(stock_code)
        if not indicators:
            raise HTTPException(status_code=404, detail=f"종목 {stock_code}의 기술적 지표를 찾을 수 없습니다.")
        return indicators
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 {stock_code} 기술적 지표 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"기술적 지표 조회 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/{stock_code}/price",
    response_model=MarketDataSnapshot,
    summary="실시간 가격 조회",
    description="특정 종목의 실시간 가격 정보를 조회합니다."
)
async def get_stock_price(
    stock_code: str,
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> MarketDataSnapshot:
    """실시간 가격 조회"""
    try:
        stock_data = await watchlist_service.get_stock_price(stock_code)
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"종목 {stock_code}의 가격 정보를 찾을 수 없습니다.")
        return stock_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 {stock_code} 가격 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"가격 정보 조회 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/refresh",
    response_model=ApiResponse,
    summary="워치리스트 갱신",
    description="워치리스트의 모든 데이터를 강제로 갱신합니다."
)
async def refresh_watchlist(
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> ApiResponse:
    """워치리스트 강제 갱신"""
    try:
        result = await watchlist_service.refresh_all_data()
        return ApiResponse(
            success=True,
            message="워치리스트가 성공적으로 갱신되었습니다.",
            data={"updated_count": result["updated_count"]}
        )
    except Exception as e:
        logger.error(f"워치리스트 갱신 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워치리스트 갱신 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/clear",
    response_model=ApiResponse,
    summary="워치리스트 초기화",
    description="워치리스트를 완전히 초기화합니다."
)
async def clear_watchlist(
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> ApiResponse:
    """워치리스트 초기화"""
    try:
        result = await watchlist_service.clear_watchlist()
        return ApiResponse(
            success=True,
            message="워치리스트가 초기화되었습니다.",
            data={"removed_count": result["removed_count"]}
        )
    except Exception as e:
        logger.error(f"워치리스트 초기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워치리스트 초기화 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/statistics",
    response_model=dict,
    summary="워치리스트 통계",
    description="워치리스트의 전체 통계 정보를 조회합니다."
)
async def get_watchlist_statistics(
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> dict:
    """워치리스트 통계 조회"""
    try:
        stats = await watchlist_service.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"워치리스트 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/{stock_code}/update",
    response_model=ApiResponse,
    summary="실시간 데이터 업데이트",
    description="특정 종목의 실시간 가격 데이터를 업데이트합니다."
)
async def update_stock_data(
    stock_code: str,
    price_update: PriceUpdateEvent,
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> ApiResponse:
    """실시간 주가 데이터 업데이트"""
    try:
        # 주가 데이터 업데이트
        success = await watchlist_service.update_stock_data(
            stock_code, 
            int(price_update.current_price)
        )
        
        if success:
            return ApiResponse(
                success=True,
                message=f"종목 {stock_code} 데이터가 업데이트되었습니다.",
                data={
                    "stock_code": stock_code,
                    "current_price": price_update.current_price,
                    "timestamp": price_update.timestamp.isoformat()
                }
            )
        else:
            return ApiResponse(
                success=False,
                message=f"종목 {stock_code} 데이터 업데이트 실패"
            )
            
    except Exception as e:
        logger.error(f"종목 {stock_code} 데이터 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"데이터 업데이트 중 오류가 발생했습니다: {str(e)}"
        )

@router.get(
    "/{stock_code}/analysis",
    response_model=dict,
    summary="기술적 분석 조회",
    description="특정 종목의 1분봉 데이터를 기반으로 한 기술적 분석 결과를 조회합니다."
)
async def get_technical_analysis(
    stock_code: str,
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> dict:
    """기술적 분석 결과 조회"""
    try:
        # 기본적인 가격 데이터 조회
        if stock_code not in watchlist_service.price_history:
            raise HTTPException(
                status_code=404, 
                detail=f"종목 {stock_code}의 가격 히스토리를 찾을 수 없습니다."
            )
        
        price_history = watchlist_service.price_history[stock_code]
        
        if len(price_history) < 20:
            return {
                "stock_code": stock_code,
                "message": "분석에 충분한 데이터가 대기 중입니다.",
                "data_points": len(price_history),
                "required_points": 20
            }
        
        # DataFrame 구조를 TechnicalAnalysisService에 맞게 변환
        minute_data = price_history.rename(columns={'close': '종가'})
        
        # 기술적 분석 실행
        analysis_result = TechnicalAnalysisService.analyze_minute_data(stock_code, minute_data)
        
        return {
            "stock_code": stock_code,
            "analysis_result": analysis_result,
            "data_points": len(price_history),
            "last_update": price_history['timestamp'].iloc[-1].isoformat() if not price_history.empty else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 {stock_code} 기술적 분석 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"기술적 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.post(
    "/bulk-update",
    response_model=ApiResponse,
    summary="대량 데이터 업데이트",
    description="워치리스트의 여러 종목을 대량으로 업데이트합니다."
)
async def bulk_update_watchlist(
    updates: List[PriceUpdateEvent],
    watchlist_service: WatchlistService = Depends(get_watchlist_service)
) -> ApiResponse:
    """대량 데이터 업데이트"""
    try:
        updated_count = 0
        failed_count = 0
        
        for update in updates:
            try:
                success = await watchlist_service.update_stock_data(
                    update.stock_code, 
                    int(update.current_price)
                )
                if success:
                    updated_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"종목 {update.stock_code} 업데이트 실패: {str(e)}")
                failed_count += 1
        
        return ApiResponse(
            success=True,
            message=f"대량 업데이트 완료: {updated_count}개 성공, {failed_count}개 실패",
            data={
                "updated_count": updated_count,
                "failed_count": failed_count,
                "total_count": len(updates)
            }
        )
        
    except Exception as e:
        logger.error(f"대량 데이터 업데이트 실패: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"대량 업데이트 중 오류가 발생했습니다: {str(e)}"
        )