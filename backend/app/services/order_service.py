"""
주문 서비스
사용자 수동 매매 주문 처리 로직
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

from app.core.korea_invest import KoreaInvestAPIService
from app.models.order_models import (
    OrderRequest,
    OrderModifyRequest,
    OrderCancelRequest,
    OrderResponse,
    OrderDetail,
    PendingOrdersResponse,
    OrderHistoryResponse,
    OrderType,
    OrderSide,
    OrderStatus,
    adjust_price_to_tick
)


class OrderService:
    """주문 서비스 클래스"""

    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest = korea_invest_service
        # 실제 운영에서는 데이터베이스나 Redis 사용
        # 현재는 메모리에 저장 (테스트용)
        self._pending_orders: List[OrderDetail] = []
        self._order_history: List[OrderDetail] = []

    async def place_buy_order(self, request: OrderRequest) -> OrderResponse:
        """
        매수 주문 실행

        Args:
            request: 주문 요청 데이터

        Returns:
            OrderResponse: 주문 응답
        """
        try:
            logger.info(f"매수 주문 시작: {request.stock_name}({request.stock_code}), "
                       f"수량: {request.quantity}, 가격: {request.price}")

            # 가격 호가 단위 조정
            adjusted_price = request.price
            # use_enum_values=True이므로 문자열로 비교
            if request.order_type != OrderType.MARKET.value and request.price:
                adjusted_price = adjust_price_to_tick(request.price)
                if adjusted_price != request.price:
                    logger.info(f"가격 호가 단위 조정: {request.price} → {adjusted_price}")

            # 한국투자증권 API 호출
            result = await self.korea_invest.buy_order(
                stock_code=request.stock_code,
                order_qty=request.quantity,
                order_price=adjusted_price if adjusted_price else 0,
                order_type=request.order_type
            )

            if not result.get("success"):
                return OrderResponse(
                    success=False,
                    order_number=None,
                    status=OrderStatus.REJECTED,
                    message=result.get("message", "매수 주문이 거부되었습니다."),
                    stock_code=request.stock_code,
                    stock_name=request.stock_name,
                    order_side=OrderSide.BUY,
                    quantity=request.quantity,
                    price=adjusted_price
                )

            # API 응답에서 주문번호 추출
            api_data = result.get("data", {})
            order_number = api_data.get("주문번호") or api_data.get("order_no") or f"BUY{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 주문 상세 정보 저장 (미체결 주문 목록에 추가)
            order_detail = OrderDetail(
                order_number=order_number,
                stock_code=request.stock_code,
                stock_name=request.stock_name,
                order_type=request.order_type,
                order_side=OrderSide.BUY,
                order_status=OrderStatus.ACCEPTED,
                quantity=request.quantity,
                filled_quantity=0,
                remaining_quantity=request.quantity,
                order_price=adjusted_price if adjusted_price else 0,
                filled_price=None,
                order_time=datetime.now(),
                filled_time=None,
                order_amount=adjusted_price * request.quantity if adjusted_price else 0,
                filled_amount=0,
                commission=0,
                tax=0
            )
            self._pending_orders.append(order_detail)

            logger.info(f"매수 주문 성공: 주문번호 {order_number}")

            return OrderResponse(
                success=True,
                order_number=order_number,
                status=OrderStatus.ACCEPTED,
                message="매수 주문이 성공적으로 접수되었습니다.",
                stock_code=request.stock_code,
                stock_name=request.stock_name,
                order_side=OrderSide.BUY,
                quantity=request.quantity,
                price=adjusted_price,
                order_time=datetime.now()
            )

        except Exception as e:
            logger.error(f"매수 주문 실행 중 오류 발생: {str(e)}", exc_info=True)
            return OrderResponse(
                success=False,
                order_number=None,
                status=OrderStatus.REJECTED,
                message=f"매수 주문 실행 중 오류가 발생했습니다: {str(e)}",
                stock_code=request.stock_code,
                stock_name=request.stock_name
            )

    async def place_sell_order(self, request: OrderRequest) -> OrderResponse:
        """
        매도 주문 실행

        Args:
            request: 주문 요청 데이터

        Returns:
            OrderResponse: 주문 응답
        """
        try:
            logger.info(f"매도 주문 시작: {request.stock_name}({request.stock_code}), "
                       f"수량: {request.quantity}, 가격: {request.price}")

            # 가격 호가 단위 조정
            adjusted_price = request.price
            # use_enum_values=True이므로 문자열로 비교
            if request.order_type != OrderType.MARKET.value and request.price:
                adjusted_price = adjust_price_to_tick(request.price)
                if adjusted_price != request.price:
                    logger.info(f"가격 호가 단위 조정: {request.price} → {adjusted_price}")

            # 한국투자증권 API 호출
            result = await self.korea_invest.sell_order(
                stock_code=request.stock_code,
                order_qty=request.quantity,
                order_price=adjusted_price if adjusted_price else 0,
                order_type=request.order_type
            )

            if not result.get("success"):
                return OrderResponse(
                    success=False,
                    order_number=None,
                    status=OrderStatus.REJECTED,
                    message=result.get("message", "매도 주문이 거부되었습니다."),
                    stock_code=request.stock_code,
                    stock_name=request.stock_name,
                    order_side=OrderSide.SELL,
                    quantity=request.quantity,
                    price=adjusted_price
                )

            # API 응답에서 주문번호 추출
            api_data = result.get("data", {})
            order_number = api_data.get("주문번호") or api_data.get("order_no") or f"SELL{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 주문 상세 정보 저장 (미체결 주문 목록에 추가)
            order_detail = OrderDetail(
                order_number=order_number,
                stock_code=request.stock_code,
                stock_name=request.stock_name,
                order_type=request.order_type,
                order_side=OrderSide.SELL,
                order_status=OrderStatus.ACCEPTED,
                quantity=request.quantity,
                filled_quantity=0,
                remaining_quantity=request.quantity,
                order_price=adjusted_price if adjusted_price else 0,
                filled_price=None,
                order_time=datetime.now(),
                filled_time=None,
                order_amount=adjusted_price * request.quantity if adjusted_price else 0,
                filled_amount=0,
                commission=0,
                tax=0
            )
            self._pending_orders.append(order_detail)

            logger.info(f"매도 주문 성공: 주문번호 {order_number}")

            return OrderResponse(
                success=True,
                order_number=order_number,
                status=OrderStatus.ACCEPTED,
                message="매도 주문이 성공적으로 접수되었습니다.",
                stock_code=request.stock_code,
                stock_name=request.stock_name,
                order_side=OrderSide.SELL,
                quantity=request.quantity,
                price=adjusted_price,
                order_time=datetime.now()
            )

        except Exception as e:
            logger.error(f"매도 주문 실행 중 오류 발생: {str(e)}", exc_info=True)
            return OrderResponse(
                success=False,
                order_number=None,
                status=OrderStatus.REJECTED,
                message=f"매도 주문 실행 중 오류가 발생했습니다: {str(e)}",
                stock_code=request.stock_code,
                stock_name=request.stock_name
            )

    async def modify_order(self, request: OrderModifyRequest) -> OrderResponse:
        """
        주문 정정

        Args:
            request: 주문 정정 요청 데이터

        Returns:
            OrderResponse: 주문 응답
        """
        try:
            logger.info(f"주문 정정 시작: 주문번호 {request.order_number}, "
                       f"수량: {request.quantity}, 가격: {request.price}")

            # 가격 호가 단위 조정
            adjusted_price = adjust_price_to_tick(request.price)

            # TODO: 실제 API 연동 필요
            # 현재는 한국투자증권 API에 정정 메서드가 없으므로 mock 응답

            # 미체결 주문 목록에서 찾아서 수정
            order_found = False
            for order in self._pending_orders:
                if order.order_number == request.order_number:
                    order.quantity = request.quantity
                    order.remaining_quantity = request.quantity
                    order.order_price = adjusted_price
                    order.order_amount = adjusted_price * request.quantity
                    order_found = True
                    break

            if not order_found:
                return OrderResponse(
                    success=False,
                    order_number=request.order_number,
                    status=OrderStatus.REJECTED,
                    message="정정할 주문을 찾을 수 없습니다."
                )

            logger.info(f"주문 정정 성공: 주문번호 {request.order_number}")

            return OrderResponse(
                success=True,
                order_number=request.order_number,
                status=OrderStatus.ACCEPTED,
                message="주문이 성공적으로 정정되었습니다.",
                stock_code=request.stock_code,
                quantity=request.quantity,
                price=adjusted_price,
                order_time=datetime.now()
            )

        except Exception as e:
            logger.error(f"주문 정정 중 오류 발생: {str(e)}", exc_info=True)
            return OrderResponse(
                success=False,
                order_number=request.order_number,
                status=OrderStatus.REJECTED,
                message=f"주문 정정 중 오류가 발생했습니다: {str(e)}"
            )

    async def cancel_order(self, request: OrderCancelRequest) -> OrderResponse:
        """
        주문 취소

        Args:
            request: 주문 취소 요청 데이터

        Returns:
            OrderResponse: 주문 응답
        """
        try:
            logger.info(f"주문 취소 시작: 주문번호 {request.order_number}")

            # TODO: 실제 API 연동 필요
            # 현재는 한국투자증권 API에 취소 메서드가 없으므로 mock 응답

            # 미체결 주문 목록에서 제거
            order_to_cancel = None
            for i, order in enumerate(self._pending_orders):
                if order.order_number == request.order_number:
                    order_to_cancel = self._pending_orders.pop(i)
                    order_to_cancel.order_status = OrderStatus.CANCELLED
                    # 취소된 주문은 체결 내역으로 이동
                    self._order_history.append(order_to_cancel)
                    break

            if not order_to_cancel:
                return OrderResponse(
                    success=False,
                    order_number=request.order_number,
                    status=OrderStatus.REJECTED,
                    message="취소할 주문을 찾을 수 없습니다."
                )

            logger.info(f"주문 취소 성공: 주문번호 {request.order_number}")

            return OrderResponse(
                success=True,
                order_number=request.order_number,
                status=OrderStatus.CANCELLED,
                message="주문이 성공적으로 취소되었습니다.",
                stock_code=order_to_cancel.stock_code,
                stock_name=order_to_cancel.stock_name,
                order_time=datetime.now()
            )

        except Exception as e:
            logger.error(f"주문 취소 중 오류 발생: {str(e)}", exc_info=True)
            return OrderResponse(
                success=False,
                order_number=request.order_number,
                status=OrderStatus.REJECTED,
                message=f"주문 취소 중 오류가 발생했습니다: {str(e)}"
            )

    async def get_pending_orders(self, stock_code: Optional[str] = None) -> PendingOrdersResponse:
        """
        미체결 주문 조회

        Args:
            stock_code: 종목 코드 (선택, None이면 전체 조회)

        Returns:
            PendingOrdersResponse: 미체결 주문 목록
        """
        try:
            logger.info(f"미체결 주문 조회: {stock_code or '전체'}")

            # TODO: 실제 API 연동 필요
            # 현재는 메모리에 저장된 주문 목록 반환

            filtered_orders = self._pending_orders
            if stock_code:
                filtered_orders = [
                    order for order in self._pending_orders
                    if order.stock_code == stock_code
                ]

            return PendingOrdersResponse(
                success=True,
                message="미체결 주문 조회 성공",
                orders=filtered_orders,
                total_count=len(filtered_orders)
            )

        except Exception as e:
            logger.error(f"미체결 주문 조회 중 오류 발생: {str(e)}", exc_info=True)
            return PendingOrdersResponse(
                success=False,
                message=f"미체결 주문 조회 중 오류가 발생했습니다: {str(e)}",
                orders=[],
                total_count=0
            )

    async def get_order_history(
        self,
        stock_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> OrderHistoryResponse:
        """
        체결 내역 조회

        Args:
            stock_code: 종목 코드 (선택)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            OrderHistoryResponse: 체결 내역 목록
        """
        try:
            logger.info(f"체결 내역 조회: {stock_code or '전체'}, {start_date} ~ {end_date}")

            # TODO: 실제 API 연동 필요
            # 현재는 메모리에 저장된 체결 내역 반환

            filtered_orders = self._order_history
            if stock_code:
                filtered_orders = [
                    order for order in filtered_orders
                    if order.stock_code == stock_code
                ]

            # 통계 계산
            total_buy_amount = sum(
                order.filled_amount for order in filtered_orders
                if order.order_side == OrderSide.BUY and order.order_status == OrderStatus.FILLED
            )
            total_sell_amount = sum(
                order.filled_amount for order in filtered_orders
                if order.order_side == OrderSide.SELL and order.order_status == OrderStatus.FILLED
            )
            total_commission = sum(order.commission for order in filtered_orders)
            total_tax = sum(order.tax for order in filtered_orders)

            return OrderHistoryResponse(
                success=True,
                message="체결 내역 조회 성공",
                orders=filtered_orders,
                total_count=len(filtered_orders),
                total_buy_amount=total_buy_amount,
                total_sell_amount=total_sell_amount,
                total_commission=total_commission,
                total_tax=total_tax
            )

        except Exception as e:
            logger.error(f"체결 내역 조회 중 오류 발생: {str(e)}", exc_info=True)
            return OrderHistoryResponse(
                success=False,
                message=f"체결 내역 조회 중 오류가 발생했습니다: {str(e)}",
                orders=[],
                total_count=0,
                total_buy_amount=0,
                total_sell_amount=0,
                total_commission=0,
                total_tax=0
            )
