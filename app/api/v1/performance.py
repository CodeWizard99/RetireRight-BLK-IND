from fastapi import APIRouter
from app.observability.performance_store import get_performance_metrics

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("")
def performance():
    return get_performance_metrics()