"""
Stage 4 — P Period Processor.

Responsibility:
    Apply p period rules to q-processed transactions.
    Add extra amounts to remanent for transactions
    whose date falls within a p period.

Input  (from ctx): q_processed_transactions — after Stage 3
                   p_periods               — additive extra periods
Output (to ctx):   p_processed_transactions — remanents increased
                   p_extras_applied         — count for diagnostics

P Rules (from challenge spec):
    - ALL matching p periods contribute their extra (additive)
    - Multiple p periods match → sum ALL their extras
    - p applied AFTER q (adds on top of q result)
    - Remanent never goes below 0

Uses PProcessor (event sweep line) from core/period.

Complexity: O((n + p) log(n + p))
"""

from __future__ import annotations

from app.core.period.p_processor import PProcessor
from app.pipeline.base import BasePipelineStage, PipelineContext


class PProcessorStage(BasePipelineStage):
    """
    Stage 4: Apply p period additive extras to remanents.

    Delegates to core PProcessor for the sweep line algorithm.
    This stage is purely orchestration.
    """

    @property
    def stage_name(self) -> str:
        return "S4_PProcessor"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        """
        Apply p period rules to all q-processed transactions.

        If no p periods defined → pass transactions through unchanged.
        """
        if not ctx.p_periods:
            # No p periods — pass through untouched
            ctx.p_processed_transactions = ctx.q_processed_transactions
            ctx.p_extras_applied         = 0
            return ctx

        proc = PProcessor()
        proc.build(ctx.p_periods)

        result = proc.apply(ctx.q_processed_transactions)

        ctx.p_processed_transactions = result
        ctx.p_extras_applied         = sum(
            1 for t in result if t.get("p_extra_applied", False)
        )

        return ctx

    def _count_inputs(self, ctx: PipelineContext) -> int:
        return len(ctx.q_processed_transactions)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        return len(ctx.p_processed_transactions)