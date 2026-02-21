from fastapi import FastAPI
from app.api.router import api_router
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.timing import TimingMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.error_handler import global_exception_handler


def create_app() -> FastAPI:
    app = FastAPI(
        title="BlackRock Auto-Savings Challenge",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(
        RateLimiterMiddleware,
        max_requests=200,
        window_sec=60,
    )
    app.add_exception_handler(Exception, global_exception_handler)
    app.include_router(api_router)

    return app


app = create_app()