"""
K Period Grouper — Prefix sum + binary search.

Problem:
    Up to 1M k periods, up to 1M transactions.
    For each k period, sum remanents of ALL transactions
    whose timestamp falls within [period.start, period.end].

    A transaction can belong to multiple k periods.
    Each k period is calculated independently.

Algorithm:
    1. Sort transactions by timestamp          O(n log n)
    2. Build prefix sum on sorted remanents    O(n)
    3. For each k period:
       - Binary search left boundary           O(log n)
       - Binary search right boundary          O(log n)
       - prefix[right] - prefix[left]          O(1)

Total: O(n log n + k log n)
vs Naive: O(n * k) = 10^12 at max scale

Memory: O(n) for sorted arrays + prefix sums
        No per-period memory — all share same arrays

Python's bisect module is implemented in C —
extremely fast for sorted list binary search.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from decimal import Decimal

from app.core.period.period_utils import to_epoch


@dataclass(slots=True)
class KPeriodResult:
    """Aggregated result for a single k period."""
    start:             str      # Original input string
    end:               str      # Original input string
    start_epoch:       int
    end_epoch:         int
    amount:            Decimal  # Sum of remanents in period
    transaction_count: int      # Number of transactions in period


class KPeriodGrouper:
    """
    Prefix-sum grouper for k period aggregation.

    Build once, query many times.
    All k periods share the same sorted transaction array.

    Usage:
        grouper = KPeriodGrouper()
        grouper.build(transactions)       # O(n log n)
        results = grouper.compute_all(k_periods)  # O(k log n)
    """

    __slots__ = (
        "_timestamps",
        "_prefix_amounts",
        "_prefix_counts",
    )

    def __init__(self):
        self._timestamps:     list[int]     = []
        self._prefix_amounts: list[Decimal] = [Decimal("0")]
        self._prefix_counts:  list[int]     = [0]

    # ─────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────

    def build(self, transactions: list[dict]) -> None:
        """
        Sort transactions and build prefix sum arrays.

        Args:
            transactions: List of dicts with:
                          'timestamp_unix' (int)
                          'remanent'       (Decimal)

        Time:  O(n log n) — dominated by sort
        Space: O(n)
        """
        if not transactions:
            self._timestamps     = []
            self._prefix_amounts = [Decimal("0")]
            self._prefix_counts  = [0]
            return

        # Sort by timestamp ascending
        sorted_txns = sorted(
            transactions,
            key=lambda t: t["timestamp_unix"]
        )

        self._timestamps = [t["timestamp_unix"] for t in sorted_txns]

        # Build prefix sums
        # prefix_amounts[i] = sum of remanents for sorted_txns[0 .. i-1]
        # prefix_counts[i]  = count of txns in sorted_txns[0 .. i-1]
        self._prefix_amounts = [Decimal("0")]
        self._prefix_counts  = [0]

        running_amount = Decimal("0")
        running_count  = 0

        for txn in sorted_txns:
            running_amount += txn["remanent"]
            running_count  += 1
            self._prefix_amounts.append(running_amount)
            self._prefix_counts.append(running_count)

    # ─────────────────────────────────────────────────────────
    # Query
    # ─────────────────────────────────────────────────────────

    def query(
        self,
        start_epoch: int,
        end_epoch: int,
    ) -> tuple[Decimal, int]:
        """
        Sum remanents for transactions in [start_epoch, end_epoch].

        Uses Python's C-optimised bisect for boundary search.

        Args:
            start_epoch: Period start (inclusive)
            end_epoch:   Period end   (inclusive)

        Returns:
            (total_remanent, transaction_count)

        Time: O(log n)
        """
        # bisect_left:  find first index where timestamps[i] >= start_epoch
        # bisect_right: find first index where timestamps[i] >  end_epoch
        left  = bisect.bisect_left(self._timestamps, start_epoch)
        right = bisect.bisect_right(self._timestamps, end_epoch)

        amount = self._prefix_amounts[right] - self._prefix_amounts[left]
        count  = self._prefix_counts[right]  - self._prefix_counts[left]

        return amount, count

    # ─────────────────────────────────────────────────────────
    # Batch
    # ─────────────────────────────────────────────────────────

    def compute_all(
        self,
        k_periods: list[dict],
    ) -> list[KPeriodResult]:
        """
        Compute results for all k periods.

        Preserves input ordering of k_periods in output.

        Args:
            k_periods: List of dicts with 'start', 'end' strings

        Returns:
            List of KPeriodResult, same order as input

        Time: O(k log n)
        """
        results: list[KPeriodResult] = []

        for period in k_periods:
            start_str   = period["start"]
            end_str     = period["end"]
            start_epoch = to_epoch(start_str)
            end_epoch   = to_epoch(end_str)

            amount, count = self.query(start_epoch, end_epoch)

            results.append(KPeriodResult(
                start=start_str,
                end=end_str,
                start_epoch=start_epoch,
                end_epoch=end_epoch,
                amount=amount,
                transaction_count=count,
            ))

        return results