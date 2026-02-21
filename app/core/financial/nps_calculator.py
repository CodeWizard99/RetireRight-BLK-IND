"""
NPS (National Pension Scheme) specific calculations.

Rules per challenge spec:
1. NPS_Deduction = min(invested, 10% of annual_income, ₹2,00,000)
2. Tax_Benefit   = Tax(income) - Tax(income - NPS_Deduction)
3. Tax benefit returned separately — does NOT compound
4. Salary treated as pre-tax

Zero external dependencies — only imports from within core.financial.
Complexity: O(s) where s = tax slabs — effectively O(1)
"""

from decimal import Decimal

from app.core.financial.tax_calculator import calculate_tax

# NPS limits per challenge spec
# Duplicated here intentionally — keeps this module self-contained
# Config values in settings.py are for runtime override at API layer
_NPS_MAX_DEDUCTION  = Decimal("200000")   # ₹2,00,000 absolute cap
_NPS_INCOME_PCT_CAP = Decimal("0.10")     # 10% of annual income cap


def calculate_nps_deduction(
    invested_amount: Decimal,
    annual_income: Decimal,
    max_deduction: Decimal = _NPS_MAX_DEDUCTION,
    income_pct_cap: Decimal = _NPS_INCOME_PCT_CAP,
) -> Decimal:
    """
    Calculate eligible NPS deduction under 80CCD(1B).

    NPS_Deduction = min(invested, 10% of annual_income, ₹2,00,000)

    Args:
        invested_amount: Amount actually invested in NPS
        annual_income:   Annual income (monthly_wage * 12)
        max_deduction:   Absolute cap (default ₹2,00,000)
        income_pct_cap:  Income % cap (default 10%)

    Returns:
        Eligible NPS deduction amount

    Examples:
        invested=145, income=600000 → min(145, 60000, 200000) = 145
        invested=300000, income=1500000 → min(300000, 150000, 200000) = 150000
        invested=300000, income=5000000 → min(300000, 500000, 200000) = 200000
    """
    income_cap = annual_income * income_pct_cap
    return min(invested_amount, income_cap, max_deduction)


def calculate_nps_tax_benefit(
    invested_amount: Decimal,
    annual_income: Decimal,
    max_deduction: Decimal = _NPS_MAX_DEDUCTION,
    income_pct_cap: Decimal = _NPS_INCOME_PCT_CAP,
) -> Decimal:
    """
    Calculate tax benefit from NPS investment.

    Tax_Benefit = Tax(income) - Tax(income - NPS_Deduction)

    The benefit is the tax SAVED by claiming the NPS deduction.
    If income is in 0% slab entirely → benefit = 0.
    Tax benefit does NOT compound.

    Args:
        invested_amount: Amount invested in NPS for the period
        annual_income:   Annual income (pre-tax)
        max_deduction:   Absolute cap (default ₹2,00,000)
        income_pct_cap:  Income % cap (default 10%)

    Returns:
        Tax benefit amount (always >= 0)
    """
    deduction = calculate_nps_deduction(
        invested_amount, annual_income, max_deduction, income_pct_cap
    )

    if deduction <= Decimal("0"):
        return Decimal("0")

    tax_before = calculate_tax(annual_income)
    tax_after  = calculate_tax(annual_income - deduction)

    return max(Decimal("0"), tax_before - tax_after)


def calculate_nps_returns(
    invested_amount: Decimal,
    annual_income: Decimal,
    years: int,
    inflation_rate: Decimal,
    nps_annual_rate: Decimal = Decimal("0.0711"),
    compounding_frequency: int = 1,
) -> dict:
    """
    Full NPS return calculation for a k period.

    Combines: compound growth + tax benefit + inflation adjustment.
    Tax benefit does NOT compound (per challenge spec).

    Args:
        invested_amount:       Total remanent invested via NPS
        annual_income:         Annual income (monthly_wage * 12)
        years:                 Years to retirement
        inflation_rate:        Annual inflation rate (e.g. Decimal("0.055"))
        nps_annual_rate:       NPS rate (default 7.11%)
        compounding_frequency: n in compound formula (default 1 = annual)

    Returns:
        Dict with keys:
            nominal_value  — final value before inflation adjustment
            real_value     — inflation-adjusted real value
            profit         — nominal_value - invested_amount
            tax_benefit    — tax saved (does not compound)
    """
    from app.core.financial.compound_interest import compound_interest
    from app.core.financial.inflation import adjust_for_inflation

    nominal    = compound_interest(
        invested_amount, nps_annual_rate, years, compounding_frequency
    )
    real_value = adjust_for_inflation(nominal, inflation_rate, years)
    profit     = max(Decimal("0"), nominal - invested_amount)
    tax_benefit = calculate_nps_tax_benefit(invested_amount, annual_income)

    return {
        "nominal_value": nominal,
        "real_value":    real_value,
        "profit":        profit,
        "tax_benefit":   tax_benefit,
    }