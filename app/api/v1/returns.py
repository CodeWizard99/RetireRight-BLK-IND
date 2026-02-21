from decimal import Decimal
from fastapi import APIRouter

from app.pipeline.orchestrator import PipelineOrchestrator
from app.schemas.requests.returns import ReturnsRequest

router = APIRouter(prefix="/returns", tags=["Returns"])


# ──────────────────────────────────────────────
# Adapters
# ──────────────────────────────────────────────

def _expenses_to_dict(expenses):
    return [
        {
            "date": e.timestamp,
            "amount": e.amount,
        }
        for e in expenses
    ]


def _q_periods_to_dict(periods):
    return [
        {
            "start": p.start,
            "end": p.end,
            "fixed": p.value,
        }
        for p in periods
    ]


def _p_periods_to_dict(periods):
    return [
        {
            "start": p.start,
            "end": p.end,
            "extra": p.value,
        }
        for p in periods
    ]


def _k_periods_to_dict(periods):
    return [
        {
            "start": p.start,
            "end": p.end,
        }
        for p in periods
    ]


# ──────────────────────────────────────────────
# /returns:nps
# ──────────────────────────────────────────────

@router.post(":nps")
def returns_nps(req: ReturnsRequest):
    orchestrator = PipelineOrchestrator()

    ctx = orchestrator.run(
        raw_transactions=_expenses_to_dict(req.expenses),
        q_periods=_q_periods_to_dict(req.q_periods),
        p_periods=_p_periods_to_dict(req.p_periods),
        k_periods=_k_periods_to_dict(req.k_periods),
        wage=Decimal(str(req.wage)),
        age=req.age,
        inflation_rate=Decimal(str(req.inflation)),
        instrument="nps",
    )

    return {
        "instrument": "nps",
        "returns": ctx.returns_results,
        "total_invested": str(ctx.total_transaction_amount),
        "total_ceiling": str(ctx.total_ceiling),
        "stage_metrics": ctx.stage_metrics,
        "duration_ms": ctx.pipeline_duration_ms,
        "errors": ctx.errors,
    }


# ──────────────────────────────────────────────
# /returns:index
# ──────────────────────────────────────────────

@router.post(":index")
def returns_index(req: ReturnsRequest):
    orchestrator = PipelineOrchestrator()

    ctx = orchestrator.run(
        raw_transactions=_expenses_to_dict(req.expenses),
        q_periods=_q_periods_to_dict(req.q_periods),
        p_periods=_p_periods_to_dict(req.p_periods),
        k_periods=_k_periods_to_dict(req.k_periods),
        wage=Decimal(str(req.wage)),
        age=req.age,
        inflation_rate=Decimal(str(req.inflation)),
        instrument="index",
    )

    return {
        "instrument": "index",
        "returns": ctx.returns_results,
        "total_invested": str(ctx.total_transaction_amount),
        "total_ceiling": str(ctx.total_ceiling),
        "stage_metrics": ctx.stage_metrics,
        "duration_ms": ctx.pipeline_duration_ms,
        "errors": ctx.errors,
    }