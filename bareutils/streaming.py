"""Streaming"""

from __future__ import annotations
import codecs
from typing import AsyncIterable


async def bytes_reader(body: AsyncIterable[bytes]) -> bytes:
    """Extracts the body body as bytes.

    Args:
        body (AsyncIterable[bytes]): The body argument of the request.

    Returns:
        bytes: The body as bytes.
    """
    buf = b''
    async for value in body:
        buf += value
    return buf


async def text_reader(body: AsyncIterable[bytes], encoding: str = 'utf-8') -> str:
    """Extracts the body contents as text.

    Args:
        body (AsyncIterable[bytes]): The body of the request.
        encoding (str, optional): The encoding of the text. Defaults to 'utf-8'.

    Returns:
        str: The body contents as a string.
    """
    codec_info: codecs.CodecInfo = codecs.lookup(encoding)
    decoder = codec_info.incrementaldecoder()
    text = ''
    async for b in body:
        text += decoder.decode(b)
    return text


async def bytes_writer(buf: bytes, chunk_size: int = -1) -> AsyncIterable[bytes]:
    """Creates an asynchronous iterator from the supplied response body.

    Args:
        buf (bytes): The response body to return.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.

    Yields:
        AsyncIterable[bytes]: The body bytes
    """
    if chunk_size == -1:
        yield buf
    else:
        start, end = 0, chunk_size
        while start < len(buf):
            yield buf[start:end]
            start, end = end, end + chunk_size


async def text_writer(
        text: str,
        encoding: str = 'utf-8',
        chunk_size: int = -1
) -> AsyncIterable[bytes]:
    """Creates an asynchronous iterator from the supplied response body.

    Args:
        text (str): The response body.
        encoding (str, optional): The encoding to apply when transforming the
            text into bytes. Defaults to 'utf-8'.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.

    Yields:
        AsyncIterable[bytes]: The body bytes
    """
    if chunk_size == -1:
        yield text.encode(encoding=encoding)
    else:
        start, end = 0, chunk_size
        while start < len(text):
            yield text[start:end].encode(encoding=encoding)
            start, end = end, end + chunk_size
