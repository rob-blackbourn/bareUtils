# Managing cookies

The bareUtils module `bareutils.cookies` provides constants and helper
functions for dealing with cookies.

More information can be found in the [api](/api/bareutils.cookies/).

# Setting cookies

A `set-cookie` header value can be created with `encode_set_cookie`.

```python
from datetime import timedelta
from bareutils.cookies import encode_set_cookie

set_cookie = bareutils.cookies.encode_set_cookie(
    b'mycookie',
    b'98745hjk988588',
    max_age = timedelta(hours=2)
)
headers = [(b'set-cookie', set_cookie)]
```

The `decode_set_cookie` function decodes the `set-cookie` header value and
returns a dictionary containing the set-cookie parameters.

# Retrieving cookies

The `decode_cookies` function takes the `cookie` header value and returns a
mapping of cookie names to a list of values. This must be a list as cookie names
are not guaranteed to be unique. The `encode_cookies` function does the reverse.
