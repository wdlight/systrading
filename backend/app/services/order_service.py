"""
주문 서비스
사용자 수동 매매 주문 처리 로직
"""

from typing import Dict, Any, List, Optional
import os
from datetime import datetime, date
import pandas as pd
from loguru import logger
from fastapi import HTTPException
from pydantic import ValidationError

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
        """주문/체결내역 DataFrame을 OrderDetail 리스트로 파싱 (수정된 로직)"""
        orders = []
        if df is None or df.empty:
            return orders

        # 입력 DF의 메타 로깅 (환경 변수로 토글)
        ORDER_PARSER_DEBUG = os.getenv('ORDER_PARSER_DEBUG') == '1'
        if ORDER_PARSER_DEBUG:
            try:
                logger.info(
                    f"[주문파서] 입력 DataFrame 메타 | rows={len(df)} | columns={list(df.columns)} | dtypes={ {c: str(t) for c,t in df.dtypes.to_dict().items()} }"
                )
            except Exception:
                pass

        df = df.astype(object).where(pd.notnull(df), None)
        records = df.to_dict('records')

        def _safe_parse_time(
            date_str: Optional[str],
            time_str: Optional[str],
            *,
            required: bool
        ) -> Optional[datetime]:
            """API 응답의 날짜/시간 조합을 안전하게 datetime으로 변환"""
            if not time_str or str(time_str).strip() in ("0", "000000"):
                return datetime.now() if required else None

            time_token = str(time_str).strip().zfill(6)
            date_token = str(date_str).strip() if date_str else datetime.now().strftime("%Y%m%d")

            try:
                return datetime.strptime(f"{date_token}{time_token}", "%Y%m%d%H%M%S")
            except ValueError:
                return datetime.now() if required else None

        # 상세 로깅은 과도한 로그를 피하기 위해 최대 5건으로 제한
        max_debug_logs = 5
        debug_count = 0

        for item in records:
            try:
                # --- Gemini Modification v2 Start ---
                
                # 1. Raw 필드와 기본 가공 먼저 수행
                item['raw_filled_price'] = str(item.get('avg_prvs', ''))
                item['raw_filled_quantity'] = str(item.get('tot_ccld_qty', ''))
                item['raw_filled_amount'] = str(item.get('tot_ccld_amt', ''))
                item['raw_commission'] = str(item.get('fee', ''))
                item['raw_tax'] = str(item.get('tax', ''))
                item['raw_filled_time'] = str(item.get('ccld_tmd', ''))

                item['order_time'] = _safe_parse_time(item.get('ord_dt'), item.get('ord_tmd'), required=True)
                # filled_time 우선순위(요청사항): ord_tmd(체결시각으로 간주) > infm_tmd
                filled_time_token_src = None
                filled_time_token = None
                if item.get('ord_tmd'):
                    filled_time_token = item.get('ord_tmd')
                    filled_time_token_src = 'ord_tmd'
                elif item.get('infm_tmd'):
                    filled_time_token = item.get('infm_tmd')
                    filled_time_token_src = 'infm_tmd'
                item['filled_time'] = _safe_parse_time(item.get('ord_dt'), filled_time_token, required=False)
                item['order_side'] = 'buy' if item.get('sll_buy_dvsn_cd') == '02' else 'sell'
                item['order_status'] = OrderStatus.FILLED if is_history else (OrderStatus.PARTIAL if int(float(item.get('tot_ccld_qty', 0) or 0)) > 0 else OrderStatus.ACCEPTED)
                
                # 2. Pydantic 파싱 시도 (콤마 때문에 실패할 수 있음)
                try:
                    # 임시로 order_amount 필드를 채워둠 (validation 통과 목적)
                    item['order_amount'] = 0
                    order_detail = OrderDetail.parse_obj(item)
                except ValidationError:
                    # 3. 파싱 실패 시, 콤마 제거 후 재시도
                    numeric_fields = ['ord_qty', 'tot_ccld_qty', 'rmn_qty', 'ord_unpr', 'avg_prvs', 'tot_ccld_amt', 'fee', 'tax']
                    for field in numeric_fields:
                        if field in item and isinstance(item[field], str):
                            item[field] = item[field].replace(',', '')
                    order_detail = OrderDetail.parse_obj(item)

                # 4. 파싱 후 금액/수량 보정
                order_price = order_detail.order_price or 0
                order_qty = order_detail.quantity or 0
                order_detail.order_amount = order_price * order_qty

                if order_detail.filled_amount == 0 and order_detail.filled_price and order_detail.filled_quantity > 0:
                    order_detail.filled_amount = order_detail.filled_price * order_detail.filled_quantity

                # 시장가 주문(또는 가격 0으로 들어온 주문)의 최종 주문가를 체결가로 설정
                try:
                    if (order_detail.order_type == OrderType.MARKET.value or order_detail.order_price == 0) and (order_detail.filled_price is not None):
                        order_detail.order_price = int(order_detail.filled_price)
                        order_detail.order_amount = order_detail.order_price * order_qty
                except Exception:
                    # 타입 문제 등으로 실패 시 조용히 스킵
                    pass
                
                # 디버그 로깅 (상위 5건만, 환경 변수로 토글)
                if ORDER_PARSER_DEBUG and debug_count < max_debug_logs:
                    logger.info(
                        (
                            f"[주문파서] 파싱 샘플"
                            f" | stock={order_detail.stock_code}({order_detail.stock_name})"
                            f" | side={order_detail.order_side} | status={order_detail.order_status}"
                            f" | ord_qty={order_detail.quantity} @ {order_detail.order_price} => ord_amt={order_detail.order_amount}"
                            f" | filled_qty={order_detail.filled_quantity} @ {order_detail.filled_price} => filled_amt={order_detail.filled_amount}"
                            f" | ord_time={order_detail.order_time} | filled_time={order_detail.filled_time}"
                            f" | raw_times={item.get('ord_dt')} {item.get('ord_tmd')} / {filled_time_token} (src={filled_time_token_src})"
                        )
                    )
                    expected_filled_amt = (order_detail.filled_price or 0) * (order_detail.filled_quantity or 0)
                    if order_detail.filled_amount != expected_filled_amt:
                        logger.warning(
                            f"[주문파서] 체결금액 불일치: calc={expected_filled_amt} vs field={order_detail.filled_amount} | odno={order_detail.order_number}"
                        )
                    debug_count += 1

                orders.append(order_detail)
                # --- Gemini Modification v2 End ---

            except (ValueError, TypeError, ValidationError) as e:
                logger.warning(f"주문 내역 항목 파싱 오류: {e}, 항목: {item}")
                continue
        
        logger.info(
            "주문 내역 파싱 완료",
            extra={
                "is_history": is_history,
                "row_count": len(records),
                "parsed_count": len(orders),
                "failed_count": len(records) - len(orders),
            }
        )
        if orders:
            first_order = orders[0]
            last_order = orders[-1]
            logger.debug(
                "주문 내역 대표 샘플",
                extra={
                    "first_order": first_order.model_dump(),
                    "last_order": last_order.model_dump(),
                }
            )
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

            logger.info(
                "체결 내역 조회 요청",
                extra={
                    "stock_code": stock_code,
                    "start_date": s_date,
                    "end_date": e_date,
                }
            )

            df = await self.korea_invest.inquire_order_history(
                start_date=s_date,
                end_date=e_date,
                stock_code=stock_code or ""
            )

            if df is None:
                logger.warning("체결 내역 조회 결과: DataFrame 없음")
                return OrderHistoryResponse(success=True, message="체결 내역 없음", orders=[], total_count=0)

            row_count = len(df)
            logger.info(
                "체결 내역 원본 DataFrame 정보",
                extra={
                    "row_count": row_count,
                    "columns": list(df.columns),
                    "sample": df.head(5).to_dict(orient="records") if row_count > 0 else [],
                }
            )

            orders = self._parse_order_df(df, is_history=True)

            total_buy_amount = sum(
                order.filled_amount
                for order in orders
                if order.order_side == OrderSide.BUY.value
            )
            total_sell_amount = sum(
                order.filled_amount
                for order in orders
                if order.order_side == OrderSide.SELL.value
            )
            total_commission = sum(order.commission for order in orders)
            total_tax = sum(order.tax for order in orders)

            response = OrderHistoryResponse(
                success=True,
                message="체결 내역 조회 성공",
                orders=orders,
                total_count=len(orders),
                total_buy_amount=total_buy_amount,
                total_sell_amount=total_sell_amount,
                total_commission=total_commission,
                total_tax=total_tax,
            )
            logger.info(
                "체결 내역 요약",
                extra={
                    "stock_code": stock_code,
                    "total_count": response.total_count,
                    "total_buy_amount": response.total_buy_amount,
                    "total_sell_amount": response.total_sell_amount,
                    "total_commission": response.total_commission,
                    "total_tax": response.total_tax,
                }
            )
            if orders:
                def _to_sample(order: OrderDetail):
                    data = order.model_dump()
                    keys = [
                        "order_number",
                        "stock_code",
                        "stock_name",
                        "order_side",
                        "order_status",
                        "quantity",
                        "filled_quantity",
                        "remaining_quantity",
                        "order_price",
                        "filled_price",
                        "order_time",
                        "filled_time",
                    ]
                    return {k: data.get(k) for k in keys}

                sample_orders = [_to_sample(order) for order in orders[:5]]
                logger.info(
                    "체결 내역 샘플 데이터",
                    extra={
                        "stock_code": stock_code,
                        "sample_count": len(sample_orders),
                        "sample_orders": sample_orders,
                    }
                )
            else:
                logger.info(
                    "체결 내역 데이터 없음",
                    extra={
                        "stock_code": stock_code,
                    }
                )
            return response
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
