"""
Inflation adjustment utilities.

A_real = A / (1 + inflation)^t

Supports fractional years.
"""

from decimal import Decimal, getcontext

getcontext().prec = 28


def inflation_factor(
    annual_inflation: Decimal,
    years: Decimal,
) -> Decimal:
    """
    Calculate (1 + inflation)^t

    Supports fractional years.
    """

    r = Decimal(str(annual_inflation))
    t = Decimal(str(years))

    return (Decimal("1") + r) ** t


def adjust_for_inflation(
    nominal_value: Decimal,
    annual_inflation: Decimal,
    years: Decimal,
) -> Decimal:
    """
    Adjust nominal value for inflation.
    """
    factor = inflation_factor(annual_inflation, years)
    return nominal_value / factor