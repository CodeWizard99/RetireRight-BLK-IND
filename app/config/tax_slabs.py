"""
Tax slab configuration.
Fully configurable — change tax rules without touching business logic.
Slabs are inclusive lower bound, exclusive upper bound (except last slab).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class TaxSlab:
    min_income:  Decimal            # Inclusive lower bound
    max_income:  Optional[Decimal]  # Inclusive upper bound; None = unbounded
    rate:        Decimal            # Marginal rate for this slab
    base_income: Decimal            # Income threshold where this slab starts


# Simplified tax slabs as per challenge document
# ₹0 to ₹7,00,000:          0%
# ₹7,00,001 to ₹10,00,000: 10% on amount above ₹7L
# ₹10,00,001 to ₹12,00,000: 15% on amount above ₹10L
# ₹12,00,001 to ₹15,00,000: 20% on amount above ₹12L
# Above ₹15,00,000:          30% on amount above ₹15L

TAX_SLABS: tuple[TaxSlab, ...] = (
    TaxSlab(
        min_income=Decimal("0"),
        max_income=Decimal("700000"),
        rate=Decimal("0.00"),
        base_income=Decimal("0"),
    ),
    TaxSlab(
        min_income=Decimal("700001"),
        max_income=Decimal("1000000"),
        rate=Decimal("0.10"),
        base_income=Decimal("700000"),
    ),
    TaxSlab(
        min_income=Decimal("1000001"),
        max_income=Decimal("1200000"),
        rate=Decimal("0.15"),
        base_income=Decimal("1000000"),
    ),
    TaxSlab(
        min_income=Decimal("1200001"),
        max_income=Decimal("1500000"),
        rate=Decimal("0.20"),
        base_income=Decimal("1200000"),
    ),
    TaxSlab(
        min_income=Decimal("1500001"),
        max_income=None,             # Unbounded — highest slab
        rate=Decimal("0.30"),
        base_income=Decimal("1500000"),
    ),
)