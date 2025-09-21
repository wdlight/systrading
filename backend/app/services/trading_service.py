"""
매매 서비스
자동매매 설정, 주문 처리 등 매매 관련 비즈니스 로직 처리
"""

from typing import List, Dict, Any, Optional
from utils.logger import logger
from datetime import datetime, timedelta
import json
import os

from app.models.watchlist_models import (
    TradingConditions, TradeExecutionResult, WatchlistItem, 
    BuyConditions, SellConditions, TechnicalIndicators
)
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.core.korea_invest import KoreaInvestAPIService


class TradingService:
    """매매 관련 서비스"""
    
    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest_service = korea_invest_service
        self.is_trading_active = False
        self.trading_start_time = None
        self.trading_conditions = None
        self.order_history = []
        self.trading_stats = {
            "total_trades": 0,
            "profit_trades": 0,
            "loss_trades": 0,
            "total_profit_loss": 0.0
        }
        
        # 설정 파일 경로
        self.settings_file = "trading_settings.json"
        self._load_settings()
    
    def _load_settings(self):
        """설정 파일에서 매매 조건 로드"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "trading_conditions" in data:
                        # dict를 Pydantic 모델로 변환
                        self.trading_conditions = TradingConditions(**data["trading_conditions"])
                        logger.info("매매 설정을 파일에서 로드했습니다.")
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {str(e)}")
        
        # 기본 설정 적용
        if not self.trading_conditions:
            self.trading_conditions = TradingConditions()
    
    def _save_settings(self):
        """설정을 파일에 저장"""
        try:
            data = {
                "trading_conditions": self.trading_conditions.dict() if self.trading_conditions else None,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {str(e)}")
    
    async def get_trading_conditions(self) -> TradingConditions:
        """현재 매매 조건 조회"""
        return self.trading_conditions
    
    async def update_trading_conditions(self, conditions: TradingConditions):
        """매매 조건 업데이트"""
        try:
            self.trading_conditions = conditions
            self._save_settings()
            logger.info("매매 조건이 업데이트되었습니다.")
            
        except Exception as e:
            logger.error(f"매매 조건 업데이트 실패: {str(e)}")
            raise
    
    async def start_trading(self) -> Dict[str, Any]:
        """자동매매 시작"""
        try:
            if self.is_trading_active:
                return {
                    "success": False,
                    "message": "자동매매가 이미 실행 중입니다."
                }
            
            if not self.trading_conditions:
                return {
                    "success": False,
                    "message": "매매 조건이 설정되지 않았습니다."
                }
            
            # 연결 상태 확인
            status = self.korea_invest_service.get_connection_status()
            if not status["connected"]:
                return {
                    "success": False,
                    "message": "한국투자증권 API가 연결되지 않았습니다."
                }
            
            self.is_trading_active = True
            self.trading_start_time = datetime.now()
            
            logger.info("자동매매가 시작되었습니다.")
            
            return {
                "success": True,
                "message": "자동매매가 시작되었습니다.",
                "start_time": self.trading_start_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"자동매매 시작 실패: {str(e)}")
            return {
                "success": False,
                "message": f"자동매매 시작 실패: {str(e)}"
            }
    
    async def stop_trading(self) -> Dict[str, Any]:
        """자동매매 중지"""
        try:
            if not self.is_trading_active:
                return {
                    "success": False,
                    "message": "자동매매가 실행되지 않고 있습니다."
                }
            
            self.is_trading_active = False
            
            logger.info("자동매매가 중지되었습니다.")
            
            return {
                "success": True,
                "message": "자동매매가 중지되었습니다."
            }
            
        except Exception as e:
            logger.error(f"자동매매 중지 실패: {str(e)}")
            return {
                "success": False,
                "message": f"자동매매 중지 실패: {str(e)}"
            }
    
    async def get_trading_status(self) -> Dict[str, Any]:
        """매매 상태 조회"""
        return {
            "is_running": self.is_trading_active,
            "start_time": self.trading_start_time.isoformat() if self.trading_start_time else None,
            "total_trades": self.trading_stats["total_trades"],
            "profit_trades": self.trading_stats["profit_trades"],
            "loss_trades": self.trading_stats["loss_trades"],
            "auto_trading_enabled": self.trading_conditions.auto_trading_enabled if self.trading_conditions else False
        }
    
    async def check_buy_conditions(self, stock_code: str, analysis_result: Dict[str, Any]) -> bool:
        """
        매수 조건 체크
        PyQt5의 매수 조건 체크 로직과 동일
        """
        try:
            if not self.trading_conditions.buy_conditions.enabled:
                return False
            
            # 기술적 지표 기반 매매 신호 체크
            signals = TechnicalAnalysisService.get_trading_signals(
                analysis_result,
                self.trading_conditions.buy_conditions.dict(),
                self.trading_conditions.sell_conditions.dict()
            )
            
            return signals.get('buy_signal', False)
            
        except Exception as e:
            logger.error(f"매수 조건 체크 실패 ({stock_code}): {str(e)}")
            return False
    
    async def check_sell_conditions(self, stock_code: str, analysis_result: Dict[str, Any], 
                                  current_item: WatchlistItem) -> bool:
        """
        매도 조건 체크
        PyQt5의 매도 조건 체크 로직과 동일
        """
        try:
            if not self.trading_conditions.sell_conditions.enabled:
                return False
            
            # 기술적 지표 기반 매매 신호 체크
            signals = TechnicalAnalysisService.get_trading_signals(
                analysis_result,
                self.trading_conditions.buy_conditions.dict(),
                self.trading_conditions.sell_conditions.dict()
            )
            
            # 기술적 지표 조건
            tech_signal = signals.get('sell_signal', False)
            
            # 수익률 조건 체크
            profit_condition = self._check_profit_conditions(current_item)
            
            # 트레일링스탑 조건 체크
            trailing_stop_condition = self._check_trailing_stop(current_item)
            
            return tech_signal or profit_condition or trailing_stop_condition
            
        except Exception as e:
            logger.error(f"매도 조건 체크 실패 ({stock_code}): {str(e)}")
            return False
    
    def _check_profit_conditions(self, item: WatchlistItem) -> bool:
        """수익률 기반 매도 조건 체크"""
        try:
            # 목표 수익률 달성
            if (self.trading_conditions.sell_conditions.profit_target and 
                item.profit_rate and 
                item.profit_rate >= self.trading_conditions.sell_conditions.profit_target):
                logger.info(f"목표 수익률 달성: {item.profit_rate}% >= {self.trading_conditions.sell_conditions.profit_target}%")
                return True
            
            # 손절매 조건
            if (self.trading_conditions.sell_conditions.stop_loss and 
                item.profit_rate and 
                item.profit_rate <= -self.trading_conditions.sell_conditions.stop_loss):
                logger.info(f"손절매 조건: {item.profit_rate}% <= -{self.trading_conditions.sell_conditions.stop_loss}%")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"수익률 조건 체크 실패: {str(e)}")
            return False
    
    def _check_trailing_stop(self, item: WatchlistItem) -> bool:
        """트레일링스탑 조건 체크"""
        try:
            if not self.trading_conditions.trailing_stop.enabled:
                return False
            
            # 트레일링스탑 발동 조건 (수익률 기준)
            if (not item.trailing_stop_active and 
                item.profit_rate and 
                item.profit_rate >= self.trading_conditions.trailing_stop.activation_rate):
                
                # 트레일링스탑 발동
                logger.info(f"트레일링스탑 발동: 수익률 {item.profit_rate}%")
                return False  # 발동만 하고 매도하지는 않음
            
            # 트레일링스탑 매도 조건
            if (item.trailing_stop_active and 
                item.trailing_stop_high and 
                item.current_price):
                
                # 고점 대비 하락률 계산
                drop_rate = (item.trailing_stop_high - item.current_price) / item.trailing_stop_high * 100
                
                if drop_rate >= self.trading_conditions.trailing_stop.trailing_rate:
                    logger.info(f"트레일링스탑 매도 조건: 고점 대비 {drop_rate}% 하락")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"트레일링스탑 조건 체크 실패: {str(e)}")
            return False
    
    async def execute_buy_order(self, stock_code: str, analysis_result: Dict[str, Any]) -> TradeExecutionResult:
        """
        매수 주문 실행
        PyQt5의 매수 로직과 동일
        """
        try:
            # 매수 조건 재확인
            if not await self.check_buy_conditions(stock_code, analysis_result):
                return TradeExecutionResult(
                    success=False,
                    message="매수 조건이 충족되지 않음"
                )
            
            # 매수 금액 계산
            buy_amount = self.trading_conditions.buy_conditions.amount
            current_price = analysis_result.get('current_price', 0)
            
            if current_price <= 0:
                return TradeExecutionResult(
                    success=False,
                    message="유효하지 않은 현재가"
                )
            
            # 주문 수량 계산
            quantity = int(buy_amount / current_price)
            
            if quantity <= 0:
                return TradeExecutionResult(
                    success=False,
                    message="매수 수량이 0 이하"
                )
            
            # API를 통한 실제 매수 주문 실행
            order_result = await self.korea_invest_service.place_buy_order(
                stock_code=stock_code,
                quantity=quantity,
                price=current_price  # 시장가 주문
            )
            
            if order_result and order_result.get('success'):
                logger.info(f"매수 주문 성공 - 종목: {stock_code}, 수량: {quantity}, 가격: {current_price}")
                
                # 실행 기록 저장
                self._add_order_record("매수", {
                    'stock_code': stock_code,
                    'quantity': quantity,
                    'price': current_price
                }, order_result)
                
                return TradeExecutionResult(
                    success=True,
                    order_id=order_result.get('order_id'),
                    message=f"매수 주문 성공: {quantity}주 @ {current_price}원"
                )
            else:
                return TradeExecutionResult(
                    success=False,
                    message=f"매수 주문 실패: {order_result.get('message', '알 수 없는 오류')}"
                )
            
        except Exception as e:
            logger.error(f"매수 주문 실행 실패 ({stock_code}): {str(e)}")
            return TradeExecutionResult(
                success=False,
                message=f"매수 주문 실행 실패: {str(e)}"
            )
    
    async def execute_sell_order(self, stock_code: str, item: WatchlistItem) -> TradeExecutionResult:
        """
        매도 주문 실행
        PyQt5의 매도 로직과 동일
        """
        try:
            if item.quantity <= 0:
                return TradeExecutionResult(
                    success=False,
                    message="보유 수량이 0 이하"
                )
            
            # API를 통한 실제 매도 주문 실행
            order_result = await self.korea_invest_service.place_sell_order(
                stock_code=stock_code,
                quantity=item.quantity,
                price=item.current_price  # 시장가 주문
            )
            
            if order_result and order_result.get('success'):
                logger.info(f"매도 주문 성공 - 종목: {stock_code}, 수량: {item.quantity}, 가격: {item.current_price}")
                
                # 실행 기록 저장
                self._add_order_record("매도", {
                    'stock_code': stock_code,
                    'quantity': item.quantity,
                    'price': item.current_price,
                    'profit_rate': item.profit_rate
                }, order_result)
                
                return TradeExecutionResult(
                    success=True,
                    order_id=order_result.get('order_id'),
                    message=f"매도 주문 성공: {item.quantity}주 @ {item.current_price}원 (수익률: {item.profit_rate}%)"
                )
            else:
                return TradeExecutionResult(
                    success=False,
                    message=f"매도 주문 실패: {order_result.get('message', '알 수 없는 오류')}"
                )
            
        except Exception as e:
            logger.error(f"매도 주문 실행 실패 ({stock_code}): {str(e)}")
            return TradeExecutionResult(
                success=False,
                message=f"매도 주문 실행 실패: {str(e)}"
            )
    
    def _add_order_record(self, order_type: str, order: Dict[str, Any], result: Dict[str, Any]):
        """주문 기록 추가"""
        try:
            record = {
                "order_type": order_type,
                "stock_code": order.get('stock_code'),
                "quantity": order.get('quantity'),
                "price": order.get('price'),
                "profit_rate": order.get('profit_rate'),
                "order_time": datetime.now().isoformat(),
                "result": result
            }
            
            self.order_history.append(record)
            self.trading_stats["total_trades"] += 1
            
            # 메모리 관리를 위해 최근 1000개만 유지
            if len(self.order_history) > 1000:
                self.order_history = self.order_history[-1000:]
                
        except Exception as e:
            logger.error(f"주문 기록 추가 실패: {str(e)}")
    
    async def get_order_history(self, limit: int = 50) -> List[OrderHistory]:
        """주문 내역 조회"""
        try:
            # 최근 주문 내역 반환
            recent_orders = self.order_history[-limit:] if limit > 0 else self.order_history
            
            history = []
            for record in reversed(recent_orders):  # 최신 순으로 정렬
                order_history = OrderHistory(
                    order_id=record.get("result", {}).get("data", {}).get("order_id", "N/A"),
                    stock_code=record["stock_code"],
                    stock_name="",  # 실제로는 종목명 조회 필요
                    order_type=record["order_type"],
                    quantity=record["quantity"],
                    price=record["price"],
                    executed_quantity=0,  # 실제 체결 정보 필요
                    executed_price=0,     # 실제 체결 정보 필요
                    status="접수",         # 실제 주문 상태 확인 필요
                    order_time=datetime.fromisoformat(record["order_time"])
                )
                history.append(order_history)
            
            return history
            
        except Exception as e:
            logger.error(f"주문 내역 조회 실패: {str(e)}")
            return []
    
    async def get_pending_orders(self) -> List[OrderHistory]:
        """미체결 주문 조회"""
        try:
            # 실제로는 한국투자증권 API에서 미체결 주문을 조회해야 함
            # 여기서는 기본 구조만 제공
            return []
            
        except Exception as e:
            logger.error(f"미체결 주문 조회 실패: {str(e)}")
            return []
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """주문 취소"""
        try:
            # 실제로는 한국투자증권 API에서 주문을 취소해야 함
            # 여기서는 기본 구조만 제공
            return {
                "success": False,
                "message": "주문 취소 기능이 구현되지 않았습니다."
            }
            
        except Exception as e:
            logger.error(f"주문 취소 실패: {str(e)}")
            return {
                "success": False,
                "message": f"주문 취소 실패: {str(e)}"
            }
    
    async def get_trading_performance(self, days: int = 30) -> Dict[str, Any]:
        """매매 성과 조회"""
        try:
            # 지정된 기간의 거래 내역 분석
            cutoff_date = datetime.now() - timedelta(days=days)
            
            recent_trades = [
                record for record in self.order_history
                if datetime.fromisoformat(record["order_time"]) >= cutoff_date
            ]
            
            total_trades = len(recent_trades)
            buy_trades = len([t for t in recent_trades if t["order_type"] == "매수"])
            sell_trades = len([t for t in recent_trades if t["order_type"] == "매도"])
            
            return {
                "period_days": days,
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "profit_trades": self.trading_stats["profit_trades"],
                "loss_trades": self.trading_stats["loss_trades"],
                "total_profit_loss": self.trading_stats["total_profit_loss"],
                "win_rate": (self.trading_stats["profit_trades"] / max(1, total_trades)) * 100,
                "is_trading_active": self.is_trading_active,
                "trading_start_time": self.trading_start_time.isoformat() if self.trading_start_time else None
            }
            
        except Exception as e:
            logger.error(f"매매 성과 조회 실패: {str(e)}")
            return {
                "error": f"매매 성과 조회 실패: {str(e)}"
            }