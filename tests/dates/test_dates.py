"""Tests for dates"""

from datetime import datetime, timezone

from bareutils.dates import parse_date
from bareutils.dates.rfc_7231 import format_date


def test_date_rfc7231():
    """Test parsing and formatting dates"""
    text = 'Mon, 09 Dec 2019 07:44:23 GMT'
    value = parse_date(text)
    formatted = format_date(value)
    assert formatted == text
    parsed = parse_date(formatted)
    assert parsed == value


def test_date_rfc850():
    """Test parsing and formatting dates"""
    text = 'Mon, 23-Mar-20 07:36:36 GMT'
    value = parse_date(text)
    assert value == datetime(2020, 3, 23, 7, 36, 36, tzinfo=timezone.utc)
