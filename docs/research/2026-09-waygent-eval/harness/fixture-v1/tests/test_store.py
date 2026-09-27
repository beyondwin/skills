import unittest

from promptops.store import PromptMissing, PromptStore


class StoreTest(unittest.TestCase):
    def test_create_get(self):
        s = PromptStore()
        s.create("a", "hello")
        self.assertEqual(s.get("a").body, "hello")

    def test_missing(self):
        with self.assertRaises(PromptMissing):
            PromptStore().get("nope")

    def test_list_ids_sorted(self):
        s = PromptStore()
        s.create("b", "1")
        s.create("a", "2")
        self.assertEqual(s.list_ids(), ["a", "b"])
