"""Tests for headers"""

from datetime import datetime, timezone
import bareutils.header as header


def test_upsert():
    """Test upsert"""
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
    """Test to_dict"""
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


def test_accept():
    """Test accept"""
    assert header.accept(
        [
            (b'accept', b'application/json')
        ]
    ) == {b'application/json': 1.0}
    assert header.accept([
        (
            b'accept',
            b'text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8'
        )
    ]) == {
        b'text/html': 1.0,
        b'application/xhtml+xml': 1.0,
        b'application/xml': 0.9,
        b'*/*': 0.8
    }

def test_accept_ch():
    """Test accept_ch"""
    assert header.accept_ch([
        (b'accept-ch', b'DPR, Viewport-Width')
    ]) == [b'DPR', b'Viewport-Width']

def test_accept_ch_lifetime():
    """Test for accept_ch_lifetime"""
    assert header.accept_ch_lifetime([
        (b'accept-ch-lifetime', b'86400')
    ]) == 86400

def test_accept_charset():
    """Test accept_charset"""
    assert header.accept_charset(
        [(b'accept-charset', b'utf-8')]) == {b'utf-8': 1.0}
    assert header.accept_charset([(b'accept-charset', b'utf-8, iso-8859-1;q=0.5')]) == {
        b'utf-8': 1.0,
        b'iso-8859-1': 0.5,
    }


def test_accept_encoding():
    """Test accept_encoding"""
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
    assert header.accept_encoding([
        (b'accept-encoding', b'deflate, gzip;q=1.0, *;q=0.5')
    ]) == {
        b'deflate': 1.0,
        b'gzip': 1.0,
        b'*': 0.5,
    }


def test_accept_language():
    """Test accept_language"""
    assert header.accept_language(
        [(b'accept-language', b'en-GB')]) == {b'en-GB': 1.0}
    assert header.accept_language([
        (b'accept-language', b'fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5')
    ]) == {
        b'fr-CH': 1.0,
        b'fr': 0.9,
        b'en': 0.8,
        b'de': 0.7,
        b'*': 0.5,
    }


def test_accept_patch():
    """Test accept_patch"""
    assert header.accept_patch([
        (b'accept-patch', b'application/example, text/example')
    ]) == [
        (b'application/example', None),
        (b'text/example', None),
    ]
    assert header.accept_patch([
        (b'accept-patch', b'text/example;charset=utf-8')
    ]) == [
        (b'text/example', b'utf-8'),
    ]
    assert header.accept_patch([
        (b'accept-patch', b'application/merge-patch+json')
    ]) == [
        (b'application/merge-patch+json', None)
    ]


def test_accept_ranges():
    """Test accept_ranges"""
    assert header.accept_ranges([(b'accept-ranges', b'bytes')]) == b'bytes'
    assert header.accept_ranges([(b'accept-ranges', b'none')]) == b'none'


def test_access_control_allow_credentials():
    """Test access_control_allow_credentials"""
    assert header.access_control_allow_credentials([
        (b'access-control-allow-credentials', b'true')
    ])


def test_access_control_allow_headers():
    """Test access_control_allow_headers"""
    assert header.access_control_allow_headers([
        (b'access-control-allow-headers', b'X-Custom-Header')
    ]) == [
        b'X-Custom-Header'
    ]
    assert header.access_control_allow_headers([
        (
            b'access-control-allow-headers',
            b'X-Custom-Header, Upgrade-Insecure-Requests'
        )
    ]) == [
        b'X-Custom-Header',
        b'Upgrade-Insecure-Requests'
    ]


def test_access_control_allow_origin():
    """Test access_control_allow_origin"""
    assert header.access_control_allow_origin(
        [(b'access-control-allow-origin', b'null')]) == b'null'
    assert header.access_control_allow_origin(
        [(b'access-control-allow-origin', b'*')]) == b'*'
    assert header.access_control_allow_origin([
        (b'access-control-allow-origin', b'https://developer.mozilla.org')
    ]) == b'https://developer.mozilla.org'


def test_access_control_allow_methods():
    """Test access_control_allow_methods"""
    assert header.access_control_allow_methods([
        (b'access-control-allow-methods', b'POST, GET, OPTIONS')
    ]) == [
        b'POST',
        b'GET',
        b'OPTIONS'
    ]

def test_authorization():
    """Test authorization"""
    assert header.authorization(
        [(b'authorization', b'Basic YWxhZGRpbjpvcGVuc2VzYW1l')]
    ) == (b'Basic', b'YWxhZGRpbjpvcGVuc2VzYW1l')

def test_content_length():
    """Test content_length"""
    headers = [
        (b'content-type', b'application/json'),
        (b'content-length', b'256')
    ]

    assert header.content_length(headers) == 256


def test_content_type():
    """Test content_type"""
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


def test_cookie():
    """Test cookie"""
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


def test_if_modified_since():
    """Test if_modified_since"""
    headers = [
        (b'if-modified-since', b'Wed, 21 Oct 2015 07:28:00 GMT')
    ]
    assert header.if_modified_since(
        headers) == datetime(2015, 10, 21, 7, 28, 0)


def test_last_modified():
    """Test last_modified"""
    headers = [
        (b'last-modified', b'Wed, 21 Oct 2015 07:28:00 GMT')
    ]
    assert header.last_modified(headers) == datetime(2015, 10, 21, 7, 28, 0)


def test_set_cookie():
    """Test set_cookie"""
    headers = [
        (
            b'set-cookie',
            b'foo=abcde; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/'
        ),
        (
            b'set-cookie',
            b'foo=fghij; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/foo'
        ),
        (
            b'set-cookie',
            b'foo=klmno; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'
        ),
        (
            b'set-cookie',
            b'bar=12345; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'
        ),
    ]
    unpacked = header.set_cookie(headers)
    assert b'foo' in unpacked and b'bar' in unpacked
    assert len(unpacked[b'foo']) == 3 and len(unpacked[b'bar']) == 1


def test_cache_control():
    """Test cache_control"""
    assert header.cache_control([(b'cache-control', b'public, max-age=31536000')]) == {
        b'public': None,
        b'max-age': 31536000
    }


def test_content_disposition():
    """Test content_disposition"""
    assert header.content_disposition([
        (b'content-disposition', b'attachment; filename="cool.html"')
    ]) == (
        b'attachment',
        {
            b'filename': b'cool.html'
        }
    )
    assert header.content_disposition([
        (b'content-disposition', b'form-data; name="field1"')
    ]) == (
        b'form-data',
        {
            b'name': b'field1'
        }
    )
    assert header.content_disposition([
        (
            b'content-disposition',
            b'form-data; name="field2"; filename="example.txt"'
        )
    ]) == (
        b'form-data',
        {
            b'name': b'field2',
            b'filename': b'example.txt'
        }
    )


def test_content_range():
    """Test content_range"""
    assert header.content_range([
        (b'content-range', b'bytes 200-1000/67589')
    ]) == (b'bytes', (200, 1000), 67589)
    assert header.content_range([
        (b'content-range', b'bytes 200-1000/*')
    ]) == (b'bytes', (200, 1000), None)
    assert header.content_range([
        (b'content-range', b'bytes */67589')
    ]) == (b'bytes', None, 67589)

def test_content_security_policy():
    """Test content_security_policy"""
    assert header.content_security_policy([
        (
            b'content-security-policy',
            b"default-src 'self' http://example.com; connect-src 'none';"
        )
    ]) == [
        (b'default-src', [b"'self'", b'http://example.com']),
        (b'connect-src', [b"'none'"])
    ]

def test_cross_origin_resource_policy():
    """Test cross_origin_resource_policy"""
    assert header.cross_origin_resource_policy([
        (b'cross-origin-resource-policy', b'same-site')
    ]) == b'same-site'

def test_date():
    """Test date"""
    assert header.date([
        (b'date', b'Wed, 21 Oct 2015 07:28:00 GMT')
    ]) == datetime(2015, 10, 21, 7, 28)

def test_dnt():
    """Test for dnt"""
    assert header.dnt([
        (b'DNT', b'1')
    ]) == 1

def test_dpr():
    """Test dpr"""
    assert header.dpr([
        (b'DPR', b'1.0')
    ]) == 1.0

def test_device_memory():
    """Test device_memory"""
    assert header.device_memory([
        (b'device-memory', b'0.5')
    ]) == 0.5

def test_expect():
    """Test expect"""
    assert header.expect([
        (b'expect', b'100-continue')
    ]) == b'100-continue'

def test_expires():
    """Test expires"""
    assert header.expires([
        (b'expires', b'Wed, 21 Oct 2015 07:28:00 GMT')
    ]) == datetime(2015, 10, 21, 7, 28)

def test_host():
    """Test host"""
    assert header.host([
        (b'host', b'developer.cdn.mozilla.net')
    ]) == (b'developer.cdn.mozilla.net', None)
    assert header.host([
        (b'host', b'localhost:8080')
    ]) == (b'localhost', 8080)

def test_location():
    """Test location"""
    assert header.location([
        (b'location', b'/index.html')
    ]) == b'/index.html'

def test_origin():
    """Test origin"""
    assert header.origin([
        (b'origin', b'https://developer.mozilla.org')
    ]) == b'https://developer.mozilla.org'

def test_referer():
    """Test referer"""
    assert header.referer([
        (b'referer', b'https://developer.mozilla.org/en-US/docs/Web/JavaScript')
    ]) == b'https://developer.mozilla.org/en-US/docs/Web/JavaScript'

def test_server():
    """Test server"""
    assert header.server([
        (b'server', b'Apache/2.4.1 (Unix)')
    ]) == b'Apache/2.4.1 (Unix)'

def test_vary():
    """Test vary"""
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


def test_collect():
    """Test collect"""
    headers = [
        (b'content-type', b'application/json'),
        (b'content-length', b'256'),
        (
            b'set-cookie',
            b'foo=abcde; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/'
        ),
        (
            b'set-cookie',
            b'foo=fghij; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=example.com; Path=/foo'
        ),
        (
            b'set-cookie',
            b'foo=klmno; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'
        ),
        (
            b'set-cookie',
            b'bar=12345; Expires=Fri, 30 Aug 2019 00:00:00 GMT; Domain=other.com; Path=/'
        ),
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
        (b'accept', b'text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8'),
        (b'authorization', b'Basic YWxhZGRpbjpvcGVuc2VzYW1l'),
        (b'host', b'developer.cdn.mozilla.net'),
        (b'expect', b'100-continue'),
        (b'date', b'Wed, 21 Oct 2015 07:28:00 GMT'),
        (b'expires', b'Wed, 21 Oct 2015 07:28:00 GMT'),
        (b'location', b'/index.html'),
        (b'origin', b'https://developer.mozilla.org'),
        (b'referer', b'https://developer.mozilla.org/en-US/docs/Web/JavaScript'),
        (b'server', b'Apache/2.4.1 (Unix)'),
        (
            b'content-security-policy',
            b"default-src 'self' http://example.com; connect-src 'none';"
        ),
        (b'cross-origin-resource-policy', b'same-site'),
        (b'DNT', b'1'),
        (b'DPR', b'1.0'),
        (b'device-memory', b'0.5'),
        (b'accept-ch', b'DPR, Viewport-Width'),
        (b'accept-ch', b'Width'),
        (b'accept-ch-lifetime', b'86400')
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
        },
        b'accept': {
            b'text/html': 1.0,
            b'application/xhtml+xml': 1.0,
            b'application/xml': 0.9,
            b'*/*': 0.8
        },
        b'authorization': (b'Basic', b'YWxhZGRpbjpvcGVuc2VzYW1l'),
        b'host': (b'developer.cdn.mozilla.net', None),
        b'expect': b'100-continue',
        b'date': datetime(2015, 10, 21, 7, 28),
        b'expires': datetime(2015, 10, 21, 7, 28),
        b'location': b'/index.html',
        b'origin': b'https://developer.mozilla.org',
        b'referer': b'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
        b'server': b'Apache/2.4.1 (Unix)',
        b'content-security-policy': [
            (b'default-src', [b"'self'", b'http://example.com']),
            (b'connect-src', [b"'none'"])
        ],
        b'cross-origin-resource-policy': b'same-site',
        b'DNT': 1,
        b'DPR': 1.0,
        b'device-memory': 0.5,
        b'accept-ch': [b'DPR', b'Viewport-Width', b'Width'],
        b'accept-ch-lifetime': 86400
    }
