"""
테스트 설정 및 공통 픽스처 (simple_server.py 전용)
"""

import pytest
import asyncio
import pandas as pd
import numpy as np
from typing import Generator
from unittest.mock import AsyncMock, Mock


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """이벤트 루프 픽스처"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_korea_invest_api():
    """모의 한국투자증권 API (simple_server.py용)"""
    api_mock = Mock()
    
    # get_acct_balance 메서드 mock
    sample_df = pd.DataFrame({
        '종목코드': ['005930', '000660'],
        '종목명': ['삼성전자', 'SK하이닉스'],
        '보유수량': [10, 5],
        '매입단가': [75000, 127000],
        '현재가': [78000, 130000],
        '전일대비': [1000, -2000],
        '수익률': [4.0, -1.6]
    })
    api_mock.get_acct_balance.return_value = [10000000, sample_df]
    
    # get_minute_chart_data 메서드 mock
    chart_df = pd.DataFrame({
        '종가': [78000, 77000, 76000],
        'RSI': [45.2, 44.1, 43.5],
        'MACD': [120.5, 119.8, 118.2],
        'MACD_signal': [118.3, 117.9, 116.5]
    })
    api_mock.get_minute_chart_data.return_value = chart_df
    
    return api_mock


@pytest.fixture
def sample_price_data():
    """샘플 가격 데이터 (기술적 지표 계산용)"""
    # 50개 데이터 포인트의 가격 시리즈 생성
    np.random.seed(42)  # 재현 가능한 결과를 위해
    base_price = 50000
    price_changes = np.random.normal(0, 1000, 50)
    prices = []
    
    current_price = base_price
    for change in price_changes:
        current_price += change
        current_price = max(current_price, 10000)  # 최소가 10,000원
        prices.append(current_price)
    
    return pd.Series(prices)


# 테스트 상수들
class TestConstants:
    """테스트에서 사용하는 상수들"""
    
    SAMSUNG_STOCK_CODE = "005930"
    SK_HYNIX_STOCK_CODE = "000660"
    INVALID_STOCK_CODE = "999999"
    
    # 기술적 지표 허용 오차
    TECHNICAL_INDICATOR_TOLERANCE = 0.01
    
    # 매매 조건 기본값
    DEFAULT_BUY_AMOUNT = 100000
    DEFAULT_RSI_BUY_THRESHOLD = 30
    DEFAULT_RSI_SELL_THRESHOLD = 70


@pytest.fixture
def test_constants():
    """테스트 상수 픽스처"""
    return TestConstants