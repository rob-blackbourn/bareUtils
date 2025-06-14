"""Compression utilities

Only compression directly supported by standard library functions are provided
here to avoid the need for additional dependencies. Other compression methods
should be implemented in a separate module.
"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import AsyncIterable, Callable, cast
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

    @abstractmethod
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
        """A bytes object which contains any bytes past the end of the
        compressed data.

        That is, this remains b"" until the last byte that contains compression
        data is available. If the whole bytestring turned out to contain
        compressed data, this is b"", an empty bytes object.
        """

    @property
    @abstractmethod
    def unconsumed_tail(self) -> bytes:
        """A bytes object that contains any data that was not consumed by the
        last decompress() call because it exceeded the limit for the
        uncompressed data buffer.
        """

    @property
    @abstractmethod
    def eof(self) -> bool:
        """A boolean indicating whether the end of the compressed data stream has been reached.

        This makes it possible to distinguish between a properly formed compressed
        stream, and an incomplete or truncated one.
        """

    @abstractmethod
    def decompress(self, buf: bytes, max_length: int = 0) -> bytes:
        """Decompress data, returning a bytes object containing the uncompressed
        data corresponding to at least part of the data in string.

        This data should be concatenated to the output produced by any preceding
        calls to the decompress() method. Some of the input data may be
        preserved in internal buffers for later processing.

        If the optional parameter max_length is non-zero then the return value
        will be no longer than max_length. This may mean that not all of the
        compressed input can be processed; and unconsumed data will be stored in
        the attribute unconsumed_tail. This bytestring must be passed to a
        subsequent call to decompress() if decompression is to continue. If
        max_length is zero then the whole input is decompressed, and
        unconsumed_tail is empty.

        Args:
            buf (bytes): The data to decompress.
            max_length (int, optional): Max length of output. Defaults to 0.

        Returns:
            bytes: The decompressed data.
        """

    @abstractmethod
    def flush(self, length: int | None = None) -> bytes:
        """All pending input is processed, and a bytes object containing the
        remaining uncompressed output is returned. After calling flush(), the
        decompress() method cannot be called again; the only realistic action is
        to delete the object.

        Args:
            length (int | None, optional): The initial size of the output
                buffer. Defaults to None.

        Returns:
            bytes: The remaining uncompressed output.
        """

    @abstractmethod
    def copy(self) -> Decompressor:
        """Returns a copy of the decompression object.

        This can be used to save the state of the decompressor midway through
        the data stream in order to speed up random seeks into the stream at a
        future point.

        Returns:
            Decompressor: A copy of the decompressor.
        """


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
        zlib.decompressobj(zlib.MAX_WBITS)
    )


async def compression_reader_adapter(
        reader: AsyncIterable[bytes],
        decompressobj: Decompressor
) -> AsyncIterable[bytes]:
    """Adapters a reader to decompress the data.

    Args:
        reader (AsyncIterable[bytes]): The reader.
        decompressobj (Decompressor): The decompressor.

    Returns:
        AsyncIterable[bytes]: An async iterable of decompressed bytes.

    Yields:
        bytes: Decompressed bytes.
    """
    async for item in reader:
        yield decompressobj.decompress(item)
    yield decompressobj.flush()


async def compression_reader(
        source: AsyncIterable[bytes],
        decompressobj: Decompressor
) -> bytes:
    """Reads a compressed stream and returns the decompressed bytes.

    Args:
        source (AsyncIterable[bytes]): The input stream.
        decompressobj (Decompressor): The decompressor.

    Returns:
        bytes: The decompressed bytes.
    """
    return await bytes_reader(compression_reader_adapter(source, decompressobj))
