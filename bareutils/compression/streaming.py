"""
Compression streaming.
"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Optional
import zlib

from baretypes import Content

from ..streaming import bytes_writer, bytes_reader


class Compressor(metaclass=ABCMeta):
    """A class to represent the methods available on a compressor"""

    @abstractmethod
    def compress(self, buf: bytes) -> bytes:
        """Compress a buffer

        Args:
            buf (bytes): The buffer to compress.

        Returns:
            bytes: The compressed buffer.
        """

    def flush(self) -> bytes:
        """Flush the compressor

        Returns:
            bytes: The remaining bytes.
        """


def make_gzip_compressobj() -> Compressor:
    """Make a compressor for 'gzip'

    Returns:
        Compressor: A gzip compressor.
    """
    return zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)


def make_deflate_compressobj() -> Compressor:
    """Make a compressor for 'deflate'

    Returns:
        Compressor: A deflate compressor.
    """
    return zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)


def make_compress_compressobj() -> Compressor:
    """Make a compressor for 'compress'

    Note: This is not used by browsers anymore and should be avoided.

    Returns:
        Compressor: A compress compressor.
    """
    return zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)


async def compression_writer_adapter(
        writer: Content,
        compressobj: Compressor
) -> Content:
    """Adapts a bytes generator to generated compressed output.

    Args:
        writer (Content): The writer to be adapted.
        compressobj (Compressor): A compressor

    Yields:
        Content: The compressed content as bytes
    """
    async for buf in writer:
        yield compressobj.compress(buf)
    yield compressobj.flush()


def compression_writer(
        buf: bytes,
        compressobj: Compressor,
        chunk_size: int = -1
) -> Content:
    """Create an async iterator for compressed content.

    Args:
        buf (bytes): The bytes to compress.
        compressobj (Compressor): The compressor.
        chunk_size (int, optional): An optional chunk size where -1 indicates no
            chunking. Defaults to -1.

    Returns:
        Content: An async iterator of compressed bytes.
    """
    return compression_writer_adapter(bytes_writer(buf, chunk_size), compressobj)


class Decompressor(metaclass=ABCMeta):
    """A class to represent the methods available on a compressor"""

    @property
    @abstractmethod
    def unused_data(self) -> bytes:
        ...

    @property
    @abstractmethod
    def unconsumed_tail(self) -> bytes:
        ...

    @property
    @abstractmethod
    def eof(self) -> bool:
        ...

    @abstractmethod
    def decompress(self, buf: bytes, max_length: int = 0) -> bytes:
        ...

    @abstractmethod
    def flush(self, length: Optional[int] = None) -> bytes:
        ...

    @abstractmethod
    def copy(self) -> Decompressor:
        ...


def make_gzip_decompressobj() -> Decompressor:
    """Make a compressor for 'gzip'

    Returns:
        Decompressor: A gzip compressor.
    """
    return zlib.decompressobj(zlib.MAX_WBITS | 16)


def make_deflate_decompressobj() -> Decompressor:
    """Make a compressor for 'deflate'

    Returns:
        Decompressor: A deflate compressor.
    """
    return zlib.decompressobj(-zlib.MAX_WBITS)


def make_compress_decompressobj() -> Decompressor:
    """Make a compressor for 'compress'

    Note: This is not used by browsers anymore and should be avoided.

    Returns:
        Decompressor: A compress compressor.
    """
    return zlib.decompressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)


async def compression_reader_adapter(
        reader: Content,
        decompressobj: Decompressor
) -> Content:
    async for item in reader:
        yield decompressobj.decompress(item)
    yield decompressobj.flush()


async def compression_reader(source: Content, decompressobj: Decompressor) -> bytes:
    return await bytes_reader(compression_reader_adapter(source, decompressobj))
