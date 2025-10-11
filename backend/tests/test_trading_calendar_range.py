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

from app.utils.trading_calendar import get_default_calendar


def test_get_previous_trading_days():
    """월요일로부터 이전 3 거래일 테스트"""

    print("\n" + "="*80)
    print("📅 거래일 유틸리티 테스트")
    print("="*80 + "\n")

    calendar = get_default_calendar()

    # 테스트 1: 화요일(10/7)로부터 이전 3개 거래일
    # 주의: 10/6은 추석 연휴
    tuesday = datetime(2025, 10, 7)  # 화요일
    print(f"기준 날짜: {tuesday.strftime('%Y-%m-%d (%A)')}")

    previous_days = []
    current_day = tuesday
    for _ in range(3):
        prev_day = calendar.get_previous_trading_day(current_day)
        previous_days.insert(0, prev_day)
        current_day = prev_day

    print(f"\n이전 3개 거래일:")
    for i, day in enumerate(previous_days, 1):
        is_trading = calendar.is_trading_day(day)
        print(f"   {i}. {day.strftime('%Y-%m-%d (%A)')} - 거래일: {is_trading}")

    assert len(previous_days) == 3, f"Expected 3 days, got {len(previous_days)}"
    assert all(calendar.is_trading_day(d) for d in previous_days), "Non-trading day found!"

    # 테스트 2: 10월 1일로부터 이전 5개 거래일
    oct1 = datetime(2025, 10, 1)
    print(f"\n\n기준 날짜: {oct1.strftime('%Y-%m-%d (%A)')}")

    previous_days_2 = []
    current_day_2 = oct1
    for _ in range(5):
        prev_day = calendar.get_previous_trading_day(current_day_2)
        previous_days_2.insert(0, prev_day)
        current_day_2 = prev_day

    print(f"\n이전 5개 거래일:")
    for i, day in enumerate(previous_days_2, 1):
        is_trading = calendar.is_trading_day(day)
        print(f"   {i}. {day.strftime('%Y-%m-%d (%A)')} - 거래일: {is_trading}")

    assert len(previous_days_2) == 5, f"Expected 5 days, got {len(previous_days_2)}"

    # 테스트 3: 날짜 범위 내 거래일 조회
    start_date = datetime(2025, 10, 1)
    end_date = datetime(2025, 10, 7)
    print(f"\n\n날짜 범위: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

    trading_days = calendar.get_trading_days(start_date, end_date)

    print(f"\n거래일 목록 ({len(trading_days)}개):")
    for i, day in enumerate(trading_days, 1):
        print(f"   {i}. {day.strftime('%Y-%m-%d (%A)')}")

    print("\n" + "="*80)
    print("✅ 모든 테스트 통과!")
    print("="*80)


if __name__ == "__main__":
    test_get_previous_trading_days()