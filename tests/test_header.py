from datetime import datetime
import bareutils.header as header


def test_content_length():
    headers = [
        (b'content-type', b'application/json'),
        (b'content-length', b'256')
    ]

    assert header.content_length(headers) == 256


def test_cookie():
    headers = [
        (b'content-type', b'application/json'),
        (b'cookie', b'foo=bar'),
        (b'cookie', b'one=first; two=second; three=third;'),
        (b'cookie', b'four=fourth; '),
        (b'cookie', b'four=fourth again; ')
    ]

    cookies = header.cookie(headers)
    assert len(cookies) == 5
    assert b'one' in cookies
    assert cookies[b'one'][0] == b'first'
    assert b'two' in cookies
    assert cookies[b'two'][0] == b'second'
    assert b'three' in cookies
    assert cookies[b'three'][0] == b'third'
    assert b'four' in cookies
    assert cookies[b'four'][0] == b'fourth'
    assert cookies[b'four'][1] == b'fourth again'


def test_vary():
    headers = [
        (b'content-type', b'application/json'),
        (b'vary', b'accept-encoding, user-agent'),
        (b'cookie', b'one=first; two=second; three=third;'),
        (b'cookie', b'four=fourth; ')
    ]

    vary = header.vary(headers)
    assert len(vary) == 2
    assert b'user-agent' in vary
    assert b'accept-encoding' in vary


def test_upsert():
    headers = [
        (b'content-type', b'application/json'),
        (b'vary', b'accept-encoding, user-agent'),
        (b'cookie', b'one=first; two=second; three=third;')
    ]

    header.upsert(b'content-type', b'text/plain', headers)
    assert len(header.find_all(b'content-type', headers)) == 1
    assert header.find(b'content-type', headers) == b'text/plain'

    header.upsert(b'content-encoding', b'gzip', headers)
    assert len(header.find_all(b'content-encoding', headers)) == 1
    assert header.find(b'content-encoding', headers) == b'gzip'


def test_to_dict():
    headers = [
        (b'content-type', b'application/json'),
        (b'vary', b'accept-encoding, user-agent'),
        (b'cookie', b'one=first; two=second; three=third;'),
        (b'cookie', b'four=fourth; ')
    ]

    dct = header.to_dict(headers)
    assert dct == {
        b'content-type': [b'application/json'],
        b'vary': [b'accept-encoding, user-agent'],
        b'cookie': [b'one=first; two=second; three=third;', b'four=fourth; ']
    }


def test_if_modified_since():
    headers = [
        (b'if-modified-since', b'Wed, 21 Oct 2015 07:28:00 GMT')
    ]
    assert header.if_modified_since(headers) == datetime(2015, 10, 21, 7, 28, 0)


def test_set_cookie():
    headers = [
        (b'set-cookie', b'foo=abcde; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/'),
        (b'set-cookie', b'foo=fghij; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/foo'),
        (b'set-cookie', b'foo=klmno; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'),
        (b'set-cookie', b'bar=12345; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'),
    ]
    unpacked = header.set_cookie(headers)
    assert b'foo' in unpacked and b'bar' in unpacked
    assert len(unpacked[b'foo']) == 3 and len(unpacked[b'bar']) == 1
