"""
Stage 2 — Transaction Validator.

Responsibility:
    Apply business rules to parsed transactions.
    Separate into valid and invalid with clear error messages.

Input  (from ctx): parsed_transactions — enriched with ceiling/remanent
Output (to ctx):   valid_transactions   — pass all rules
                   invalid_transactions — fail any rule (with message)

Validation rules (in order):
    1. Amount must be positive (> 0)
    2. Amount must be < 5 × 10^5 (500,000)
    3. Timestamp must be unique (ti ≠ tj constraint from challenge)
    4. Ceiling must be correct multiple of 100
    5. Remanent must equal ceiling - amount

Duplicate detection uses a hash set — O(1) per lookup, O(n) total.
Stage is stateless — safe for concurrent use.

Complexity: O(n) overall
"""

from __future__ import annotations
from decimal import Decimal
from app.pipeline.base import BasePipelineStage, PipelineContext

# From challenge spec: x < 5 × 10^5
_MAX_AMOUNT     = Decimal("500000")
_ROUNDING_MULT  = 100


class ValidatorStage(BasePipelineStage):
    """
    Stage 2: Validate parsed transactions against business rules.

    Produces clean split of valid / invalid transactions.
    Invalid transactions carry a human-readable message field.
    """

    @property
    def stage_name(self) -> str:
        return "S2_Validator"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        """
        Validate all parsed transactions.

        Starts with any parse errors from Stage 1 already in
        invalid_transactions, appends new validation failures.
        """
        valid:    list[dict] = []
        invalid:  list[dict] = list(ctx.invalid_transactions)  # carry forward parse errors
        seen_timestamps: set[int] = set()

        for txn in ctx.parsed_transactions:
            failure = self._validate(txn, seen_timestamps)
            if failure:
                invalid.append({**txn, "message": failure})
            else:
                seen_timestamps.add(txn["timestamp_unix"])
                valid.append(txn)

        ctx.valid_transactions   = valid
        ctx.invalid_transactions = invalid

        # Totals used by returns endpoint
        ctx.total_transaction_amount = sum(
            (Decimal(str(t["amount"])) for t in valid), 
            Decimal("0")  # <--- Explicit start value
        )

        ctx.total_ceiling = sum(
            (Decimal(str(t["ceiling"])) for t in valid), 
            Decimal("0")  # <--- Explicit start value
        )

        return ctx

    def _validate(
        self,
        txn: dict,
        seen: set[int],
    ) -> str | None:
        """
        Run all validation rules on a single transaction.

        Returns:
            None if valid, error message string if invalid.
        """
        amount = Decimal(str(txn["amount"]))

        # Rule 1: must be positive
        if amount < Decimal("0"):
            return "Negative amounts are not allowed"

        if amount == Decimal("0"):
            return "Amount must be greater than zero"

        # Rule 2: must be within bounds
        if amount >= _MAX_AMOUNT:
            return f"Amount {amount} exceeds maximum allowed {_MAX_AMOUNT}"

        # Rule 3: duplicate timestamp
        ts = txn["timestamp_unix"]
        if ts in seen:
            return "Duplicate transaction"

        # Rule 4 + 5: ceiling/remanent consistency
        ceiling  = Decimal(str(txn["ceiling"]))
        remanent = Decimal(str(txn["remanent"]))
        _m       = Decimal(str(_ROUNDING_MULT))

        if ceiling % _m != Decimal("0"):
            return f"Ceiling {ceiling} is not a multiple of {_ROUNDING_MULT}"

        if ceiling <= amount:
            return f"Ceiling {ceiling} must be greater than amount {amount}"

        expected_remanent = ceiling - amount
        if abs(remanent - expected_remanent) > Decimal("0.001"):
            return (
                f"Remanent {remanent} does not match "
                f"ceiling - amount = {expected_remanent}"
            )

        return None  # All rules passed

    def _count_inputs(self, ctx: PipelineContext) -> int:
        return len(ctx.parsed_transactions)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        return len(ctx.valid_transactions)