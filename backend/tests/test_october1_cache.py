"""
10월 1일 데이터 캐시 확인 및 생성 테스트
"""

import sys
import os
import asyncio
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from app.core.korea_invest import KoreaInvestAPIService
from app.services.chart_cache_service import ChartCacheService
from brokers.korea_investment.ki_env import KoreaInvestEnv
from brokers.korea_investment.ki_api import KoreaInvestAPI
from app.core.config import reload_settings

async def main():
    """10월 1일 데이터 조회 및 캐시 확인"""

    print("\n" + "="*80)
    print("📅 10월 1일 데이터 조회 및 캐시 확인")
    print("="*80 + "\n")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 초기화
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("🔧 초기화 중...")
    settings = reload_settings()
    config = settings.get_korea_invest_config()

    env = KoreaInvestEnv(config)
    api = KoreaInvestAPI(config, base_headers=env.get_base_headers())
    korea_invest_service = KoreaInvestAPIService(api)
    cache_service = ChartCacheService(cache_dir="kordata")

    stock_code = "005930"
    target_date = datetime(2025, 10, 1)

    print(f"   종목: {stock_code} (삼성전자)")
    print(f"   날짜: {target_date.strftime('%Y-%m-%d')}")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 2. 기존 캐시 확인
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cache_file = f"kordata/{stock_code}/20251001.json"
    print(f"📂 기존 캐시 확인: {cache_file}")

    if os.path.exists(cache_file):
        file_size = os.path.getsize(cache_file)
        print(f"   ✅ 캐시 파일 존재 (크기: {file_size:,} bytes)")
        print(f"   📋 캐시 삭제 후 재생성하겠습니다...")
        os.remove(cache_file)
    else:
        print(f"   ⚠️ 캐시 파일 없음 - 새로 생성합니다")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 3. 과거 데이터 조회 (캐시 자동 생성)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("🌐 과거 데이터 조회 중...")
    print("-" * 80)

    candles = await cache_service.get_historical_minute_candles(
        stock_code=stock_code,
        target_date=target_date,
        korea_invest_service=korea_invest_service
    )

    print("-" * 80)
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 4. 결과 확인
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if candles:
        print("✅ 데이터 조회 성공!")
        print(f"   총 개수: {len(candles)}개")
        print()

        print("📊 시간 범위:")
        print(f"   첫 데이터: {candles[0].시간}")
        print(f"   마지막 데이터: {candles[-1].시간}")
        print()

        print("📋 처음 10개 데이터:")
        for i, candle in enumerate(candles[:10], 1):
            print(f"   {i:2d}. {candle.시간} | 시: {candle.시가:>6,} | "
                  f"고: {candle.고가:>6,} | 저: {candle.저가:>6,} | "
                  f"종: {candle.종가:>6,} | 거래량: {candle.거래량:>8,}")
        print()

        print("📋 마지막 10개 데이터:")
        for i, candle in enumerate(candles[-10:], len(candles)-9):
            print(f"   {i:2d}. {candle.시간} | 시: {candle.시가:>6,} | "
                  f"고: {candle.고가:>6,} | 저: {candle.저가:>6,} | "
                  f"종: {candle.종가:>6,} | 거래량: {candle.거래량:>8,}")
        print()

        # 가격 통계
        prices = [c.종가 for c in candles]
        volumes = [c.거래량 for c in candles]

        print("📈 데이터 통계:")
        print(f"   최고가: {max(prices):,}원")
        print(f"   최저가: {min(prices):,}원")
        print(f"   시작가: {candles[0].시가:,}원")
        print(f"   종가: {candles[-1].종가:,}원")
        print(f"   등락: {candles[-1].종가 - candles[0].시가:+,}원")
        print(f"   총 거래량: {sum(volumes):,}주")
        print()

        # 캐시 파일 확인
        if os.path.exists(cache_file):
            file_size = os.path.getsize(cache_file)
            print(f"💾 캐시 파일 생성 완료:")
            print(f"   경로: {cache_file}")
            print(f"   크기: {file_size:,} bytes")
            print(f"   ✅ 다음 조회 시 캐시에서 즉시 로드됩니다!")
        else:
            print(f"⚠️ 캐시 파일이 생성되지 않음: {cache_file}")

    else:
        print("❌ 데이터 조회 실패")

    print("\n" + "="*80)
    print("🏁 테스트 완료")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
