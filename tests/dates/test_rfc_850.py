"""Tests for dates"""

from bareutils.dates.rfc_850 import format_date, try_parse_date


def test_date_rfc850():
    """Test parsing and formatting dates"""
    text = 'Mon, 23-Mar-20 07:36:36 GMT'
    value = try_parse_date(text)
    formatted = format_date(value)
    assert formatted == text
    parsed = try_parse_date(formatted)
    assert parsed == value
