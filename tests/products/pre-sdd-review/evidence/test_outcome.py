from __future__ import annotations

import copy
import dataclasses
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import completed_review, make_git_repo, pending_record, write

from pre_sdd_review_evidence import reporting, repository, schema, storage


RECORDED_AT = "2026-08-30T12:00:00Z"


def repaired_finding() -> dict[str, object]:
    return {
        "id": "PSDR-001",
        "severity": "BLOCKER",
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


def outcome_for(
    review: dict[str, object],
    *,
    status: str = "implementation-completed",
    evaluated: list[str] | None = None,
    escaped: list[dict[str, object]] | None = None,
    disputed: list[dict[str, object]] | None = None,
    prevented: list[dict[str, object]] | None = None,
    basis: str = "verified-repository-evidence",
    confidence: str = "high",
    label: str | None = None,
) -> dict[str, object]:
    downstream = {
        "status": status,
        "plan_hash_matched": True,
        "replan_count": 0,
        "evaluated_finding_ids": [] if evaluated is None else evaluated,
        "escaped_findings": [] if escaped is None else escaped,
        "disputed_findings": [] if disputed is None else disputed,
        "prevented_rework": [] if prevented is None else prevented,
    }
    return {
        "schema_version": 1,
        "record_type": "outcome",
        "run_id": review["run_id"],
        "recorded_at": RECORDED_AT,
        "recorder": {"client": "codex", "version": None, "model": None},
        "downstream": downstream,
        "assessment": {
            "label": (
                "abandoned"
                if label is None and status in {"implementation-abandoned", "cancelled"}
                else "good"
                if label is None
                else label
            ),
            "basis": basis,
            "confidence": confidence,
        },
    }


class OutcomeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.paths = storage.EvidencePaths.from_home(self.workspace / "evidence")
        self.repo = make_git_repo(self.workspace)
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** `docs/design.md`\n")
        write(self.repo / "docs/design.md", "# Design\n")
        self.key = repository.load_or_create_identity(self.paths.home)

    def finalize(
        self, *, verdict: str = "READY", finding: dict[str, object] | None = None
    ) -> dict[str, object]:
        pending = pending_record()
        pending["target"] = dataclasses.asdict(
            repository.resolve_target(self.repo, Path("docs/plan.md"), self.key)
        )
        handle = storage.create_pending(self.paths, pending)
        review = completed_review(pending, verdict=verdict)
        if finding is not None:
            review["result"]["findings"] = [finding]  # type: ignore[index]
            review["result"]["repair_passes"] = 1  # type: ignore[index]
            review["metrics"]["repair_passes"] = 1  # type: ignore[index]
        storage.finish_review(self.paths, handle.run_id, review)
        return review

    def test_resolve_has_exact_matched_stale_ambiguous_and_not_found_states(self) -> None:
        first = self.finalize()
        matched = reporting.resolve_review(self.paths, self.repo, Path("docs/plan.md"))
        self.assertEqual(matched.status, "matched")
        self.assertEqual(matched.run_id, first["run_id"])
        self.assertEqual(matched.candidate_run_ids, (str(first["run_id"]),))

        write(self.repo / "docs/plan.md", "# Changed\n\n**Spec:** `docs/design.md`\n")
        stale = reporting.resolve_review(self.paths, self.repo, Path("docs/plan.md"))
        self.assertEqual(stale.status, "stale")
        self.assertIsNone(stale.run_id)

        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** `docs/design.md`\n")
        second = self.finalize()
        ambiguous = reporting.resolve_review(
            self.paths, self.repo, Path("docs/plan.md")
        )
        self.assertEqual(ambiguous.status, "ambiguous")
        self.assertIsNone(ambiguous.run_id)
        self.assertEqual(
            set(ambiguous.candidate_run_ids),
            {str(first["run_id"]), str(second["run_id"])},
        )

        other_workspace = self.workspace / "other"
        other_workspace.mkdir()
        other_repo = make_git_repo(other_workspace)
        write(other_repo / "docs/plan.md", "# Plan\n\n**Spec:** `docs/design.md`\n")
        write(other_repo / "docs/design.md", "# Design\n")
        missing = reporting.resolve_review(
            self.paths, other_repo, Path("docs/plan.md")
        )
        self.assertEqual(missing.status, "not-found")
        self.assertEqual(missing.candidate_run_ids, ())

    def test_resolve_uses_validated_reviews_and_shared_bounded_reader(self) -> None:
        review = self.finalize()
        run_dir = next(self.paths.runs.glob(f"*/*/{review['run_id']}"))
        corrupt = run_dir.parent / "00000000-0000-4000-8000-000000000000"
        corrupt.mkdir(mode=0o700)
        (corrupt / "review.json").write_bytes(b"{broken")
        if os.name == "posix":
            (corrupt / "review.json").chmod(0o600)
        calls: list[tuple[Path, int]] = []
        real_reader = schema.read_bounded_bytes

        def spy(path: Path, limit: int) -> bytes:
            calls.append((Path(path), limit))
            return real_reader(path, limit)

        with mock.patch.object(storage, "read_bounded_bytes", side_effect=spy):
            result = reporting.resolve_review(
                self.paths, self.repo, Path("docs/plan.md")
            )
        self.assertEqual(result.status, "matched")
        self.assertTrue(any(path.name == "review.json" for path, _ in calls))

    def test_all_terminal_statuses_and_confidences_validate(self) -> None:
        review = self.finalize()
        for status in sorted(schema.DOWNSTREAM_STATUSES):
            for confidence in sorted(schema.CONFIDENCES):
                with self.subTest(status=status, confidence=confidence):
                    record = outcome_for(
                        review, status=status, confidence=confidence,
                        basis="agent-inferred",
                    )
                    self.assertEqual(
                        schema.validate_outcome(record, review)["assessment"]["confidence"],
                        confidence,
                    )

    def test_structured_escape_dispute_and_prevention_have_exact_links(self) -> None:
        review = self.finalize(finding=repaired_finding())
        escaped = [{
            "severity": "BLOCKER", "class": "coverage",
            "pattern_key": "missing-acceptance",
            "consequence_category": "escaped-material-defect",
            "basis": "user-reported",
        }]
        false_ready = outcome_for(
            review, escaped=escaped, basis="user-reported", label="false-ready"
        )
        self.assertEqual(
            schema.validate_outcome(false_ready, review)["assessment"]["label"],
            "false-ready",
        )

        disputed = [{
            "finding_id": "PSDR-001", "class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework",
            "basis": "agent-observed",
        }]
        noisy = outcome_for(
            review, evaluated=["PSDR-001"], disputed=disputed,
            basis="agent-observed", label="noisy",
        )
        self.assertEqual(schema.validate_outcome(noisy, review)["assessment"]["label"], "noisy")

        prevented = [{
            "finding_id": "PSDR-001", "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework",
            "basis": "verified-repository-evidence",
        }]
        prevention = outcome_for(
            review, evaluated=["PSDR-001"], prevented=prevented,
            basis="verified-repository-evidence", label="prevented-rework",
        )
        self.assertEqual(
            schema.validate_outcome(prevention, review)["assessment"]["label"],
            "prevented-rework",
        )

    def test_invalid_links_copies_prevention_status_and_basis_promotion_fail(self) -> None:
        finding = repaired_finding()
        review = self.finalize(finding=finding)
        base_prevention = {
            "finding_id": "PSDR-001", "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework", "basis": "agent-observed",
        }
        cases: list[dict[str, object]] = []
        cases.append(outcome_for(review, evaluated=["PSDR-999"]))
        mismatched = copy.deepcopy(base_prevention); mismatched["pattern_key"] = "wrong"
        cases.append(outcome_for(
            review, evaluated=["PSDR-001"], prevented=[mismatched],
            basis="agent-observed", label="prevented-rework",
        ))
        promotion = outcome_for(
            review, evaluated=["PSDR-001"], prevented=[base_prevention],
            basis="verified-repository-evidence", label="prevented-rework",
        )
        cases.append(promotion)
        for record in cases:
            with self.subTest(record=record["downstream"]), self.assertRaises(schema.EvidenceError):
                schema.validate_outcome(record, review)

        unresolved = repaired_finding()
        unresolved.update({"status": "unresolved", "repair_pass": None})
        revise = self.finalize(verdict="REVISE", finding=unresolved)
        invalid = outcome_for(
            revise, evaluated=["PSDR-001"], prevented=[base_prevention],
            basis="agent-observed", label="prevented-rework",
        )
        with self.assertRaisesRegex(schema.EvidenceError, "repaired"):
            schema.validate_outcome(invalid, revise)

    def test_every_dispute_and_prevention_copy_field_has_an_isolated_mismatch_row(self) -> None:
        review = self.finalize(finding=repaired_finding())
        dispute = {
            "finding_id": "PSDR-001", "class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework", "basis": "agent-observed",
        }
        prevention = {
            "finding_id": "PSDR-001", "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework", "basis": "agent-observed",
        }
        rows = (
            ("disputed", dispute, "class", "coverage"),
            ("disputed", dispute, "pattern_key", "wrong-pattern"),
            ("disputed", dispute, "consequence_category", "false-block"),
            ("prevented", prevention, "pattern_key", "wrong-pattern"),
            ("prevented", prevention, "consequence_category", "false-block"),
        )
        for kind, original, field, value in rows:
            changed = copy.deepcopy(original)
            changed[field] = value
            record = outcome_for(
                review,
                evaluated=["PSDR-001"],
                disputed=[changed] if kind == "disputed" else None,
                prevented=[changed] if kind == "prevented" else None,
                basis="agent-observed",
                label="noisy" if kind == "disputed" else "prevented-rework",
            )
            with self.subTest(kind=kind, field=field), self.assertRaisesRegex(
                schema.EvidenceError, "copy|match"
            ):
                schema.validate_outcome(record, review)

    def test_non_ready_escape_is_durably_inconclusive_until_matching_dispute(self) -> None:
        unresolved = repaired_finding()
        unresolved.update({"status": "unresolved", "repair_pass": None})
        escaped = [{
            "severity": "IMPORTANT", "class": "coverage",
            "pattern_key": "downstream-escape",
            "consequence_category": "escaped-material-defect",
            "basis": "verified-repository-evidence",
        }]

        first_review = self.finalize(verdict="REVISE", finding=unresolved)
        inconclusive = outcome_for(
            first_review,
            evaluated=["PSDR-001"],
            escaped=escaped,
            basis="agent-inferred",
            label="inconclusive",
        )
        storage.record_outcome(
            self.paths, str(first_review["run_id"]), inconclusive
        )
        self.assertEqual(
            storage.load_outcome(
                self.paths, str(first_review["run_id"])
            )["assessment"]["label"],
            "inconclusive",
        )

        second_review = self.finalize(verdict="REVISE", finding=unresolved)
        dispute = [{
            "finding_id": "PSDR-001", "class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework",
            "basis": "user-reported",
        }]
        noisy = outcome_for(
            second_review,
            evaluated=["PSDR-001"],
            escaped=escaped,
            disputed=dispute,
            basis="user-reported",
            label="noisy",
        )
        storage.record_outcome(self.paths, str(second_review["run_id"]), noisy)
        self.assertEqual(
            storage.load_outcome(
                self.paths, str(second_review["run_id"])
            )["assessment"]["label"],
            "noisy",
        )

    def test_direct_bounded_json_normalizes_large_integer_value_error(self) -> None:
        path = self.workspace / "large-integer.json"
        path.write_bytes(b'{"value":' + b"1" * 5000 + b"}")
        self.assertLess(path.stat().st_size, schema.OUTCOME_HARD_LIMIT)
        with self.assertRaises(schema.EvidenceError) as raised:
            schema.read_bounded_json(path, schema.OUTCOME_HARD_LIMIT)
        self.assertEqual(raised.exception.code, "invalid-json")

    def test_outcome_run_id_must_be_canonical_and_match_the_review(self) -> None:
        review = self.finalize()
        for run_id in (
            "not-a-uuid",
            "00000000-0000-4000-8000-000000000000",
        ):
            record = outcome_for(review)
            record["run_id"] = run_id
            with self.subTest(run_id=run_id), self.assertRaises(schema.EvidenceError):
                schema.validate_outcome(record, review)

    def test_assessment_basis_uses_all_sufficient_triggering_records(self) -> None:
        review = self.finalize()
        escaped = [
            {
                "severity": "BLOCKER", "class": "coverage",
                "pattern_key": "material-escape",
                "consequence_category": "escaped-material-defect",
                "basis": "agent-observed",
            },
            {
                "severity": "IMPORTANT", "class": "coverage",
                "pattern_key": "important-escape",
                "consequence_category": "other",
                "basis": "verified-repository-evidence",
            },
        ]
        record = outcome_for(
            review, escaped=escaped, basis="verified-repository-evidence",
            label="false-ready",
        )
        self.assertEqual(
            schema.validate_outcome(record, review)["assessment"]["basis"],
            "verified-repository-evidence",
        )

    def test_important_escape_and_dispute_are_both_material(self) -> None:
        finding = repaired_finding()
        finding["severity"] = "IMPORTANT"
        review = self.finalize(finding=finding)
        dispute = [{
            "finding_id": "PSDR-001", "class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework", "basis": "user-reported",
        }]
        downstream = outcome_for(
            review, evaluated=["PSDR-001"], disputed=dispute,
            basis="user-reported", label="noisy",
        )
        self.assertEqual(
            schema.validate_outcome(downstream, review)["assessment"]["label"],
            "noisy",
        )
        escaped = [{
            "severity": "IMPORTANT", "class": "coverage",
            "pattern_key": "important-escape",
            "consequence_category": "escaped-material-defect",
            "basis": "user-reported",
        }]
        false_ready = outcome_for(
            review, escaped=escaped, basis="user-reported", label="false-ready"
        )
        self.assertEqual(
            schema.validate_outcome(false_ready, review)["assessment"]["label"],
            "false-ready",
        )

    def test_outcome_is_create_only_bounded_and_review_stays_immutable(self) -> None:
        review = self.finalize(finding=repaired_finding())
        record = outcome_for(review, evaluated=["PSDR-001"])
        review_before = storage.load_review(self.paths, str(review["run_id"]))
        first = storage.record_outcome(self.paths, str(review["run_id"]), record)
        self.assertEqual(
            storage.load_outcome(self.paths, str(review["run_id"])),
            schema.validate_outcome(record, review),
        )
        self.assertEqual(storage.load_review(self.paths, str(review["run_id"])), review_before)
        with self.assertRaisesRegex(schema.EvidenceError, "already recorded"):
            storage.record_outcome(self.paths, str(review["run_id"]), record)
        self.assertEqual(first.path.read_bytes(), schema.canonical_json_bytes(record))

        calls: list[tuple[Path, int]] = []
        real_reader = schema.read_bounded_bytes
        with mock.patch.object(
            storage,
            "read_bounded_bytes",
            side_effect=lambda path, limit: (
                calls.append((Path(path), limit)), real_reader(path, limit)
            )[1],
        ):
            storage.load_outcome(self.paths, str(review["run_id"]))
        self.assertIn((first.path, schema.OUTCOME_HARD_LIMIT), calls)

    def test_outcome_publication_race_never_overwrites_winner(self) -> None:
        review = self.finalize()
        record = outcome_for(review)
        run_dir = next(self.paths.runs.glob(f"*/*/{review['run_id']}"))
        winner = b'{"winner":true}\n'

        def race(point: str, _path: Path) -> None:
            if point == "outcome-temp-fsynced":
                (run_dir / "outcome.json").write_bytes(winner)

        with self.assertRaisesRegex(schema.EvidenceError, "already recorded"):
            storage.record_outcome(
                self.paths, str(review["run_id"]), record,
                interruption_hook=race,
            )
        self.assertEqual((run_dir / "outcome.json").read_bytes(), winner)
        self.assertFalse((run_dir / ".write.lock").exists())
        self.assertFalse(any(path.name.endswith(".tmp") for path in run_dir.iterdir()))

    def test_outcome_rejects_unknown_sensitive_content_fields(self) -> None:
        review = self.finalize()
        for field in ("prompt", "transcript", "credential", "path", "source"):
            record = outcome_for(review)
            record["downstream"][field] = "do-not-store"  # type: ignore[index]
            with self.subTest(field=field), self.assertRaises(schema.EvidenceError):
                schema.validate_outcome(record, review)


if __name__ == "__main__":
    unittest.main()
