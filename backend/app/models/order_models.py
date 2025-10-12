"""
주문 관련 데이터 모델
사용자 수동 매매 주문을 위한 Pydantic 모델 정의
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderType(str, Enum):
    """주문 유형"""
    LIMIT = "00"           # 지정가
    MARKET = "01"          # 시장가
    CONDITIONAL = "02"     # 조건부지정가
    BEST = "03"           # 최유리지정가
    PRIORITY = "04"       # 최우선지정가


class OrderSide(str, Enum):
    """주문 방향"""
    BUY = "buy"           # 매수
    SELL = "sell"         # 매도


class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING = "pending"    # 접수 대기
    ACCEPTED = "accepted"  # 접수 완료
    FILLED = "filled"      # 체결 완료
    PARTIAL = "partial"    # 부분 체결
    CANCELLED = "cancelled"  # 취소
    REJECTED = "rejected"  # 거부


class OrderRequest(BaseModel):
    """주문 요청 모델"""
    stock_code: str = Field(..., description="종목 코드 (6자리)")
    stock_name: str = Field(..., description="종목명")
    order_type: OrderType = Field(default=OrderType.LIMIT, description="주문 유형")
    order_side: Optional[OrderSide] = Field(None, description="매수/매도 구분 (엔드포인트에서 자동 설정)")
    quantity: int = Field(..., gt=0, description="주문 수량")
    price: Optional[int] = Field(default=None, ge=0, description="주문 가격 (시장가는 0 또는 None)")

    @validator('stock_code')
    def validate_stock_code(cls, v):
        """종목 코드 검증"""
        if not v or len(v) != 6 or not v.isdigit():
            raise ValueError('종목 코드는 6자리 숫자여야 합니다')
        return v

    @validator('price')
    def validate_price(cls, v, values):
        """주문 가격 검증"""
        order_type = values.get('order_type')
        # use_enum_values=True이므로 문자열로 비교
        if order_type == OrderType.MARKET.value:
            # 시장가는 가격이 0 또는 None
            return 0
        else:
            # 지정가 등은 가격 필수
            if v is None or v <= 0:
                raise ValueError('지정가 주문은 가격을 입력해야 합니다')
            return v

    class Config:
        use_enum_values = True


class OrderModifyRequest(BaseModel):
    """주문 정정 요청 모델"""
    order_number: str = Field(..., description="원주문번호")
    stock_code: str = Field(..., description="종목 코드")
    order_type: OrderType = Field(default=OrderType.LIMIT, description="정정 주문 유형")
    quantity: int = Field(..., gt=0, description="정정 수량")
    price: int = Field(..., gt=0, description="정정 가격")

    class Config:
        use_enum_values = True


class OrderCancelRequest(BaseModel):
    """주문 취소 요청 모델"""
    order_number: str = Field(..., description="원주문번호")
    stock_code: str = Field(..., description="종목 코드")
    order_type: OrderType = Field(default=OrderType.LIMIT, description="취소 주문 유형")
    quantity: int = Field(..., gt=0, description="취소 수량")
    price: int = Field(..., gt=0, description="취소 가격")

    class Config:
        use_enum_values = True


class OrderResponse(BaseModel):
    """주문 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    order_number: Optional[str] = Field(None, description="주문 번호")
    status: str = Field(..., description="주문 상태")
    message: str = Field(..., description="응답 메시지")

    # 추가 정보
    stock_code: Optional[str] = Field(None, description="종목 코드")
    stock_name: Optional[str] = Field(None, description="종목명")
    order_side: Optional[str] = Field(None, description="매수/매도")
    quantity: Optional[int] = Field(None, description="주문 수량")
    price: Optional[int] = Field(None, description="주문 가격")
    order_time: Optional[datetime] = Field(None, description="주문 시각")


class OrderDetail(BaseModel):
    """주문 상세 정보 모델"""
    order_number: str = Field(..., description="주문 번호")
    stock_code: str = Field(..., description="종목 코드")
    stock_name: str = Field(..., description="종목명")
    order_type: str = Field(..., description="주문 유형")
    order_side: str = Field(..., description="매수/매도")
    order_status: OrderStatus = Field(..., description="주문 상태")

    # 수량 정보
    quantity: int = Field(..., description="주문 수량")
    filled_quantity: int = Field(default=0, description="체결 수량")
    remaining_quantity: int = Field(..., description="미체결 수량")

    # 가격 정보
    order_price: int = Field(..., description="주문 가격")
    filled_price: Optional[int] = Field(None, description="체결 가격")

    # 시간 정보
    order_time: datetime = Field(..., description="주문 시각")
    filled_time: Optional[datetime] = Field(None, description="체결 시각")

    # 금액 정보
    order_amount: int = Field(..., description="주문 금액")
    filled_amount: int = Field(default=0, description="체결 금액")
    commission: int = Field(default=0, description="수수료")
    tax: int = Field(default=0, description="제세금")

    class Config:
        use_enum_values = True


class PendingOrdersResponse(BaseModel):
    """미체결 주문 조회 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    orders: List[OrderDetail] = Field(default_factory=list, description="미체결 주문 목록")
    total_count: int = Field(default=0, description="전체 미체결 주문 수")


class OrderHistoryResponse(BaseModel):
    """체결 내역 조회 응답"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    orders: List[OrderDetail] = Field(default_factory=list, description="체결 내역 목록")
    total_count: int = Field(default=0, description="전체 체결 내역 수")

    # 통계 정보
    total_buy_amount: int = Field(default=0, description="총 매수 금액")
    total_sell_amount: int = Field(default=0, description="총 매도 금액")
    total_commission: int = Field(default=0, description="총 수수료")
    total_tax: int = Field(default=0, description="총 제세금")


class TickSize(BaseModel):
    """호가 단위 정보"""
    min_price: int = Field(..., description="최소 가격")
    max_price: Optional[int] = Field(None, description="최대 가격")
    tick_size: int = Field(..., description="호가 단위")


# 호가 단위 테이블
TICK_SIZE_TABLE = [
    TickSize(min_price=0, max_price=1000, tick_size=1),
    TickSize(min_price=1000, max_price=5000, tick_size=5),
    TickSize(min_price=5000, max_price=10000, tick_size=10),
    TickSize(min_price=10000, max_price=50000, tick_size=50),
    TickSize(min_price=50000, max_price=100000, tick_size=100),
    TickSize(min_price=100000, max_price=500000, tick_size=500),
    TickSize(min_price=500000, max_price=None, tick_size=1000),
]


def get_tick_size(price: int) -> int:
    """
    가격에 따른 호가 단위 반환

    Args:
        price: 주식 가격

    Returns:
        호가 단위
    """
    for tick in TICK_SIZE_TABLE:
        if tick.max_price is None:
            return tick.tick_size
        if tick.min_price <= price < tick.max_price:
            return tick.tick_size
    return 1


def adjust_price_to_tick(price: int) -> int:
    """
    가격을 호가 단위에 맞게 조정

    Args:
        price: 조정할 가격

    Returns:
        호가 단위로 조정된 가격
    """
    tick_size = get_tick_size(price)
    return (price // tick_size) * tick_size
