"""
계좌 관련 API 엔드포인트
계좌 잔고, 보유 종목, 거래 내역 등을 처리
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from utils.logger import logger

from app.models.schemas import (
    AccountBalance, 
    AccountSummary, 
    Position,
    ApiResponse,
    ErrorResponse
)
from app.services.account_service import AccountService
from app.core.dependencies import get_account_service


router = APIRouter(prefix="/account")

@router.get(
    "/balance",
    response_model=AccountBalance,
    summary="계좌 잔고 조회",
    description="계좌의 전체 잔고 정보와 보유 종목 목록을 조회합니다."
)
async def get_account_balance(
    account_service: AccountService = Depends(get_account_service)
) -> AccountBalance:
    """계좌 잔고 조회"""
    try:
        balance = await account_service.get_balance()
        return balance
    except Exception as e:
        logger.error(f"계좌 잔고 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"계좌 잔고 조회 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/summary",
    response_model=AccountSummary,
    summary="계좌 요약 정보",
    description="계좌의 요약 정보만 조회합니다."
)
async def get_account_summary(
    account_service: AccountService = Depends(get_account_service)
) -> AccountSummary:
    """계좌 요약 정보 조회"""
    try:
        summary = await account_service.get_summary()
        return summary
    except Exception as e:
        logger.error(f"계좌 요약 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"계좌 요약 조회 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/positions",
    response_model=List[Position],
    summary="보유 종목 목록",
    description="현재 보유 중인 종목들의 상세 정보를 조회합니다."
)
async def get_positions(
    account_service: AccountService = Depends(get_account_service)
) -> List[Position]:
    """보유 종목 목록 조회"""
    try:
        positions = await account_service.get_positions()
        return positions
    except Exception as e:
        logger.error(f"보유 종목 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보유 종목 조회 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/positions/{stock_code}",
    response_model=Position,
    summary="특정 종목 포지션 조회",
    description="특정 종목의 보유 정보를 조회합니다."
)
async def get_position_by_stock(
    stock_code: str,
    account_service: AccountService = Depends(get_account_service)
) -> Position:
    """특정 종목 포지션 조회"""
    try:
        position = await account_service.get_position_by_stock(stock_code)
        if not position:
            raise HTTPException(status_code=404, detail=f"종목 {stock_code}에 대한 보유 정보를 찾을 수 없습니다.")
        return position
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 {stock_code} 포지션 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"포지션 조회 중 오류가 발생했습니다: {str(e)}")

@router.post(
    "/refresh",
    response_model=ApiResponse,
    summary="계좌 정보 갱신",
    description="계좌 정보를 강제로 갱신합니다."
)
async def refresh_account_info(
    account_service: AccountService = Depends(get_account_service)
) -> ApiResponse:
    """계좌 정보 강제 갱신"""
    try:
        await account_service.refresh_account_info()
        return ApiResponse(
            success=True,
            message="계좌 정보가 성공적으로 갱신되었습니다."
        )
    except Exception as e:
        logger.error(f"계좌 정보 갱신 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"계좌 정보 갱신 중 오류가 발생했습니다: {str(e)}")

@router.get(
    "/status",
    response_model=dict,
    summary="계좌 연결 상태",
    description="한국투자증권 API 연결 상태를 확인합니다."
)
async def get_account_status(
    account_service: AccountService = Depends(get_account_service)
) -> dict:
    """계좌 연결 상태 확인"""
    try:
        status = await account_service.get_connection_status()
        return {
            "connected": status["connected"],
            "last_update": status["last_update"],
            "account_number": status["account_number"],
            "message": "계좌 연결 상태가 정상입니다." if status["connected"] else "계좌 연결이 끊어져 있습니다."
        }
    except Exception as e:
        logger.error(f"계좌 상태 확인 실패: {str(e)}")
        return {
            "connected": False,
            "last_update": None,
            "account_number": None,
            "message": f"계좌 상태 확인 중 오류가 발생했습니다: {str(e)}"
        }