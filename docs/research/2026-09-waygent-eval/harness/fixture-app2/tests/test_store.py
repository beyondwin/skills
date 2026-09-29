import unittest

from usage.store import CallStore


class StoreTest(unittest.TestCase):
    def test_load_seed(self):
        calls = CallStore.load("data/calls.jsonl").all()
        self.assertEqual(len(calls), 10)
        self.assertEqual(calls[0].id, "c01")
