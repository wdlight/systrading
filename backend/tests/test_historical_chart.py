"""
과거 분봉 데이터 조회 테스트 스크립트

실행 방법:
1. vkis 가상환경 활성화
   cd backend
   source vkis/bin/activate

2. 테스트 실행
   python tests/test_historical_chart.py

또는 pytest 사용:
   pytest tests/test_historical_chart.py -v -s
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.trading_service import TradingService
from app.services.chart_cache_service import ChartCacheService
from app.core.korea_invest import KoreaInvestAPIService
from loguru import logger


async def test_historical_data():
    """과거 데이터 조회 테스트"""

    print("\n" + "="*80)
    print("📅 과거 분봉 데이터 조회 테스트 시작")
    print("="*80 + "\n")

    try:
        # 설정 로드
        from app.core.config import get_settings
        settings = get_settings()

        # 서비스 초기화
        print("🔧 서비스 초기화 중...")
        ki_service = KoreaInvestAPIService(settings)
        trading_service = TradingService(ki_service)

        stock_code = "005930"  # 삼성전자
        print(f"📊 테스트 종목: {stock_code} (삼성전자)\n")

        # 테스트 1: 어제 데이터
        print("-" * 80)
        yesterday = datetime.now() - timedelta(days=1)
        print(f"📅 테스트 1: 어제 데이터 ({yesterday.strftime('%Y-%m-%d')})")
        print("-" * 80)

        data = await trading_service.get_minute_chart_data(
            stock_code=stock_code,
            target_date=yesterday
        )

        if data:
            print(f"✅ 데이터 개수: {len(data)}")
            print(f"   첫 데이터: {data[0].timestamp} - Open: {data[0].open}, Close: {data[0].close}")
            print(f"   마지막 데이터: {data[-1].timestamp} - Open: {data[-1].open}, Close: {data[-1].close}")
        else:
            print("⚠️ 데이터 없음 (비거래일일 가능성)")

        print()

        # 테스트 2: 그제 데이터
        print("-" * 80)
        two_days_ago = datetime.now() - timedelta(days=2)
        print(f"📅 테스트 2: 그제 데이터 ({two_days_ago.strftime('%Y-%m-%d')})")
        print("-" * 80)

        data = await trading_service.get_minute_chart_data(
            stock_code=stock_code,
            target_date=two_days_ago
        )

        if data:
            print(f"✅ 데이터 개수: {len(data)}")
            print(f"   첫 데이터: {data[0].timestamp}")
            print(f"   마지막 데이터: {data[-1].timestamp}")
        else:
            print("⚠️ 데이터 없음 (비거래일일 가능성)")

        print()

        # 테스트 3: 오늘 데이터 (기존 API 검증)
        print("-" * 80)
        print(f"📅 테스트 3: 오늘 데이터")
        print("-" * 80)

        data = await trading_service.get_minute_chart_data(
            stock_code=stock_code,
            target_date=None  # 오늘
        )

        if data:
            print(f"✅ 데이터 개수: {len(data)}")
            print(f"   첫 데이터: {data[0].timestamp}")
            print(f"   마지막 데이터: {data[-1].timestamp}")
        else:
            print("⚠️ 데이터 없음")

        print()

        # 테스트 4: 캐시 동작 확인 (두 번째 요청)
        print("-" * 80)
        print(f"📅 테스트 4: 캐시 동작 확인 (어제 데이터 재요청)")
        print("-" * 80)

        import time
        start_time = time.time()

        data = await trading_service.get_minute_chart_data(
            stock_code=stock_code,
            target_date=yesterday
        )

        elapsed = time.time() - start_time

        if data:
            print(f"✅ 데이터 개수: {len(data)}")
            print(f"⚡ 응답 시간: {elapsed:.3f}초 (캐시 히트 예상)")
        else:
            print("⚠️ 데이터 없음")

        print()

        # 최종 결과
        print("=" * 80)
        print("🎉 모든 테스트 완료!")
        print("=" * 80)
        print("\n📝 다음 단계:")
        print("  1. 로그를 확인하여 API 호출이 정상적으로 이루어졌는지 확인")
        print("  2. 캐시 디렉토리(kordata/)를 확인하여 데이터가 저장되었는지 확인")
        print("  3. 비거래일인 경우 이전 거래일 데이터가 반환되는지 확인")
        print()

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # asyncio 실행
    asyncio.run(test_historical_data())
