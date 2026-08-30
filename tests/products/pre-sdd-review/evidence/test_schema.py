from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401
from pre_sdd_review_evidence import schema


SHA = "a" * 64
RUN_ID = "123e4567-e89b-12d3-a456-426614174000"
TIME = "2026-08-30T10:00:00Z"


def valid_finding(**changes: object) -> dict[str, object]:
    finding: dict[str, object] = {
        "id": "PSDR-001",
        "severity": "IMPORTANT",
        "class": "verification-gap",
        "pattern_key": "build-only-acceptance",
        "consequence_category": "avoidable-rework",
        "status": "repaired",
        "location": {"path": "docs/plan.md", "locator": "Task 4 / Verification"},
        "evidence_refs": ["package.json#scripts.test"],
        "consequence": "A build-only check can accept wrong behavior.",
        "minimal_fix": "Add behavioral acceptance evidence.",
        "repair_pass": 1,
    }
    finding.update(changes)
    return finding


def valid_review(**changes: object) -> dict[str, object]:
    review: dict[str, object] = {
        "schema_version": 1,
        "record_type": "review",
        "run_id": RUN_ID,
        "started_at": TIME,
        "completed_at": "2026-08-30T10:04:12Z",
        "skill": {
            "name": "pre-sdd-review",
            "declared_version": "1.2.0",
            "release_version": "1.2.0",
            "skill_sha256": SHA,
            "reviewer_protocol_sha256": SHA,
            "release_manifest_sha256": SHA,
            "cli_version": "1.0.0",
            "schema_version": 1,
        },
        "client": {"id": "codex", "version": None, "model": None},
        "protocol": {
            "mode": "default",
            "execution": "full",
            "reviewer_count": 1,
            "fresh_reviewer": True,
            "read_only_enforced": True,
            "conditional_trigger": None,
            "degraded_reasons": [],
        },
        "target": {
            "repo_id": "repo-123",
            "initial_head": "b" * 40,
            "initial_dirty": False,
            "plan_path": "docs/plan.md",
            "plan_initial_sha256": SHA,
            "design_path": "docs/design.md",
            "design_initial_sha256": SHA,
            "resolution_status": "resolved",
        },
        "result": {
            "completion": "completed",
            "verdict": "READY",
            "block_reason": None,
            "completion_reason": None,
            "review_passes": 2,
            "repair_passes": 1,
            "findings": [valid_finding()],
        },
        "freshness": {
            "final_head": "b" * 40,
            "final_dirty": False,
            "plan_final_sha256": SHA,
            "design_final_sha256": SHA,
        },
        "metrics": {
            "elapsed_ms": 252000,
            "recorder_elapsed_ms": 12,
            "reviewer_count": 1,
            "review_passes": 2,
            "repair_passes": 1,
            "token_usage": {"input": 5, "output": 7, "total": 12, "provenance": "measured"},
        },
    }
    for key, value in changes.items():
        if key in {"verdict", "completion", "block_reason", "completion_reason", "review_passes", "repair_passes", "findings"}:
            review["result"][key] = value  # type: ignore[index]
        else:
            review[key] = value
    if review["result"]["verdict"] == "REVISE":  # type: ignore[index]
        review["result"]["findings"][0]["status"] = "unresolved"  # type: ignore[index]
    return review


def valid_downstream(**changes: object) -> dict[str, object]:
    downstream: dict[str, object] = {
        "status": "implementation-completed",
        "plan_hash_matched": True,
        "replan_count": 0,
        "evaluated_finding_ids": ["PSDR-001"],
        "escaped_findings": [],
        "disputed_findings": [],
        "prevented_rework": [],
    }
    downstream.update(changes)
    return downstream


def valid_outcome(**changes: object) -> dict[str, object]:
    outcome: dict[str, object] = {
        "schema_version": 1,
        "record_type": "outcome",
        "run_id": RUN_ID,
        "recorded_at": TIME,
        "recorder": {"client": "codex", "version": None, "model": None},
        "downstream": valid_downstream(),
        "assessment": {
            "label": "good",
            "basis": "verified-repository-evidence",
            "confidence": "high",
        },
    }
    outcome.update(changes)
    return outcome


class SchemaContractTests(unittest.TestCase):
    def test_review_limits_and_enums_are_exact(self) -> None:
        self.assertEqual(schema.SCHEMA_VERSION, 1)
        self.assertEqual(schema.REVIEW_HARD_LIMIT, 32 * 1024)
        self.assertEqual(schema.OUTCOME_HARD_LIMIT, 8 * 1024)
        self.assertEqual(schema.VERDICTS, frozenset({"READY", "REVISE", "BLOCKED"}))
        self.assertEqual(schema.FINDING_CLASSES, frozenset({"authority-drift", "repo-reality", "coverage", "ordering", "verification-gap"}))

    def test_accepts_and_normalizes_a_complete_review_without_mutating_caller(self) -> None:
        review = valid_review()
        review["protocol"]["degraded_reasons"] = ["other", "other"]  # type: ignore[index]
        review["protocol"]["execution"] = "degraded"  # type: ignore[index]
        before = copy.deepcopy(review)
        normalized = schema.validate_review(review)
        self.assertEqual(review, before)
        self.assertEqual(normalized["protocol"]["degraded_reasons"], ["other"])

    def test_every_review_object_rejects_unknown_and_prohibited_content_keys(self) -> None:
        for key in ("extra", "prompt", "response", "document_body", "code", "environment"):
            review = valid_review()
            review[key] = "private"  # type: ignore[index]
            with self.subTest(key=key), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)

    def test_required_nested_keys_and_nullable_values_are_closed(self) -> None:
        cases = (
            ("skill", "name"), ("client", "model"), ("protocol", "mode"),
            ("target", "repo_id"), ("result", "verdict"), ("freshness", "final_head"),
            ("metrics", "token_usage"),
        )
        for section, key in cases:
            review = valid_review()
            del review[section][key]  # type: ignore[index]
            with self.subTest(section=section, key=key), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)

    def test_uuid_time_hash_strings_and_safe_paths_are_exact(self) -> None:
        mutations = (
            ("run_id", "not-a-uuid"), ("started_at", "2026-08-30T10:00:00+00:00"),
            ("skill.skill_sha256", "A" * 64), ("target.plan_path", "/private/plan.md"),
            ("target.design_path", "docs/../design.md"), ("target.plan_path", "line\nbreak"),
        )
        for name, value in mutations:
            review = valid_review()
            parent, _, key = name.partition(".")
            if key:
                review[parent][key] = value  # type: ignore[index]
            else:
                review[parent] = value
            with self.subTest(name=name), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)

    def test_finding_bounds_duplicate_normalization_and_ready_invariants(self) -> None:
        review = valid_review()
        finding = review["result"]["findings"][0]  # type: ignore[index]
        finding["evidence_refs"] = ["a", "a"]
        self.assertEqual(schema.validate_review(review)["result"]["findings"][0]["evidence_refs"], ["a"])
        for name, value in (("consequence", "x" * 301), ("minimal_fix", "x" * 301), ("status", "unresolved")):
            review = valid_review()
            review["result"]["findings"][0][name] = value  # type: ignore[index]
            with self.subTest(name=name), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)
        duplicate = valid_review()
        duplicate["result"]["findings"].append(valid_finding())  # type: ignore[index]
        with self.assertRaises(schema.EvidenceError):
            schema.validate_review(duplicate)

    def test_protocol_and_completion_cross_field_invariants(self) -> None:
        cases = []
        full = valid_review(); full["protocol"]["fresh_reviewer"] = False  # type: ignore[index]
        cases.append(full)
        triggered = valid_review(); triggered["protocol"]["conditional_trigger"] = "auth-boundary"  # type: ignore[index]
        cases.append(triggered)
        degraded = valid_review(); degraded["protocol"]["execution"] = "degraded"  # type: ignore[index]
        cases.append(degraded)
        revise = valid_review(); revise["result"]["verdict"] = "REVISE"; revise["result"]["findings"] = []  # type: ignore[index]
        cases.append(revise)
        abandoned = valid_review(); abandoned["result"].update({"completion": "abandoned", "verdict": None, "completion_reason": "client-interrupted", "review_passes": 0, "repair_passes": 0, "findings": []}); abandoned["metrics"].update({"review_passes": 0, "repair_passes": 0})  # type: ignore[index]
        abandoned["freshness"] = {"final_head": None, "final_dirty": None, "plan_final_sha256": None, "design_final_sha256": None}
        self.assertIsInstance(schema.validate_review(abandoned), dict)
        abandoned["result"]["completion_reason"] = None  # type: ignore[index]
        cases.append(abandoned)
        for review in cases:
            with self.subTest(review=review["result"]), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)

    def test_mirrored_counts_token_totals_and_resolution_rows_are_enforced(self) -> None:
        for section, key, value in (("metrics", "reviewer_count", 2), ("metrics", "review_passes", 3), ("metrics", "repair_passes", 0), ("metrics", "token_usage", {"input": 1, "output": 2, "total": 9, "provenance": "measured"})):
            review = valid_review(); review[section][key] = value  # type: ignore[index]
            with self.subTest(key=key), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)
        not_git = valid_review()
        not_git["target"].update({"repo_id": None, "initial_head": None, "initial_dirty": None, "plan_path": None, "plan_initial_sha256": None, "design_path": None, "design_initial_sha256": None, "resolution_status": "not-git-repository"})  # type: ignore[index]
        not_git["freshness"] = {"final_head": None, "final_dirty": None, "plan_final_sha256": None, "design_final_sha256": None}
        self.assertIsInstance(schema.validate_review(not_git), dict)
        not_git["target"]["repo_id"] = "leak"  # type: ignore[index]
        with self.assertRaises(schema.EvidenceError):
            schema.validate_review(not_git)

    def test_canonical_json_and_bounded_readers_are_exact(self) -> None:
        self.assertEqual(schema.canonical_json_bytes({"z": "한", "a": 1}), b'{"a":1,"z":"\xed\x95\x9c"}\n')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = root / "data"; binary.write_bytes(b"x" * 5)
            self.assertEqual(schema.read_bounded_bytes(binary, 5), b"x" * 5)
            with self.assertRaises(schema.EvidenceError): schema.read_bounded_bytes(binary, 4)
            payload = root / "payload.json"; payload.write_text('{"a":1}', encoding="utf-8")
            self.assertEqual(schema.read_bounded_json(payload, 7), {"a": 1})
            with self.assertRaises(schema.EvidenceError): schema.read_bounded_json(payload, 6)

    def test_false_ready_requires_ready_and_material_escape(self) -> None:
        review = valid_review(verdict="REVISE")
        downstream = valid_downstream(escaped_findings=[{"class": "coverage", "severity": "BLOCKER", "pattern_key": "missing", "consequence_category": "escaped-material-defect", "basis": "user-reported"}])
        with self.assertRaisesRegex(schema.EvidenceError, "false-ready requires READY"):
            schema.validate_outcome(valid_outcome(assessment={"label": "false-ready", "basis": "user-reported", "confidence": "high"}, downstream=downstream), review)

    def test_outcome_links_findings_and_assessment_derivation(self) -> None:
        review = valid_review()
        downstream = valid_downstream(prevented_rework=[{"finding_id": "PSDR-001", "pattern_key": "build-only-acceptance", "consequence_category": "avoidable-rework", "basis": "agent-observed"}])
        outcome = valid_outcome(downstream=downstream, assessment={"label": "prevented-rework", "basis": "agent-observed", "confidence": "medium"})
        self.assertEqual(schema.validate_outcome(outcome, review)["assessment"]["label"], "prevented-rework")
        self.assertEqual(schema.derive_assessment(review, valid_downstream(escaped_findings=[{"class": "coverage", "severity": "BLOCKER", "pattern_key": "missing", "consequence_category": "escaped-material-defect", "basis": "user-reported"}])), "false-ready")
        bad = valid_downstream(prevented_rework=[{"finding_id": "PSDR-001", "pattern_key": "wrong", "consequence_category": "avoidable-rework", "basis": "agent-observed"}])
        with self.assertRaises(schema.EvidenceError): schema.validate_outcome(valid_outcome(downstream=bad, assessment={"label": "prevented-rework", "basis": "agent-observed", "confidence": "low"}), review)

    def test_outcome_size_and_abandoned_downstream_are_bounded(self) -> None:
        review = valid_review()
        abandoned = valid_outcome(downstream=valid_downstream(status="cancelled"), assessment={"label": "abandoned", "basis": "verified-repository-evidence", "confidence": "low"})
        self.assertEqual(schema.validate_outcome(abandoned, review)["assessment"]["label"], "abandoned")
        too_large = valid_review(); too_large["result"]["findings"] = [valid_finding(consequence="x" * 300, minimal_fix="y" * 300) for _ in range(60)]  # type: ignore[index]
        for index, finding in enumerate(too_large["result"]["findings"]): finding["id"] = f"PSDR-{index:03d}"  # type: ignore[index]
        with self.assertRaises(schema.EvidenceError): schema.validate_review(too_large)
