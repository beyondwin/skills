"""Task 9: undo restores only what this run applied, never over a later change."""
import asyncio
import unittest

from promptops.batch import BatchRun
from promptops.fake_model import FakeModel
from promptops.store import PromptStore


def store_with(**bodies):
    s = PromptStore()
    for k, v in bodies.items():
        s.create(k, v)
    return s


def done_run(s, pids, **kw):
    r = BatchRun(s, FakeModel(**kw), pids, style="w", model_name="m")
    asyncio.run(r.run())
    return r


class T9(unittest.TestCase):
    def test_t9_basic_undo_restores(self):
        s = store_with(a="x", b="y")
        r = done_run(s, ["a", "b"])
        self.assertEqual(r.undo(), {"a": "restored", "b": "restored"})
        self.assertEqual((s.get("a").body, s.get("a").version), ("x", 3))

    def test_t9_edge_only_applied_items(self):
        s = store_with(a="x", b="REFUSE", c="BOOM")
        r = done_run(s, ["a", "b", "c"])
        out = r.undo()
        self.assertEqual(set(out), {"a"})
        self.assertEqual((s.get("b").version, s.get("c").version), (1, 1))

    def test_t9_edge_skip_changed_since(self):
        s = store_with(a="x", b="y")
        r = done_run(s, ["a", "b"])
        s.save("a", "later edit", 2)
        out = r.undo()
        self.assertEqual(out, {"a": "skipped:changed", "b": "restored"})
        self.assertEqual(s.get("a").body, "later edit")

    def test_t9_edge_skip_missing(self):
        s = store_with(a="x", b="y")
        r = done_run(s, ["a", "b"])
        s.delete("a")
        self.assertEqual(r.undo(), {"a": "skipped:missing", "b": "restored"})

    def test_t9_edge_undo_emits_save_event(self):
        s = store_with(a="x")
        r = done_run(s, ["a"])
        r.undo()
        self.assertEqual(s.events.of("prompt.saved")[-1], {"id": "a", "version": 3})

    def test_t9_basic_undo_twice_and_before_finish(self):
        s = store_with(a="x")
        fresh = BatchRun(s, FakeModel(), ["a"], style="w", model_name="m")
        with self.assertRaises(RuntimeError):
            fresh.undo()
        r = done_run(s, ["a"])
        r.undo()
        with self.assertRaises(RuntimeError):
            r.undo()
        self.assertEqual(s.get("a").body, "x")
