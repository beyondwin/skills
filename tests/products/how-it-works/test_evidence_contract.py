"""Synthetic inputs only; these tests do not create live execution records."""

import copy
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.lib.product_contract import payload_sha256

spec = importlib.util.spec_from_file_location("how_evidence", HERE / "live" / "evidence_contract.py")
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def synthetic_record():
    dimensions = {name: {"status": "not_measured", "method": "not_run"}
                  for name in module.DIMENSIONS}
    return {
        "schema_version": 2, "product": "how-it-works", "product_version": "2.0.0",
        "payload_sha256": "a" * 64, "model": "synthetic-model",
        "host": "codex", "client_version": "synthetic-client",
        "runner_version": "how-evidence-1", "executed_on": "2026-09-08",
        "cases": {"explicit-dns-path": {"invocation": "pass", "dimensions": dimensions}},
    }

class EvidenceContractTests(unittest.TestCase):
    def test_broken_mermaid_does_not_prove_syntax_or_loading(self):
        text = '```mermaid\nnot mermaid H1\n```\n1. **H1** — synthetic hop\n'
        result = module.observe_text(text)
        self.assertEqual(result["fence"]["status"], "pass")
        self.assertEqual(result["hop_ids"]["status"], "pass")
        for key in ("mermaid_syntax", "meaning", "skill_loading"):
            self.assertEqual(result[key]["status"], "not_measured")

    def test_mismatched_hops_fail(self):
        text = '```mermaid\nflowchart LR\nA["H1 start"]\n```\n1. **H2** — stop\n'
        self.assertEqual(module.observe_text(text)["hop_ids"]["status"], "fail")

    def test_legacy_record_is_unchanged_and_unbound(self):
        record = json.loads((HERE / "live" / "smoke-record.json").read_text())
        before = copy.deepcopy(record)
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="a"*64),
                         "historical-unbound")
        self.assertEqual(record, before)

    def test_different_payload_cannot_claim_current_build(self):
        record = synthetic_record()
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="b"*64),
                         "different-payload")
        record["model"] = None
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="a"*64),
                         "unbound")

    def test_regex_cannot_be_syntax_evidence(self):
        record = synthetic_record()
        record["cases"]["explicit-dns-path"]["dimensions"]["mermaid_syntax"] = {
            "status": "pass", "method": "regex"}
        with self.assertRaisesRegex(ValueError, "invalid evidence method"):
            module.record_binding(record, current_version="2.0.0", current_hash="a"*64)

    def test_current_metadata_binding_is_not_a_quality_verdict(self):
        record = synthetic_record()
        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="a"*64),
                         "current-bounded")
        self.assertEqual(record["cases"]["explicit-dns-path"]["dimensions"]["meaning"]["status"],
                         "not_measured")
        self.assertEqual(module.record_binding(record, current_version="2.0.1", current_hash="a"*64),
                         "different-payload")

    def test_source_reference_mutation_breaks_binding(self):
        with tempfile.TemporaryDirectory(prefix="how-evidence-") as directory:
            copied = Path(directory) / "how-it-works"
            shutil.copytree(ROOT / "skills" / "how-it-works", copied)
            record = synthetic_record()
            record["payload_sha256"] = payload_sha256(copied)
            target = copied / "references" / "output.md"
            target.write_bytes(target.read_bytes() + b"\nSynthetic audit mutation.\n")
            self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash=payload_sha256(copied)),
                             "different-payload")

    def test_invalid_record_shapes_are_rejected(self):
        variants = []
        for key, value in (("schema_version", True), ("extra", "unexpected"),
                           ("executed_on", "not-a-date"), ("cases", {})):
            record = synthetic_record()
            record[key] = value
            variants.append(record)
        missing = synthetic_record()
        del missing["cases"]["explicit-dns-path"]["dimensions"]["meaning"]
        variants.append(missing)
        for record in variants:
            with self.subTest(record=record), self.assertRaises(ValueError):
                module.record_binding(record, current_version="2.0.0", current_hash="a"*64)

    def test_duplicate_or_absent_hops_never_prove_quality(self):
        duplicate = '```mermaid\nA["H1 start"]\n```\n1. **H1** — a\n2. **H1** — b\n'
        self.assertEqual(module.observe_text(duplicate)["hop_ids"]["status"], "fail")
        missing = module.observe_text("A plain answer.")
        self.assertEqual(missing["fence"]["status"], "fail")
        for key in ("hop_ids", "skill_loading", "mermaid_syntax", "meaning"):
            self.assertEqual(missing[key]["status"], "not_measured")

    def test_closed_nonempty_fences_and_unique_hops_are_lexical_only(self):
        text = '```mermaid\nA["H1"] --> B["H2"]\n```\n1. **H1** — first\n2. **H2** — next\n'
        self.assertEqual(module.observe_text(text), {
            "fence": {"status": "pass", "method": "lexical"},
            "hop_ids": {"status": "pass", "method": "lexical"},
            "skill_loading": {"status": "not_measured", "method": "not_run"},
            "mermaid_syntax": {"status": "not_measured", "method": "not_run"},
            "meaning": {"status": "not_measured", "method": "not_run"},
        })
        for text in ('```mermaid\nH1\n', '```mermaid\n \n```',
                     '```mermaid\nH1\n```\n```mermaid\n\n```'):
            with self.subTest(text=text):
                result = module.observe_text(text)
                self.assertEqual(result["fence"], {"status": "fail", "method": "lexical"})
                self.assertEqual(result["hop_ids"], {"status": "not_measured", "method": "not_run"})

    def test_code_fenced_hop_lists_do_not_count_as_prose(self):
        text = '```mermaid\nA["H1"]\n```\n```text\n1. **H1** — fake prose\n```'
        self.assertEqual(module.observe_text(text)["hop_ids"]["status"], "fail")

    def test_declared_methods_are_dimension_specific_and_not_authentication(self):
        allowed = {"fence": ("lexical",), "hop_ids": ("lexical",),
                   "skill_loading": ("host_event",), "mermaid_syntax": ("parser", "renderer"),
                   "meaning": ("semantic_review",)}
        for dimension, methods in allowed.items():
            for method in methods:
                for status in ("pass", "fail"):
                    record = synthetic_record()
                    record["cases"]["explicit-dns-path"]["dimensions"][dimension] = {
                        "status": status, "method": method}
                    before = copy.deepcopy(record)
                    with self.subTest(dimension=dimension, method=method, status=status):
                        self.assertEqual(module.record_binding(record, current_version="2.0.0", current_hash="a"*64),
                                         "current-bounded")
                        self.assertEqual(record, before)
        for dimension in allowed:
            for status, method in (("pass", "not_run"), ("fail", "regex"),
                                   ("not_measured", allowed[dimension][0]), ("pass", [])):
                record = synthetic_record()
                record["cases"]["explicit-dns-path"]["dimensions"][dimension] = {
                    "status": status, "method": method}
                with self.subTest(dimension=dimension, status=status, method=method), self.assertRaisesRegex(ValueError, "invalid evidence method"):
                    module.record_binding(record, current_version="2.0.0", current_hash="a"*64)

    def test_malformed_metadata_and_nested_shapes_are_rejected(self):
        variants = [None, [], {}, {"schema_version": 3}]
        for key, value in (("product", "other"), ("product_version", " "), ("host", "unknown"),
                           ("host", []), ("client_version", None), ("runner_version", 2),
                           ("executed_on", "2026-02-30"), ("payload_sha256", "A"*64),
                           ("payload_sha256", "a"*63), ("payload_sha256", None),
                           ("model", " "), ("model", False), ("cases", [])):
            record = synthetic_record()
            record[key] = value
            variants.append(record)
        for case in (None, {}, {"invocation": "pass", "dimensions": {}, "extra": True},
                     {"invocation": [], "dimensions": {}},
                     {"invocation": "unknown", "dimensions": {}}):
            record = synthetic_record()
            record["cases"]["explicit-dns-path"] = case
            variants.append(record)
        for item in (None, {}, {"status": "pass", "method": "lexical", "extra": 0},
                     {"status": [], "method": "lexical"}, {"status": "unknown", "method": "lexical"}):
            record = synthetic_record()
            record["cases"]["explicit-dns-path"]["dimensions"]["fence"] = item
            variants.append(record)
        for record in variants:
            with self.subTest(record=record), self.assertRaises(ValueError):
                module.record_binding(record, current_version="2.0.0", current_hash="a"*64)

    def test_historical_shape_validation_does_not_reinterpret_host_verdicts(self):
        historical = {"schema_version": 1, "executed_on": "2026-08-28", "hosts": []}
        self.assertEqual(module.record_binding(historical, current_version="2.0.0", current_hash="a"*64),
                         "historical-unbound")
        for key, value in (("extra", True), ("executed_on", None), ("executed_on", "bad"), ("hosts", {})):
            record = {**historical, key: value}
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                module.record_binding(record, current_version="2.0.0", current_hash="a"*64)

    def test_unknown_model_stays_unbound_even_for_a_different_payload(self):
        record = synthetic_record()
        record["model"] = None
        self.assertEqual(module.record_binding(record, current_version="2.0.1", current_hash="b"*64), "unbound")
        record["cases"]["explicit-dns-path"]["dimensions"]["meaning"] = {"status": "pass", "method": "regex"}
        with self.assertRaisesRegex(ValueError, "invalid evidence method"):
            module.record_binding(record, current_version="2.0.0", current_hash="a"*64)
