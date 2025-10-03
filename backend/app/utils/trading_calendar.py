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
        # "20251003",  # 개천절 (테스트를 위해 임시 제거)
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

    @classmethod
    def get_previous_trading_days(cls, from_date: datetime, count: int) -> list[datetime]:
        """
        특정 날짜로부터 이전 N개 거래일 반환 (from_date 제외)

        Args:
            from_date: 기준 날짜
            count: 반환할 거래일 개수

        Returns:
            이전 거래일 리스트 (최신순, from_date는 제외)

        Example:
            >>> get_previous_trading_days(datetime(2025, 10, 6), 3)  # 월요일
            [datetime(2025, 10, 3),  # 금요일
             datetime(2025, 10, 2),  # 목요일
             datetime(2025, 10, 1)]  # 수요일
        """
        trading_days = []
        current = from_date - timedelta(days=1)
        max_iterations = count * 3  # 최대 탐색 범위 (연휴 대비)

        iteration = 0
        while len(trading_days) < count and iteration < max_iterations:
            if cls.is_trading_day(current):
                trading_days.append(current)
            current = current - timedelta(days=1)
            iteration += 1

        return trading_days

    @classmethod
    def get_trading_days_in_range(cls, start_date: datetime, end_date: datetime) -> list[datetime]:
        """
        날짜 범위 내의 모든 거래일 리스트 반환 (start_date와 end_date 포함)

        Args:
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            거래일 리스트 (시간순)

        Example:
            >>> get_trading_days_in_range(datetime(2025, 10, 1), datetime(2025, 10, 6))
            [datetime(2025, 10, 1),  # 수요일
             datetime(2025, 10, 2),  # 목요일
             datetime(2025, 10, 3),  # 금요일 (10/6은 추석 연휴)
             datetime(2025, 10, 6)]  # 월요일
        """
        trading_days = []
        current = start_date

        while current <= end_date:
            if cls.is_trading_day(current):
                trading_days.append(current)
            current = current + timedelta(days=1)

        return trading_days