"""Portfolio History API 통합 테스트"""

import asyncio
from app.core.config import Settings
from app.core.dependencies import get_korea_invest_service
from app.services.benchmark_service import BenchmarkService
from app.services.portfolio_analytics_service import PortfolioAnalyticsService


async def main():
    """메인 테스트"""

    print("=== Portfolio History 통합 테스트 ===\n")

    # 1. 서비스 초기화
    settings = Settings()
    korea_invest = await get_korea_invest_service()

    if not korea_invest.is_connected:
        print("❌ 한투 API 연결 실패")
        return

    print("✅ 한투 API 연결 성공\n")

    # 2. 서비스 생성
    benchmark = BenchmarkService(korea_invest)
    analytics = PortfolioAnalyticsService(korea_invest, benchmark)

    # 3. 각 기간별 테스트
    periods = ["1D", "1W", "1M", "3M"]

    for period in periods:
        print(f"--- {period} ---")

        try:
            result = await analytics.get_portfolio_history(period)

            if result:
                print(f"  데이터 포인트: {len(result)}개")
                print(f"  시작: {result[0].date}")
                print(f"    포트폴리오: {result[0].portfolio:,.0f}원")
                print(f"    벤치마크: {result[0].benchmark:,.0f}원")
                print(f"  종료: {result[-1].date}")
                print(f"    포트폴리오: {result[-1].portfolio:,.0f}원")
                print(f"    벤치마KOSPI: {result[-1].benchmark:,.0f}원")

                # 수익률 계산
                pf_return = ((result[-1].portfolio / result[0].portfolio) - 1) * 100
                bm_return = ((result[-1].benchmark / result[0].benchmark) - 1) * 100

                print(f"  수익률:")
                print(f"    포트폴리오: {pf_return:+.2f}%")
                print(f"    벤치마크: {bm_return:+.2f}%")
                print(f"    초과수익: {pf_return - bm_return:+.2f}%p")
            else:
                print("  ⚠️ 데이터 없음")

        except Exception as e:
            print(f"  ❌ 오류: {e}")

        print()

    print("=== 테스트 완료 ===")


if __name__ == "__main__":
    asyncio.run(main())
