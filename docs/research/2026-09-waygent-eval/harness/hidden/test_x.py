"""Extended hidden tests, added after the blind judge. Each is a defect class the judge raised in at
least one final tree that design.md requires and the plan's public API can reproduce."""
import asyncio
import unittest

from promptops.batch import BatchRun
from promptops.errors import PromptOpsError
from promptops.fake_model import FakeModel
from promptops.session import EditSession
from promptops.store import PromptStore


class X(unittest.TestCase):
    def test_x_edge_recreated_prompt_not_overwritten_by_stale_session(self):
        # design 4: no path may silently overwrite someone else's change (delete + recreate).
        s = PromptStore()
        s.create("p", "old")
        e = EditSession(s, "p")
        e.edit("mine")
        s.delete("p")
        s.create("p", "replacement")
        try:
            e.save()
        except PromptOpsError:
            pass
        self.assertEqual(s.get("p").body, "replacement")

    def test_x_edge_reload_after_recreate_clears_missing(self):
        s = PromptStore()
        s.create("p", "old")
        e = EditSession(s, "p")
        s.delete("p")
        e.reload()
        self.assertTrue(e.missing)
        s.create("p", "back")
        e.reload()
        self.assertFalse(e.missing)

    def test_x_edge_refusal_after_cancel_counts_as_cancelled(self):
        # design 3: after stop, unfinished items are cancelled, whatever the model says later.
        s = PromptStore()
        s.create("a", "REFUSE a")
        holder = {}

        def hook(model, body, style, name):
            holder["r"].cancel()

        r = BatchRun(s, FakeModel(on_call=hook), ["a"], style="w", model_name="m")
        holder["r"] = r
        out = asyncio.run(r.run())
        self.assertEqual(out, {"a": "cancelled"})

    def test_x_edge_busy_released_when_batch_task_cancelled_before_start(self):
        # design 3: however a run ends, the lock is released - including a caller cancelling it at once.
        from promptops.workspace import Workspace

        s = PromptStore()
        s.create("a", "x")
        ws = Workspace(s, FakeModel())

        async def main():
            t = asyncio.ensure_future(ws.run_batch(["a"]))
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass

        asyncio.run(main())
        self.assertFalse(ws.busy)
