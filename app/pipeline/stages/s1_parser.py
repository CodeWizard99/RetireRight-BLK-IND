"""
Stage 1 — Transaction Parser.

Responsibility:
    Transform raw expense inputs into enriched transaction objects.
    Calculate ceiling and remanent for each expense.

Input  (from ctx): raw_transactions — list of {date, amount}
Output (to ctx):   parsed_transactions — list of {date, amount,
                                                   ceiling, remanent,
                                                   timestamp_unix}

Rules:
    - amount must be numeric and positive
    - ceiling = next multiple of 100 strictly above amount
    - remanent = ceiling - amount
    - timestamp_unix precomputed for downstream period processing

This stage does NOT validate business rules — that is Stage 2's job.
It only rejects what it cannot parse (bad types, unparseable dates).

Complexity: O(n) — one pass through transactions
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from app.core.financial.rounding import parse_and_round
from app.core.period.period_utils import to_epoch
from app.pipeline.base import BasePipelineStage, PipelineContext


class ParserStage(BasePipelineStage):
    """
    Stage 1: Parse and enrich raw expense transactions.

    Converts raw {date, amount} into fully enriched transaction dicts
    ready for downstream processing.
    """

    @property
    def stage_name(self) -> str:
        return "S1_Parser"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        """
        Parse all raw transactions.

        Skips unparseable entries (adds to invalid with reason).
        Successfully parsed entries go to parsed_transactions.
        """
        parsed  = []
        invalid = []

        for raw in ctx.raw_transactions:
            result = self._parse_one(raw)
            if result["_valid"]:
                result.pop("_valid")
                parsed.append(result)
            else:
                msg = result.pop("_error")
                result.pop("_valid")
                invalid.append({**result, "message": msg})

        ctx.parsed_transactions   = parsed
        # Parsing errors go into invalid — Stage 2 will add more
        ctx.invalid_transactions  = invalid

        return ctx

    def _parse_one(self, raw: dict) -> dict:
        """
        Parse a single raw transaction.

        Returns dict with _valid=True on success, _valid=False + _error on failure.
        """
        result: dict = {"date": raw.get("date", ""), "amount": raw.get("amount")}

        # ── Parse amount ─────────────────────────────────────
        try:
            amount = Decimal(str(raw["amount"]))
        except (InvalidOperation, KeyError, TypeError):
            return {**result, "_valid": False,
                    "_error": f"Invalid amount: {raw.get('amount')}"}

        result["amount"] = float(amount)

        # ── Parse timestamp → epoch ───────────────────────────
        try:
            epoch = to_epoch(str(raw["date"]))
        except (ValueError, KeyError) as e:
            return {**result, "_valid": False,
                    "_error": f"Invalid date format: {raw.get('date')} — {e}"}

        result["timestamp_unix"] = epoch

        # ── Calculate ceiling + remanent ──────────────────────
        # Negative/zero amounts will be caught here cleanly
        try:
            ceiling, remanent = parse_and_round(amount)
        except ValueError as e:
            return {**result, "_valid": False, "_error": str(e)}

        result["ceiling"]  = float(ceiling)
        result["remanent"] = Decimal(str(remanent))   # Keep as Decimal internally

        return {**result, "_valid": True}

    def _count_inputs(self, ctx: PipelineContext) -> int:
        return len(ctx.raw_transactions)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        return len(ctx.parsed_transactions)