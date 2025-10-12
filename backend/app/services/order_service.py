"""
주문 서비스
사용자 수동 매매 주문 처리 로직
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import pandas as pd
from loguru import logger
from fastapi import HTTPException

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
    """주문 서비스 클래스 (API 연동)"""

    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest = korea_invest_service

    async def place_buy_order(self, request: OrderRequest) -> OrderResponse:
        """매수 주문 (유효성 검증, 응답 파싱, 에러 처리 강화)"""
        if request.order_type == OrderType.LIMIT.value and (request.price is None or request.price <= 0):
            return OrderResponse(success=False, status="rejected", message="지정가 주문은 반드시 0보다 큰 가격을 입력해야 합니다.")
        
        try:
            adjusted_price = adjust_price_to_tick(request.price) if request.order_type == OrderType.LIMIT.value else 0

            api_response_obj = await self.korea_invest.buy_order(
                stock_code=request.stock_code,
                order_qty=request.quantity,
                order_price=adjusted_price,
                order_type="00" if request.order_type == OrderType.LIMIT.value else "01"
            )
            
            if not api_response_obj or not api_response_obj.is_ok():
                body = api_response_obj.get_body() if api_response_obj else None
                error_message = getattr(body, 'msg1', 'API 호출에 실패했습니다.') if body else "API 응답 없음"
                logger.warning(f"매수 주문 실패: {error_message} (stock_code: {request.stock_code})")
                
                user_message = error_message
                if "잔고" in error_message:
                    user_message = "증거금 또는 잔고가 부족합니다."
                
                return OrderResponse(success=False, status="rejected", message=user_message)

            response_body = api_response_obj.get_body()
            order_number = getattr(response_body.output, 'ODNO', None) if hasattr(response_body, 'output') else None
            
            return OrderResponse(
                success=True, status="accepted", order_number=order_number,
                message="매수 주문이 정상적으로 접수되었습니다."
            )
        except Exception as e:
            logger.error(f"place_buy_order 시스템 오류: {e}", exc_info=True)
            return OrderResponse(success=False, status="rejected", message=f"시스템 오류가 발생했습니다: {e}")

    async def place_sell_order(self, request: OrderRequest) -> OrderResponse:
        """매도 주문 (유효성 검증, 응답 파싱, 에러 처리 강화)"""
        if request.order_type == OrderType.LIMIT.value and (request.price is None or request.price <= 0):
            return OrderResponse(success=False, status="rejected", message="지정가 주문은 반드시 0보다 큰 가격을 입력해야 합니다.")

        try:
            adjusted_price = adjust_price_to_tick(request.price) if request.order_type == OrderType.LIMIT.value else 0

            api_response_obj = await self.korea_invest.sell_order(
                stock_code=request.stock_code,
                order_qty=request.quantity,
                order_price=adjusted_price,
                order_type="00" if request.order_type == OrderType.LIMIT.value else "01"
            )

            if not api_response_obj or not api_response_obj.is_ok():
                body = api_response_obj.get_body() if api_response_obj else None
                error_message = getattr(body, 'msg1', 'API 호출에 실패했습니다.') if body else "API 응답 없음"
                logger.warning(f"매도 주문 실패: {error_message} (stock_code: {request.stock_code})")
                
                user_message = error_message
                if "잔고" in error_message or "수량" in error_message:
                    user_message = "보유 수량이 부족합니다."

                return OrderResponse(success=False, status="rejected", message=user_message)

            response_body = api_response_obj.get_body()
            order_number = getattr(response_body.output, 'ODNO', None) if hasattr(response_body, 'output') else None

            return OrderResponse(
                success=True, status="accepted", order_number=order_number,
                message="매도 주문이 정상적으로 접수되었습니다."
            )
        except Exception as e:
            logger.error(f"place_sell_order 시스템 오류: {e}", exc_info=True)
            return OrderResponse(success=False, status="rejected", message=f"시스템 오류가 발생했습니다: {e}")

    def _parse_order_df(self, df: pd.DataFrame, is_history: bool) -> List[OrderDetail]:
        """주문/체결내역 DataFrame을 OrderDetail 리스트로 파싱"""
        orders = []
        if df is None or df.empty:
            return orders

        df = df.astype(object).where(pd.notnull(df), None) # NaN을 None으로 변환
        records = df.to_dict('records')

        for item in records:
            try:
                # 시간 파싱
                ord_dt_str = item.get('ord_dt')
                ord_tmd_str = item.get('ord_tmd')
                ccld_tmd_str = item.get('ccld_tmd')

                order_time = None
                if ord_dt_str and ord_tmd_str:
                    order_time = datetime.strptime(f"{ord_dt_str} {ord_tmd_str}", "%Y%m%d %H%M%S")
                elif ord_tmd_str: # 미체결 내역은 오늘 날짜 사용
                    order_time = datetime.strptime(f"{date.today()} {ord_tmd_str}", "%Y-%m-%d %H%M%S")
                else:
                    order_time = datetime.now()

                filled_time = None
                if ord_dt_str and ccld_tmd_str:
                    filled_time = datetime.strptime(f"{ord_dt_str} {ccld_tmd_str}", "%Y%m%d %H%M%S")

                # 수량/가격 숫자 변환
                order_price = int(float(item.get('ord_unpr', 0) or 0))
                order_qty = int(float(item.get('ord_qty', 0) or 0))
                filled_qty = int(float(item.get('tot_ccld_qty', 0) or 0))
                filled_price = int(float(item.get('avg_prvs', 0) or 0))

                # 기본 필드 보정
                item['ord_unpr'] = order_price
                item['ord_qty'] = order_qty
                item['tot_ccld_qty'] = filled_qty
                item['avg_prvs'] = filled_price if filled_price > 0 else None
                item['rmn_qty'] = int(float(item.get('rmn_qty', order_qty - filled_qty) or 0))

                if item['rmn_qty'] < 0:
                    item['rmn_qty'] = 0

                total_filled_amount = filled_price * filled_qty
                item['tot_ccld_amt'] = total_filled_amount
                item['fee'] = int(float(item.get('fee', 0) or 0))
                item['tax'] = int(float(item.get('tax', 0) or 0))

                # 데이터 가공
                item['order_side'] = 'buy' if item.get('sll_buy_dvsn_cd') == '02' else 'sell'
                item['order_time'] = order_time
                item['filled_time'] = filled_time
                item['order_amount'] = order_price * order_qty
                
                if is_history:
                    item['order_status'] = OrderStatus.FILLED
                else:
                    item['order_status'] = OrderStatus.PARTIAL if int(item.get('tot_ccld_qty', 0)) > 0 else OrderStatus.ACCEPTED

                # 모델 생성
                order_detail = OrderDetail.parse_obj(item)
                orders.append(order_detail)
            except (ValueError, TypeError) as e:
                logger.warning(f"주문 내역 항목 파싱 오류: {e}, 항목: {item}")
                continue
        return orders

    async def get_pending_orders(self, stock_code: Optional[str]) -> PendingOrdersResponse:
        """미체결 주문 조회 (실제 API 연동 및 파싱)"""
        try:
            df = await self.korea_invest.inquire_pending_orders(stock_code or "")
            orders = self._parse_order_df(df, is_history=False)
            return PendingOrdersResponse(success=True, message="미체결 주문 조회 성공", orders=orders, total_count=len(orders))
        except Exception as e:
            logger.error(f"get_pending_orders 처리 중 오류: {e}", exc_info=True)
            return PendingOrdersResponse(success=False, message=f"미체결 내역 조회 중 서버 오류 발생: {e}", orders=[], total_count=0)

    async def get_order_history(
        self,
        stock_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> OrderHistoryResponse:
        """체결 내역 조회 (실제 API 연동)"""
        try:
            s_date = start_date or (datetime.now() - pd.Timedelta(days=7)).strftime('%Y%m%d')
            e_date = end_date or datetime.now().strftime('%Y%m%d')
            
            df = await self.korea_invest.inquire_order_history(start_date=s_date, end_date=e_date, stock_code=stock_code or "")
            orders = self._parse_order_df(df, is_history=True)
            return OrderHistoryResponse(success=True, message="체결 내역 조회 성공", orders=orders, total_count=len(orders))
        except Exception as e:
            logger.error(f"get_order_history 처리 중 오류: {e}", exc_info=True)
            return OrderHistoryResponse(success=False, message=f"체결 내역 조회 중 서버 오류 발생: {e}", orders=[], total_count=0)

    async def modify_order(self, request: OrderModifyRequest) -> OrderResponse:
        """주문 정정 (미체결 조회 후 실행)"""
        try:
            pending_orders_resp = await self.get_pending_orders(stock_code=request.stock_code)
            if not pending_orders_resp.success:
                return OrderResponse(success=False, status="rejected", message="정정할 미체결 주문을 조회하지 못했습니다.")

            target_order = next(
                (
                    o
                    for o in pending_orders_resp.orders
                    if o.order_number == request.order_number or o.org_order_no == request.order_number
                ),
                None
            )

            if not target_order or not target_order.branch_code:
                return OrderResponse(success=False, status="rejected", message=f"정정할 주문(원주문번호: {request.order_number})을 찾을 수 없거나, 주문 정보(지점코드)가 부족합니다.")

            adjusted_price = adjust_price_to_tick(request.price)

            effective_org_order_no = target_order.org_order_no or target_order.order_number

            api_response_obj = await self.korea_invest.modify_order(
                branch_code=target_order.branch_code,
                org_order_no=effective_org_order_no,
                new_quantity=request.quantity,
                new_price=adjusted_price
            )

            if not api_response_obj or not api_response_obj.is_ok():
                body = api_response_obj.get_body() if api_response_obj else None
                error_message = getattr(body, 'msg1', 'API 호출에 실패했습니다.') if body else "API 응답 없음"
                logger.warning(f"주문 정정 실패: {error_message} (원주문번호: {request.order_number})")
                return OrderResponse(success=False, status="rejected", message=error_message)

            response_body = api_response_obj.get_body()
            order_number = getattr(response_body.output, 'ODNO', None) if hasattr(response_body, 'output') else None

            return OrderResponse(success=True, status="accepted", order_number=order_number, message="주문이 성공적으로 정정되었습니다.")
        except Exception as e:
            logger.error(f"modify_order 시스템 오류: {e}", exc_info=True)
            return OrderResponse(success=False, status="rejected", message=f"시스템 오류가 발생했습니다: {e}")

    async def cancel_order(self, request: OrderCancelRequest) -> OrderResponse:
        """주문 취소 (미체결 조회 후 실행)"""
        try:
            pending_orders_resp = await self.get_pending_orders(stock_code=request.stock_code)
            if not pending_orders_resp.success:
                return OrderResponse(success=False, status="rejected", message="취소할 미체결 주문을 조회하지 못했습니다.")

            target_order = next(
                (
                    o
                    for o in pending_orders_resp.orders
                    if o.order_number == request.order_number or o.org_order_no == request.order_number
                ),
                None
            )

            if not target_order or not target_order.branch_code:
                return OrderResponse(success=False, status="rejected", message=f"취소할 주문(원주문번호: {request.order_number})을 찾을 수 없거나, 주문 정보(지점코드)가 부족합니다.")

            effective_org_order_no = target_order.org_order_no or target_order.order_number

            api_response_obj = await self.korea_invest.cancel_order(
                branch_code=target_order.branch_code,
                org_order_no=effective_org_order_no,
                cancel_quantity=request.quantity
            )

            if not api_response_obj or not api_response_obj.is_ok():
                body = api_response_obj.get_body() if api_response_obj else None
                error_message = getattr(body, 'msg1', 'API 호출에 실패했습니다.') if body else "API 응답 없음"
                logger.warning(f"주문 취소 실패: {error_message} (원주문번호: {request.order_number})")
                return OrderResponse(success=False, status="rejected", message=error_message)

            response_body = api_response_obj.get_body()
            order_number = getattr(response_body.output, 'ODNO', None) if hasattr(response_body, 'output') else None

            return OrderResponse(success=True, status="cancelled", order_number=order_number, message="주문이 성공적으로 취소되었습니다.")
        except Exception as e:
            logger.error(f"cancel_order 시스템 오류: {e}", exc_info=True)
            return OrderResponse(success=False, status="rejected", message=f"시스템 오류가 발생했습니다: {e}")
