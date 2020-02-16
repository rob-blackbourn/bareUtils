"""Responses"""

import json
from typing import Any, Callable, Optional

from baretypes import Headers, HttpResponse, PushResponses

from .streaming import bytes_writer


def bytes_response(
        status: int,
        headers: Optional[Headers],
        buf: bytes,
        content_type: bytes = b'application/octet-stream',
        chunk_size: int = -1,
        pushes: Optional[PushResponses] = None
) -> HttpResponse:
    """A helper function to create a bytes response.

    Args:
        status (int): The HTTP status code.
        headers (Optional[Headers]): The HTTP headers.
        buf (bytes): The data to send.
        content_type (bytes, optional): The content type of the data. Defaults
            to b'application/octet-stream'.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk. Defaults to -1.
        pushes (Optional[PushResponses], optional): Optional posh responses for
            HTTP/2. Defaults to None.

    Returns:
        HttpResponse: The HTTP response.
    """
    headers = [] if headers is None else list(headers)

    headers.append((b'content-type', content_type))
    if chunk_size == -1:
        headers.append((b'content-length', str(len(buf)).encode('ascii')))

    return status, headers, bytes_writer(buf, chunk_size), pushes


def text_response(
        status: int,
        headers: Optional[Headers],
        text: str,
        encoding: str = 'utf-8',
        content_type: bytes = b'text/plain',
        chunk_size: int = -1,
        pushes: Optional[PushResponses] = None
) -> HttpResponse:
    """A helper function to create a text response.

    Args:
        status (int): The HTTP status code.
        headers (Optional[Headers]): The HTTP headers.
        text (str): The text to send.
        encoding (str, optional): [description]. Defaults to 'utf-8'.
        content_type (bytes, optional): The content type. Defaults to b'text/plain'.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk. Defaults to -1.
        pushes (Optional[PushResponses], optional): Optional posh responses for
            HTTP/2. Defaults to None.

    Returns:
        HttpResponse: The HTTP response.
    """
    return bytes_response(status, headers, text.encode(encoding), content_type, chunk_size, pushes)


def json_response(
        status: int,
        headers: Optional[Headers],
        obj: Any,
        content_type: bytes = b'application/json',
        dumps: Callable[[Any], str] = json.dumps,
        chunk_size: int = -1,
        pushes: Optional[PushResponses] = None
) -> HttpResponse:
    """A helper function to send a json response.

    Args:
        status (int): The HTTP status code.
        headers (Optional[Headers]): The HTTP headers.
        obj (Any): The object to send as JSON.
        content_type (bytes, optional): The content type. Defaults to
            b'application/json'.
        dumps (Callable[[Any], str], optional): The function to use to turn the
            object into JSON. Defaults to json.dumps.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk. Defaults to -1.
        pushes (Optional[PushResponses], optional): Optional posh responses for
            HTTP/2. Defaults to None.

    Returns:
        HttpResponse: The HTTP response.
    """
    return text_response(status, headers, dumps(obj), 'utf-8', content_type, chunk_size, pushes)
