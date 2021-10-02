"""Functions and constants for dealing with HTTP response status codes.

Attributes:
    CONTINUE (int): 100 - This interim response indicates that everything so far
        is OK and that the client should continue with the request or ignore it if it
        is already finished.
    SWITCHING_PROTOCOL (int): 101 - This code is sent in response to an Upgrade
        request header by the client, and indicates the protocol the server is
        switching to.
    PROCESSING (int): 102 - This code indicates that the server has received and
        is processing the request, but no response is available yet.
    EARLY_HINTS (int): 103 - This status code is primarily intended to be used
        with the Link header to allow the user agent to start preloading
        resources while the server is still preparing a response.
    OK (int): 200 - The request has succeeded. The meaning of a success varies
        depending on the HTTP method: For GET the resource has been fetched and
        is transmitted in the message body. For HEAD the entity headers are in
        the message body. For PUT or POST the resource describing the result of
        the action is transmitted in the message body. For TRACE the message
        body contains the request message as received by the server
    CREATED (int): 201 - The request has succeeded and a new resource has been
        created as a result of it. This is typically the response sent  after a
        POST request, or after some PUT requests.
    ACCEPTED (int): 202 - The request has been received but not yet acted upon.
        It is non-committal, meaning that there is no way in HTTP to later send
        an asynchronous response indicating the outcome of processing the
        request. It is intended for cases where another process or server
        handles the request, or for batch processing.
    NON_AUTHORITATIVE_INFORMATION (int): 203 - This response code means returned
        meta-information set is not exact set as available from the origin
        server, but collected from a local or a third party copy. Except this
        condition, 200 OK response should be preferred instead of this response.
    NO_CONTENT (int): 204 - There is no content to send for this request, but
        the headers may be useful. The user-agent may update its cached headers
        for this resource with the new ones.
    RESET_CONTENT (int): 205 - This response code is sent after accomplishing
        request to tell user agent reset document view which sent this request.
    PARTIAL_CONTENT (int): 206 - This response code is used because of range
        header sent by the client to separate download into multiple streams.
    MULTI_STATUS (int): 207 - A Multi-Status response conveys information about
        multiple resources in situations where multiple status codes might be
        appropriate.
    MULTI_STATUS_DAV (int): 208 - Used inside a DAV: propstat response element
        to avoid enumerating the internal members of multiple bindings to the
        same collection repeatedly.
    IM_USED (int): 226 - The server has fulfilled a GET request for the
        resource, and the response is a representation of the result of one or
        more instance-manipulations applied to the current instance.
    MULTIPLE_CHOICE (int): 300 - The request has more than one possible
        response. The user-agent or user should choose one of them. There is no
        standardized way of choosing one of the responses.
    MOVED_PERMANENTLY (int): 301 - This response code means that the URI of the
        requested resource has been changed permanently. Probably, the new URI
        would be given in the response.
    FOUND (int): 302 - This response code means that the URI of requested
        resource has been changed temporarily. New changes in the URI might be
        made in the future. Therefore, this same URI should be used by the
        client in future requests.
    SEE_OTHER (int): 303 - The server sent this response to direct the client to
        get the requested resource at another URI with a GET request.
    NOT_MODIFIED (int): 304 - This is used for caching purposes. It tells the
        client that the response has not been modified, so the client can
        continue to use the same cached version of the response.
    USE_PROXY (int): 305 - Was defined in a previous version of the HTTP
        specification to indicate that a requested response must be accessed by
        a proxy. It has been deprecated due to security concerns regarding
        in-band configuration of a proxy.
    UNUSED (int): 306 - This response code is no longer used, it is just
        reserved currently. It was used in a previous version of the HTTP 1.1
        specification.
    TEMPORARY_REDIRECT (int): 307 - The server sends this response to direct the
        client to get the requested resource at another URI with same method
        that was used in the prior request. This has the same semantics as the
        302 Found HTTP response code, with the exception that the user agent
        must not change the HTTP method used: If a POST was used in the first
        request, a POST must be used in the second request.
    PERMANENT_REDIRECT (int): 308 - This means that the resource is now
        permanently located at another URI, specified by the Location: HTTP
        Response header. This has the same semantics as the 301 Moved
        Permanently HTTP response code, with the exception that the user agent
        must not change the HTTP method used: If a POST was used in the first
        request, a POST must be used in the second request.
    BAD_REQUEST (int): 400 - This response means that server could not
        understand the request due to invalid syntax.
    UNAUTHORIZED (int): 401 - Although the HTTP standard specifies
        "unauthorized", semantically this response means "unauthenticated". That
        is, the client must authenticate itself to get the requested response.
    PAYMENT_REQUIRED (int): 402 - This response code is reserved for future use.
        Initial aim for creating this code was using it for digital payment
        systems however this is not used currently.
    FORBIDDEN (int): 403 - The client does not have access rights to the
        content, i.e. they are unauthorized, so server is rejecting to give
        proper response. Unlike 401, the client's identity is known to the
        server.
    NOT_FOUND (int): 404 - The server can not find requested resource. In the
        browser, this means the URL is not recognized. In an API, this can also
        mean that the endpoint is valid but the resource itself does not exist.
        Servers may also send this response instead of 403 to hide the existence
        of a resource from an unauthorized client. This response code is
        probably the most famous one due to its frequent occurrence on the web.
    METHOD_NOT_ALLOWED (int): 405 - The request method is known by the server
        but has been disabled and cannot be used. For example, an API may forbid
        DELETE-ing a resource. The two mandatory methods, GET and HEAD, must
        never be disabled and should not return this error code.
    NOT_ACCEPTABLE (int): 406 - This response is sent when the web server, after
        performing server-driven content negotiation, doesn't find any content
        following the criteria given by the user agent.
    PROXY_AUTHENTICATION_REQUIRED (int): 407 - This is similar to 401 but
        authentication is needed to be done by a proxy.
    REQUEST_TIMEOUT (int): 408 - This response is sent on an idle connection by
        some servers, even without any previous request by the client. It  means
        that the server would like to shut down this unused connection. This
        response is used much more since some browsers, like Chrome, Firefox
        27+, or IE9, use HTTP pre-connection mechanisms to speed up surfing.
        Also note that some servers merely shut down the connection without
        sending this message.
    CONFLICT (int): 409 - This response is sent when a request conflicts with
        the current state of the server.
    GONE (int): 410 - This response would be sent when the requested content has
        been permanently deleted from server, with no forwarding address.
        Clients are expected to remove their caches and links to the resource.
        The HTTP specification intends this status code to be used for
        "limited-time, promotional services". APIs should not feel compelled to
        indicate resources that have been deleted with this status code.
    LENGTH_REQUIRED (int): 411 - Server rejected the request because the
        content-length header field is not defined and the server requires it.
    PRECONDITION_FAILED (int): 412 - The client has indicated preconditions in
        its headers which the server does not meet.
    PAYLOAD_TOO_LARGE (int): 413 - Request entity is larger than limits defined
        by server; the server might close the connection or return an
        retry-after header field.
    URI_TOO_LONG (int): 414 - The URI requested by the client is longer than the
        server is willing to interpret.
    UNSUPPORTED_MEDIA_TYPE (int): 415 - The media format of the requested data
        is not supported by the server, so the server is rejecting the request.
    REQUESTED_RANGE_NOT_SATISFIABLE (int): 416 - The range specified by the
        Range header field in the request can't be fulfilled; it's possible that
        the range is outside the size of the target URI's data.
    EXPECTATION_FAILED (int): 417 - This response code means the expectation
        indicated by the Expect request header field can't be met by the server.
    IM_A_TEAPOT (int): 418 - The server refuses the attempt to brew coffee with
        a teapot.
    MISDIRECTED_REQUEST (int): 421 - The request was directed at a server that
        is not able to produce a response. This can be sent by a server that is
        not configured to produce responses for the combination of scheme and
        authority that are included in the request URI.
    UNPROCESSABLE_ENTITY (int): 422 - The request was well-formed but was unable
        to be followed due to semantic errors.
    LOCKED (int): 423 - The resource that is being accessed is locked.
    FAILED_DEPENDENCY (int): 424 - The request failed due to failure of a
        previous request.
    TOO_EARLY (int): 425 - Indicates that the server is unwilling to risk
        processing a request that might be replayed.
    UPGRADE_REQUIRED (int): 426 - The server refuses to perform the request
        using the current protocol but might be willing to do so after the
        client upgrades to a different protocol. The server sends an Upgrade
        header in a 426 response to indicate the required protocol(s).
    PRECONDITION_REQUIRED (int): 428 - The origin server requires the request to
        be conditional. Intended to prevent the 'lost update' problem, where a
        client GETs a resource's state, modifies it, and PUTs it back to the
        server, when meanwhile a third party has modified the state on the
        server, leading to a conflict.
    TOO_MANY_REQUESTS (int): 429 - The user has sent too many requests in a
        given amount of time ("rate limiting").
    REQUEST_HEADER_FIELDS_TOO_LARGE (int): 431 - The server is unwilling to
        process the request because its header fields are too large. The request
        MAY be resubmitted after reducing the size of the request header fields.
    UNAVAILABLE_FOR_LEGAL_REASONS (int): 451 - The user requests an illegal
        resource, such as a web page censored by a government.
    INTERNAL_SERVER_ERROR (int): 500 - The server has encountered a situation it
        doesn't know how to handle.
    NOT_IMPLEMENTED (int): 501 - The request method is not supported by the
        server and cannot be handled. The only methods that servers are required
        to support (and therefore that must not return this code) are GET and
        HEAD.
    BAD_GATEWAY (int): 502 - This error response means that the server, while
        working as a gateway to get a response needed to handle the request, got
        an invalid response.
    SERVICE_UNAVAILABLE (int): 503 - The server is not ready to handle the
        request. Common causes are a server that is down for maintenance or that
        is overloaded. Note that together with this response, a user-friendly
        page explaining the problem should be sent. This responses should be
        used for temporary conditions and the Retry-After: HTTP header should,
        if possible, contain the estimated time before the recovery of the
        service. The webmaster must also take care about the caching-related
        headers that are sent along with this response, as these temporary
        condition responses should usually not be cached.
    GATEWAY_TIMEOUT (int): 504 - This error response is given when the server is
        acting as a gateway and cannot get a response in time.
    HTTP_VERSION_NOT_SUPPORTED (int): 505 - The HTTP version used in the request
        is not supported by the server.
    VARIANT_ALSO_NEGOTIATES (int): 506 - The server has an internal
        configuration error: transparent content negotiation for the request
        results in a circular reference.
    INSUFFICIENT_STORAGE (int): 507 - The server has an internal configuration
        error: the chosen variant resource is configured to engage in
        transparent content negotiation itself, and is therefore not a proper
        end point in the negotiation process.
    LOOP_DETECTED (int): 508 - The server detected an infinite loop while
        processing the request.
    NOT_EXTENDED (int): 510 - Further extensions to the request are required for
        the server to fulfill it.
    NETWORK_AUTHENTICATION_IS_REQUIRED 9int): 511 - The 511 status code
        indicates that the client needs to authenticate to gain network access.
"""


def is_information(code: int) -> bool:
    """Return true if the code is an information HTTP response code.

    Args:
        code (int): The HTTP response code.

    Returns:
        bool: True if the code was informational else false.
    """
    return 100 <= code < 200


def is_successful(code: int) -> bool:
    """Return true if the code is a successful HTTP response code.

    Args:
        code (int): The HTTP response code.

    Returns:
        bool: True if the code was successful else false.
    """
    return 200 <= code < 300


def is_redirection(code: int) -> bool:
    """Return true if the code is aa redirection HTTP response code.

    Args:
        code (int): The HTTP response code.

    Returns:
        bool: True if the code was a redirection else false.
    """
    return 300 <= code < 400


def is_client_error(code: int) -> bool:
    """Return true if the code is a client error HTTP response code.

    Args:
        code (int): The HTTP response code.

    Returns:
        bool: True if the code was a client error else false.
    """
    return 400 <= code < 500


def is_server_error(code: int) -> bool:
    """Return true if the code is a server error HTTP response code.

    Args:
        code (int): The HTTP response code.

    Returns:
        bool: True if the code was a server error else false.
    """
    return 500 <= code < 600


# Information responses

"""
This interim response indicates that everything so far is OK and that the client
should continue with the request or ignore it if it is already finished.
"""
CONTINUE = 100

"""
This code is sent in response to an Upgrade request header by the client, and
indicates the protocol the server is  switching to.
"""
SWITCHING_PROTOCOL = 101

"""
This code indicates that the server has received and is processing the request,
but no response is available yet.
"""
PROCESSING = 102

"""
This status code is primarily intended to be used with the Link header to allow
the user agent to start preloading resources while the server is still preparing
a response.
"""
EARLY_HINTS = 103

# Successful responses

"""
The request has succeeded. The meaning of a success varies depending on the HTTP
method:
GET: The resource has been fetched and is transmitted in the message body.
HEAD: The entity headers are in the message body.
PUT or POST: The resource describing the result of the action is transmitted in the message body.
TRACE: The message body contains the request message as received by the server
"""
OK = 200

"""
The request has succeeded and a new resource has been created as a result of it.
This is typically the response sent  after a POST request, or after some PUT
requests.
"""
CREATED = 201

"""
The request has been received but not yet acted upon. It is non-committal,
meaning that there is no way in HTTP to later send an asynchronous response
indicating the outcome of processing the request. It is intended for cases where
another process or server handles the request, or for batch processing.
"""
ACCEPTED = 202

"""
This response code means returned meta-information set is not exact set as
available from the origin server, but collected from a local or a third party
copy. Except this condition, 200 OK response should be preferred instead of this
response.
"""
NON_AUTHORITATIVE_INFORMATION = 203

"""
There is no content to send for this request, but the headers may be useful. The
user-agent may update its cached headers for this resource with the new ones.
"""
NO_CONTENT = 204

"""
This response code is sent after accomplishing request to tell user agent reset
document view which sent this request.
"""
RESET_CONTENT = 205

"""
This response code is used because of range header sent by the client to
separate download into multiple streams.
"""
PARTIAL_CONTENT = 206

"""
A Multi-Status response conveys information about multiple resources in
situations where multiple status codes might be appropriate.
"""
MULTI_STATUS = 207

"""
Used inside a DAV: propstat response element to avoid enumerating the internal
members of multiple bindings to the same collection repeatedly.
"""
MULTI_STATUS_DAV = 208

"""
The server has fulfilled a GET request for the resource, and the response is a
representation of the result of one or more instance-manipulations applied to
the current instance.
"""
IM_USED = 226

# Redirection messages

"""
The request has more than one possible response. The user-agent or user should
choose one of them. There is no standardized way of choosing one of the
responses.
"""
MULTIPLE_CHOICE = 300

"""
This response code means that the URI of the requested resource has been changed
permanently. Probably, the new URI would be given in the response.
"""
MOVED_PERMANENTLY = 301

"""
This response code means that the URI of requested resource has been changed
temporarily. New changes in the URI might be made in the future. Therefore, this
same URI should be used by the client in future requests.
"""
FOUND = 302

"""
The server sent this response to direct the client to get the requested resource
at another URI with a GET request.
"""
SEE_OTHER = 303

"""
This is used for caching purposes. It tells the client that the response has not
been modified, so the client can continue to use the same cached version of the
response.
"""
NOT_MODIFIED = 304

"""
Was defined in a previous version of the HTTP specification to indicate that a
requested response must be accessed by a proxy. It has been deprecated due to
security concerns regarding in-band configuration of a proxy.
"""
USE_PROXY = 305

"""
This response code is no longer used, it is just reserved currently. It was used
in a previous version of the HTTP 1.1 specification.
"""
UNUSED = 306

"""
The server sends this response to direct the client to get the requested
resource at another URI with same method that was used in the prior request.
This has the same semantics as the 302 Found HTTP response code, with the
exception that the user agent must not change the HTTP method used: If a POST
was used in the first request, a POST must be used in the second request.
"""
TEMPORARY_REDIRECT = 307

"""
This means that the resource is now permanently located at another URI,
specified by the Location: HTTP Response header. This has the same semantics as
the 301 Moved Permanently HTTP response code, with the exception that the user
agent must not change the HTTP method used: If a POST was used in the first
request, a POST must be used in the second request.
"""
PERMANENT_REDIRECT = 308

# Client error responses

"""
This response means that server could not understand the request due to invalid
syntax.
"""
BAD_REQUEST = 400

"""
Although the HTTP standard specifies "unauthorized", semantically this response
means "unauthenticated". That is, the client must authenticate itself to get the
requested response.
"""
UNAUTHORIZED = 401

"""
This response code is reserved for future use. Initial aim for creating this
code was using it for digital payment systems however this is not used
currently.
"""
PAYMENT_REQUIRED = 402

"""
The client does not have access rights to the content, i.e. they are
unauthorized, so server is rejecting to give proper response. Unlike 401, the
client's identity is known to the server.
"""
FORBIDDEN = 403

"""
The server can not find requested resource. In the browser, this means the URL
is not recognized. In an API, this can also mean that the endpoint is valid but
the resource itself does not exist. Servers may also send this response instead
of 403 to hide the existence of a resource from an unauthorized client. This
response code is probably the most famous one due to its frequent occurrence on
the web.
"""
NOT_FOUND = 404

"""
The request method is known by the server but has been disabled and cannot be
used. For example, an API may forbid DELETE-ing a resource. The two mandatory
methods, GET and HEAD, must never be disabled and should not return this error
code.
"""
METHOD_NOT_ALLOWED = 405

"""
This response is sent when the web server, after performing server-driven
content negotiation, doesn't find any content following the criteria given by
the user agent.
"""
NOT_ACCEPTABLE = 406

"""
This is similar to 401 but authentication is needed to be done by a proxy.
"""
PROXY_AUTHENTICATION_REQUIRED = 407

"""
This response is sent on an idle connection by some servers, even without any
previous request by the client. It means that the server would like to shut down
this unused connection. This response is used much more since some browsers,
like Chrome, Firefox 27+, or IE9, use HTTP pre-connection mechanisms to speed up
surfing. Also note that some servers merely shut down the connection without
sending this message.
"""
REQUEST_TIMEOUT = 408

"""
This response is sent when a request conflicts with the current state of the
server.
"""
CONFLICT = 409

"""
This response would be sent when the requested content has been permanently
deleted from server, with no forwarding address. Clients are expected to remove
their caches and links to the resource. The HTTP specification intends this
status code to be used for "limited-time, promotional services". APIs should not
feel compelled to indicate resources that have been deleted with this status code.
"""
GONE = 410

"""
Server rejected the request because the Content-Length header field is not
defined and the server requires it.
"""
LENGTH_REQUIRED = 411

"""
The client has indicated preconditions in its headers which the server does not
meet.
"""
PRECONDITION_FAILED = 412

"""
Request entity is larger than limits defined by server; the server might close
the connection or return an Retry-After header field.
"""
PAYLOAD_TOO_LARGE = 413

"""
The URI requested by the client is longer than the server is willing to
interpret.
"""
URI_TOO_LONG = 414

"""
The media format of the requested data is not supported by the server, so the
server is rejecting the request.
"""
UNSUPPORTED_MEDIA_TYPE = 415

"""
The range specified by the Range header field in the request can't be fulfilled;
it's possible that the range is outside the size of the target URI's data.
"""
REQUESTED_RANGE_NOT_SATISFIABLE = 416

"""
This response code means the expectation indicated by the Expect request header
field can't be met by the server.
"""
EXPECTATION_FAILED = 417

"""
The server refuses the attempt to brew coffee with a teapot.
"""
IM_A_TEAPOT = 418

"""
The request was directed at a server that is not able to produce a response.
This can be sent by a server that is not configured to produce responses for the
combination of scheme and authority that are included in the request URI.
"""
MISDIRECTED_REQUEST = 421

"""
The request was well-formed but was unable to be followed due to semantic
errors.
"""
UNPROCESSABLE_ENTITY = 422

"""
The resource that is being accessed is locked.
"""
LOCKED = 423

"""
The request failed due to failure of a previous request.
"""
FAILED_DEPENDENCY = 424

"""
Indicates that the server is unwilling to risk processing a request that might
be replayed.
"""
TOO_EARLY = 425

"""
The server refuses to perform the request using the current protocol but might
be willing to do so after the client upgrades to a different protocol. The
server sends an Upgrade header in a 426 response to indicate the required
protocol(s).
"""
UPGRADE_REQUIRED = 426

"""
The origin server requires the request to be conditional. Intended to prevent
the 'lost update' problem, where a client GETs a resource's state, modifies it,
and PUTs it back to the server, when meanwhile a third party has modified the
state on the server, leading to a conflict.
"""
PRECONDITION_REQUIRED = 428

"""
The user has sent too many requests in a given amount of time ("rate limiting").
"""
TOO_MANY_REQUESTS = 429

"""
The server is unwilling to process the request because its header fields are too
large. The request MAY be resubmitted after reducing the size of the request
header fields.
"""
REQUEST_HEADER_FIELDS_TOO_LARGE = 431

"""
The user requests an illegal resource, such as a web page censored by a
government.
"""
UNAVAILABLE_FOR_LEGAL_REASONS = 451

# Server error responses

"""
The server has encountered a situation it doesn't know how to handle.
"""
INTERNAL_SERVER_ERROR = 500

"""
The request method is not supported by the server and cannot be handled. The
only methods that servers are required to support (and therefore that must not
return this code) are GET and HEAD.
"""
NOT_IMPLEMENTED = 501

"""
This error response means that the server, while working as a gateway to get a
response needed to handle the request, got an invalid response.
"""
BAD_GATEWAY = 502

"""
The server is not ready to handle the request. Common causes are a server that
is down for maintenance or that is overloaded. Note that together with this
response, a user-friendly page explaining the problem should be sent. This
responses should be used for temporary conditions and the Retry-After: HTTP
header should, if possible, contain the estimated time before the recovery of
the service. The webmaster must also take care about the caching-related headers
that are sent along with this response, as these temporary condition responses
should usually not be cached.
"""
SERVICE_UNAVAILABLE = 503

"""
This error response is given when the server is acting as a gateway and cannot
get a response in time.
"""
GATEWAY_TIMEOUT = 504

"""
The HTTP version used in the request is not supported by the server.
"""
HTTP_VERSION_NOT_SUPPORTED = 505

"""
The server has an internal configuration error: transparent content negotiation
for the request results in a circular reference.
"""
VARIANT_ALSO_NEGOTIATES = 506

"""
The server has an internal configuration error: the chosen variant resource is
configured to engage in transparent content negotiation itself, and is therefore
not a proper end point in the negotiation process.
"""
INSUFFICIENT_STORAGE = 507

"""
The server detected an infinite loop while processing the request.
"""
LOOP_DETECTED = 508

"""
Further extensions to the request are required for the server to fulfill it.
"""
NOT_EXTENDED = 510

"""
The 511 status code indicates that the client needs to authenticate to gain
network access.
"""
NETWORK_AUTHENTICATION_IS_REQUIRED = 511
