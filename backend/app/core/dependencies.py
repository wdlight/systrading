"""
FastAPI 의존성 주입
서비스 인스턴스들을 관리하고 주입
"""

from functools import lru_cache
from typing import Generator

from app.core.config import get_settings
from app.core.korea_invest import KoreaInvestAPIService

# 전역 서비스 인스턴스들
_korea_invest_service = None
_account_service = None
_trading_service = None
_watchlist_service = None

@lru_cache()
def get_korea_invest_service() -> KoreaInvestAPIService:
    """한국투자증권 API 서비스 인스턴스 반환"""
    global _korea_invest_service
    if _korea_invest_service is None:
        settings = get_settings()
        _korea_invest_service = KoreaInvestAPIService(settings)
    return _korea_invest_service

def get_account_service():
    """계좌 서비스 인스턴스 반환"""
    global _account_service
    if _account_service is None:
        from app.services.account_service import AccountService
        korea_invest_service = get_korea_invest_service()
        _account_service = AccountService(korea_invest_service)
    return _account_service

def get_trading_service():
    """매매 서비스 인스턴스 반환"""
    global _trading_service
    if _trading_service is None:
        from app.services.trading_service import TradingService
        korea_invest_service = get_korea_invest_service()
        _trading_service = TradingService(korea_invest_service)
    return _trading_service

def get_watchlist_service():
    """워치리스트 서비스 인스턴스 반환"""
    global _watchlist_service
    if _watchlist_service is None:
        from app.services.watchlist_service import WatchlistService
        korea_invest_service = get_korea_invest_service()
        _watchlist_service = WatchlistService(korea_invest_service)
    return _watchlist_service

def reset_services():
    """모든 서비스 인스턴스 재설정 (테스트용)"""
    global _korea_invest_service, _account_service, _trading_service, _watchlist_service
    _korea_invest_service = None
    _account_service = None
    _trading_service = None
    _watchlist_service = None
    
    # 캐시 초기화
    get_korea_invest_service.cache_clear()