"""Price per one million tokens, in USD."""
from decimal import Decimal

PRICES = {
    "sol": (Decimal("2.00"), Decimal("8.00")),
    "nova": (Decimal("0.50"), Decimal("1.50")),
}
MILLION = Decimal(1_000_000)


def cost(model, input_tokens, output_tokens):
    """Unrounded cost of one call."""
    price_in, price_out = PRICES[model]
    return (price_in * input_tokens + price_out * output_tokens) / MILLION
