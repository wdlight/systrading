"""
계좌 서비스
계좌 잔고, 보유 종목 등 계좌 관련 비즈니스 로직 처리
"""

from typing import List, Optional, Dict, Any
from utils.logger import logger
from datetime import datetime

from app.models.schemas import AccountBalance, AccountSummary, Position
from app.core.korea_invest import KoreaInvestAPIService

logger = logging.getLogger(__name__)

class AccountService:
    """계좌 관련 서비스"""
    
    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest_service = korea_invest_service
        self.last_update = None
        self.cached_balance = None
        
    async def get_balance(self) -> AccountBalance:
        """계좌 잔고 조회"""
        try:
            balance_data = await self.korea_invest_service.get_account_balance()
            
            if not balance_data or not isinstance(balance_data, dict):
                raise Exception("계좌 잔고 데이터를 가져올 수 없습니다.")
            
            if "total_value" not in balance_data:
                raise Exception("잘못된 계좌 데이터 형식입니다.")
            
            # 요약 정보 생성
            summary = AccountSummary(
                account_number=self.korea_invest_service.settings.KI_ACCOUNT_NUMBER,
                total_asset=balance_data["total_value"],
                total_evaluation=balance_data["total_value"],
                available_cash=balance_data.get("available_cash", 0),
                total_profit_loss=balance_data.get("total_unrealized_pnl", 0) or sum(pos.get("unrealized_pnl", 0) for pos in balance_data.get("positions", [])),
                total_profit_rate=self._calculate_total_profit_rate(balance_data)
            )
            
            # 포지션 정보 변환
            positions = []
            for pos_data in balance_data["positions"]:
                position = Position(
                    stock_code=pos_data["stock_code"],
                    stock_name=pos_data["stock_name"],
                    quantity=pos_data["quantity"],
                    sellable_quantity=pos_data["sellable_quantity"],
                    avg_price=pos_data["avg_price"],
                    current_price=pos_data["current_price"],
                    unrealized_pnl=pos_data["unrealized_pnl"],
                    profit_rate=pos_data["profit_rate"],
                    day_change=pos_data["day_change"],
                    day_change_rate=pos_data["day_change_rate"]
                )
                positions.append(position)
            
            account_balance = AccountBalance(
                summary=summary,
                positions=positions
            )
            
            # 캐시 업데이트
            self.cached_balance = account_balance
            self.last_update = datetime.now()
            
            return account_balance
            
        except Exception as e:
            logger.error(f"계좌 잔고 조회 실패: {str(e)}")
            raise
    
    async def get_summary(self) -> AccountSummary:
        """계좌 요약 정보만 조회"""
        balance = await self.get_balance()
        return balance.summary
    
    async def get_positions(self) -> List[Position]:
        """보유 종목 목록 조회"""
        balance = await self.get_balance()
        return balance.positions
    
    async def get_position_by_stock(self, stock_code: str) -> Optional[Position]:
        """특정 종목의 포지션 조회"""
        positions = await self.get_positions()
        
        for position in positions:
            if position.stock_code == stock_code:
                return position
        
        return None
    
    async def refresh_account_info(self) -> bool:
        """계좌 정보 강제 갱신"""
        try:
            # 캐시 무효화
            self.cached_balance = None
            self.last_update = None
            
            # 새로운 데이터 조회
            await self.get_balance()
            
            logger.info("계좌 정보가 갱신되었습니다.")
            return True
            
        except Exception as e:
            logger.error(f"계좌 정보 갱신 실패: {str(e)}")
            return False
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """계좌 연결 상태 확인"""
        try:
            status = self.korea_invest_service.get_connection_status()
            
            return {
                "connected": status["connected"],
                "last_update": self.last_update.isoformat() if self.last_update else None,
                "account_number": self.korea_invest_service.settings.KI_ACCOUNT_NUMBER,
                "last_error": status.get("last_error")
            }
            
        except Exception as e:
            logger.error(f"연결 상태 확인 실패: {str(e)}")
            return {
                "connected": False,
                "last_update": None,
                "account_number": None,
                "last_error": str(e)
            }
    
    def get_cached_balance(self) -> Optional[AccountBalance]:
        """캐시된 잔고 정보 반환"""
        return self.cached_balance
    
    def _calculate_total_profit_rate(self, balance_data: Dict[str, Any]) -> float:
        """전체 수익률 계산"""
        total_value = balance_data.get("total_value", 0)
        total_pnl = balance_data.get("total_unrealized_pnl", 0)
        
        if total_value > 0 and total_pnl != 0:
            invested_amount = total_value - total_pnl
            if invested_amount > 0:
                return round((total_pnl / invested_amount) * 100, 2)
        
        return 0.0