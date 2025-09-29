from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.core.dependencies import get_stock_service
from app.services.stock_service import StockService
from loguru import logger
from app.models.schemas import ApiResponse

router = APIRouter()

@router.get("/{stock_code}/chart/test", response_model=ApiResponse,
    summary="API 연결 테스트",
    description="프론트엔드에서 백엔드 API 연결 상태를 테스트하기 위한 엔드포인트입니다."
)
async def test_api_connection(
    stock_code: str
) -> ApiResponse:
    """API 연결 테스트"""
    return ApiResponse(
        success=True,
        message=f"API 연결 테스트 성공: {stock_code}에 대한 차트 테스트 엔드포인트가 응답했습니다.",
        data={
            "stock_code": stock_code,
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        }
    )

@router.get("/{stock_code}/price")
async def get_stock_current_price(
    stock_code: str,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    종목의 실시간 현재가 정보 조회
    """
    price_data = await stock_service.get_current_price(stock_code)
    if price_data is None:
        raise HTTPException(status_code=404, detail=f"Failed to get current price for {stock_code}")

    response_data = {
        "success": True,
        "stock_code": stock_code,
        "current_price": int(price_data.get("stck_prpr", "0")),
        "change_amount": int(price_data.get("prdy_vrss", "0")),
        "change_rate": float(price_data.get("prdy_ctrt", "0.0")),
        "volume": int(price_data.get("acml_vol", "0")),
        "trading_value": int(price_data.get("acml_tr_pbmn", "0")),
        "high_price": int(price_data.get("stck_hgpr", "0")),
        "low_price": int(price_data.get("stck_lwpr", "0")),
        "open_price": int(price_data.get("stck_oprc", "0")),
        "previous_close": int(price_data.get("stck_sdpr", "0")),
        "market_cap": int(price_data.get("mktm", "0")),
        "timestamp": datetime.now().isoformat(),
        "market_status": price_data.get("mksc_shrn_iscd", ""),
    }
    return response_data

@router.get("/{stock_code}/quote")
async def get_stock_quote_info(
    stock_code: str,
    stock_service: StockService = Depends(get_stock_service)
):
    """
    종목의 상세 시세 정보 조회 (현재가 + 추가 정보)
    """
    quote_data = await stock_service.get_quote_info(stock_code)
    if quote_data is None:
        raise HTTPException(status_code=404, detail=f"Failed to get quote info for {stock_code}")

    response_data = {
        "success": True,
        "stock_code": stock_code,
        "current_price": int(quote_data.get("stck_prpr", "0")),
        "change_amount": int(quote_data.get("prdy_vrss", "0")),
        "change_rate": float(quote_data.get("prdy_ctrt", "0.0")),
        "volume": int(quote_data.get("acml_vol", "0")),
        "trading_value": int(quote_data.get("acml_tr_pbmn", "0")),
        "high_price": int(quote_data.get("stck_hgpr", "0")),
        "low_price": int(quote_data.get("stck_lwpr", "0")),
        "open_price": int(quote_data.get("stck_oprc", "0")),
        "previous_close": int(quote_data.get("stck_sdpr", "0")),
        "market_cap": int(quote_data.get("mktm", "0")),
        "timestamp": datetime.now().isoformat(),
        "market_status": quote_data.get("mksc_shrn_iscd", ""),
        "recent_candles": quote_data.get("recent_candles", []),
        "avg_volume_5d": quote_data.get("avg_volume_5d", 0),
        "price_range_5d": quote_data.get("price_range_5d", {"high": 0, "low": 0}),
        "last_updated": quote_data.get("last_updated")
    }
    return response_data


@router.get("/{stock_code}/chart", response_model=Dict[str, Any])
async def get_stock_chart_data(
    stock_code: str,
    period: str = Query('D', description="기간 구분 (D: 일, W: 주, M: 월)"),
    format: str = Query('kis', description="응답 형식 (kis: 원본, frontend: 프론트엔드용)"),
    stock_service: StockService = Depends(get_stock_service)
):
    """
    지정된 종목 코드와 기간에 대한 차트 데이터를 조회합니다.
    """
    if period not in ['D', 'W', 'M']:
        raise HTTPException(status_code=400, detail="기간(period)은 'D', 'W', 'M' 중 하나여야 합니다.")

    if format not in ['kis', 'frontend']:
        raise HTTPException(status_code=400, detail="format은 'kis' 또는 'frontend' 중 하나여야 합니다.")

    logger.info(f"{stock_code}에 대한 {period} 차트 데이터 요청 (format: {format})")

    try:
        # 기본 차트 데이터 조회
        chart_data = await stock_service.get_chart_data(stock_code, period)
        if chart_data is None:
            raise HTTPException(status_code=500, detail="API 서비스에서 데이터를 가져오는 데 실패했습니다.")

        if not chart_data.get("output2"):
            logger.warning(f"{stock_code} ({period})에 대한 데이터가 없습니다.")
            if format == 'frontend':
                return {
                    "success": False,
                    "message": "차트 데이터가 없습니다.",
                    "data": [],
                    "metadata": {
                        "stock_code": stock_code,
                        "period": period,
                        "count": 0,
                        "last_updated": datetime.now().isoformat()
                    }
                }
            else:
                return {"output1": {}, "output2": []}

        # format에 따른 응답 처리
        if format == 'frontend':
            return await _convert_to_frontend_format(stock_code, period, chart_data)
        else:
            return chart_data

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"차트 데이터 API 처리 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"서버 내부 오류가 발생했습니다: {e}")

async def _convert_to_frontend_format(stock_code: str, period: str, chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    KIS API 응답을 프론트엔드 친화적 형식으로 변환
    """
    try:
        output2 = chart_data.get("output2", [])
        converted_data = []

        for item in output2:
            try:
                # 기본 OHLCV 데이터 변환
                open_price = int(item.get("stck_oprc", "0"))
                high_price = int(item.get("stck_hgpr", "0"))
                low_price = int(item.get("stck_lwpr", "0"))
                close_price = int(item.get("stck_clpr", "0"))
                volume = int(item.get("acml_vol", "0"))
                date_str = item.get("stck_bsop_date", "")

                # 날짜 형식 변환 (YYYYMMDD -> ISO format)
                try:
                    if len(date_str) == 8:
                        date_obj = datetime.strptime(date_str, "%Y%m%d")
                        timestamp = date_obj.isoformat()
                    else:
                        timestamp = date_str
                except:
                    timestamp = date_str

                converted_item = {
                    "timestamp": timestamp,
                    "open": open_price,
                    "high": high_price,
                    "low": low_price,
                    "close": close_price,
                    "volume": volume,
                    "tradingValue": close_price * volume,
                    # 실제 외국인/기관 데이터는 별도 API 필요 (임시값)
                    "foreignBuy": 0,
                    "foreignSell": 0,
                    "institutionalBuy": 0,
                    "institutionalSell": 0,
                    "individualBuy": volume,  # 임시로 개인투자자 매수량을 전체 거래량으로 설정
                    "individualSell": 0
                }

                # 데이터 유효성 검증
                if (low_price <= close_price <= high_price and
                    low_price <= open_price <= high_price and
                    all(price > 0 for price in [open_price, high_price, low_price, close_price]) and
                    volume >= 0):
                    converted_data.append(converted_item)
                else:
                    logger.warning(f"유효하지 않은 OHLCV 데이터: {item}")

            except (ValueError, TypeError) as e:
                logger.warning(f"데이터 변환 실패: {item}, 오류: {e}")
                continue

        # 날짜순 정렬 (오래된 데이터부터)
        converted_data.sort(key=lambda x: x['timestamp'])

        # 통계 정보 계산
        total_volume = sum(item['volume'] for item in converted_data)
        avg_price = sum(item['close'] for item in converted_data) / len(converted_data) if converted_data else 0

        return {
            "success": True,
            "message": "차트 데이터 조회 성공",
            "data": converted_data,
            "metadata": {
                "stock_code": stock_code,
                "period": period,
                "count": len(converted_data),
                "total_volume": total_volume,
                "average_price": round(avg_price, 2),
                "date_range": {
                    "start": converted_data[0]['timestamp'] if converted_data else None,
                    "end": converted_data[-1]['timestamp'] if converted_data else None
                },
                "last_updated": datetime.now().isoformat()
            }
        }

    except Exception as e:
        logger.error(f"프론트엔드 형식 변환 중 오류: {e}")
        return {
            "success": False,
            "message": f"데이터 변환 실패: {str(e)}",
            "data": [],
            "metadata": {
                "stock_code": stock_code,
                "period": period,
                "count": 0,
                "last_updated": datetime.now().isoformat()
            }
        }