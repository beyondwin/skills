"""Task 10: workspace undo of the last finished batch."""
import asyncio
import unittest

from promptops.fake_model import FakeModel
from promptops.store import PromptStore
from promptops.workspace import Busy, Workspace


def store_with(**bodies):
    s = PromptStore()
    for k, v in bodies.items():
        s.create(k, v)
    return s


class T10(unittest.TestCase):
    def test_t10_basic_nothing_to_undo(self):
        self.assertEqual(Workspace(store_with(a="x"), FakeModel()).undo_last(), {})

    def test_t10_basic_undo_last(self):
        s = store_with(a="x")
        ws = Workspace(s, FakeModel())
        asyncio.run(ws.run_batch(["a"]))
        self.assertEqual(ws.undo_last(), {"a": "restored"})
        self.assertEqual(s.get("a").body, "x")

    def test_t10_edge_busy_during_run(self):
        s = store_with(a="x", b="y")
        ws = Workspace(s, FakeModel(delay=0.05))
        got = {}

        async def main():
            asyncio.run  # noqa: B018
            await ws.run_batch(["a"])
            t = asyncio.ensure_future(ws.run_batch(["b"]))
            await asyncio.sleep(0.01)
            try:
                ws.undo_last()
            except Busy:
                got["busy"] = True
            await t

        asyncio.run(main())
        self.assertTrue(got.get("busy"))
        self.assertEqual(s.get("a").body, "[plain|base] x")

    def test_t10_edge_undo_after_cancelled_run(self):
        s = store_with(**{f"p{i}": "x" for i in range(4)})
        holder = {}

        def hook(model, body, style, name):
            if len(model.calls) == 2:
                holder["ws"].cancel()

        ws = Workspace(s, FakeModel(on_call=hook))
        holder["ws"] = ws
        out = asyncio.run(ws.run_batch(s.list_ids(), limit=1))
        applied = {k for k, v in out.items() if v == "applied"}
        undo = ws.undo_last()
        self.assertEqual(set(undo), applied)
        self.assertTrue(all(s.get(p).body == "x" for p in s.list_ids()))
