"""
거래 내역 수집 및 포지션 재구성 서비스
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

from app.core.korea_invest import KoreaInvestAPIService
from app.models.schemas import Trade, DailyPosition
from app.utils.trading_calendar import TradingCalendar


class TradeHistoryService:
    """거래 내역 수집 및 포지션 재구성"""

    def __init__(self, korea_invest_service: KoreaInvestAPIService):
        self.korea_invest = korea_invest_service

    async def get_trade_history(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Trade]:
        """
        한투 API로 거래 내역 조회

        TR_ID: TTTC8001R
        """
        logger.info(f"거래 내역 조회: {start_date.date()} ~ {end_date.date()}")

        try:
            result = await self.korea_invest.get_trade_history(
                start_date.strftime("%Y%m%d"),
                end_date.strftime("%Y%m%d")
            )

            if result is None or result.empty:
                logger.warning("거래 내역 없음")
                return []

            # ⚠️ 중요: result가 DataFrame인 경우 dict로 변환 필요
            # 현재 KoreaInvestAPI.get_daily_ccld()는 pandas DataFrame 반환
            if isinstance(result, pd.DataFrame):
                result = result.to_dict('records')

            trades = []
            for item in result:
                # 매도/매수 구분
                trade_type = "buy" if item["sll_buy_dvsn_cd"] == "02" else "sell"

                # 수수료/세금 계산
                fee = int(float(item.get("tot_ccld_amt", 0)) * 0.00015)  # 0.015%
                tax = 0
                if trade_type == "sell":
                    tax = int(float(item.get("tot_ccld_amt", 0)) * 0.0023)  # 0.23%

                trade = Trade(
                    trade_date=item["ord_dt"],
                    trade_time=item.get("ord_tmd", "000000"),  # ✅ 체결시각 추가
                    stock_code=item["pdno"],
                    stock_name=item["prdt_name"],
                    trade_type=trade_type,
                    quantity=int(item["tot_ccld_qty"]),
                    price=int(float(item["avg_prvs"])),
                    amount=int(float(item["tot_ccld_amt"])),
                    fee=fee,
                    tax=tax
                )
                trades.append(trade)

            logger.info(f"✅ 거래 내역: {len(trades)}건")
            return trades

        except Exception as e:
            logger.error(f"거래 내역 조회 실패: {e}")
            return []

    def reconstruct_daily_positions(
        self,
        trades: List[Trade],
        current_positions: Dict[str, int],  # {종목코드: 수량}
        trading_days: List[datetime]
    ) -> Dict[datetime, Dict[str, int]]:
        """
        거래 내역으로부터 일별 포지션 역산

        알고리즘:
        1. 종료일(가장 최근) = 현재 포지션
        2. 거래일을 역순으로 순회
        3. 매수 → 보유량 감소 (과거에는 없었음)
        4. 매도 → 보유량 증가 (과거에는 있었음)

        Example:
            현재: 삼성전자 100주
            10/10: 매수 10주 → 10/9에는 90주
            10/5: 매도 20주 → 10/4에는 110주
        """
        logger.info(f"포지션 재구성: {len(trading_days)}일")

        # 거래 내역을 날짜별로 그룹화
        trades_by_date = {}
        for trade in trades:
            date_str = trade.trade_date
            if date_str not in trades_by_date:
                trades_by_date[date_str] = []
            trades_by_date[date_str].append(trade)

        # ⚠️ 중요: 같은 날짜 내 거래는 체결 시간 기준 역순 정렬 필요
        # 역산 시 최신 거래부터 처리해야 정확한 포지션 복원 가능
        for date_str in trades_by_date:
            # 체결 시간(ord_tmd) 기준 내림차순 정렬
            # 예: ["153000", "120000", "100000"] → 최신부터 처리
            # Trade 모델에 trade_time 필드가 추가되어 있어야 함
            trades_by_date[date_str] = sorted(
                trades_by_date[date_str],
                key=lambda t: t.trade_time,  # 체결시각 기준
                reverse=True  # 역순 정렬 (최신 → 과거)
            )
            logger.debug(
                f"{date_str}: {len(trades_by_date[date_str])}건 거래 "
                f"(시간 범위: {trades_by_date[date_str][-1].trade_time} ~ "
                f"{trades_by_date[date_str][0].trade_time})"
            )

        # 일별 포지션 초기화
        daily_positions = {}
        current = current_positions.copy()

        # 거래일을 역순으로 순회 (미래 → 과거)
        for date in reversed(trading_days):
            date_str = date.strftime("%Y%m%d")

            # 현재 날짜의 포지션 저장
            daily_positions[date] = current.copy()

            # 해당 날짜의 거래가 있으면 역산 (최신 거래부터)
            if date_str in trades_by_date:
                for trade in trades_by_date[date_str]:
                    stock_code = trade.stock_code

                    if trade.trade_type == "buy":
                        # 매수 → 과거에는 없었음
                        current[stock_code] = current.get(stock_code, 0) - trade.quantity

                        # ⚠️ 주의: 수량이 음수가 되는 경우 처리
                        # 동일 종목의 과거 거래가 더 있다면 다시 더해질 수 있음
                        if current[stock_code] < 0:
                            logger.warning(
                                f"⚠️ {stock_code} 포지션 음수: {current[stock_code]}주 "
                                f"(거래: {trade.trade_date})"
                            )
                            # 옵션 1: 0으로 보정 (보수적)
                            # current[stock_code] = 0
                            # 옵션 2: 음수 유지 (과거 거래가 더 있을 경우 복원됨)
                            # 현재는 옵션 2 사용

                        if current[stock_code] <= 0 and stock_code in current:
                            del current[stock_code]
                    else:
                        # 매도 → 과거에는 있었음
                        current[stock_code] = current.get(stock_code, 0) + trade.quantity

        logger.info(f"✅ 포지션 재구성 완료")
        return daily_positions
