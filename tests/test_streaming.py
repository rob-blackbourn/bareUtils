import pytest
from bareutils.streaming import bytes_reader, bytes_writer, text_reader, text_writer


@pytest.mark.asyncio
async def test_bytes():
    source = b'This is not a test' * 10
    writer = bytes_writer(source)
    dest = await bytes_reader(writer)
    assert dest == source


@pytest.mark.asyncio
async def test_bytes_chunked():
    source = b'This is not a test' * 10
    writer = bytes_writer(source, chunk_size=10)
    dest = await bytes_reader(writer)
    assert dest == source


@pytest.mark.asyncio
async def test_text():
    source = 'This is not a test' * 10
    writer = text_writer(source)
    dest = await text_reader(writer)
    assert dest == source


@pytest.mark.asyncio
async def test_text_chunked():
    source = 'This is not a test' * 10
    writer = text_writer(source, chunk_size=10)
    dest = await text_reader(writer)
    assert dest == source
