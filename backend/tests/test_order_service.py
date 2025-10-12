# backend/tests/test_order_service.py
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.services.order_service import OrderService
from app.models.order_models import OrderRequest, OrderType

@pytest.mark.asyncio
async def test_place_buy_order_limit_price_validation():
    """지정가 주문 시 가격이 0이거나 없으면 실패해야 한다."""
    mock_korea_invest = AsyncMock()
    order_service = OrderService(mock_korea_invest)
    
    # 가격이 0인 지정가 주문
    invalid_request_zero_price = OrderRequest(
        stock_code="005930", stock_name="삼성전자", order_type=OrderType.LIMIT, quantity=1, price=0
    )
    
    # 가격이 없는 지정가 주문
    invalid_request_none_price = OrderRequest(
        stock_code="005930", stock_name="삼성전자", order_type=OrderType.LIMIT, quantity=1, price=None
    )
    
    response_zero = await order_service.place_buy_order(invalid_request_zero_price)
    response_none = await order_service.place_buy_order(invalid_request_none_price)
    
    assert not response_zero.success
    assert "가격을 입력해야 합니다" in response_zero.message
    
    assert not response_none.success
    assert "가격을 입력해야 합니다" in response_none.message
    
    # 실제 API가 호출되지 않았는지 확인
    mock_korea_invest.buy_order.assert_not_called()
