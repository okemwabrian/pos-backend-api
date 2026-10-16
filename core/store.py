from decimal import Decimal, ROUND_HALF_UP


STORE_NAME = "FREE HOUSE BAR & RESTAURANT"
TILL_NUMBER = "5453103"
VAT_RATE = Decimal("16.00")


def calculate_vat(taxable_amount):
    return (taxable_amount * VAT_RATE / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def calculate_included_vat(gross_amount):
    return (gross_amount * VAT_RATE / (Decimal("100") + VAT_RATE)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
