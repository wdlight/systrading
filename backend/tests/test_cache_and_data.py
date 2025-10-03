"""
캐시 저장 및 10월 1일 데이터 확인 테스트
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

from app.services.trading_service import TradingService

async def test_cache_and_data():
    """캐시 저장 및 데이터 확인"""

    print("\n" + "="*80)
    print("📅 10월 1일 데이터 조회 및 캐시 저장 테스트")
    print("="*80 + "\n")

    # 서비스 초기화 (TradingService가 내부적으로 모든 의존성 처리)
    print("🔧 서비스 초기화 중...")
    trading_service = TradingService()

    stock_code = "005930"
    target_date = datetime(2025, 10, 1)

    print(f"📊 테스트 파라미터")
    print(f"   종목: {stock_code} (삼성전자)")
    print(f"   날짜: {target_date.strftime('%Y-%m-%d')}")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 과거 데이터 조회 (TradingService 사용)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("🌐 과거 데이터 조회 중 (TradingService 사용)...")
    print("-" * 80)

    candles = await trading_service.get_minute_chart_data(
        stock_code=stock_code,
        target_date=target_date,
        regular_hours_only=True
    )

    print("-" * 80)
    print()

    if candles:
        print("✅ 데이터 조회 성공!")
        print(f"   총 개수: {len(candles)}개")
        print()

        print("📋 시간 범위:")
        print(f"   첫 데이터: {candles[0].시간}")
        print(f"   마지막 데이터: {candles[-1].시간}")
        print()

        print("📋 처음 5개 데이터:")
        for i, candle in enumerate(candles[:5], 1):
            print(f"   {i}. 시간: {candle.시간}, 시가: {candle.시가:,}, "
                  f"고가: {candle.고가:,}, 저가: {candle.저가:,}, "
                  f"종가: {candle.종가:,}, 거래량: {candle.거래량:,}")
        print()

        print("📋 마지막 5개 데이터:")
        for i, candle in enumerate(candles[-5:], len(candles)-4):
            print(f"   {i}. 시간: {candle.시간}, 시가: {candle.시가:,}, "
                  f"고가: {candle.고가:,}, 저가: {candle.저가:,}, "
                  f"종가: {candle.종가:,}, 거래량: {candle.거래량:,}")
        print()

        # 캐시 파일 확인
        cache_file = f"kordata/{stock_code}/20251001.json"
        if os.path.exists(cache_file):
            file_size = os.path.getsize(cache_file)
            print(f"💾 캐시 파일 확인:")
            print(f"   경로: {cache_file}")
            print(f"   크기: {file_size:,} bytes")
            print(f"   ✅ 캐시 저장 완료!")
        else:
            print(f"⚠️ 캐시 파일이 생성되지 않음: {cache_file}")

    else:
        print("❌ 데이터 조회 실패")

    print("\n" + "="*80)
    print("🏁 테스트 완료")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(test_cache_and_data())
