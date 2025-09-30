"""
한국 주식시장 거래시간 관리 유틸리티

정규 장: 09:00 ~ 15:30
시간외 종가: 08:30 ~ 09:00
시간외 단일가: 15:30 ~ 16:00
"""

from datetime import datetime, time, timedelta
from typing import Optional, Tuple
from enum import Enum


class TradingSession(str, Enum):
    """거래 세션 구분"""
    PRE_MARKET = "pre_market"      # 8:30 ~ 9:00 (시간외 종가)
    REGULAR = "regular"             # 9:00 ~ 15:30 (정규 장)
    AFTER_MARKET = "after_market"   # 15:30 ~ 16:00 (시간외 단일가)
    CLOSED = "closed"               # 장 외 시간


class TradingHoursManager:
    """한국 주식시장 거래시간 관리"""

    # 정규 장 시간
    REGULAR_MARKET_START = time(9, 0, 0)
    REGULAR_MARKET_END = time(15, 30, 0)

    # 시간외 거래 시간
    PRE_MARKET_START = time(8, 30, 0)
    AFTER_MARKET_END = time(16, 0, 0)

    @classmethod
    def get_session(cls, dt: datetime) -> TradingSession:
        """
        주어진 시간의 거래 세션 반환

        Args:
            dt: 확인할 시간

        Returns:
            TradingSession: 해당 시간의 거래 세션
        """
        t = dt.time()

        if cls.PRE_MARKET_START <= t < cls.REGULAR_MARKET_START:
            return TradingSession.PRE_MARKET
        elif cls.REGULAR_MARKET_START <= t < cls.REGULAR_MARKET_END:
            return TradingSession.REGULAR
        elif cls.REGULAR_MARKET_END <= t < cls.AFTER_MARKET_END:
            return TradingSession.AFTER_MARKET
        else:
            return TradingSession.CLOSED

    @classmethod
    def is_regular_hours(cls, dt: datetime) -> bool:
        """
        정규 장 시간 여부

        Args:
            dt: 확인할 시간

        Returns:
            bool: 정규 장 시간이면 True
        """
        return cls.get_session(dt) == TradingSession.REGULAR

    @classmethod
    def is_trading_hours(cls, dt: datetime, include_extended: bool = False) -> bool:
        """
        거래 시간 여부 (시간외 포함 옵션)

        Args:
            dt: 확인할 시간
            include_extended: 시간외 거래 포함 여부

        Returns:
            bool: 거래 시간이면 True
        """
        session = cls.get_session(dt)
        if include_extended:
            return session in [TradingSession.PRE_MARKET, TradingSession.REGULAR, TradingSession.AFTER_MARKET]
        else:
            return session == TradingSession.REGULAR

    @classmethod
    def is_today(cls, dt: datetime, reference_date: Optional[datetime] = None) -> bool:
        """
        지정된 날짜인지 확인

        Args:
            dt: 확인할 시간
            reference_date: 기준 날짜 (None이면 오늘)

        Returns:
            bool: 같은 날짜면 True
        """
        if reference_date is None:
            reference_date = datetime.now()
        return dt.date() == reference_date.date()

    @classmethod
    def get_trading_day_start(cls, date: Optional[datetime] = None) -> datetime:
        """
        거래일의 시작 시간 (0시)

        Args:
            date: 대상 날짜 (None이면 오늘)

        Returns:
            datetime: 해당 날짜의 0시
        """
        if date is None:
            date = datetime.now()
        return datetime.combine(date.date(), time(0, 0, 0))

    @classmethod
    def get_regular_market_range(cls, date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        정규 장 시작/종료 시간

        Args:
            date: 대상 날짜 (None이면 오늘)

        Returns:
            Tuple[datetime, datetime]: (시작 시간, 종료 시간)
        """
        if date is None:
            date = datetime.now()
        start = datetime.combine(date.date(), cls.REGULAR_MARKET_START)
        end = datetime.combine(date.date(), cls.REGULAR_MARKET_END)
        return start, end

    @classmethod
    def get_extended_market_range(cls, date: Optional[datetime] = None) -> Tuple[datetime, datetime]:
        """
        시간외 거래 포함 시간 범위

        Args:
            date: 대상 날짜 (None이면 오늘)

        Returns:
            Tuple[datetime, datetime]: (시작 시간, 종료 시간)
        """
        if date is None:
            date = datetime.now()
        start = datetime.combine(date.date(), cls.PRE_MARKET_START)
        end = datetime.combine(date.date(), cls.AFTER_MARKET_END)
        return start, end

    @classmethod
    def get_next_reset_time(cls) -> datetime:
        """
        다음 리셋 시간 (다음날 0시)

        Returns:
            datetime: 다음 리셋 시간
        """
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        return datetime.combine(tomorrow.date(), time(0, 0, 0))

    @classmethod
    def get_time_until_reset(cls) -> timedelta:
        """
        리셋까지 남은 시간

        Returns:
            timedelta: 남은 시간
        """
        now = datetime.now()
        next_reset = cls.get_next_reset_time()
        return next_reset - now

    @classmethod
    def format_time_until_reset(cls) -> str:
        """
        리셋까지 남은 시간을 포맷팅

        Returns:
            str: "X시간 Y분 Z초" 형식
        """
        remaining = cls.get_time_until_reset()
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        seconds = int(remaining.total_seconds() % 60)
        return f"{hours}시간 {minutes}분 {seconds}초"