"""
포트폴리오 분석 서비스 v2.0

✅ 실제 거래 내역 반영
✅ 정확한 현금 흐름 계산
✅ Frontend 타입 호환
"""

import asyncio
from typing import List, Dict, Literal, Tuple, Optional
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

from app.core.korea_invest import KoreaInvestAPIService
from app.services.account_service import AccountService
from app.services.benchmark_service import BenchmarkService
from app.services.trade_history_service import TradeHistoryService
from app.services.cash_flow_tracker import CashFlowTracker
from app.models.schemas import PortfolioHistoryPoint
from app.utils.trading_calendar import TradingCalendar


from app.services.snapshot_manager import SnapshotManager

class PortfolioAnalyticsService:
    """포트폴리오 분석 서비스"""

    def __init__(
        self,
        korea_invest_service: KoreaInvestAPIService,
        benchmark_service: BenchmarkService,
        snapshot_manager: Optional[SnapshotManager] = None
    ):
        self.korea_invest = korea_invest_service
        self.benchmark = benchmark_service
        self.trade_history = TradeHistoryService(korea_invest_service)
        self.cash_tracker = CashFlowTracker()
        self.snapshot_manager = snapshot_manager or SnapshotManager()

    async def get_portfolio_history(
        self,
        period: Literal["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"]
    ) -> List[PortfolioHistoryPoint]:
        """
        포트폴리오 시계열 데이터 조회 (v2.2: 벤치마크 기준)
        """
        logger.info(f"📊 Portfolio History: {period}")

        # 1. 기간 -> 날짜
        start_date, end_date = self._period_to_dates(period)
        logger.info(f"   조회 기간: {start_date.date()} ~ {end_date.date()}")

        # 2. 벤치마크 데이터 먼저 조회 (거래일의 기준)
        benchmark_df = await self.benchmark.get_kospi_history(start_date, end_date)
        if benchmark_df.empty:
            logger.error("벤치마크 데이터 조회 실패. 포트폴리오 이력을 계산할 수 없습니다.")
            return []
        
        trading_days = benchmark_df.index.to_pydatetime().tolist()
        benchmark_values = benchmark_df["종가"].astype(float).tolist()
        logger.info(f"   벤치마크 기준 거래일: {len(trading_days)}일")
        
        # trading_days 리스트가 비어있으면 더 이상 진행하지 않음
        if not trading_days:
            logger.warning("계산할 거래일이 없습니다.")
            return []

        # 실제 계산에 사용될 시작일과 종료일 업데이트
        start_date, end_date = trading_days[0], trading_days[-1]
        logger.info(f"   실제 계산 기간: {start_date.date()} ~ {end_date.date()}")

        # 3. 스냅샷 로드 시도
        baseline_snapshot = self.snapshot_manager.load_latest_snapshot(end_date)
        
        if baseline_snapshot:
            try:
                snapshot_date = datetime.strptime(baseline_snapshot['date'], "%Y-%m-%d")
                calendar = TradingCalendar()
                if not calendar.is_trading_day(snapshot_date):
                    snapshot_date = calendar.get_previous_trading_day(snapshot_date)
                
                if snapshot_date > start_date:
                    start_date = snapshot_date
                    logger.info(f"   스냅샷 사용. 계산 시작일 조정: {start_date.date()}")
            except (ValueError, KeyError):
                logger.warning("스냅샷 날짜 파싱 오류, 전체 기간 재계산")
                baseline_snapshot = None

        # 4. 현재 계좌 잔고 및 거래 내역 조회
        account_service = AccountService(self.korea_invest)
        balance = await account_service.get_balance()
        if not balance:
            logger.error("계좌 조회 실패")
            return []

        trades = await self.trade_history.get_trade_history(start_date, end_date)
        logger.info(f"   조회된 거래: {len(trades)}건")

        # 5. 기준 시점의 포지션과 현금 결정
        if baseline_snapshot:
            reconstructed = self.snapshot_manager.replay_from_snapshot(
                baseline_snapshot, trades, end_date
            )
            current_positions = reconstructed["positions"]
            current_cash = reconstructed["cash"]
            logger.info("   스냅샷으로부터 현재 상태 재구성 완료")
        else:
            current_positions = {p.stock_code: p.quantity for p in balance.positions}
            current_cash = balance.available_cash
            logger.info("   API로부터 현재 상태 사용")

        logger.info(f"   현재 상태: {len(current_positions)}개 종목, 현금 {current_cash:,.0f}원")

        # 6. 일별 포지션 및 현금 재구성
        daily_positions = self.trade_history.reconstruct_daily_positions(
            trades, current_positions, trading_days
        )
        daily_cash = self.cash_tracker.calculate_daily_cash(
            trades, current_cash, trading_days
        )

        # 7. 종목별 가격 조회
        stock_codes = set(key for d in daily_positions.values() for key in d)
        
        price_histories = await self._fetch_stock_histories(
            list(stock_codes), start_date, end_date
        )

        # 8. 일별 포트폴리오 가치 계산
        portfolio_values = []
        for date in trading_days:
            positions = daily_positions.get(date, {})
            cash = daily_cash.get(date, current_cash)

            total_value = cash
            for stock_code, quantity in positions.items():
                price = self._get_price_at_date(price_histories.get(stock_code), date)
                if price > 0:
                    total_value += price * quantity

            portfolio_values.append({"date": date, "value": total_value})
        
        if not portfolio_values:
            logger.error("포트폴리오 가치 계산 결과가 없습니다.")
            return []

        logger.info(
            f"   포트폴리오 가치: 시작 {portfolio_values[0]['value']:,.0f}원, 종료 {portfolio_values[-1]['value']:,.0f}원"
        )

        # 9. 벤치마크 정규화
        normalized_benchmark = self.benchmark.normalize_to_portfolio(
            benchmark_values, portfolio_values[0]["value"]
        )

        # 10. 결과 조합
        result = [
            PortfolioHistoryPoint(
                date=pv["date"].strftime("%Y-%m-%dT15:30:00+09:00"),
                portfolio=pv["value"],
                benchmark=bv
            )
            for pv, bv in zip(portfolio_values, normalized_benchmark)
        ]

        logger.info(f"✅ 최종 완료: {len(result)}개 데이터 포인트 생성")
        return result

    def _period_to_dates(
        self,
        period: Literal["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"]
    ) -> Tuple[datetime, datetime]:
        """기간 → (시작일, 종료일)"""
        calendar = TradingCalendar()
        end_date = datetime.now()

        # 오늘이 거래일이 아니면 마지막 거래일로 설정
        if not calendar.is_trading_day(end_date):
            end_date = calendar.get_previous_trading_day(end_date)
            logger.info(f"   오늘이 비거래일, 종료일을 마지막 거래일({end_date.date()})로 조정")

        if period == "1D":
            # 1D의 경우, 시작일을 종료일과 동일하게 설정하여 당일 데이터만 가져오도록 함
            start_date = end_date
        elif period == "1W":
            start_date = end_date - timedelta(weeks=1)
        elif period == "1M":
            start_date = end_date - timedelta(days=30)
        elif period == "3M":
            start_date = end_date - timedelta(days=90)
        elif period == "6M":
            start_date = end_date - timedelta(days=180)
        elif period == "1Y":
            start_date = end_date - timedelta(days=365)
        else:  # ALL
            start_date = end_date - timedelta(days=1095)  # 3년

        return start_date, end_date

    def _generate_trading_days(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[datetime]:
        """거래일 리스트 생성"""
        calendar = TradingCalendar()
        return calendar.get_trading_days(start_date, end_date)

    async def _fetch_stock_histories(
        self,
        stock_codes: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        종목별 가격 히스토리 병렬 조회 (최적화)

        ✅ Semaphore로 동시 요청을 5개로 제한하여 API 부하 방지
        """
        logger.info(f"종목별 가격 조회: {len(stock_codes)}개")
        semaphore = asyncio.Semaphore(5)

        async def fetch_one(stock_code: str):
            async with semaphore:
                try:
                    result = await self.korea_invest.get_daily_chart_data(
                        stock_code,
                        start_date.strftime("%Y%m%d"),
                        end_date.strftime("%Y%m%d")
                    )
                    logger.debug(f"✅ {stock_code} 조회 완료")

                    if isinstance(result, list):
                        from datetime import datetime
                        df = pd.DataFrame([
                            {
                                "일자": datetime.fromisoformat(c.timestamp).strftime("%Y%m%d") if isinstance(c.timestamp, str) else c.timestamp.strftime("%Y%m%d"),
                                "종가": c.close,
                                "시가": c.open,
                                "고가": c.high,
                                "저가": c.low,
                                "거래량": c.volume
                            }
                            for c in result
                        ]).set_index("일자")
                    else:
                        df = result

                    return stock_code, df
                except Exception as e:
                    logger.error(f"{stock_code} 조회 실패: {e}")
                    return stock_code, None

        tasks = [fetch_one(code) for code in stock_codes]
        results = await asyncio.gather(*tasks)

        return {
            code: df
            for code, df in results
            if df is not None and not df.empty
        }

    def _get_price_at_date(
        self,
        price_history: Optional[pd.DataFrame],
        target_date: datetime
    ) -> float:
        """특정 날짜의 가격 조회"""
        if price_history is None or price_history.empty:
            return 0

        date_str = target_date.strftime("%Y%m%d")

        # 정확한 날짜 매칭
        if date_str in price_history.index:
            return float(price_history.loc[date_str, "종가"])

        # 가장 가까운 과거 날짜 찾기
        available_dates = [
            d for d in price_history.index
            if d <= date_str
        ]

        if not available_dates:
            return 0

        nearest_date = max(available_dates)
        return float(price_history.loc[nearest_date, "종가"])

    def _align_benchmark(
        self,
        benchmark_data: List[float],
        trading_days: List[datetime]
    ) -> List[float]:
        """
        벤치마크 데이터와 거래일 정렬

        ⚠️ 현재 구현: 단순 샘플링/패딩 (선형 보간 없음)
        기간이 길고 데이터가 촘촘하지 않은 경우 오차가 커질 수 있음

        TODO (Phase 2 권장):
        - 선형 보간(scipy.interpolate.interp1d) 추가
        - 이동 평균 스무딩 옵션 추가
        - 날짜 기반 정확한 매칭 (현재는 인덱스 기반)
        """
        if len(benchmark_data) == len(trading_days):
            return benchmark_data

        # 간단한 보간: 비율 맞춰서 샘플링
        if len(benchmark_data) > len(trading_days):
            step = len(benchmark_data) / len(trading_days)
            return [
                benchmark_data[int(i * step)]
                for i in range(len(trading_days))
            ]
        else:
            # 부족하면 마지막 값 복사
            return benchmark_data + [benchmark_data[-1]] * (len(trading_days) - len(benchmark_data))
