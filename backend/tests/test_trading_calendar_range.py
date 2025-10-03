"""
거래일 유틸리티 테스트
"""

import sys
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

from app.utils.trading_calendar import TradingCalendar


def test_get_previous_trading_days():
    """월요일로부터 이전 3 거래일 테스트"""

    print("\n" + "="*80)
    print("📅 거래일 유틸리티 테스트")
    print("="*80 + "\n")

    # 테스트 1: 월요일(10/7)로부터 이전 3개 거래일
    # 주의: 10/6은 추석 연휴
    monday = datetime(2025, 10, 7)  # 화요일 (10/6은 추석)
    print(f"기준 날짜: {monday.strftime('%Y-%m-%d (%A)')}")

    previous_days = TradingCalendar.get_previous_trading_days(monday, 3)

    print(f"\n이전 3개 거래일:")
    for i, day in enumerate(previous_days, 1):
        is_trading = TradingCalendar.is_trading_day(day)
        print(f"   {i}. {day.strftime('%Y-%m-%d (%A)')} - 거래일: {is_trading}")

    assert len(previous_days) == 3, f"Expected 3 days, got {len(previous_days)}"
    assert all(TradingCalendar.is_trading_day(d) for d in previous_days), "Non-trading day found!"

    # 테스트 2: 10월 1일로부터 이전 5개 거래일
    oct1 = datetime(2025, 10, 1)
    print(f"\n\n기준 날짜: {oct1.strftime('%Y-%m-%d (%A)')}")

    previous_days = TradingCalendar.get_previous_trading_days(oct1, 5)

    print(f"\n이전 5개 거래일:")
    for i, day in enumerate(previous_days, 1):
        is_trading = TradingCalendar.is_trading_day(day)
        print(f"   {i}. {day.strftime('%Y-%m-%d (%A)')} - 거래일: {is_trading}")

    assert len(previous_days) == 5, f"Expected 5 days, got {len(previous_days)}"

    # 테스트 3: 날짜 범위 내 거래일 조회
    start_date = datetime(2025, 10, 1)
    end_date = datetime(2025, 10, 7)
    print(f"\n\n날짜 범위: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    trading_days = TradingCalendar.get_trading_days_in_range(start_date, end_date)

    print(f"\n거래일 목록 ({len(trading_days)}개):")
    for i, day in enumerate(trading_days, 1):
        print(f"   {i}. {day.strftime('%Y-%m-%d (%A)')}")

    print("\n" + "="*80)
    print("✅ 모든 테스트 통과!")
    print("="*80)


if __name__ == "__main__":
    test_get_previous_trading_days()
