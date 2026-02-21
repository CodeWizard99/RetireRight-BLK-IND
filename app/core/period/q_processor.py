"""
Q Period Processor — Sorted list + active set approach.

Problem:
    Up to 1M q periods, up to 1M transactions.
    For each transaction, find which q period applies
    (latest start date wins; tie → first in original list).

Algorithm — Sweep with Active Set:
    1. Convert all q periods to epoch, sort by start ascending
    2. Sort transactions by timestamp ascending
    3. Sweep left to right:
       - Maintain an "active set" of q periods whose start <= current txn
       - Remove from active set any period whose end < current txn
       - Active set is a max-heap keyed by (start DESC, index ASC)
         so top of heap is always the correct answer

Complexity:
    Preprocessing:  O(q log q + n log n)   — sorting
    Processing:     O((n + q) log q)        — heap ops
    Total:          O((n + q) log(n + q))

vs Naive: O(n * q) = 10^12 ops at max scale → completely infeasible
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from decimal import Decimal

from app.core.period.period_utils import to_epoch


@dataclass(slots=True, order=False)
class QPeriod:
    """A single q period with precomputed epochs."""
    start:          int     # epoch
    end:            int     # epoch
    fixed:          Decimal
    original_index: int     # position in input — for tie-breaking


class QProcessor:
    """
    Processes q period rules using sorted list + active heap.

    Q Rule:
        - If transaction timestamp falls in a q period → replace
          remanent with period's fixed amount
        - Multiple matches → latest start wins
        - Same start → lowest original_index wins (first in input)

    Usage:
        proc = QProcessor()
        proc.build(q_periods)
        result = proc.apply(transactions)
    """

    def __init__(self):
        self._periods: list[QPeriod] = []

    # ─────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────

    def build(self, q_periods: list[dict]) -> None:
        """
        Preprocess q periods — parse epochs, sort by start.

        Args:
            q_periods: List of dicts with 'start', 'end', 'fixed'

        Time: O(q log q)
        """
        self._periods = []

        for idx, p in enumerate(q_periods):
            self._periods.append(QPeriod(
                start=to_epoch(p["start"]),
                end=to_epoch(p["end"]),
                fixed=Decimal(str(p["fixed"])),
                original_index=idx,
            ))

        # Sort by start ascending for sweep
        self._periods.sort(key=lambda p: p.start)

    # ─────────────────────────────────────────────────────────
    # Apply
    # ─────────────────────────────────────────────────────────

    def apply(self, transactions: list[dict]) -> list[dict]:
        """
        Apply q period rules to all transactions.

        Transactions must have 'timestamp_unix' and 'remanent' fields.
        Returns transactions with updated 'remanent' values.

        Args:
            transactions: List of transaction dicts, each with:
                          'timestamp_unix' (int),
                          'remanent' (Decimal)

        Returns:
            New list of dicts with remanent possibly replaced

        Time: O((n + q) log q)
        """
        if not self._periods or not transactions:
            return transactions

        # Sort transactions by timestamp — sweep requires this
        # Preserve original index for output ordering
        indexed = sorted(
            enumerate(transactions),
            key=lambda t: t[1]["timestamp_unix"]
        )

        results = list(transactions)   # shallow copy, mutate remanent
        period_ptr = 0
        total_periods = len(self._periods)

        # Max-heap for active q periods
        # Python heapq is min-heap, so negate for max behavior
        # Heap key: (-start, original_index) → latest start, then first in list
        active_heap: list[tuple[int, int, QPeriod]] = []

        for orig_idx, txn in indexed:
            ts = txn["timestamp_unix"]

            # ── Activate all periods whose start <= ts ──────
            while period_ptr < total_periods and \
                  self._periods[period_ptr].start <= ts:
                p = self._periods[period_ptr]
                # Push: key = (-start, original_index) for correct ordering
                heapq.heappush(active_heap, (-p.start, p.original_index, p))
                period_ptr += 1

            # ── Evict expired periods (end < ts) ────────────
            # Pop from heap while top period has ended before ts
            while active_heap and active_heap[0][2].end < ts:
                heapq.heappop(active_heap)

            # ── Apply best active period if any ─────────────
            if active_heap:
                _, _, best_period = active_heap[0]
                # Double-check: best period must actually contain ts
                # (heap may have stale entries from earlier eviction)
                if best_period.start <= ts <= best_period.end:
                    updated = dict(results[orig_idx])
                    updated["remanent"] = best_period.fixed
                    updated["q_period_applied"] = True
                    results[orig_idx] = updated

        return results

    def get_fixed_for(self, timestamp: int) -> Decimal | None:
        """
        Get fixed amount for a single timestamp.
        Convenience method for one-off lookups.

        Uses binary search to find candidates, then filters.
        O(log q + k) where k = matching periods

        Args:
            timestamp: Epoch to query

        Returns:
            Fixed amount or None if no period applies
        """
        import bisect

        if not self._periods:
            return None

        starts = [p.start for p in self._periods]

        # All periods that could contain timestamp:
        # their start must be <= timestamp
        right = bisect.bisect_right(starts, timestamp)

        best: QPeriod | None = None
        for p in self._periods[:right]:
            if p.end >= timestamp:  # period contains timestamp
                if best is None:
                    best = p
                elif p.start > best.start:
                    best = p
                elif p.start == best.start and \
                     p.original_index < best.original_index:
                    best = p

        return best.fixed if best else None