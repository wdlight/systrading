"""
yfinance 기반 지수 서비스 테스트
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.services.yfinance_service.yf_index_service import YFinanceIndexService

class TestYFinanceIndexService:
    """YFinance 지수 서비스 테스트"""
    
    @pytest.fixture
    def yf_service(self):
        """테스트용 서비스 인스턴스"""
        return YFinanceIndexService()
    
    def test_service_initialization(self, yf_service):
        """서비스 초기화 테스트"""
        assert yf_service is not None
        assert len(yf_service.get_supported_indices()) == 14
        assert "kospi" in yf_service.get_supported_indices()
        assert "nasdaq" in yf_service.get_supported_indices()
        assert "dax" in yf_service.get_supported_indices()
    
    def test_supported_indices(self, yf_service):
        """지원 지수 목록 테스트"""
        indices = yf_service.get_supported_indices()
        
        # 기존 지수들
        assert indices["kospi"] == "^KS11"
        assert indices["kosdaq"] == "^KQ11"
        assert indices["nasdaq"] == "^IXIC"
        assert indices["dow"] == "^DJI"
        assert indices["sp500"] == "^GSPC"
        assert indices["usd_krw"] == "USDKRW=X"
        
        # 추가 지수들
        assert indices["nyse"] == "^NYA"
        assert indices["russell2000"] == "^RUT"
        assert indices["ftse"] == "^FTSE"
        assert indices["dax"] == "^GDAXI"
        assert indices["cac40"] == "^FCHI"
        assert indices["nikkei225"] == "^N225"
        assert indices["hangseng"] == "^HSI"
        assert indices["shanghai"] == "000001.SS"
    
    def test_supported_regions(self, yf_service):
        """지역별 지수 목록 테스트"""
        regions = yf_service.get_supported_regions()
        
        assert "asia" in regions
        assert "europe" in regions
        assert "americas" in regions
        assert "forex" in regions
        
        # 아시아 지수
        asia_indices = regions["asia"]
        assert "kospi" in asia_indices
        assert "kosdaq" in asia_indices
        assert "nikkei225" in asia_indices
        assert "hangseng" in asia_indices
        assert "shanghai" in asia_indices
        
        # 유럽 지수
        europe_indices = regions["europe"]
        assert "ftse" in europe_indices
        assert "dax" in europe_indices
        assert "cac40" in europe_indices
        
        # 아메리카 지수
        americas_indices = regions["americas"]
        assert "nasdaq" in americas_indices
        assert "dow" in americas_indices
        assert "sp500" in americas_indices
        assert "nyse" in americas_indices
        assert "russell2000" in americas_indices
        
        # 환율
        forex_indices = regions["forex"]
        assert "usd_krw" in forex_indices
    
    @pytest.mark.asyncio
    async def test_get_market_indices_success(self, yf_service):
        """정상적인 지수 데이터 조회 테스트"""
        # Mock 데이터 설정
        mock_data = {
            "regularMarketPrice": 3632.61,
            "previousClose": 3600.00
        }
        
        with patch.object(yf_service, '_fetch_index_data', return_value=mock_data):
            result = await yf_service.get_market_indices()
            
            # 결과 검증
            assert len(result) == 14
            
            # 모든 지수가 포함되어 있는지 확인
            expected_indices = ["kospi", "kosdaq", "nasdaq", "dow", "sp500", "usd_krw",
                              "nyse", "russell2000", "ftse", "dax", "cac40", "nikkei225", 
                              "hangseng", "shanghai"]
            for index_name in expected_indices:
                assert index_name in result
                assert result[index_name]["current"] == 3632.61
                assert result[index_name]["change"] == 32.61
                assert abs(result[index_name]["change_rate"] - 0.91) < 0.01
    
    @pytest.mark.asyncio
    async def test_get_market_indices_failure(self, yf_service):
        """API 실패 시 기본값 반환 테스트"""
        with patch.object(yf_service, '_fetch_index_data', return_value=None):
            result = await yf_service.get_market_indices()
            
            # 모든 지수가 기본값으로 반환되는지 확인
            assert len(result) == 14
            for index_name, data in result.items():
                assert data["current"] == 0.0
                assert data["change"] == 0.0
                assert data["change_rate"] == 0.0
                assert "error" in data
    
    @pytest.mark.asyncio
    async def test_get_market_indices_by_region(self, yf_service):
        """지역별 지수 데이터 조회 테스트"""
        # Mock 데이터 설정
        mock_data = {
            "regularMarketPrice": 1000.0,
            "previousClose": 950.0
        }
        
        with patch.object(yf_service, '_fetch_index_data', return_value=mock_data):
            # 아시아 지수 테스트
            asia_result = await yf_service.get_market_indices_by_region("asia")
            assert len(asia_result) == 5
            assert "kospi" in asia_result
            assert "kosdaq" in asia_result
            assert "nikkei225" in asia_result
            assert "hangseng" in asia_result
            assert "shanghai" in asia_result
            
            # 유럽 지수 테스트
            europe_result = await yf_service.get_market_indices_by_region("europe")
            assert len(europe_result) == 3
            assert "ftse" in europe_result
            assert "dax" in europe_result
            assert "cac40" in europe_result
            
            # 아메리카 지수 테스트
            americas_result = await yf_service.get_market_indices_by_region("americas")
            assert len(americas_result) == 5
            assert "nasdaq" in americas_result
            assert "dow" in americas_result
            assert "sp500" in americas_result
            assert "nyse" in americas_result
            assert "russell2000" in americas_result
    
    @pytest.mark.asyncio
    async def test_get_market_indices_by_region_invalid(self, yf_service):
        """잘못된 지역 요청 테스트"""
        with pytest.raises(ValueError):
            await yf_service.get_market_indices_by_region("invalid_region")
    
    def test_format_index_data(self, yf_service):
        """데이터 형식 변환 테스트"""
        mock_data = {
            "regularMarketPrice": 1000.0,
            "previousClose": 950.0
        }
        
        result = yf_service._format_index_data("kospi", "^KS11", mock_data)
        
        assert result["current"] == 1000.0
        assert result["change"] == 50.0
        assert abs(result["change_rate"] - 5.26) < 0.01
        assert result["code"] == "0001"
        assert result["market"] == "U"
        assert result["ticker"] == "^KS11"
        assert "last_updated" in result
    
    def test_index_code_mapping(self, yf_service):
        """지수 코드 매핑 테스트"""
        # 기존 지수
        assert yf_service._get_index_code("kospi") == "0001"
        assert yf_service._get_index_code("kosdaq") == "1001"
        assert yf_service._get_index_code("nasdaq") == "NDX"
        assert yf_service._get_index_code("dow") == "DJI"
        assert yf_service._get_index_code("sp500") == "US500"
        assert yf_service._get_index_code("usd_krw") == "USDKRW"
        
        # 추가 지수
        assert yf_service._get_index_code("nyse") == "NYA"
        assert yf_service._get_index_code("russell2000") == "RUT"
        assert yf_service._get_index_code("ftse") == "FTSE"
        assert yf_service._get_index_code("dax") == "GDAXI"
        assert yf_service._get_index_code("cac40") == "FCHI"
        assert yf_service._get_index_code("nikkei225") == "N225"
        assert yf_service._get_index_code("hangseng") == "HSI"
        assert yf_service._get_index_code("shanghai") == "SSEC"
    
    def test_market_code_mapping(self, yf_service):
        """시장 코드 매핑 테스트"""
        # 기존 지수
        assert yf_service._get_market_code("kospi") == "U"
        assert yf_service._get_market_code("kosdaq") == "K"
        assert yf_service._get_market_code("nasdaq") == "N"
        assert yf_service._get_market_code("dow") == "N"
        assert yf_service._get_market_code("sp500") == "N"
        assert yf_service._get_market_code("usd_krw") == "X"
        
        # 추가 지수
        assert yf_service._get_market_code("nyse") == "N"          # 미국
        assert yf_service._get_market_code("russell2000") == "N"   # 미국
        assert yf_service._get_market_code("ftse") == "E"          # 유럽
        assert yf_service._get_market_code("dax") == "E"           # 유럽
        assert yf_service._get_market_code("cac40") == "E"         # 유럽
        assert yf_service._get_market_code("nikkei225") == "A"     # 아시아
        assert yf_service._get_market_code("hangseng") == "A"      # 아시아
        assert yf_service._get_market_code("shanghai") == "A"      # 아시아

    @pytest.mark.asyncio
    async def test_get_market_indices_real_fetch(self, yf_service, request):
        """실제 yfinance 데이터를 조회해 값을 출력한다."""
        try:
            result = await yf_service.get_market_indices()
        except Exception as exc:
            pytest.skip(f"실제 데이터 조회 중 예외 발생: {exc}")

        assert isinstance(result, dict)

        terminal_reporter = request.config.pluginmanager.get_plugin("terminalreporter")

        def emit(line: str) -> None:
            """pytest 캡처와 무관하게 터미널에 출력"""
            if terminal_reporter is not None:
                terminal_reporter.write_line(line)
            else:
                print(line)

        for index_name, data in result.items():
            emit(
                f"[REAL] {index_name}: current={data.get('current')}, "
                f"change={data.get('change')}, change_rate={data.get('change_rate')}, "
                f"ticker={data.get('ticker')}, error={data.get('error')}"
            )

    def test_get_default_data(self, yf_service):
        """기본값 데이터 테스트"""
        default_data = yf_service._get_default_data("kospi", "^KS11")

        assert default_data["code"] == "0001"
        assert default_data["market"] == "U"
        assert default_data["current"] == 0.0
        assert default_data["change"] == 0.0
        assert default_data["change_rate"] == 0.0
        assert default_data["ticker"] == "^KS11"
        assert "last_updated" in default_data
        assert "error" in default_data
    
    def test_get_all_default_data(self, yf_service):
        """모든 기본값 데이터 테스트"""
        all_default_data = yf_service._get_all_default_data()
        
        assert len(all_default_data) == 14
        
        for index_name, data in all_default_data.items():
            assert data["current"] == 0.0
            assert data["change"] == 0.0
            assert data["change_rate"] == 0.0
            assert "error" in data
            assert "last_updated" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
