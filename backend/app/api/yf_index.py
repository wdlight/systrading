"""
yfinance 기반 지수 API 엔드포인트
전 세계 주요 지수 데이터를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from loguru import logger

from app.services.yfinance_service.yf_index_service import YFinanceIndexService
from app.models.schemas import MarketOverview

router = APIRouter(prefix="/yf-index", tags=["YFinance Index"])

# 전역 서비스 인스턴스
_yf_service = None

def get_yf_index_service() -> YFinanceIndexService:
    """YFinance 지수 서비스 인스턴스 반환"""
    global _yf_service
    if _yf_service is None:
        _yf_service = YFinanceIndexService()
    return _yf_service

@router.get("/overview", response_model=MarketOverview, summary="yfinance 전체 시장 현황 조회")
async def get_yf_market_overview(
    yf_service: YFinanceIndexService = Depends(get_yf_index_service)
) -> Dict[str, Any]:
    """
    yfinance를 사용하여 전 세계 주요 지수 정보를 조회합니다.
    
    포함 지수:
    - 아시아: KOSPI, KOSDAQ, Nikkei 225, Hang Seng, Shanghai Composite
    - 유럽: FTSE 100, DAX, CAC 40
    - 아메리카: NASDAQ, DOW, S&P 500, NYSE, Russell 2000
    - 환율: USD/KRW
    
    기존 /api/stocks/overview와 동일한 형식으로 응답합니다.
    """
    try:
        logger.info("yfinance 기반 전체 시장 현황 조회 시작")
        
        # 전체 지수 데이터 조회
        indices = await yf_service.get_market_indices()
        
        # 기존 형식에 맞춰 응답 구성
        response = {
            "market_status": "open",
            # 기존 주요 지수
            "kospi": indices.get("kospi", {}),
            "kosdaq": indices.get("kosdaq", {}),
            "nasdaq": indices.get("nasdaq", {}),
            "sp500": indices.get("sp500", {}),
            "dow": indices.get("dow", {}),
            "usd_krw": indices.get("usd_krw", {}),
            
            # 추가 지수들
            "nyse": indices.get("nyse", {}),
            "russell2000": indices.get("russell2000", {}),
            "ftse": indices.get("ftse", {}),
            "dax": indices.get("dax", {}),
            "cac40": indices.get("cac40", {}),
            "nikkei225": indices.get("nikkei225", {}),
            "hangseng": indices.get("hangseng", {}),
            "shanghai": indices.get("shanghai", {}),
            
            # 향후 확장 가능한 필드들
            "top_gainers": [],
            "top_losers": []
        }
        
        logger.info(f"yfinance 기반 시장 현황 조회 완료 - {len(indices)}개 지수")
        return response
        
    except Exception as e:
        logger.error(f"yfinance 시장 현황 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"시장 현황 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/overview/region/{region}", summary="지역별 시장 현황 조회")
async def get_yf_market_overview_by_region(
    region: str,
    yf_service: YFinanceIndexService = Depends(get_yf_index_service)
) -> Dict[str, Any]:
    """
    지역별 지수 정보를 조회합니다.
    
    지원 지역:
    - asia: 아시아 지수 (KOSPI, KOSDAQ, Nikkei 225, Hang Seng, Shanghai Composite)
    - europe: 유럽 지수 (FTSE 100, DAX, CAC 40)
    - americas: 아메리카 지수 (NASDAQ, DOW, S&P 500, NYSE, Russell 2000)
    - forex: 환율 (USD/KRW)
    """
    try:
        logger.info(f"yfinance {region} 지역 시장 현황 조회 시작")
        
        # 지역별 지수 데이터 조회
        indices = await yf_service.get_market_indices_by_region(region)
        
        response = {
            "region": region,
            "market_status": "open",
            "indices": indices,
            "count": len(indices),
            "timestamp": yf_service._get_all_default_data().get("kospi", {}).get("last_updated", "")
        }
        
        logger.info(f"{region} 지역 시장 현황 조회 완료 - {len(indices)}개 지수")
        return response
        
    except ValueError as e:
        logger.warning(f"지원하지 않는 지역 요청: {region}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"{region} 지역 시장 현황 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"{region} 지역 시장 현황 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/indices", summary="지원 지수 목록 조회")
async def get_supported_indices(
    yf_service: YFinanceIndexService = Depends(get_yf_index_service)
) -> Dict[str, Any]:
    """
    yfinance에서 지원하는 모든 지수 목록을 조회합니다.
    """
    try:
        indices = yf_service.get_supported_indices()
        regions = yf_service.get_supported_regions()
        
        return {
            "total_count": len(indices),
            "indices": indices,
            "regions": regions,
            "description": "yfinance에서 지원하는 전 세계 주요 지수 목록"
        }
        
    except Exception as e:
        logger.error(f"지원 지수 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"지원 지수 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/indices/{index_name}", summary="특정 지수 정보 조회")
async def get_specific_index(
    index_name: str,
    yf_service: YFinanceIndexService = Depends(get_yf_index_service)
) -> Dict[str, Any]:
    """
    특정 지수의 상세 정보를 조회합니다.
    
    지원 지수: kospi, kosdaq, nasdaq, dow, sp500, usd_krw, nyse, russell2000, 
              ftse, dax, cac40, nikkei225, hangseng, shanghai
    """
    try:
        supported_indices = yf_service.get_supported_indices()
        
        if index_name not in supported_indices:
            raise HTTPException(
                status_code=404, 
                detail=f"지원하지 않는 지수입니다: {index_name}. 지원 지수: {list(supported_indices.keys())}"
            )
        
        logger.info(f"{index_name} 지수 정보 조회 시작")
        
        # 전체 지수 데이터에서 해당 지수만 추출
        all_indices = await yf_service.get_market_indices()
        index_data = all_indices.get(index_name, {})
        
        if not index_data:
            raise HTTPException(status_code=404, detail=f"{index_name} 지수 데이터를 찾을 수 없습니다.")
        
        response = {
            "index_name": index_name,
            "ticker": supported_indices[index_name],
            "data": index_data,
            "timestamp": index_data.get("last_updated", "")
        }
        
        logger.info(f"{index_name} 지수 정보 조회 완료")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"{index_name} 지수 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"{index_name} 지수 정보 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/health", summary="yfinance 서비스 상태 확인")
async def health_check():
    """
    yfinance 서비스 상태를 확인합니다.
    KOSPI 지수 조회를 통한 연결 테스트를 수행합니다.
    """
    try:
        yf_service = get_yf_index_service()
        
        # 간단한 테스트 조회 (KOSPI)
        test_data = await yf_service._fetch_index_data("^KS11")
        
        if test_data and test_data.get("regularMarketPrice"):
            current_price = test_data.get("regularMarketPrice", 0)
            return {
                "status": "healthy",
                "message": "yfinance 서비스 정상 동작",
                "test_index": "KOSPI (^KS11)",
                "test_price": current_price,
                "supported_indices": len(yf_service.get_supported_indices())
            }
        else:
            return {
                "status": "warning",
                "message": "yfinance 데이터 조회 실패",
                "test_index": "KOSPI (^KS11)",
                "test_price": None
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"yfinance 서비스 오류: {str(e)}",
            "test_index": "KOSPI (^KS11)",
            "test_price": None
        }

@router.get("/stats", summary="yfinance 서비스 통계")
async def get_service_stats(
    yf_service: YFinanceIndexService = Depends(get_yf_index_service)
) -> Dict[str, Any]:
    """
    yfinance 서비스의 통계 정보를 제공합니다.
    """
    try:
        indices = yf_service.get_supported_indices()
        regions = yf_service.get_supported_regions()
        
        # 캐시 정보
        cache_info = {
            "cache_duration": yf_service.cache_duration,
            "cached_items": len(yf_service.cache),
            "cache_keys": list(yf_service.cache.keys())
        }
        
        return {
            "service": "YFinance Index Service",
            "version": "1.0.0",
            "total_indices": len(indices),
            "regions": {
                name: len(indices) for name, indices in regions.items()
            },
            "cache": cache_info,
            "description": "전 세계 주요 지수 데이터를 제공하는 yfinance 기반 서비스"
        }
        
    except Exception as e:
        logger.error(f"서비스 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"서비스 통계 조회 중 오류가 발생했습니다: {str(e)}")
