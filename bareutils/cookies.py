"""Cookies"""

from datetime import datetime, timedelta
from typing import (
    Any,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Union
)

from .dates import parse_date
from .dates.rfc_7231 import format_date


def encode_set_cookie(
        name: bytes,
        value: bytes,
        *,
        expires: Optional[datetime] = None,
        max_age: Optional[Union[int, timedelta]] = None,
        path: Optional[bytes] = None,
        domain: Optional[bytes] = None,
        secure: bool = False,
        http_only: bool = False,
        same_site: Optional[bytes] = None
) -> bytes:
    """Encode set-cookie

    Args:
        name (bytes): The cookie name
        value (bytes): The cookie value
        expires (Optional[datetime], optional): The time the cookie expires.
            Defaults to None.
        max_age (Optional[Union[int, timedelta]], optional): The maximum age of
            the cookie in seconds. Defaults to None.
        path (Optional[bytes], optional): The cookie path. Defaults to None.
        domain (Optional[bytes], optional): The cookie domain. Defaults to None.
        secure (bool, optional): Indicates if the cookie is restricted to https.
            Defaults to False.
        http_only (bool, optional): Indicates if the cookie is available to the
            API. Defaults to False.
        same_site (Optional[bytes], optional): CORS directive. Defaults to None.

    Raises:
        RuntimeError: Raised if the __Secure- or __Host- was used without secure
        ValueError: If a date could not be parsed.

    Returns:
        bytes: The set-cookie header
    """
    if not secure and (name.startswith(b'__Secure-') or name.startswith(b'__Host-')):
        raise RuntimeError(
            'Keys starting __Secure- or __Host- require the secure directive'
        )

    set_cookie = name + b'=' + value

    if expires is not None:
        set_cookie += b'; Expires=' + format_date(expires).encode()

    if max_age is not None:
        if isinstance(max_age, timedelta):
            set_cookie += b'; Max-Age=' + \
                str(int(max_age.total_seconds())).encode()
        else:
            set_cookie += b'; Max-Age=' + str(int(max_age)).encode()

    if domain is not None:
        set_cookie += b'; Domain=' + domain

    if path is not None:
        set_cookie += b'; Path=' + path

    if secure:
        set_cookie += b'; Secure'

    if http_only:
        set_cookie += b'; HttpOnly'

    if same_site is not None:
        set_cookie += b'; SameSite=' + same_site

    return set_cookie


def decode_set_cookie(set_cookie: bytes) -> Mapping[str, Any]:
    """Decode a set-cookie header into a dictionary.

    The `max-age` value is represented as a `datatime.timedelta`.
    The `expires` value is represented as a `datetine.datetime`.
    The `secure` value is represented as a `bool`.

    Args:
        set_cookie (bytes): The set-cookie header

    Returns:
        Mapping[str, Any]: A dictionary of the values
    """
    i = iter(set_cookie.split(b';'))
    key, _, value = next(i).partition(b'=')
    result: Dict[str, Any] = {'name': key, 'value': value}
    for item in i:
        key, _, value = item.partition(b'=')
        name = key.lower().strip().decode('ascii')
        if name == 'secure':
            result['secure'] = True
        elif name == 'httponly':
            result['http_only'] = True
        elif name == 'expires':
            result['expires'] = parse_date(value.decode('ascii'))
        elif name == 'max-age':
            result['max_age'] = timedelta(seconds=int(value))
        elif name == 'samesite':
            result['same_site'] = value.decode('ascii')
        else:
            result[name] = value
    return result


def encode_cookies(cookies: Mapping[bytes, List[bytes]]) -> bytes:
    """Encode the cookie header

    Args:
        cookies (Mapping[bytes, List[bytes]]): The cookies

    Returns:
        bytes: The cookie header
    """
    return b'; '.join(
        name + b'=' + value
        for name, values in cookies.items()
        for value in values
    )


def decode_cookies(cookies: bytes) -> Mapping[bytes, List[bytes]]:
    """Decode a cookie header

    Args:
        cookies (bytes): The header

    Returns:
        Mapping[bytes, List[bytes]]: The cookies
    """
    result: MutableMapping[bytes, List[bytes]] = dict()
    for morsel in cookies.rstrip(b'; ').split(b'; '):
        name, _, value = morsel.partition(b'=')
        result.setdefault(name, []).append(value)
    return result


def make_cookie(
        key: bytes,
        value: bytes,
        *,
        expires: Optional[Union[datetime, timedelta]] = None,
        path: Optional[bytes] = None,
        domain: Optional[bytes] = None,
        secure: bool = False,
        http_only: bool = False,
        same_site: Optional[bytes] = None
) -> bytes:
    """Make a set-cookie header

    Args:
        key (bytes): The cookie name
        value (bytes): The cookie value
        expires (Optional[Union[datetime, timedelta]], optional): The expiry
            time of the cookie. Defaults to None.
        path (Optional[bytes], optional): The cookie path. Defaults to None.
        domain (Optional[bytes], optional): The cookie domain. Defaults to None.
        secure (bool, optional): Indicates if the cookie is restricted to https.
            Defaults to False.
        http_only (bool, optional): Indicates if the cookie is available to the
            API. Defaults to False.
        same_site (Optional[bytes], optional): CORS directive. Defaults to None.

    Returns:
        bytes: The set-cookie header
    """
    return encode_set_cookie(
        key,
        value,
        expires=expires if isinstance(expires, datetime) else None,
        max_age=expires if isinstance(expires, (int, timedelta)) else None,
        path=path,
        domain=domain,
        secure=secure,
        http_only=http_only,
        same_site=same_site
    )


def make_expired_cookie(key: bytes, path: bytes = b'/') -> bytes:
    """Make an expired cookie

    Args:
        key (bytes): The cookie name
        path (bytes, optional): The cookie path. Defaults to b'/'.

    Returns:
        bytes: [description]
    """
    return make_cookie(key, b'', expires=timedelta(seconds=0), path=path)
