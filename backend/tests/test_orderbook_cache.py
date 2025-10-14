"""
호가 캐시 테스트
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from app.services.realtime_service import RealtimeDataService


@pytest.fixture
def mock_korea_invest_service():
    """Mock KoreaInvestAPIService"""
    return Mock()


@pytest.fixture
def mock_connection_manager():
    """Mock ConnectionManager"""
    manager = Mock()
    manager.broadcast_to_stock_subscribers = AsyncMock()
    return manager


@pytest.fixture
def mock_queue():
    """Mock Queue"""
    return Mock()


@pytest.fixture
def realtime_service(mock_korea_invest_service, mock_connection_manager, mock_queue):
    """RealtimeDataService 인스턴스"""
    return RealtimeDataService(
        mock_korea_invest_service,
        mock_connection_manager,
        mock_queue
    )


@pytest.mark.asyncio
async def test_orderbook_cache_ttl(realtime_service):
    """호가 캐시 TTL 테스트"""
    with patch('app.utils.trading_hours.TradingHoursManager') as mock_trading_hours:
        # 장 시간 내로 설정
        mock_trading_hours.is_trading_hours.return_value = True
        
        # 캐시 저장
        await realtime_service._handle_hoga_data({
            "stock_code": "005930",
            "data": {
                "stock_code": "005930",
                "asks": [{"price": 71800, "quantity": 100, "order_count": 0}],
                "bids": [{"price": 71700, "quantity": 150, "order_count": 0}],
                "current_price": 71700,
                "timestamp": "2025-10-14T18:00:15"
            }
        })
    
    # 즉시 조회: 성공
    cached = realtime_service.get_cached_orderbook("005930")
    assert cached is not None
    assert cached["stock_code"] == "005930"
    assert cached["current_price"] == 71700
    
    # TTL 만료 시뮬레이션 (300초 후)
    realtime_service.orderbook_cache_ttl = 0.1  # 100ms로 설정
    time.sleep(0.2)  # 200ms 대기
    
    # TTL 만료 후 조회: None
    cached = realtime_service.get_cached_orderbook("005930")
    assert cached is None


@pytest.mark.asyncio
async def test_orderbook_cache_invalidation(realtime_service):
    """호가 캐시 무효화 테스트"""
    with patch('app.utils.trading_hours.TradingHoursManager') as mock_trading_hours:
        # 장 시간 내로 설정
        mock_trading_hours.is_trading_hours.return_value = True
        
        # 캐시 저장
        await realtime_service._handle_hoga_data({
            "stock_code": "005930",
            "data": {
                "stock_code": "005930",
                "asks": [{"price": 71800, "quantity": 100, "order_count": 0}],
                "bids": [{"price": 71700, "quantity": 150, "order_count": 0}],
                "current_price": 71700,
                "timestamp": "2025-10-14T18:00:15"
            }
        })
    
    # 캐시 존재 확인
    cached = realtime_service.get_cached_orderbook("005930")
    assert cached is not None
    
    # 캐시 무효화
    realtime_service.invalidate_orderbook_cache("005930")
    
    # 캐시 삭제 확인
    cached = realtime_service.get_cached_orderbook("005930")
    assert cached is None


@pytest.mark.asyncio
async def test_orderbook_cache_multiple_stocks(realtime_service):
    """여러 종목 캐시 테스트"""
    with patch('app.utils.trading_hours.TradingHoursManager') as mock_trading_hours:
        # 장 시간 내로 설정
        mock_trading_hours.is_trading_hours.return_value = True
        
        # 첫 번째 종목 캐시
        await realtime_service._handle_hoga_data({
            "stock_code": "005930",
            "data": {
                "stock_code": "005930",
                "asks": [{"price": 71800, "quantity": 100, "order_count": 0}],
                "bids": [{"price": 71700, "quantity": 150, "order_count": 0}],
                "current_price": 71700,
                "timestamp": "2025-10-14T18:00:15"
            }
        })
        
        # 두 번째 종목 캐시
        await realtime_service._handle_hoga_data({
            "stock_code": "000660",
            "data": {
                "stock_code": "000660",
                "asks": [{"price": 120000, "quantity": 200, "order_count": 0}],
                "bids": [{"price": 119000, "quantity": 250, "order_count": 0}],
                "current_price": 119500,
                "timestamp": "2025-10-14T18:00:15"
            }
        })
    
    # 두 종목 모두 캐시에 있어야 함
    cached_005930 = realtime_service.get_cached_orderbook("005930")
    cached_000660 = realtime_service.get_cached_orderbook("000660")
    
    assert cached_005930 is not None
    assert cached_005930["current_price"] == 71700
    
    assert cached_000660 is not None
    assert cached_000660["current_price"] == 119500
    
    # 하나만 무효화
    realtime_service.invalidate_orderbook_cache("005930")
    
    # 005930은 삭제, 000660은 유지
    cached_005930 = realtime_service.get_cached_orderbook("005930")
    cached_000660 = realtime_service.get_cached_orderbook("000660")
    
    assert cached_005930 is None
    assert cached_000660 is not None


@pytest.mark.asyncio
async def test_orderbook_cache_broadcast(realtime_service):
    """호가 데이터 브로드캐스트 테스트"""
    with patch('app.utils.trading_hours.TradingHoursManager') as mock_trading_hours:
        # 장 시간 내로 설정
        mock_trading_hours.is_trading_hours.return_value = True
        
        # 호가 데이터 처리
        await realtime_service._handle_hoga_data({
            "stock_code": "005930",
            "data": {
                "stock_code": "005930",
                "asks": [{"price": 71800, "quantity": 100, "order_count": 0}],
                "bids": [{"price": 71700, "quantity": 150, "order_count": 0}],
                "current_price": 71700,
                "timestamp": "2025-10-14T18:00:15"
            }
        })
    
    # 브로드캐스트 호출 확인
    realtime_service.connection_manager.broadcast_to_stock_subscribers.assert_called_once()
    
    # 호출된 인수 확인
    call_args = realtime_service.connection_manager.broadcast_to_stock_subscribers.call_args
    stock_code = call_args[0][0]
    message = call_args[0][1]
    
    assert stock_code == "005930"
    assert message["type"] == "orderbook_update"
    assert message["stock_code"] == "005930"
    assert "data" in message


@pytest.mark.asyncio
async def test_orderbook_cache_invalid_data(realtime_service):
    """잘못된 데이터 처리 테스트"""
    # 빈 데이터로 처리 시도
    await realtime_service._handle_hoga_data({
        "stock_code": "",  # 빈 종목코드
        "data": {}
    })
    
    # 캐시에 저장되지 않아야 함
    cached = realtime_service.get_cached_orderbook("")
    assert cached is None
    
    # 종목코드가 없는 경우
    await realtime_service._handle_hoga_data({
        "data": {
            "stock_code": "005930",
            "asks": [{"price": 71800, "quantity": 100, "order_count": 0}],
            "bids": [{"price": 71700, "quantity": 150, "order_count": 0}],
            "current_price": 71700,
            "timestamp": "2025-10-14T18:00:15"
        }
    })
    
    # 캐시에 저장되지 않아야 함
    cached = realtime_service.get_cached_orderbook("005930")
    assert cached is None


if __name__ == "__main__":
    pytest.main([__file__])
