"""
Compression streaming.
"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import AsyncIterable, Callable, Optional, cast
import zlib

from .streaming import bytes_writer, bytes_reader


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


CompressorFactory = Callable[[], Compressor]


def make_gzip_compressobj() -> Compressor:
    """Make a compressor for 'gzip'

    Returns:
        Compressor: A gzip compressor.
    """
    return cast(
        Compressor,
        zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
    )


def make_deflate_compressobj() -> Compressor:
    """Make a compressor for 'deflate'

    Returns:
        Compressor: A deflate compressor.
    """
    return cast(
        Compressor,
        zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    )


def make_compress_compressobj() -> Compressor:
    """Make a compressor for 'compress'

    Note: This is not used by browsers anymore and should be avoided.

    Returns:
        Compressor: A compress compressor.
    """
    return cast(
        Compressor,
        zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)
    )


async def compression_writer_adapter(
        writer: AsyncIterable[bytes],
        compressobj: Compressor
) -> AsyncIterable[bytes]:
    """Adapts a bytes generator to generated compressed output.

    Args:
        writer (AsyncIterable[bytes]): The writer to be adapted.
        compressobj (Compressor): A compressor

    Yields:
        AsyncIterable[bytes]: The compressed content as bytes
    """
    async for buf in writer:
        yield compressobj.compress(buf)
    yield compressobj.flush()


def compression_writer(
        buf: bytes,
        compressobj: Compressor,
        chunk_size: int = -1
) -> AsyncIterable[bytes]:
    """Create an async iterator for compressed content.

    Args:
        buf (bytes): The bytes to compress.
        compressobj (Compressor): The compressor.
        chunk_size (int, optional): An optional chunk size where -1 indicates no
            chunking. Defaults to -1.

    Returns:
        AsyncIterable[bytes]: An async iterator of compressed bytes.
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


DecompressorFactory = Callable[[], Decompressor]


def make_gzip_decompressobj() -> Decompressor:
    """Make a compressor for 'gzip'

    Returns:
        Decompressor: A gzip compressor.
    """
    return cast(
        Decompressor,
        zlib.decompressobj(zlib.MAX_WBITS | 16)
    )


def make_deflate_decompressobj() -> Decompressor:
    """Make a compressor for 'deflate'

    Returns:
        Decompressor: A deflate compressor.
    """
    return cast(
        Decompressor,
        zlib.decompressobj(-zlib.MAX_WBITS)
    )


def make_compress_decompressobj() -> Decompressor:
    """Make a compressor for 'compress'

    Note: This is not used by browsers anymore and should be avoided.

    Returns:
        Decompressor: A compress compressor.
    """
    return cast(
        Decompressor,
        zlib.decompressobj(9, zlib.DEFLATED, zlib.MAX_WBITS) # type: ignore
    )


async def compression_reader_adapter(
        reader: AsyncIterable[bytes],
        decompressobj: Decompressor
) -> AsyncIterable[bytes]:
    async for item in reader:
        yield decompressobj.decompress(item)
    yield decompressobj.flush()


async def compression_reader(
        source: AsyncIterable[bytes],
        decompressobj: Decompressor
) -> bytes:
    return await bytes_reader(compression_reader_adapter(source, decompressobj))
