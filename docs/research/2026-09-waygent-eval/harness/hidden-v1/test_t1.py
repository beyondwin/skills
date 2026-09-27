"""Hidden acceptance tests. Never copied into the agent's repo.

Each test name starts with the task (t1..t6) and ends with the principle or kind it probes.
"basic" tests follow the plan's explicit sentences; "edge" tests probe behavior the plan
states only as a principle (the class a per-task or final review is supposed to catch).
"""
import asyncio
import unittest

from promptops.fake_model import FakeModel
from promptops.store import PromptMissing, PromptStore, VersionConflict


def run(coro):
    return asyncio.run(coro)


def store_with(**bodies):
    s = PromptStore()
    for k, v in bodies.items():
        s.create(k, v)
    return s




class T1(unittest.TestCase):
    def test_t1_basic_versions(self):
        s = store_with(a="x")
        self.assertEqual(s.get("a").version, 1)
        p = s.save("a", "y", 1)
        self.assertEqual((p.body, p.version), ("y", 2))
        self.assertEqual(s.get("a").version, 2)

    def test_t1_basic_conflict(self):
        s = store_with(a="x")
        s.save("a", "y", 1)
        with self.assertRaises(VersionConflict) as cm:
            s.save("a", "z", 1)
        self.assertEqual(cm.exception.current_version, 2)
        self.assertEqual(s.get("a").body, "y")

    def test_t1_basic_missing(self):
        with self.assertRaises(PromptMissing):
            PromptStore().save("nope", "b", 1)

    def test_t1_basic_put_removed(self):
        self.assertFalse(hasattr(PromptStore(), "put"))

    def test_t1_edge_copies_get(self):
        s = store_with(a="x")
        p = s.get("a")
        p.body = "hacked"
        p.version = 99
        self.assertEqual((s.get("a").body, s.get("a").version), ("x", 1))

    def test_t1_edge_copies_create_save(self):
        s = PromptStore()
        c = s.create("a", "x")
        c.body = "hacked"
        self.assertEqual(s.get("a").body, "x")
        v = s.save("a", "y", 1)
        v.body = "hacked2"
        self.assertEqual(s.get("a").body, "y")
