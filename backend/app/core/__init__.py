"""
Core 패키지
핵심 설정, 의존성, API 서비스 등을 정의
"""

from .config import get_settings, Settings
from .dependencies import (
    get_korea_invest_service,
    get_account_service,
    get_trading_service,
    get_watchlist_service
)
from .korea_invest import KoreaInvestAPIService

__all__ = [
    "get_settings",
    "Settings",
    "get_korea_invest_service",
    "get_account_service", 
    "get_trading_service",
    "get_watchlist_service",
    "KoreaInvestAPIService"
]