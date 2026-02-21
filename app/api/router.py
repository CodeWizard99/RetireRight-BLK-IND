from fastapi import APIRouter

from app.api.v1 import transactions, returns, performance

api_router = APIRouter(prefix="/blackrock/challenge/v1")

api_router.include_router(transactions.router)
api_router.include_router(returns.router)
api_router.include_router(performance.router)