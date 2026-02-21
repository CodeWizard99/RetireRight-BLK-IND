"""
Pipeline Orchestrator.

Wires all 6 stages in sequence:
    S1 Parser → S2 Validator → S3 QProcessor →
    S4 PProcessor → S5 KGrouper → S6 ReturnsCalculator

Responsibilities:
    - Build PipelineContext from raw request data
    - Execute each stage in order
    - Measure total + per-stage latency
    - Handle stage failures without crashing entire pipeline
    - Return enriched context to API layer

Design decisions:
    - Stateless orchestrator — new instance per request
    - Each stage is independently skippable (no-op if input missing)
    - Per-stage timing captured automatically via BasePipelineStage.execute()
    - Errors are collected, not raised — partial results returned

Complexity: O((n + q + p) log(n + q + p) + k log n)
            Dominated by period processing at scale.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Optional

from app.pipeline.base import PipelineContext
from app.pipeline.stages.s1_parser import ParserStage
from app.pipeline.stages.s2_validator import ValidatorStage
from app.pipeline.stages.s3_q_processor import QProcessorStage
from app.pipeline.stages.s4_p_processor import PProcessorStage
from app.pipeline.stages.s5_k_grouper import KGrouperStage
from app.pipeline.stages.s6_returns import ReturnsCalculatorStage

from app.observability.performance_store import record_pipeline_execution


class PipelineOrchestrator:
    """
    Executes the full processing pipeline for a request.

    Each call to run() is independent — safe for concurrent use.

    Usage:
        orchestrator = PipelineOrchestrator()
        ctx = orchestrator.run(
            raw_transactions=[...],
            q_periods=[...],
            p_periods=[...],
            k_periods=[...],
            wage=Decimal("50000"),
            age=29,
            inflation_rate=Decimal("0.055"),
            instrument="nps",
        )
        results = ctx.returns_results
    """

    # Stage registry — ordered, all active by default
    # To skip a stage: subclass and override _build_stages()
    _STAGE_CLASSES = [
        ParserStage,
        ValidatorStage,
        QProcessorStage,
        PProcessorStage,
        KGrouperStage,
        ReturnsCalculatorStage,
    ]

    def run(
        self,
        raw_transactions: list[dict],
        q_periods:        list[dict]          = [],
        p_periods:        list[dict]          = [],
        k_periods:        list[dict]          = [],
        wage:             Optional[Decimal]   = None,
        age:              Optional[int]       = None,
        inflation_rate:   Optional[Decimal]   = None,
        instrument:       str                 = "nps",
    ) -> PipelineContext:
        """
        Execute the complete pipeline.

        Args:
            raw_transactions: Raw expense list [{date, amount}, ...]
            q_periods:        Fixed amount override periods
            p_periods:        Additive extra periods
            k_periods:        Evaluation grouping periods
            wage:             Monthly wage in INR
            age:              Investor current age
            inflation_rate:   Annual inflation rate (e.g. Decimal("0.055"))
            instrument:       "nps" or "index"

        Returns:
            Populated PipelineContext with all stage outputs
        """
        ctx = self._build_context(
            raw_transactions=raw_transactions,
            q_periods=q_periods or [],
            p_periods=p_periods or [],
            k_periods=k_periods or [],
            wage=wage,
            age=age,
            inflation_rate=inflation_rate,
            instrument=instrument,
        )

        stages = self._build_stages()
        pipeline_start = time.perf_counter()

        for stage in stages:
            try:
                ctx = stage.execute(ctx)
            except Exception as e:
                # Stage failure — log error, continue with partial results
                ctx.add_error(f"{stage.stage_name} failed: {str(e)}")
                # Re-raise in development for fast feedback
                from app.config.settings import config
                if config.is_development:
                    raise

        ctx.pipeline_duration_ms = round(
            (time.perf_counter() - pipeline_start) * 1000, 3
        )

        record_pipeline_execution(ctx.pipeline_duration_ms)

        return ctx

    def run_parse_only(
        self,
        raw_transactions: list[dict],
    ) -> PipelineContext:
        """
        Run S1 only — for the /transactions:parse endpoint.
        """
        ctx = self._build_context(raw_transactions=raw_transactions)
        pipeline_start = time.perf_counter()
        ctx = ParserStage().execute(ctx)
        ctx.pipeline_duration_ms = round(
            (time.perf_counter() - pipeline_start) * 1000,
            3,
        )
        record_pipeline_execution(ctx.pipeline_duration_ms)
        return ctx

    def run_validate_only(
        self,
        parsed_transactions: list[dict],
        wage: Optional[Decimal] = None,
    ) -> PipelineContext:

        # Build empty context first
        ctx = self._build_context(
            raw_transactions=[],   # Not used here
            wage=wage,
        )

        # Inject parsed transactions directly
        ctx.parsed_transactions = parsed_transactions

        pipeline_start = time.perf_counter()

        # Run ONLY validator
        ctx = ValidatorStage().execute(ctx)

        ctx.pipeline_duration_ms = round(
            (time.perf_counter() - pipeline_start) * 1000,
            3,
        )

        record_pipeline_execution(ctx.pipeline_duration_ms)

        return ctx

    def run_filter_only(
        self,
        raw_transactions: list[dict],
        q_periods: list[dict],
        p_periods: list[dict],
        k_periods: list[dict],
        wage: Optional[Decimal] = None,
    ) -> PipelineContext:

        ctx = self._build_context(
            raw_transactions=raw_transactions,
            q_periods=q_periods,
            p_periods=p_periods,
            k_periods=k_periods,
            wage=wage,
        )

        pipeline_start = time.perf_counter()

        # 🔥 FULL chain for filter endpoint
        ctx = ParserStage().execute(ctx)
        ctx = ValidatorStage().execute(ctx)
        ctx = QProcessorStage().execute(ctx)
        ctx = PProcessorStage().execute(ctx)
        ctx = KGrouperStage().execute(ctx)

        ctx.pipeline_duration_ms = round(
            (time.perf_counter() - pipeline_start) * 1000,
            3,
        )

        record_pipeline_execution(ctx.pipeline_duration_ms)

        return ctx
    # ─────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _build_context(
        raw_transactions: list[dict]          = [],
        q_periods:        list[dict]          = [],
        p_periods:        list[dict]          = [],
        k_periods:        list[dict]          = [],
        wage:             Optional[Decimal]   = None,
        age:              Optional[int]       = None,
        inflation_rate:   Optional[Decimal]   = None,
        instrument:       str                 = "nps",
    ) -> PipelineContext:
        """Build a fresh PipelineContext from request parameters."""
        ctx = PipelineContext(
            raw_transactions=raw_transactions or [],
            q_periods=q_periods or [],
            p_periods=p_periods or [],
            k_periods=k_periods or [],
            wage=wage,
            age=age,
            inflation_rate=inflation_rate,
            instrument=instrument,
        )
        # Placeholder for total duration (set after pipeline completes)
        ctx.pipeline_duration_ms = 0.0
        return ctx

    @classmethod
    def _build_stages(cls) -> list:
        """Instantiate all pipeline stages."""
        return [stage_cls() for stage_cls in cls._STAGE_CLASSES]