"""
실시간 API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.services.realtime_service import RealtimeDataService


@pytest.fixture
def mock_realtime_service():
    """Mock RealtimeDataService"""
    service = Mock(spec=RealtimeDataService)
    
    # 캐시된 데이터 반환 (장 시간 내)
    service.get_cached_orderbook.return_value = {
        "stock_code": "005930",
        "current_price": 91600,
        "asks": [
            {"price": 91700, "quantity": 1000, "order_count": 5},
            {"price": 91800, "quantity": 950, "order_count": 4}
        ],
        "bids": [
            {"price": 91600, "quantity": 1000, "order_count": 5},
            {"price": 91500, "quantity": 950, "order_count": 4}
        ],
        "timestamp": "2025-10-14T20:00:00",
        "market_status": "open"
    }
    
    return service


@pytest.fixture
def client_with_mock_service(mock_realtime_service):
    """Mock 서비스가 주입된 테스트 클라이언트"""
    def get_realtime_service_override():
        return mock_realtime_service
    
    from app.dependencies import get_realtime_service
    app.dependency_overrides[get_realtime_service] = get_realtime_service_override
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Cleanup
    app.dependency_overrides.clear()


def test_get_current_orderbook_cached_data(client_with_mock_service, mock_realtime_service):
    """캐시된 호가 데이터 조회 테스트"""
    response = client_with_mock_service.get("/api/realtime/orderbook/005930")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["stock_code"] == "005930"
    assert data["current_price"] == 91600
    assert data["market_status"] == "open"
    assert len(data["asks"]) == 2
    assert len(data["bids"]) == 2
    
    # 캐시 조회 메서드 호출 확인
    mock_realtime_service.get_cached_orderbook.assert_called_once_with("005930")


def test_get_current_orderbook_no_cache(client_with_mock_service, mock_realtime_service):
    """캐시 없는 경우 테스트"""
    # 캐시 없음을 시뮬레이션
    mock_realtime_service.get_cached_orderbook.return_value = None
    
    with patch('app.api.realtime.TradingHoursManager') as mock_trading_hours:
        # 장 시간 내로 설정
        mock_trading_hours.is_trading_hours.return_value = True
        
        response = client_with_mock_service.get("/api/realtime/orderbook/005930")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["stock_code"] == "005930"
        assert data["current_price"] == 91600  # 더미 데이터
        assert data["market_status"] == "open"
        assert len(data["asks"]) == 10
        assert len(data["bids"]) == 10


def test_get_current_orderbook_market_closed(client_with_mock_service, mock_realtime_service):
    """장 시간 외 테스트"""
    # 캐시 없음을 시뮬레이션
    mock_realtime_service.get_cached_orderbook.return_value = None
    
    with patch('app.api.realtime.TradingHoursManager') as mock_trading_hours:
        # 장 시간 외로 설정
        mock_trading_hours.is_trading_hours.return_value = False
        
        response = client_with_mock_service.get("/api/realtime/orderbook/005930")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["stock_code"] == "005930"
        assert data["current_price"] == 0
        assert data["market_status"] == "closed"
        assert len(data["asks"]) == 10
        assert len(data["bids"]) == 10
        
        # 모든 호가가 0이어야 함
        for ask in data["asks"]:
            assert ask["price"] == 0
            assert ask["quantity"] == 0
            assert ask["order_count"] == 0
        
        for bid in data["bids"]:
            assert bid["price"] == 0
            assert bid["quantity"] == 0
            assert bid["order_count"] == 0


def test_subscribe_orderbook(client_with_mock_service):
    """호가 구독 테스트"""
    with patch('app.api.realtime.ws_req_queue') as mock_queue:
        response = client_with_mock_service.post("/api/realtime/subscribe/orderbook?stock_code=005930")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["stock_code"] == "005930"
        assert "구독 시작" in data["message"]
        
        # Queue에 구독 요청이 추가되었는지 확인
        mock_queue.put.assert_called_once()


def test_unsubscribe_orderbook(client_with_mock_service, mock_realtime_service):
    """호가 구독 해제 테스트"""
    with patch('app.api.realtime.ws_req_queue') as mock_queue:
        response = client_with_mock_service.post("/api/realtime/unsubscribe/orderbook?stock_code=005930")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["stock_code"] == "005930"
        assert "구독 해제" in data["message"]
        
        # Queue에 구독 해제 요청이 추가되었는지 확인
        mock_queue.put.assert_called_once()
        
        # 캐시 무효화가 호출되었는지 확인
        mock_realtime_service.invalidate_orderbook_cache.assert_called_once_with("005930")


def test_api_error_handling(client_with_mock_service, mock_realtime_service):
    """API 에러 처리 테스트"""
    # 서비스에서 예외 발생 시뮬레이션
    mock_realtime_service.get_cached_orderbook.side_effect = Exception("Test error")
    
    response = client_with_mock_service.get("/api/realtime/orderbook/005930")
    
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data


def test_invalid_stock_code(client_with_mock_service):
    """잘못된 종목코드 테스트"""
    response = client_with_mock_service.get("/api/realtime/orderbook/invalid")
    
    # 종목코드 검증이 없다면 200이지만, 빈 데이터가 반환될 것
    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "invalid"


if __name__ == "__main__":
    pytest.main([__file__])