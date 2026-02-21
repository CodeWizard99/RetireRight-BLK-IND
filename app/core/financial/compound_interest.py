"""
Compound Interest Engine — Spec Corrected

Formula:
    A = P * (1 + r/n)^(n*t)

Where:
    P = principal
    r = annual interest rate (decimal)
    n = compounding frequency
    t = years (can be fractional)

No retirement logic here.
Pure financial math.
"""

from decimal import Decimal, getcontext

getcontext().prec = 28  # High precision


def compound_interest(
    principal: Decimal,
    annual_rate: Decimal,
    years: Decimal,
    compounding_frequency: int = 1,
) -> Decimal:
    """
    Calculate compound interest final value.

    Supports fractional years.
    """

    if principal <= 0:
        return Decimal("0")

    n = Decimal(str(compounding_frequency))
    r = Decimal(str(annual_rate))
    t = Decimal(str(years))

    base = Decimal("1") + (r / n)
    exponent = n * t

    return principal * (base ** exponent)


def calculate_profit(
    final_amount: Decimal,
    principal: Decimal,
) -> Decimal:
    """
    Profit = final_amount - principal
    Never negative.
    """
    profit = final_amount - principal
    return profit if profit > 0 else Decimal("0")