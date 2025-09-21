# RSI/MACD 트레이딩 전략 엔진
# rsimacd_trading.py에서 이동된 트레이딩 로직

import pandas as pd
import talib as ta
from loguru import logger
from typing import Dict, Any
from core.interfaces.strategy_interface import StrategyInterface

class RSIMACDTradingEngine(StrategyInterface):
    """RSI/MACD 기반 트레이딩 전략 엔진"""
    
    def __init__(self):
        self.strategy_name = "RSI_MACD_Strategy"
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        RSI/MACD 지표 계산
        
        Args:
            df: OHLCV 데이터프레임 (종가 컬럼 필요)
        
        Returns:
            pd.DataFrame: 지표가 추가된 데이터프레임
        """
        try:
            # EMA 기반 MACD 계산
            df['EMA_fast'] = df['종가'].ewm(span=9, adjust=False).mean()
            df['EMA_slow'] = df['종가'].ewm(span=18, adjust=False).mean()
            df['MACD'] = df['EMA_fast'] - df['EMA_slow']
            df['MACD_signal'] = df['MACD'].ewm(span=6, adjust=False).mean()
            
            # RSI 계산
            df['RSI'] = ta.RSI(df['종가'], timeperiod=14)
            
            logger.debug(f"지표 계산 완료 - MACD: {df['MACD'].iloc[-1]:.4f}, RSI: {df['RSI'].iloc[-1]:.2f}")
            return df
            
        except Exception as e:
            logger.error(f"지표 계산 중 오류 발생: {e}")
            raise
    
    def check_buy_signal(self, df: pd.DataFrame, buy_conditions: Dict[str, Any]) -> bool:
        """
        매수 시그널 체크
        
        Args:
            df: 지표가 계산된 데이터프레임
            buy_conditions: 매수 조건 설정
                - macd_type: "상향돌파", "하향돌파", "이상", "이하"
                - rsi_type: "상향돌파", "하향돌파", "이상", "이하"
                - rsi_value: RSI 기준값
        
        Returns:
            bool: 매수 시그널 여부
        """
        try:
            if len(df) < 2:
                return False
            
            현MACD = df['MACD'].iloc[-1]
            현MACD_signal = df['MACD_signal'].iloc[-1]
            전MACD = df['MACD'].iloc[-2]
            전MACD_signal = df['MACD_signal'].iloc[-2]
            현RSI = df['RSI'].iloc[-1]
            전RSI = df['RSI'].iloc[-2]
            
            # MACD 조건 체크
            macd_signal = self._check_macd_condition(
                현MACD, 현MACD_signal, 전MACD, 전MACD_signal, 
                buy_conditions.get('macd_type', '상향돌파')
            )
            
            # RSI 조건 체크
            rsi_signal = self._check_rsi_condition(
                현RSI, 전RSI, 
                buy_conditions.get('rsi_type', '하향돌파'),
                buy_conditions.get('rsi_value', 30)
            )
            
            result = macd_signal and rsi_signal
            if result:
                logger.info(f"매수 시그널 발생 - MACD: {현MACD:.4f}/{현MACD_signal:.4f}, RSI: {현RSI:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"매수 시그널 체크 중 오류 발생: {e}")
            return False
    
    def check_sell_signal(self, df: pd.DataFrame, sell_conditions: Dict[str, Any]) -> bool:
        """
        매도 시그널 체크
        
        Args:
            df: 지표가 계산된 데이터프레임
            sell_conditions: 매도 조건 설정
        
        Returns:
            bool: 매도 시그널 여부
        """
        try:
            if len(df) < 2:
                return False
            
            현MACD = df['MACD'].iloc[-1]
            현MACD_signal = df['MACD_signal'].iloc[-1]
            전MACD = df['MACD'].iloc[-2]
            전MACD_signal = df['MACD_signal'].iloc[-2]
            현RSI = df['RSI'].iloc[-1]
            전RSI = df['RSI'].iloc[-2]
            
            # MACD 조건 체크
            macd_signal = self._check_macd_condition(
                현MACD, 현MACD_signal, 전MACD, 전MACD_signal, 
                sell_conditions.get('macd_type', '하향돌파')
            )
            
            # RSI 조건 체크
            rsi_signal = self._check_rsi_condition(
                현RSI, 전RSI, 
                sell_conditions.get('rsi_type', '상향돌파'),
                sell_conditions.get('rsi_value', 70)
            )
            
            result = macd_signal and rsi_signal
            if result:
                logger.info(f"매도 시그널 발생 - MACD: {현MACD:.4f}/{현MACD_signal:.4f}, RSI: {현RSI:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"매도 시그널 체크 중 오류 발생: {e}")
            return False
    
    def _check_macd_condition(self, 현MACD: float, 현MACD_signal: float, 
                             전MACD: float, 전MACD_signal: float, condition_type: str) -> bool:
        """MACD 조건 체크"""
        if condition_type == "상향돌파":
            return 현MACD >= 현MACD_signal and 전MACD < 전MACD_signal
        elif condition_type == "하향돌파":
            return 현MACD <= 현MACD_signal and 전MACD > 전MACD_signal
        elif condition_type == "이상":
            return 현MACD >= 현MACD_signal
        elif condition_type == "이하":
            return 현MACD <= 현MACD_signal
        else:
            raise ValueError(f"알 수 없는 MACD 조건: {condition_type}")
    
    def _check_rsi_condition(self, 현RSI: float, 전RSI: float, condition_type: str, rsi_value: float) -> bool:
        """RSI 조건 체크"""
        if condition_type == "상향돌파":
            return 현RSI >= rsi_value and 전RSI < rsi_value
        elif condition_type == "하향돌파":
            return 현RSI <= rsi_value and 전RSI > rsi_value
        elif condition_type == "이상":
            return 현RSI >= rsi_value
        elif condition_type == "이하":
            return 현RSI <= rsi_value
        else:
            raise ValueError(f"알 수 없는 RSI 조건: {condition_type}")
    
    def calculate_position_size(self, balance: int, current_price: int) -> int:
        """
        포지션 크기 계산
        
        Args:
            balance: 투자 가능 금액
            current_price: 현재가
        
        Returns:
            int: 주문 수량
        """
        if current_price <= 0:
            return 0
        
        order_qty = balance // current_price
        logger.debug(f"포지션 크기 계산 - 잔고: {balance:,}, 현재가: {current_price:,}, 주문수량: {order_qty}")
        return order_qty
    
    def calculate_profit_rate(self, current_price: float, avg_price: float) -> float:
        """
        수익률 계산
        
        Args:
            current_price: 현재가
            avg_price: 평균단가
        
        Returns:
            float: 수익률 (%)
        """
        if not avg_price or avg_price == 0:
            return 0.0
        
        profit_rate = round((current_price - avg_price) / avg_price * 100, 2)
        return profit_rate
    
    def get_strategy_name(self) -> str:
        """전략 이름 반환"""
        return self.strategy_name