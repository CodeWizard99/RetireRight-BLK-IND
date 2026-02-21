"""
Stage 6 — Returns Calculator.

Responsibility:
    Calculate investment returns for each k period.
    Applies compound interest + inflation adjustment.
    For NPS: also calculates tax benefit.
    For Index: no restrictions, no tax benefit.

Input  (from ctx): k_results       — amounts per k period from Stage 5
                   age             — investor age
                   wage            — monthly wage (for NPS tax calc)
                   inflation_rate  — annual inflation rate
                   instrument      — "nps" | "index"
Output (to ctx):   returns_results — k_results enriched with
                                     profit, taxBenefit, realValue

Formula (per challenge spec):
    A = P * (1 + r/n)^(n*t)
    t = max(60 - age, 5)
    A_real = A / (1 + inflation)^t
    profit = A - P  (nominal)
    taxBenefit = Tax(income) - Tax(income - NPS_Deduction) [NPS only]

Complexity: O(k) — one calculation per k period
"""

from __future__ import annotations

from decimal import Decimal

from app.config.settings import config
from app.core.financial.compound_interest import (
    calculate_investment_years,
    compound_interest,
    calculate_profit,
)
from app.core.financial.inflation import adjust_for_inflation, inflation_factor
from app.core.financial.nps_calculator import calculate_nps_tax_benefit
from app.pipeline.base import BasePipelineStage, PipelineContext

# Default inflation if not provided (5.5% per challenge example)
_DEFAULT_INFLATION = Decimal("0.055")


class ReturnsCalculatorStage(BasePipelineStage):
    """
    Stage 6: Calculate investment returns per k period.

    Branches on instrument type:
        NPS   → 7.11% + tax benefit
        Index → 14.49%, no tax benefit
    """

    @property
    def stage_name(self) -> str:
        return "S6_ReturnsCalculator"

    def process(self, ctx: PipelineContext) -> PipelineContext:
        """
        Calculate returns for all k periods.

        Uses age + wage + inflation from context.
        Falls back to safe defaults if not provided.
        """
        if not ctx.k_results:
            ctx.returns_results = []
            return ctx

        age            = ctx.age or 30
        inflation_rate = ctx.inflation_rate or _DEFAULT_INFLATION
        annual_income  = ctx.annual_income or Decimal("0")
        instrument     = (ctx.instrument or "nps").lower()

        years = calculate_investment_years(age)

        # Pre-compute inflation factor once — reuse across all k periods
        infl_factor = inflation_factor(inflation_rate, years)

        if instrument == "nps":
            rate = config.instrument.nps_annual_rate
            n    = config.instrument.compounding_frequency
            results = self._calc_nps(
                ctx.k_results, rate, n, years, infl_factor, annual_income
            )
        else:
            rate = config.instrument.index_annual_rate
            n    = config.instrument.compounding_frequency
            results = self._calc_index(
                ctx.k_results, rate, n, years, infl_factor
            )

        ctx.returns_results = results
        return ctx

    # ─────────────────────────────────────────────────────────
    # NPS returns
    # ─────────────────────────────────────────────────────────

    def _calc_nps(
        self,
        k_results:     list[dict],
        rate:          Decimal,
        n:             int,
        years:         int,
        infl_factor:   Decimal,
        annual_income: Decimal,
    ) -> list[dict]:
        """
        NPS: compound interest + tax benefit + inflation adjustment.
        """
        results = []

        for period in k_results:
            amount = period["amount"]

            if amount <= Decimal("0"):
                results.append(self._zero_result(period, include_tax=True))
                continue

            nominal    = compound_interest(amount, rate, years, n)
            profit     = calculate_profit(nominal, amount)
            real_value = nominal / infl_factor
            tax_benefit = calculate_nps_tax_benefit(amount, annual_income)

            results.append({
                "start":       period["start"],
                "end":         period["end"],
                "amount":      round(float(amount), 2),
                "profit":      round(float(profit), 2),
                "taxBenefit":  round(float(tax_benefit), 2),
                "realValue":   round(float(real_value), 2),
                "nominalValue": round(float(nominal), 2),
            })

        return results

    # ─────────────────────────────────────────────────────────
    # Index Fund returns
    # ─────────────────────────────────────────────────────────

    def _calc_index(
        self,
        k_results:   list[dict],
        rate:        Decimal,
        n:           int,
        years:       int,
        infl_factor: Decimal,
    ) -> list[dict]:
        """
        Index fund: compound interest + inflation. No tax benefit.
        """
        results = []

        for period in k_results:
            amount = period["amount"]

            if amount <= Decimal("0"):
                results.append(self._zero_result(period, include_tax=False))
                continue

            nominal    = compound_interest(amount, rate, years, n)
            profit     = calculate_profit(nominal, amount)
            real_value = nominal / infl_factor

            results.append({
                "start":       period["start"],
                "end":         period["end"],
                "amount":      round(float(amount), 2),
                "profit":      round(float(profit), 2),
                "taxBenefit":  0.0,     # Always 0 for index fund
                "realValue":   round(float(real_value), 2),
                "nominalValue": round(float(nominal), 2),
            })

        return results

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _zero_result(period: dict, include_tax: bool) -> dict:
        """Return zero-value result for an empty k period."""
        return {
            "start":        period["start"],
            "end":          period["end"],
            "amount":       0.0,
            "profit":       0.0,
            "taxBenefit":   0.0,
            "realValue":    0.0,
            "nominalValue": 0.0,
        }

    def _count_inputs(self, ctx: PipelineContext) -> int:
        return len(ctx.k_results)

    def _count_outputs(self, ctx: PipelineContext) -> int:
        return len(ctx.returns_results)