from decimal import Decimal

DELIVERY_FEE = Decimal("0.00")


def calculate_order_totals(subtotal: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Return the backend-authoritative subtotal, delivery fee, and total."""
    delivery_fee = DELIVERY_FEE
    return subtotal, delivery_fee, subtotal + delivery_fee
