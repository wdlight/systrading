"""
워치리스트 관련 데이터 모델
PyQt5 rsimacd_trading.py의 realtime_watchlist_df 구조를 기반으로 정의
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MACDConditionType(str, Enum):
    """MACD 조건 타입"""
    UPWARD_CROSS = "상향돌파"
    DOWNWARD_CROSS = "하향돌파"
    ABOVE = "이상"
    BELOW = "이하"


class RSIConditionType(str, Enum):
    """RSI 조건 타입"""
    UPWARD_CROSS = "상향돌파"
    DOWNWARD_CROSS = "하향돌파"
    ABOVE = "이상"
    BELOW = "이하"


class WatchlistItem(BaseModel):
    """워치리스트 아이템 - realtime_watchlist_df 구조 기반"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: Optional[str] = Field(None, description="종목명")
    current_price: float = Field(0.0, description="현재가")
    profit_rate: Optional[float] = Field(None, description="수익률 (%)")
    avg_price: Optional[float] = Field(None, description="평균단가")
    quantity: int = Field(0, description="보유수량")
    macd: Optional[float] = Field(None, description="MACD 값")
    macd_signal: Optional[float] = Field(None, description="MACD 시그널")
    rsi: Optional[float] = Field(None, description="RSI 값")
    trailing_stop_active: bool = Field(False, description="트레일링스탑 발동여부")
    trailing_stop_high: Optional[float] = Field(None, description="트레일링스탑 발동후 고가")
    last_updated: datetime = Field(default_factory=datetime.now, description="마지막 업데이트 시각")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BuyConditions(BaseModel):
    """매수 조건 설정"""
    amount: int = Field(100000, description="매수 금액")
    macd_type: MACDConditionType = Field(MACDConditionType.UPWARD_CROSS, description="MACD 조건 타입")
    rsi_value: int = Field(30, description="RSI 기준값")
    rsi_type: RSIConditionType = Field(RSIConditionType.ABOVE, description="RSI 조건 타입")
    enabled: bool = Field(True, description="매수 조건 활성화")


class SellConditions(BaseModel):
    """매도 조건 설정"""
    macd_type: MACDConditionType = Field(MACDConditionType.DOWNWARD_CROSS, description="MACD 조건 타입")
    rsi_value: int = Field(70, description="RSI 기준값")
    rsi_type: RSIConditionType = Field(RSIConditionType.BELOW, description="RSI 조건 타입")
    profit_target: Optional[float] = Field(None, description="목표 수익률 (%)")
    stop_loss: Optional[float] = Field(None, description="손절매 비율 (%)")
    enabled: bool = Field(True, description="매도 조건 활성화")


class TrailingStopSettings(BaseModel):
    """트레일링스탑 설정"""
    enabled: bool = Field(False, description="트레일링스탑 활성화")
    activation_rate: float = Field(5.0, description="트레일링스탑 발동 수익률 (%)")
    trailing_rate: float = Field(2.0, description="트레일링스탑 추적 비율 (%)")


class TradingConditions(BaseModel):
    """전체 매매 조건 설정"""
    buy_conditions: BuyConditions = Field(default_factory=BuyConditions)
    sell_conditions: SellConditions = Field(default_factory=SellConditions)
    trailing_stop: TrailingStopSettings = Field(default_factory=TrailingStopSettings)
    auto_trading_enabled: bool = Field(False, description="자동매매 활성화")


class TechnicalIndicators(BaseModel):
    """기술적 지표 데이터"""
    macd: Optional[float] = Field(None, description="MACD 값")
    macd_signal: Optional[float] = Field(None, description="MACD 시그널")
    rsi: Optional[float] = Field(None, description="RSI 값")
    timestamp: datetime = Field(default_factory=datetime.now, description="계산 시각")


class PriceUpdateEvent(BaseModel):
    """가격 업데이트 이벤트"""
    stock_code: str = Field(..., description="종목코드")
    current_price: float = Field(..., description="현재가")
    change: float = Field(0.0, description="전일대비 변화")
    change_rate: float = Field(0.0, description="전일대비 변화율 (%)")
    volume: Optional[int] = Field(None, description="거래량")
    timestamp: datetime = Field(default_factory=datetime.now, description="업데이트 시각")


class WatchlistUpdateEvent(BaseModel):
    """워치리스트 업데이트 이벤트"""
    type: str = Field(..., description="이벤트 타입")
    stock_code: str = Field(..., description="종목코드")
    data: Dict[str, Any] = Field(..., description="업데이트 데이터")
    timestamp: datetime = Field(default_factory=datetime.now, description="이벤트 발생 시각")


class AddStockRequest(BaseModel):
    """종목 추가 요청"""
    stock_code: str = Field(..., description="종목코드", min_length=6, max_length=6)
    stock_name: Optional[str] = Field(None, description="종목명")


class RemoveStockRequest(BaseModel):
    """종목 제거 요청"""
    stock_code: str = Field(..., description="종목코드")


class TradeExecutionResult(BaseModel):
    """거래 실행 결과"""
    success: bool = Field(..., description="실행 성공 여부")
    order_id: Optional[str] = Field(None, description="주문 ID")
    message: str = Field(..., description="결과 메시지")
    timestamp: datetime = Field(default_factory=datetime.now, description="실행 시각")


class MarketDataSnapshot(BaseModel):
    """시장 데이터 스냅샷"""
    stock_code: str = Field(..., description="종목코드")
    open_price: float = Field(..., description="시가")
    high_price: float = Field(..., description="고가")
    low_price: float = Field(..., description="저가")
    close_price: float = Field(..., description="종가")
    volume: int = Field(..., description="거래량")
    timestamp: datetime = Field(..., description="데이터 시각")


class WatchlistSummary(BaseModel):
    """워치리스트 요약 정보"""
    total_stocks: int = Field(..., description="총 종목 수")
    total_value: float = Field(..., description="총 평가 금액")
    total_profit_loss: float = Field(..., description="총 손익")
    total_profit_rate: float = Field(..., description="총 수익률")
    last_updated: datetime = Field(default_factory=datetime.now, description="마지막 업데이트")