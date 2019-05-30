from abc import ABCMeta, abstractmethod
import codecs
from typing import AsyncIterator
import zlib
from baretypes import Content


async def bytes_reader(content: Content) -> bytes:
    """Extracts the body content as bytes.

    :param content: The content argument of the request handler.
    :return: The body as bytes.
    """
    buf = b''
    async for b in content:
        buf += b
    return buf


async def text_reader(content: Content, encoding: str = 'utf-8') -> str:
    """Extracts the body contents as text.

    :param content: The content argument of the request handler.
    :param encoding: The encoding of the text (defaults to 'utf-8').
    :return: The body contents as a string.
    """
    codec_info: codecs.CodecInfo = codecs.lookup(encoding)
    decoder = codec_info.incrementaldecoder()
    text = ''
    async for b in content:
        text += decoder.decode(b)
    return text


async def bytes_writer(buf: bytes, chunk_size: int = -1) -> AsyncIterator[bytes]:
    """Creates an asynchronous generator from the supplied response body.

    :param buf: The response body to return.
    :param chunk_size: The size of each chunk to send or -1 to send as a single chunk.
    :return: An asynchronous generator of bytes.
    """

    if chunk_size == -1:
        yield buf
    else:
        start, end = 0, chunk_size
        while start < len(buf):
            yield buf[start:end]
            start, end = end, end + chunk_size


async def text_writer(text: str, encoding: str = 'utf-8', chunk_size: int = -1) -> AsyncIterator[bytes]:
    """Creates an asynchronous generator from the supplied response body.

    :param text: The response body.
    :param encoding:  The encoding to apply when transforming the text into bytes (defaults to 'utf-8').
    :param chunk_size: The size of each chunk to send or -1 to send as a single chunk.
    :return: An asynchronous generator of bytes.
    """

    if chunk_size == -1:
        yield text.encode(encoding=encoding)
    else:
        start, end = 0, chunk_size
        while start < len(text):
            yield text[start:end].encode(encoding=encoding)
            start, end = end, end + chunk_size


class Compressor(metaclass=ABCMeta):
    """A class to represent the methods available on a compressor"""


    @abstractmethod
    def compress(self, buf: bytes) -> bytes:
        ...


    def flush(self) -> bytes:
        ...


def make_gzip_compressobj() -> Compressor:
    """Make a compressor for 'gzip'

    :return: A gzip compressor.
    """
    return zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)


def make_deflate_compressobj() -> Compressor:
    """Make a compressor for 'deflate'

    :return: A deflate compressor.
    """
    return zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)


def make_compress_compressobj() -> Compressor:
    """Make a compressor for 'compress'

    :return: A compress compressor.

    Note: This is not used by browsers anymore and should be avoided.
    """
    return zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)


async def compression_writer_adapter(
        writer: AsyncIterator[bytes],
        compressobj: Compressor
) -> AsyncIterator[bytes]:
    """Adaptes a bytes generator to generated compressed output.

    :param writer: The writer to be adapted.
    :param compressobj: A compressor
    :return: A generator producing compressed output.
    """
    async for buf in writer:
        yield compressobj.compress(buf)
    yield compressobj.flush()


def compression_writer(
        buf: bytes,
        compressobj: Compressor,
        chunk_size: int = -1
) -> AsyncIterator[bytes]:
    """Create an async generator for compressed content.

    :param buf: The bytes to compress
    :param compressobj: The compressor.
    :param chunk_size: An optional chunk size where -1 indicates no chunking.
    :return: An sync generator of compressed bytes.
    """
    return compression_writer_adapter(bytes_writer(buf, chunk_size), compressobj)
