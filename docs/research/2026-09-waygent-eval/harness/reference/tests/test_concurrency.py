import asyncio
import unittest

from promptops.concurrency import gather_limited


class GatherLimitedTest(unittest.TestCase):
    def test_limit_and_errors(self):
        active = peak = 0

        async def fn(i):
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.01)
            active -= 1
            if i == 2:
                raise ValueError(i)
            return i * 10

        out = asyncio.run(gather_limited(range(5), fn, 2))
        self.assertLessEqual(peak, 2)
        self.assertEqual(out[0], (0, 0))
        self.assertIsInstance(out[2][1], ValueError)
