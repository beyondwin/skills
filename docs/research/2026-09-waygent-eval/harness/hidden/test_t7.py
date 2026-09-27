"""Task 7: transient ModelError is retried (3 calls max) everywhere; refusals never are."""
import asyncio
import unittest

from promptops.batch import BatchRun
from promptops.candidates import generate_candidates
from promptops.fake_model import FakeModel, ModelError
from promptops.store import PromptStore


def store_with(**bodies):
    s = PromptStore()
    for k, v in bodies.items():
        s.create(k, v)
    return s


def flaky(fail_times):
    seen = {}

    def hook(model, body, style, name):
        k = (body, style)
        seen[k] = seen.get(k, 0) + 1
        if seen[k] <= fail_times:
            raise ModelError("timeout")

    return hook


class T7(unittest.TestCase):
    def test_t7_basic_batch_retries_transient(self):
        s = store_with(a="x")
        m = FakeModel(on_call=flaky(2))
        out = asyncio.run(BatchRun(s, m, ["a"], style="warm", model_name="m1").run())
        self.assertEqual(out, {"a": "applied"})
        self.assertEqual(len(m.calls), 3)

    def test_t7_basic_batch_gives_up_after_three(self):
        s = store_with(a="x")
        m = FakeModel(on_call=flaky(5))
        out = asyncio.run(BatchRun(s, m, ["a"], style="warm", model_name="m1").run())
        self.assertEqual(out, {"a": "failed:error"})
        self.assertEqual(len(m.calls), 3)

    def test_t7_edge_refusal_not_retried(self):
        s = store_with(a="REFUSE")
        m = FakeModel()
        out = asyncio.run(BatchRun(s, m, ["a"], style="warm", model_name="m1").run())
        self.assertEqual(out, {"a": "rejected"})
        self.assertEqual(len(m.calls), 1)

    def test_t7_edge_candidates_also_retry(self):
        # Design 5: the rule applies to every place that calls the model.
        s = store_with(a="x")
        m = FakeModel(on_call=flaky(1))
        cs = asyncio.run(generate_candidates(s, m, "a", ["warm", "bold"], model_name="m1"))
        self.assertEqual(set(cs.candidates), {"warm", "bold"})
        self.assertEqual(cs.errors, {})

    def test_t7_edge_no_retry_after_cancel(self):
        s = store_with(a="x")
        holder = {}

        def hook(model, body, style, name):
            holder["r"].cancel()
            raise ModelError("timeout")

        m = FakeModel(on_call=hook)
        r = BatchRun(s, m, ["a"], style="warm", model_name="m1")
        holder["r"] = r
        out = asyncio.run(r.run())
        self.assertEqual(len(m.calls), 1)
        self.assertEqual(out, {"a": "cancelled"})
