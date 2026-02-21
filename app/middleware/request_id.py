"""
Request ID Middleware.

Adds a unique request identifier to:
    - request.state.request_id
    - Response headers (X-Request-ID)

Useful for tracing, debugging, and log correlation.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        # Generate UUID4 request ID
        request_id = str(uuid.uuid4())

        # Attach to request context
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response