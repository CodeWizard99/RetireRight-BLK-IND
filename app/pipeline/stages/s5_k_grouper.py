"""
Stage 5 — K Period Grouper.

Responsibility:
    Group p-processed transactions into k evaluation periods.
    Sum remanents per k period for returns calculation.

Input  (from ctx): p_processed_transactions — after Stage 4
                   k_periods               — evaluation date windows
Output (to ctx):   k_results               — list of period summaries
                                             with amount per period

K Rules (from challenge spec):
    - For each k period: sum remanents of transactions in [start, end]
    - A transaction can belong to MULTIPLE k periods simultaneously
    - Each k period calculated independently — no shared state
    - Date ranges inclusive on both ends

Uses KPeriodGrouper (prefix sum + binary search) from core/period.
Preprocessing once, O(log n) query per k period.

Complexity: O(n log n) build + O(k log n) queries
"""

from __future__ import annotations

from app.core.period.k_grouper import KPeriodGrouper
from app.pipeline.base import BasePipelineStage, PipelineContext


class KGrouperStage(BasePipelineStage):
    """
    Stage 5: Group transactions into k evaluation periods.

    Delegates to core KPeriodGrouper for prefix sum + binary search.
    This stage is purely orchestration.
    """

    @property
    def stage_name(self) -> str:
        return "S5_KGrouper"

    def process(self, ctx: PipelineContext) -> PipelineContext:

        if not ctx.k_periods:
            ctx.k_results = []
            return ctx

        grouper = KPeriodGrouper()
        grouper.build(ctx.p_processed_transactions)

        raw_results = grouper.compute_all(ctx.k_periods)

        # ──────────────────────────────────────────────
        # 1️⃣ Aggregate results (existing behavior)
        # ──────────────────────────────────────────────
        ctx.k_results = [
            {
                "start":             r.start,
                "end":               r.end,
                "start_epoch":       r.start_epoch,
                "end_epoch":         r.end_epoch,
                "amount":            r.amount,
                "transaction_count": r.transaction_count,
            }
            for r in raw_results
        ]

        # ──────────────────────────────────────────────
        # 2️⃣ Annotate transactions with inkPeriod flag
        # ──────────────────────────────────────────────
        for txn in ctx.p_processed_transactions:

            ts = txn["timestamp_unix"]

            in_any_k = any(
                r.start_epoch <= ts <= r.end_epoch
                for r in raw_results
            )

            txn["in_k_period"] = in_any_k

        return ctx

    def _count_inputs(self, ctx: PipelineContext) -> int:
        return len(ctx.p_processed_transactions)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        return len(ctx.k_results)