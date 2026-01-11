# datetime util

from datetime import datetime, timezone

def get_current_utc_datetime() -> datetime:
    """현재 UTC 날짜 및 시간 반환"""
    return datetime.now(tz=timezone.utc)