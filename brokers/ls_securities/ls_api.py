# TODO: LS증권 API 구현 예정
# BrokerInterface를 상속받아 구현

from core.interfaces.broker_interface import BrokerInterface
from typing import Dict, Any, Tuple
import pandas as pd

class LSSecuritiesAPI(BrokerInterface):
    """LS증권 API 클라이언트 (향후 구현 예정)"""
    
    def __init__(self, config):
        """
        TODO: LS증권 API 초기화
        Args:
            config: LS증권 API 설정
        """
        self.config = config
        pass
    
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """TODO: LS증권 인증 구현"""
        pass
    
    def get_account_balance(self) -> Tuple[int, pd.DataFrame]:
        """TODO: LS증권 계좌 잔고 조회 구현"""
        pass
    
    def buy_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """TODO: LS증권 매수 주문 구현"""
        pass
    
    def sell_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """TODO: LS증권 매도 주문 구현"""
        pass
    
    def cancel_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """TODO: LS증권 주문 취소 구현"""
        pass
    
    def get_minute_chart_data(self, stock_code: str) -> pd.DataFrame:
        """TODO: LS증권 1분봉 차트 데이터 조회 구현"""
        pass