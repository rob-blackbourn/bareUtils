import pytest
from bareutils.compression import (
    compression_writer,
    compression_reader,
    make_gzip_compressobj,
    make_gzip_decompressobj,
    make_deflate_compressobj,
    make_deflate_decompressobj,
    make_compress_compressobj,
    make_compress_decompressobj,
)


@pytest.mark.asyncio
async def test_gzip():
    source = b'This is not a test' * 10
    writer = compression_writer(source, make_gzip_compressobj())
    dest = await compression_reader(writer, make_gzip_decompressobj())
    assert dest == source


@pytest.mark.asyncio
async def test_deflate():
    source = b'This is not a test' * 10
    writer = compression_writer(source, make_deflate_compressobj())
    dest = await compression_reader(writer, make_deflate_decompressobj())
    assert dest == source


@pytest.mark.asyncio
async def test_compress():
    source = b'This is not a test' * 10
    writer = compression_writer(source, make_compress_compressobj())
    dest = await compression_reader(writer, make_compress_decompressobj())
    assert dest == source
