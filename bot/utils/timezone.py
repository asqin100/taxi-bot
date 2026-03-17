"""Timezone utilities for consistent Moscow time handling across the application."""
from datetime import datetime
from zoneinfo import ZoneInfo

# Moscow timezone - all times in database are stored as naive datetime in Moscow time
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def now() -> datetime:
    """Get current time in Moscow timezone as naive datetime.

    Use this instead of datetime.now() throughout the application to ensure
    consistent timezone handling.

    Returns:
        datetime: Current Moscow time as naive datetime (no tzinfo)
    """
    return datetime.now(tz=MOSCOW_TZ).replace(tzinfo=None)


def from_timestamp(timestamp: float) -> datetime:
    """Convert Unix timestamp to Moscow time as naive datetime.

    Args:
        timestamp: Unix timestamp (seconds since epoch)

    Returns:
        datetime: Moscow time as naive datetime
    """
    utc_time = datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
    moscow_time = utc_time.astimezone(MOSCOW_TZ)
    return moscow_time.replace(tzinfo=None)
