"""Tests for dates"""

from datetime import datetime, timezone

import pytest

from bareutils.dates import try_parse_date, parse_date


def test_parse_date():
    """Test parsing and formatting dates"""
    text = 'Mon, 23-Mar-20 07:36:36 GMT'
    value = parse_date(text)
    assert value == datetime(2020, 3, 23, 7, 36, 36, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        parse_date('Invalid date string')


def test_try_parse_date():
    """Test parsing and formatting dates"""
    text = 'Mon, 23-Mar-20 07:36:36 GMT'
    value = try_parse_date(text)
    assert value == datetime(2020, 3, 23, 7, 36, 36, tzinfo=timezone.utc)

    assert try_parse_date('Invalid date string') is None
