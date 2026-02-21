"""
Base pipeline stage contract.

Every stage in the processing pipeline implements this interface.
Enforces:
    - Single responsibility: each stage does exactly one thing
    - Measurability: every stage reports its own execution time
    - Replaceability: swap any stage without touching others
    - Type safety: input/output contracts via PipelineContext

Design pattern: Chain of Responsibility
Each stage receives the full context, mutates what it owns,
passes it forward. Stages are stateless — safe for concurrent use.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Optional


@dataclass
class StageMetrics:
    """Execution metrics for a single pipeline stage."""
    stage_name:   str
    duration_ms:  float
    input_count:  int
    output_count: int
    metadata:     dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineContext:
    """
    Shared context flowing through every pipeline stage.

    Mutable — each stage reads what it needs, writes its results.
    Stages must never delete fields set by earlier stages.

    Lifecycle:
        Created fresh per request.
        Passed sequentially through S1 → S2 → S3 → S4 → S5 → S6.
        Returned to API layer after S6.
    """

    # ── Input fields (set before pipeline starts) ──────────────
    raw_transactions:  list[dict] = field(default_factory=list)
    q_periods:         list[dict] = field(default_factory=list)
    p_periods:         list[dict] = field(default_factory=list)
    k_periods:         list[dict] = field(default_factory=list)
    wage:              Optional[Decimal] = None      # Monthly wage
    age:               Optional[int]     = None
    inflation_rate:    Optional[Decimal] = None
    instrument:        str               = "nps"     # "nps" | "index"

    # ── S1: Parser outputs ─────────────────────────────────────
    parsed_transactions: list[dict] = field(default_factory=list)

    # ── S2: Validator outputs ──────────────────────────────────
    valid_transactions:   list[dict] = field(default_factory=list)
    invalid_transactions: list[dict] = field(default_factory=list)

    # ── S3: Q Processor outputs ────────────────────────────────
    q_processed_transactions: list[dict] = field(default_factory=list)
    q_overrides_applied:      int        = 0

    # ── S4: P Processor outputs ────────────────────────────────
    p_processed_transactions: list[dict] = field(default_factory=list)
    p_extras_applied:         int        = 0

    # ── S5: K Grouper outputs ──────────────────────────────────
    k_results: list[dict] = field(default_factory=list)

    # ── S6: Returns Calculator outputs ─────────────────────────
    returns_results:              list[dict] = field(default_factory=list)
    total_transaction_amount:     Decimal    = Decimal("0")
    total_ceiling:                Decimal    = Decimal("0")

    # ── Cross-stage diagnostics ────────────────────────────────
    stage_metrics: list[StageMetrics] = field(default_factory=list)
    errors:        list[str]          = field(default_factory=list)

    pipeline_duration_ms: float = 0.0

    def record_metric(self, metric: StageMetrics) -> None:
        self.stage_metrics.append(metric)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def annual_income(self) -> Optional[Decimal]:
        """Derived from monthly wage."""
        if self.wage is None:
            return None
        return self.wage * Decimal("12")


class BasePipelineStage(ABC):
    """
    Abstract base for all pipeline stages.

    Subclasses implement process() with their specific logic.
    Base class handles timing automatically.
    """

    @property
    @abstractmethod
    def stage_name(self) -> str:
        """Unique identifier for this stage."""
        ...

    @abstractmethod
    def process(self, ctx: PipelineContext) -> PipelineContext:
        """
        Execute this stage's logic.

        Args:
            ctx: Pipeline context — read inputs, write outputs

        Returns:
            Same context object with this stage's outputs populated
        """
        ...

    def execute(self, ctx: PipelineContext) -> PipelineContext:
        """
        Execute stage with automatic timing.
        Called by orchestrator — do not override.
        """
        input_count = self._count_inputs(ctx)
        start       = time.perf_counter()

        ctx = self.process(ctx)

        duration_ms  = (time.perf_counter() - start) * 1000
        output_count = self._count_outputs(ctx)

        ctx.record_metric(StageMetrics(
            stage_name=self.stage_name,
            duration_ms=round(duration_ms, 3),
            input_count=input_count,
            output_count=output_count,
        ))

        return ctx

    def _count_inputs(self, ctx: PipelineContext) -> int:
        """Override to report meaningful input count."""
        return len(ctx.raw_transactions)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        """Override to report meaningful output count."""
        return len(ctx.valid_transactions)