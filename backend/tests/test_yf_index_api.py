"""
yfinance 기반 지수 API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

class TestYFinanceIndexAPI:
    """YFinance 지수 API 테스트"""
    
    @pytest.fixture
    def client(self):
        """테스트 클라이언트"""
        return TestClient(app)
    
    def test_get_yf_market_overview_success(self, client):
        """yfinance 전체 시장 현황 조회 성공 테스트"""
        response = client.get("/api/yf-index/overview")
        
        assert response.status_code == 200
        data = response.json()
        
        # 필수 필드 존재 확인
        required_fields = ["market_status", "kospi", "kosdaq", "nasdaq", "dow", "sp500", "usd_krw",
                          "nyse", "russell2000", "ftse", "dax", "cac40", "nikkei225", "hangseng", "shanghai"]
        for field in required_fields:
            assert field in data
        
        # 지수 데이터 구조 확인
        for index_name in ["kospi", "kosdaq", "nasdaq", "dow", "sp500", "usd_krw",
                          "nyse", "russell2000", "ftse", "dax", "cac40", "nikkei225", "hangseng", "shanghai"]:
            index_data = data[index_name]
            assert "current" in index_data
            assert "change" in index_data
            assert "change_rate" in index_data
            assert "code" in index_data
            assert "market" in index_data
            assert "ticker" in index_data
            assert "last_updated" in index_data
            assert isinstance(index_data["current"], (int, float))
    
    def test_get_yf_market_overview_response_format(self, client):
        """응답 형식이 기존 API와 호환되는지 확인"""
        response = client.get("/api/yf-index/overview")
        data = response.json()
        
        # 기존 형식과 동일한 구조인지 확인
        assert data["market_status"] == "open"
        
        # KOSPI 데이터 예시 검증
        kospi = data["kospi"]
        assert "code" in kospi
        assert "market" in kospi
        assert "current" in kospi
        assert "change" in kospi
        assert "change_rate" in kospi
        assert kospi["code"] == "0001"
        assert kospi["market"] == "U"
    
    def test_get_yf_market_overview_by_region_asia(self, client):
        """아시아 지역 지수 조회 테스트"""
        response = client.get("/api/yf-index/overview/region/asia")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["region"] == "asia"
        assert data["market_status"] == "open"
        assert "indices" in data
        assert "count" in data
        assert data["count"] == 5
        
        # 아시아 지수 확인
        indices = data["indices"]
        assert "kospi" in indices
        assert "kosdaq" in indices
        assert "nikkei225" in indices
        assert "hangseng" in indices
        assert "shanghai" in indices
        
        # 각 지수 데이터 구조 확인
        for index_name in ["kospi", "kosdaq", "nikkei225", "hangseng", "shanghai"]:
            index_data = indices[index_name]
            assert "current" in index_data
            assert "change" in index_data
            assert "change_rate" in index_data
    
    def test_get_yf_market_overview_by_region_europe(self, client):
        """유럽 지역 지수 조회 테스트"""
        response = client.get("/api/yf-index/overview/region/europe")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["region"] == "europe"
        assert data["count"] == 3
        
        # 유럽 지수 확인
        indices = data["indices"]
        assert "ftse" in indices
        assert "dax" in indices
        assert "cac40" in indices
    
    def test_get_yf_market_overview_by_region_americas(self, client):
        """아메리카 지역 지수 조회 테스트"""
        response = client.get("/api/yf-index/overview/region/americas")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["region"] == "americas"
        assert data["count"] == 5
        
        # 아메리카 지수 확인
        indices = data["indices"]
        assert "nasdaq" in indices
        assert "dow" in indices
        assert "sp500" in indices
        assert "nyse" in indices
        assert "russell2000" in indices
    
    def test_get_yf_market_overview_by_region_forex(self, client):
        """환율 지수 조회 테스트"""
        response = client.get("/api/yf-index/overview/region/forex")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["region"] == "forex"
        assert data["count"] == 1
        
        # 환율 지수 확인
        indices = data["indices"]
        assert "usd_krw" in indices
    
    def test_get_yf_market_overview_by_region_invalid(self, client):
        """잘못된 지역 요청 테스트"""
        response = client.get("/api/yf-index/overview/region/invalid_region")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "지원하지 않는 지역" in data["detail"]
    
    def test_get_supported_indices(self, client):
        """지원 지수 목록 조회 테스트"""
        response = client.get("/api/yf-index/indices")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_count" in data
        assert "indices" in data
        assert "regions" in data
        assert "description" in data
        
        assert data["total_count"] == 14
        
        # 지수 목록 확인
        indices = data["indices"]
        assert "kospi" in indices
        assert "nasdaq" in indices
        assert "dax" in indices
        assert indices["kospi"] == "^KS11"
        assert indices["nasdaq"] == "^IXIC"
        assert indices["dax"] == "^GDAXI"
        
        # 지역별 지수 확인
        regions = data["regions"]
        assert "asia" in regions
        assert "europe" in regions
        assert "americas" in regions
        assert "forex" in regions
    
    def test_get_specific_index_kospi(self, client):
        """특정 지수(KOSPI) 조회 테스트"""
        response = client.get("/api/yf-index/indices/kospi")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["index_name"] == "kospi"
        assert data["ticker"] == "^KS11"
        assert "data" in data
        assert "timestamp" in data
        
        # KOSPI 데이터 확인
        index_data = data["data"]
        assert "current" in index_data
        assert "change" in index_data
        assert "change_rate" in index_data
        assert "code" in index_data
        assert "market" in index_data
        assert index_data["code"] == "0001"
        assert index_data["market"] == "U"
    
    def test_get_specific_index_nasdaq(self, client):
        """특정 지수(NASDAQ) 조회 테스트"""
        response = client.get("/api/yf-index/indices/nasdaq")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["index_name"] == "nasdaq"
        assert data["ticker"] == "^IXIC"
        
        # NASDAQ 데이터 확인
        index_data = data["data"]
        assert index_data["code"] == "NDX"
        assert index_data["market"] == "N"
    
    def test_get_specific_index_dax(self, client):
        """특정 지수(DAX) 조회 테스트"""
        response = client.get("/api/yf-index/indices/dax")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["index_name"] == "dax"
        assert data["ticker"] == "^GDAXI"
        
        # DAX 데이터 확인
        index_data = data["data"]
        assert index_data["code"] == "GDAXI"
        assert index_data["market"] == "E"
    
    def test_get_specific_index_invalid(self, client):
        """잘못된 지수 요청 테스트"""
        response = client.get("/api/yf-index/indices/invalid_index")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "지원하지 않는 지수" in data["detail"]
    
    def test_health_check(self, client):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get("/api/yf-index/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "message" in data
        assert "test_index" in data
        assert "test_price" in data
        assert data["status"] in ["healthy", "warning", "error"]
        assert data["test_index"] == "KOSPI (^KS11)"
    
    def test_service_stats(self, client):
        """서비스 통계 엔드포인트 테스트"""
        response = client.get("/api/yf-index/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "total_indices" in data
        assert "regions" in data
        assert "cache" in data
        assert "description" in data
        
        assert data["service"] == "YFinance Index Service"
        assert data["version"] == "1.0.0"
        assert data["total_indices"] == 14
        
        # 지역별 지수 개수 확인
        regions = data["regions"]
        assert regions["asia"] == 5
        assert regions["europe"] == 3
        assert regions["americas"] == 5
        assert regions["forex"] == 1
        
        # 캐시 정보 확인
        cache = data["cache"]
        assert "cache_duration" in cache
        assert "cached_items" in cache
        assert "cache_keys" in cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
