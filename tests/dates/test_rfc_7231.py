"""Tests for dates"""


from bareutils.dates.rfc_7231 import parse_date, format_date


def test_date_rfc7231():
    """Test parsing and formatting dates"""
    text = 'Mon, 09 Dec 2019 07:44:23 GMT'
    value = parse_date(text)
    formatted = format_date(value)
    assert formatted == text
    parsed = parse_date(formatted)
    assert parsed == value
