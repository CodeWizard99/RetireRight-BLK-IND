"""
Period Pipeline Orchestrator.

Wires together Q → P → K processing in the correct order.
This is the single entry point for all period-related logic.

Processing order (from challenge spec):
    Step 1: ceiling + remanent (done upstream in parser)
    Step 2: Apply q rules     (replace remanent if in q period)
    Step 3: Apply p rules     (add extra if in p period)
    Step 4: Group by k        (sum remanents per k period)
    Step 5: Calculate returns (done downstream in returns engine)

This module owns Steps 2–4.

Complexity: O((n + q + p) log(n + q + p) + k log n)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.core.period.k_grouper import KPeriodGrouper, KPeriodResult
from app.core.period.p_processor import PProcessor
from app.core.period.period_utils import to_epoch
from app.core.period.q_processor import QProcessor


@dataclass
class PipelineInput:
    """
    Input to the period pipeline.
    All transactions must have timestamp_unix pre-computed.
    """
    transactions: list[dict]   # Each must have: timestamp_unix, remanent
    q_periods:    list[dict]   # Each: start, end, fixed
    p_periods:    list[dict]   # Each: start, end, extra
    k_periods:    list[dict]   # Each: start, end


@dataclass
class PipelineOutput:
    """
    Output from the period pipeline.
    """
    # Transactions after q + p applied
    processed_transactions: list[dict]

    # K period grouping results
    k_results: list[KPeriodResult]

    # Diagnostic counts
    q_overrides_applied: int
    p_extras_applied: int


class PeriodPipeline:
    """
    Orchestrates Q → P → K period processing.

    Stateless — build processors per request.
    Safe for concurrent use with separate instances.

    Usage:
        pipeline = PeriodPipeline()
        output = pipeline.run(input)
    """

    def run(self, pipeline_input: PipelineInput) -> PipelineOutput:
        """
        Execute the full period processing pipeline.

        Args:
            pipeline_input: Transactions + all period definitions

        Returns:
            PipelineOutput with processed transactions and k results
        """
        txns       = pipeline_input.transactions
        q_periods  = pipeline_input.q_periods
        p_periods  = pipeline_input.p_periods
        k_periods  = pipeline_input.k_periods

        # ── Step 1: Attach epoch to each transaction ─────────────
        # Ensures all processors work with integers, not strings
        txns = self._attach_epochs(txns)

        # ── Step 2: Apply Q rules ────────────────────────────────
        q_proc = QProcessor()
        q_proc.build(q_periods)
        txns_after_q = q_proc.apply(txns)
        q_count = sum(
            1 for t in txns_after_q if t.get("q_period_applied", False)
        )

        # ── Step 3: Apply P rules ────────────────────────────────
        p_proc = PProcessor()
        p_proc.build(p_periods)
        txns_after_p = p_proc.apply(txns_after_q)
        p_count = sum(
            1 for t in txns_after_p if t.get("p_extra_applied", False)
        )

        # ── Step 4: K Grouping ───────────────────────────────────
        grouper = KPeriodGrouper()
        grouper.build(txns_after_p)
        k_results = grouper.compute_all(k_periods)

        return PipelineOutput(
            processed_transactions=txns_after_p,
            k_results=k_results,
            q_overrides_applied=q_count,
            p_extras_applied=p_count,
        )

    @staticmethod
    def _attach_epochs(transactions: list[dict]) -> list[dict]:
        """
        Pre-compute epoch for every transaction.
        Mutates timestamp_unix field if not already present.

        O(n) with LRU-cached to_epoch calls.
        """
        result = []
        for txn in transactions:
            if "timestamp_unix" not in txn:
                updated = dict(txn)
                updated["timestamp_unix"] = to_epoch(txn["date"])
                result.append(updated)
            else:
                result.append(txn)
        return result