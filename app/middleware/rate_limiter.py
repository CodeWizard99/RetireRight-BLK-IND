"""
Simple in-memory rate limiter.
"""

import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimiterMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, max_requests: int = 100, window_sec: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_sec   = window_sec
        self.request_log  = defaultdict(list)

    async def dispatch(self, request: Request, call_next):

        # Safely extract client IP
        client = request.client
        client_ip = client.host if client else "unknown"

        now = time.time()
        timestamps = self.request_log[client_ip]

        # Remove expired entries
        cutoff = now - self.window_sec
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

        # Enforce limit
        if len(timestamps) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "limit": self.max_requests,
                    "window_sec": self.window_sec,
                },
            )

        timestamps.append(now)

        return await call_next(request)