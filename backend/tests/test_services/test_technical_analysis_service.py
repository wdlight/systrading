"""
TechnicalAnalysisService 단위 테스트
PyQt5의 기술적 지표 계산 로직 검증
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

from app.services.technical_analysis_service import TechnicalAnalysisService
from tests.conftest import (
    assert_technical_indicators_valid, 
    create_test_analysis_result,
    TestConstants
)


class TestTechnicalAnalysisService:
    """기술적 분석 서비스 테스트"""

    def test_calculate_macd_with_sufficient_data(self, sample_price_data):
        """충분한 데이터로 MACD 계산 테스트"""
        # Given: 50개의 가격 데이터
        prices = sample_price_data
        
        # When: MACD 계산 (PyQt5 파라미터)
        macd, macd_signal = TechnicalAnalysisService.calculate_macd(
            prices, 
            fast_period=TestConstants.MACD_FAST_PERIOD,
            slow_period=TestConstants.MACD_SLOW_PERIOD,
            signal_period=TestConstants.MACD_SIGNAL_PERIOD
        )
        
        # Then: 유효한 결과 반환
        assert not np.isnan(macd), "MACD should not be NaN with sufficient data"
        assert not np.isnan(macd_signal), "MACD signal should not be NaN with sufficient data"
        assert isinstance(macd, float), "MACD should be float type"
        assert isinstance(macd_signal, float), "MACD signal should be float type"

    def test_calculate_macd_with_insufficient_data(self):
        """불충분한 데이터로 MACD 계산 테스트"""
        # Given: 10개의 가격 데이터 (18기간보다 작음)
        prices = pd.Series([50000, 51000, 49000, 52000, 48000, 53000, 47000, 54000, 46000, 55000])
        
        # When: MACD 계산
        macd, macd_signal = TechnicalAnalysisService.calculate_macd(prices)
        
        # Then: NaN 반환
        assert np.isnan(macd), "MACD should be NaN with insufficient data"
        assert np.isnan(macd_signal), "MACD signal should be NaN with insufficient data"

    def test_calculate_rsi_with_sufficient_data(self, sample_price_data, skip_talib_tests):
        """충분한 데이터로 RSI 계산 테스트"""
        # Given: 50개의 가격 데이터
        prices = sample_price_data
        
        # When: RSI 계산
        rsi = TechnicalAnalysisService.calculate_rsi(prices, TestConstants.RSI_PERIOD)
        
        # Then: 유효한 RSI 값 (0-100 범위)
        assert not np.isnan(rsi), "RSI should not be NaN with sufficient data"
        assert 0 <= rsi <= 100, f"RSI should be between 0-100, got {rsi}"
        assert isinstance(rsi, float), "RSI should be float type"

    def test_calculate_rsi_with_insufficient_data(self, skip_talib_tests):
        """불충분한 데이터로 RSI 계산 테스트"""
        # Given: 10개의 가격 데이터 (14기간보다 작음)
        prices = pd.Series([50000, 51000, 49000, 52000, 48000, 53000, 47000, 54000, 46000, 55000])
        
        # When: RSI 계산
        rsi = TechnicalAnalysisService.calculate_rsi(prices)
        
        # Then: NaN 반환
        assert np.isnan(rsi), "RSI should be NaN with insufficient data"

    def test_calculate_all_indicators_with_valid_data(self, sample_minute_data):
        """유효한 1분봉 데이터로 모든 지표 계산 테스트"""
        # Given: 50개의 1분봉 데이터
        minute_data = sample_minute_data
        
        # When: 모든 기술적 지표 계산
        indicators = TechnicalAnalysisService.calculate_all_indicators(minute_data)
        
        # Then: 모든 지표가 계산됨
        assert_technical_indicators_valid(indicators)
        assert not np.isnan(indicators['macd']), "MACD should be calculated"
        assert not np.isnan(indicators['macd_signal']), "MACD signal should be calculated"
        assert not np.isnan(indicators['rsi']), "RSI should be calculated"

    def test_calculate_all_indicators_with_empty_data(self):
        """빈 데이터프레임으로 지표 계산 테스트"""
        # Given: 빈 데이터프레임
        minute_data = pd.DataFrame()
        
        # When: 모든 기술적 지표 계산
        indicators = TechnicalAnalysisService.calculate_all_indicators(minute_data)
        
        # Then: NaN 반환
        assert np.isnan(indicators['macd']), "MACD should be NaN with empty data"
        assert np.isnan(indicators['macd_signal']), "MACD signal should be NaN with empty data"
        assert np.isnan(indicators['rsi']), "RSI should be NaN with empty data"

    def test_calculate_all_indicators_with_none_data(self):
        """None 데이터로 지표 계산 테스트"""
        # Given: None 데이터
        minute_data = None
        
        # When: 모든 기술적 지표 계산
        indicators = TechnicalAnalysisService.calculate_all_indicators(minute_data)
        
        # Then: NaN 반환
        assert np.isnan(indicators['macd']), "MACD should be NaN with None data"
        assert np.isnan(indicators['macd_signal']), "MACD signal should be NaN with None data"
        assert np.isnan(indicators['rsi']), "RSI should be NaN with None data"

    def test_analyze_minute_data_success(self, sample_minute_data, test_constants):
        """1분봉 데이터 분석 성공 테스트"""
        # Given: 유효한 1분봉 데이터
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        minute_data = sample_minute_data
        
        # When: 1분봉 데이터 분석
        result = TechnicalAnalysisService.analyze_minute_data(stock_code, minute_data)
        
        # Then: 분석 결과 반환
        assert result is not None
        assert result['stock_code'] == stock_code
        assert 'current_price' in result
        assert 'current' in result
        assert 'previous' in result
        assert 'timestamp' in result
        
        # 현재 지표 검증
        current = result['current']
        assert 'macd' in current
        assert 'macd_signal' in current
        assert 'rsi' in current

    def test_analyze_minute_data_with_empty_data(self, test_constants):
        """빈 1분봉 데이터 분석 테스트"""
        # Given: 빈 데이터프레임
        stock_code = test_constants.SAMSUNG_STOCK_CODE
        minute_data = pd.DataFrame()
        
        # When: 1분봉 데이터 분석
        result = TechnicalAnalysisService.analyze_minute_data(stock_code, minute_data)
        
        # Then: 빈 결과 반환
        assert result == {}

    def test_check_macd_condition_upward_cross(self):
        """MACD 상향돌파 조건 테스트"""
        # Given: MACD 상향돌파 상황
        current_macd = 1.5
        current_signal = 1.2
        prev_macd = 0.8
        prev_signal = 1.0
        
        # When: 상향돌파 조건 체크
        result = TechnicalAnalysisService.check_macd_condition(
            current_macd, current_signal, prev_macd, prev_signal, "상향돌파"
        )
        
        # Then: True 반환 (현재: MACD >= 시그널, 이전: MACD < 시그널)
        assert result is True

    def test_check_macd_condition_downward_cross(self):
        """MACD 하향돌파 조건 테스트"""
        # Given: MACD 하향돌파 상황
        current_macd = 0.8
        current_signal = 1.0
        prev_macd = 1.5
        prev_signal = 1.2
        
        # When: 하향돌파 조건 체크
        result = TechnicalAnalysisService.check_macd_condition(
            current_macd, current_signal, prev_macd, prev_signal, "하향돌파"
        )
        
        # Then: True 반환 (현재: MACD <= 시그널, 이전: MACD > 시그널)
        assert result is True

    def test_check_macd_condition_above(self):
        """MACD 이상 조건 테스트"""
        # Given: MACD >= 시그널 상황
        current_macd = 1.5
        current_signal = 1.2
        prev_macd = 1.0
        prev_signal = 1.3
        
        # When: 이상 조건 체크
        result = TechnicalAnalysisService.check_macd_condition(
            current_macd, current_signal, prev_macd, prev_signal, "이상"
        )
        
        # Then: True 반환
        assert result is True

    def test_check_macd_condition_below(self):
        """MACD 이하 조건 테스트"""
        # Given: MACD <= 시그널 상황
        current_macd = 1.0
        current_signal = 1.2
        prev_macd = 1.5
        prev_signal = 1.1
        
        # When: 이하 조건 체크
        result = TechnicalAnalysisService.check_macd_condition(
            current_macd, current_signal, prev_macd, prev_signal, "이하"
        )
        
        # Then: True 반환
        assert result is True

    def test_check_macd_condition_with_nan_values(self):
        """NaN 값으로 MACD 조건 테스트"""
        # Given: NaN 값들
        current_macd = np.nan
        current_signal = 1.2
        prev_macd = 1.0
        prev_signal = 1.3
        
        # When: 조건 체크
        result = TechnicalAnalysisService.check_macd_condition(
            current_macd, current_signal, prev_macd, prev_signal, "상향돌파"
        )
        
        # Then: False 반환
        assert result is False

    def test_check_rsi_condition_upward_cross(self):
        """RSI 상향돌파 조건 테스트"""
        # Given: RSI 상향돌파 상황 (30 기준선)
        current_rsi = 35.0
        prev_rsi = 28.0
        rsi_value = 30.0
        
        # When: 상향돌파 조건 체크
        result = TechnicalAnalysisService.check_rsi_condition(
            current_rsi, prev_rsi, rsi_value, "상향돌파"
        )
        
        # Then: True 반환
        assert result is True

    def test_check_rsi_condition_downward_cross(self):
        """RSI 하향돌파 조건 테스트"""
        # Given: RSI 하향돌파 상황 (70 기준선)
        current_rsi = 65.0
        prev_rsi = 75.0
        rsi_value = 70.0
        
        # When: 하향돌파 조건 체크
        result = TechnicalAnalysisService.check_rsi_condition(
            current_rsi, prev_rsi, rsi_value, "하향돌파"
        )
        
        # Then: True 반환
        assert result is True

    def test_check_rsi_condition_above(self):
        """RSI 이상 조건 테스트"""
        # Given: RSI >= 기준값 상황
        current_rsi = 35.0
        prev_rsi = 25.0
        rsi_value = 30.0
        
        # When: 이상 조건 체크
        result = TechnicalAnalysisService.check_rsi_condition(
            current_rsi, prev_rsi, rsi_value, "이상"
        )
        
        # Then: True 반환
        assert result is True

    def test_check_rsi_condition_below(self):
        """RSI 이하 조건 테스트"""
        # Given: RSI <= 기준값 상황
        current_rsi = 65.0
        prev_rsi = 75.0
        rsi_value = 70.0
        
        # When: 이하 조건 체크
        result = TechnicalAnalysisService.check_rsi_condition(
            current_rsi, prev_rsi, rsi_value, "이하"
        )
        
        # Then: True 반환
        assert result is True

    def test_check_rsi_condition_with_nan_values(self):
        """NaN 값으로 RSI 조건 테스트"""
        # Given: NaN RSI 값
        current_rsi = np.nan
        prev_rsi = 25.0
        rsi_value = 30.0
        
        # When: 조건 체크
        result = TechnicalAnalysisService.check_rsi_condition(
            current_rsi, prev_rsi, rsi_value, "상향돌파"
        )
        
        # Then: False 반환
        assert result is False

    def test_get_trading_signals_buy_signal(self):
        """매수 신호 생성 테스트"""
        # Given: 매수 조건을 만족하는 분석 결과
        analysis_result = create_test_analysis_result()
        buy_conditions = {
            'macd_type': '상향돌파',
            'rsi_value': 30,
            'rsi_type': '이상'
        }
        sell_conditions = {
            'macd_type': '하향돌파',
            'rsi_value': 70,
            'rsi_type': '이하'
        }
        
        # When: 매매 신호 분석
        signals = TechnicalAnalysisService.get_trading_signals(
            analysis_result, buy_conditions, sell_conditions
        )
        
        # Then: 매수 신호 확인
        assert 'buy_signal' in signals
        assert 'sell_signal' in signals
        assert 'buy_macd' in signals
        assert 'buy_rsi' in signals
        assert 'sell_macd' in signals
        assert 'sell_rsi' in signals

    def test_get_trading_signals_with_empty_analysis(self):
        """빈 분석 결과로 매매 신호 테스트"""
        # Given: 빈 분석 결과
        analysis_result = {}
        buy_conditions = {'macd_type': '상향돌파', 'rsi_value': 30, 'rsi_type': '이상'}
        sell_conditions = {'macd_type': '하향돌파', 'rsi_value': 70, 'rsi_type': '이하'}
        
        # When: 매매 신호 분석
        signals = TechnicalAnalysisService.get_trading_signals(
            analysis_result, buy_conditions, sell_conditions
        )
        
        # Then: False 신호 반환
        assert signals['buy_signal'] is False
        assert signals['sell_signal'] is False

    def test_format_technical_indicators(self):
        """기술적 지표 포맷 테스트"""
        # Given: 기술적 지표 값들
        macd = 1.5
        macd_signal = 1.2
        rsi = 65.0
        
        # When: 기술적 지표 포맷
        indicators = TechnicalAnalysisService.format_technical_indicators(macd, macd_signal, rsi)
        
        # Then: TechnicalIndicators 모델 반환
        assert indicators.macd == macd
        assert indicators.macd_signal == macd_signal
        assert indicators.rsi == rsi
        assert indicators.timestamp is not None

    def test_format_technical_indicators_with_nan(self):
        """NaN 값으로 기술적 지표 포맷 테스트"""
        # Given: NaN 값들
        macd = np.nan
        macd_signal = np.nan
        rsi = np.nan
        
        # When: 기술적 지표 포맷
        indicators = TechnicalAnalysisService.format_technical_indicators(macd, macd_signal, rsi)
        
        # Then: None 값으로 변환
        assert indicators.macd is None
        assert indicators.macd_signal is None
        assert indicators.rsi is None
        assert indicators.timestamp is not None

    @pytest.mark.parametrize("condition_type,expected", [
        ("상향돌파", True),
        ("하향돌파", False),
        ("이상", True),
        ("이하", False),
        ("알수없음", False)
    ])
    def test_check_macd_condition_parametrized(self, condition_type, expected):
        """다양한 MACD 조건 타입 테스트"""
        # Given: MACD >= 시그널, 이전 MACD < 이전 시그널 상황
        current_macd = 1.5
        current_signal = 1.2
        prev_macd = 0.8
        prev_signal = 1.0
        
        # When: 조건 체크
        result = TechnicalAnalysisService.check_macd_condition(
            current_macd, current_signal, prev_macd, prev_signal, condition_type
        )
        
        # Then: 예상 결과와 일치
        assert result == expected

    @pytest.mark.parametrize("condition_type,expected", [
        ("상향돌파", True),
        ("하향돌파", False),
        ("이상", True),
        ("이하", False),
        ("알수없음", False)
    ])
    def test_check_rsi_condition_parametrized(self, condition_type, expected):
        """다양한 RSI 조건 타입 테스트"""
        # Given: RSI > 기준값, 이전 RSI < 기준값 상황
        current_rsi = 35.0
        prev_rsi = 28.0
        rsi_value = 30.0
        
        # When: 조건 체크
        result = TechnicalAnalysisService.check_rsi_condition(
            current_rsi, prev_rsi, rsi_value, condition_type
        )
        
        # Then: 예상 결과와 일치
        assert result == expected