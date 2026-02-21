"""
P Period Processor — Event sweep line approach.

Problem:
    Up to 1M p periods, up to 1M transactions.
    For each transaction, sum the 'extra' from ALL
    p periods that contain the transaction timestamp.
    (ALL matching periods contribute — additive rule)

Algorithm — Event Sweep Line:
    Convert each p period into 2 events:
        START at period.start:   +extra (activate)
        END   at period.end + 1: -extra (deactivate)

    Merge events + transaction timestamps into single sorted list.
    Single left-to-right sweep maintains running total.
    At each transaction, running total = sum of active extras.

    This is O((n + p) log(n + p)) vs O(n * p) naive.

Key insight:
    P periods are PURELY ADDITIVE.
    No selection logic needed — all matching periods contribute.
    The sweep line handles overlapping periods automatically.

Ordering at same timestamp:
    START events before TRANSACTION events before END events
    Ensures inclusive range boundaries work correctly.
    (if txn is exactly at period.start → period IS active)
"""

from __future__ import annotations

from decimal import Decimal
from enum import IntEnum

from app.core.period.period_utils import to_epoch


class _EvtType(IntEnum):
    """
    Sort order at same timestamp:
    START(0) → TRANSACTION(1) → END(2)
    Ensures period is active at its start timestamp.
    """
    START       = 0
    TRANSACTION = 1
    END         = 2


class PProcessor:
    """
    Processes p period rules using event sweep line.

    P Rule:
        - ALL matching p periods add their extra to remanent
        - Applied AFTER q rules (adds on top of whatever remanent is)
        - Negative remanent clamped to 0

    Usage:
        proc = PProcessor()
        proc.build(p_periods)
        result = proc.apply(transactions)
    """

    def __init__(self):
        # List of (timestamp, event_type, delta)
        self._events: list[tuple[int, int, Decimal]] = []

    # ─────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────

    def build(self, p_periods: list[dict]) -> None:
        """
        Convert p periods into sweep line events.

        Args:
            p_periods: List of dicts with 'start', 'end', 'extra'

        Time: O(p) — two events per period
        """
        self._events = []

        for period in p_periods:
            start_ep = to_epoch(period["start"])
            end_ep   = to_epoch(period["end"])
            extra    = Decimal(str(period["extra"]))

            # Activate at start
            self._events.append((start_ep, _EvtType.START, extra))

            # Deactivate at end + 1 (end is inclusive)
            self._events.append((end_ep + 1, _EvtType.END, -extra))

    # ─────────────────────────────────────────────────────────
    # Apply
    # ─────────────────────────────────────────────────────────

    def apply(self, transactions: list[dict]) -> list[dict]:
        """
        Apply p period rules — add extras to all transaction remanents.

        Args:
            transactions: List of dicts with:
                          'timestamp_unix' (int)
                          'remanent'       (Decimal)

        Returns:
            New list of dicts with remanent increased by p extras

        Time: O((n + p) log(n + p))
        """
        if not self._events or not transactions:
            return transactions

        # Build merged event list: period events + transaction events
        # Transaction events use TRANSACTION priority (1)
        all_events: list[tuple[int, int, int | Decimal, int]] = []
        # (timestamp, event_type, value, txn_index)

        for ts, etype, delta in self._events:
            all_events.append((ts, int(etype), delta, -1))

        for idx, txn in enumerate(transactions):
            all_events.append((
                txn["timestamp_unix"],
                int(_EvtType.TRANSACTION),
                Decimal("0"),
                idx,
            ))

        # Sort: primary=timestamp, secondary=event_type
        # START(0) < TRANSACTION(1) < END(2) at same timestamp
        all_events.sort(key=lambda e: (e[0], e[1]))

        # Single sweep
        running = Decimal("0")
        extras: dict[int, Decimal] = {}

        for ts, etype, value, txn_idx in all_events:
            if etype == _EvtType.START:
                running += value
            elif etype == _EvtType.END:
                running += value   # value is negative here
            else:
                # TRANSACTION — record current running extra
                extras[txn_idx] = max(Decimal("0"), running)

        # Apply extras to transactions
        results = []
        for idx, txn in enumerate(transactions):
            extra = extras.get(idx, Decimal("0"))
            if extra > Decimal("0"):
                updated = dict(txn)
                updated["remanent"] = txn["remanent"] + extra
                updated["p_extra_applied"] = float(extra)
                results.append(updated)
            else:
                results.append(txn)

        return results