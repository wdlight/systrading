"""
Portfolio API 디버깅 스크립트
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# backend 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import get_settings
from app.core.korea_invest import KoreaInvestAPIService
from app.services.benchmark_service import BenchmarkService
from app.services.portfolio_analytics_service import PortfolioAnalyticsService
from app.services.snapshot_manager import SnapshotManager
from app.utils.trading_calendar import TradingCalendar
from loguru import logger

async def main():
    """Portfolio API 디버깅"""
    logger.info("=" * 60)
    logger.info("🔍 Portfolio API 디버깅")
    logger.info("=" * 60)

    # 1. 거래일 계산 테스트
    calendar = TradingCalendar()
    end_date = datetime.now()
    start_date_1M = end_date - timedelta(days=30)

    logger.info(f"\n📅 기간 설정")
    logger.info(f"   Start: {start_date_1M.strftime('%Y-%m-%d %A')}")
    logger.info(f"   End:   {end_date.strftime('%Y-%m-%d %A')}")

    trading_days = calendar.get_trading_days(start_date_1M, end_date)
    logger.info(f"\n📊 거래일: {len(trading_days)}일")
    if trading_days:
        logger.info(f"   첫날: {trading_days[0].strftime('%Y-%m-%d %A')}")
        logger.info(f"   마지막: {trading_days[-1].strftime('%Y-%m-%d %A')}")

    # 2. 스냅샷 확인
    snapshot_manager = SnapshotManager()
    latest_snapshot = snapshot_manager.load_latest_snapshot(end_date)

    if latest_snapshot:
        logger.info(f"\n📸 스냅샷 발견")
        logger.info(f"   날짜: {latest_snapshot.get('date')}")
        logger.info(f"   타임스탬프: {latest_snapshot.get('timestamp')}")
        logger.info(f"   총자산: {latest_snapshot.get('total_asset'):,}원")

        # 스냅샷 날짜 파싱
        snapshot_date = datetime.strptime(latest_snapshot['date'], "%Y-%m-%d")
        logger.info(f"   스냅샷 날짜: {snapshot_date.strftime('%Y-%m-%d %A')}")

        # start_date 조정 시뮬레이션
        adjusted_start = start_date_1M
        if snapshot_date > start_date_1M:
            adjusted_start = snapshot_date
            logger.info(f"\n⚠️  start_date 조정됨: {start_date_1M.date()} → {adjusted_start.date()}")

        # 조정된 기간의 거래일
        adjusted_trading_days = calendar.get_trading_days(adjusted_start, end_date)
        logger.info(f"\n📊 조정된 거래일: {len(adjusted_trading_days)}일")
        if adjusted_trading_days:
            logger.info(f"   첫날: {adjusted_trading_days[0].strftime('%Y-%m-%d %A')}")
            logger.info(f"   마지막: {adjusted_trading_days[-1].strftime('%Y-%m-%d %A')}")
        else:
            logger.error("❌ 조정 후 거래일이 없습니다! 이것이 204 응답의 원인입니다.")
    else:
        logger.info("\n📸 스냅샷 없음")

    # 3. Portfolio Analytics 실행
    logger.info(f"\n🔄 Portfolio Analytics 실행")
    try:
        settings = get_settings()
        korea_invest = KoreaInvestAPIService(settings)
        benchmark = BenchmarkService(korea_invest)
        analytics = PortfolioAnalyticsService(korea_invest, benchmark, snapshot_manager)

        result = await analytics.get_portfolio_history("1M")
        logger.info(f"✅ 결과: {len(result)}개 데이터 포인트")
        if result:
            for i, point in enumerate(result[:3]):
                logger.info(f"   [{i}] {point.date}, 포트폴리오: {point.portfolio:,.0f}, 벤치마크: {point.benchmark:,.0f}")

    except Exception as e:
        logger.error(f"❌ Portfolio Analytics 실패: {e}", exc_info=True)

    logger.info("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
