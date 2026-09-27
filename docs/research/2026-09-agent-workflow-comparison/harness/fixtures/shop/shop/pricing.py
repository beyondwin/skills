"""주문 금액 계산."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

MAX_DISCOUNT_RATE = 0.5  # 할인 상한
FREE_SHIPPING_THRESHOLD = 50_000
SHIPPING_FEE = 3_000


@dataclass(frozen=True)
class Coupon:
    code: str
    kind: str  # "percent" | "fixed"
    value: int  # percent: 1~100, fixed: 원


def apply_coupon(total: int, coupon: Optional[Coupon]) -> int:
    """쿠폰을 적용한 상품 금액을 돌려준다."""
    if coupon is None:
        return total
    if coupon.kind == "percent":
        discount = total * coupon.value // 100
    elif coupon.kind == "fixed":
        discount = coupon.value
    else:
        raise ValueError(f"unknown coupon kind: {coupon.kind}")
    discount = min(discount, int(total * MAX_DISCOUNT_RATE))
    return max(total - discount, 0)


def shipping_fee(subtotal: int) -> int:
    return 0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FEE


def order_total(subtotal: int, coupon: Optional[Coupon] = None) -> int:
    """상품 금액(subtotal)에 쿠폰과 배송비를 반영한 결제 금액."""
    return apply_coupon(subtotal, coupon) + shipping_fee(subtotal)
