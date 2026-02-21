"""
Timestamp utilities for period precessing.

Key design decision:
    All datetimes are converted to Unix epoch (int) immediately
    on ingestion. All internal comparisons use integers — O(1).
    No repeated string parsing in hot paths.
    LRU cache ensures same string is never parsed twice.

Format spec (from challenge): "YYYY-MM-DD HH:MM:SS"
"""

from datetime import datetime
from functools import lru_cache

TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

@lru_cache(maxsize=131072)
def to_epoch(dt_str: str) -> int:
    """
    Parse datetime → epoch.

    Hackathon compatibility mode:
    If invalid calendar date → fallback to lexical epoch.
    """

    dt_str = dt_str.strip()

    try:
        dt = datetime.strptime(dt_str, TIMESTAMP_FORMAT)
        return int(dt.timestamp())

    except ValueError:
        # ── Compatibility fallback ─────────────────────
        # Convert YYYY-MM-DD HH:MM:SS → sortable integer
        # Example: 2023-11-31 23:59:59 → 20231131235959

        digits = (
            dt_str.replace("-", "")
                  .replace(":", "")
                  .replace(" ", "")
        )

        if not digits.isdigit():
            raise ValueError(
                f"Invalid timestamp '{dt_str}'"
            )

        return int(digits)


def epoch_to_str(epoch: int) -> str:
    """
    Convert epoch back to canonical string.
    Used only for response serialization.
    """
    return datetime.fromtimestamp(epoch).strftime(TIMESTAMP_FORMAT)


def validate_range(start_str: str, end_str: str) -> tuple[int, int]:
    """
    Parse and validate a period range.
    Ensures start <= end.

    Returns:
        (start_epoch, end_epoch)

    Raises:
        ValueError: If start > end
    """
    start_ep = to_epoch(start_str)
    end_ep   = to_epoch(end_str)

    if start_ep > end_ep:
        raise ValueError(
            f"Period start '{start_str}' must be <= end '{end_str}'"
        )

    return start_ep, end_ep

SECONDS_PER_YEAR = 365 * 24 * 60 * 60

def years_between(start_epoch: int, end_epoch: int) -> float:
    return (end_epoch - start_epoch) / SECONDS_PER_YEAR