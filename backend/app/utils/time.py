from datetime import datetime, timezone, timedelta


KST = timezone(timedelta(hours=9))


def parse_kis_time(time_str: str, *, base: datetime | None = None) -> datetime:
    """
    한국투자증권 HHMMSS 문자열을 datetime(KST)으로 변환한다.

    Args:
        time_str: HHMMSS 형식의 문자열
        base: 기준 datetime. None이면 현재 KST 날짜 기준.

    Returns:
        datetime: KST 타임존의 datetime
    """
    base_dt = base.astimezone(KST) if base else datetime.now(tz=KST)
    hour = int(time_str[0:2]) if time_str and len(time_str) >= 2 else 0
    minute = int(time_str[2:4]) if time_str and len(time_str) >= 4 else 0
    second = int(time_str[4:6]) if time_str and len(time_str) >= 6 else 0
    return base_dt.replace(hour=hour, minute=minute, second=second, microsecond=0)
