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


from promptops.batch import BatchRun



def batch(s, m, pids, **kw):
    kw.setdefault("style", "warm")
    kw.setdefault("model_name", "m1")
    return BatchRun(s, m, pids, **kw)
class T4(unittest.TestCase):
    def test_t4_basic_cancel_before_start(self):
        s = store_with(a="x", b="y")
        m = FakeModel()
        r = batch(s, m, ["a", "b"])
        r.cancel()
        out = run(r.run())
        self.assertEqual(out, {"a": "cancelled", "b": "cancelled"})
        self.assertEqual(m.calls, [])
        self.assertEqual(r.state, "cancelled")
        self.assertFalse(r.locked)

    def test_t4_edge_cancel_mid_run_no_saves_after(self):
        s = store_with(**{f"p{i}": f"x{i}" for i in range(6)})
        holder = {}
        saves_after_cancel = []
        real = s.save

        def spy(pid, body, ev, **kw):
            if holder.get("cancelled"):
                saves_after_cancel.append(pid)
            return real(pid, body, ev, **kw)

        s.save = spy

        def hook(model, body, style, name):
            if len(model.calls) == 3:
                holder["r"].cancel()
                holder["cancelled"] = True

        m = FakeModel(on_call=hook)
        r = batch(s, m, s.list_ids(), limit=2)
        holder["r"] = r
        out = run(r.run())
        self.assertEqual(saves_after_cancel, [])
        self.assertEqual(r.state, "cancelled")
        self.assertFalse(r.locked)
        self.assertLess(len(m.calls), 6)
        self.assertEqual(len(out), 6)
        self.assertIn("cancelled", out.values())
        c = r.counts
        self.assertEqual(c["applied"] + c["rejected"] + c["failed"] + c["cancelled"], 6)

    def test_t4_edge_locked_only_while_running(self):
        s = store_with(a="x")
        states = []
        holder = {}
        m = FakeModel(on_call=lambda *a: states.append(holder["r"].locked))
        r = batch(s, m, ["a"])
        holder["r"] = r
        self.assertFalse(r.locked)
        run(r.run())
        self.assertEqual(states, [True])
        self.assertFalse(r.locked)

    def test_t4_edge_cancel_after_done_is_noop(self):
        s = store_with(a="x")
        r = batch(s, FakeModel(), ["a"])
        run(r.run())
        r.cancel()
        self.assertEqual(r.state, "done")
        self.assertEqual(r.outcomes, {"a": "applied"})

    def test_t4_edge_unlock_after_unexpected_error(self):
        s = store_with(a="x")

        def hook(*a):
            raise RuntimeError("model client crashed")

        r = batch(s, FakeModel(on_call=hook), ["a"])
        try:
            run(r.run())
        except Exception:
            pass
        self.assertFalse(r.locked)
        self.assertNotEqual(r.state, "running")
