"""Tests for cookies.py"""

from datetime import datetime, timezone
from bareutils.cookies import (
    make_cookie,
    encode_set_cookie,
    decode_set_cookie,
    encode_cookies,
    decode_cookies,
    parse_date,
    format_date
)


def test_make_cookie():
    """Test make_cookie"""
    assert make_cookie(b'foo', b'bar') == b'foo=bar'
    assert make_cookie(
        b'sessionid', b'38afes7a8', http_only=True, path=b'/'
    ) == b'sessionid=38afes7a8; Path=/; HttpOnly'
    assert make_cookie(
        b'id',
        b'a3fWa',
        expires=datetime(2015, 10, 21, 7, 28, 0, tzinfo=timezone.utc),
        secure=True,
        http_only=True
    ) == b'id=a3fWa; Expires=Wed, 21 Oct 2015 07:28:00 GMT; Secure; HttpOnly'
    # pylint: disable=line-too-long
    assert make_cookie(
        b'qwerty',
        b'219ffwef9w0f',
        domain=b'somecompany.co.uk',
        path=b'/',
        expires=datetime(2019, 8, 30, 0, 0, 0, tzinfo=timezone.utc)
    ) == b'qwerty=219ffwef9w0f; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=somecompany.co.uk; Path=/'


def test_set_cookie():
    """Test encode and decode set-cookie"""
    # pylint: disable=line-too-long
    orig = b'qwerty=219ffwef9w0f; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=somecompany.co.uk; Path=/'
    unpacked = decode_set_cookie(orig)
    cookie = encode_set_cookie(**unpacked)
    assert orig == cookie
    print(unpacked)


def test_cookies():
    """Test encode and decode cookie"""
    orig = b'PHPSESSID=298zf09hf012fh2; csrftoken=u32t4o3tb3gg43; _gat=1'
    result = decode_cookies(orig)
    roundtrip = encode_cookies(result)
    assert orig == roundtrip

    trailing_semi = b'PHPSESSID=298zf09hf012fh2; csrftoken=u32t4o3tb3gg43; _gat=1;'
    result = decode_cookies(trailing_semi)
    roundtrip = encode_cookies(result)
    assert trailing_semi[:-1] == roundtrip


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
