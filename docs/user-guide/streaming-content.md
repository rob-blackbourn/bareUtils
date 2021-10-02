# Streaming

The bareUtils module `bareutils.streaming` provides constants and helper
functions for streaming body content.

More information can be found in the [api](/api/bareutils.streaming/).

Body content is sent and received as asynchronous iterators.

The most common functions are:

- `bytes_reader` to read streams of bytes,
- `bytes_writer` to write streams of bytes,
- `text_reader` to read streams of text,
- `text_writer` to write streams of text.

For example to read a text stream from a request handler:

```python
from bareasgi import HttpRequest, HttpResponse
from bareutils import text_reader

async def handle_request(request: HttpRequest) -> HttpResponse:
    text = await text_reader(content)
    return HttpResponse(200, [(b'content-type', b'text/plain')], text_write(text.lower()))
```
