"""
Pydantic 모델 정의
API 요청/응답에 사용되는 데이터 스키마
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from decimal import Decimal

# ===== 기본 데이터 모델 =====

class StockData(BaseModel):
    """주식 기본 정보"""
    code: str = Field(..., description="종목코드")
    name: str = Field(..., description="종목명")
    current_price: int = Field(..., description="현재가")
    change: int = Field(..., description="전일대비 변화량")
    change_rate: float = Field(..., description="등락률 (%)")
    volume: int = Field(0, description="거래량")

class TechnicalIndicators(BaseModel):
    """기술적 지표"""
    rsi: float = Field(..., description="RSI 값")
    macd: float = Field(..., description="MACD 값")
    macd_signal: float = Field(..., description="MACD 시그널")
    macd_histogram: Optional[float] = Field(None, description="MACD 히스토그램")

class Position(BaseModel):
    """보유 포지션"""
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    quantity: int = Field(..., description="보유수량")
    sellable_quantity: int = Field(..., description="매도가능수량")
    avg_price: int = Field(..., description="매입단가")
    current_price: int = Field(..., description="현재가")
    unrealized_pnl: int = Field(..., description="평가손익")
    profit_rate: float = Field(..., description="수익률 (%)")
    day_change: int = Field(..., description="전일대비")
    day_change_rate: float = Field(..., description="전일대비 등락률 (%)")

# ===== 계좌 관련 모델 =====

class AccountSummary(BaseModel):
    """계좌 요약 정보"""
    account_number: str = Field(..., description="계좌번호")
    total_asset: int = Field(..., description="총 자산")
    total_evaluation: int = Field(..., description="총 평가금액")
    available_cash: int = Field(..., description="주문가능현금")
    total_profit_loss: int = Field(..., description="총 손익")
    total_profit_rate: float = Field(..., description="총 수익률 (%)")

class AccountBalance(BaseModel):
    """계좌 잔고 정보"""
    summary: AccountSummary
    positions: List[Position] = Field(default_factory=list, description="보유 종목 목록")

# ===== 매매 조건 모델 =====

ConditionType = Literal["상향돌파", "하향돌파", "이상", "이하"]

class BuyConditions(BaseModel):
    """매수 조건"""
    amount: int = Field(..., description="매수 금액", gt=0)
    macd_type: ConditionType = Field(..., description="MACD 조건 타입")
    rsi_value: float = Field(..., description="RSI 기준값", ge=0, le=100)
    rsi_type: ConditionType = Field(..., description="RSI 조건 타입")

class SellConditions(BaseModel):
    """매도 조건"""
    macd_type: ConditionType = Field(..., description="MACD 조건 타입")
    rsi_value: float = Field(..., description="RSI 기준값", ge=0, le=100)
    rsi_type: ConditionType = Field(..., description="RSI 조건 타입")

class TradingConditions(BaseModel):
    """매매 조건 설정"""
    buy_conditions: BuyConditions
    sell_conditions: SellConditions

class TradingStatus(BaseModel):
    """매매 상태"""
    is_running: bool = Field(..., description="자동매매 실행 중 여부")
    start_time: Optional[datetime] = Field(None, description="시작 시간")
    total_trades: int = Field(0, description="총 거래 횟수")
    profit_trades: int = Field(0, description="수익 거래 횟수")
    loss_trades: int = Field(0, description="손실 거래 횟수")

# ===== 워치리스트 모델 =====

class WatchlistItem(BaseModel):
    """워치리스트 항목"""
    stock_code: str = Field(..., description="종목코드")
    current_price: int = Field(..., description="현재가")
    profit_rate: float = Field(..., description="수익률 (%)")
    avg_price: Optional[int] = Field(None, description="평균단가")
    quantity: int = Field(0, description="보유수량")
    macd: float = Field(..., description="MACD 값")
    macd_signal: float = Field(..., description="MACD 시그널")
    rsi: float = Field(..., description="RSI 값")
    trailing_stop_activated: bool = Field(False, description="트레일링스탑 발동 여부")
    trailing_stop_high: Optional[int] = Field(None, description="트레일링스탑 발동 후 고가")

class WatchlistResponse(BaseModel):
    """워치리스트 응답"""
    items: List[WatchlistItem] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

# ===== 주문 관리 모델 =====

OrderType = Literal["00", "01"]  # 00: 지정가, 01: 시장가

class OrderRequest(BaseModel):
    """주문 요청"""
    stock_code: str = Field(..., description="종목코드", min_length=6, max_length=6)
    quantity: int = Field(..., description="주문수량", gt=0)
    price: int = Field(..., description="주문가격", ge=0)
    order_type: OrderType = Field("00", description="주문유형")

class OrderResponse(BaseModel):
    """주문 응답"""
    success: bool = Field(..., description="주문 성공 여부")
    order_id: Optional[str] = Field(None, description="주문번호")
    message: str = Field(..., description="응답 메시지")
    timestamp: datetime = Field(default_factory=datetime.now)

class OrderHistory(BaseModel):
    """주문 내역"""
    order_id: str = Field(..., description="주문번호")
    stock_code: str = Field(..., description="종목코드")
    stock_name: str = Field(..., description="종목명")
    order_type: str = Field(..., description="주문구분")
    quantity: int = Field(..., description="주문수량")
    price: int = Field(..., description="주문단가")
    executed_quantity: int = Field(..., description="체결수량")
    executed_price: int = Field(..., description="체결단가")
    status: str = Field(..., description="주문상태")
    order_time: datetime = Field(..., description="주문시간")

# ===== 실시간 메시지 모델 =====

MessageType = Literal["price_update", "watchlist_update", "account_update", "order_update", "connection_status"]

class RealtimeMessage(BaseModel):
    """실시간 메시지"""
    type: MessageType = Field(..., description="메시지 타입")
    timestamp: datetime = Field(default_factory=datetime.now, description="타임스탬프")
    data: dict = Field(..., description="메시지 데이터")

class PriceUpdate(BaseModel):
    """가격 업데이트 메시지"""
    type: Literal["price_update"] = "price_update"
    timestamp: datetime = Field(default_factory=datetime.now)
    data: StockData

class WatchlistUpdate(BaseModel):
    """워치리스트 업데이트 메시지"""
    type: Literal["watchlist_update"] = "watchlist_update"
    timestamp: datetime = Field(default_factory=datetime.now)
    data: List[WatchlistItem]

class AccountUpdate(BaseModel):
    """계좌 업데이트 메시지"""
    type: Literal["account_update"] = "account_update"
    timestamp: datetime = Field(default_factory=datetime.now)
    data: AccountBalance

# ===== 응답 모델 =====

class ApiResponse(BaseModel):
    """일반 API 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[dict] = Field(None, description="응답 데이터")
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = Field(False, description="성공 여부")
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    timestamp: datetime = Field(default_factory=datetime.now)