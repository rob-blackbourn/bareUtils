import collections
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Mapping, MutableMapping, Any, Tuple, Callable, NamedTuple
from baretypes import Header
from .cookies import decode_cookies, decode_set_cookie


class _MergeType(Enum):
    NONE = auto()
    EXTEND = auto()
    APPEND = auto()


class _Parser(NamedTuple):
    parse: Callable[[bytes], Any]
    merge_type: _MergeType


_PARSERS: MutableMapping[bytes, _Parser] = dict()


def index(name: bytes, headers: List[Header]) -> int:
    """Find the index of the header in the list.

    :param name: The header name.
    :param headers: The headers to search.
    :return: The index of the header or -1 if not found.
    """
    return next((i for i, (k, v) in enumerate(headers) if k == name), -1)


def find(name: bytes, headers: List[Header], default: Optional[bytes] = None) -> Optional[bytes]:
    """Find the value of a header, or return a default value.

    :param name: The name of the header.
    :param headers: The headers to search.
    :param default: An optional default value, otherwise None.
    :return: The value of the header if found, otherwise the default value.
    """
    return next((v for k, v in headers if k == name), default)


def find_all(name: bytes, headers: List[Header]) -> List[bytes]:
    """Find all the values for a given header.

    :param name: The name of the header.
    :param headers: The headers to search.
    :return: A list of the header values which may be empty if there were none found.
    """
    return [v for k, v in headers if k == name]


def upsert(name: bytes, value: bytes, headers: List[Header]) -> None:
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


def to_dict(headers: List[Header]) -> MutableMapping[bytes, List[bytes]]:
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


def find_date(name: bytes, headers: List[Header]) -> Optional[datetime]:
    """Find a header containing a date.

    :param name: The name of the header.
    :param headers: The headers.
    :return: The date if found, otherwise None.
    """
    value = find(name, headers)
    return datetime.strptime(value.decode(), '%a, %d %b %Y %H:%M:%S %Z') if value else None


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


def parse_accept_encoding(value: bytes, *, add_identity: bool = False) -> Mapping[bytes, float]:
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


_PARSERS[b'accept-encoding'] = _Parser(parse_accept_encoding, _MergeType.NONE)


def accept_encoding(headers: List[Header], *, add_identity: bool = False) -> Optional[Mapping[bytes, float]]:
    """Extracts the accept encoding header if it exists into a mapping of the encoding
    and the quality value which defaults to 1.0 if missing.

    :param headers: The headers to search.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: A mapping of the encodings and qualities.
    """
    value = find(b'accept-encoding', headers)
    return None if value is None else parse_accept_encoding(value, add_identity=add_identity)


def parse_content_encoding(value: bytes, *, add_identity: bool = False) -> List[bytes]:
    """Parses the content encodings into a list.

    :param value: The header value.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: The list of content encodings or None is absent.
    """
    encodings = value.split(b', ')

    if add_identity and b'identity' not in encodings:
        encodings.append(b'identity')

    return encodings


_PARSERS[b'content-encoding'] = _Parser(parse_content_encoding, _MergeType.NONE)


def content_encoding(headers: List[Header], *, add_identity: bool = False) -> Optional[List[bytes]]:
    """Returns the content encodings in a list or None if they were not specified.

    :param headers: The headers.
    :param add_identity: If True ensures the 'identity' encoding is included.
    :return: The list of content encodings or None is absent.
    """
    value = find(b'content-encoding', headers)
    return None if value is None else parse_content_encoding(value, add_identity=add_identity)


def parse_content_length(value: bytes) -> int:
    """Parses the content length as an integer.

    :param value: The header value.
    :return: The length as an integer or None is absent.
    """
    return int(value)


_PARSERS[b'content-length'] = _Parser(parse_content_length, _MergeType.NONE)


def content_length(headers: List[Header]) -> Optional[int]:
    """Returns the content length as an integer if specified, otherwise None.

    :param headers: The headers.
    :return: The length as an integer or None is absent.
    """
    value = find(b'content-length', headers)
    return None if value is None else parse_content_length(value)


def parse_cookie(value: bytes) -> Mapping[bytes, List[bytes]]:
    """Returns the cookies as a name-value mapping.

    :param headers: The headers.
    :return: The cookies as a name-value mapping.
    """
    cookies: MutableMapping[bytes, List[bytes]] = dict()
    for k, v in decode_cookies(value).items():
        cookies.setdefault(k, []).extend(v)
    return cookies


_PARSERS[b'cookie'] = _Parser(parse_cookie, _MergeType.EXTEND)


def cookie(headers: List[Header]) -> Mapping[bytes, List[bytes]]:
    """Returns the cookies as a name-value mapping.

    :param headers: The headers.
    :return: The cookies as a name-value mapping.
    """
    cookies: MutableMapping[bytes, List[bytes]] = dict()
    for value in find_all(b'cookie', headers):
        for k, v in parse_cookie(value).items():
            cookies.setdefault(k, []).extend(v)
    return cookies


_PARSERS[b'set-cookie'] = _Parser(decode_set_cookie, _MergeType.APPEND)


def set_cookie(headers: List[Header]) -> Mapping[bytes, List[Mapping[str, Any]]]:
    """Returns the cookies as a name-value mapping.

    :param headers: The headers.
    :return: The cookies as a name-value mapping.
    """
    set_cookies: MutableMapping[bytes, List[Mapping[str, Any]]] = dict()
    for header in find_all(b'set-cookie', headers):
        decoded = decode_set_cookie(header)
        set_cookies.setdefault(decoded['name'], []).append(decoded)
    return set_cookies


def parse_vary(value: bytes) -> List[bytes]:
    """Returns the vary header value as a list of headers.

    :param value: The header value.
    :return: A list of the vary headers.
    """
    return value.split(b', ') if value is not None else None


_PARSERS[b'vary'] = _Parser(parse_vary, _MergeType.NONE)


def vary(headers: List[Header]) -> Optional[List[bytes]]:
    """Returns the vary header value as a list of headers.

    :param headers: The headers.
    :return: A list of the vary headers.
    """
    value = find(b'vary', headers)
    return None if value is None else parse_vary(value)


def parse_date(value: bytes) -> datetime:
    """parse as date.

    :param value: The header value.
    :return: The date.
    """
    return datetime.strptime(value.decode(), '%a, %d %b %Y %H:%M:%S %Z') if value else None


_PARSERS[b'if-modified-since'] = _Parser(parse_date, _MergeType.NONE)


def if_modified_since(headers: List[Header]) -> Optional[datetime]:
    value = find(b'if-modified-since', headers)
    return None if value is None else parse_date(value)


_PARSERS[b'last-modified'] = _Parser(parse_date, _MergeType.NONE)


def last_modified(headers: List[Header]) -> Optional[datetime]:
    value = find(b'last-modified', headers)
    return None if value is None else parse_date(value)


def parse_content_type(value: bytes) -> Tuple[bytes, Optional[Mapping[bytes, float]]]:
    """Returns the content type

    :param headers: The headers
    :return: A tuple of the media type and a mapping of the parameters or None if absent.
    """
    media_type, sep, rest = value.partition(b';')
    parameters = {
        first.strip(): rest.strip()
        for first, sep, rest in [x.partition(b'=') for x in rest.split(b';')] if first
    } if sep == b';' else None

    return media_type, parameters


_PARSERS[b'content-type'] = _Parser(parse_content_type, _MergeType.NONE)


def content_type(headers: List[Header]) -> Optional[Tuple[bytes, Optional[Mapping[bytes, float]]]]:
    """Returns the content type if any otherwise None

    :param headers: The headers
    :return: A tuple of the media type and a mapping of the parameters or None if absent.
    """
    value = find(b'content-type', headers)
    return None if value is None else parse_content_type(value)


_DEFAULT_PARSER = _Parser(lambda x: x, _MergeType.APPEND)


def collect(headers: List[Header]) -> Mapping[bytes, Any]:
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
