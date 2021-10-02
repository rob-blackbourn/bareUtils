"""RFC7231"""

from datetime import datetime, timezone
import re
from typing import Optional

# pylint: disable=line-too-long
# Date: <day-name>, <day> <month> <year> <hour>:<minute>:<second> GMT
DATE_PATTERN = re.compile(
    r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun), (\d{2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (\d{4}) (\d{2}):(\d{2}):(\d{2}) GMT$'
)
DAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
MONTH_NAMES = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def try_parse_date(value: str) -> Optional[datetime]:
    """Parse a date according to RFC 7231, section 7.1.1.2: Date

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
        int(year),
        1 + MONTH_NAMES.index(month),
        int(day),
        int(hour),
        int(minute),
        int(second),
        tzinfo=timezone.utc
    )


def parse_date(value: str) -> datetime:
    """Parses a date according to RFC 7231, section 7.1.1.2: Date

    Args:
        value (str): The value to parse.

    Raises:
        ValueError: If the format could not be parsed.

    Returns:
        datetime: The parsed date.
    """
    return datetime.strptime(value, '%a, %d %b %Y %H:%M:%S %Z')


def format_date(value: datetime) -> str:
    """Format a date according to RFC 7231, section 7.1.1.2: Date

    Args:
        value (datetime): The datetime to format

    Returns:
        str: The formatted datetime
    """
    time_tuple = value.utctimetuple()
    return "{day}, {mday:02d} {mon} {year:04d} {hour:02d}:{min:02d}:{sec:02d} GMT".format(
        day=DAY_NAMES[time_tuple.tm_wday],
        mday=time_tuple.tm_mday,
        mon=MONTH_NAMES[time_tuple.tm_mon - 1],
        year=time_tuple.tm_year,
        hour=time_tuple.tm_hour,
        min=time_tuple.tm_min,
        sec=time_tuple.tm_sec
    )
