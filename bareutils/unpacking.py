"""Unpackers"""

from email.parser import BytesFeedParser
from email.message import Message
from typing import AsyncIterable, List, Tuple, Union

MessageParams = List[Tuple[str, str]]
MessagePayload = Union[List[Message], str, bytes, None]


async def unpack_multipart_form_data(
        content_type: bytes,
        content: AsyncIterable[bytes]
) -> List[Tuple[MessageParams, MessagePayload]]:
    """Unpack multipart form data

    Args:
        content_type (bytes): The 'content-type' header
        content (AsyncIterable[bytes]): The content to parse.

    Raises:
        AssertionError: When the problems were found with the data

    Returns:
        List[Tuple[MessageParams, MessagePayload]]: The form and files
    """
    # Create the parser and prime it with the content
    # type.
    parser = BytesFeedParser()
    parser.feed(b'Content-Type: ')  # type: ignore[arg-type]
    parser.feed(content_type)  # type: ignore[arg-type]
    parser.feed(b'\r\n\r\n')  # type: ignore[arg-type]

    # Feed the content to the parser.
    async for buf in content:
        parser.feed(buf)
    msg = parser.close()

    assert msg is not None, "The parser should return a message"
    assert msg.is_multipart(), "The message should be a multipart message"
    assert not msg.defects, "The message should not have defects"

    msg_payload = msg.get_payload()
    assert msg_payload is not None, "The message payload should not be empty"

    data: List[Tuple[MessageParams, MessagePayload]] = []
    for msg_part in msg_payload:
        assert isinstance(
            msg_part, Message), "A message part should also be a message"
        assert not msg_part.is_multipart(), "A message part should not be multipart"
        assert not msg_part.defects, "A message part should not have defects"

        content_disposition = msg_part.get_params(header='content-disposition')
        assert content_disposition, "A message part should have a content-disposition header"

        part_payload: MessagePayload = msg_part.get_payload(decode=True)
        data.append(
            (content_disposition, part_payload)
        )

    return data
