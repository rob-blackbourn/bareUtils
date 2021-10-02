# Response Codes

The bareUtils module `bareutils.response_codes` provides constants and helper
functions for dealing with response codes

More information can be found in the [api](/api/bareutils.response_code/).

For example bareClient might check for a response code of 200 (OK):

    #!python
    import asyncio
    from bareclient import HttpClient
    from bareutils import response_code

    async def main(url):
        async with HttpClient(url, method='GET') as response:
            if response.status_code == response_code.OK and response.body:
                async for part in response.body:
                    print(part)

    asyncio.run(main('https://docs.python.org/3/library/cgi.html'))

We import the module using the `from` syntax on line 3 in order to make everything
in the module available. The we can use `response_code.OK` on line 7.

If we just wanted to test for a valid response code we could have used
`response_code.is_successful(response['status_code'])`.
