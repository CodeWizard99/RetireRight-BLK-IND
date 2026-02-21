"""
Inflation adjustment — converts nominal returns to real returns.

Formula: A_real = A / (1 + inflation)^t

Where:
    A_real    = Inflation-adjusted (real) amount
    A         = Nominal amount after compound interest
    inflation = Annual inflation rate (e.g. 0.055 for 5.5%)
    t         = Number of years

Gives the real purchasing power of the corpus in today's money.
Zero external dependencies — pure Python stdlib.

Complexity: O(1) per calculation
"""

from decimal import Decimal, getcontext

getcontext().prec = 28


def adjust_for_inflation(
    nominal_amount: Decimal,
    inflation_rate: Decimal,
    years: int,
) -> Decimal:
    """
    Adjust nominal investment return for inflation.

    A_real = A / (1 + inflation)^t

    Args:
        nominal_amount: Amount after compound interest (nominal)
        inflation_rate: Annual inflation rate as decimal (e.g. 0.055)
        years:          Number of years of inflation exposure

    Returns:
        Real (inflation-adjusted) amount in today's purchasing power

    Examples:
        adjust_for_inflation(Decimal("1219.27"), Decimal("0.055"), 31) → 231.89
        adjust_for_inflation(Decimal("9619.72"), Decimal("0.055"), 31) → 1829.52
    """
    if nominal_amount <= Decimal("0"):
        return Decimal("0")

    if inflation_rate < Decimal("0"):
        raise ValueError(
            f"Inflation rate cannot be negative, got {inflation_rate}"
        )

    factor = inflation_factor(inflation_rate, years)
    return nominal_amount / factor


def inflation_factor(
    inflation_rate: Decimal,
    years: int,
) -> Decimal:
    """
    Calculate the cumulative inflation factor.
    Extracted so callers can reuse it across multiple instruments
    without recomputing.

    factor = (1 + inflation)^t

    Args:
        inflation_rate: Annual inflation rate as decimal
        years:          Number of years

    Returns:
        Cumulative inflation factor
    """
    return (Decimal("1") + inflation_rate) ** Decimal(str(years))