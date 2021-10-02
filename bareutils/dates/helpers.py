"""Date helpers"""

from datetime import datetime
from typing import Optional

from . import rfc_7231
from . import rfc_850


def try_parse_date(value: str) -> Optional[datetime]:
    """Try to parse a date

    Args:
        value (str): The string to parse

    Returns:
        Optional[datetime]: The parsed date or None if the date could not be
            parsed.
    """
    result = rfc_7231.try_parse_date(value)
    if result:
        return result
    result = rfc_850.try_parse_date(value)
    if result:
        return result
    return None


def parse_date(value: str) -> datetime:
    """Parse a date

    Args:
        value (str): The string to parse

    Raises:
        ValueError: If the date could not be parsed

    Returns:
        datetime: The parsed datetime
    """
    result = try_parse_date(value)
    if not result:
        raise ValueError()
    return result
