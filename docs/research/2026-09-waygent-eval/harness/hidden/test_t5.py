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


from promptops.workspace import Busy, Workspace



class T5(unittest.TestCase):
    def test_t5_basic_run_batch_uses_selection(self):
        s = store_with(a="x")
        m = FakeModel()
        ws = Workspace(s, m)
        ws.selected_model, ws.selected_style = "m2", "bold"
        out = run(ws.run_batch(["a"]))
        self.assertEqual(out, {"a": "applied"})
        self.assertEqual(s.get("a").body, "[bold|m2] x")
        self.assertFalse(ws.busy)

    def test_t5_edge_target_pinned(self):
        # v26 high: switching the model mid-run sent the remaining items to the new model.
        s = store_with(**{f"p{i}": "x" for i in range(6)})
        holder = {}

        def hook(model, body, style, name):
            ws = holder["ws"]
            ws.selected_model = "other"
            ws.selected_style = "other"

        m = FakeModel(on_call=hook)
        ws = Workspace(s, m)
        holder["ws"] = ws
        ws.selected_model, ws.selected_style = "m1", "warm"
        run(ws.run_batch(s.list_ids(), limit=1))
        self.assertEqual({(st, n) for _, st, n in m.calls}, {("warm", "m1")})

    def test_t5_edge_busy_rejects_second_run(self):
        s = store_with(a="x", b="y")
        ws = Workspace(s, FakeModel(delay=0.05))
        got = {}

        async def main():
            t = asyncio.ensure_future(ws.run_batch(["a"]))
            await asyncio.sleep(0.01)
            self.assertTrue(ws.busy)
            try:
                await ws.run_batch(["b"])
            except Busy:
                got["busy"] = True
            await t

        run(main())
        self.assertTrue(got.get("busy"))
        self.assertFalse(ws.busy)
        self.assertEqual(s.get("b").body, "y")

    def test_t5_edge_busy_released_after_cancel(self):
        s = store_with(**{f"p{i}": "x" for i in range(4)})
        holder = {}

        def hook(model, body, style, name):
            holder["ws"].cancel()

        ws = Workspace(s, FakeModel(on_call=hook))
        holder["ws"] = ws
        out = run(ws.run_batch(s.list_ids(), limit=1))
        self.assertFalse(ws.busy)
        self.assertIn("cancelled", out.values())
        ws.cancel()  # nothing running: no error

    def test_t5_edge_busy_released_after_crash(self):
        s = store_with(a="x")

        def hook(*a):
            raise RuntimeError("crash")

        ws = Workspace(s, FakeModel(on_call=hook))
        try:
            run(ws.run_batch(["a"]))
        except Exception:
            pass
        self.assertFalse(ws.busy)


class T5Errors(unittest.TestCase):
    def test_t5_edge_busy_is_domain_error(self):
        from promptops.errors import PromptOpsError
        self.assertTrue(issubclass(Busy, PromptOpsError))
