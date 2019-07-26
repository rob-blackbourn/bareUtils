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
    :return: A list of the header values which may be empty if there were none found.
    """
    return [v for k, v in headers if k == name]


def upsert(name: bytes, value: bytes, headers: Headers) -> None:
    """If the header exists overwrite the value, otherwise append a new value.

    :param name: The header name.
    :param value: The header value.
    :param headers: The headers.
    """
    for i in range(len(headers)):
        if headers[i][0] == name:
            headers[i] = (name, value)
            return
    headers.append((name, value))


def to_dict(headers: Headers) -> MutableMapping[bytes, List[bytes]]:
    """Convert a list of headers into a dictionary where the key is the header name and the value is a list of the
    values of the headers for that name

    :param headers: A list of headers.
    :return: A dictionary where the key is the header name and the value is a list of the values of the headers for that
        name
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


def parse_quality(value: bytes) -> Optional[float]:
    """Parse a quality attribute of the form 'q=0.5'

    :param value: The attribute value
    :return: The value as a float or None if there was no value.
    :raises: ValueError if there was a 'q' qualifier, but no value.
    """
    if value == b'':
        return None
    k, v = value.split(b'=')
    if k != b'q':
        raise ValueError('expected "q"')
    return float(v)


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


def accept_charset(headers: Headers, *, add_wildcard: bool = False) -> Optional[Mapping[bytes, float]]:
    """Extracts the accept encoding header if it exists into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param headers: The headers to search.
    :param add_wildcard: If True ensures the '*' charset is included.
    :return: A mapping of the encodings and qualities.
    """
    value = find(b'accept-charset', headers)
    return None if value is None else _parse_accept_charset(value, add_wildcard=add_wildcard)


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


def accept_language(headers: Headers, *, add_wildcard: bool = False) -> Optional[Mapping[bytes, float]]:
    """Extracts the accept language header if it exists into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param headers: The headers to search.
    :param add_wildcard: If True ensures the '*' charset is included.
    :return: A mapping of the encodings and qualities.
    """
    value = find(b'accept-language', headers)
    return None if value is None else _parse_accept_language(value, add_wildcard=add_wildcard)


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


def accept_encoding(headers: Headers, *, add_identity: bool = False) -> Optional[Mapping[bytes, float]]:
    """Extracts the accept encoding header if it exists into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param headers: The headers to search.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: A mapping of the encodings and qualities.
    """
    value = find(b'accept-encoding', headers)
    return None if value is None else _parse_accept_encoding(value, add_identity=add_identity)


def _parse_media_type_and_encoding(value: bytes) -> Tuple[bytes, Optional[bytes]]:
    media_type, sep, rest = value.partition(b';')
    if not sep:
        encoding = None
    else:
        tag, sep, encoding = rest.partition(b'=')
        if tag != b'charset':
            raise Exception('encoding must start with chartset')
    return media_type.strip(), encoding.strip() if encoding else None


def _parse_accept_patch(value: bytes) -> List[Tuple[bytes, Optional[bytes]]]:
    """Parses the accept patch header returning a list of tuples of media type and encoding.

    :param value: The header value
    :return: A list of tuples of media type and encoding.
    """
    return [
        _parse_media_type_and_encoding(item)
        for item in value.split(b',')
    ]


_PARSERS[b'accept-patch'] = _Parser(_parse_accept_encoding, _MergeType.NONE)


def accept_patch(headers: Headers) -> Optional[List[Tuple[bytes, Optional[bytes]]]]:
    """

    :param headers: The headers to search.
    :return: An optional list of tuples of media type and optional charset.
    """
    value = find(b'accept-patch', headers)
    return None if value is None else _parse_accept_patch(value)


def _parse_accept_ranges(value: bytes) -> bytes:
    return value.strip()


_PARSERS[b'accept-ranges'] = _Parser(_parse_accept_ranges, _MergeType.NONE)


def accept_ranges(headers: Headers) -> Optional[bytes]:
    """Returns the value of the accept ranges header of None if missing

    :param headers: The headers
    :return: The header value (bytes or none)
    """
    value = find(b'accept-ranges', headers)
    return None if value is None else _parse_accept_ranges(value)


def _parse_access_control_allow_credentials(value: bytes) -> bool:
    return value.lower() == b'true'


_PARSERS[b'access-control-allow-credentials'] = _Parser(_parse_access_control_allow_credentials, _MergeType.NONE)


def access_control_allow_credentials(headers: Headers) -> Optional[bool]:
    """Extracts the access control allow credentials header as a bool or None if missing.

    :param headers: The headers.
    :return: a bool or None
    """
    value = find(b'access-control-allow-credentials', headers)
    return None if value is None else _parse_access_control_allow_credentials(value)


_PARSERS[b'access-control-allow-headers'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def access_control_allow_headers(headers: Headers) -> Optional[List[bytes]]:
    value = find(b'access-control-allow-headers', headers)
    return None if value is None else _parse_comma_separated_list(value)


_PARSERS[b'access-control-allow-methods'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def access_control_allow_methods(headers: Headers) -> Optional[List[bytes]]:
    value = find(b'access-control-allow-methods', headers)
    return None if value is None else _parse_comma_separated_list(value)


_PARSERS[b'access-control-allow-origin'] = _Parser(_pass_through, _MergeType.NONE)


def access_control_allow_origin(headers: Headers) -> Optional[bytes]:
    return find(b'access-control-allow-origin', headers)


def _parse_access_control_expose_headers(value: bytes, *, add_simple_response_headers: bool = False) -> List[bytes]:
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


_PARSERS[b'access-control-expose-headers'] = _Parser(_parse_access_control_expose_headers, _MergeType.NONE)


def access_control_expose_headers(
        headers: Headers,
        *,
        add_simple_response_headers: bool = False
) -> Optional[List[bytes]]:
    value = find(b'access-control-expose-headers', headers)
    return None if value is None else _parse_access_control_expose_headers(
        value,
        add_simple_response_headers=add_simple_response_headers
    )


_PARSERS[b'access-control-max-age'] = _Parser(_parse_int, _MergeType.NONE)


def access_control_max_age(headers: Headers) -> Optional[int]:
    value = find(b'access-control-max-age', headers)
    return None if value is None else _parse_int(value)


_PARSERS[b'access-control-request-headers'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def access_control_request_headers(headers: Headers) -> Optional[List[bytes]]:
    value = find(b'access-control-request-headers', headers)
    return None if value is None else _parse_comma_separated_list(value)


_PARSERS[b'access-control-request-method'] = _Parser(_pass_through, _MergeType.NONE)


def access_control_request_method(headers: Headers) -> Optional[bytes]:
    value = find(b'access-control-request-method', headers)
    return None if value is None else _pass_through(value)


_PARSERS[b'age'] = _Parser(_parse_int, _MergeType.NONE)


def age(headers: Headers) -> Optional[int]:
    value = find(b'age', headers)
    return None if value is None else _parse_int(value)


_PARSERS[b'allow'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def allow(headers: Headers) -> Optional[List[bytes]]:
    value = find(b'allow', headers)
    return None if value is None else _parse_comma_separated_list(value)


def _parse_authorization(value: bytes) -> Tuple[bytes, bytes]:
    auth_type, _, credentials = value.partition(b' ')
    return auth_type.strip(), credentials


def _parse_cache_control(value: bytes) -> Mapping[bytes, Optional[int]]:
    return {
        name.strip(): int(rest) if sep == b'=' else None
        for name, sep, rest in [item.partition(b'=') for item in value.split(b',')]
    }


_PARSERS[b'cache-control'] = _Parser(_parse_cache_control, _MergeType.NONE)


def cache_control(headers: Headers) -> Optional[Mapping[bytes, Optional[int]]]:
    value = find(b'cache-control', headers)
    return None if value is None else _parse_cache_control(value)


_PARSERS[b'clear-site-data'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def clear_site_data(headers: Headers) -> Optional[List[bytes]]:
    value = find(b'clear-site-data', headers)
    return None if value is None else _parse_comma_separated_list(value)


_PARSERS[b'connection'] = _Parser(_pass_through, _MergeType.NONE)


def connection(headers: Headers) -> Optional[bytes]:
    return find(b'connection', headers)


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


_PARSERS[b'content-encoding'] = _Parser(_parse_content_encoding, _MergeType.NONE)


def content_encoding(headers: Headers, *, add_identity: bool = False) -> Optional[List[bytes]]:
    """Returns the content encodings in a list or None if they were not specified.

    :param headers: The headers.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: The list of content encodings or None is absent.
    """
    value = find(b'content-encoding', headers)
    return None if value is None else _parse_content_encoding(value, add_identity=add_identity)


_PARSERS[b'content-length'] = _Parser(_parse_int, _MergeType.NONE)


def content_length(headers: Headers) -> Optional[int]:
    """Returns the content length as an integer if specified, otherwise None.

    :param headers: The headers.
    :return: The length as an integer or None is absent.
    """
    value = find(b'content-length', headers)
    return None if value is None else _parse_int(value)


_PARSERS[b'content-location'] = _Parser(_pass_through, _MergeType.NONE)


def content_location(headers: Headers) -> Optional[bytes]:
    return find(b'content-location', headers)


def _parse_content_range(value: bytes) -> Tuple[bytes, Optional[Tuple[int, int]], Optional[int]]:
    unit, _, rest = value.strip().partition(b' ')
    range_, _, size = rest.strip().partition(b'/')
    if range_ == b'*':
        range_ = None
    else:
        start, _, end = range_.partition(b'-')
        range_ = (int(start), int(end))
    size = None if size.strip() == b'*' else int(size)
    return unit, range_, size


_PARSERS[b'content-range'] = _Parser(_parse_content_range, _MergeType.NONE)


def content_range(headers: Headers) -> Optional[Tuple[bytes, Optional[Tuple[int, int]], Optional[int]]]:
    value = find(b'content-range', headers)
    return None if value is None else _parse_content_range(value)


def _parse_cookie(value: bytes) -> Mapping[bytes, List[bytes]]:
    """Returns the cookies as a name-value mapping.

    :param value: The header value.
    :return: The cookies as a name-value mapping.
    """
    cookies: MutableMapping[bytes, List[bytes]] = dict()
    for k, v in decode_cookies(value).items():
        cookies.setdefault(k, []).extend(v)
    return cookies


_PARSERS[b'cookie'] = _Parser(_parse_cookie, _MergeType.EXTEND)


def cookie(headers: Headers) -> Mapping[bytes, List[bytes]]:
    """Returns the cookies as a name-value mapping.

    :param headers: The headers.
    :return: The cookies as a name-value mapping.
    """
    cookies: MutableMapping[bytes, List[bytes]] = dict()
    for value in find_all(b'cookie', headers):
        for k, v in _parse_cookie(value).items():
            cookies.setdefault(k, []).extend(v)
    return cookies


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


def _parse_date(value: bytes) -> datetime:
    """parse as date.

    :param value: The header value.
    :return: The date.
    """
    return datetime.strptime(value.decode(), '%a, %d %b %Y %H:%M:%S %Z') if value else None


_PARSERS[b'if-modified-since'] = _Parser(_parse_date, _MergeType.NONE)


def if_modified_since(headers: Headers) -> Optional[datetime]:
    value = find(b'if-modified-since', headers)
    return None if value is None else _parse_date(value)


_PARSERS[b'last-modified'] = _Parser(_parse_date, _MergeType.NONE)


def last_modified(headers: Headers) -> Optional[datetime]:
    value = find(b'last-modified', headers)
    return None if value is None else _parse_date(value)


def _parse_content_disposition(value: bytes) -> Tuple[bytes, Optional[Mapping[bytes, float]]]:
    """Returns the content type

    :param value: The header value
    :return: A tuple of the media type and a mapping of the parameters or None if absent.
    """
    media_type, sep, rest = value.partition(b';')
    parameters = {
        first.strip(): rest.strip(b'"')
        for first, sep, rest in [x.partition(b'=') for x in rest.split(b';')] if first
    } if sep == b';' else None

    return media_type, parameters


_PARSERS[b'content-disposition'] = _Parser(_parse_content_disposition, _MergeType.NONE)


def content_disposition(headers: Headers) -> Optional[Tuple[bytes, Optional[Mapping[bytes, float]]]]:
    """Returns the content type if any otherwise None

    :param headers: The headers
    :return: A tuple of the media type and a mapping of the parameters or None if absent.
    """
    value = find(b'content-disposition', headers)
    return None if value is None else _parse_content_disposition(value)


_PARSERS[b'content-language'] = _Parser(_parse_comma_separated_list, _MergeType.NONE)


def content_language(headers: Headers) -> Optional[List[bytes]]:
    value = find(b'content-language', headers)
    return None if value is None else _parse_comma_separated_list(value)


def _parse_content_type(value: bytes) -> Tuple[bytes, Optional[Mapping[bytes, float]]]:
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


def content_type(headers: Headers) -> Optional[Tuple[bytes, Optional[Mapping[bytes, float]]]]:
    """Returns the content type if any otherwise None

    :param headers: The headers
    :return: A tuple of the media type and a mapping of the parameters or None if absent.
    """
    value = find(b'content-type', headers)
    return None if value is None else _parse_content_type(value)


def collect(headers: Headers) -> Mapping[bytes, Any]:
    collection: MutableMapping[bytes, Any] = dict()
    for name, value in headers:
        parser = _PARSERS.get(name, _DEFAULT_PARSER)
        if parser.merge_type == _MergeType.APPEND:
            result = parser.parse(value)
            collection.setdefault(name, []).append(result)
        elif parser.merge_type == _MergeType.EXTEND:
            result = parser.parse(value)
            dct = collection.setdefault(name, dict())
            for k, v in result.items():
                dct.setdefault(k, []).extend(v)
        else:
            collection[name] = parser.parse(value)
    return collection
