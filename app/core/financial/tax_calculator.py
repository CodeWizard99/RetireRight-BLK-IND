"""
Tax calculation using configurable slab-based system.

Simplified tax rules per challenge spec:
- ₹0 to ₹7,00,000:           0%
- ₹7,00,001 to ₹10,00,000:  10% on amount above ₹7L
- ₹10,00,001 to ₹12,00,000: 15% on amount above ₹10L
- ₹12,00,001 to ₹15,00,000: 20% on amount above ₹12L
- Above ₹15,00,000:          30% on amount above ₹15L

Assumptions per challenge spec:
1. Salary is pre-tax
2. Standard deduction and 80C/80D not considered
3. Tax benefit returned separately — does not compound

Slabs sourced from config/tax_slabs.py — fully configurable.
Zero business logic in tax_slabs.py, zero config in this file.

Complexity: O(s) where s = number of slabs (5) — effectively O(1)
"""

from decimal import Decimal

from app.config.tax_slabs import TAX_SLABS, TaxSlab


def calculate_tax(annual_income: Decimal) -> Decimal:
    """
    Calculate total income tax using slab-based marginal system.

    Iterates slabs bottom to top. For each slab, calculates tax
    on the portion of income within that slab's range.

    Args:
        annual_income: Annual income before tax (pre-tax salary)

    Returns:
        Total tax payable as Decimal (always >= 0)

    Examples:
        calculate_tax(Decimal("600000"))  → 0        (0% slab)
        calculate_tax(Decimal("800000"))  → 10000    (10% on 1L above 7L)
        calculate_tax(Decimal("1100000")) → 45000    (10%*3L + 15%*1L)
        calculate_tax(Decimal("2000000")) → 270000
    """
    if annual_income <= Decimal("0"):
        return Decimal("0")

    tax = Decimal("0")

    for slab in TAX_SLABS:
        # Income is below this slab entirely — stop
        if annual_income < slab.min_income:
            break

        if slab.max_income is None:
            # Unbounded top slab — tax on all above base_income
            taxable = annual_income - slab.base_income
        elif annual_income <= slab.max_income:
            # Income lands within this slab
            taxable = annual_income - slab.base_income
        else:
            # Income exceeds this slab — tax on full slab width
            taxable = slab.max_income - slab.base_income

        if slab.rate > Decimal("0") and taxable > Decimal("0"):
            tax += taxable * slab.rate

        # Stop iterating once we've reached the slab that contains income
        if slab.max_income is None or annual_income <= slab.max_income:
            break

    return max(Decimal("0"), tax)


def find_tax_slab(annual_income: Decimal) -> TaxSlab:
    """
    Find the marginal tax slab for a given income level.

    Args:
        annual_income: Annual income

    Returns:
        The TaxSlab whose range contains annual_income
    """
    for slab in reversed(TAX_SLABS):
        if annual_income >= slab.min_income:
            return slab

    return TAX_SLABS[0]   # Below all slabs → 0% slab


def marginal_tax_rate(annual_income: Decimal) -> Decimal:
    """
    Get the marginal tax rate for a given income.

    Args:
        annual_income: Annual income

    Returns:
        Marginal rate as decimal (e.g. 0.30 for 30%)
    """
    return find_tax_slab(annual_income).rate