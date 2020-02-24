"""RFC 850"""

from datetime import datetime, timezone
import re
from typing import Optional

# 'Mon, 23-Mar-20 07:36:36 GMT'
DATE_PATTERN = re.compile(
    r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\d{2})-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-(\d{2}) (\d{2}):(\d{2}):(\d{2}) GMT$'
)
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def try_parse_date(value: str) -> Optional[datetime]:
    """Parse a date according to RFC 850.

    e.g. 'Mon, 23-Mar-20 07:36:36 GMT'

    Args:
        value (str): The string to parse

    Raises:
        ParseError: If the string cannot be parsed to a date

    Returns:
        datetime: The parsed datetime
    """
    matches = DATE_PATTERN.match(value)
    if not matches:
        return None
    _day_of_week, day, month, year, hour, minute, second = matches.groups()
    return datetime(
        2000 + int(year),
        1 + MONTH_NAMES.index(month),
        int(day),
        int(hour),
        int(minute),
        int(second),
        tzinfo=timezone.utc
    )


def format_date(value: datetime) -> str:
    """Format a date according to RFC 850

    e.g. 'Mon, 23-Mar-20 07:36:36 GMT'

    Args:
        value (datetime): The datetime to format

    Returns:
        str: The formatted datetime
    """
    time_tuple = value.utctimetuple()
    return "{day}, {mday:02d}-{mon}-{year:02d} {hour:02d}:{min:02d}:{sec:02d} GMT".format(
        day=DAY_NAMES[time_tuple.tm_wday],
        mday=time_tuple.tm_mday,
        mon=MONTH_NAMES[time_tuple.tm_mon - 1],
        year=2000-time_tuple.tm_year,
        hour=time_tuple.tm_hour,
        min=time_tuple.tm_min,
        sec=time_tuple.tm_sec
    )
