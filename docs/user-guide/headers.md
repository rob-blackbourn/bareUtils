# Reading and writing headers

The bareUtils module `bareutils.header` provides constants and helper
functions for dealing with ASGI headers.

More information can be found in the [api](/api/bareutils.header/).

The most common function is `find_header`.

```python
import asyncio
from bareclient import HttpClient
import bareutils.response_code as response_code
import bareutils.header as header

async def main(url):
    async with HttpClient(url, method='GET') as response:
        if response['status_code'] == response_code.OK and response['more_body']:
            content_type = header.find_header(b'content-type', response['headers'])
            if content_type == b'text/html':
                async for part in response['body']:
                    print(part)

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```

Note how the header names an values are byte strings.

Some helper functions have been provide for the commen headers: e.g. `content_type`.
