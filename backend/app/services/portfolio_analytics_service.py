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
from app.services.benchmark_service import BenchmarkService
from app.services.trade_history_service import TradeHistoryService
from app.services.cash_flow_tracker import CashFlowTracker
from app.models.schemas import PortfolioHistoryPoint
from app.utils.trading_calendar import TradingCalendar


class PortfolioAnalyticsService:
    """포트폴리오 분석 서비스"""

    def __init__(
        self,
        korea_invest_service: KoreaInvestAPIService,
        benchmark_service: BenchmarkService
    ):
        self.korea_invest = korea_invest_service
        self.benchmark = benchmark_service
        self.trade_history = TradeHistoryService(korea_invest_service)
        self.cash_tracker = CashFlowTracker()

    async def get_portfolio_history(
        self,
        period: Literal["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"]
    ) -> List[PortfolioHistoryPoint]:
        """
        포트폴리오 시계열 데이터 조회

        ✅ v2.0: 실제 거래 내역 반영
        """
        logger.info(f"📊 Portfolio History: {period}")

        # 1. 기간 → 날짜
        start_date, end_date = self._period_to_dates(period)
        logger.info(f"   {start_date.date()} ~ {end_date.date()}")

        # 2. 현재 계좌 잔고
        balance = await self.korea_invest.get_account_balance()
        if not balance:
            logger.error("계좌 조회 실패")
            return []

        current_positions = {
            p["stock_code"]: p["quantity"]
            for p in balance["positions"]
        }
        current_cash = balance.get("available_cash", 0)

        logger.info(f"   종목: {len(current_positions)}개")
        logger.info(f"   현금: {current_cash:,.0f}원")

        # 3. 거래일 타임라인
        trading_days = self._generate_trading_days(start_date, end_date)
        logger.info(f"   거래일: {len(trading_days)}일")

        # 4. 거래 내역 조회 ✅ NEW
        trades = await self.trade_history.get_trade_history(
            start_date,
            end_date
        )
        logger.info(f"   거래: {len(trades)}건")

        # 5. 일별 포지션 재구성 ✅ NEW
        daily_positions = self.trade_history.reconstruct_daily_positions(
            trades,
            current_positions,
            trading_days
        )

        # 6. 일별 현금 계산 ✅ NEW
        daily_cash = self.cash_tracker.calculate_daily_cash(
            trades,
            current_cash,
            trading_days
        )

        # 7. 종목별 가격 조회
        stock_codes = set()
        for positions in daily_positions.values():
            stock_codes.update(positions.keys())

        price_histories = await self._fetch_stock_histories(
            list(stock_codes),
            start_date,
            end_date
        )

        # 8. 일별 포트폴리오 가치 계산 ✅ NEW
        portfolio_values = []
        for date in trading_days:
            positions = daily_positions.get(date, {})
            cash = daily_cash.get(date, current_cash)

            total_value = cash
            for stock_code, quantity in positions.items():
                price = self._get_price_at_date(
                    price_histories.get(stock_code),
                    date
                )
                if price > 0:
                    total_value += price * quantity

            portfolio_values.append({
                "date": date,
                "value": total_value
            })

        logger.info(
            f"   시작: {portfolio_values[0]['value']:,.0f}원, "
            f"종료: {portfolio_values[-1]['value']:,.0f}원"
        )

        # 9. 벤치마크 조회 및 정규화
        try:
            benchmark_data = await self.benchmark.get_kospi_history(
                start_date,
                end_date
            )

            if len(benchmark_data) != len(trading_days):
                benchmark_data = self._align_benchmark(
                    benchmark_data,
                    trading_days
                )

            normalized_benchmark = self.benchmark.normalize_to_portfolio(
                benchmark_data,
                portfolio_values[0]["value"]
            )

        except Exception as e:
            logger.error(f"벤치마크 실패: {e}")
            normalized_benchmark = [0] * len(portfolio_values)

        # 10. 결과 조합 ✅ Frontend 타입 일치
        result = [
            PortfolioHistoryPoint(
                date=pv["date"].strftime("%Y-%m-%dT15:30:00+09:00"),
                portfolio=pv["value"],
                benchmark=bv
            )
            for pv, bv in zip(portfolio_values, normalized_benchmark)
        ]

        logger.info(f"✅ 완료: {len(result)}개 포인트")
        return result

    def _period_to_dates(
        self,
        period: Literal["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"]
    ) -> Tuple[datetime, datetime]:
        """기간 → (시작일, 종료일)"""
        end_date = datetime.now()

        if period == "1D":
            start_date = end_date - timedelta(days=1)
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
        종목별 가격 히스토리 병렬 조회

        ⚠️ 중요: get_day_chart_data() 반환 타입 확인 필요
        - 현재 코드 기준으로 List[ChartCandle]을 반환
        - DataFrame으로 사용하려면 변환 필요
        - 또는 get_day_chart_data()를 DataFrame 반환 버전으로 래핑
        """
        logger.info(f"종목별 가격 조회: {len(stock_codes)}개")

        async def fetch_one(stock_code: str):
            try:
                result = await self.korea_invest.get_daily_chart_data(
                    stock_code,
                    start_date.strftime("%Y%m%d"),
                    end_date.strftime("%Y%m%d")
                )

                # ⚠️ List[ChartCandle] → DataFrame 변환 필요
                if isinstance(result, list):
                    # ChartCandle 리스트를 DataFrame으로 변환
                    # ⚠️ 중요: ChartCandle에는 date 필드가 없음!
                    # timestamp 필드를 사용하여 날짜 추출
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
                    df = result  # 이미 DataFrame인 경우

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
