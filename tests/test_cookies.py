"""Tests for cookies.py"""

from datetime import datetime, timedelta, timezone

import pytest

from bareutils.cookies import (
    encode_set_cookie,
    decode_set_cookie,
    encode_cookies,
    decode_cookies,
    make_cookie,
    make_expired_cookie,
)


def test_make_cookie() -> None:
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


def test_set_cookie() -> None:
    """Test encode and decode set-cookie"""
    # pylint: disable=line-too-long
    orig = b'qwerty=219ffwef9w0f; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=somecompany.co.uk; Path=/'
    unpacked = decode_set_cookie(orig)
    cookie = encode_set_cookie(**unpacked)
    assert orig == cookie


def test_cookies() -> None:
    """Test encode and decode cookie"""
    orig = b'PHPSESSID=298zf09hf012fh2; csrftoken=u32t4o3tb3gg43; _gat=1'
    result = decode_cookies(orig)
    roundtrip = encode_cookies(result)
    assert orig == roundtrip

    trailing_semi = b'PHPSESSID=298zf09hf012fh2; csrftoken=u32t4o3tb3gg43; _gat=1;'
    result = decode_cookies(trailing_semi)
    roundtrip = encode_cookies(result)
    assert trailing_semi[:-1] == roundtrip


def test_secure_cookies() -> None:
    """Test secure cookies"""
    set_cookie = encode_set_cookie(b'__Secure-', b'Secure', secure=True)
    cookie = decode_set_cookie(set_cookie)
    assert cookie['secure'] is True

    with pytest.raises(ValueError):
        encode_set_cookie(b'__Secure-', b'Not secure!', secure=False)

    encode_set_cookie(b'__Host-', b'Secure', secure=True)
    with pytest.raises(ValueError):
        encode_set_cookie(b'__Host-', b'Not secure!', secure=False)


def test_max_age() -> None:
    """Test max-age"""
    set_cookie = encode_set_cookie(
        b'foo',
        b'bar',
        max_age=10
    )
    assert set_cookie == b'foo=bar; Max-Age=10'
    cookie = decode_set_cookie(set_cookie)
    assert cookie['max_age'] == timedelta(seconds=10)

    assert encode_set_cookie(
        b'foo',
        b'bar',
        max_age=timedelta(seconds=10)
    ) == b'foo=bar; Max-Age=10'

    assert encode_set_cookie(
        b'foo',
        b'bar',
        max_age=timedelta(days=1)
    ) == b'foo=bar; Max-Age=86400'


def test_same_site() -> None:
    """Test same-site"""
    set_cookie = encode_set_cookie(
        b'foo',
        b'bar',
        same_site=b'Lax'
    )
    assert set_cookie == b'foo=bar; SameSite=Lax'
    cookie = decode_set_cookie(set_cookie)
    assert cookie['same_site'] == b'Lax'

    assert encode_set_cookie(
        b'foo',
        b'bar',
        same_site=b'Strict'
    ) == b'foo=bar; SameSite=Strict'

    assert encode_set_cookie(
        b'foo',
        b'bar',
        same_site=b'None'
    ) == b'foo=bar; SameSite=None'


def test_http_only() -> None:
    """Test for HttpOnly cookies"""
    set_cookie = encode_set_cookie(
        b'foo',
        b'bar',
        http_only=True
    )
    assert set_cookie == b'foo=bar; HttpOnly'
    cookie = decode_set_cookie(set_cookie)
    assert cookie['http_only'] is True

    set_cookie = encode_set_cookie(
        b'foo',
        b'bar',
        http_only=False
    )
    assert set_cookie == b'foo=bar'


def test_make_expired_cookie() -> None:
    """Test make_expired_cookie"""
    assert make_expired_cookie(
        b'foo', b'/'
    ) == b'foo=; Max-Age=0; Path=/'
