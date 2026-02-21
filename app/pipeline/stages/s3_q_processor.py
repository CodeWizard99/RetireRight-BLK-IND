"""
Stage 3 — Q Period Processor.

Responsibility:
    Apply q period rules to valid transactions.
    Replace remanent with fixed amount for transactions
    whose date falls within a q period.

Input  (from ctx): valid_transactions — after Stage 2
                   q_periods          — fixed amount periods
Output (to ctx):   q_processed_transactions — remanents possibly replaced
                   q_overrides_applied      — count for diagnostics

Q Rules (from challenge spec):
    - Transaction in q period → replace remanent with fixed amount
    - Multiple q periods match → use the one with LATEST start date
    - Same start date → use FIRST in original list (lowest index)
    - q applied BEFORE p (processing order matters)

Uses QProcessor (sorted list + active heap) from core/period.

Complexity: O((n + q) log q)
"""

from __future__ import annotations

from app.core.period.q_processor import QProcessor
from app.pipeline.base import BasePipelineStage, PipelineContext


class QProcessorStage(BasePipelineStage):
    """
    Stage 3: Apply q period fixed-amount overrides.

    Delegates to core QProcessor for the actual algorithm.
    This stage is purely orchestration — no business logic here.
    """

    @property
    def stage_name(self) -> str:
        return "S3_QProcessor"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        """
        Apply q period rules to all valid transactions.

        If no q periods defined → pass transactions through unchanged.
        """
        if not ctx.q_periods:
            # No q periods — pass through untouched
            ctx.q_processed_transactions = ctx.valid_transactions
            ctx.q_overrides_applied      = 0
            return ctx

        proc = QProcessor()
        proc.build(ctx.q_periods)

        result = proc.apply(ctx.valid_transactions)

        ctx.q_processed_transactions = result
        ctx.q_overrides_applied      = sum(
            1 for t in result if t.get("q_period_applied", False)
        )

        return ctx

    def _count_inputs(self, ctx: PipelineContext) -> int:
        return len(ctx.valid_transactions)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        return len(ctx.q_processed_transactions)