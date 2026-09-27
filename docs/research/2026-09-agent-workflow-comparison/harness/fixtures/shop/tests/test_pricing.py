import unittest

from shop.pricing import Coupon, apply_coupon, order_total, shipping_fee


class PricingTest(unittest.TestCase):
    def test_no_coupon(self):
        self.assertEqual(apply_coupon(10_000, None), 10_000)

    def test_percent_coupon(self):
        self.assertEqual(apply_coupon(20_000, Coupon("P10", "percent", 10)), 18_000)

    def test_fixed_coupon(self):
        self.assertEqual(apply_coupon(20_000, Coupon("F3000", "fixed", 3_000)), 17_000)

    def test_shipping_under_threshold(self):
        self.assertEqual(shipping_fee(30_000), 3_000)

    def test_order_total(self):
        self.assertEqual(order_total(60_000, Coupon("P10", "percent", 10)), 54_000)


if __name__ == "__main__":
    unittest.main()
