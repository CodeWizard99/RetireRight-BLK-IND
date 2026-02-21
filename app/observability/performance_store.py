"""
In-memory performance metrics store.

Used by:
    - Pipeline orchestrator
    - /performance endpoint

Stores last execution snapshot only
(stateless system — no persistence required).
"""

from __future__ import annotations

import os
import psutil
import threading
from dataclasses import dataclass, asdict
from typing import Dict


# ──────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────

@dataclass
class PerformanceSnapshot:
    latency_ms: float
    memory_mb: float
    threads_used: int


# ──────────────────────────────────────────────
# Store (singleton in module scope)
# ──────────────────────────────────────────────

_last_snapshot: PerformanceSnapshot = PerformanceSnapshot(
    latency_ms=0.0,
    memory_mb=0.0,
    threads_used=1,
)


# ──────────────────────────────────────────────
# Writers
# ──────────────────────────────────────────────

def record_pipeline_execution(latency_ms: float) -> None:
    """
    Record performance metrics after a pipeline run.
    Called by orchestrator.
    """

    global _last_snapshot

    process = psutil.Process(os.getpid())

    memory_mb = process.memory_info().rss / (1024 * 1024)
    threads   = threading.active_count()

    _last_snapshot = PerformanceSnapshot(
        latency_ms=round(latency_ms, 3),
        memory_mb=round(memory_mb, 3),
        threads_used=threads,
    )


# ──────────────────────────────────────────────
# Readers
# ──────────────────────────────────────────────

def get_performance_metrics() -> Dict:
    """
    Returns last recorded performance snapshot.
    Used by /performance endpoint.
    """

    return asdict(_last_snapshot)