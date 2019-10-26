"""Exports for compression"""

from .streaming import (
    Compressor,
    make_gzip_compressobj,
    make_deflate_compressobj,
    make_compress_compressobj,
    compression_writer_adapter,
    compression_writer,
    Decompressor,
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    make_compress_decompressobj,
    compression_reader_adapter,
    compression_reader
)

from .middleware import (
    CompressionMiddleware,
    make_default_compression_middleware
)

__all__ = [
    'Compressor',
    'make_gzip_compressobj',
    'make_deflate_compressobj',
    'make_compress_compressobj',
    'compression_writer_adapter',
    'compression_writer',
    'make_gzip_decompressobj',
    'make_deflate_decompressobj',
    'make_compress_decompressobj',
    'compression_reader_adapter',
    'compression_reader',

    'CompressionMiddleware',
    'make_default_compression_middleware'
]
