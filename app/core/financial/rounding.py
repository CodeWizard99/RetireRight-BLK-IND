"""
Rounding calculations — core of the auto-saving mechanism.

Rules (from challenge spec):
    - Ceiling: next multiple of 100 STRICTLY above expense amount
    - If amount is already a multiple of 100 → ceiling = amount + 100
    - Remanent: ceiling - amount (always in range [1, 100])

All calculations use Decimal — never float for money.
Zero external dependencies — pure Python stdlib.

Complexity: O(1) per transaction
"""

from decimal import Decimal

# Default rounding multiple — overridable per call
_DEFAULT_MULTIPLE = 100


def calculate_ceiling(
    amount: Decimal,
    multiple: int = _DEFAULT_MULTIPLE,
) -> Decimal:
    """
    Calculate the next multiple strictly above the amount.

    Examples:
        250  → 300
        375  → 400
        620  → 700
        480  → 500
        300  → 400   (already multiple → go to NEXT)
        100  → 200
        1519 → 1600

    Args:
        amount:   Transaction amount (must be positive)
        multiple: Rounding multiple (default 100)

    Returns:
        Next multiple strictly above amount

    Raises:
        ValueError: If amount is not positive
    """
    if amount <= Decimal("0"):
        raise ValueError(
            f"Amount must be positive for ceiling calculation, got {amount}"
        )

    _m        = Decimal(str(multiple))
    remainder = amount % _m

    if remainder == Decimal("0"):
        # Exact multiple → go one higher
        return amount + _m
    else:
        # Round up to next multiple
        return (amount // _m + Decimal("1")) * _m


def calculate_remanent(
    amount: Decimal,
    ceiling: Decimal,
) -> Decimal:
    """
    Calculate the remanent (amount to invest).
    remanent = ceiling - amount

    Always positive by construction (ceiling > amount always).

    Args:
        amount:  Original transaction amount
        ceiling: Pre-calculated ceiling value

    Returns:
        Remanent — always in range [1, multiple]
    """
    return ceiling - amount


def parse_and_round(
    amount: Decimal,
    multiple: int = _DEFAULT_MULTIPLE,
) -> tuple[Decimal, Decimal]:
    """
    Calculate both ceiling and remanent in one call.

    Args:
        amount:   Raw transaction amount
        multiple: Rounding multiple (default 100)

    Returns:
        (ceiling, remanent)
    """
    ceiling  = calculate_ceiling(amount, multiple)
    remanent = calculate_remanent(amount, ceiling)
    return ceiling, remanent