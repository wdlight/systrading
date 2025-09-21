"""
WatchlistService 단위 테스트
워치리스트 관리 기능 검증
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from app.services.watchlist_service import WatchlistService
from app.models.watchlist_models import WatchlistItem, TechnicalIndicators
from tests.conftest import (
    assert_watchlist_item_valid,
    assert_api_response_success,
    TestConstants
)


class TestWatchlistService:
    """워치리스트 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_get_watchlist_empty(self, watchlist_service):
        """빈 워치리스트 조회 테스트"""
        # Given: 빈 워치리스트
        
        # When: 워치리스트 조회
        items = await watchlist_service.get_watchlist()
        
        # Then: 빈 리스트 반환
        assert isinstance(items, list)
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_get_watchlist_with_items(self, populated_watchlist_service):
        """종목이 있는 워치리스트 조회 테스트"""
        # Given: 종목이 추가된 워치리스트
        service = populated_watchlist_service
        
        # When: 워치리스트 조회
        items = await service.get_watchlist()
        
        # Then: 종목 리스트 반환
        assert isinstance(items, list)
        assert len(items) == 2
        
        # 각 아이템 검증
        for item in items:
            assert_watchlist_item_valid(item)
            assert isinstance(item, WatchlistItem)

    @pytest.mark.asyncio
    async def test_get_watchlist_item_exists(self, populated_watchlist_service, test_constants):
        """존재하는 종목 조회 테스트"""
        # Given: 종목이 추가된 워치리스트
        service = populated_watchlist_service
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # When: 특정 종목 조회
        item = await service.get_watchlist_item(stock_code)
        
        # Then: 종목 정보 반환
        assert item is not None
        assert_watchlist_item_valid(item)
        assert item.stock_code == stock_code
        assert item.current_price == 70000
        assert item.profit_rate == 5.5

    @pytest.mark.asyncio
    async def test_get_watchlist_item_not_exists(self, watchlist_service, test_constants):
        """존재하지 않는 종목 조회 테스트"""
        # Given: 빈 워치리스트
        stock_code = test_constants.INVALID_STOCK_CODE
        
        # When: 존재하지 않는 종목 조회
        item = await watchlist_service.get_watchlist_item(stock_code)
        
        # Then: None 반환
        assert item is None

    @pytest.mark.asyncio
    async def test_add_stock_success(self, watchlist_service, test_constants):
        """종목 추가 성공 테스트"""
        # Given: 빈 워치리스트와 유효한 종목 코드
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # When: 종목 추가
        result = await watchlist_service.add_stock(stock_code)
        
        # Then: 성공 응답
        assert_api_response_success(result)
        assert stock_code in watchlist_service.watchlist_df.index
        
        # 초기 데이터 확인
        row = watchlist_service.watchlist_df.loc[stock_code]
        assert row['현재가'] == 50000  # mock 데이터
        assert row['수익률'] == 0.0
        assert row['평균단가'] == 50000  # 현재가로 초기화
        assert row['보유수량'] == 0

    @pytest.mark.asyncio
    async def test_add_stock_already_exists(self, populated_watchlist_service, test_constants):
        """이미 존재하는 종목 추가 테스트"""
        # Given: 이미 종목이 있는 워치리스트
        service = populated_watchlist_service
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # When: 이미 존재하는 종목 추가 시도
        result = await service.add_stock(stock_code)
        
        # Then: 실패 응답
        assert result['success'] is False
        assert "이미 워치리스트에 있습니다" in result['message']

    @pytest.mark.asyncio
    async def test_remove_stock_success(self, populated_watchlist_service, test_constants):
        """종목 제거 성공 테스트"""
        # Given: 종목이 있는 워치리스트
        service = populated_watchlist_service
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # 종목이 존재하는지 확인
        assert stock_code in service.watchlist_df.index
        
        # When: 종목 제거
        result = await service.remove_stock(stock_code)
        
        # Then: 성공 응답 및 종목 제거 확인
        assert_api_response_success(result)
        assert stock_code not in service.watchlist_df.index
        assert stock_code not in service.price_history

    @pytest.mark.asyncio
    async def test_remove_stock_not_exists(self, watchlist_service, test_constants):
        """존재하지 않는 종목 제거 테스트"""
        # Given: 빈 워치리스트
        stock_code = test_constants.INVALID_STOCK_CODE
        
        # When: 존재하지 않는 종목 제거 시도
        result = await watchlist_service.remove_stock(stock_code)
        
        # Then: 실패 응답
        assert result['success'] is False
        assert "워치리스트에 없습니다" in result['message']

    @pytest.mark.asyncio
    async def test_get_technical_indicators_exists(self, populated_watchlist_service, test_constants):
        """기술적 지표 조회 테스트 (종목 존재)"""
        # Given: 종목이 있는 워치리스트
        service = populated_watchlist_service
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # When: 기술적 지표 조회
        indicators = await service.get_technical_indicators(stock_code)
        
        # Then: 지표 정보 반환
        assert indicators is not None
        assert isinstance(indicators, TechnicalIndicators)
        assert indicators.rsi == 65.0
        assert indicators.macd == 1.5
        assert indicators.macd_signal == 1.2
        assert indicators.timestamp is not None

    @pytest.mark.asyncio
    async def test_get_technical_indicators_not_exists(self, watchlist_service, test_constants):
        """기술적 지표 조회 테스트 (종목 없음)"""
        # Given: 빈 워치리스트
        stock_code = test_constants.INVALID_STOCK_CODE
        
        # When: 존재하지 않는 종목의 기술적 지표 조회
        indicators = await watchlist_service.get_technical_indicators(stock_code)
        
        # Then: None 반환
        assert indicators is None

    @pytest.mark.asyncio
    async def test_update_stock_data_success(self, populated_watchlist_service, test_constants):
        """주가 데이터 업데이트 성공 테스트"""
        # Given: 종목이 있는 워치리스트
        service = populated_watchlist_service
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        new_price = 75000
        
        # 초기 가격 히스토리 설정
        service.price_history[stock_code] = pd.DataFrame({
            'close': [70000, 71000, 72000],
            'timestamp': [datetime.now(), datetime.now(), datetime.now()]
        })
        
        # When: 주가 데이터 업데이트
        success = await service.update_stock_data(stock_code, new_price)
        
        # Then: 업데이트 성공
        assert success is True
        
        # 현재가 업데이트 확인
        assert service.watchlist_df.loc[stock_code, '현재가'] == new_price
        
        # 수익률 계산 확인 (평균단가 66000원 기준)
        expected_profit_rate = round((new_price - 66000) / 66000 * 100, 2)
        assert service.watchlist_df.loc[stock_code, '수익률'] == expected_profit_rate
        
        # 가격 히스토리 업데이트 확인
        assert len(service.price_history[stock_code]) == 4
        assert service.price_history[stock_code]['close'].iloc[-1] == new_price

    @pytest.mark.asyncio
    async def test_update_stock_data_not_exists(self, watchlist_service, test_constants):
        """존재하지 않는 종목 데이터 업데이트 테스트"""
        # Given: 빈 워치리스트
        stock_code = test_constants.INVALID_STOCK_CODE
        new_price = 50000
        
        # When: 존재하지 않는 종목 업데이트 시도
        success = await watchlist_service.update_stock_data(stock_code, new_price)
        
        # Then: 업데이트 실패
        assert success is False

    @pytest.mark.asyncio
    async def test_refresh_all_data_success(self, populated_watchlist_service):
        """전체 데이터 갱신 성공 테스트"""
        # Given: 종목이 있는 워치리스트
        service = populated_watchlist_service
        
        # When: 전체 데이터 갱신
        result = await service.refresh_all_data()
        
        # Then: 성공 응답
        assert result['success'] is True
        assert result['updated_count'] == 2  # 2개 종목
        assert 'last_update' in result

    @pytest.mark.asyncio
    async def test_refresh_all_data_empty(self, watchlist_service):
        """빈 워치리스트 데이터 갱신 테스트"""
        # Given: 빈 워치리스트
        
        # When: 전체 데이터 갱신
        result = await watchlist_service.refresh_all_data()
        
        # Then: 성공 응답 (갱신된 종목 없음)
        assert result['success'] is True
        assert result['updated_count'] == 0

    @pytest.mark.asyncio
    async def test_clear_watchlist_success(self, populated_watchlist_service):
        """워치리스트 초기화 성공 테스트"""
        # Given: 종목이 있는 워치리스트
        service = populated_watchlist_service
        initial_count = len(service.watchlist_df)
        
        # When: 워치리스트 초기화
        result = await service.clear_watchlist()
        
        # Then: 성공 응답 및 초기화 확인
        assert_api_response_success(result)
        assert result['removed_count'] == initial_count
        assert len(service.watchlist_df) == 0
        assert len(service.price_history) == 0

    @pytest.mark.asyncio
    async def test_get_statistics_empty(self, watchlist_service):
        """빈 워치리스트 통계 조회 테스트"""
        # Given: 빈 워치리스트
        
        # When: 통계 조회
        stats = await watchlist_service.get_statistics()
        
        # Then: 기본 통계 반환
        assert stats['total_stocks'] == 0
        assert stats['profit_stocks'] == 0
        assert stats['loss_stocks'] == 0
        assert stats['avg_profit_rate'] == 0.0
        assert stats['last_update'] is None

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(self, populated_watchlist_service):
        """데이터가 있는 워치리스트 통계 조회 테스트"""
        # Given: 종목이 있는 워치리스트 (수익: 005930, 손실: 000660)
        service = populated_watchlist_service
        
        # When: 통계 조회
        stats = await service.get_statistics()
        
        # Then: 정확한 통계 반환
        assert stats['total_stocks'] == 2
        assert stats['profit_stocks'] == 1  # 005930 (+5.5%)
        assert stats['loss_stocks'] == 1    # 000660 (-2.3%)
        assert stats['neutral_stocks'] == 0
        assert stats['avg_profit_rate'] == round((5.5 + (-2.3)) / 2, 2)  # 1.6%
        assert stats['max_profit_rate'] == 5.5
        assert stats['min_profit_rate'] == -2.3

    @pytest.mark.asyncio
    async def test_calculate_technical_indicators_sufficient_data(self, watchlist_service, test_constants):
        """충분한 데이터로 기술적 지표 계산 테스트"""
        # Given: 충분한 가격 히스토리가 있는 종목
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # 워치리스트에 종목 추가
        await watchlist_service.add_stock(stock_code)
        
        # 충분한 가격 히스토리 생성 (30개)
        prices = [50000 + i * 100 for i in range(30)]
        timestamps = [datetime.now() for _ in range(30)]
        watchlist_service.price_history[stock_code] = pd.DataFrame({
            'close': prices,
            'timestamp': timestamps
        })
        
        # When: 기술적 지표 계산
        await watchlist_service._calculate_technical_indicators(stock_code)
        
        # Then: 지표가 계산됨
        row = watchlist_service.watchlist_df.loc[stock_code]
        # 충분한 데이터로 지표가 계산되었는지 확인 (NaN이 아님)
        assert not pd.isna(row['RSI'])
        assert not pd.isna(row['MACD'])
        assert not pd.isna(row['MACD시그널'])

    @pytest.mark.asyncio
    async def test_calculate_technical_indicators_insufficient_data(self, watchlist_service, test_constants):
        """불충분한 데이터로 기술적 지표 계산 테스트"""
        # Given: 불충분한 가격 히스토리가 있는 종목
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # 워치리스트에 종목 추가
        await watchlist_service.add_stock(stock_code)
        
        # 불충분한 가격 히스토리 생성 (10개)
        prices = [50000 + i * 100 for i in range(10)]
        timestamps = [datetime.now() for _ in range(10)]
        watchlist_service.price_history[stock_code] = pd.DataFrame({
            'close': prices,
            'timestamp': timestamps
        })
        
        # When: 기술적 지표 계산
        await watchlist_service._calculate_technical_indicators(stock_code)
        
        # Then: 지표 계산이 실행되지만 결과가 없을 수 있음 (최소 20개 데이터 필요)
        # 이 경우는 에러가 발생하지 않고 조용히 리턴해야 함
        assert stock_code in watchlist_service.watchlist_df.index

    @pytest.mark.asyncio
    async def test_get_stock_price_success(self, watchlist_service):
        """주가 조회 성공 테스트"""
        # Given: 워치리스트 서비스 (mock API 응답 설정됨)
        stock_code = "005930"
        
        # When: 주가 조회
        stock_data = await watchlist_service.get_stock_price(stock_code)
        
        # Then: 주가 데이터 반환
        assert stock_data is not None
        assert stock_data.stock_code == stock_code
        assert stock_data.close_price == 50000  # mock 데이터
        assert stock_data.volume == 1000000
        assert stock_data.timestamp is not None

    @pytest.mark.asyncio
    async def test_price_history_memory_management(self, watchlist_service, test_constants):
        """가격 히스토리 메모리 관리 테스트"""
        # Given: 워치리스트에 종목 추가
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        await watchlist_service.add_stock(stock_code)
        
        # When: 250개의 가격 데이터 추가 (200개 제한 초과)
        for i in range(250):
            await watchlist_service.update_stock_data(stock_code, 50000 + i)
        
        # Then: 200개로 제한됨
        assert len(watchlist_service.price_history[stock_code]) == 200
        
        # 최신 데이터가 유지되는지 확인
        latest_price = watchlist_service.price_history[stock_code]['close'].iloc[-1]
        assert latest_price == 50000 + 249  # 마지막 가격

    @pytest.mark.asyncio
    async def test_profit_rate_calculation_with_valid_avg_price(self, watchlist_service, test_constants):
        """유효한 평균단가로 수익률 계산 테스트"""
        # Given: 종목 추가 및 평균단가 설정
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        await watchlist_service.add_stock(stock_code)
        
        # 평균단가 설정
        watchlist_service.watchlist_df.loc[stock_code, '평균단가'] = 50000
        
        # When: 가격 업데이트 (10% 상승)
        new_price = 55000
        await watchlist_service.update_stock_data(stock_code, new_price)
        
        # Then: 수익률 정확히 계산됨
        profit_rate = watchlist_service.watchlist_df.loc[stock_code, '수익률']
        expected_rate = round((55000 - 50000) / 50000 * 100, 2)  # 10.0%
        assert profit_rate == expected_rate

    @pytest.mark.asyncio
    async def test_profit_rate_calculation_with_invalid_avg_price(self, watchlist_service, test_constants):
        """무효한 평균단가로 수익률 계산 테스트"""
        # Given: 종목 추가 및 무효한 평균단가 설정
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        await watchlist_service.add_stock(stock_code)
        
        # 평균단가를 NaN으로 설정
        watchlist_service.watchlist_df.loc[stock_code, '평균단가'] = np.nan
        
        # When: 가격 업데이트
        new_price = 55000
        await watchlist_service.update_stock_data(stock_code, new_price)
        
        # Then: 수익률 계산되지 않음 (기존 값 유지)
        profit_rate = watchlist_service.watchlist_df.loc[stock_code, '수익률']
        assert profit_rate == 0.0  # 초기값 유지

    @pytest.mark.asyncio 
    async def test_create_watchlist_item_with_valid_data(self, populated_watchlist_service, test_constants):
        """유효한 데이터로 워치리스트 아이템 생성 테스트"""
        # Given: 종목이 있는 워치리스트
        service = populated_watchlist_service
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        
        # When: 워치리스트 아이템 생성
        item = await service._create_watchlist_item(stock_code)
        
        # Then: 유효한 아이템 반환
        assert_watchlist_item_valid(item)
        assert item.stock_code == stock_code
        assert item.current_price == 70000
        assert item.profit_rate == 5.5
        assert item.avg_price == 66000
        assert item.quantity == 10
        assert item.macd == 1.5
        assert item.macd_signal == 1.2
        assert item.rsi == 65.0
        assert item.trailing_stop_active is False

    @pytest.mark.asyncio
    async def test_create_watchlist_item_with_none_values(self, watchlist_service, test_constants):
        """None 값들이 있는 데이터로 워치리스트 아이템 생성 테스트"""
        # Given: None 값들이 포함된 종목 데이터
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        await watchlist_service.add_stock(stock_code)
        
        # 일부 값을 None으로 설정
        watchlist_service.watchlist_df.loc[stock_code, '평균단가'] = None
        watchlist_service.watchlist_df.loc[stock_code, '트레일링스탑발동후고가'] = None
        
        # When: 워치리스트 아이템 생성
        item = await watchlist_service._create_watchlist_item(stock_code)
        
        # Then: None 값들이 올바르게 처리됨
        assert item is not None
        assert item.avg_price is None
        assert item.trailing_stop_high is None