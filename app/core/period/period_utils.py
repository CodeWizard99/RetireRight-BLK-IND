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
    Parse datetime string to Unix epoch seconds.
    Cached — same string is never parsed twice.

    LRU cache of 131072 covers virtually all real-world
    period + transaction date combinations.

    Args:
        dt_str: "YYYY-MM-DD HH:MM:SS" format string

    Returns:
        Unix timestamp as integer

    Raises:
        ValueError: If format doesn't match
    """
    try:
        dt = datetime.strptime(dt_str.strip(), TIMESTAMP_FORMAT)
        return int(dt.timestamp())
    except ValueError as e:
        raise ValueError(
            f"Invalid timestamp '{dt_str}'. "
            f"Expected '{TIMESTAMP_FORMAT}'. Error: {e}"
        )


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