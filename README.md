Google Endpoints auth decorator for Python
==========================================

Provide an utility class to easily handle some common authorization
cases when using Google Cloud Endpoints on App Engine for Python
within a Google Apps environment.

This class can check for 4 levels of authorization :

 * None : the request is not authorized at all
 * Google : the request is authorized using a Google account that
does not belongs to the provided Google Apps domain
 * Domain : the request is authorized using a Google Apps account
that belongs to provided Google Apps domain
 * Administrator : the request is authorized using a Google Apps account
that is a member of a provided administrator Google Groups

## Example

```python
authenticator = EndpointsAuthenticator('client_id@gserviceaccount.com',
    '/path/to/private.pem',
    'CUSTOMER_ID',
    'superadmin@acme.com',
    'administrators@groups.acme.com',
    cache=memcache,
    cache_prefix='auth')

# later in your API definition
@endpoints.api(name='myapi', version='v1')
class MyApi(remote.Service):
    @endpoints.method(
        message_types.VoidMessage,
        message_types.VoidMessage,
        path='foo/bar',
        http_method='GET',
        name='foobar')
    # here is the import bit of code
    @authenticator.ensure(auth_level=AuthLevel.ADMINISTRATOR)
    def foobar(self, request):
        # does nothing
        return message_types.VoidMessage()
```

## Reference

@authenticator.ensure(auth_level)

Params

 * ```auth_level``` : with one of the following enum values
     - AuthLevel.NONE
     - AuthLevel.GOOGLE
     - AuthLevel.DOMAIN
     - AuthLevel.ADMINISTRATOR

Returns ```None```

Throws

 * ```endpoints.UnauthorizedException```
 * ```endpoints.ForbiddenException```

## License

MIT License

Copyright (c) 2017 Pierre Beaujeu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.