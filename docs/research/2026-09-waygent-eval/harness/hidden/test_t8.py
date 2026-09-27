"""Task 8: batch.progress per finished item, exactly one batch.finished however the run ends."""
import asyncio
import unittest

from promptops.batch import BatchRun
from promptops.fake_model import FakeModel
from promptops.store import PromptStore

KEYS = ("applied", "rejected", "failed", "cancelled")


def store_with(**bodies):
    s = PromptStore()
    for k, v in bodies.items():
        s.create(k, v)
    return s


class T8(unittest.TestCase):
    def test_t8_basic_progress_and_finished(self):
        s = store_with(a="x", b="REFUSE", c="y", d="z")
        asyncio.run(BatchRun(s, FakeModel(), ["a", "b", "c", "d"], style="w", model_name="m", limit=2).run())
        prog = s.events.of("batch.progress")
        self.assertEqual(len(prog), 4)
        sums = [sum(p[k] for k in KEYS) for p in prog]
        self.assertEqual(sums, sorted(sums))
        self.assertEqual(sums[-1], 4)
        self.assertTrue(all(p["total"] == 4 for p in prog))
        fin = s.events.of("batch.finished")
        self.assertEqual(len(fin), 1)
        self.assertEqual(fin[0]["state"], "done")
        self.assertEqual((fin[0]["applied"], fin[0]["rejected"], fin[0]["total"]), (3, 1, 4))

    def test_t8_edge_finished_once_when_cancelled(self):
        s = store_with(**{f"p{i}": "x" for i in range(5)})
        holder = {}

        def hook(model, body, style, name):
            if len(model.calls) == 2:
                holder["r"].cancel()

        r = BatchRun(s, FakeModel(on_call=hook), s.list_ids(), style="w", model_name="m", limit=1)
        holder["r"] = r
        asyncio.run(r.run())
        fin = s.events.of("batch.finished")
        self.assertEqual(len(fin), 1)
        self.assertEqual(fin[0]["state"], "cancelled")
        self.assertEqual(sum(fin[0][k] for k in KEYS), 5)

    def test_t8_edge_finished_once_when_cancelled_before_start(self):
        s = store_with(a="x")
        r = BatchRun(s, FakeModel(), ["a"], style="w", model_name="m")
        r.cancel()
        asyncio.run(r.run())
        fin = s.events.of("batch.finished")
        self.assertEqual(len(fin), 1)
        self.assertEqual(fin[0]["state"], "cancelled")

    def test_t8_edge_finished_once_on_crash(self):
        s = store_with(a="x", b="y")

        def hook(*a):
            raise RuntimeError("client crashed")

        r = BatchRun(s, FakeModel(on_call=hook), ["a", "b"], style="w", model_name="m")
        try:
            asyncio.run(r.run())
        except Exception:
            pass
        self.assertEqual(len(s.events.of("batch.finished")), 1)

    def test_t8_edge_failed_item_emits_no_save_event(self):
        s = store_with(a="x")

        def hook(model, body, style, name):
            s.save("a", "someone", 1)

        asyncio.run(BatchRun(s, FakeModel(on_call=hook), ["a"], style="w", model_name="m").run())
        self.assertEqual(s.events.of("prompt.saved"), [{"id": "a", "version": 2}])
