from decimal import Decimal
from fastapi import APIRouter

from app.pipeline.orchestrator import PipelineOrchestrator
from app.schemas.requests.parse import ParseRequest
from app.schemas.requests.validator import ValidatorRequest
from app.schemas.requests.filter import FilterRequest
from app.schemas.responses.parse import (
    ParseResponse,
    TransactionParsed,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ──────────────────────────────────────────────
# Adapters — Pydantic → Pipeline dict contract
# ──────────────────────────────────────────────

def _expenses_to_dict(expenses):
    return [
        {
            "date": e.date,
            "amount": e.amount,
        }
        for e in expenses
    ]

def _transactions_to_dict(transactions):
    result = []

    for t in transactions:
        ts_unix = int(t.date.timestamp())

        result.append({
            "date": t.date,
            "timestamp_unix": ts_unix,   # 🔥 Required by validator
            "amount": t.amount,
            "ceiling": t.ceiling,
            "remanent": t.remanent,
        })

    return result


def _q_to_dict(q_periods):
    return [
        {
            "fixed": x.fixed,
            "start": x.start.strftime("%Y-%m-%d %H:%M:%S"),
            "end": x.end.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for x in q_periods
    ]

def _p_to_dict(p_periods):
    return [
        {
            "extra": x.extra,
            "start": x.start.strftime("%Y-%m-%d %H:%M:%S"),
            "end": x.end.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for x in p_periods
    ]

def _k_to_dict(k_periods):
    return [
        {
            "start": x.start.strftime("%Y-%m-%d %H:%M:%S"),
            "end": x.end.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for x in k_periods
    ]

from app.core.period.period_utils import epoch_to_str


def _format_valid(txns):

    formatted = []

    for t in txns:
        formatted.append({
            "date": epoch_to_str(t["timestamp_unix"]),
            "amount": float(t["amount"]),
            "ceiling": float(t["ceiling"]),
            "remanent": float(t["remanent"]),
            "inkPeriod": t.get("in_k_period", True)  # default True
        })

    return formatted


def _format_invalid(txns):

    formatted = []

    for t in txns:
        formatted.append({
            "date": epoch_to_str(t["timestamp_unix"]),
            "amount": float(t["amount"]),
            "message": t["message"],
        })

    return formatted

# ──────────────────────────────────────────────
# /transactions:parse  → S1 only
# ──────────────────────────────────────────────

@router.post(":parse")
def parse_transactions(req: ParseRequest):
    orchestrator = PipelineOrchestrator()

    ctx = orchestrator.run_parse_only(
        raw_transactions=_expenses_to_dict(req.root)
    )
    transactions = [
        TransactionParsed(
            date=tx["date"].strftime("%Y-%m-%d %H:%M:%S"),        # rename field
            amount=float(tx["amount"]),
            ceiling=float(tx["ceiling"]),
            remanent=float(tx["remanent"]),
        )
        for tx in ctx.parsed_transactions
    ]

    total_remanent = sum(tx.remanent for tx in transactions)

    return transactions
    return ParseResponse(
        transactions=transactions,
        # total_remanent=total_remanent,
    )


# ──────────────────────────────────────────────
# /transactions:validator  → S1 + S2
# ──────────────────────────────────────────────

@router.post(":validator")
def validate_transactions(req: ValidatorRequest):

    orchestrator = PipelineOrchestrator()

    ctx = orchestrator.run_validate_only(
        parsed_transactions=_transactions_to_dict(req.transactions),
        wage=Decimal(str(req.wage)),
    )

    return {
        "valid": ctx.valid_transactions,
        "invalid": ctx.invalid_transactions,
        "duration_ms": ctx.pipeline_duration_ms,
    }

    # return {
    #     "valid": ctx.valid_transactions,
    #     "invalid": ctx.invalid_transactions,
    #     "stage_metrics": ctx.stage_metrics,
    #     "duration_ms": ctx.pipeline_duration_ms,
    #     "errors": ctx.errors,
    # }


# ──────────────────────────────────────────────
# /transactions:filter  → S1 → S5
# ──────────────────────────────────────────────

@router.post(":filter")
def filter_transactions(req: FilterRequest):

    orchestrator = PipelineOrchestrator()

    ctx = orchestrator.run_filter_only(
        raw_transactions=_expenses_to_dict(req.transactions),
        q_periods=_q_to_dict(req.q),
        p_periods=_p_to_dict(req.p),
        k_periods=_k_to_dict(req.k),
        wage=Decimal(str(req.wage)),
    )

    return {
        "valid": _format_valid(ctx.valid_transactions),
        "invalid": _format_invalid(ctx.invalid_transactions),
        "duration_ms": ctx.pipeline_duration_ms,
    }