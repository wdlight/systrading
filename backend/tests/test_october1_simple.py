"""
10월 1일 데이터 확인 - 간단 테스트
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from brokers.korea_investment.ki_env import KoreaInvestEnv
from brokers.korea_investment.ki_api import KoreaInvestAPI
from app.core.config import reload_settings

def main():
    """10월 1일 데이터 확인"""

    print("\n" + "="*80)
    print("📅 10월 1일 데이터 확인")
    print("="*80 + "\n")

    # 초기화
    print("🔧 초기화 중...")
    settings = reload_settings()
    config = settings.get_korea_invest_config()

    env = KoreaInvestEnv(config)
    api = KoreaInvestAPI(config, base_headers=env.get_base_headers())

    stock_code = "005930"
    target_date = "20251001"

    print(f"   종목: {stock_code} (삼성전자)")
    print(f"   날짜: {target_date}")
    print()

    # 데이터 조회
    print("🌐 API 호출 중...")
    print("-" * 80)

    df = api.get_daily_minute_chart_data(stock_code, target_date)

    print("-" * 80)
    print()

    if df is not None and not df.empty:
        print("✅ 데이터 조회 성공!")
        print(f"   총 개수: {len(df)}개")
        print()

        print("📊 시간 범위:")
        print(f"   첫 시간: {df.iloc[0]['시간']}")
        print(f"   마지막 시간: {df.iloc[-1]['시간']}")
        print()

        print("📋 처음 10개 데이터:")
        print(df.head(10).to_string(index=False))
        print()

        print("📋 마지막 10개 데이터:")
        print(df.tail(10).to_string(index=False))
        print()

        print("📈 데이터 통계:")
        print(f"   최고가: {df['고가'].max():,}원")
        print(f"   최저가: {df['저가'].min():,}원")
        print(f"   시작가: {df.iloc[0]['시가']:,}원")
        print(f"   종가: {df.iloc[-1]['종가']:,}원")
        print(f"   등락: {df.iloc[-1]['종가'] - df.iloc[0]['시가']:+,}원")
        print(f"   총 거래량: {df['거래량'].sum():,}주")

    else:
        print("❌ 데이터 없음")

    print("\n" + "="*80)
    print("🏁 테스트 완료")
    print("="*80)

if __name__ == "__main__":
    main()
