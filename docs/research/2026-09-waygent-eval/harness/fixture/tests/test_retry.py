import asyncio
import unittest

from promptops.retry import retry_async


class RetryTest(unittest.TestCase):
    def test_retries_then_succeeds(self):
        calls = []

        async def fn():
            calls.append(1)
            if len(calls) < 3:
                raise TimeoutError()
            return "ok"

        self.assertEqual(asyncio.run(retry_async(fn, retry_on=(TimeoutError,))), "ok")
        self.assertEqual(len(calls), 3)

    def test_other_errors_propagate(self):
        async def fn():
            raise ValueError()

        with self.assertRaises(ValueError):
            asyncio.run(retry_async(fn, retry_on=(TimeoutError,)))
