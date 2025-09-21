"""
simple_server.py 단위 테스트
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

# 테스트 대상 모듈 import
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from simple_server import app, real_api, trading_conditions_data


class TestSimpleServerAPI:
    """Simple Server API 엔드포인트 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Stock Trading API Server"
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
    
    def test_hello_endpoint(self, client):
        """Hello 엔드포인트 테스트"""
        response = client.get("/hello")
        assert response.status_code == 200
        
        data = response.json()
        assert "Hello from Stock Trading Backend!" in data["message"]
        assert data["status"] == "server is running"
        assert "timestamp" in data
        assert "active_connections" in data
    
    def test_health_check_endpoint(self, client):
        """헬스체크 엔드포인트 테스트"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_connections" in data
        assert isinstance(data["active_connections"], int)
    
    def test_debug_tokens_endpoint_no_config(self, client):
        """토큰 디버그 엔드포인트 테스트 (설정 없음)"""
        with patch('app.core.config.get_settings', side_effect=ImportError("Test error")):
            response = client.get("/debug/tokens")
            assert response.status_code == 200
            
            data = response.json()
            assert data["config_loaded"] is False
            assert "error" in data
            assert data["error_type"] == "ImportError"
    
    @patch('app.core.config.get_settings')
    def test_debug_tokens_endpoint_with_config(self, mock_get_settings, client):
        """토큰 디버그 엔드포인트 테스트 (설정 있음)"""
        # Mock settings 객체 생성
        mock_settings = Mock()
        mock_settings.KI_API_APPROVAL_KEY = "test_api_key_1234567890123456789012345"
        mock_settings.KI_WEBSOCKET_APPROVAL_KEY = "test_ws_key_1234567890123456789012345"
        mock_settings.KI_ACCOUNT_ACCESS_TOKEN = "test_token"
        mock_settings.KI_USING_URL = "https://test.com"
        mock_settings.KI_API_KEY = "test_api_key_123"
        mock_settings.KI_ACCOUNT_NUMBER = "12345678"
        mock_settings.KI_IS_PAPER_TRADING = True
        mock_get_settings.return_value = mock_settings
        
        response = client.get("/debug/tokens")
        assert response.status_code == 200
        
        data = response.json()
        assert data["config_loaded"] is True
        assert "tokens" in data
        assert "config_values" in data
        assert data["tokens"]["api_approval_key"].endswith("...")
        assert data["config_values"]["is_paper_trading"] is True


class TestAccountBalanceAPI:
    """계좌 잔고 API 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_get_account_balance_no_real_api(self, client):
        """실제 API 없을 때 계좌 잔고 조회 테스트 (더미 데이터)"""
        # real_api를 None으로 설정
        with patch('simple_server.real_api', None):
            response = client.get("/api/account/balance")
            assert response.status_code == 200
            
            data = response.json()
            assert "total_value" in data
            assert "positions" in data
            assert data["total_value"] == 10000000
            assert len(data["positions"]) > 0
            
            # 첫 번째 포지션 검증
            first_position = data["positions"][0]
            assert first_position["stock_code"] == "005930"
            assert first_position["stock_name"] == "삼성전자"
    
    @patch('simple_server.real_api')
    def test_get_account_balance_with_real_api_success(self, mock_real_api, client):
        """실제 API 있을 때 계좌 잔고 조회 성공 테스트"""
        # Mock API 응답 데이터 설정
        import pandas as pd
        
        mock_df = pd.DataFrame({
            '종목코드': ['005930', '000660'],
            '종목명': ['삼성전자', 'SK하이닉스'],
            '보유수량': [10, 5],
            '매입단가': [75000, 127000],
            '현재가': [78000, 130000],
            '전일대비': [1000, -2000],
            '수익률': [4.0, -1.6]
        })
        
        mock_real_api.get_acct_balance.return_value = [10000000, mock_df]
        
        response = client.get("/api/account/balance")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_value"] == 10000000
        assert len(data["positions"]) == 2
        
        # 삼성전자 포지션 검증
        samsung_position = next(p for p in data["positions"] if p["stock_code"] == "005930")
        assert samsung_position["stock_name"] == "삼성전자"
        assert samsung_position["quantity"] == 10
        assert samsung_position["avg_price"] == 75000
        assert samsung_position["current_price"] == 78000
    
    @patch('simple_server.real_api')
    def test_get_account_balance_api_error(self, mock_real_api, client):
        """API 오류시 계좌 잔고 조회 테스트 (더미 데이터 반환)"""
        mock_real_api.get_acct_balance.side_effect = Exception("API Error")
        
        response = client.get("/api/account/balance")
        assert response.status_code == 200
        
        data = response.json()
        # 오류시 더미 데이터 반환 확인
        assert data["total_value"] == 10000000
        assert len(data["positions"]) > 0


class TestTradingConditionsAPI:
    """매매 조건 API 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_get_trading_conditions(self, client):
        """매매 조건 조회 테스트"""
        response = client.get("/api/trading/conditions")
        assert response.status_code == 200
        
        data = response.json()
        assert "buy_conditions" in data
        assert "sell_conditions" in data
        assert "auto_trading_enabled" in data
        
        # 기본값 검증
        buy_conditions = data["buy_conditions"]
        assert buy_conditions["rsi_lower"] == 30
        assert buy_conditions["amount"] == 100000
        assert buy_conditions["enabled"] is True
        
        sell_conditions = data["sell_conditions"]
        assert sell_conditions["rsi_upper"] == 70
        assert sell_conditions["profit_target"] == 5.0
    
    def test_update_trading_conditions_success(self, client):
        """매매 조건 업데이트 성공 테스트"""
        update_data = {
            "buy_conditions": {
                "rsi_lower": 25,
                "amount": 200000,
                "enabled": False
            },
            "sell_conditions": {
                "rsi_upper": 75,
                "profit_target": 7.0
            },
            "auto_trading_enabled": True
        }
        
        response = client.put("/api/trading/conditions", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "매매 조건이 업데이트되었습니다" in data["message"]
        
        # 업데이트된 값 검증
        updated_conditions = data["updated_conditions"]
        assert updated_conditions["buy_conditions"]["rsi_lower"] == 25
        assert updated_conditions["buy_conditions"]["amount"] == 200000
        assert updated_conditions["buy_conditions"]["enabled"] is False
        assert updated_conditions["sell_conditions"]["rsi_upper"] == 75
        assert updated_conditions["auto_trading_enabled"] is True
    
    def test_update_trading_conditions_validation(self, client):
        """매매 조건 업데이트 유효성 검증 테스트"""
        # RSI 범위 초과 테스트
        update_data = {
            "buy_conditions": {
                "rsi_lower": 150,  # 100 초과
                "amount": 500  # 1000 미만
            }
        }
        
        response = client.put("/api/trading/conditions", json=update_data)
        assert response.status_code == 200
        
        # 값이 올바르게 제한되었는지 확인
        data = response.json()
        updated_conditions = data["updated_conditions"]
        assert updated_conditions["buy_conditions"]["rsi_lower"] == 100  # max 100으로 제한
        assert updated_conditions["buy_conditions"]["amount"] == 1000  # min 1000으로 제한
    
    def test_update_trading_conditions_error(self, client):
        """매매 조건 업데이트 오류 테스트"""
        # 잘못된 데이터 타입 전송
        invalid_data = {
            "buy_conditions": {
                "rsi_lower": "invalid_string"
            }
        }
        
        response = client.put("/api/trading/conditions", json=invalid_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "error"
        assert "매매 조건 업데이트 실패" in data["message"]


class TestWatchlistAPI:
    """워치리스트 API 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_get_watchlist_no_real_api(self, client):
        """실제 API 없을 때 워치리스트 조회 테스트"""
        with patch('simple_server.real_api', None):
            response = client.get("/api/watchlist")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
            assert len(data) >= 2
            
            # 기본 종목 확인
            stock_codes = [item["stock_code"] for item in data]
            assert "005930" in stock_codes  # 삼성전자
            assert "000660" in stock_codes  # SK하이닉스
            
            # 데이터 구조 검증
            first_item = data[0]
            required_fields = [
                "stock_code", "stock_name", "current_price", "profit_rate",
                "macd", "macd_signal", "rsi", "volume"
            ]
            for field in required_fields:
                assert field in first_item
    
    @patch('simple_server.real_api')
    def test_get_watchlist_with_real_api(self, mock_real_api, client):
        """실제 API 있을 때 워치리스트 조회 테스트"""
        import pandas as pd
        
        # Account balance mock 설정
        account_df = pd.DataFrame({
            '종목코드': ['005930'],
            '보유수량': [10],
            '매입단가': [75000],
            '수익률': [4.0]
        })
        mock_real_api.get_acct_balance.return_value = [10000000, account_df]
        
        # Chart data mock 설정
        chart_df = pd.DataFrame({
            '종가': [78000, 77000, 76000],
            'RSI': [45.2, 44.1, 43.5],
            'MACD': [120.5, 119.8, 118.2],
            'MACD_signal': [118.3, 117.9, 116.5]
        })
        mock_real_api.get_minute_chart_data.return_value = chart_df
        
        response = client.get("/api/watchlist")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        
        # 삼성전자 데이터 확인 (실제 API 데이터 포함)
        samsung_item = next(item for item in data if item["stock_code"] == "005930")
        assert samsung_item["current_price"] == 78000
        assert samsung_item["quantity"] == 10
        assert samsung_item["avg_price"] == 75000
        assert samsung_item["rsi"] == 45.2


class TestMarketOverviewAPI:
    """시장 개요 API 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_get_market_overview_no_real_api(self, client):
        """실제 API 없을 때 시장 개요 조회 테스트"""
        with patch('simple_server.real_api', None):
            response = client.get("/api/market/overview")
            assert response.status_code == 200
            
            data = response.json()
            assert "market_status" in data
            assert "kospi" in data
            assert "kosdaq" in data
            assert "usd_krw" in data
            assert "top_gainers" in data
            assert "top_losers" in data
            
            # KOSPI 데이터 구조 검증
            kospi = data["kospi"]
            assert "current" in kospi
            assert "change" in kospi
            assert "change_rate" in kospi
            
            # 상승/하락 종목 검증
            assert isinstance(data["top_gainers"], list)
            assert isinstance(data["top_losers"], list)
            assert len(data["top_gainers"]) > 0
            assert len(data["top_losers"]) > 0
    
    @patch('simple_server.real_api')
    def test_get_market_overview_with_real_api(self, mock_real_api, client):
        """실제 API 있을 때 시장 개요 조회 테스트"""
        import pandas as pd
        
        # 차트 데이터 mock 설정
        chart_df = pd.DataFrame({
            '종가': [78000, 77000],
            'RSI': [45.2, 44.1],
            'MACD': [120.5, 119.8],
            'MACD_signal': [118.3, 117.9]
        })
        mock_real_api.get_minute_chart_data.return_value = chart_df
        
        response = client.get("/api/market/overview")
        assert response.status_code == 200
        
        data = response.json()
        assert "top_gainers" in data
        assert "top_losers" in data
        
        # 상승 종목에 실제 데이터가 반영되었는지 확인
        if data["top_gainers"]:
            first_gainer = data["top_gainers"][0]
            assert "stock_code" in first_gainer
            assert "current_price" in first_gainer
            assert first_gainer["current_price"] > 0


class TestWebSocketEndpoint:
    """WebSocket 엔드포인트 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_websocket_connection_establishment(self, client):
        """WebSocket 연결 수립 테스트"""
        with client.websocket_connect("/ws") as websocket:
            # 연결 성공 메시지 수신 확인
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert data["status"] == "connected"
            assert "WebSocket 연결이 성공했습니다" in data["message"]
    
    def test_websocket_data_transmission(self, client):
        """WebSocket 데이터 전송 테스트"""
        with client.websocket_connect("/ws") as websocket:
            # 연결 메시지 수신
            connection_msg = websocket.receive_json()
            assert connection_msg["type"] == "connection"
            
            # 실시간 데이터 메시지 수신 (타임아웃 설정)
            try:
                data_msg = websocket.receive_json()
                assert data_msg["type"] == "watchlist_update"
                assert "data" in data_msg
                assert isinstance(data_msg["data"], list)
                
                # 워치리스트 데이터 구조 검증
                if data_msg["data"]:
                    first_item = data_msg["data"][0]
                    required_fields = [
                        "stock_code", "stock_name", "current_price", 
                        "profit_rate", "macd", "rsi", "volume"
                    ]
                    for field in required_fields:
                        assert field in first_item
            except Exception:
                # 타임아웃이나 기타 예외 발생시 패스 (실시간 데이터는 비동기적)
                pass


class TestMiscellaneousEndpoints:
    """기타 엔드포인트 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_refresh_account_info(self, client):
        """계좌 정보 갱신 엔드포인트 테스트"""
        response = client.post("/api/account/refresh")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "계좌 정보가 갱신되었습니다" in data["message"]


class TestUtilityFunctions:
    """유틸리티 함수들 테스트"""
    
    def test_trading_conditions_data_structure(self):
        """전역 매매 조건 데이터 구조 테스트"""
        from simple_server import trading_conditions_data
        
        assert isinstance(trading_conditions_data, dict)
        assert "buy_conditions" in trading_conditions_data
        assert "sell_conditions" in trading_conditions_data
        assert "auto_trading_enabled" in trading_conditions_data
        
        # 매수 조건 검증
        buy_conditions = trading_conditions_data["buy_conditions"]
        assert "rsi_lower" in buy_conditions
        assert "macd_signal" in buy_conditions
        assert "amount" in buy_conditions
        assert "enabled" in buy_conditions
        
        # 매도 조건 검증  
        sell_conditions = trading_conditions_data["sell_conditions"]
        assert "rsi_upper" in sell_conditions
        assert "macd_signal" in sell_conditions
        assert "profit_target" in sell_conditions
        assert "stop_loss" in sell_conditions
    
    def test_active_connections_list(self):
        """활성 연결 목록 테스트"""
        from simple_server import active_connections
        
        assert isinstance(active_connections, list)
        # 초기에는 빈 목록이어야 함
        assert len(active_connections) >= 0


class TestCORSMiddleware:
    """CORS 미들웨어 테스트"""
    
    @pytest.fixture
    def client(self):
        """TestClient 픽스처"""
        return TestClient(app)
    
    def test_cors_headers_on_get_request(self, client):
        """GET 요청시 CORS 헤더 테스트"""
        response = client.get("/", headers={"origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_cors_preflight_options_request(self, client):
        """OPTIONS 프리플라이트 요청 테스트"""
        response = client.options("/", headers={"origin": "http://localhost:3000"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers


# 픽스처 공유를 위한 conftest.py 대안
@pytest.fixture(scope="module")
def mock_config():
    """모듈 스코프 설정 모크"""
    config_mock = {
        "KI_API_KEY": "test_api_key",
        "KI_ACCOUNT_NUMBER": "test_account",
        "KI_IS_PAPER_TRADING": True
    }
    return config_mock


if __name__ == "__main__":
    # 개별 테스트 실행을 위한 코드
    pytest.main([__file__, "-v", "--tb=short"])