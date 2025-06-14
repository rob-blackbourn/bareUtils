"""Header utilities

A collection of functions to extract headers from the ASGI scope.
"""

import collections
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    NamedTuple,
)

from .cookies import decode_cookies, decode_set_cookie
from .dates.rfc_7231 import parse_date

type Header = tuple[bytes, bytes]


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


def index(name: bytes, headers: Iterable[tuple[bytes, bytes]]) -> int:
    """Find the index of the header in the list.

    Args:
        name (bytes): The header name.
        headers (Iterable[tuple[bytes, bytes]]): The headers to search.

    Returns:
        int: The index of the header or -1 if not found.
    """
    return next((i for i, (k, _) in enumerate(headers) if k == name), -1)


def find(
        name: bytes,
        headers: Iterable[tuple[bytes, bytes]],
        default: bytes | None = None
) -> bytes | None:
    """Find the value of a header, or return a default value.

    Args:
        name (bytes): The header name.
        headers (Iterable[tuple[bytes, bytes]]): The headers to search.
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The value of the header if found, otherwise the default value.
    """
    return next((v for k, v in headers if k == name), default)


def find_exact(
        name: bytes,
        headers: Iterable[tuple[bytes, bytes]]
) -> bytes:
    """Find the value of a header, or raise an error.

    Args:
        name (bytes): The header name.
        headers (Iterable[tuple[bytes, bytes]]): The headers to search.

    Raises:
        KeyError: If the name was not found.

    Returns:
        bytes: The value of the header.
    """
    for k, v in headers:
        if k == name:
            return v
    raise KeyError


def find_all(name: bytes, headers: Iterable[tuple[bytes, bytes]]) -> list[bytes]:
    """Find all the values for a given header.

    Args:
        name (bytes): The header name.
        headers (Iterable[tuple[bytes, bytes]]): The headers to search.

    Returns:
        list[bytes]: A list of the header values which may be empty if there
            were none found.
    """
    return [v for k, v in headers if k == name]


def upsert(
        name: bytes,
        value: bytes,
        headers: list[tuple[bytes, bytes]]
) -> None:
    """If the header exists overwrite the value, otherwise append a new value.

    Args:
        name (bytes): The header name.
        value (bytes): The header value.
        headers (list[tuple[bytes, bytes]]): The headers.
    """
    for i, item in enumerate(headers):
        if item[0] == name:
            headers[i] = (name, value)
            return
    headers.append((name, value))


def to_dict(
        headers: Iterable[tuple[bytes, bytes]]
) -> dict[bytes, list[bytes]]:
    """Convert a list of headers into a dictionary where the key is the header
    name and the value is a list of the values of the headers for that name

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.

    Returns:
        dict[bytes, list[bytes]]: A dictionary where the key is the
            header name and the value is a list of the values of the headers for
            that name
    """
    items: dict[bytes, list[bytes]] = collections.defaultdict(list)
    for name, value in headers:
        items[name].append(value)
    return items


def _parse_date(value: bytes) -> datetime:
    return parse_date(value.decode())


def find_date(
        name: bytes,
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: datetime | None = None
) -> datetime | None:
    """Find a header containing a date.

    Args:
        name (bytes): The name of the header.
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (datetime | None, optional): The headers, Defaults to None.

    Returns:
        datetime | None: The date if found, otherwise the default value.
    """
    value = find(name, headers)
    return default if not value else _parse_date(value)


def _parse_comma_separated_list(value: bytes) -> list[bytes]:
    return [item.strip() for item in value.split(b',')]


def _parse_int(value: bytes) -> int:
    return int(value)


def _parse_float(value: bytes) -> float:
    return float(value)


def _parse_quality(value: bytes) -> float | None:
    if value == b'':
        return None
    name, quality = value.split(b'=')
    if name != b'q':
        raise ValueError('expected "q"')
    return float(quality)


def _parse_media_type_and_encoding(
        value: bytes
) -> tuple[bytes, bytes | None]:
    media_type, sep, rest = value.partition(b';')
    if not sep:
        encoding = None
    else:
        tag, sep, encoding = rest.partition(b'=')
        if tag != b'charset':
            raise ValueError('encoding must start with charset')
    return media_type.strip(), encoding.strip() if encoding else None


ACCEPT = b'accept'


def _parse_accept_params(value: bytes) -> Mapping[bytes, Any]:
    if value == b'':
        return {b'q': 1.0}
    return {
        name.strip(): float(token.strip()) if name == b'q' else token.strip()
        for name, _sep, token in [
            param.partition(b'=')
            for param in value.split(b';')
        ]
    }


def _parse_accept(
        value: bytes,
        *,
        add_wildcard: bool = False
) -> Mapping[bytes, Mapping[bytes, Any]]:
    values = {
        media_type: _parse_accept_params(params)
        for media_type, _sep, params in [
            x.strip().partition(b';') for x in value.split(b',')
        ]
    }

    if add_wildcard and b'*' not in values:
        values[b'*'] = {b'q': 1.0}

    return values


_PARSERS[ACCEPT] = _Parser(_parse_accept, _MergeType.NONE)


def accept(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        add_wildcard: bool = False,
        default: Mapping[bytes, Mapping[bytes, Any]] | None = None
) -> Mapping[bytes, Mapping[bytes, Any]] | None:
    """Returns the accept header if it exists.

    Where quality is not given it defaults to 1.0.

    ```python
    >>> accept([(b'accept', b'text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8')])
    {b'text/html': {b'q': 1.0}, b'application/xhtml+xml': {b'q': 1.0}, b'application/xml': {b'q': 0.9}, b'*/*': {b'q': 0.8}}
    ```

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        add_wildcard (bool, optional): If true add the implicit wildcard '*'.
            Defaults to False.
        default (Optional[Mapping[bytes, Mapping[bytes, Any]]], optional): An optional
            default. Defaults to None.

    Returns:
        Optional[Mapping[bytes, Mapping[bytes, Any]]]: A dictionary where the key
            is media type and the value is a mapping of the parameters.
    """
    value = find(ACCEPT, headers)
    return default if value is None else _parse_accept(value, add_wildcard=add_wildcard)


ACCEPT_CH = b'accept-ch'

_PARSERS[ACCEPT_CH] = _Parser(_parse_comma_separated_list, _MergeType.CONCAT)


def accept_ch(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """The Accept-CH header is set by the server to specify which Client Hints
    headers client should include in subsequent requests.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (Optional[Mapping[bytes, float]], optional): An optional
            default. Defaults to None.

    Returns:
        list[bytes] | None: The client hints
    """
    value = find(ACCEPT_CH, headers)
    return default if value is None else _parse_comma_separated_list(value)


ACCEPT_CH_LIFETIME = b'accept-ch-lifetime'

_PARSERS[ACCEPT_CH_LIFETIME] = _Parser(_parse_int, _MergeType.NONE)


def accept_ch_lifetime(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: int | None = None
) -> int | None:
    """The Accept-CH-Lifetime header is set by the server to specify the
    persistence of Accept-CH header value that specifies for which Client Hints
    headers client should include in subsequent requests.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (Optional[Mapping[bytes, float]], optional): An optional
            default. Defaults to None.

    Returns:
        int | None: The lifetime in seconds
    """
    value = find(ACCEPT_CH_LIFETIME, headers)
    return default if value is None else _parse_int(value)


ACCEPT_CHARSET = b'accept-charset'


def _parse_accept_charset(value: bytes, *, add_wildcard: bool = False) -> Mapping[bytes, float]:
    charsets = {
        first: _parse_quality(rest) or 1.0
        for first, _, rest in [x.partition(b';') for x in value.split(b', ')]
    }

    if add_wildcard and b'*' not in charsets:
        charsets[b'*'] = 1.0

    return charsets


_PARSERS[ACCEPT_CHARSET] = _Parser(_parse_accept_charset, _MergeType.NONE)


def accept_charset(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        add_wildcard: bool = False,
        default: Mapping[bytes, float] | None = None
) -> Mapping[bytes, float] | None:
    """Extracts the accept encoding header if it exists into a mapping of the
    encoding and the quality value which defaults to 1.0 if missing.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        add_wildcard (bool, optional): If True ensures the '*' charset is
            included. Defaults to False.
        default (Optional[Mapping[bytes, float]], optional): An optional
            default. Defaults to None.

    Returns:
        Optional[Mapping[bytes, float]]: A mapping of the encodings and qualities.
    """
    value = find(ACCEPT_CHARSET, headers)
    return default if value is None else _parse_accept_charset(
        value,
        add_wildcard=add_wildcard
    )


ACCEPT_ENCODING = b'accept-encoding'


def _parse_accept_encoding(value: bytes, *, add_identity: bool = False) -> Mapping[bytes, float]:
    encodings = {
        first: _parse_quality(rest) or 1.0
        for first, _, rest in [x.partition(b';') for x in value.split(b', ')]
    }

    if add_identity and b'identity' not in encodings:
        encodings[b'identity'] = 1.0

    return encodings


_PARSERS[ACCEPT_ENCODING] = _Parser(_parse_accept_encoding, _MergeType.NONE)


def accept_encoding(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        add_identity: bool = False,
        default: Mapping[bytes, float] | None = None
) -> Mapping[bytes, float] | None:
    """Extracts the accept encoding header if it exists into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers to search.
        add_identity (bool, optional): If True ensures the 'identity' encoding
            is included.. Defaults to False.
        default (Optional[Mapping[bytes, float]], optional): An optional
            default. Defaults to None.

    Returns:
        Optional[Mapping[bytes, float]]: A mapping of the encodings and qualities.
    """
    value = find(ACCEPT_ENCODING, headers)
    return default if value is None else _parse_accept_encoding(value, add_identity=add_identity)


ACCEPT_LANGUAGE = b'accept-language'


def _parse_accept_language(value: bytes, *, add_wildcard: bool = False) -> Mapping[bytes, float]:
    languages = {
        first: _parse_quality(rest) or 1.0
        for first, _, rest in [x.partition(b';') for x in value.split(b', ')]
    }

    if add_wildcard and b'*' not in languages:
        languages[b'*'] = 1.0

    return languages


_PARSERS[ACCEPT_LANGUAGE] = _Parser(_parse_accept_language, _MergeType.NONE)


def accept_language(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        add_wildcard: bool = False,
        default: Mapping[bytes, float] | None = None
) -> Mapping[bytes, float] | None:
    """Extracts the accept language header if it exists into a mapping of the
    encoding and the quality value which defaults to 1.0 if missing.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers to search.
        add_wildcard (bool, optional): If True ensures the '*' charset is
            included. Defaults to False.
        default (Optional[Mapping[bytes, float]], optional): [description].
            Defaults to None.

    Returns:
        Optional[Mapping[bytes, float]]: A mapping of the encodings and
            qualities.
    """
    value = find(ACCEPT_LANGUAGE, headers)
    return default if value is None else _parse_accept_language(value, add_wildcard=add_wildcard)


ACCEPT_PATCH = b'accept-patch'


def _parse_accept_patch(value: bytes) -> list[tuple[bytes, bytes | None]]:
    return [
        _parse_media_type_and_encoding(item)
        for item in value.split(b',')
    ]


_PARSERS[ACCEPT_PATCH] = _Parser(_parse_accept_encoding, _MergeType.NONE)


def accept_patch(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[tuple[bytes, bytes | None]] | None = None
) -> list[tuple[bytes, bytes | None]] | None:
    """The Accept-Patch response HTTP header advertises which media-type the
    server is able to understand.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers to search.
        default (Optional[list[tuple[bytes, bytes | None]]], optional): An
            optional default value. Defaults to None.

    Returns:
        Optional[list[tuple[bytes, bytes | None]]]: A list of tuples of media
            type and optional charset.
    """
    value = find(ACCEPT_PATCH, headers)
    return default if value is None else _parse_accept_patch(value)


ACCEPT_RANGES = b'accept-ranges'


def _parse_accept_ranges(value: bytes) -> bytes:
    return value.strip()


_PARSERS[ACCEPT_RANGES] = _Parser(_parse_accept_ranges, _MergeType.NONE)


def accept_ranges(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """Returns the value of the accept ranges header of None if missing

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The header value (bytes or none)
    """
    value = find(ACCEPT_RANGES, headers)
    return default if value is None else _parse_accept_ranges(value)


ACCESS_CONTROL_ALLOW_CREDENTIALS = b'access-control-allow-credentials'


def _parse_access_control_allow_credentials(value: bytes) -> bool:
    return value.lower() == b'true'


_PARSERS[ACCESS_CONTROL_ALLOW_CREDENTIALS] = _Parser(
    _parse_access_control_allow_credentials,
    _MergeType.NONE
)


def access_control_allow_credentials(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bool | None = None
) -> bool | None:
    """Extracts the access control allow credentials header as a bool or None if
    missing.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (Optional[bool], optional): An optional default value. Defaults
            to None.

    Returns:
        Optional[bool]: A bool or None
    """
    value = find(ACCESS_CONTROL_ALLOW_CREDENTIALS, headers)
    return default if value is None else _parse_access_control_allow_credentials(value)


ACCESS_CONTROL_ALLOW_HEADERS = b'access-control-allow-headers'

_PARSERS[ACCESS_CONTROL_ALLOW_HEADERS] = _Parser(
    _parse_comma_separated_list,
    _MergeType.NONE
)


def access_control_allow_headers(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """The Access-Control-Allow-Headers response header is used in response to
    a preflight request which includes the Access-Control-Request-Headers to
    indicate which HTTP headers can be used during the actual request.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: A list of the allowed headers or '*' for all headers.
    """
    value = find(ACCESS_CONTROL_ALLOW_HEADERS, headers)
    return default if value is None else _parse_comma_separated_list(value)


ACCESS_CONTROL_ALLOW_METHODS = b'access-control-allow-methods'

_PARSERS[ACCESS_CONTROL_ALLOW_METHODS] = _Parser(
    _parse_comma_separated_list,
    _MergeType.NONE
)


def access_control_allow_methods(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """The Access-Control-Allow-Methods response header specifies the method or
    methods allowed when accessing the resource in response to a preflight
    request.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: A list of the allowed methods, or '*' for all
            methods.
    """
    value = find(ACCESS_CONTROL_ALLOW_METHODS, headers)
    return default if value is None else _parse_comma_separated_list(value)


ACCESS_CONTROL_ALLOW_ORIGIN = b'access-control-allow-origin'

_PARSERS[ACCESS_CONTROL_ALLOW_ORIGIN] = _Parser(_pass_through, _MergeType.NONE)


def access_control_allow_origin(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Access-Control-Allow-Origin response header indicates whether the
    response can be shared with requesting code from the given origin.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        bytes | None: The origin or '*' for all origins, or 'null'
    """
    value = find(ACCESS_CONTROL_ALLOW_ORIGIN, headers)
    return default if value is None else value


ACCESS_CONTROL_EXPOSE_HEADERS = b'access-control-expose-headers'


def _parse_access_control_expose_headers(
        value: bytes,
        *,
        add_simple_response_headers: bool = False
) -> list[bytes]:
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


_PARSERS[ACCESS_CONTROL_EXPOSE_HEADERS] = _Parser(
    _parse_access_control_expose_headers,
    _MergeType.NONE
)


def access_control_expose_headers(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        add_simple_response_headers: bool = False,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """[summary]

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        add_simple_response_headers (bool, optional): If true add the safe-listed
            headers. Defaults to False.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: The headers to expose.
    """
    value = find(ACCESS_CONTROL_EXPOSE_HEADERS, headers)
    return default if value is None else _parse_access_control_expose_headers(
        value,
        add_simple_response_headers=add_simple_response_headers
    )


ACCESS_CONTROL_MAX_AGE = b'access-control-max-age'

_PARSERS[ACCESS_CONTROL_MAX_AGE] = _Parser(_parse_int, _MergeType.NONE)


def access_control_max_age(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: int | None = None
) -> int | None:
    """The Access-Control-Max-Age response header indicates how long the results
    of a preflight request (that is the information contained in the
    Access-Control-Allow-Methods and Access-Control-Allow-Headers headers) can
    be cached.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (int | None, optional): An optional default value. Defaults
            to None.

    Returns:
        int | None: The number of seconds
    """
    value = find(ACCESS_CONTROL_MAX_AGE, headers)
    return default if value is None else _parse_int(value)


ACCESS_CONTROL_REQUEST_HEADERS = b'access-control-request-headers'

_PARSERS[ACCESS_CONTROL_REQUEST_HEADERS] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE)


def access_control_request_headers(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """The Access-Control-Request-Headers request header is used by browsers
    when issuing a preflight request, to let the server know which HTTP headers
    the client might send when the actual request is made.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: The request headers
    """
    value = find(ACCESS_CONTROL_REQUEST_HEADERS, headers)
    return default if value is None else _parse_comma_separated_list(value)


ACCESS_CONTROL_REQUEST_METHOD = b'access-control-request-method'

_PARSERS[ACCESS_CONTROL_REQUEST_METHOD] = _Parser(
    _pass_through, _MergeType.NONE)


def access_control_request_method(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Access-Control-Request-Method request header is used by browsers when
    issuing a preflight request, to let the server know which HTTP method will
    be used when the actual request is made. This header is necessary as the
    preflight request is always an OPTIONS and doesn't use the same method as
    the actual request.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The method
    """
    value = find(ACCESS_CONTROL_REQUEST_METHOD, headers)
    return default if value is None else _pass_through(value)


AGE = b'age'

_PARSERS[AGE] = _Parser(_parse_int, _MergeType.NONE)


def age(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: int | None = None
) -> int | None:
    """The Age header contains the time in seconds the object has been in a
    proxy cache.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (int | None, optional): An optional default value. Defaults to None.

    Returns:
        int | None: The time in seconds.
    """
    value = find(AGE, headers)
    return default if value is None else _parse_int(value)


ALLOW = b'allow'

_PARSERS[b'allow'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def allow(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """The Allow header lists the set of methods supported by a resource.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: A list of methods
    """
    value = find(ALLOW, headers)
    return default if value is None else _parse_comma_separated_list(value)


AUTHORIZATION = b'authorization'


def _parse_authorization(value: bytes) -> tuple[bytes, bytes]:
    auth_type, _, credentials = value.partition(b' ')
    return auth_type.strip(), credentials


_PARSERS[AUTHORIZATION] = _Parser(_parse_authorization, _MergeType.NONE)


def authorization(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: tuple[bytes, bytes] | None = None
) -> tuple[bytes, bytes] | None:
    """The HTTP Authorization request header contains the credentials to
    authenticate a user agent with a server, usually after the server has
    responded with a 401 Unauthorized status and the WWW-Authenticate header.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (tuple[bytes, bytes] | None, optional): An optional default
            value. Defaults to None.

    Returns:
        tuple[bytes, bytes] | None: The type and credentials.
    """
    value = find(AUTHORIZATION, headers)
    return default if value is None else _parse_authorization(value)


CACHE_CONTROL = b'cache-control'


def _parse_cache_control(value: bytes) -> Mapping[bytes, int | None]:
    return {
        name.strip(): int(rest) if sep == b'=' else None
        for name, sep, rest in [item.partition(b'=')
                                for item in value.split(b',')]
    }


_PARSERS[CACHE_CONTROL] = _Parser(_parse_cache_control, _MergeType.NONE)


def cache_control(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: Mapping[bytes, int | None] | None = None
) -> Mapping[bytes, int | None] | None:
    """The Cache-Control general-header field is used to specify directives for
    caching mechanisms in both requests and responses. Caching directives are
    unidirectional, meaning that a given directive in a request is not implying
    that the same directive is to be given in the response.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (Mapping[bytes, int | None] | None, optional): An optional
            default value. Defaults to None.

    Returns:
        Mapping[bytes, int | None] | None: A dictionary of the directives
            and values.
    """
    value = find(CACHE_CONTROL, headers)
    return default if value is None else _parse_cache_control(value)


CLEAR_SITE_DATA = b'clear-site-data'

_PARSERS[CLEAR_SITE_DATA] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE)


def clear_site_data(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """The Clear-Site-Data header clears browsing data (cookies, storage, cache)
    associated with the requesting website. It allows web developers to have
    more control over the data stored locally by a browser for their origins.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: A list of the directives.
    """
    value = find(CLEAR_SITE_DATA, headers)
    return default if value is None else _parse_comma_separated_list(value)


CONNECTION = b'connection'

_PARSERS[CONNECTION] = _Parser(_pass_through, _MergeType.NONE)


def connection(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Connection general header controls whether or not the network
    connection stays open after the current transaction finishes. If the value
    sent is keep-alive, the connection is persistent and not closed, allowing
    for subsequent requests to the same server to be done.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The value
    """
    value = find(CONNECTION, headers)
    return default if value is None else value


CONTENT_DISPOSITION = b'content-disposition'


def _parse_content_disposition(
        value: bytes
) -> tuple[bytes, Mapping[bytes, bytes] | None]:
    media_type, sep, rest = value.partition(b';')
    parameters = {
        first.strip(): rest.strip(b'"')
        for first, _, rest in [x.partition(b'=') for x in rest.split(b';')] if first
    } if sep == b';' else None

    return media_type, parameters


_PARSERS[CONTENT_DISPOSITION] = _Parser(
    _parse_content_disposition, _MergeType.NONE)


def content_disposition(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: tuple[bytes, Mapping[bytes, bytes] | None] | None = None
) -> tuple[bytes, Mapping[bytes, bytes] | None] | None:
    """Returns the content type if any otherwise None

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (tuple[bytes, Mapping[bytes, bytes] | None] | None, optional): An
            optional default. Defaults to None.

    Returns:
        tuple[bytes, Mapping[bytes, bytes] | None] | None: A tuple of the
            media type and a mapping of the parameters.
    """
    value = find(CONTENT_DISPOSITION, headers)
    return default if value is None else _parse_content_disposition(value)


CONTENT_ENCODING = b'content-encoding'


def _parse_content_encoding(value: bytes, *, add_identity: bool = False) -> list[bytes]:
    encodings = value.split(b', ')

    if add_identity and b'identity' not in encodings:
        encodings.append(b'identity')

    return encodings


_PARSERS[CONTENT_ENCODING] = _Parser(
    _parse_content_encoding,
    _MergeType.NONE
)


def content_encoding(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        add_identity: bool = False,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """Returns the content encodings in a list or None if they were not
    specified.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        add_identity (bool, optional): If True ensures the 'identity' encoding
            is included. Defaults to False.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: The list of content encodings.
    """
    value = find(CONTENT_ENCODING, headers)
    return default if value is None else _parse_content_encoding(
        value,
        add_identity=add_identity
    )


CONTENT_LANGUAGE = b'content-language'

_PARSERS[CONTENT_LANGUAGE] = _Parser(
    _parse_comma_separated_list, _MergeType.NONE
)


def content_language(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """The Content-Language entity header is used to describe the language(s)
    intended for the audience, so that it allows a user to differentiate
    according to the users' own preferred language.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: The language.
    """
    value = find(CONTENT_LANGUAGE, headers)
    return default if value is None else _parse_comma_separated_list(value)


CONTENT_LENGTH = b'content-length'

_PARSERS[CONTENT_LENGTH] = _Parser(_parse_int, _MergeType.NONE)


def content_length(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: int | None = None
) -> int | None:
    """[summary]

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (int | None, optional): An optional default value. Defaults
            to None.

    Returns:
        int | None: The length as an integer, or the default.
    """
    value = find(CONTENT_LENGTH, headers)
    return default if value is None else _parse_int(value)


CONTENT_LOCATION = b'content-location'

_PARSERS[CONTENT_LOCATION] = _Parser(_pass_through, _MergeType.NONE)


def content_location(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Content-Location header indicates an alternate location for the
    returned data. The principal use is to indicate the URL of a resource
    transmitted as the result of content negotiation.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The location, or the default.
    """
    return find(CONTENT_LOCATION, headers, default=default)


CONTENT_RANGE = b'content-range'


def _parse_content_range(
        value: bytes
) -> tuple[bytes, tuple[int, int] | None, int | None]:
    unit, _, rest = value.strip().partition(b' ')
    range_, _, size_ = rest.strip().partition(b'/')
    if range_ == b'*':
        from_to = None
    else:
        start, _, end = range_.partition(b'-')
        from_to = (int(start), int(end))
    size = None if size_.strip() == b'*' else int(size_)
    return unit, from_to, size


_PARSERS[CONTENT_RANGE] = _Parser(_parse_content_range, _MergeType.NONE)


def content_range(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: tuple[bytes, tuple[int, int]
                       | None, int | None] | None = None,
) -> tuple[bytes, tuple[int, int] | None, int | None] | None:
    """The Content-Range response HTTP header indicates where in a full body
    message a partial message belongs.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (tuple[bytes, tuple[int, int] | None, int | None] | None, optional): An
            optional default value. Defaults to None.

    Returns:
        tuple[bytes, tuple[int, int] | None, int | None] | None: The
            content-range header if found, or the default.
    """
    value = find(CONTENT_RANGE, headers)
    return default if value is None else _parse_content_range(value)


CONTENT_SECURITY_POLICY = b'content-security-policy'


def _parse_content_security_policy(value: bytes) -> list[tuple[bytes, list[bytes]]]:
    return [
        (directive.strip(), args.strip().split(b' '))
        for directive, sep, args in [
            policy_directive.strip().partition(b' ')
            for policy_directive in value.strip().split(b';')
        ]
        if sep
    ]


_PARSERS[CONTENT_SECURITY_POLICY] = _Parser(
    _parse_content_security_policy, _MergeType.CONCAT)


def content_security_policy(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[tuple[bytes, list[bytes]]] | None = None
) -> list[tuple[bytes, list[bytes]]] | None:
    """The HTTP Content-Security-Policy response header allows web site
    administrators to control resources the user agent is allowed to load for a
    given page. With a few exceptions, policies mostly involve specifying server
    origins and script endpoints. This helps guard against cross-site scripting
    attacks (XSS).

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (list[tuple[bytes, list[bytes]]]] | None optional): An
            optional default. Defaults to None.

    Returns:
        list[tuple[bytes, list[bytes]]]] | None The policy or the default.
    """
    value = find(CONTENT_SECURITY_POLICY, headers)
    return default if value is None else _parse_content_security_policy(value)


CONTENT_SECURITY_POLICY_REPORT_ONLY = b'content-security-policy-report-only'

_PARSERS[CONTENT_SECURITY_POLICY_REPORT_ONLY] = _Parser(
    _parse_content_security_policy,
    _MergeType.CONCAT
)


def content_security_policy_report_only(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[tuple[bytes, list[bytes]]] | None = None
) -> list[tuple[bytes, list[bytes]]] | None:
    """The HTTP Content-Security-Policy-Report-Only response header allows web
    developers to experiment with policies by monitoring (but not enforcing)
    their effects. These violation reports consist of JSON documents sent via an
    HTTP POST request to the specified URI.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[tuple[bytes, list[bytes]]]] | None optional): An
            optional default value. Defaults to None.

    Returns:
        list[tuple[bytes, list[bytes]]]] | None The policy, or the default.
    """
    value = find(CONTENT_SECURITY_POLICY_REPORT_ONLY, headers)
    return default if value is None else _parse_content_security_policy(value)


CONTENT_TYPE = b'content-type'


def _parse_content_type(
        value: bytes
) -> tuple[bytes, Mapping[bytes, bytes] | None]:
    media_type, sep, rest = value.partition(b';')
    parameters = {
        first.strip(): rest.strip()
        for first, _, rest in [x.partition(b'=')
                               for x in rest.split(b';')]
        if first
    } if sep == b';' else None

    return media_type, parameters


_PARSERS[CONTENT_TYPE] = _Parser(_parse_content_type, _MergeType.NONE)


def content_type(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: tuple[bytes, Mapping[bytes, bytes] | None] | None = None
) -> tuple[bytes, Mapping[bytes, bytes] | None] | None:
    """Returns the content type if any otherwise None

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (tuple[bytes, Mapping[bytes, bytes] | None] | None, optional): An
            optional default value. Defaults to None.

    Returns:
        tuple[bytes, Mapping[bytes, bytes] | None] | None: A tuple of the
            media type and a mapping of the parameters or the default if absent.
    """
    value = find(CONTENT_TYPE, headers)
    return default if value is None else _parse_content_type(value)


COOKIE = b'cookie'


def _parse_cookie(value: bytes) -> Mapping[bytes, list[bytes]]:
    cookies: MutableMapping[bytes, list[bytes]] = {}
    for name, content in decode_cookies(value).items():
        cookies.setdefault(name, []).extend(content)
    return cookies


_PARSERS[COOKIE] = _Parser(_parse_cookie, _MergeType.EXTEND)


def cookie(headers: Iterable[tuple[bytes, bytes]]) -> Mapping[bytes, list[bytes]]:
    """Returns the cookies as a name-value mapping.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.

    Returns:
        Mapping[bytes, list[bytes]]: The cookies as a name-value mapping.
    """
    cookies: MutableMapping[bytes, list[bytes]] = {}
    for value in find_all(COOKIE, headers):
        for name, content in _parse_cookie(value).items():
            cookies.setdefault(name, []).extend(content)
    return cookies


CROSS_ORIGIN_RESOURCE_POLICY = b'cross-origin-resource-policy'

_PARSERS[CROSS_ORIGIN_RESOURCE_POLICY] = _Parser(
    _pass_through,
    _MergeType.NONE
)


def cross_origin_resource_policy(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The HTTP Cross-Origin-Resource-Policy response header conveys a desire
    that the browser blocks no-cors cross-origin/cross-site requests to the
    given resource.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The policy if present or the default.
    """
    value = find(CROSS_ORIGIN_RESOURCE_POLICY, headers)
    return default if value is None else value


DATE = b'date'

_PARSERS[DATE] = _Parser(_parse_date, _MergeType.NONE)


def date(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: datetime | None = None
) -> datetime | None:
    """The Date general HTTP header contains the date and time at which the
    message was originated.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (datetime | None, optional): An optional default value.
            Defaults to None.

    Returns:
        datetime | None: The date and time at which the message was originated
    """
    return find_date(DATE, headers, default=default)


DNT = b'DNT'

_PARSERS[DNT] = _Parser(_parse_int, _MergeType.NONE)


def dnt(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: int | None = None
) -> int | None:
    """The DNT (Do Not Track) request header indicates the user's tracking
    preference. It lets users indicate whether they would prefer privacy rather
    than personalized content.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (int | None, optional): An optional default value. Defaults
            to None.

    Returns:
        int | None: 0 for allow tracking, 1 for deny tracking or the default.
    """
    value = find(DNT, headers)
    return default if value is None else _parse_int(value)


DPR = b'DPR'

_PARSERS[DPR] = _Parser(_parse_float, _MergeType.NONE)


def dpr(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: float | None = None
) -> float | None:
    """The DPR header is a Client Hints headers which represents the client
    device pixel ratio (DPR), which is the the number of physical device pixels
    corresponding to every CSS pixel.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (float | None, optional): An optional default value. Defaults
            to None.

    Returns:
        float | None: The device pixel ratio if present, or the default value.
    """
    value = find(DPR, headers)
    return default if value is None else _parse_float(value)


DEVICE_MEMORY = b'device-memory'

_PARSERS[DEVICE_MEMORY] = _Parser(_parse_float, _MergeType.NONE)


def device_memory(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: float | None = None
) -> float | None:
    """The Device-Memory header is a Device Memory API header that works like
    Client Hints header which represents the approximate amount of RAM client
    device has.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (float | None, optional): An optional default value.
            Defaults to None.

    Returns:
        float | None: The device memory
    """
    value = find(DEVICE_MEMORY, headers)
    return default if value is None else _parse_float(value)


ETAG = b'etag'

EXPECT = b'expect'

_PARSERS[EXPECT] = _Parser(_pass_through, _MergeType.NONE)


def expect(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """Returns the expect header

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value.
            Defaults to None.

    Returns:
        bytes | None: The expect directive if present, or the default value.
    """
    value = find(EXPECT, headers)
    return default if value is None else value


EXPIRES = b'expires'

_PARSERS[b'expires'] = _Parser(_parse_date, _MergeType.NONE)


def expires(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: datetime | None = None
) -> datetime | None:
    """The Expires header contains the date/time after which the response is
    considered stale.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (datetime | None, optional): An optional default value.
            Defaults to None.

    Returns:
        datetime | None: The date/time after which the response is considered
            stale, or the default value.
    """
    return find_date(EXPIRES, headers, default=default)


FROM = b'from'

_PARSERS[b'from'] = _Parser(_pass_through, _MergeType.NONE)

HOST = b'host'


def _parse_host(value: bytes) -> tuple[bytes, int | None]:
    host_, sep, port = value.partition(b':')
    return (host_, None) if not sep else (host_, int(port))


_PARSERS[HOST] = _Parser(_parse_host, _MergeType.NONE)


def host(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: tuple[bytes, int | None] | None = None
) -> tuple[bytes, int | None] | None:
    """Returns the host header as a name, port tuple

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (tuple[bytes, int | None] | None, optional): An optional
            default value. Defaults to None.

    Returns:
        tuple[bytes, int | None] | None: The host as a name, port tuple.
    """
    value = find(HOST, headers)
    return default if value is None else _parse_host(value)


IF_MODIFIED_SINCE = b'if-modified-since'

_PARSERS[IF_MODIFIED_SINCE] = _Parser(_parse_date, _MergeType.NONE)


def if_modified_since(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: datetime | None = None
) -> datetime | None:
    """The If-Modified-Since request HTTP header makes the request conditional:
    the server will send back the requested resource, with a 200 status, only if
    it has been last modified after the given date. If the request has not been
    modified since, the response will be a 304 without any body; the
    Last-Modified response header of a previous request will contain the date of
    last modification. Unlike If-Unmodified-Since, If-Modified-Since can only be
    used with a GET or HEAD.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers
        default (datetime | None, optional): [description]. Defaults to None.

    Returns:
        datetime | None: The timestamp if present, otherwise the default
            value.
    """
    return find_date(IF_MODIFIED_SINCE, headers, default=default)


IF_NONE_MATCH = b'if-none-match'

LAST_MODIFIED = b'last-modified'

_PARSERS[LAST_MODIFIED] = _Parser(_parse_date, _MergeType.NONE)


def last_modified(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: datetime | None = None
) -> datetime | None:
    """The Last-Modified response HTTP header contains the date and time at
    which the origin server believes the resource was last modified. It is used
    as a validator to determine if a resource received or stored is the same.
    Less accurate than an ETag header, it is a fallback mechanism. Conditional
    requests containing If-Modified-Since or If-Unmodified-Since headers make
    use of this field.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (datetime | None, optional): An optional default value.
            Defaults to None.

    Returns:
        datetime | None: The timestamp if present, otherwise the default
            value.
    """
    return find_date(LAST_MODIFIED, headers, default=default)


LOCATION = b'location'

_PARSERS[LOCATION] = _Parser(_pass_through, _MergeType.NONE)


def location(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Location response header indicates the URL to redirect a page to. It
    only provides a meaning when served with a 3xx (redirection) or 201
    (created) status response.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The redirect location
    """
    value = find(LOCATION, headers)
    return default if value is None else value


ORIGIN = b'origin'

_PARSERS[ORIGIN] = _Parser(_pass_through, _MergeType.NONE)


def origin(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Origin request header indicates where a fetch originates from. It
    doesn't include any path information, but only the server name. It is sent
    with CORS requests, as well as with POST requests. It is similar to the
    Referer header, but, unlike this header, it doesn't disclose the whole path.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value.
            Defaults to None.

    Returns:
        bytes | None: The origin if present, otherwise the default value.
    """
    value = find(ORIGIN, headers)
    return default if value is None else value


PROXY_AUTHORIZATION = b'proxy-authorization'


def proxy_authorization(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: tuple[bytes, bytes] | None = None
) -> tuple[bytes, bytes] | None:
    """The HTTP Proxy-Authorization request header contains the credentials to
    authenticate a user agent to a proxy server, usually after the server has
    responded with a 407 Proxy Authentication Required status and the
    Proxy-Authenticate header.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (tuple[bytes, bytes] | None, optional): An optional default
            value. Defaults to None.

    Returns:
        tuple[bytes, bytes] | None: The type and credentials.
    """
    value = find(PROXY_AUTHORIZATION, headers)
    return default if value is None else _parse_authorization(value)


REFERER = b'referer'

_PARSERS[REFERER] = _Parser(_pass_through, _MergeType.NONE)


def referer(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Referer request header contains the address of the previous web page
    from which a link to the currently requested page was followed. The Referer
    header allows servers to identify where people are visiting them from and
    may use that data for analytics, logging, or optimized caching, for example.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value. Defaults
            to None.

    Returns:
        bytes | None: The referer if present; otherwise the default value.
    """
    value = find(REFERER, headers)
    return default if value is None else value


SERVER = b'server'

_PARSERS[SERVER] = _Parser(_pass_through, _MergeType.NONE)


def server(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: bytes | None = None
) -> bytes | None:
    """The Server header contains information about the software used by the
    origin server to handle the request.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (bytes | None, optional): An optional default value.
            Defaults to None.

    Returns:
        bytes | None: The product directive
    """
    value = find(SERVER, headers)
    return default if value is None else value


SET_COOKIE = b'set-cookie'

_PARSERS[SET_COOKIE] = _Parser(decode_set_cookie, _MergeType.APPEND)


def set_cookie(
        headers: Iterable[tuple[bytes, bytes]]
) -> Mapping[bytes, list[Mapping[str, Any]]]:
    """Returns the cookies as a name-value mapping.

    Args:
        headers (Headers): The headers.

    Returns:
        Mapping[bytes, list[Mapping[str, Any]]]: The cookies as a name-value
            mapping.
    """
    set_cookies: MutableMapping[bytes, list[Mapping[str, Any]]] = {}
    for header in find_all(SET_COOKIE, headers):
        decoded = decode_set_cookie(header)
        set_cookies.setdefault(decoded['name'], []).append(decoded)
    return set_cookies


TRANSFER_ENCODING = b'transfer-encoding'

VARY = b'vary'


def _parse_vary(value: bytes) -> list[bytes]:
    return value.split(b', ')


_PARSERS[VARY] = _Parser(_parse_vary, _MergeType.NONE)


def vary(
        headers: Iterable[tuple[bytes, bytes]],
        *,
        default: list[bytes] | None = None
) -> list[bytes] | None:
    """Returns the vary header value as a list of headers.

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers.
        default (list[bytes] | None, optional): An optional default value.
            Defaults to None.

    Returns:
        list[bytes] | None: A list of the vary headers if present; otherwise
            the default value.
    """
    value = find(VARY, headers)
    return default if value is None else _parse_vary(value)


def collect(headers: Iterable[tuple[bytes, bytes]]) -> dict[bytes, Any]:
    """Collect all headers into a mapping

    Args:
        headers (Iterable[tuple[bytes, bytes]]): The headers

    Returns:
        dict[bytes, Any]: A mapping of the parsed headers
    """
    collection: dict[bytes, Any] = {}
    for name, value in headers:
        parser = _PARSERS.get(name, _DEFAULT_PARSER)
        match parser.merge_type:
            case _MergeType.APPEND:
                result = parser.parse(value)
                collection.setdefault(name, []).append(result)
            case _MergeType.CONCAT:
                result = parser.parse(value)
                collection.setdefault(name, []).extend(result)
            case _MergeType.EXTEND:
                result = parser.parse(value)
                dct = collection.setdefault(name, {})
                for k, v in result.items():
                    dct.setdefault(k, []).extend(v)
            case _:
                collection[name] = parser.parse(value)
    return collection
