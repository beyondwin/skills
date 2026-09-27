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


class T3(unittest.TestCase):
    def test_t3_basic_applied(self):
        s = store_with(a="x", b="y")
        r = batch(s, FakeModel(), ["a", "b"])
        out = run(r.run())
        self.assertEqual(out, {"a": "applied", "b": "applied"})
        self.assertEqual(s.get("a").body, "[warm|m1] x")
        self.assertEqual(s.get("a").version, 2)
        self.assertEqual(r.state, "done")

    def test_t3_basic_mixed_outcomes_and_counts(self):
        s = store_with(a="x", b="REFUSE", c="BOOM", d="z")
        r = batch(s, FakeModel(), ["a", "b", "c", "d"])
        out = run(r.run())
        self.assertEqual(out, {"a": "applied", "b": "rejected", "c": "failed:error", "d": "applied"})
        self.assertEqual(r.counts, {"applied": 2, "rejected": 1, "failed": 1, "cancelled": 0, "total": 4})
        self.assertEqual(s.get("b").body, "REFUSE")
        self.assertEqual(s.get("b").version, 1)

    def test_t3_basic_limit(self):
        s = store_with(**{f"p{i}": "x" for i in range(8)})
        m = FakeModel()
        run(batch(s, m, s.list_ids(), limit=2).run())
        self.assertLessEqual(m.peak, 2)
        self.assertEqual(len(m.calls), 8)

    def test_t3_edge_conflict_preserves_remote_edit(self):
        s = store_with(a="x", b="y")

        def hook(model, body, style, name):
            if body == "x":
                s.save("a", "someone else", 1)

        r = batch(s, FakeModel(on_call=hook), ["a", "b"])
        out = run(r.run())
        self.assertEqual(out["a"], "failed:conflict")
        self.assertEqual(s.get("a").body, "someone else")
        self.assertEqual(out["b"], "applied")

    def test_t3_edge_missing_mid_run(self):
        s = store_with(a="x", b="y")

        def hook(model, body, style, name):
            if body == "x":
                s.delete("a")

        out = run(batch(s, FakeModel(on_call=hook), ["a", "b"]).run())
        self.assertEqual(out, {"a": "failed:missing", "b": "applied"})

    def test_t3_edge_missing_before_run(self):
        s = store_with(b="y")
        out = run(batch(s, FakeModel(), ["gone", "b"]).run())
        self.assertEqual(out, {"gone": "failed:missing", "b": "applied"})

    def test_t3_edge_counts_only_finished_during_run(self):
        s = store_with(**{f"p{i}": "x" for i in range(6)})
        seen = []
        holder = {}

        def hook(model, body, style, name):
            r = holder["r"]
            c = r.counts
            seen.append((c["applied"] + c["rejected"] + c["failed"] + c["cancelled"], len(r.outcomes), c["total"]))

        r = batch(s, FakeModel(on_call=hook), s.list_ids(), limit=2)
        holder["r"] = r
        run(r.run())
        self.assertTrue(seen)
        for finished, n_outcomes, total in seen:
            self.assertEqual(finished, n_outcomes)
            self.assertEqual(total, 6)
        c = r.counts
        self.assertEqual(c["applied"] + c["rejected"] + c["failed"] + c["cancelled"], c["total"])

    def test_t3_edge_unexpected_store_error_is_item_failure(self):
        s = store_with(a="x", b="y")
        real = s.save

        def flaky(pid, body, ev, **kw):
            if pid == "a":
                raise RuntimeError("disk full")
            return real(pid, body, ev, **kw)

        s.save = flaky
        r = batch(s, FakeModel(), ["a", "b"])
        out = run(r.run())
        self.assertEqual(out, {"a": "failed:error", "b": "applied"})
        self.assertEqual(r.state, "done")
