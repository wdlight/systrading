"""Portfolio Analytics 테스트"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.services.portfolio_analytics_service import PortfolioAnalyticsService
from app.models.schemas import Trade


@pytest.mark.asyncio
async def test_portfolio_history_basic():
    """기본 시계열 조회 테스트"""

    # Mock 서비스
    korea_invest_mock = Mock()
    korea_invest_mock.get_account_balance = AsyncMock(return_value={
        "positions": [
            {"stock_code": "005930", "quantity": 10}
        ],
        "available_cash": 1000000
    })

    benchmark_mock = Mock()

    service = PortfolioAnalyticsService(
        korea_invest_mock,
        benchmark_mock
    )

    result = await service.get_portfolio_history("1W")

    assert len(result) > 0
    assert all(hasattr(p, "date") for p in result)
    assert all(hasattr(p, "portfolio") for p in result)
    assert all(hasattr(p, "benchmark") for p in result)


@pytest.mark.asyncio
async def test_trade_history_reconstruction():
    """거래 내역 포지션 재구성 테스트"""
    from app.services.trade_history_service import TradeHistoryService

    service = TradeHistoryService(Mock())

    # 테스트 데이터
    trades = [
        Trade(
            trade_date="20251010",
            stock_code="005930",
            stock_name="삼성전자",
            trade_type="buy",
            quantity=10,
            price=70000,
            amount=700000,
            fee=105,
            tax=0
        )
    ]

    current_positions = {"005930": 20}
    trading_days = [
        datetime(2025, 10, 9),
        datetime(2025, 10, 10)
    ]

    result = service.reconstruct_daily_positions(
        trades,
        current_positions,
        trading_days
    )

    # 10/9: 10주 매수 전 → 10주
    # 10/10: 매수 후 → 20주
    assert result[datetime(2025, 10, 9)]["005930"] == 10
    assert result[datetime(2025, 10, 10)]["005930"] == 20


@pytest.mark.asyncio
async def test_cash_flow_calculation():
    """현금 흐름 계산 테스트"""
    from app.services.cash_flow_tracker import CashFlowTracker

    tracker = CashFlowTracker()

    trades = [
        Trade(
            trade_date="20251010",
            stock_code="005930",
            stock_name="삼성전자",
            trade_type="buy",
            quantity=10,
            price=70000,
            amount=700000,
            fee=105,
            tax=0
        )
    ]

    current_cash = 1000000
    trading_days = [
        datetime(2025, 10, 9),
        datetime(2025, 10, 10)
    ]

    result = tracker.calculate_daily_cash(
        trades,
        current_cash,
        trading_days
    )

    # 10/9: 매수 전 → 1,700,105원
    # 10/10: 매수 후 → 1,000,000원
    assert result[datetime(2025, 10, 9)] == 1700105
    assert result[datetime(2025, 10, 10)] == 1000000
