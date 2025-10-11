"""
거래일 계산 유틸리티 v3.0 (Dynamic)

한국 주식시장의 거래일을 동적으로 계산합니다.
- 'holidays' 라이브러리를 사용하여 공휴일 및 대체공휴일 자동 계산
- 연말 휴장일(12월 31일) 자동 포함
"""

from datetime import datetime, timedelta
from typing import List
import holidays


class TradingCalendar:
    """
    한국 주식 거래일 계산기.
    'holidays' 라이브러리를 사용하여 공휴일을 동적으로 처리합니다.
    """

    def __init__(self, years: List[int] = None):
        """
        TradingCalendar 초기화.
        지정된 연도 범위의 공휴일 및 연말 휴장일을 로드합니다.
        지정하지 않으면 현재 연도 기준 +- 5년으로 설정됩니다.
        """
        if years is None:
            current_year = datetime.now().year
            years = list(range(current_year - 5, current_year + 6))

        # 대한민국 공휴일 로드
        self.holidays = holidays.KR(years=years)

        # 주식 시장의 연말 휴장일(12월 31일) 추가
        for year in years:
            # 12월 31일이 주말이 아닌 경우 휴장일로 추가
            last_day = datetime(year, 12, 31)
            if last_day.weekday() < 5:  # 0-4 (월-금)
                self.holidays[last_day] = "연말 휴장일"

    def is_trading_day(self, date: datetime) -> bool:
        """
        특정 날짜가 거래일인지 확인합니다.
        주말, 공휴일, 연말 휴장일을 제외합니다.
        """
        # 주말 체크 (토요일=5, 일요일=6)
        if date.weekday() >= 5:
            return False

        # 공휴일 체크 (holidays 라이브러리 사용)
        # date 객체의 날짜 부분만 비교하기 위해 date.date() 사용
        if date.date() in self.holidays:
            return False

        return True

    def get_next_trading_day(self, date: datetime, max_attempts: int = 30) -> datetime:
        """
        주어진 날짜 이후의 가장 가까운 거래일을 반환합니다.
        """
        next_day = date + timedelta(days=1)
        for _ in range(max_attempts):
            if self.is_trading_day(next_day):
                return next_day
            next_day += timedelta(days=1)
        raise ValueError(f"{max_attempts}일 내에 다음 거래일을 찾을 수 없습니다: {date}")

    def get_previous_trading_day(self, date: datetime, max_attempts: int = 30) -> datetime:
        """
        주어진 날짜 이전의 가장 가까운 거래일을 반환합니다.
        """
        prev_day = date - timedelta(days=1)
        for _ in range(max_attempts):
            if self.is_trading_day(prev_day):
                return prev_day
            prev_day -= timedelta(days=1)
        raise ValueError(f"{max_attempts}일 내에 이전 거래일을 찾을 수 없습니다: {date}")

    def get_trading_days(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> List[datetime]:
        """기간 내 거래일 리스트 반환"""
        if start_date > end_date:
            return []

        days = []
        current_day = start_date
        while current_day <= end_date:
            if self.is_trading_day(current_day):
                days.append(current_day)
            current_day += timedelta(days=1)
        return days

    def count_trading_days(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """기간 내 거래일 수 계산"""
        return len(self.get_trading_days(start_date, end_date))


# --- Singleton 인스턴스 관리 ---
_default_calendar = None


def get_default_calendar() -> "TradingCalendar":
    """
    기본 TradingCalendar 싱글톤 인스턴스를 반환합니다.
    """
    global _default_calendar
    if _default_calendar is None:
        _default_calendar = TradingCalendar()
    return _default_calendar
