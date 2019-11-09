from datetime import datetime, timezone
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
    assert header.if_modified_since(
        headers) == datetime(2015, 10, 21, 7, 28, 0)


def test_last_modified():
    headers = [
        (b'last-modified', b'Wed, 21 Oct 2015 07:28:00 GMT')
    ]
    assert header.last_modified(headers) == datetime(2015, 10, 21, 7, 28, 0)


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


def test_content_type():
    media_type, params = header.content_type(
        [(b'content-type', b'application/json')])
    assert media_type == b'application/json' and params is None
    media_type, params = header.content_type(
        [(b'content-type', b'text/html; charset=utf-8')])
    assert media_type == b'text/html' and params is not None
    assert len(params) == 1 and params[b'charset'] == b'utf-8'
    media_type, params = header.content_type(
        [(b'content-type', b'multipart/form-data; boundary=something')])
    assert media_type == b'multipart/form-data' and params is not None
    assert len(params) == 1 and params[b'boundary'] == b'something'


def test_accept_charset():
    assert header.accept_charset(
        [(b'accept-charset', b'utf-8')]) == {b'utf-8': 1.0}
    assert header.accept_charset([(b'accept-charset', b'utf-8, iso-8859-1;q=0.5')]) == {
        b'utf-8': 1.0,
        b'iso-8859-1': 0.5,
    }


def test_accept_encoding():
    assert header.accept_encoding(
        [(b'accept-encoding', b'gzip')]) == {b'gzip': 1.0}
    assert header.accept_encoding(
        [(b'accept-encoding', b'compress')]) == {b'compress': 1.0}
    assert header.accept_encoding(
        [(b'accept-encoding', b'deflate')]) == {b'deflate': 1.0}
    assert header.accept_encoding(
        [(b'accept-encoding', b'br')]) == {b'br': 1.0}
    assert header.accept_encoding(
        [(b'accept-encoding', b'identity')]) == {b'identity': 1.0}
    assert header.accept_encoding([(b'accept-encoding', b'*')]) == {b'*': 1.0}
    assert header.accept_encoding([(b'accept-encoding', b'deflate, gzip;q=1.0, *;q=0.5')]) == {
        b'deflate': 1.0,
        b'gzip': 1.0,
        b'*': 0.5,
    }


def test_accept():
    assert header.accept(
        [
            (b'accept', b'application/json')
        ]
    ) == {b'application/json': 1.0}
    assert header.accept(
        [
            (b'accept', b'text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8')
        ]
    ) == {
        b'text/html': 1.0,
        b'application/xhtml+xml': 1.0,
        b'application/xml': 0.9,
        b'*/*': 0.8
    }


def test_accept_language():
    assert header.accept_language(
        [(b'accept-language', b'en-GB')]) == {b'en-GB': 1.0}
    assert header.accept_language([(b'accept-language', b'fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5')]) == {
        b'fr-CH': 1.0,
        b'fr': 0.9,
        b'en': 0.8,
        b'de': 0.7,
        b'*': 0.5,
    }


def test_accept_patch():
    assert header.accept_patch([(b'accept-patch', b'application/example, text/example')]) == [
        (b'application/example', None),
        (b'text/example', None),
    ]
    assert header.accept_patch([(b'accept-patch', b'text/example;charset=utf-8')]) == [
        (b'text/example', b'utf-8'),
    ]
    assert header.accept_patch([(b'accept-patch', b'application/merge-patch+json')]) == [
        (b'application/merge-patch+json', None),
    ]


def test_accept_ranges():
    assert header.accept_ranges([(b'accept-ranges', b'bytes')]) == b'bytes'
    assert header.accept_ranges([(b'accept-ranges', b'none')]) == b'none'


def test_access_control_allow_credentials():
    assert header.access_control_allow_credentials(
        [(b'access-control-allow-credentials', b'true')]) == True


def test_access_control_allow_headers():
    assert header.access_control_allow_headers([(b'access-control-allow-headers', b'X-Custom-Header')]) == [
        b'X-Custom-Header'
    ]
    assert header.access_control_allow_headers(
        [(b'access-control-allow-headers', b'X-Custom-Header, Upgrade-Insecure-Requests')]
    ) == [
        b'X-Custom-Header',
        b'Upgrade-Insecure-Requests'
    ]


def test_access_control_allow_origin():
    assert header.access_control_allow_origin(
        [(b'access-control-allow-origin', b'null')]) == b'null'
    assert header.access_control_allow_origin(
        [(b'access-control-allow-origin', b'*')]) == b'*'
    assert header.access_control_allow_origin(
        [(b'access-control-allow-origin', b'https://developer.mozilla.org')]) == b'https://developer.mozilla.org'


def test_access_control_allow_methods():
    assert header.access_control_allow_methods([(b'access-control-allow-methods', b'POST, GET, OPTIONS')]) == [
        b'POST',
        b'GET',
        b'OPTIONS'
    ]


def test_cache_control():
    assert header.cache_control([(b'cache-control', b'public, max-age=31536000')]) == {
        b'public': None,
        b'max-age': 31536000
    }


def test_content_disposition():
    assert header.content_disposition([(b'content-disposition', b'attachment; filename="cool.html"')]) == (
        b'attachment',
        {
            b'filename': b'cool.html'
        }
    )
    assert header.content_disposition([(b'content-disposition', b'form-data; name="field1"')]) == (
        b'form-data',
        {
            b'name': b'field1'
        }
    )
    assert header.content_disposition(
        [(b'content-disposition', b'form-data; name="field2"; filename="example.txt"')]
    ) == (
        b'form-data',
        {
            b'name': b'field2',
            b'filename': b'example.txt'
        }
    )


def test_content_range():
    assert header.content_range(
        [(b'content-range', b'bytes 200-1000/67589')]) == (b'bytes', (200, 1000), 67589)
    assert header.content_range(
        [(b'content-range', b'bytes 200-1000/*')]) == (b'bytes', (200, 1000), None)
    assert header.content_range(
        [(b'content-range', b'bytes */67589')]) == (b'bytes', None, 67589)


def test_collect():
    headers = [
        (b'content-type', b'application/json'),
        (b'content-length', b'256'),
        (b'set-cookie', b'foo=abcde; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/'),
        (b'set-cookie', b'foo=fghij; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/foo'),
        (b'set-cookie', b'foo=klmno; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'),
        (b'set-cookie', b'bar=12345; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'),
        (b'if-modified-since', b'Wed, 21 Oct 2015 07:28:00 GMT'),
        (b'last-modified', b'Wed, 21 Oct 2015 07:28:00 GMT'),
        (b'vary', b'accept-encoding, user-agent'),
        (b'cookie', b'foo=bar'),
        (b'cookie', b'one=first; two=second; three=third;'),
        (b'cookie', b'four=fourth; '),
        (b'cookie', b'four=fourth again; '),
        (b'accept-encoding', b'deflate, gzip;q=1.0, *;q=0.5'),
        (b'accept-charset', b'utf-8, iso-8859-1;q=0.5'),
        (b'accept-language', b'fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5'),
    ]
    result = header.collect(headers)
    assert result == {
        b'content-type': (b'application/json', None),
        b'content-length': 256,
        b'set-cookie': [
            {
                'name': b'foo',
                'value': b'abcde',
                'expires': datetime(2019, 8, 30, 0, 0, tzinfo=timezone.utc),
                'domain': b'example.com',
                'path': b'/'
            },
            {
                'name': b'foo',
                'value': b'fghij',
                'expires': datetime(2019, 8, 30, 0, 0, tzinfo=timezone.utc),
                'domain': b'example.com',
                'path': b'/foo'
            },
            {
                'name': b'foo',
                'value': b'klmno',
                'expires': datetime(2019, 8, 30, 0, 0, tzinfo=timezone.utc),
                'domain': b'other.com',
                'path': b'/'
            },
            {
                'name': b'bar',
                'value': b'12345',
                'expires': datetime(2019, 8, 30, 0, 0, tzinfo=timezone.utc),
                'domain': b'other.com',
                'path': b'/'
            }
        ],
        b'if-modified-since': datetime(2015, 10, 21, 7, 28),
        b'last-modified': datetime(2015, 10, 21, 7, 28),
        b'vary': [b'accept-encoding', b'user-agent'],
        b'cookie': {
            b'foo': [b'bar'],
            b'one': [b'first'],
            b'two': [b'second'],
            b'three': [b'third'],
            b'four': [b'fourth', b'fourth again']
        },
        b'accept-encoding': {
            b'deflate': 1.0,
            b'gzip': 1.0,
            b'*': 0.5,
        },
        b'accept-charset': {
            b'utf-8': 1.0,
            b'iso-8859-1': 0.5,
        },
        b'accept-language': {
            b'fr-CH': 1.0,
            b'fr': 0.9,
            b'en': 0.8,
            b'de': 0.7,
            b'*': 0.5,
        }
    }
