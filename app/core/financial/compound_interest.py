"""
Compound interest calculation.

Formula: A = P * (1 + r/n)^(n*t)

Where:
    A = Final amount
    P = Principal (remanent invested)
    r = Annual interest rate
    n = Compounding frequency (1 = annually per challenge spec)
    t = Years to retirement (60 - age, minimum 5 if age >= 60)

All calculations use Decimal for financial precision.
Zero external dependencies — pure Python stdlib.

Complexity: O(1) per calculation
"""

from decimal import Decimal, getcontext

# 28 significant digits — more than sufficient for financial calculations
getcontext().prec = 28

# Defaults from challenge spec — overridable per call
_DEFAULT_RETIREMENT_AGE   = 60
_DEFAULT_MIN_INVEST_YEARS = 5


def calculate_investment_years(
    age: int,
    retirement_age: int = _DEFAULT_RETIREMENT_AGE,
    min_investment_years: int = _DEFAULT_MIN_INVEST_YEARS,
) -> int:
    """
    Calculate number of years until retirement.

    Rules (from challenge spec):
    - t = retirement_age - age   (if age < retirement_age)
    - t = min_investment_years   (if age >= retirement_age)

    Args:
        age:                  Current age of investor
        retirement_age:       Target retirement age (default 60)
        min_investment_years: Minimum years if already retired (default 5)

    Returns:
        Number of years for compound interest calculation

    Examples:
        age=29  → 31  (60 - 29)
        age=60  →  5  (minimum)
        age=65  →  5  (minimum)
    """
    if age >= retirement_age:
        return min_investment_years
    return retirement_age - age


def compound_interest(
    principal: Decimal,
    annual_rate: Decimal,
    years: int,
    compounding_frequency: int = 1,
) -> Decimal:
    """
    Calculate compound interest final value.

    A = P * (1 + r/n)^(n*t)

    Args:
        principal:             Initial investment amount (P)
        annual_rate:           Annual interest rate as decimal (e.g. 0.0711)
        years:                 Investment duration in years (t)
        compounding_frequency: Times compounded per year (n) — 1 for annual

    Returns:
        Final amount after compound interest

    Examples:
        compound_interest(Decimal("145"), Decimal("0.0711"), 31) → 1219.27
        compound_interest(Decimal("145"), Decimal("0.1449"), 31) → 9619.72
    """
    if principal <= Decimal("0"):
        return Decimal("0")

    n   = Decimal(str(compounding_frequency))
    r   = annual_rate
    t   = Decimal(str(years))

    # A = P * (1 + r/n)^(n*t)
    base     = Decimal("1") + (r / n)
    exponent = n * t

    return principal * (base ** exponent)


def calculate_profit(
    final_amount: Decimal,
    principal: Decimal,
) -> Decimal:
    """
    Calculate profit (gain) from investment.

    profit = final_amount - principal

    Args:
        final_amount: Value after compound interest
        principal:    Initial invested amount

    Returns:
        Profit amount (floored at 0 — never negative)
    """
    return max(Decimal("0"), final_amount - principal)