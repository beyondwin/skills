from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
            "declared_version": "1.3.1",
            "release_version": "1.3.1",
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
            "repo_id": "d" * 64,
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


def valid_abandoned_review() -> dict[str, object]:
    review = valid_review()
    review["protocol"] = {
        "mode": "default",
        "execution": "unknown",
        "reviewer_count": 0,
        "fresh_reviewer": False,
        "read_only_enforced": False,
        "conditional_trigger": None,
        "degraded_reasons": [],
    }
    review["result"] = {
        "completion": "abandoned",
        "verdict": None,
        "block_reason": None,
        "completion_reason": "client-interrupted",
        "review_passes": 0,
        "repair_passes": 0,
        "findings": [],
    }
    review["freshness"] = {
        "final_head": None,
        "final_dirty": None,
        "plan_final_sha256": None,
        "design_final_sha256": None,
    }
    review["metrics"] = {
        "elapsed_ms": 252000,
        "recorder_elapsed_ms": 12,
        "reviewer_count": 0,
        "review_passes": 0,
        "repair_passes": 0,
        "token_usage": None,
    }
    return review


class SchemaContractTests(unittest.TestCase):
    def test_review_limits_and_enums_are_exact(self) -> None:
        self.assertEqual(schema.SCHEMA_VERSION, 1)
        self.assertEqual(schema.REVIEW_HARD_LIMIT, 32 * 1024)
        self.assertEqual(schema.OUTCOME_HARD_LIMIT, 8 * 1024)
        self.assertEqual(schema.VERDICTS, frozenset({"READY", "REVISE", "BLOCKED"}))
        self.assertEqual(schema.FINDING_CLASSES, frozenset({"authority-drift", "repo-reality", "coverage", "ordering", "verification-gap"}))
        self.assertEqual(schema.CLIENT_IDS, frozenset({"codex", "claude-code", "cursor", "grok", "other", "unknown"}))
        self.assertEqual(schema.MODES, frozenset({"default", "review-only"}))
        self.assertEqual(schema.EXECUTIONS, frozenset({"full", "degraded", "blocked", "unknown"}))
        self.assertEqual(schema.CONDITIONAL_TRIGGERS, frozenset({"runtime-removal", "schema-migration", "auth-boundary", "data-boundary", "external-side-effect"}))
        self.assertEqual(schema.DEGRADED_REASONS, frozenset({"fresh-reviewer-unavailable", "read-only-unavailable", "conditional-reviewer-unavailable", "host-capability-unknown", "other"}))
        self.assertEqual(schema.RESOLUTION_STATUSES, frozenset({"resolved", "plan-missing", "spec-field-missing", "spec-path-invalid", "design-missing", "outside-repository", "not-git-repository"}))
        self.assertEqual(schema.FINDING_STATUSES, frozenset({"repaired", "unresolved", "blocked-by-authority", "accepted-as-is"}))
        self.assertEqual(schema.CONSEQUENCE_CATEGORIES, frozenset({"escaped-material-defect", "avoidable-rework", "false-block", "protocol-degradation", "input-resolution-failure", "other"}))
        self.assertEqual(schema.DOWNSTREAM_STATUSES, frozenset({"sdd-completed", "implementation-completed", "implementation-abandoned", "cancelled"}))
        self.assertEqual(schema.ASSESSMENT_LABELS, frozenset({"good", "false-ready", "noisy", "prevented-rework", "inconclusive", "abandoned"}))
        self.assertEqual(schema.EVIDENCE_BASES, frozenset({"verified-repository-evidence", "user-reported", "agent-observed", "agent-inferred", "unknown"}))
        self.assertEqual(schema.CONFIDENCES, frozenset({"low", "medium", "high"}))

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
            ("target.repo_id", "/absolute/repository"),
            ("target.repo_id", "repo-123"),
            ("target.repo_id", "g" * 64),
            ("target.repo_id", "A" * 64),
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

    def test_abandoned_review_requires_the_canonical_protocol_result_freshness_and_metrics_projection(self) -> None:
        self.assertIsInstance(schema.validate_review(valid_abandoned_review()), dict)
        mutations: tuple[tuple[str, str, object, tuple[str, str, object] | None], ...] = (
            ("protocol", "execution", "blocked", None),
            ("protocol", "reviewer_count", 1, ("metrics", "reviewer_count", 1)),
            ("protocol", "fresh_reviewer", True, None),
            ("protocol", "read_only_enforced", True, None),
            ("protocol", "conditional_trigger", "auth-boundary", None),
            ("protocol", "degraded_reasons", ["other"], None),
            ("result", "verdict", "READY", None),
            ("result", "block_reason", "repository-unavailable", None),
            ("result", "completion_reason", None, None),
            ("result", "review_passes", 1, ("metrics", "review_passes", 1)),
            ("result", "repair_passes", 1, ("metrics", "repair_passes", 1)),
            ("result", "findings", [valid_finding()], None),
            ("freshness", "final_head", "b" * 40, None),
            ("freshness", "final_dirty", False, None),
            ("freshness", "plan_final_sha256", SHA, None),
            ("freshness", "design_final_sha256", SHA, None),
            (
                "metrics",
                "token_usage",
                {"input": 1, "output": 2, "total": 3, "provenance": "measured"},
                None,
            ),
        )
        for section, key, value, paired in mutations:
            review = valid_abandoned_review()
            review[section][key] = value  # type: ignore[index]
            if paired is not None:
                pair_section, pair_key, pair_value = paired
                review[pair_section][pair_key] = pair_value  # type: ignore[index]
            with self.subTest(section=section, key=key), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)

    def test_all_string_envelopes_reject_c1_and_unicode_line_separators(self) -> None:
        for character in ("\u0080", "\u0085", "\u009f", "\u2028", "\u2029"):
            review = valid_review()
            review["result"]["findings"][0]["consequence"] = f"before{character}after"  # type: ignore[index]
            with self.subTest(record="review", codepoint=ord(character)), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)

            outcome = valid_outcome()
            outcome["recorder"]["model"] = f"before{character}after"  # type: ignore[index]
            with self.subTest(record="outcome", codepoint=ord(character)), self.assertRaises(schema.EvidenceError):
                schema.validate_outcome(outcome, valid_review())

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
        abandoned = valid_abandoned_review()
        self.assertIsInstance(schema.validate_review(abandoned), dict)
        abandoned["result"]["completion_reason"] = None  # type: ignore[index]
        cases.append(abandoned)
        for review in cases:
            with self.subTest(review=review["result"]), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)

    def test_completion_reason_and_nullable_rows_are_exact(self) -> None:
        review = valid_review()
        review["metrics"]["token_usage"] = None  # type: ignore[index]
        review["result"]["findings"][0]["repair_pass"] = None  # type: ignore[index]
        self.assertIsInstance(schema.validate_review(review), dict)
        completed = valid_review(completion_reason="client-interrupted")
        with self.assertRaises(schema.EvidenceError):
            schema.validate_review(completed)
        abandoned = valid_abandoned_review()
        self.assertIsInstance(schema.validate_review(abandoned), dict)
        abandoned["result"]["completion_reason"] = "Uppercase"  # type: ignore[index]
        with self.assertRaises(schema.EvidenceError):
            schema.validate_review(abandoned)

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

    def test_references_require_canonical_posix_relative_forms(self) -> None:
        for path in ("docs\\plan.md", "./docs/plan.md", "docs//plan.md", "docs/./plan.md"):
            review = valid_review()
            review["target"]["plan_path"] = path  # type: ignore[index]
            with self.subTest(path=path), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)
        review = valid_review()
        review["result"]["findings"][0]["evidence_refs"] = ["src\\app.py#symbol"]  # type: ignore[index]
        with self.assertRaises(schema.EvidenceError):
            schema.validate_review(review)

    def test_times_require_extended_utc_rfc3339_seconds(self) -> None:
        for value in ("20260830T100000Z", "2026-08-30T10:00Z", "2026-08-30 10:00:00Z", "2026-08-30T10:00:00. Z"):
            review = valid_review()
            review["started_at"] = value
            with self.subTest(value=value), self.assertRaises(schema.EvidenceError):
                schema.validate_review(review)
        review = valid_review()
        review["started_at"] = "2026-08-30T10:00:00.123Z"
        self.assertIsInstance(schema.validate_review(review), dict)

    def test_every_required_review_and_outcome_key_is_closed(self) -> None:
        review_sections = {
            "skill": ("name", "declared_version", "release_version", "skill_sha256", "reviewer_protocol_sha256", "release_manifest_sha256", "cli_version", "schema_version"),
            "client": ("id", "version", "model"),
            "protocol": ("mode", "execution", "reviewer_count", "fresh_reviewer", "read_only_enforced", "conditional_trigger", "degraded_reasons"),
            "target": ("repo_id", "initial_head", "initial_dirty", "plan_path", "plan_initial_sha256", "design_path", "design_initial_sha256", "resolution_status"),
            "result": ("completion", "verdict", "block_reason", "completion_reason", "review_passes", "repair_passes", "findings"),
            "freshness": ("final_head", "final_dirty", "plan_final_sha256", "design_final_sha256"),
            "metrics": ("elapsed_ms", "recorder_elapsed_ms", "reviewer_count", "review_passes", "repair_passes", "token_usage"),
        }
        for section, keys in review_sections.items():
            for key in keys:
                review = valid_review()
                del review[section][key]  # type: ignore[index]
                with self.subTest(record="review", section=section, key=key), self.assertRaises(schema.EvidenceError):
                    schema.validate_review(review)
        outcome_sections = {
            "recorder": ("client", "version", "model"),
            "downstream": ("status", "plan_hash_matched", "replan_count", "evaluated_finding_ids", "escaped_findings", "disputed_findings", "prevented_rework"),
            "assessment": ("label", "basis", "confidence"),
        }
        for section, keys in outcome_sections.items():
            for key in keys:
                outcome = valid_outcome()
                del outcome[section][key]  # type: ignore[index]
                with self.subTest(record="outcome", section=section, key=key), self.assertRaises(schema.EvidenceError):
                    schema.validate_outcome(outcome, valid_review())

    def test_every_finding_and_location_required_key_is_closed(self) -> None:
        finding_keys = (
            "id", "severity", "class", "pattern_key", "consequence_category",
            "status", "location", "evidence_refs", "consequence", "minimal_fix",
            "repair_pass",
        )
        for key in finding_keys:
            review = valid_review()
            del review["result"]["findings"][0][key]  # type: ignore[index]
            with self.subTest(object="finding", key=key), self.assertRaises(schema.EvidenceError) as raised:
                schema.validate_review(review)
            self.assertEqual(raised.exception.code, "invalid-keys")
        for key in ("path", "locator"):
            review = valid_review()
            del review["result"]["findings"][0]["location"][key]  # type: ignore[index]
            with self.subTest(object="finding.location", key=key), self.assertRaises(schema.EvidenceError) as raised:
                schema.validate_review(review)
            self.assertEqual(raised.exception.code, "invalid-keys")

    def test_every_nullable_review_and_outcome_field_has_an_isolated_row(self) -> None:
        def not_git_review() -> dict[str, object]:
            review = valid_review()
            review["target"].update({  # type: ignore[index]
                "repo_id": None,
                "initial_head": None,
                "initial_dirty": None,
                "plan_path": None,
                "plan_initial_sha256": None,
                "design_path": None,
                "design_initial_sha256": None,
                "resolution_status": "not-git-repository",
            })
            review["freshness"] = {  # type: ignore[index]
                "final_head": None,
                "final_dirty": None,
                "plan_final_sha256": None,
                "design_final_sha256": None,
            }
            return review

        accepted_review_cases = (
            ("client.version", valid_review, lambda item: item["client"].__setitem__("version", None)),
            ("client.model", valid_review, lambda item: item["client"].__setitem__("model", None)),
            ("protocol.conditional_trigger", valid_review, lambda item: item["protocol"].__setitem__("conditional_trigger", None)),
            ("result.block_reason", valid_review, lambda item: item["result"].__setitem__("block_reason", None)),
            ("result.completion_reason", valid_review, lambda item: item["result"].__setitem__("completion_reason", None)),
            ("finding.repair_pass", valid_review, lambda item: item["result"]["findings"][0].__setitem__("repair_pass", None)),
            ("metrics.token_usage", valid_review, lambda item: item["metrics"].__setitem__("token_usage", None)),
            ("target.repo_id", not_git_review, lambda item: item["target"].__setitem__("repo_id", None)),
            ("target.initial_head", not_git_review, lambda item: item["target"].__setitem__("initial_head", None)),
            ("target.initial_dirty", not_git_review, lambda item: item["target"].__setitem__("initial_dirty", None)),
            ("target.plan_path", not_git_review, lambda item: item["target"].__setitem__("plan_path", None)),
            ("target.plan_initial_sha256", not_git_review, lambda item: item["target"].__setitem__("plan_initial_sha256", None)),
            ("target.design_path", not_git_review, lambda item: item["target"].__setitem__("design_path", None)),
            ("target.design_initial_sha256", not_git_review, lambda item: item["target"].__setitem__("design_initial_sha256", None)),
            ("freshness.final_head", not_git_review, lambda item: item["freshness"].__setitem__("final_head", None)),
            ("freshness.final_dirty", not_git_review, lambda item: item["freshness"].__setitem__("final_dirty", None)),
            ("freshness.plan_final_sha256", not_git_review, lambda item: item["freshness"].__setitem__("plan_final_sha256", None)),
            ("freshness.design_final_sha256", not_git_review, lambda item: item["freshness"].__setitem__("design_final_sha256", None)),
        )
        for name, factory, mutate in accepted_review_cases:
            review = factory()
            mutate(review)
            with self.subTest(field=name):
                self.assertIsInstance(schema.validate_review(review), dict)
        abandoned = valid_abandoned_review()
        self.assertIsInstance(schema.validate_review(abandoned), dict)
        outcome = valid_outcome()
        for key in ("version", "model"):
            isolated = copy.deepcopy(outcome)
            isolated["recorder"][key] = None  # type: ignore[index]
            with self.subTest(field=f"recorder.{key}"):
                self.assertIsInstance(schema.validate_outcome(isolated, valid_review()), dict)

    def test_every_outcome_nested_record_key_is_closed(self) -> None:
        escaped = {"severity": "BLOCKER", "class": "coverage", "pattern_key": "missed-coverage", "consequence_category": "escaped-material-defect", "basis": "user-reported"}
        escaped_outcome = valid_outcome(downstream=valid_downstream(escaped_findings=[escaped]), assessment={"label": "false-ready", "basis": "user-reported", "confidence": "high"})
        for key in tuple(escaped):
            broken = copy.deepcopy(escaped_outcome)
            del broken["downstream"]["escaped_findings"][0][key]  # type: ignore[index]
            with self.subTest(record="escaped", key=key), self.assertRaises(schema.EvidenceError):
                schema.validate_outcome(broken, valid_review())
        review = valid_review()
        review["result"]["findings"][0]["severity"] = "BLOCKER"  # type: ignore[index]
        disputed = {"finding_id": "PSDR-001", "class": "verification-gap", "pattern_key": "build-only-acceptance", "consequence_category": "avoidable-rework", "basis": "agent-observed"}
        disputed_outcome = valid_outcome(downstream=valid_downstream(disputed_findings=[disputed]), assessment={"label": "noisy", "basis": "agent-observed", "confidence": "medium"})
        for key in tuple(disputed):
            broken = copy.deepcopy(disputed_outcome)
            del broken["downstream"]["disputed_findings"][0][key]  # type: ignore[index]
            with self.subTest(record="disputed", key=key), self.assertRaises(schema.EvidenceError):
                schema.validate_outcome(broken, review)
        prevented = {"finding_id": "PSDR-001", "pattern_key": "build-only-acceptance", "consequence_category": "avoidable-rework", "basis": "agent-observed"}
        prevented_outcome = valid_outcome(downstream=valid_downstream(prevented_rework=[prevented]), assessment={"label": "prevented-rework", "basis": "agent-observed", "confidence": "medium"})
        for key in tuple(prevented):
            broken = copy.deepcopy(prevented_outcome)
            del broken["downstream"]["prevented_rework"][0][key]  # type: ignore[index]
            with self.subTest(record="prevented", key=key), self.assertRaises(schema.EvidenceError):
                schema.validate_outcome(broken, valid_review())

    def test_every_resolution_status_has_its_exact_nullability_projection(self) -> None:
        cases = {
            "resolved": ({}, {}),
            "plan-missing": ({"plan_initial_sha256": None, "design_path": None, "design_initial_sha256": None}, {"plan_final_sha256": None, "design_final_sha256": None}),
            "spec-field-missing": ({"design_path": None, "design_initial_sha256": None}, {"design_final_sha256": None}),
            "spec-path-invalid": ({"design_path": None, "design_initial_sha256": None}, {"design_final_sha256": None}),
            "design-missing": ({"design_initial_sha256": None}, {"design_final_sha256": None}),
            "outside-repository": ({"plan_path": None, "plan_initial_sha256": None, "design_path": None, "design_initial_sha256": None}, {"plan_final_sha256": None, "design_final_sha256": None}),
            "not-git-repository": ({"repo_id": None, "initial_head": None, "initial_dirty": None, "plan_path": None, "plan_initial_sha256": None, "design_path": None, "design_initial_sha256": None}, {"final_head": None, "final_dirty": None, "plan_final_sha256": None, "design_final_sha256": None}),
        }
        for status, (target_changes, freshness_changes) in cases.items():
            review = valid_review()
            review["target"]["resolution_status"] = status  # type: ignore[index]
            review["target"].update(target_changes)  # type: ignore[index]
            review["freshness"].update(freshness_changes)  # type: ignore[index]
            with self.subTest(status=status):
                self.assertIsInstance(schema.validate_review(review), dict)

    def test_bounded_reader_requests_exactly_limit_plus_one_bytes(self) -> None:
        class RecordingStream:
            def __init__(self) -> None:
                self.calls: list[int] = []

            def __enter__(self):
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def read(self, amount: int) -> bytes:
                self.calls.append(amount)
                return b"{}"

        stream = RecordingStream()
        with mock.patch.object(Path, "open", return_value=stream):
            self.assertEqual(schema.read_bounded_bytes(Path("ignored"), 7), b"{}")
        self.assertEqual(stream.calls, [8])

    def test_review_and_outcome_hard_size_limits_reject_records(self) -> None:
        too_large = valid_review()
        too_large["result"]["findings"] = [valid_finding(consequence="x" * 300, minimal_fix="y" * 300) for _ in range(60)]  # type: ignore[index]
        for index, finding in enumerate(too_large["result"]["findings"]):
            finding["id"] = f"PSDR-{index:03d}"
        with self.assertRaises(schema.EvidenceError):
            schema.validate_review(too_large)
        escaped = [
            {"severity": "BLOCKER", "class": "coverage", "pattern_key": f"escape-{index:03d}-{'x' * 65}", "consequence_category": "escaped-material-defect", "basis": "user-reported"}
            for index in range(50)
        ]
        outcome = valid_outcome(downstream=valid_downstream(escaped_findings=escaped), assessment={"label": "false-ready", "basis": "user-reported", "confidence": "high"})
        with self.assertRaises(schema.EvidenceError):
            schema.validate_outcome(outcome, valid_review())
