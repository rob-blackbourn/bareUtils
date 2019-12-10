"""Header utilities"""

import collections
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Mapping, MutableMapping, Any, Tuple, Callable, NamedTuple
from baretypes import Headers
from .cookies import decode_cookies, decode_set_cookie


class _MergeType(Enum):
    NONE = auto()
    EXTEND = auto()
    APPEND = auto()
    CONCAT = auto()

class _Parser(NamedTuple):
    parse: Callable[[bytes], Any]
    merge_type: _MergeType


_PARSERS: MutableMapping[bytes, _Parser] = dict()


def _pass_through(value: bytes) -> bytes:
    return value


_DEFAULT_PARSER = _Parser(_pass_through, _MergeType.APPEND)


def index(name: bytes, headers: Headers) -> int:
    """Find the index of the header in the list.

    :param name: The header name.
    :param headers: The headers to search.
    :return: The index of the header or -1 if not found.
    """
    return next((i for i, (k, v) in enumerate(headers) if k == name), -1)


def find(name: bytes, headers: Headers, default: Optional[bytes] = None) -> Optional[bytes]:
    """Find the value of a header, or return a default value.

    :param name: The name of the header.
    :param headers: The headers to search.
    :param default: An optional default value, otherwise None.
    :return: The value of the header if found, otherwise the default value.
    """
    return next((v for k, v in headers if k == name), default)


def find_all(name: bytes, headers: Headers) -> List[bytes]:
    """Find all the values for a given header.

    :param name: The name of the header.
    :param headers: The headers to search.
    :return: A list of the header values which may be empty if there were none
        found.
    """
    return [v for k, v in headers if k == name]


def upsert(name: bytes, value: bytes, headers: Headers) -> None:
    """If the header exists overwrite the value, otherwise append a new value.

    :param name: The header name.
    :param value: The header value.
    :param headers: The headers.
    """
    for i, item in enumerate(headers):
        if item[0] == name:
            headers[i] = (name, value)
            return
    headers.append((name, value))


def to_dict(headers: Headers) -> MutableMapping[bytes, List[bytes]]:
    """Convert a list of headers into a dictionary where the key is the header
    name and the value is a list of the values of the headers for that name

    :param headers: A list of headers.
    :return: A dictionary where the key is the header name and the value is a
        list of the values of the headers for that name
    """
    items: MutableMapping[bytes, List[bytes]] = collections.defaultdict(list)
    for name, value in headers:
        items[name].append(value)
    return items


def find_date(name: bytes, headers: Headers) -> Optional[datetime]:
    """Find a header containing a date.

    :param name: The name of the header.
    :param headers: The headers.
    :return: The date if found, otherwise None.
    """
    value = find(name, headers)
    return datetime.strptime(value.decode(), '%a, %d %b %Y %H:%M:%S %Z') if value else None


def _parse_comma_separated_list(value: bytes) -> List[bytes]:
    return [item.strip() for item in value.split(b',')]


def _parse_int(value: bytes) -> int:
    return int(value)


def _parse_float(value: bytes) -> float:
    return float(value)


def _parse_date(value: bytes) -> datetime:
    """parse as date.

    :param value: The header value.
    :return: The date.
    """
    return datetime.strptime(value.decode(), '%a, %d %b %Y %H:%M:%S %Z')


def parse_quality(value: bytes) -> Optional[float]:
    """Parse a quality attribute of the form 'q=0.5'

    :param value: The attribute value
    :return: The value as a float or None if there was no value.
    :raises: ValueError if there was a 'q' qualifier, but no value.
    """
    if value == b'':
        return None
    name, quality = value.split(b'=')
    if name != b'q':
        raise ValueError('expected "q"')
    return float(quality)


def _parse_media_type_and_encoding(
        value: bytes
) -> Tuple[bytes, Optional[bytes]]:
    media_type, sep, rest = value.partition(b';')
    if not sep:
        encoding = None
    else:
        tag, sep, encoding = rest.partition(b'=')
        if tag != b'charset':
            raise Exception('encoding must start with chartset')
    return media_type.strip(), encoding.strip() if encoding else None


# Accept

def _parse_accept(value: bytes, *, add_wildcard: bool = False) -> Mapping[bytes, float]:
    values = {
        first: parse_quality(rest) or 1.0
        for first, sep, rest in [x.partition(b';') for x in value.split(b', ')]
    }

    if add_wildcard and b'*' not in values:
        values[b'*'] = 1.0

    return values


_PARSERS[b'accept'] = _Parser(_parse_accept, _MergeType.NONE)


def accept(
        headers: Headers,
        *,
        add_wildcard: bool = False,
        default: Optional[Mapping[bytes, float]] = None
) -> Optional[Mapping[bytes, float]]:
    """Returns the accept header it it exists.

    Where quality is not given it defaults to 1.0.

    >>> accept([(b'accept', b'text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8')])
    {b'text/html': 1.0, b'application/xhtml+xml': 1.0, b'application/xml': 0.9, b'*/*': 0.8}

    :param headers: The headers
    :type headers: Headers
    :param add_wildcard: If true add the implicit wildcard '*', defaults to False
    :type add_wildcard: bool, optional
    :param default: An optional default, defaults to None
    :type default: Optional[Mapping[bytes, float]]
    :return: A dictionary where the key is media type and the value is quality.
    :rtype: Optional[Mapping[bytes, float]]
    """
    value = find(b'accept', headers)
    return default if value is None else _parse_accept(value, add_wildcard=add_wildcard)

# Accept-CH

_PARSERS[b'accept-ch'] = _Parser(_parse_comma_separated_list, _MergeType.CONCAT)

def accept_ch(
        headers: Headers,
        *,
        default: Optional[List[bytes]] = None
) -> Optional[List[bytes]]:
    """The Accept-CH header is set by the server to specify which Client Hints
    headers client should include in subsequent requests.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[List[bytes]]
    :return: The client hints
    :rtype: Optional[List[bytes]]
    """
    value = find(b'accept-ch', headers)
    return default if value is None else _parse_comma_separated_list(value)

# Accept-CH-Lifetime

_PARSERS[b'accept-ch-lifetime'] = _Parser(_parse_int, _MergeType.NONE)

def accept_ch_lifetime(
        headers: Headers,
        *,
        default: Optional[int] = None
) -> Optional[int]:
    """The Accept-CH-Lifetime header is set by the server to specify the
    persistence of Accept-CH header value that specifies for which Client Hints
    headers client should include in subsequent requests.
    
    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[int], optional
    :return: The lifetime in seconds
    :rtype: Optional[int]
    """
    value = find(b'accept-ch-lifetime', headers)
    return default if value is None else _parse_int(value)


# Accept-Charset

def _parse_accept_charset(value: bytes, *, add_wildcard: bool = False) -> Mapping[bytes, float]:
    """Parses the accept charset header into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param value: The header value.
    :param add_wildcard: If True ensures the '*' charset is included.
    :return: A mapping of the encodings and qualities.
    """
    charsets = {
        first: parse_quality(rest) or 1.0
        for first, sep, rest in [x.partition(b';') for x in value.split(b', ')]
    }

    if add_wildcard and b'*' not in charsets:
        charsets[b'*'] = 1.0

    return charsets


_PARSERS[b'accept-charset'] = _Parser(_parse_accept_charset, _MergeType.NONE)


def accept_charset(
        headers: Headers,
        *,
        add_wildcard: bool = False,
        default: Optional[Mapping[bytes, float]] = None
) -> Optional[Mapping[bytes, float]]:
    """Extracts the accept encoding header if it exists into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param headers: The headers to search.
    :param add_wildcard: If True ensures the '*' charset is included.
    :param default: An optional default value, defaults to None
    :type default: Optional[Mapping[bytes, float]], optional
    :return: A mapping of the encodings and qualities.
    """
    value = find(b'accept-charset', headers)
    return default if value is None else _parse_accept_charset(value, add_wildcard=add_wildcard)

# Accept-Encoding

def _parse_accept_encoding(value: bytes, *, add_identity: bool = False) -> Mapping[bytes, float]:
    """Parses the accept encoding header into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param value: The header value.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: A mapping of the encodings and qualities.
    """
    encodings = {
        first: parse_quality(rest) or 1.0
        for first, sep, rest in [x.partition(b';') for x in value.split(b', ')]
    }

    if add_identity and b'identity' not in encodings:
        encodings[b'identity'] = 1.0

    return encodings


_PARSERS[b'accept-encoding'] = _Parser(_parse_accept_encoding, _MergeType.NONE)


def accept_encoding(
        headers: Headers,
        *,
        add_identity: bool = False,
        default: Optional[Mapping[bytes, float]] = None
) -> Optional[Mapping[bytes, float]]:
    """Extracts the accept encoding header if it exists into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param headers: The headers to search.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :param default: An optional default value
    :return: A mapping of the encodings and qualities.
    """
    value = find(b'accept-encoding', headers)
    return default if value is None else _parse_accept_encoding(value, add_identity=add_identity)


# Accept-Language

def _parse_accept_language(value: bytes, *, add_wildcard: bool = False) -> Mapping[bytes, float]:
    """Parses the accept language header into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param value: The header value.
    :param add_wildcard: If True ensures the '*' charset is included.
    :return: A mapping of the encodings and qualities.
    """
    languages = {
        first: parse_quality(rest) or 1.0
        for first, sep, rest in [x.partition(b';') for x in value.split(b', ')]
    }

    if add_wildcard and b'*' not in languages:
        languages[b'*'] = 1.0

    return languages


_PARSERS[b'accept-language'] = _Parser(_parse_accept_language, _MergeType.NONE)


def accept_language(
        headers: Headers,
        *,
        add_wildcard: bool = False,
        default: Optional[Mapping[bytes, float]] = None
) -> Optional[Mapping[bytes, float]]:
    """Extracts the accept language header if it exists into a mapping of the
    encoding and the quality value which defaults to 1.0 if missing.

    :param headers: The headers to search.
    :param add_wildcard: If True ensures the '*' charset is included.
    :param default: An optional default value.
    :return: A mapping of the encodings and qualities.
    """
    value = find(b'accept-language', headers)
    return default if value is None else _parse_accept_language(value, add_wildcard=add_wildcard)


# Accept-Patch

def _parse_accept_patch(value: bytes) -> List[Tuple[bytes, Optional[bytes]]]:
    """Parses the accept patch header returning a list of tuples of media type
    and encoding.

    :param value: The header value
    :return: A list of tuples of media type and encoding.
    """
    return [
        _parse_media_type_and_encoding(item)
        for item in value.split(b',')
    ]


_PARSERS[b'accept-patch'] = _Parser(_parse_accept_encoding, _MergeType.NONE)


def accept_patch(
        headers: Headers,
        *,
        default: Optional[List[Tuple[bytes, Optional[bytes]]]] = None
) -> Optional[List[Tuple[bytes, Optional[bytes]]]]:
    """The Accept-Patch response HTTP header advertises which media-type the
    server is able to understand.

    :param headers: The headers to search.
    :param default: An optional default value.
    :return: An optional list of tuples of media type and optional charset.
    """
    value = find(b'accept-patch', headers)
    return default if value is None else _parse_accept_patch(value)


# Accept-Ranges

def _parse_accept_ranges(value: bytes) -> bytes:
    return value.strip()


_PARSERS[b'accept-ranges'] = _Parser(_parse_accept_ranges, _MergeType.NONE)


def accept_ranges(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """Returns the value of the accept ranges header of None if missing

    :param headers: The headers
    :param default: An optional default value.
    :return: The header value (bytes or none)
    """
    value = find(b'accept-ranges', headers)
    return default if value is None else _parse_accept_ranges(value)


# Access-Control-Allow-Credentials

def _parse_access_control_allow_credentials(value: bytes) -> bool:
    return value.lower() == b'true'


_PARSERS[b'access-control-allow-credentials'] = _Parser(
    _parse_access_control_allow_credentials, _MergeType.NONE)


def access_control_allow_credentials(
        headers: Headers,
        *,
        default: Optional[bool] = None
) -> Optional[bool]:
    """Extracts the access control allow credentials header as a bool or None if missing.

    :param headers: The headers.
    :param default: An optional default value.
    :return: a bool or None
    """
    value = find(b'access-control-allow-credentials', headers)
    return default if value is None else _parse_access_control_allow_credentials(value)


# Access-Control-Allow-Headers

_PARSERS[b'access-control-allow-headers'] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE)


def access_control_allow_headers(
        headers: Headers,
        *,
        default: Optional[List[bytes]] = None
) -> Optional[List[bytes]]:
    """The Access-Control-Allow-Headers response header is used in response to
    a preflight request which includes the Access-Control-Request-Headers to
    indicate which HTTP headers can be used during the actual request.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value.
    :type default: Optional[List[bytes]]
    :return: A list of the allowed headers or '*' for all headers.
    :rtype: Optional[List[bytes]]
    """
    value = find(b'access-control-allow-headers', headers)
    return default if value is None else _parse_comma_separated_list(value)


# Access-Control-Allow-Methods

_PARSERS[b'access-control-allow-methods'] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE)


def access_control_allow_methods(
        headers: Headers,
        *,
        default: Optional[List[bytes]] = None
) -> Optional[List[bytes]]:
    """The Access-Control-Allow-Methods response header specifies the method or
    methods allowed when accessing the resource in response to a preflight
    request.

    :param headers: The headers
    :type headers: Headers
    :return: A list of the allowed methods, or '*' for all methods.
    :rtype: Optional[List[bytes]]
    """
    value = find(b'access-control-allow-methods', headers)
    return default if value is None else _parse_comma_separated_list(value)


# Access-Control-Allow-Origin

_PARSERS[b'access-control-allow-origin'] = _Parser(
    _pass_through, _MergeType.NONE)


def access_control_allow_origin(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """The Access-Control-Allow-Origin response header indicates whether the
    response can be shared with requesting code from the given origin.

    :param headers: The headers
    :type headers: Headers
    :return: The origin or '*' for all origins, or 'null'
    :rtype: Optional[bytes]
    """
    value = find(b'access-control-allow-origin', headers)
    return default if value is None else value

# Access-Control-Expose-Headers

def _parse_access_control_expose_headers(
        value: bytes,
        *,
        add_simple_response_headers: bool = False
) -> List[bytes]:
    headers = _parse_comma_separated_list(value)
    if add_simple_response_headers:
        headers.extend([
            b'cache-control',
            b'content-language',
            b'content-type',
            b'expires',
            b'last-modified',
            b'pragma',
        ])
    return headers


_PARSERS[b'access-control-expose-headers'] = _Parser(
    _parse_access_control_expose_headers, _MergeType.NONE)


def access_control_expose_headers(
        headers: Headers,
        *,
        add_simple_response_headers: bool = False,
        default: Optional[List[bytes]] = None
) -> Optional[List[bytes]]:
    """The Access-Control-Expose-Headers response header indicates which headers
    can be exposed as part of the response by listing their names.

    :param headers: The headers
    :type headers: Headers
    :param add_simple_response_headers: If true add the safelisted headers,
        defaults to False
    :type add_simple_response_headers: bool, optional
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: The headers to expose
    :rtype: Optional[List[bytes]]
    """
    value = find(b'access-control-expose-headers', headers)
    return default if value is None else _parse_access_control_expose_headers(
        value,
        add_simple_response_headers=add_simple_response_headers
    )

# Access-Control-Max-Age

_PARSERS[b'access-control-max-age'] = _Parser(_parse_int, _MergeType.NONE)


def access_control_max_age(
        headers: Headers,
        *,
        default: Optional[int]
) -> Optional[int]:
    """The Access-Control-Max-Age response header indicates how long the results
    of a preflight request (that is the information contained in the
    Access-Control-Allow-Methods and Access-Control-Allow-Headers headers) can
    be cached.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: The number of seconds
    :rtype: Optional[int]
    """
    value = find(b'access-control-max-age', headers)
    return default if value is None else _parse_int(value)

# Access-Control-Request-Headers

_PARSERS[b'access-control-request-headers'] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE)


def access_control_request_headers(
        headers: Headers,
        *,
        default: Optional[List[bytes]] = None
) -> Optional[List[bytes]]:
    """The Access-Control-Request-Headers request header is used by browsers
    when issuing a preflight request, to let the server know which HTTP headers
    the client might send when the actual request is made.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: The request headers
    :rtype: Optional[List[bytes]]
    """
    value = find(b'access-control-request-headers', headers)
    return default if value is None else _parse_comma_separated_list(value)

# Access-Control-Request-Method

_PARSERS[b'access-control-request-method'] = _Parser(
    _pass_through, _MergeType.NONE)

def access_control_request_method(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """The Access-Control-Request-Method request header is used by browsers when
    issuing a preflight request, to let the server know which HTTP method will
    be used when the actual request is made. This header is necessary as the
    preflight request is always an OPTIONS and doesn't use the same method as
    the actual request.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: The method
    :rtype: Optional[bytes]
    """
    value = find(b'access-control-request-method', headers)
    return default if value is None else _pass_through(value)

# Age

_PARSERS[b'age'] = _Parser(_parse_int, _MergeType.NONE)


def age(
        headers: Headers,
        *,
        default: Optional[int] = None
) -> Optional[int]:
    """The Age header contains the time in seconds the object has been in a
    proxy cache.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: The time in seconds
    :rtype: Optional[int]
    """
    value = find(b'age', headers)
    return None if value is None else _parse_int(value)

# Allow

_PARSERS[b'allow'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def allow(
        headers: Headers,
        *,
        default: Optional[List[bytes]] = None
) -> Optional[List[bytes]]:
    """The Allow header lists the set of methods supported by a resource.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: A list of methods
    :rtype: Optional[List[bytes]]
    """
    value = find(b'allow', headers)
    return default if value is None else _parse_comma_separated_list(value)

def _parse_authorization(value: bytes) -> Tuple[bytes, bytes]:
    auth_type, _, credentials = value.partition(b' ')
    return auth_type.strip(), credentials

_PARSERS[b'authorization'] = _Parser(_parse_authorization, _MergeType.NONE)

def authorization(
        headers: Headers,
        *,
        default: Optional[Tuple[bytes, bytes]] = None
) -> Optional[Tuple[bytes, bytes]]:
    """The HTTP Authorization request header contains the credentials to
    authenticate a user agent with a server, usually after the server has
    responded with a 401 Unauthorized status and the WWW-Authenticate header.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: The type and credentials
    :rtype: Optional[Tuple[bytes, bytes]]
    """
    value = find(b'authorization', headers)
    return default if value is None else _parse_authorization(value)

# Cache-Control

def _parse_cache_control(value: bytes) -> Mapping[bytes, Optional[int]]:
    return {
        name.strip(): int(rest) if sep == b'=' else None
        for name, sep, rest in [item.partition(b'=') for item in value.split(b',')]
    }


_PARSERS[b'cache-control'] = _Parser(_parse_cache_control, _MergeType.NONE)


def cache_control(
        headers: Headers,
        *,
        default: Optional[Mapping[bytes, Optional[int]]] = None
) -> Optional[Mapping[bytes, Optional[int]]]:
    """The Cache-Control general-header field is used to specify directives for
    caching mechanisms in both requests andresponses. Caching directives are
    unidirectional, meaning that a given directive in a request is not implying
    that the same directive is to be given in the response.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[Mapping[bytes, Optional[int]]]
    :return: A dictionary of the directives and values
    :rtype: Optional[Mapping[bytes, Optional[int]]]
    """
    value = find(b'cache-control', headers)
    return default if value is None else _parse_cache_control(value)


# Clear-Site-Data

_PARSERS[b'clear-site-data'] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE)


def clear_site_data(
        headers: Headers,
        *,
        default: Optional[List[bytes]]
) -> Optional[List[bytes]]:
    """The Clear-Site-Data header clears browsing data (cookies, storage, cache)
    associated with the requesting website. It allows web developers to have
    more control over the data stored locally by a browser for their origins.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: A list of the directives.
    :rtype: Optional[List[bytes]]
    """
    value = find(b'clear-site-data', headers)
    return default if value is None else _parse_comma_separated_list(value)


# Connection

_PARSERS[b'connection'] = _Parser(_pass_through, _MergeType.NONE)


def connection(
        headers: Headers,
        *,
        default: Optional[bytes]
) -> Optional[bytes]:
    """The Connection general header controls whether or not the network
    connection stays open after the current transaction finishes. If the value
    sent is keep-alive, the connection is persistent and not closed, allowing
    for subsequent requests to the same server to be done.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[List[bytes]]
    :return: The value
    :rtype: Optional[bytes]
    """
    value = find(b'connection', headers)
    return default if value is none else value

# Content-Disposition

def _parse_content_disposition(
        value: bytes
) -> Tuple[bytes, Optional[Mapping[bytes, bytes]]]:
    """Returns the content type

    :param value: The header value
    :return: A tuple of the media type and a mapping of the parameters or None
        if absent.
    """
    media_type, sep, rest = value.partition(b';')
    parameters = {
        first.strip(): rest.strip(b'"')
        for first, sep, rest in [x.partition(b'=') for x in rest.split(b';')] if first
    } if sep == b';' else None

    return media_type, parameters


_PARSERS[b'content-disposition'] = _Parser(
    _parse_content_disposition, _MergeType.NONE)


def content_disposition(
        headers: Headers
) -> Optional[Tuple[bytes, Optional[Mapping[bytes, bytes]]]]:
    """Returns the content type if any otherwise None

    :param headers: The headers
    :return: A tuple of the media type and a mapping of the parameters or None
        if absent.
    """
    value = find(b'content-disposition', headers)
    return None if value is None else _parse_content_disposition(value)

# Content-Encoding

def _parse_content_encoding(value: bytes, *, add_identity: bool = False) -> List[bytes]:
    """Parses the content encodings into a list.

    :param value: The header value.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: The list of content encodings or None is absent.
    """
    encodings = value.split(b', ')

    if add_identity and b'identity' not in encodings:
        encodings.append(b'identity')

    return encodings


_PARSERS[b'content-encoding'] = _Parser(
    _parse_content_encoding, _MergeType.NONE)


def content_encoding(headers: Headers, *, add_identity: bool = False) -> Optional[List[bytes]]:
    """Returns the content encodings in a list or None if they were not specified.

    :param headers: The headers.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: The list of content encodings or None is absent.
    """
    value = find(b'content-encoding', headers)
    return None if value is None else _parse_content_encoding(value, add_identity=add_identity)


# Content-Language

_PARSERS[b'content-language'] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE)


def content_language(headers: Headers) -> Optional[List[bytes]]:
    """The Content-Language entity header is used to describe the language(s)
    intended for the audience, so that it allows a user to differentiate
    according to the users' own preferred language.

    :param headers: The headers
    :type headers: Headers
    :return: The language
    :rtype: Optional[List[bytes]]
    """
    value = find(b'content-language', headers)
    return None if value is None else _parse_comma_separated_list(value)


# Content-Length

_PARSERS[b'content-length'] = _Parser(_parse_int, _MergeType.NONE)


def content_length(headers: Headers) -> Optional[int]:
    """Returns the content length as an integer if specified, otherwise None.

    :param headers: The headers.
    :return: The length as an integer or None is absent.
    """
    value = find(b'content-length', headers)
    return None if value is None else _parse_int(value)

# Content-Location

_PARSERS[b'content-location'] = _Parser(_pass_through, _MergeType.NONE)


def content_location(headers: Headers) -> Optional[bytes]:
    """The Content-Location header indicates an alternate location for the
    returned data. The principal use is to indicate the URL of a resource
    transmitted as the result of content negotiation.

    :param headers: The headers
    :type headers: Headers
    :return: The location
    :rtype: Optional[bytes]
    """
    return find(b'content-location', headers)

# Content-Range

def _parse_content_range(
        value: bytes
) -> Tuple[bytes, Optional[Tuple[int, int]], Optional[int]]:
    unit, _, rest = value.strip().partition(b' ')
    range_, _, size_ = rest.strip().partition(b'/')
    if range_ == b'*':
        from_to = None
    else:
        start, _, end = range_.partition(b'-')
        from_to = (int(start), int(end))
    size = None if size_.strip() == b'*' else int(size_)
    return unit, from_to, size


_PARSERS[b'content-range'] = _Parser(_parse_content_range, _MergeType.NONE)


def content_range(
        headers: Headers
) -> Optional[Tuple[bytes, Optional[Tuple[int, int]], Optional[int]]]:
    """The Content-Range response HTTP header indicates where in a full body
    message a partial message belongs.

    :param headers: The headers
    :type headers: Headers
    :return: The content-range header if found/
    :rtype: Optional[Tuple[bytes, Optional[Tuple[int, int]], Optional[int]]]
    """
    value = find(b'content-range', headers)
    return None if value is None else _parse_content_range(value)

# Content-Security-Policy

def _parse_content_security_policy(value: bytes) -> List[Tuple[bytes, List[bytes]]]:
    return [
        (directive.strip(), args.strip().split(b' '))
        for directive, sep, args in [
            policy_directive.strip().partition(b' ')
            for policy_directive in value.strip().split(b';')
        ]
        if sep
    ]

_PARSERS[b'content-security-policy'] = _Parser(_parse_content_security_policy, _MergeType.CONCAT)

def content_security_policy(
        headers: Headers,
        *,
        default: Optional[List[Tuple[bytes, List[bytes]]]] = None
) -> Optional[List[Tuple[bytes, List[bytes]]]]:
    """The HTTP Content-Security-Policy response header allows web site
    administrators to control resources the user agent is allowed to load for a
    given page. With a few exceptions, policies mostly involve specifying server
    origins and script endpoints. This helps guard against cross-site scripting
    attacks (XSS).

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value
    :type default: Optional[List[Tuple[bytes, List[bytes]]]], default None
    :return: The policy
    :rtype: Optional[List[Tuple[bytes, List[bytes]]]]
    """
    value = find(b'content-security-policy', headers)
    return default if value is None else _parse_content_security_policy(value)

# Content-Security-Policy-Report-Only

_PARSERS[b'content-security-policy-report-only'] = _Parser(
    _parse_content_security_policy,
    _MergeType.CONCAT
)

def content_security_policy_report_only(
        headers: Headers,
        *,
        default: Optional[List[Tuple[bytes, List[bytes]]]] = None
) -> Optional[List[Tuple[bytes, List[bytes]]]]:
    """The HTTP Content-Security-Policy-Report-Only response header allows web
    developers to experiment with policies by monitoring (but not enforcing)
    their effects. These violation reports consist of JSON documents sent via an
    HTTP POST request to the specified URI.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value
    :type default: Optional[List[Tuple[bytes, List[bytes]]]], default None
    :return: The policy
    :rtype: Optional[List[Tuple[bytes, List[bytes]]]]
    """
    value = find(b'content-security-policy-report-only', headers)
    return default if value is None else _parse_content_security_policy(value)

# Content-Type

def _parse_content_type(
        value: bytes
) -> Tuple[bytes, Optional[Mapping[bytes, bytes]]]:
    """Returns the content type

    :param value: The header value
    :return: A tuple of the media type and a mapping of the parameters or None if absent.
    """
    media_type, sep, rest = value.partition(b';')
    parameters = {
        first.strip(): rest.strip()
        for first, sep, rest in [x.partition(b'=') for x in rest.split(b';')] if first
    } if sep == b';' else None

    return media_type, parameters


_PARSERS[b'content-type'] = _Parser(_parse_content_type, _MergeType.NONE)


def content_type(
        headers: Headers
) -> Optional[Tuple[bytes, Optional[Mapping[bytes, bytes]]]]:
    """Returns the content type if any otherwise None

    :param headers: The headers
    :return: A tuple of the media type and a mapping of the parameters or None if absent.
    """
    value = find(b'content-type', headers)
    return None if value is None else _parse_content_type(value)

# Cookie

def _parse_cookie(value: bytes) -> Mapping[bytes, List[bytes]]:
    """Returns the cookies as a name-value mapping.

    :param value: The header value.
    :return: The cookies as a name-value mapping.
    """
    cookies: MutableMapping[bytes, List[bytes]] = dict()
    for name, content in decode_cookies(value).items():
        cookies.setdefault(name, []).extend(content)
    return cookies


_PARSERS[b'cookie'] = _Parser(_parse_cookie, _MergeType.EXTEND)


def cookie(headers: Headers) -> Mapping[bytes, List[bytes]]:
    """Returns the cookies as a name-value mapping.

    :param headers: The headers.
    :return: The cookies as a name-value mapping.
    """
    cookies: MutableMapping[bytes, List[bytes]] = dict()
    for value in find_all(b'cookie', headers):
        for name, content in _parse_cookie(value).items():
            cookies.setdefault(name, []).extend(content)
    return cookies

# Cross-Origin-Resource-Policy

_PARSERS[b'cross-origin-resource-policy'] = _Parser(
    _pass_through,
    _MergeType.NONE
)

def cross_origin_resource_policy(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """The HTTP Cross-Origin-Resource-Policy response header conveys a desire
    that the browser blocks no-cors cross-origin/cross-site requests to the
    given resource.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value
    :type default: Optional[bytes]
    :return: The policy
    :rtype: Optional[bytes]
    """
    value = find(b'cross-origin-resource-policy', headers)
    return default if value is None else value


# Date

_PARSERS[b'date'] = _Parser(_parse_date, _MergeType.NONE)

def date(
        headers: Headers,
        *,
        default: Optional[datetime] = None
) -> Optional[datetime]:
    """The Date general HTTP header contains the date and time at which the
    message was originated.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[datetime], optional
    :return: The date and time at which the message was originated
    :rtype: Optional[datetime]
    """
    value = find(b'date', headers)
    return default if value is None else _parse_date(value)

# DNT

_PARSERS[b'DNT'] = _Parser(_parse_int, _MergeType.NONE)

def dnt(
        headers: Headers,
        *,
        default: Optional[int] = None
) -> Optional[int]:
    """The DNT (Do Not Track) request header indicates the user's tracking
    preference. It lets users indicate whether they would prefer privacy rather
    than personalized content.
    
    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[int], optional
    :return: 0 for allow tracking, 1 for deny tracking
    :rtype: Optional[int]
    """
    value = find(b'DNT', headers)
    return default if value is None else _parse_int(value)

# DPR

_PARSERS[b'DPR'] = _Parser(_parse_float, _MergeType.NONE)

def dpr(headers: Headers, *, default: Optional[float] = None) -> Optional[float]:
    """The DPR header is a Client Hints headers which represents the client
    device pixel ratio (DPR), which is the the number of physical device pixels
    corresponding to every CSS pixel.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[float], optional
    :return: The device pixel ratio
    :rtype: Optional[float]
    """
    value = find(b'DPR', headers)
    return default if value is None else _parse_float(value)

# Device-Memory

_PARSERS[b'device-memory'] = _Parser(_parse_float, _MergeType.NONE)

def device_memory(
        headers: Headers,
        *,
        default: Optional[float] = None
) -> Optional[float]:
    """The Device-Memory header is a Device Memory API header that works like
    Client Hints header which represents the approximate amount of RAM client
    device has.
    
    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[float], optional
    :return: The device memory
    :rtype: Optional[float]
    """
    value = find(b'device-memory', headers)
    return default if value is None else _parse_float(value)


# Expect

_PARSERS[b'expect'] = _Parser(_pass_through, _MergeType.NONE)

def expect(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """Returns the expect header
    
    :param headers: The headers
    :type headers: Headers
    :param default: An optional default value, defaults to None
    :type default: Optional[bytes], optional
    :return: The expect directive
    :rtype: Optional[bytes]
    """
    value = find(b'expect', headers)
    return default if value is None else value

# Expires

_PARSERS[b'expires'] = _Parser(_parse_date, _MergeType.NONE)

def expires(
        headers: Headers,
        *,
        default: Optional[datetime] = None
) -> Optional[datetime]:
    """The Expires header contains the date/time after which the response is
    considered stale.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[datetime], optional
    :return: The date/time after which the response is considered stale
    :rtype: Optional[datetime]
    """
    value = find(b'expires', headers)
    return default if value is None else _parse_date(value)

# From

_PARSERS[b'from'] = _Parser(_pass_through, _MergeType.NONE)

# Host

def _parse_host(value: bytes) -> Tuple[bytes, Optional[int]]:
    host_, sep, port = value.partition(b':')
    return (host_, None) if not sep else (host_, int(port))

_PARSERS[b'host'] = _Parser(_parse_host, _MergeType.NONE)

def host(
        headers: Headers,
        *,
        default: Optional[Tuple[bytes, Optional[int]]] = None
) ->  Optional[Tuple[bytes, Optional[int]]]:
    """Returns the host header as a name, port tuple
    
    :param headers: The headers
    :type headers: Headers
    :param default: Optional default, defaults to None
    :type default: Optional[Tuple[bytes, Optional[int]]], optional
    :return: The host as a name, port tuple.
    :rtype: Optional[Tuple[bytes, Optional[int]]]
    """
    value = find(b'host', headers)
    return default if value is None else _parse_host(value)

# If-Modified-Since

_PARSERS[b'if-modified-since'] = _Parser(_parse_date, _MergeType.NONE)

def if_modified_since(headers: Headers) -> Optional[datetime]:
    """The If-Modified-Since request HTTP header makes the request conditional:
    the server will send back the requested resource, with a 200 status, only if
    it has been last modified after the given date. If the request has not been
    modified since, the response will be a 304 without any body; the
    Last-Modified response header of a previous request will contain the date of
    last modification. Unlike If-Unmodified-Since, If-Modified-Since can only be
    used with a GET or HEAD.

    :param headers: The headers
    :type headers: Headers
    :return: The timestamp
    :rtype: Optional[datetime]
    """
    value = find(b'if-modified-since', headers)
    return None if value is None else _parse_date(value)

# Last-Modified

_PARSERS[b'last-modified'] = _Parser(_parse_date, _MergeType.NONE)


def last_modified(headers: Headers) -> Optional[datetime]:
    """The Last-Modified response HTTP header contains the date and time at
    which the origin server believes the resource was last modified. It is used
    as a validator to determine if a resource received or stored is the same.
    Less accurate than an ETag header, it is a fallback mechanism. Conditional
    requests containing If-Modified-Since or If-Unmodified-Since headers make
    use of this field.

    :param headers: The headers
    :type headers: Headers
    :return: The timestamp
    :rtype: Optional[datetime]
    """
    value = find(b'last-modified', headers)
    return None if value is None else _parse_date(value)


# Location

_PARSERS[b'location'] = _Parser(_pass_through, _MergeType.NONE)

def location(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """The Location response header indicates the URL to redirect a page to. It
    only provides a meaning when served with a 3xx (redirection) or 201
    (created) status response.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[bytes], optional
    :return: The redirect location
    :rtype: Optional[datetime]
    """
    value = find(b'location', headers)
    return default if value is None else value

# Origin

_PARSERS[b'origin'] = _Parser(_pass_through, _MergeType.NONE)

def origin(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """The Origin request header indicates where a fetch originates from. It
    doesn't include any path information, but only the server name. It is sent
    with CORS requests, as well as with POST requests. It is similar to the
    Referer header, but, unlike this header, it doesn't disclose the whole path.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[bytes], optional
    :return: The origins
    :rtype: Optional[datetime]
    """
    value = find(b'origin', headers)
    return default if value is None else value

# Referer

_PARSERS[b'referer'] = _Parser(_pass_through, _MergeType.NONE)

def referer(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """The Referer request header contains the address of the previous web page
    from which a link to the currently requested page was followed. The Referer
    header allows servers to identify where people are visiting them from and
    may use that data for analytics, logging, or optimized caching, for example.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[bytes], optional
    :return: The referer
    :rtype: Optional[datetime]
    """
    value = find(b'referer', headers)
    return default if value is None else value

# Server

_PARSERS[b'server'] = _Parser(_pass_through, _MergeType.NONE)

def server(
        headers: Headers,
        *,
        default: Optional[bytes] = None
) -> Optional[bytes]:
    """The Server header contains information about the software used by the
    origin server to handle the request.

    :param headers: The headers
    :type headers: Headers
    :param default: An optional default, defaults to None
    :type default: Optional[bytes], optional
    :return: The product directive
    :rtype: Optional[datetime]
    """
    value = find(b'server', headers)
    return default if value is None else value

# Set-Cookie

_PARSERS[b'set-cookie'] = _Parser(decode_set_cookie, _MergeType.APPEND)


def set_cookie(headers: Headers) -> Mapping[bytes, List[Mapping[str, Any]]]:
    """Returns the cookies as a name-value mapping.

    :param headers: The headers.
    :return: The cookies as a name-value mapping.
    """
    set_cookies: MutableMapping[bytes, List[Mapping[str, Any]]] = dict()
    for header in find_all(b'set-cookie', headers):
        decoded = decode_set_cookie(header)
        set_cookies.setdefault(decoded['name'], []).append(decoded)
    return set_cookies


# Vary

def _parse_vary(value: bytes) -> List[bytes]:
    """Returns the vary header value as a list of headers.

    :param value: The header value.
    :return: A list of the vary headers.
    """
    return value.split(b', ') if value is not None else None


_PARSERS[b'vary'] = _Parser(_parse_vary, _MergeType.NONE)


def vary(headers: Headers) -> Optional[List[bytes]]:
    """Returns the vary header value as a list of headers.

    :param headers: The headers.
    :return: A list of the vary headers.
    """
    value = find(b'vary', headers)
    return None if value is None else _parse_vary(value)

def collect(headers: Headers) -> Mapping[bytes, Any]:
    """Collect all headers into a mapping

    :param headers: The headers
    :type headers: Headers
    :return: A mapping of the parsed headers
    :rtype: Mapping[bytes, Any]
    """
    collection: MutableMapping[bytes, Any] = dict()
    for name, value in headers:
        parser = _PARSERS.get(name, _DEFAULT_PARSER)
        if parser.merge_type == _MergeType.APPEND:
            result = parser.parse(value)
            collection.setdefault(name, []).append(result)
        elif parser.merge_type == _MergeType.CONCAT:
            result = parser.parse(value)
            collection.setdefault(name, []).extend(result)
        elif parser.merge_type == _MergeType.EXTEND:
            result = parser.parse(value)
            dct = collection.setdefault(name, dict())
            for k, v in result.items():
                dct.setdefault(k, []).extend(v)
        else:
            collection[name] = parser.parse(value)
    return collection
