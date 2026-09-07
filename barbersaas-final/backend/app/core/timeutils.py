from datetime import datetime
from zoneinfo import ZoneInfo


def as_business_time(value: datetime, timezone_name: str) -> datetime:
    tz = ZoneInfo(timezone_name)
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def as_utc(value: datetime, timezone_name: str) -> datetime:
    return as_business_time(value, timezone_name).astimezone(ZoneInfo("UTC"))
