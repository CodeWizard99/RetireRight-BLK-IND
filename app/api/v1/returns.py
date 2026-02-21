from decimal import Decimal
from fastapi import APIRouter

from app.pipeline.orchestrator import PipelineOrchestrator
from app.schemas.requests.returns import ReturnsRequest

router = APIRouter(prefix="/returns", tags=["Returns"])


# ──────────────────────────────────────────────
# Adapters — API → Pipeline DTO
# ──────────────────────────────────────────────

def _expenses_to_dict(expenses):
    """
    Convert request transactions → pipeline raw format.
    Core expects string timestamps.
    """
    return [
        {
            "date": e.date,
            "amount": e.amount,
        }
        for e in expenses
    ]


def _q_periods_to_dict(periods):
    return [
        {
            "start": p.start,
            "end": p.end,
            "fixed": p.fixed,
        }
        for p in periods
    ]


def _p_periods_to_dict(periods):
    return [
        {
            "start": p.start,
            "end": p.end,
            "extra": p.extra,
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
# Response Adapter — Pipeline → API DTO
# ──────────────────────────────────────────────

def _format_returns(ctx):

    return {
        "totalTransactionAmount": float(
            ctx.total_transaction_amount
        ),

        "totalCeiling": float(
            ctx.total_ceiling
        ),

        "savingsByDates": [
            {
                "start": r["start"],
                "end": r["end"],
                "amount": float(r["amount"]),
                "profit": float(r["profit"]),
                "taxBenefit": float(
                    r.get("tax_benefit", 0)
                ),
            }
            for r in ctx.returns_results
        ],
    }

# ──────────────────────────────────────────────
# /returns:nps
# ──────────────────────────────────────────────

@router.post(":nps")
def returns_nps(req: ReturnsRequest):

    orchestrator = PipelineOrchestrator()

    ctx = orchestrator.run(
        raw_transactions=_expenses_to_dict(req.transactions),
        q_periods=_q_periods_to_dict(req.q),
        p_periods=_p_periods_to_dict(req.p),
        k_periods=_k_periods_to_dict(req.k),
        wage=Decimal(str(req.wage)),
        age=req.age,
        inflation_rate=Decimal(str(req.inflation)),
        instrument="nps",
    )

    return _format_returns(ctx)


# ──────────────────────────────────────────────
# /returns:index
# ──────────────────────────────────────────────

@router.post(":index")
def returns_index(req: ReturnsRequest):

    orchestrator = PipelineOrchestrator()

    ctx = orchestrator.run(
        raw_transactions=_expenses_to_dict(req.transactions),
        q_periods=_q_periods_to_dict(req.q),
        p_periods=_p_periods_to_dict(req.p),
        k_periods=_k_periods_to_dict(req.k),
        wage=Decimal(str(req.wage)),
        age=req.age,
        inflation_rate=Decimal(str(req.inflation)),
        instrument="index",
    )

    return _format_returns(ctx)