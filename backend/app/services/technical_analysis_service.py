"""
기술적 분석 서비스
MACD, RSI 등 기술적 지표 계산
PyQt5 rsimacd_trading.py의 기술적 지표 계산 로직 기반
"""

import pandas as pd
import numpy as np
import talib as ta
from typing import Tuple, Optional, Dict, Any
import logging
from datetime import datetime

from app.models.watchlist_models import TechnicalIndicators

logger = logging.getLogger(__name__)


class TechnicalAnalysisService:
    """기술적 분석 서비스"""
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast_period: int = 9, slow_period: int = 18, signal_period: int = 6) -> Tuple[float, float]:
        """
        MACD 계산 (PyQt5의 로직과 동일)
        EMA 기반 MACD 계산
        """
        try:
            if len(prices) < max(fast_period, slow_period, signal_period):
                return np.nan, np.nan
            
            # EMA 계산 (PyQt5와 동일한 파라미터)
            ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
            ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
            
            # MACD 라인 계산
            macd_line = ema_fast - ema_slow
            
            # 시그널 라인 계산 (MACD의 EMA)
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
            
            return float(macd_line.iloc[-1]), float(signal_line.iloc[-1])
            
        except Exception as e:
            logger.error(f"MACD 계산 오류: {e}")
            return np.nan, np.nan
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """RSI 계산 (TA-Lib 사용, PyQt5와 동일)"""
        try:
            if len(prices) < period:
                return np.nan
            
            rsi_values = ta.RSI(prices.values, timeperiod=period)
            return float(rsi_values[-1]) if not np.isnan(rsi_values[-1]) else np.nan
            
        except Exception as e:
            logger.error(f"RSI 계산 오류: {e}")
            return np.nan
    
    @staticmethod
    def calculate_all_indicators(minute_data: pd.DataFrame) -> Dict[str, float]:
        """
        모든 기술적 지표 계산
        PyQt5의 1분봉 조회 결과 처리와 동일한 로직
        """
        try:
            if minute_data is None or minute_data.empty:
                return {
                    'macd': np.nan,
                    'macd_signal': np.nan,
                    'rsi': np.nan
                }
            
            # 종가 데이터 추출
            close_prices = minute_data['종가'] if '종가' in minute_data.columns else minute_data.iloc[:, -1]
            
            # MACD 계산 (PyQt5와 동일한 파라미터: 9, 18, 6)
            macd, macd_signal = TechnicalAnalysisService.calculate_macd(
                close_prices, 
                fast_period=9, 
                slow_period=18, 
                signal_period=6
            )
            
            # RSI 계산 (14일)
            rsi = TechnicalAnalysisService.calculate_rsi(close_prices, period=14)
            
            logger.debug(f"기술적 지표 계산 완료 - MACD: {macd:.2f}, 시그널: {macd_signal:.2f}, RSI: {rsi:.2f}")
            
            return {
                'macd': macd,
                'macd_signal': macd_signal,
                'rsi': rsi
            }
            
        except Exception as e:
            logger.error(f"기술적 지표 계산 실패: {e}")
            return {
                'macd': np.nan,
                'macd_signal': np.nan,
                'rsi': np.nan
            }
    
    @staticmethod
    def analyze_minute_data(stock_code: str, minute_data: pd.DataFrame) -> Dict[str, Any]:
        """
        1분봉 데이터 분석
        PyQt5의 receive_tr_result에서 1분봉조회 처리 로직과 동일
        """
        try:
            if minute_data is None or minute_data.empty:
                logger.warning(f"종목 {stock_code}의 1분봉 데이터가 없습니다")
                return {}
            
            # 최신 가격 정보
            latest_data = minute_data.iloc[-1]
            current_price = int(latest_data['종가']) if '종가' in minute_data.columns else int(latest_data.iloc[-1])
            
            # 기술적 지표 계산
            indicators = TechnicalAnalysisService.calculate_all_indicators(minute_data)
            
            # 이전 데이터와 현재 데이터 비교 (매매 신호 판단용)
            prev_indicators = {}
            if len(minute_data) >= 2:
                prev_data = minute_data.iloc[:-1]  # 마지막 행 제외
                prev_indicators = TechnicalAnalysisService.calculate_all_indicators(prev_data)
            
            result = {
                'stock_code': stock_code,
                'current_price': current_price,
                'current': {
                    'macd': indicators['macd'],
                    'macd_signal': indicators['macd_signal'],
                    'rsi': indicators['rsi']
                },
                'previous': {
                    'macd': prev_indicators.get('macd', np.nan),
                    'macd_signal': prev_indicators.get('macd_signal', np.nan),
                    'rsi': prev_indicators.get('rsi', np.nan)
                },
                'timestamp': datetime.now()
            }
            
            logger.debug(f"1분봉 분석 완료 - 종목: {stock_code}, 현재가: {current_price}")
            return result
            
        except Exception as e:
            logger.error(f"1분봉 데이터 분석 실패 ({stock_code}): {e}")
            return {}
    
    @staticmethod
    def check_macd_condition(current_macd: float, current_signal: float, 
                           prev_macd: float, prev_signal: float, 
                           condition_type: str) -> bool:
        """
        MACD 조건 체크
        PyQt5의 매수/매도 조건 체크 로직과 동일
        """
        try:
            if np.isnan(current_macd) or np.isnan(current_signal):
                return False
            
            if condition_type == "상향돌파":
                # 현재: MACD >= 시그널, 이전: MACD < 시그널
                return (current_macd >= current_signal and 
                       prev_macd < prev_signal)
            
            elif condition_type == "하향돌파":
                # 현재: MACD <= 시그널, 이전: MACD > 시그널
                return (current_macd <= current_signal and 
                       prev_macd > prev_signal)
            
            elif condition_type == "이상":
                return current_macd >= current_signal
            
            elif condition_type == "이하":
                return current_macd <= current_signal
            
            else:
                logger.warning(f"알 수 없는 MACD 조건 타입: {condition_type}")
                return False
                
        except Exception as e:
            logger.error(f"MACD 조건 체크 오류: {e}")
            return False
    
    @staticmethod
    def check_rsi_condition(current_rsi: float, prev_rsi: float, 
                          rsi_value: float, condition_type: str) -> bool:
        """
        RSI 조건 체크
        PyQt5의 매수/매도 조건 체크 로직과 동일
        """
        try:
            if np.isnan(current_rsi):
                return False
            
            if condition_type == "상향돌파":
                # 현재: RSI >= 기준값, 이전: RSI < 기준값
                return (current_rsi >= rsi_value and 
                       prev_rsi < rsi_value)
            
            elif condition_type == "하향돌파":
                # 현재: RSI <= 기준값, 이전: RSI > 기준값
                return (current_rsi <= rsi_value and 
                       prev_rsi > rsi_value)
            
            elif condition_type == "이상":
                return current_rsi >= rsi_value
            
            elif condition_type == "이하":
                return current_rsi <= rsi_value
            
            else:
                logger.warning(f"알 수 없는 RSI 조건 타입: {condition_type}")
                return False
                
        except Exception as e:
            logger.error(f"RSI 조건 체크 오류: {e}")
            return False
    
    @staticmethod
    def get_trading_signals(analysis_result: Dict[str, Any], 
                          buy_conditions: Dict[str, Any], 
                          sell_conditions: Dict[str, Any]) -> Dict[str, bool]:
        """
        매매 신호 분석
        PyQt5의 매수/매도 조건 체크 통합 로직
        """
        try:
            if not analysis_result:
                return {'buy_signal': False, 'sell_signal': False}
            
            current = analysis_result.get('current', {})
            previous = analysis_result.get('previous', {})
            
            # 매수 신호 체크
            buy_macd_signal = TechnicalAnalysisService.check_macd_condition(
                current.get('macd', np.nan),
                current.get('macd_signal', np.nan),
                previous.get('macd', np.nan),
                previous.get('macd_signal', np.nan),
                buy_conditions.get('macd_type', '상향돌파')
            )
            
            buy_rsi_signal = TechnicalAnalysisService.check_rsi_condition(
                current.get('rsi', np.nan),
                previous.get('rsi', np.nan),
                buy_conditions.get('rsi_value', 30),
                buy_conditions.get('rsi_type', '이상')
            )
            
            buy_signal = buy_macd_signal and buy_rsi_signal
            
            # 매도 신호 체크
            sell_macd_signal = TechnicalAnalysisService.check_macd_condition(
                current.get('macd', np.nan),
                current.get('macd_signal', np.nan),
                previous.get('macd', np.nan),
                previous.get('macd_signal', np.nan),
                sell_conditions.get('macd_type', '하향돌파')
            )
            
            sell_rsi_signal = TechnicalAnalysisService.check_rsi_condition(
                current.get('rsi', np.nan),
                previous.get('rsi', np.nan),
                sell_conditions.get('rsi_value', 70),
                sell_conditions.get('rsi_type', '이하')
            )
            
            sell_signal = sell_macd_signal and sell_rsi_signal
            
            logger.debug(f"매매 신호 - 매수: {buy_signal}, 매도: {sell_signal}")
            
            return {
                'buy_signal': buy_signal,
                'sell_signal': sell_signal,
                'buy_macd': buy_macd_signal,
                'buy_rsi': buy_rsi_signal,
                'sell_macd': sell_macd_signal,
                'sell_rsi': sell_rsi_signal
            }
            
        except Exception as e:
            logger.error(f"매매 신호 분석 실패: {e}")
            return {'buy_signal': False, 'sell_signal': False}
    
    @staticmethod
    def format_technical_indicators(macd: float, macd_signal: float, rsi: float) -> TechnicalIndicators:
        """기술적 지표를 모델 형태로 포맷"""
        return TechnicalIndicators(
            macd=macd if not np.isnan(macd) else None,
            macd_signal=macd_signal if not np.isnan(macd_signal) else None,
            rsi=rsi if not np.isnan(rsi) else None,
            timestamp=datetime.now()
        )