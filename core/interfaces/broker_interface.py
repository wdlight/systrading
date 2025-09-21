# TODO: 증권사 API 추상 인터페이스 정의
# - authenticate(): 인증 처리
# - get_account_balance(): 계좌 잔고 조회  
# - place_order(): 주문 실행
# - cancel_order(): 주문 취소
# - get_stock_price(): 주식 현재가 조회
# - get_chart_data(): 차트 데이터 조회

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

class BrokerInterface(ABC):
    """증권사 API 추상 인터페이스"""
    
    @abstractmethod
    def authenticate(self, credentials: Dict[str, str]) -> bool:
        """
        증권사 인증
        Args:
            credentials: 인증 정보 (API키, 비밀번호 등)
        Returns:
            bool: 인증 성공 여부
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Tuple[int, pd.DataFrame]:
        """
        계좌 잔고 조회
        Returns:
            Tuple[int, pd.DataFrame]: (총 평가금액, 종목별 잔고 DataFrame)
        """
        pass
    
    @abstractmethod
    def buy_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """
        매수 주문
        Args:
            stock_code: 종목코드
            order_qty: 주문수량
            order_price: 주문가격
            order_type: 주문유형
        Returns:
            Dict: 주문 결과
        """
        pass
    
    @abstractmethod
    def sell_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """
        매도 주문
        Args:
            stock_code: 종목코드
            order_qty: 주문수량
            order_price: 주문가격
            order_type: 주문유형
        Returns:
            Dict: 주문 결과
        """
        pass
    
    @abstractmethod
    def cancel_order(self, stock_code: str, order_qty: int, order_price: int, order_type: str = "00") -> Dict[str, Any]:
        """
        주문 취소
        Args:
            stock_code: 종목코드
            order_qty: 취소수량
            order_price: 취소가격
            order_type: 주문유형
        Returns:
            Dict: 취소 결과
        """
        pass
    
    @abstractmethod
    def get_minute_chart_data(self, stock_code: str) -> pd.DataFrame:
        """
        1분봉 차트 데이터 조회
        Args:
            stock_code: 종목코드
        Returns:
            pd.DataFrame: 차트 데이터
        """
        pass