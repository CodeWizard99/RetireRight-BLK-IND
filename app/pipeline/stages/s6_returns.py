"""
Stage 6 — Returns Calculator (Spec Corrected)

Calculates returns per K period using:

    A = P * (1 + r/n)^(n*t)

Where:
    P = remanent sum in that k period
    r = annual rate (NPS or Index)
    n = compounding frequency
    t = duration of that k period (in years)

Profit:
    profit = A - P

Inflation:
    realValue = A / (1 + inflation)^t

Tax:
    Only for NPS
"""

from __future__ import annotations

from decimal import Decimal
from app.config.settings import config
from app.core.financial.compound_interest import (
    compound_interest,
    calculate_profit,
)
from app.core.financial.inflation import inflation_factor
from app.core.financial.nps_calculator import calculate_nps_tax_benefit
from app.core.period.period_utils import to_epoch
from app.pipeline.base import BasePipelineStage, PipelineContext

SECONDS_PER_YEAR = Decimal("31536000")  # 365 * 24 * 60 * 60
_DEFAULT_INFLATION = Decimal("0.055")


class ReturnsCalculatorStage(BasePipelineStage):

    @property
    def stage_name(self) -> str:
        return "S6_ReturnsCalculator"

    def process(self, ctx: PipelineContext) -> PipelineContext:

        if not ctx.k_results:
            ctx.returns_results = []
            return ctx

        instrument = (ctx.instrument or "nps").lower()
        inflation_rate = ctx.inflation_rate or _DEFAULT_INFLATION
        annual_income = ctx.annual_income or Decimal("0")

        if instrument == "nps":
            rate = config.instrument.nps_annual_rate
        else:
            rate = config.instrument.index_annual_rate

        n = config.instrument.compounding_frequency

        results = []

        for period in ctx.k_results:

            principal = Decimal(str(period["amount"]))

            if principal <= 0:
                results.append(self._zero_result(period))
                continue

            # ─────────────────────────────────────────
            # Calculate duration of this k period
            # ─────────────────────────────────────────
            start_epoch = Decimal(str(to_epoch(period["start"])))
            end_epoch   = Decimal(str(to_epoch(period["end"])))

            duration_seconds = max(end_epoch - start_epoch, Decimal("0"))
            years = duration_seconds / SECONDS_PER_YEAR

            # Clamp runaway durations
            if years > Decimal("50"):
                years = Decimal("50")

            nominal = compound_interest(
                principal,
                rate,
                years,
                n,
            )

            # Safety fallback
            if nominal.is_infinite() or nominal.is_nan():
                nominal = principal

            profit = calculate_profit(nominal, principal)

            infl_factor = inflation_factor(inflation_rate, years)

            if infl_factor <= 0:
                infl_factor = Decimal("1")

            real_value = nominal / infl_factor

            tax_benefit = Decimal("0")
            if instrument == "nps":
                tax_benefit = calculate_nps_tax_benefit(
                    principal,
                    annual_income,
                )

            results.append({
                "start": period["start"],
                "end": period["end"],
                "amount": round(float(principal), 2),
                "profit": round(float(profit), 2),
                "taxBenefit": round(float(tax_benefit), 2),
                "realValue": round(float(real_value), 2),
            })

        ctx.returns_results = results
        return ctx

    @staticmethod
    def _zero_result(period: dict) -> dict:
        return {
            "start": period["start"],
            "end": period["end"],
            "amount": 0.0,
            "profit": 0.0,
            "taxBenefit": 0.0,
            "realValue": 0.0,
        }

    def _count_inputs(self, ctx: PipelineContext) -> int:
        return len(ctx.k_results)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        return len(ctx.returns_results)