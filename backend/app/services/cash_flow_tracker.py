"""
현금 흐름 추적 서비스
"""

from typing import List, Dict
from datetime import datetime
from loguru import logger

from app.models.schemas import Trade


class CashFlowTracker:
    """현금 흐름 추적 및 계산"""

    def calculate_daily_cash(
        self,
        trades: List[Trade],
        current_cash: float,
        trading_days: List[datetime]
    ) -> Dict[datetime, float]:
        """
        거래 내역 기반 일별 현금 역산

        공식:
        - 매수: 현금 감소 (체결금액 + 수수료)
        - 매도: 현금 증가 (체결금액 - 수수료 - 세금)

        알고리즘:
        1. 종료일 = 현재 현금
        2. 거래일을 역순으로 순회
        3. 매수 → 과거 현금 = 현재 + (금액 + 수수료)
        4. 매도 → 과거 현금 = 현재 - (금액 - 수수료 - 세금)
        """
        logger.info(f"현금 흐름 계산: {len(trading_days)}일")

        # 거래를 날짜별로 그룹화
        trades_by_date = {}
        for trade in trades:
            date_str = trade.trade_date
            if date_str not in trades_by_date:
                trades_by_date[date_str] = []
            trades_by_date[date_str].append(trade)

        daily_cash = {}
        cash = current_cash

        # 거래일을 역순으로 순회
        for date in reversed(trading_days):
            date_str = date.strftime("%Y%m%d")

            # 현재 날짜의 현금 저장
            daily_cash[date] = cash

            # 해당 날짜의 거래가 있으면 역산
            if date_str in trades_by_date:
                for trade in trades_by_date[date_str]:
                    if trade.trade_type == "buy":
                        # 매수 → 과거 현금 = 현재 + (금액 + 수수료)
                        cash += (trade.amount + trade.fee)
                    else:
                        # 매도 → 과거 현금 = 현재 - (금액 - 수수료 - 세금)
                        cash -= (trade.amount - trade.fee - trade.tax)

        logger.info(f"✅ 현금 흐름 계산 완료")
        logger.info(f"   시작 현금: {cash:,.0f}원")
        logger.info(f"   종료 현금: {current_cash:,.0f}원")

        return daily_cash
