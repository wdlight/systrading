# TODO: 트레이딩 전략 추상 인터페이스 정의
# - analyze(): 시장 데이터 분석 및 시그널 생성
# - get_buy_conditions(): 매수 조건 반환
# - get_sell_conditions(): 매도 조건 반환
# - calculate_indicators(): 기술적 지표 계산

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import pandas as pd

class StrategyInterface(ABC):
    """트레이딩 전략 추상 인터페이스"""
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 계산
        Args:
            df: OHLCV 데이터프레임
        Returns:
            pd.DataFrame: 지표가 추가된 데이터프레임
        """
        pass
    
    @abstractmethod
    def check_buy_signal(self, df: pd.DataFrame, buy_conditions: Dict[str, Any]) -> bool:
        """
        매수 시그널 체크
        Args:
            df: 지표가 계산된 데이터프레임
            buy_conditions: 매수 조건 설정
        Returns:
            bool: 매수 시그널 여부
        """
        pass
    
    @abstractmethod
    def check_sell_signal(self, df: pd.DataFrame, sell_conditions: Dict[str, Any]) -> bool:
        """
        매도 시그널 체크
        Args:
            df: 지표가 계산된 데이터프레임
            sell_conditions: 매도 조건 설정
        Returns:
            bool: 매도 시그널 여부
        """
        pass
    
    @abstractmethod
    def calculate_position_size(self, balance: int, current_price: int) -> int:
        """
        포지션 크기 계산
        Args:
            balance: 투자 가능 금액
            current_price: 현재가
        Returns:
            int: 주문 수량
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        전략 이름 반환
        Returns:
            str: 전략 이름
        """
        pass