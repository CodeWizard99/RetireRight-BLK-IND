"""
Financial calculation modules.

Public API — import from here, not from submodules directly.
All modules are pure Python stdlib + Decimal. Zero external dependencies.
"""

from app.core.financial.rounding import (
    calculate_ceiling,
    calculate_remanent,
    parse_and_round,
)
from app.core.financial.compound_interest import (
    calculate_investment_years,
    compound_interest,
    calculate_profit,
)
from app.core.financial.inflation import (
    adjust_for_inflation,
    inflation_factor,
)
from app.core.financial.tax_calculator import (
    calculate_tax,
    marginal_tax_rate,
    find_tax_slab,
)
from app.core.financial.nps_calculator import (
    calculate_nps_deduction,
    calculate_nps_tax_benefit,
    calculate_nps_returns,
)

__all__ = [
    # Rounding
    "calculate_ceiling",
    "calculate_remanent",
    "parse_and_round",
    # Compound interest
    "compound_interest",
    "calculate_profit",
    "calculate_investment_years",
    # Inflation
    "adjust_for_inflation",
    "inflation_factor",
    # Tax
    "calculate_tax",
    "marginal_tax_rate",
    "find_tax_slab",
    # NPS
    "calculate_nps_deduction",
    "calculate_nps_tax_benefit",
    "calculate_nps_returns",
]