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


from promptops.candidates import generate_candidates



class T6(unittest.TestCase):
    def test_t6_basic_generate_and_choose(self):
        s = store_with(a="x")
        cs = run(generate_candidates(s, FakeModel(), "a", ["warm", "bold"], model_name="m1"))
        self.assertEqual(cs.candidates, {"warm": "[warm|m1] x", "bold": "[bold|m1] x"})
        self.assertEqual(s.get("a").version, 1)  # nothing saved yet
        p = cs.choose("bold")
        self.assertEqual(p.body, "[bold|m1] x")
        self.assertEqual(s.get("a").version, 2)
        with self.assertRaises(RuntimeError):
            cs.choose("warm")
        self.assertEqual(s.get("a").body, "[bold|m1] x")

    def test_t6_edge_partial_failure_keeps_only_successes(self):
        s = store_with(a="x")

        async def hook(model, body, style, name):
            if style == "bad":
                raise RuntimeError("style exploded")

        cs = run(generate_candidates(s, FakeModel(on_call=hook), "a", ["warm", "bad", "bold"], model_name="m1"))
        self.assertEqual(set(cs.candidates), {"warm", "bold"})
        self.assertEqual(set(cs.errors), {"bad"})
        self.assertFalse(cs.all_failed)
        with self.assertRaises(KeyError):
            cs.choose("bad")
        self.assertEqual(s.get("a").version, 1)
        cs.choose("warm")
        self.assertEqual(s.get("a").body, "[warm|m1] x")

    def test_t6_edge_all_failed(self):
        s = store_with(a="BOOM")
        cs = run(generate_candidates(s, FakeModel(), "a", ["warm", "bold"], model_name="m1"))
        self.assertTrue(cs.all_failed)
        self.assertEqual(cs.candidates, {})
        self.assertEqual(set(cs.errors), {"warm", "bold"})

    def test_t6_edge_choose_after_remote_change(self):
        s = store_with(a="x")
        cs = run(generate_candidates(s, FakeModel(), "a", ["warm"], model_name="m1"))
        s.save("a", "remote", 1)
        with self.assertRaises(VersionConflict):
            cs.choose("warm")
        self.assertEqual(s.get("a").body, "remote")

    def test_t6_basic_limit(self):
        s = store_with(a="x")
        m = FakeModel()
        run(generate_candidates(s, m, "a", [f"s{i}" for i in range(6)], model_name="m1", limit=2))
        self.assertLessEqual(m.peak, 2)
