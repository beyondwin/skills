from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import io
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from support import completed_review, pending_record

from pre_sdd_review_evidence import cli, reporting, repository, schema, storage


def _finding(
    *,
    finding_id: str = "PSDR-001",
    finding_class: str = "verification-gap",
    pattern_key: str = "build-only-acceptance",
    consequence_category: str = "escaped-material-defect",
    status: str = "repaired",
) -> dict[str, object]:
    return {
        "id": finding_id,
        "severity": "IMPORTANT",
        "class": finding_class,
        "pattern_key": pattern_key,
        "consequence_category": consequence_category,
        "status": status,
        "location": {"path": "docs/plan.md", "locator": "Verification"},
        "evidence_refs": ["docs/plan.md#verification"],
        "consequence": "Content-free bounded finding summary.",
        "minimal_fix": "Add content-free synthetic proof.",
        "repair_pass": 1 if status == "repaired" else None,
    }


def _review(
    *,
    run_number: int,
    verdict: str = "READY",
    execution: str = "full",
    mode: str = "default",
    findings: list[dict[str, object]] | None = None,
    resolution_status: str = "resolved",
    completed_at: str = "2023-01-01T00:00:00Z",
    client: str = "codex",
    degraded_reasons: list[str] | None = None,
) -> dict[str, object]:
    run_id = f"00000000-0000-4000-8000-{run_number:012d}"
    pending = pending_record(
        run_id=run_id,
        status=resolution_status,
        mode=mode,
        started_at="2022-12-31T23:59:00Z",
    )
    pending["client"] = {"id": client, "version": None, "model": None}
    review = completed_review(pending, verdict=verdict, completed_at=completed_at)
    if resolution_status == "design-missing":
        review["target"]["design_initial_sha256"] = None  # type: ignore[index]
        review["freshness"]["design_final_sha256"] = None  # type: ignore[index]
    review_findings = [] if findings is None else findings
    review["result"]["findings"] = review_findings  # type: ignore[index]
    repair_passes = 1 if any(item["status"] == "repaired" for item in review_findings) else 0
    review["result"]["repair_passes"] = repair_passes  # type: ignore[index]
    review["metrics"]["repair_passes"] = repair_passes  # type: ignore[index]
    if verdict == "REVISE" and not any(item["status"] == "unresolved" for item in review_findings):
        unresolved = _finding(status="unresolved")
        review_findings.append(unresolved)
    if execution != "full":
        review["protocol"].update({  # type: ignore[union-attr]
            "execution": execution,
            "reviewer_count": 1 if execution == "degraded" else 0,
            "fresh_reviewer": False,
            "read_only_enforced": False,
            "degraded_reasons": degraded_reasons or (["read-only-unavailable"] if execution == "degraded" else []),
        })
        review["metrics"]["reviewer_count"] = review["protocol"]["reviewer_count"]  # type: ignore[index]
    return schema.validate_review(review)


def _outcome(
    review: dict[str, object],
    *,
    label: str = "good",
    basis: str = "verified-repository-evidence",
    escaped: list[dict[str, object]] | None = None,
    disputed: list[dict[str, object]] | None = None,
    prevented: list[dict[str, object]] | None = None,
    evaluated: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "record_type": "outcome",
        "run_id": review["run_id"],
        "recorded_at": "2023-01-02T00:00:00Z",
        "recorder": {"client": "codex", "version": None, "model": None},
        "downstream": {
            "status": "implementation-completed",
            "plan_hash_matched": True,
            "replan_count": 0,
            "evaluated_finding_ids": evaluated or [],
            "escaped_findings": escaped or [],
            "disputed_findings": disputed or [],
            "prevented_rework": prevented or [],
        },
        "assessment": {"label": label, "basis": basis, "confidence": "high"},
    }


def _escaped(
    *,
    finding_class: str = "verification-gap",
    pattern_key: str = "build-only-acceptance",
    consequence_category: str = "escaped-material-defect",
    basis: str = "verified-repository-evidence",
) -> dict[str, object]:
    return {
        "severity": "IMPORTANT",
        "class": finding_class,
        "pattern_key": pattern_key,
        "consequence_category": consequence_category,
        "basis": basis,
    }


class ReportingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.paths = storage.EvidencePaths.from_home(self.root / "evidence")

    def record(
        self,
        review: dict[str, object],
        outcome: dict[str, object] | None = None,
    ) -> reporting.Record:
        return reporting.Record(review=review, outcome=outcome)

    def persist(
        self,
        review: dict[str, object],
        outcome: dict[str, object] | None = None,
    ) -> None:
        repository.load_or_create_identity(self.paths.home)
        pending = pending_record(
            run_id=str(review["run_id"]),
            started_at=str(review["started_at"]),
            mode=str(review["protocol"]["mode"]),  # type: ignore[index]
        )
        pending["skill"] = review["skill"]
        pending["client"] = review["client"]
        pending["target"] = review["target"]
        storage.create_pending(self.paths, pending)
        storage.finish_review(self.paths, str(review["run_id"]), review)
        if outcome is not None:
            storage.record_outcome(self.paths, str(review["run_id"]), outcome)

    def strand(self, *, run_number: int) -> tuple[dict[str, object], Path, Path, bytes]:
        pending = pending_record(
            run_id=f"00000000-0000-4000-8000-{run_number:012d}"
        )
        with self.assertRaises(RuntimeError):
            storage.create_pending(
                self.paths,
                pending,
                interruption_hook=lambda point, _path: (
                    (_ for _ in ()).throw(RuntimeError("stop"))
                    if point == "pending-fsynced" else None
                ),
            )
        staging = self.paths.runs / f".staging-{pending['run_id']}"
        destination = self.paths.run_directory(
            str(pending["run_id"]), str(pending["started_at"])
        )
        return pending, staging, destination, (staging / ".pending.json").read_bytes()

    def run_cli(self, argv: list[str], stdin: object | None = None) -> tuple[int, object, object]:
        output = io.StringIO()
        error = io.StringIO()
        code = cli.main(
            argv,
            input_stream=io.StringIO("" if stdin is None else json.dumps(stdin)),
            output_stream=output,
            error_stream=error,
            environ={"PRE_SDD_REVIEW_HOME": str(self.paths.home)},
            cwd=self.root,
        )
        return (
            code,
            None if not output.getvalue() else json.loads(output.getvalue()),
            None if not error.getvalue() else json.loads(error.getvalue()),
        )

    def test_summary_keeps_unknown_and_degraded_out_of_verified_rates(self) -> None:
        first = _review(run_number=1)
        second = _review(run_number=2)
        third = _review(run_number=3, execution="degraded")
        fourth = _review(run_number=4, verdict="REVISE", findings=[_finding(status="unresolved")])
        records = [
            self.record(first, _outcome(first)),
            self.record(second, _outcome(second, label="false-ready", escaped=[_escaped()])),
            self.record(third, _outcome(third, basis="agent-inferred")),
            self.record(fourth),
        ]

        summary = reporting.summarize(records)

        self.assertEqual(
            summary["outcome_coverage"],
            {"numerator": 3, "denominator": 4, "interpretation": "insufficient-sample"},
        )
        self.assertEqual(
            summary["verified_false_ready"],
            {"numerator": 1, "denominator": 2, "interpretation": "insufficient-sample"},
        )
        self.assertEqual(summary["missing_outcomes"], {"count": 1, "interpretation": "not_measured"})
        self.assertEqual(summary["protocol_by_client"]["codex"], {"full": 3, "degraded": 1, "blocked": 0, "unknown": 0})

    def test_summary_uses_evaluated_findings_and_structured_prevention_only(self) -> None:
        finding = _finding()
        review = _review(run_number=10, findings=[finding])
        dispute = {
            "finding_id": "PSDR-001",
            "class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "escaped-material-defect",
            "basis": "user-reported",
        }
        prevention = {
            "finding_id": "PSDR-001",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "escaped-material-defect",
            "basis": "verified-repository-evidence",
        }
        result = reporting.summarize([
            self.record(
                review,
                _outcome(
                    review,
                    label="noisy",
                    disputed=[dispute],
                    prevented=[prevention],
                    evaluated=["PSDR-001"],
                    basis="user-reported",
                ),
            )
        ])
        self.assertEqual(result["noisy_findings"], {"numerator": 1, "denominator": 1, "interpretation": "insufficient-sample"})
        self.assertEqual(result["prevented_rework"], {"records": 1, "runs": 1})
        self.assertEqual(result["assessment_boundary"], "observer-supplied-self-improvement-evidence-not-audit-grade")

    def test_candidate_thresholds_use_exact_structured_tuple_and_distinct_runs(self) -> None:
        records: list[reporting.Record] = []
        for number in range(1, 3):
            review = _review(run_number=100 + number)
            records.append(self.record(review, _outcome(review, label="false-ready", escaped=[_escaped()])))
        for number, changed in enumerate(("class", "pattern", "category"), start=3):
            review = _review(run_number=100 + number)
            values = {
                "finding_class": "coverage" if changed == "class" else "verification-gap",
                "pattern_key": "other-pattern" if changed == "pattern" else "build-only-acceptance",
                "consequence_category": "avoidable-rework" if changed == "category" else "escaped-material-defect",
            }
            records.append(self.record(review, _outcome(review, label="false-ready", escaped=[_escaped(**values)])))

        candidates = reporting.select_candidates(records)

        exact = [item for item in candidates if item.kind == "finding-pattern" and item.group == {
            "finding_class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "escaped-material-defect",
        }]
        self.assertEqual(len(exact), 1)
        self.assertEqual(exact[0].source_run_count, 2)
        self.assertEqual(
            exact[0].candidate_id,
            "d99b8db65860e39fff0f53edd2cf6767cb1c4b5739e18e6561db81483c836cd6",
        )
        self.assertNotIn("rank", dataclasses.asdict(exact[0]))
        self.assertNotIn("quality", dataclasses.asdict(exact[0]))

    def test_degraded_and_resolution_candidates_have_discriminated_groups(self) -> None:
        records: list[reporting.Record] = []
        for number in range(3):
            review = _review(
                run_number=200 + number,
                execution="degraded",
                client="cursor",
                degraded_reasons=["read-only-unavailable"],
            )
            records.append(self.record(review))
        for number in range(5):
            records.append(self.record(_review(run_number=210 + number, resolution_status="design-missing")))

        candidates = reporting.select_candidates(records)

        degraded = next(item for item in candidates if item.kind == "degraded-reason")
        resolution = next(item for item in candidates if item.kind == "resolution-failure")
        self.assertEqual(degraded.group, {"client": "cursor", "degraded_reason": "read-only-unavailable"})
        self.assertEqual(resolution.group, {"resolution_status": "design-missing"})
        self.assertNotIn("finding_class", degraded.group)
        self.assertNotIn("pattern_key", resolution.group)

    def test_summary_reports_operational_trigger_finding_and_basis_provenance(self) -> None:
        finding = _finding()
        review = _review(run_number=250, findings=[finding])
        review["protocol"]["conditional_trigger"] = "data-boundary"  # type: ignore[index]
        review["protocol"]["reviewer_count"] = 2  # type: ignore[index]
        review["metrics"]["reviewer_count"] = 2  # type: ignore[index]
        review = schema.validate_review(review)
        result = reporting.summarize([
            self.record(review, _outcome(review, basis="user-reported"))
        ])

        self.assertEqual(result["conditional_trigger_counts"], {"data-boundary": 1})
        self.assertEqual(result["assessment_basis_counts"], {"user-reported": 1})
        self.assertEqual(result["finding_groups"], [{
            "finding_class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "escaped-material-defect",
            "count": 1,
        }])
        self.assertEqual(result["operational_overhead"]["reviewer_count"], {
            "count": 1, "total": 2, "minimum": 2, "maximum": 2,
        })
        self.assertGreater(result["operational_overhead"]["receipt_bytes"]["total"], 0)

    def test_summary_projects_pending_age_classes_without_pending_private_state(self) -> None:
        result = reporting.summarize([], (
            storage.PendingEntry("a", "2026-01-01T00:00:00Z", "resolved", None, None, "active"),
            storage.PendingEntry("b", "2026-01-01T00:00:00Z", "resolved", None, None, "interrupted"),
            storage.PendingEntry("c", "2026-01-01T00:00:00Z", "resolved", None, None, "stale"),
        ))
        self.assertEqual(result["pending_age_classes"], {"active": 1, "interrupted": 1, "stale": 1})
        self.assertNotIn("run_id", json.dumps(result))

    def test_candidate_export_is_exact_blank_create_only_and_symlink_safe(self) -> None:
        review = _review(run_number=300)
        candidate = reporting.select_candidates([
            self.record(review, _outcome(review, label="false-ready", escaped=[_escaped()]))
        ])[0]
        self.paths.home.mkdir(mode=0o700)
        self.paths.exports.mkdir(mode=0o700)

        exported = reporting.export_candidate(candidate, self.paths.exports)

        self.assertEqual(exported, self.paths.exports / candidate.candidate_id)
        self.assertEqual(
            sorted(item.name for item in exported.iterdir()),
            ["candidate.json", "design.md", "expected.json", "plan.md", "repository.json"],
        )
        metadata = json.loads((exported / "candidate.json").read_text(encoding="utf-8"))
        self.assertEqual(set(metadata), {"schema_version", "candidate_id", "kind", "source_run_count", "group", "required_synthetic_files"})
        self.assertEqual((exported / "plan.md").read_text(encoding="utf-8"), "# Plan\n\n**Spec:** ./design.md\n\n## Tasks\n")
        self.assertEqual((exported / "repository.json").read_text(encoding="utf-8"), "{}\n")
        with self.assertRaises(schema.EvidenceError):
            reporting.export_candidate(candidate, self.paths.exports)

        external = self.root / "outside"
        external.mkdir()
        unsafe = self.root / "unsafe-exports"
        unsafe.symlink_to(external, target_is_directory=True)
        with self.assertRaises(schema.EvidenceError):
            reporting.export_candidate(candidate, unsafe)
        self.assertEqual(list(external.iterdir()), [])

    def test_candidate_export_revalidates_discriminated_group_and_identity(self) -> None:
        review = _review(run_number=301)
        candidate = reporting.select_candidates([
            self.record(review, _outcome(review, label="false-ready", escaped=[_escaped()]))
        ])[0]
        self.paths.home.mkdir(mode=0o700)
        self.paths.exports.mkdir(mode=0o700)
        forged = dataclasses.replace(
            candidate,
            group={**candidate.group, "prompt": "private-marker"},
        )

        with self.assertRaisesRegex(schema.EvidenceError, "candidate"):
            reporting.export_candidate(forged, self.paths.exports)

        self.assertEqual(list(self.paths.exports.iterdir()), [])

    def test_prune_preview_digest_confirmation_and_changed_receipt_are_exact(self) -> None:
        first_review = _review(run_number=401)
        second_review = _review(run_number=402, mode="review-only")
        third_review = _review(run_number=403)
        first_outcome = _outcome(first_review)
        second_outcome = _outcome(second_review)
        for review, outcome in ((first_review, first_outcome), (second_review, second_outcome), (third_review, None)):
            self.persist(review, outcome)
        records = reporting.load_records(self.paths)
        cutoff = "2024-01-01T00:00:00Z"

        selection = reporting.preview_prune(records, cutoff, False)

        self.assertEqual([item["run_id"] for item in selection.runs], [first_review["run_id"], second_review["run_id"]])
        self.assertEqual(selection.counts, {"selected": 2, "excluded_without_outcome": 1})
        self.assertEqual(selection.digest, hashlib.sha256(schema.canonical_json_bytes(selection.payload())).hexdigest())
        outcome_path = next(self.paths.runs.glob(f"*/*/{second_review['run_id']}/outcome.json"))
        outcome_path.write_bytes(outcome_path.read_bytes() + b" ")
        with self.assertRaisesRegex(schema.EvidenceError, "selection changed"):
            reporting.confirm_prune(self.paths, selection.payload(), selection.digest)
        self.assertTrue(next(self.paths.runs.glob(f"*/*/{first_review['run_id']}"), None))
        self.assertTrue(next(self.paths.runs.glob(f"*/*/{third_review['run_id']}"), None))

    def test_prune_selection_requires_exact_utc_cutoff_and_closed_fields(self) -> None:
        selection = {
            "schema_version": 1,
            "cutoff": "2024-01-01 00:00:00Z",
            "include_without_outcome": False,
            "runs": [],
            "counts": {"selected": 0, "excluded_without_outcome": 0},
        }
        digest = hashlib.sha256(schema.canonical_json_bytes(selection)).hexdigest()
        with self.assertRaises(schema.EvidenceError):
            reporting.confirm_prune(self.paths, selection, digest)
        selection["unexpected"] = "private-marker"
        with self.assertRaises(schema.EvidenceError):
            reporting.confirm_prune(self.paths, selection, digest)

    def test_confirmed_prune_deletes_only_previewed_runs(self) -> None:
        selected = _review(run_number=410)
        unpreviewed = _review(run_number=411, completed_at="2025-01-01T00:00:00Z")
        self.persist(selected, _outcome(selected))
        self.persist(unpreviewed, _outcome(unpreviewed))
        selection = reporting.preview_prune(reporting.load_records(self.paths), "2024-01-01T00:00:00Z", False)

        deleted = reporting.confirm_prune(self.paths, selection.payload(), selection.digest)

        self.assertEqual(deleted, (str(selected["run_id"]),))
        self.assertIsNone(next(self.paths.runs.glob(f"*/*/{selected['run_id']}"), None))
        self.assertIsNotNone(next(self.paths.runs.glob(f"*/*/{unpreviewed['run_id']}"), None))

    def test_outcome_added_between_preview_and_confirmation_aborts_without_deletion(self) -> None:
        review = _review(run_number=412)
        self.persist(review)
        selection = reporting.preview_prune(
            reporting.load_records(self.paths), "2024-01-01T00:00:00Z", True
        )
        storage.record_outcome(self.paths, str(review["run_id"]), _outcome(review))

        with self.assertRaisesRegex(schema.EvidenceError, "selection changed"):
            reporting.confirm_prune(self.paths, selection.payload(), selection.digest)

        self.assertIsNotNone(next(self.paths.runs.glob(f"*/*/{review['run_id']}"), None))

    def test_missing_previewed_run_is_reported_as_selection_changed(self) -> None:
        review = _review(run_number=413)
        self.persist(review, _outcome(review))
        selection = reporting.preview_prune(
            reporting.load_records(self.paths), "2024-01-01T00:00:00Z", False
        )
        directory = next(self.paths.runs.glob(f"*/*/{review['run_id']}"))
        displaced = self.root / "displaced-run"
        directory.rename(displaced)

        with self.assertRaisesRegex(schema.EvidenceError, "selection changed") as raised:
            reporting.confirm_prune(self.paths, selection.payload(), selection.digest)

        self.assertEqual(raised.exception.code, "selection-changed")
        self.assertTrue(displaced.exists())

    def test_summary_candidates_and_prune_preview_use_bounded_reads_and_do_not_mutate(self) -> None:
        review = _review(run_number=500)
        self.persist(review, _outcome(review, label="false-ready", escaped=[_escaped()]))
        _pending, staging, destination, staged_bytes = self.strand(run_number=501)
        before = self._tree()
        calls: list[tuple[str, int]] = []
        real_reader = schema.read_bounded_json

        def spy(path: Path, limit: int) -> object:
            calls.append((Path(path).name, limit))
            return real_reader(path, limit)

        with mock.patch.object(storage, "read_bounded_json", side_effect=spy):
            for command in (["summary"], ["candidates"], ["prune", "--older-than", "730d", "--dry-run"]):
                code, output, error = self.run_cli(list(command))
                self.assertEqual((code, error), (0, None))
                self.assertIsInstance(output, dict if command[0] != "candidates" else list)
                self.assertEqual(self._tree(), before)
                self.assertTrue(staging.exists())
                self.assertFalse(destination.exists())
                self.assertEqual((staging / ".pending.json").read_bytes(), staged_bytes)
        self.assertIn(("review.json", schema.REVIEW_HARD_LIMIT), calls)
        self.assertIn(("outcome.json", schema.OUTCOME_HARD_LIMIT), calls)

    def test_public_reporting_outputs_exclude_semantic_prose_paths_and_pending_keys(self) -> None:
        marker = "private-marker-never-project"
        finding = _finding()
        finding["location"] = {"path": f"docs/{marker}.md", "locator": marker}
        finding["consequence"] = marker
        finding["minimal_fix"] = marker
        review = _review(run_number=550, findings=[finding])
        record = self.record(review, _outcome(review))
        candidate_review = _review(run_number=551)
        candidate_record = self.record(
            candidate_review,
            _outcome(candidate_review, label="false-ready", escaped=[_escaped()]),
        )

        projections = (
            reporting.summarize([record, candidate_record]),
            [item.payload() for item in reporting.select_candidates([record, candidate_record])],
        )

        rendered = json.dumps(projections, sort_keys=True)
        self.assertNotIn(marker, rendered)
        self.assertNotIn("start_locator_binding", rendered)
        self.assertNotIn("intended_mode", rendered)

    def test_broken_identity_allows_reads_and_preview_but_confirmation_fails_closed(self) -> None:
        review = _review(run_number=600)
        self.persist(review, _outcome(review))
        repository.load_or_create_identity(self.paths.home)
        original_key = self.paths.identity_key.read_bytes()
        original_config = self.paths.config.read_bytes()
        mismatched_config = json.loads(original_config)
        mismatched_config["identity_key_sha256"] = "0" * 64
        _pending, staging, destination, staged_bytes = self.strand(run_number=601)
        cases = (
            ("key-missing", None, original_config, "identity-key-missing"),
            ("key-malformed", b"broken", original_config, "identity-state-invalid"),
            ("fingerprint-mismatch", original_key, schema.canonical_json_bytes(mismatched_config), "identity-state-invalid"),
            ("identity-missing", None, None, "identity-key-missing"),
        )
        expected_preview: object | None = None
        for name, key_bytes, config_bytes, expected_code in cases:
            with self.subTest(name=name):
                if key_bytes is None:
                    self.paths.identity_key.unlink(missing_ok=True)
                else:
                    self.paths.identity_key.write_bytes(key_bytes)
                    if os.name == "posix":
                        self.paths.identity_key.chmod(0o600)
                if config_bytes is None:
                    self.paths.config.unlink(missing_ok=True)
                else:
                    self.paths.config.write_bytes(config_bytes)
                    if os.name == "posix":
                        self.paths.config.chmod(0o600)
                before = self._tree()
                preview: object | None = None
                with mock.patch.object(cli, "_utc_now", return_value="2026-08-30T00:00:00.000000Z"):
                    for command in (
                        ["show", "--run-id", str(review["run_id"])],
                        ["pending"],
                        ["summary"],
                        ["candidates"],
                        ["prune", "--older-than", "730d", "--dry-run"],
                    ):
                        code, output, error = self.run_cli(list(command))
                        self.assertEqual((code, error), (0, None))
                        if command[0] == "prune":
                            preview = output
                        self.assertEqual(self._tree(), before)
                self.assertEqual(storage.load_review(self.paths, str(review["run_id"]))["run_id"], review["run_id"])
                self.assertEqual(storage.load_outcome(self.paths, str(review["run_id"]))["run_id"], review["run_id"])
                if expected_preview is None:
                    expected_preview = preview
                self.assertEqual(preview, expected_preview)
                assert isinstance(preview, dict)
                code, output, error = self.run_cli(
                    ["prune", "--older-than", "730d", "--confirm-selection", str(preview["selection_digest"]), "--from-stdin"],
                    preview["selection"],
                )
                self.assertEqual(code, 2)
                self.assertIsNone(output)
                self.assertEqual(error["error"]["code"], expected_code)
                self.assertEqual(self._tree(), before)
                self.assertTrue(staging.exists())
                self.assertFalse(destination.exists())
                self.assertEqual((staging / ".pending.json").read_bytes(), staged_bytes)
                mutation_commands = (
                    ["start", "--skill-root", str(Path(__file__).resolve().parents[4] / "skills/pre-sdd-review"), "--plan", "missing.md", "--client", "codex", "--mode", "default"],
                    ["finish-review", "--run-id", str(review["run_id"]), "--repo", str(self.root), "--from-stdin"],
                    ["resolve", "--repo", str(self.root), "--plan", "missing.md"],
                    ["record-outcome", "--run-id", str(review["run_id"]), "--repo", str(self.root), "--from-stdin"],
                )
                for command in mutation_commands:
                    command_code, command_output, command_error = self.run_cli(command, {})
                    self.assertEqual(command_code, 2)
                    self.assertIsNone(command_output)
                    self.assertEqual(command_error["error"]["code"], expected_code)
                    self.assertEqual(self._tree(), before)
                doctor_code, doctor_output, doctor_error = self.run_cli(["doctor"])
                self.assertEqual((doctor_code, doctor_error), (0, None))
                self.assertIn(expected_code, {item["code"] for item in doctor_output["issues"]})
        self.paths.identity_key.write_bytes(original_key)
        self.paths.config.write_bytes(original_config)
        if os.name == "posix":
            self.paths.identity_key.chmod(0o600)
            self.paths.config.chmod(0o600)

    def test_candidate_export_and_confirmed_prune_recover_before_mutating(self) -> None:
        review = _review(run_number=620)
        outcome = _outcome(review, label="false-ready", escaped=[_escaped()])
        self.persist(review, outcome)
        candidate = reporting.select_candidates(reporting.load_records(self.paths))[0]
        _pending, staging, destination, _bytes = self.strand(run_number=621)

        code, output, error = self.run_cli(["candidates", "export", candidate.candidate_id])

        self.assertEqual((code, error), (0, None))
        self.assertEqual(output["candidate_id"], candidate.candidate_id)
        self.assertFalse(staging.exists())
        self.assertTrue((destination / ".pending.json").exists())
        self.assertTrue((self.paths.exports / candidate.candidate_id / "candidate.json").exists())

        selection = reporting.preview_prune(reporting.load_records(self.paths), "2024-01-01T00:00:00Z", False)
        _pending2, staging2, destination2, _bytes2 = self.strand(run_number=622)
        deleted = reporting.confirm_prune(self.paths, selection.payload(), selection.digest)
        self.assertEqual(deleted, (str(review["run_id"]),))
        self.assertFalse(staging2.exists())
        self.assertTrue((destination2 / ".pending.json").exists())

    def test_cli_candidate_export_rejects_symlink_without_leaking_target(self) -> None:
        review = _review(run_number=623)
        self.persist(review, _outcome(review, label="false-ready", escaped=[_escaped()]))
        repository.load_or_create_identity(self.paths.home)
        candidate = reporting.select_candidates(reporting.load_records(self.paths))[0]
        external = self.root / "external-private-marker"
        external.mkdir()
        self.paths.exports.symlink_to(external, target_is_directory=True)

        code, output, error = self.run_cli(["candidates", "export", candidate.candidate_id])

        self.assertEqual(code, 2)
        self.assertIsNone(output)
        self.assertNotIn(str(external), json.dumps(error))
        self.assertEqual(list(external.iterdir()), [])

    def test_cli_confirmed_prune_accepts_only_the_exact_stdin_selection(self) -> None:
        review = _review(run_number=624)
        self.persist(review, _outcome(review))
        repository.load_or_create_identity(self.paths.home)
        with mock.patch.object(cli, "_utc_now", return_value="2026-08-30T00:00:00.000000Z"):
            code, preview, error = self.run_cli(["prune", "--older-than", "730d", "--dry-run"])
        self.assertEqual((code, error), (0, None))
        code, output, error = self.run_cli([
            "prune", "--older-than", "730d",
            "--confirm-selection", str(preview["selection_digest"]), "--from-stdin",
        ], preview["selection"])
        self.assertEqual((code, error), (0, None))
        self.assertEqual(output, {"status": "pruned", "run_ids": [review["run_id"]], "count": 1})

    def test_summary_and_candidate_text_formats_are_bounded_human_views(self) -> None:
        review = _review(run_number=625)
        self.persist(review, _outcome(review, label="false-ready", escaped=[_escaped()]))
        for command, phrase in ((["summary", "--format", "text"], "not audit-grade"), (["candidates", "--format", "text"], "finding-pattern")):
            output = io.StringIO()
            error = io.StringIO()
            code = cli.main(
                command,
                input_stream=io.StringIO(), output_stream=output, error_stream=error,
                environ={"PRE_SDD_REVIEW_HOME": str(self.paths.home)}, cwd=self.root,
            )
            self.assertEqual((code, error.getvalue()), (0, ""))
            self.assertIn(phrase, output.getvalue())
            self.assertNotIn("docs/", output.getvalue())

    def test_unresolved_staging_conflict_prevents_deletion_before_locking(self) -> None:
        review = _review(run_number=700)
        self.persist(review, _outcome(review))
        selection = reporting.preview_prune(reporting.load_records(self.paths), "2024-01-01T00:00:00Z", False)
        staging = self.paths.runs / f".staging-{review['run_id']}"
        staging.mkdir(mode=0o700)
        (staging / ".pending.json").write_bytes(b"{broken")
        if os.name == "posix":
            (staging / ".pending.json").chmod(0o600)
        destination = next(self.paths.runs.glob(f"*/*/{review['run_id']}"))
        before = {item.name: item.read_bytes() for item in destination.iterdir()}

        with mock.patch.object(storage, "_acquire_lock", side_effect=AssertionError("lock must not be acquired")):
            with self.assertRaisesRegex(schema.EvidenceError, "selection changed"):
                reporting.confirm_prune(self.paths, selection.payload(), selection.digest)

        self.assertEqual({item.name: item.read_bytes() for item in destination.iterdir()}, before)
        self.assertTrue(staging.exists())

    def test_thousands_of_receipts_remain_linear_without_cache_database_or_index(self) -> None:
        records: list[reporting.Record] = []
        for number in range(3_000):
            review = _review(run_number=10_000 + number)
            outcome = _outcome(review, label="false-ready", escaped=[_escaped()])
            records.append(self.record(review, outcome))
        started = time.monotonic()

        summary = reporting.summarize(records)
        candidates = reporting.select_candidates(records)

        elapsed = time.monotonic() - started
        self.assertEqual(summary["outcome_coverage"]["numerator"], 3_000)
        self.assertEqual(next(item for item in candidates if item.kind == "finding-pattern").source_run_count, 3_000)
        self.assertLess(elapsed, 5.0)

    def _tree(self) -> tuple[tuple[str, str, int | None, bytes], ...]:
        if not self.paths.home.exists():
            return ()
        rows: list[tuple[str, str, int | None, bytes]] = []
        for path in sorted(self.paths.home.rglob("*")):
            relative = path.relative_to(self.paths.home).as_posix()
            info = path.lstat()
            mode = (info.st_mode & 0o777) if os.name == "posix" else None
            if path.is_symlink():
                rows.append((relative, "symlink", mode, os.readlink(path).encode()))
            elif path.is_dir():
                rows.append((relative, "directory", mode, b""))
            else:
                rows.append((relative, "file", mode, path.read_bytes()))
        return tuple(rows)


if __name__ == "__main__":
    unittest.main()
