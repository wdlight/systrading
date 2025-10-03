"""
한국투자증권 일자별 분봉 API 직접 테스트

실행: python tests/test_api_direct.py
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from brokers.korea_investment.ki_env import KoreaInvestEnv
from brokers.korea_investment.ki_api import KoreaInvestAPI
from datetime import datetime

def test_daily_minute_api():
    """10월 1일 삼성전자 분봉 데이터 직접 테스트"""

    print("\n" + "="*80)
    print("📅 한국투자증권 일자별 분봉 API 테스트")
    print("="*80 + "\n")

    # 설정 로드
    from app.core.config import reload_settings
    settings = reload_settings()
    config = settings.get_korea_invest_config()

    # KI API 초기화
    print("🔧 API 초기화 중...")
    env = KoreaInvestEnv(config)
    api = KoreaInvestAPI(config, base_headers=env.get_base_headers())

    # 테스트 파라미터
    stock_code = "005930"  # 삼성전자
    target_date = "20251001"  # 2025년 10월 1일

    print(f"📊 테스트 대상")
    print(f"   종목: {stock_code} (삼성전자)")
    print(f"   날짜: {target_date}")
    print()

    # API 호출
    print("🌐 API 호출 중...")
    print("-" * 80)

    df = api.get_daily_minute_chart_data(stock_code, target_date)

    print("-" * 80)
    print()

    # 결과 확인
    if df is not None and not df.empty:
        print("✅ API 호출 성공!")
        print(f"   데이터 개수: {len(df)}개")
        print()

        print("📋 데이터 샘플 (처음 5개):")
        print(df.head().to_string())
        print()

        print("📋 데이터 샘플 (마지막 5개):")
        print(df.tail().to_string())
        print()

        print("📊 데이터 요약:")
        print(f"   첫 시간: {df.iloc[0]['시간']}")
        print(f"   마지막 시간: {df.iloc[-1]['시간']}")
        print(f"   시가 범위: {df['시가'].min()} ~ {df['시가'].max()}")
        print(f"   종가 범위: {df['종가'].min()} ~ {df['종가'].max()}")
        print(f"   총 거래량: {df['거래량'].sum():,}")
        print()

        print("="*80)
        print("🎉 테스트 성공!")
        print("="*80)

    else:
        print("❌ 데이터 없음")
        print("   가능한 원인:")
        print("   - 비거래일")
        print("   - API 파라미터 오류")
        print("   - 네트워크 문제")
        print()

        # 로그 확인 안내
        print("📝 로그 파일을 확인하세요:")
        today = datetime.now().strftime("%Y%m%d")
        print(f"   logs/API_{today}.log")

if __name__ == "__main__":
    test_daily_minute_api()
