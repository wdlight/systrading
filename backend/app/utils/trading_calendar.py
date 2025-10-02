"""
한국 주식시장 거래일 계산 유틸리티
주말 및 공휴일을 제외한 거래일 계산
"""

from datetime import datetime, timedelta
from typing import Set


class TradingCalendar:
    """한국 주식시장 거래일 관리"""

    # 2025년 한국 공휴일 (YYYYMMDD 형식)
    HOLIDAYS_2025: Set[str] = {
        "20250101",  # 신정
        "20250128",  # 설날 연휴
        "20250129",  # 설날
        "20250130",  # 설날 연휴
        "20250301",  # 삼일절
        "20250505",  # 어린이날
        "20250506",  # 석가탄신일
        "20250606",  # 현충일
        "20250815",  # 광복절
        "20251003",  # 개천절
        "20251005",  # 추석 연휴
        "20251006",  # 추석
        "20251007",  # 추석 연휴
        "20251009",  # 한글날
        "20251225",  # 크리스마스
    }

    # 2024년 한국 공휴일
    HOLIDAYS_2024: Set[str] = {
        "20240101",  # 신정
        "20240209",  # 설날 연휴
        "20240210",  # 설날
        "20240211",  # 설날 연휴
        "20240212",  # 대체공휴일
        "20240301",  # 삼일절
        "20240410",  # 총선
        "20240505",  # 어린이날
        "20240506",  # 대체공휴일
        "20240515",  # 석가탄신일
        "20240606",  # 현충일
        "20240815",  # 광복절
        "20240916",  # 추석 연휴
        "20240917",  # 추석
        "20240918",  # 추석 연휴
        "20241003",  # 개천절
        "20241009",  # 한글날
        "20241225",  # 크리스마스
    }

    @classmethod
    def is_holiday(cls, date: datetime) -> bool:
        """공휴일 여부 확인"""
        date_str = date.strftime("%Y%m%d")
        year = date.year

        if year == 2025:
            return date_str in cls.HOLIDAYS_2025
        elif year == 2024:
            return date_str in cls.HOLIDAYS_2024
        else:
            # 다른 연도는 기본 공휴일만 체크 (신정, 광복절 등)
            return date_str[-4:] in {"0101", "0815", "1225"}

    @classmethod
    def is_trading_day(cls, date: datetime) -> bool:
        """거래일 여부 확인 (주말 및 공휴일 제외)"""
        # 주말 체크 (토요일=5, 일요일=6)
        if date.weekday() >= 5:
            return False

        # 공휴일 체크
        if cls.is_holiday(date):
            return False

        return True

    @classmethod
    def get_previous_trading_day(cls, date: datetime) -> datetime:
        """이전 거래일 반환"""
        current = date - timedelta(days=1)

        # 최대 10일 전까지 탐색 (연휴 대비)
        for _ in range(10):
            if cls.is_trading_day(current):
                return current
            current = current - timedelta(days=1)

        # 10일 이내에 거래일이 없으면 그냥 1일 전 반환
        return date - timedelta(days=1)

    @classmethod
    def get_next_trading_day(cls, date: datetime) -> datetime:
        """다음 거래일 반환"""
        current = date + timedelta(days=1)

        # 최대 10일 후까지 탐색
        for _ in range(10):
            if cls.is_trading_day(current):
                return current
            current = current + timedelta(days=1)

        # 10일 이내에 거래일이 없으면 그냥 1일 후 반환
        return date + timedelta(days=1)

    @classmethod
    def get_trading_days_between(cls, start_date: datetime, end_date: datetime) -> int:
        """두 날짜 사이의 거래일 수 계산"""
        count = 0
        current = start_date

        while current <= end_date:
            if cls.is_trading_day(current):
                count += 1
            current = current + timedelta(days=1)

        return count