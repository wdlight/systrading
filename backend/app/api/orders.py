"""
주문 관련 API 엔드포인트
사용자 수동 매매 주문 처리
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from loguru import logger

from app.services.order_service import OrderService
from app.core.dependencies import get_korea_invest_service
from app.core.korea_invest import KoreaInvestAPIService
from app.models.order_models import (
    OrderRequest,
    OrderModifyRequest,
    OrderCancelRequest,
    OrderResponse,
    PendingOrdersResponse,
    OrderHistoryResponse,
    OrderSide
)

router = APIRouter()


# OrderService 싱글톤 인스턴스
_order_service_instance: Optional[OrderService] = None


def get_order_service(
    korea_invest_service: KoreaInvestAPIService = Depends(get_korea_invest_service)
) -> OrderService:
    """주문 서비스 의존성 주입 (싱글톤 패턴)"""
    global _order_service_instance
    if _order_service_instance is None:
        _order_service_instance = OrderService(korea_invest_service)
    return _order_service_instance


@router.post(
    "/buy",
    response_model=OrderResponse,
    summary="매수 주문",
    description="지정가 또는 시장가 매수 주문을 실행합니다.",
    tags=["Orders"]
)
async def place_buy_order(
    request: OrderRequest,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """
    매수 주문 실행

    - **stock_code**: 종목 코드 (6자리 숫자)
    - **stock_name**: 종목명
    - **order_type**: 주문 유형 ("00": 지정가, "01": 시장가)
    - **quantity**: 주문 수량
    - **price**: 주문 가격 (시장가는 0 또는 None)
    """
    try:
        # 매수 주문으로 설정
        request.order_side = OrderSide.BUY

        # 주문 실행
        result = await order_service.place_buy_order(request)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except Exception as e:
        logger.error(f"매수 주문 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"매수 주문 처리 중 오류가 발생했습니다: {str(e)}")


@router.post(
    "/sell",
    response_model=OrderResponse,
    summary="매도 주문",
    description="지정가 또는 시장가 매도 주문을 실행합니다.",
    tags=["Orders"]
)
async def place_sell_order(
    request: OrderRequest,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """
    매도 주문 실행

    - **stock_code**: 종목 코드 (6자리 숫자)
    - **stock_name**: 종목명
    - **order_type**: 주문 유형 ("00": 지정가, "01": 시장가)
    - **quantity**: 주문 수량
    - **price**: 주문 가격 (시장가는 0 또는 None)
    """
    try:
        # 매도 주문으로 설정
        request.order_side = OrderSide.SELL

        # 주문 실행
        result = await order_service.place_sell_order(request)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except Exception as e:
        logger.error(f"매도 주문 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"매도 주문 처리 중 오류가 발생했습니다: {str(e)}")


@router.post(
    "/modify",
    response_model=OrderResponse,
    summary="주문 정정",
    description="미체결 주문의 수량이나 가격을 정정합니다.",
    tags=["Orders"]
)
async def modify_order(
    request: OrderModifyRequest,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """
    주문 정정

    - **order_number**: 원주문번호
    - **stock_code**: 종목 코드
    - **order_type**: 정정 주문 유형
    - **quantity**: 정정 수량
    - **price**: 정정 가격
    """
    try:
        result = await order_service.modify_order(request)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except Exception as e:
        logger.error(f"주문 정정 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"주문 정정 처리 중 오류가 발생했습니다: {str(e)}")


@router.delete(
    "/cancel",
    response_model=OrderResponse,
    summary="주문 취소",
    description="미체결 주문을 취소합니다.",
    tags=["Orders"]
)
async def cancel_order(
    request: OrderCancelRequest,
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """
    주문 취소

    - **order_number**: 원주문번호
    - **stock_code**: 종목 코드
    - **order_type**: 취소 주문 유형
    - **quantity**: 취소 수량
    - **price**: 취소 가격
    """
    try:
        result = await order_service.cancel_order(request)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except Exception as e:
        logger.error(f"주문 취소 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"주문 취소 처리 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/pending",
    response_model=PendingOrdersResponse,
    summary="미체결 주문 조회",
    description="미체결 주문 목록을 조회합니다.",
    tags=["Orders"]
)
async def get_pending_orders(
    stock_code: Optional[str] = Query(None, description="종목 코드 (전체 조회시 생략)"),
    order_service: OrderService = Depends(get_order_service)
) -> PendingOrdersResponse:
    """
    미체결 주문 조회

    - **stock_code**: 특정 종목의 미체결 주문만 조회 (선택)
    """
    try:
        result = await order_service.get_pending_orders(stock_code)
        return result

    except Exception as e:
        logger.error(f"미체결 주문 조회 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"미체결 주문 조회 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/history",
    response_model=OrderHistoryResponse,
    summary="체결 내역 조회",
    description="체결 내역 및 취소된 주문 목록을 조회합니다.",
    tags=["Orders"]
)
async def get_order_history(
    stock_code: Optional[str] = Query(None, description="종목 코드 (전체 조회시 생략)"),
    start_date: Optional[str] = Query(None, description="시작일 (YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="종료일 (YYYYMMDD)"),
    order_service: OrderService = Depends(get_order_service)
) -> OrderHistoryResponse:
    """
    체결 내역 조회

    - **stock_code**: 특정 종목의 체결 내역만 조회 (선택)
    - **start_date**: 조회 시작일 (선택)
    - **end_date**: 조회 종료일 (선택)
    """
    try:
        result = await order_service.get_order_history(stock_code, start_date, end_date)
        return result

    except Exception as e:
        logger.error(f"체결 내역 조회 API 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"체결 내역 조회 중 오류가 발생했습니다: {str(e)}")


@router.get(
    "/health",
    summary="주문 서비스 상태 확인",
    description="주문 서비스의 상태를 확인합니다.",
    tags=["Orders"]
)
async def health_check(
    order_service: OrderService = Depends(get_order_service)
) -> dict:
    """
    주문 서비스 상태 확인

    Returns:
        서비스 상태 정보
    """
    try:
        connection_status = order_service.korea_invest.get_connection_status()
        return {
            "status": "ok",
            "message": "주문 서비스가 정상 작동 중입니다.",
            "korea_invest_connected": connection_status.get("connected", False),
            "timestamp": str(__import__('datetime').datetime.now())
        }
    except Exception as e:
        logger.error(f"상태 확인 오류: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"상태 확인 중 오류 발생: {str(e)}",
            "timestamp": str(__import__('datetime').datetime.now())
        }
