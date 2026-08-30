from __future__ import annotations

import io
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import make_git_repo, pending_record, write

from pre_sdd_review_evidence import cli
from pre_sdd_review_evidence import storage


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.home = self.workspace / "evidence"
        self.repo = make_git_repo(self.workspace)
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** `docs/design.md`\n")
        write(self.repo / "docs/design.md", "# Design\n")
        self.skill = Path(__file__).resolve().parents[4] / "skills/pre-sdd-review"

    def run_cli(
        self, argv: list[str], stdin: str = "", *, cwd: Path | None = None
    ) -> tuple[int, str, str]:
        output = io.StringIO()
        error = io.StringIO()
        code = cli.main(
            argv,
            input_stream=io.StringIO(stdin), output_stream=output, error_stream=error,
            environ={"PRE_SDD_REVIEW_HOME": str(self.home)}, cwd=self.repo if cwd is None else cwd,
        )
        return code, output.getvalue(), error.getvalue()

    def start(self, *, mode: str = "default") -> dict[str, object]:
        code, output, error = self.run_cli([
            "start", "--skill-root", str(self.skill), "--plan", "docs/plan.md",
            "--client", "cursor", "--mode", mode,
        ])
        self.assertEqual((code, error), (0, ""))
        return json.loads(output)

    def semantic(self, *, mode: str = "default", verdict: str = "READY") -> dict[str, object]:
        return {
            "mode": mode, "execution": "full", "reviewer_count": 1,
            "fresh_reviewer": True, "read_only_enforced": True,
            "conditional_trigger": None, "degraded_reasons": [],
            "verdict": verdict, "block_reason": None, "review_passes": 1,
            "repair_passes": 0, "findings": [], "token_usage": None,
        }

    def outcome_semantic(self) -> dict[str, object]:
        return {
            "recorder": {"client": "codex", "version": None, "model": None},
            "status": "implementation-completed", "replan_count": 0,
            "evaluated_finding_ids": [], "escaped_findings": [],
            "disputed_findings": [], "prevented_rework": [],
            "basis": "agent-inferred", "confidence": "medium",
        }

    def finalized(self) -> dict[str, object]:
        started = self.start()
        code, _output, error = self.run_cli([
            "finish-review", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ], json.dumps(self.semantic()))
        self.assertEqual((code, error), (0, ""))
        return started

    def test_version_is_exact_and_does_not_touch_home(self) -> None:
        code, output, error = self.run_cli(["--version"])
        self.assertEqual(code, 0)
        self.assertEqual(output, '{"cli_version":"1.0.0","schema_version":1,"skill_name":"pre-sdd-review"}\n')
        self.assertEqual(error, "")
        self.assertFalse(self.home.exists())
        code, output, error = self.run_cli(["--version", "start"])
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")

    def test_start_then_finish_from_stdin_has_exact_status_objects(self) -> None:
        started = self.start()
        run_id = started["run_id"]
        self.assertEqual(started, {
            "status": "started", "run_id": run_id, "resolution_status": "resolved",
            "plan_path": "docs/plan.md", "design_path": "docs/design.md",
        })
        code, output, error = self.run_cli([
            "finish-review", "--run-id", str(run_id), "--repo", str(self.repo), "--from-stdin"
        ], json.dumps(self.semantic()))
        result = json.loads(output)
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(result, {"status": "recorded", "run_id": run_id, "sha256": result["sha256"]})

    def test_finish_hashes_persisted_design_path_when_plan_spec_changes(self) -> None:
        first_design = b"# Original design\n"
        second_design = b"# Replacement design\n"
        (self.repo / "docs/design-a.md").write_bytes(first_design)
        (self.repo / "docs/design-b.md").write_bytes(second_design)
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design-a.md\n")
        started = self.start()
        self.assertEqual(started["design_path"], "docs/design-a.md")
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design-b.md\n")

        code, output, error = self.run_cli([
            "finish-review", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ], json.dumps(self.semantic()))

        self.assertEqual((code, error), (0, ""))
        self.assertEqual(json.loads(output)["status"], "recorded")
        review = json.loads(self.run_cli(["show", "--run-id", str(started["run_id"])])[1])
        self.assertEqual(
            review["freshness"]["design_final_sha256"],
            hashlib.sha256(first_design).hexdigest(),
        )
        self.assertNotEqual(
            review["freshness"]["design_final_sha256"],
            hashlib.sha256(second_design).hexdigest(),
        )

    def test_argument_and_stdin_semantics_share_one_normalization_path(self) -> None:
        first = self.start()
        second = self.start()
        scalar = [
            "finish-review", "--run-id", str(first["run_id"]), "--repo", str(self.repo),
            "--mode", "default", "--execution", "full", "--reviewer-count", "1",
            "--fresh-reviewer", "true", "--read-only-enforced", "true",
            "--verdict", "READY", "--review-passes", "1", "--repair-passes", "0",
        ]
        self.assertEqual(self.run_cli(scalar)[0], 0)
        self.assertEqual(self.run_cli([
            "finish-review", "--run-id", str(second["run_id"]), "--repo", str(self.repo), "--from-stdin"
        ], json.dumps(self.semantic()))[0], 0)
        first_review = json.loads(self.run_cli(["show", "--run-id", str(first["run_id"])])[1])
        second_review = json.loads(self.run_cli(["show", "--run-id", str(second["run_id"])])[1])
        for record in (first_review, second_review):
            for key in ("run_id", "started_at", "completed_at"):
                record.pop(key)
            record["metrics"].pop("elapsed_ms")
            record["metrics"].pop("recorder_elapsed_ms")
        self.assertEqual(first_review, second_review)

    def test_finish_public_retry_uses_semantics_not_regenerated_times(self) -> None:
        started = self.start()
        command = [
            "finish-review", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ]
        first_code, first_output, first_error = self.run_cli(
            command, json.dumps(self.semantic())
        )
        self.assertEqual((first_code, first_error), (0, ""))
        first = json.loads(first_output)

        second_code, second_output, second_error = self.run_cli(
            command, json.dumps(self.semantic())
        )

        self.assertEqual((second_code, second_error), (0, ""))
        self.assertEqual(json.loads(second_output), first)
        other_workspace = self.workspace / "retry-other"
        other_workspace.mkdir()
        other_repo = make_git_repo(other_workspace)
        wrong_repo_command = command.copy()
        wrong_repo_command[wrong_repo_command.index(str(self.repo))] = str(other_repo)
        code, output, error = self.run_cli(
            wrong_repo_command, json.dumps(self.semantic())
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "wrong-repository")
        conflict = self.semantic()
        conflict["review_passes"] = 2
        code, output, error = self.run_cli(command, json.dumps(conflict))
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "already-finalized")

    def test_finish_retry_reconciles_final_beside_pending_after_interruption(self) -> None:
        started = self.start()
        command = [
            "finish-review", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ]
        real_finish = storage.finish_review

        def interrupted(paths: storage.EvidencePaths, run_id: str, review: object) -> object:
            return real_finish(
                paths,
                run_id,
                review,
                interruption_hook=lambda point, _path: (
                    (_ for _ in ()).throw(RuntimeError("interrupted"))
                    if point == "review-published"
                    else None
                ),
            )

        with mock.patch.object(cli.storage, "finish_review", side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                self.run_cli(command, json.dumps(self.semantic()))
        run_dir = next(self.home.glob(f"runs/*/*/{started['run_id']}"))
        self.assertTrue((run_dir / "review.json").exists())
        self.assertTrue((run_dir / ".pending.json").exists())

        code, output, error = self.run_cli(command, json.dumps(self.semantic()))

        self.assertEqual((code, error), (0, ""))
        self.assertEqual(json.loads(output)["status"], "recorded")
        self.assertFalse((run_dir / ".pending.json").exists())

    def test_mixed_or_oversized_input_and_mode_mismatch_fail(self) -> None:
        started = self.start(mode="review-only")
        mixed = [
            "finish-review", "--run-id", str(started["run_id"]), "--repo", str(self.repo),
            "--from-stdin", "--mode", "review-only",
        ]
        code, output, error = self.run_cli(mixed, json.dumps(self.semantic(mode="review-only")))
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertIn("error", json.loads(error))
        mismatch = dict(self.semantic())
        code, _, error = self.run_cli([
            "finish-review", "--run-id", str(started["run_id"]), "--repo", str(self.repo), "--from-stdin"
        ], json.dumps(mismatch))
        self.assertNotEqual(code, 0)
        self.assertIn("mode", json.loads(error)["error"]["message"])
        code, _, error = self.run_cli([
            "finish-review", "--run-id", str(started["run_id"]), "--repo", str(self.repo), "--from-stdin"
        ], "{" + "x" * (33 * 1024))
        self.assertNotEqual(code, 0)
        self.assertEqual(json.loads(error)["error"]["code"], "record-too-large")

    def test_non_git_start_and_finish_require_same_private_locator_binding(self) -> None:
        nongit = self.workspace / "nongit"
        nongit.mkdir()
        output = io.StringIO(); error = io.StringIO()
        code = cli.main([
            "start", "--skill-root", str(self.skill), "--plan", "docs/plan.md",
            "--client", "cursor", "--mode", "default",
        ], input_stream=io.StringIO(), output_stream=output, error_stream=error,
            environ={"PRE_SDD_REVIEW_HOME": str(self.home)}, cwd=nongit)
        started = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(started["resolution_status"], "not-git-repository")
        self.assertIsNone(started["plan_path"]); self.assertIsNone(started["design_path"])
        semantic = self.semantic(verdict="BLOCKED")
        semantic.update({"execution": "blocked", "reviewer_count": 0, "fresh_reviewer": False,
                         "read_only_enforced": False, "block_reason": "repository-unavailable"})
        code, _, error_text = self.run_cli([
            "finish-review", "--run-id", str(started["run_id"]), "--repo", str(self.repo), "--from-stdin"
        ], json.dumps(semantic))
        self.assertNotEqual(code, 0)
        self.assertEqual(json.loads(error_text)["error"]["code"], "wrong-repository")
        output = io.StringIO(); error = io.StringIO()
        code = cli.main([
            "finish-review", "--run-id", str(started["run_id"]), "--repo", str(nongit), "--from-stdin"
        ], input_stream=io.StringIO(json.dumps(semantic)), output_stream=output, error_stream=error,
            environ={"PRE_SDD_REVIEW_HOME": str(self.home)}, cwd=nongit)
        self.assertEqual((code, error.getvalue()), (0, ""))
        receipt = json.loads(self.run_cli(["show", "--run-id", str(started["run_id"])])[1])
        serialized = json.dumps(receipt)
        self.assertNotIn("start_locator_binding", serialized)
        self.assertNotIn(str(nongit), serialized)

    def test_clean_final_non_git_retry_fails_closed_for_same_and_different_locator(self) -> None:
        nongit = self.workspace / "nongit-clean-retry"
        other_nongit = self.workspace / "nongit-clean-retry-other"
        nongit.mkdir()
        other_nongit.mkdir()
        code, output, error = self.run_cli([
            "start", "--skill-root", str(self.skill), "--plan", "docs/plan.md",
            "--client", "cursor", "--mode", "default",
        ], cwd=nongit)
        self.assertEqual((code, error), (0, ""))
        started = json.loads(output)
        semantic = self.semantic(verdict="BLOCKED")
        semantic.update({
            "execution": "blocked", "reviewer_count": 0,
            "fresh_reviewer": False, "read_only_enforced": False,
            "block_reason": "repository-unavailable",
        })
        command = [
            "finish-review", "--run-id", str(started["run_id"]),
            "--repo", str(nongit), "--from-stdin",
        ]
        code, _output, error = self.run_cli(
            command, json.dumps(semantic), cwd=nongit
        )
        self.assertEqual((code, error), (0, ""))

        for label, locator in (("same", nongit), ("different", other_nongit)):
            with self.subTest(locator=label):
                retry = command.copy()
                retry[retry.index(str(nongit))] = str(locator)
                code, output, error = self.run_cli(
                    retry, json.dumps(semantic), cwd=nongit
                )
                self.assertNotEqual(code, 0)
                self.assertEqual(output, "")
                self.assertEqual(
                    json.loads(error)["error"]["code"], "wrong-repository"
                )

    def test_interrupted_final_non_git_retry_authenticates_pending_locator(self) -> None:
        nongit = self.workspace / "nongit-interrupted-retry"
        other_nongit = self.workspace / "nongit-interrupted-retry-other"
        nongit.mkdir()
        other_nongit.mkdir()
        code, output, error = self.run_cli([
            "start", "--skill-root", str(self.skill), "--plan", "docs/plan.md",
            "--client", "cursor", "--mode", "default",
        ], cwd=nongit)
        self.assertEqual((code, error), (0, ""))
        started = json.loads(output)
        semantic = self.semantic(verdict="BLOCKED")
        semantic.update({
            "execution": "blocked", "reviewer_count": 0,
            "fresh_reviewer": False, "read_only_enforced": False,
            "block_reason": "repository-unavailable",
        })
        command = [
            "finish-review", "--run-id", str(started["run_id"]),
            "--repo", str(nongit), "--from-stdin",
        ]
        real_finish = storage.finish_review

        def interrupted(paths: storage.EvidencePaths, run_id: str, review: object) -> object:
            return real_finish(
                paths, run_id, review,
                interruption_hook=lambda point, _path: (
                    (_ for _ in ()).throw(RuntimeError("interrupted"))
                    if point == "review-published" else None
                ),
            )

        with mock.patch.object(cli.storage, "finish_review", side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                self.run_cli(command, json.dumps(semantic), cwd=nongit)
        run_dir = next(self.home.glob(f"runs/*/*/{started['run_id']}"))
        self.assertTrue((run_dir / ".pending.json").exists())
        wrong = command.copy()
        wrong[wrong.index(str(nongit))] = str(other_nongit)
        code, output, error = self.run_cli(
            wrong, json.dumps(semantic), cwd=nongit
        )
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "wrong-repository")
        self.assertTrue((run_dir / ".pending.json").exists())

        code, output, error = self.run_cli(
            command, json.dumps(semantic), cwd=nongit
        )
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(json.loads(output)["status"], "recorded")
        self.assertFalse((run_dir / ".pending.json").exists())

    def test_private_locator_binding_never_leaks_from_pending_consumers_or_final(self) -> None:
        nongit = self.workspace / "DISTINCTIVE-RAW-LOCATOR-MARKER"
        nongit.mkdir()
        code, output, error = self.run_cli([
            "start", "--skill-root", str(self.skill), "--plan", "docs/plan.md",
            "--client", "cursor", "--mode", "default",
        ], cwd=nongit)
        self.assertEqual((code, error), (0, ""))
        started = json.loads(output)
        pending_path = next(self.home.glob("runs/*/*/*/.pending.json"))
        pending = json.loads(pending_path.read_text(encoding="utf-8"))
        binding = pending["start_locator_binding"]
        self.assertNotIn(str(nongit).encode(), pending_path.read_bytes())
        self.assertNotIn("locator", {key for key in pending if key != "start_locator_binding"})
        for command in (["pending"], ["doctor"]):
            code, public, error = self.run_cli(command, cwd=nongit)
            self.assertEqual((code, error), (0, ""))
            self.assertNotIn(str(nongit), public)
            self.assertNotIn(str(binding), public)
            self.assertNotIn("start_locator_binding", public)
        code, output, error = self.run_cli([
            "abandon", "--run-id", str(started["run_id"]), "--reason", "client-interrupted"
        ], cwd=nongit)
        self.assertEqual((code, error), (0, ""))
        review_path = next(self.home.glob("runs/*/*/*/review.json"))
        final = review_path.read_bytes()
        self.assertNotIn(str(nongit).encode(), final)
        self.assertNotIn(str(binding).encode(), final)
        self.assertNotIn(b"start_locator_binding", final)

    def test_start_failed_resolution_statuses_have_exact_public_shape(self) -> None:
        cases: list[tuple[str, str, str | None, str | None]] = []
        cases.append(("plan-missing", "docs/missing.md", "docs/missing.md", None))
        write(self.repo / "docs/no-spec.md", "# Plan\n")
        cases.append(("spec-field-missing", "docs/no-spec.md", "docs/no-spec.md", None))
        write(self.repo / "docs/bad-spec.md", "**Spec:** docs/design.md trailing\n")
        cases.append(("spec-path-invalid", "docs/bad-spec.md", "docs/bad-spec.md", None))
        write(self.repo / "docs/missing-design.md", "**Spec:** docs/absent.md\n")
        cases.append(("design-missing", "docs/missing-design.md", "docs/missing-design.md", "docs/absent.md"))
        outside = self.workspace / "outside-plan.md"
        write(outside, "**Spec:** docs/design.md\n")
        cases.append(("outside-repository", str(outside), None, None))
        for expected_status, plan, expected_plan, expected_design in cases:
            with self.subTest(expected_status=expected_status):
                code, output, error = self.run_cli([
                    "start", "--skill-root", str(self.skill), "--plan", plan,
                    "--client", "cursor", "--mode", "default",
                ])
                self.assertEqual((code, error), (0, ""))
                started = json.loads(output)
                run_id = started["run_id"]
                self.assertEqual(started, {
                    "status": "started", "run_id": run_id,
                    "resolution_status": expected_status,
                    "plan_path": expected_plan, "design_path": expected_design,
                })

    def test_pending_abandon_show_and_doctor_are_public_and_non_mutating(self) -> None:
        started = self.start()
        code, output, error = self.run_cli(["pending"])
        self.assertEqual((code, error), (0, ""))
        pending = json.loads(output)
        self.assertEqual(set(pending), {"status", "runs"})
        self.assertNotIn("start_locator_binding", output)
        code, output, error = self.run_cli([
            "abandon", "--run-id", str(started["run_id"]), "--reason", "client-interrupted"
        ])
        abandoned = json.loads(output)
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(abandoned, {"status": "abandoned", "run_id": started["run_id"], "sha256": abandoned["sha256"]})
        shown = json.loads(self.run_cli(["show", "--run-id", str(started["run_id"])])[1])
        self.assertEqual(shown["result"]["completion_reason"], "client-interrupted")
        code, output, error = self.run_cli(["doctor"])
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(set(json.loads(output)), {"status", "issues"})

    def test_resolve_and_record_outcome_stdin_have_exact_public_shapes(self) -> None:
        started = self.finalized()
        code, output, error = self.run_cli([
            "resolve", "--repo", str(self.repo), "--plan", "docs/plan.md",
        ])
        self.assertEqual((code, error), (0, ""))
        resolved = json.loads(output)
        self.assertEqual(resolved["status"], "matched")
        self.assertEqual(resolved["run_id"], started["run_id"])
        self.assertEqual(resolved["candidate_run_ids"], [started["run_id"]])

        code, output, error = self.run_cli([
            "record-outcome", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ], json.dumps(self.outcome_semantic()))
        recorded = json.loads(output)
        self.assertEqual((code, error), (0, ""))
        self.assertEqual(recorded, {
            "status": "recorded", "run_id": started["run_id"],
            "sha256": recorded["sha256"],
        })
        run_dir = next(self.home.glob(f"runs/*/*/{started['run_id']}"))
        self.assertTrue((run_dir / "outcome.json").is_file())
        self.assertTrue((run_dir / "review.json").is_file())

    def test_record_outcome_scalar_and_stdin_share_one_normalization_path(self) -> None:
        first = self.finalized()
        second = self.finalized()
        scalar = [
            "record-outcome", "--run-id", str(first["run_id"]),
            "--repo", str(self.repo), "--client", "codex",
            "--status", "implementation-completed", "--basis", "agent-inferred",
            "--confidence", "medium",
        ]
        self.assertEqual(self.run_cli(scalar)[0], 0)
        self.assertEqual(self.run_cli([
            "record-outcome", "--run-id", str(second["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ], json.dumps(self.outcome_semantic()))[0], 0)
        first_record = json.loads(next(self.home.glob(f"runs/*/*/{first['run_id']}/outcome.json")).read_text())
        second_record = json.loads(next(self.home.glob(f"runs/*/*/{second['run_id']}/outcome.json")).read_text())
        for record in (first_record, second_record):
            record.pop("run_id")
            record.pop("recorded_at")
        self.assertEqual(first_record, second_record)

    def test_record_outcome_scalar_repeatables_map_to_one_exact_schema_path(self) -> None:
        started = self.start()
        finding = {
            "id": "PSDR-001", "severity": "IMPORTANT",
            "class": "verification-gap", "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework", "status": "repaired",
            "location": {"path": "docs/plan.md", "locator": "Verification"},
            "evidence_refs": ["docs/plan.md#verification"],
            "consequence": "Behavioral proof was missing.",
            "minimal_fix": "Add focused behavioral proof.", "repair_pass": 1,
        }
        semantic = self.semantic()
        semantic["repair_passes"] = 1
        semantic["findings"] = [finding]
        self.assertEqual(self.run_cli([
            "finish-review", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ], json.dumps(semantic))[0], 0)
        escaped = {
            "severity": "IMPORTANT", "class": "coverage",
            "pattern_key": "missing-acceptance",
            "consequence_category": "escaped-material-defect",
            "basis": "user-reported",
        }
        disputed = {
            "finding_id": "PSDR-001", "class": "verification-gap",
            "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework",
            "basis": "user-reported",
        }
        prevented = {
            "finding_id": "PSDR-001", "pattern_key": "build-only-acceptance",
            "consequence_category": "avoidable-rework",
            "basis": "user-reported",
        }
        code, _output, error = self.run_cli([
            "record-outcome", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--client", "codex",
            "--client-version", "1", "--model", "model-a",
            "--status", "sdd-completed", "--replan-count", "2",
            "--evaluated-finding", "PSDR-001",
            "--escaped-finding-json", json.dumps(escaped),
            "--disputed-finding-json", json.dumps(disputed),
            "--prevented-rework-json", json.dumps(prevented),
            "--basis", "user-reported", "--confidence", "high",
        ])
        self.assertEqual((code, error), (0, ""))
        outcome = json.loads(next(
            self.home.glob(f"runs/*/*/{started['run_id']}/outcome.json")
        ).read_text())
        self.assertEqual(outcome["recorder"], {
            "client": "codex", "version": "1", "model": "model-a",
        })
        self.assertEqual(outcome["downstream"], {
            "status": "sdd-completed", "plan_hash_matched": True,
            "replan_count": 2, "evaluated_finding_ids": ["PSDR-001"],
            "escaped_findings": [escaped], "disputed_findings": [disputed],
            "prevented_rework": [prevented],
        })
        self.assertEqual(outcome["assessment"], {
            "label": "false-ready", "basis": "user-reported",
            "confidence": "high",
        })

    def test_record_outcome_rejects_mixed_wrong_repository_stale_plan_and_duplicate(self) -> None:
        started = self.finalized()
        command = [
            "record-outcome", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ]
        code, output, error = self.run_cli(
            command + ["--client", "codex"], json.dumps(self.outcome_semantic())
        )
        self.assertNotEqual(code, 0); self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "invalid-arguments")

        other_workspace = self.workspace / "other-outcome"
        other_workspace.mkdir()
        other_repo = make_git_repo(other_workspace)
        wrong = command.copy(); wrong[wrong.index(str(self.repo))] = str(other_repo)
        code, output, error = self.run_cli(wrong, json.dumps(self.outcome_semantic()))
        self.assertNotEqual(code, 0); self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "wrong-repository")
        self.assertNotIn(str(other_repo), error)

        write(self.repo / "docs/plan.md", "# Changed\n\n**Spec:** `docs/design.md`\n")
        code, output, error = self.run_cli(command, json.dumps(self.outcome_semantic()))
        self.assertNotEqual(code, 0); self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "stale-plan")
        self.assertNotIn(str(self.repo), error)

        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** `docs/design.md`\n")
        self.assertEqual(self.run_cli(command, json.dumps(self.outcome_semantic()))[0], 0)
        code, output, error = self.run_cli(command, json.dumps(self.outcome_semantic()))
        self.assertNotEqual(code, 0); self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "outcome-already-recorded")

    def test_record_outcome_validates_identity_before_recovery_then_recovers(self) -> None:
        started = self.finalized()
        paths = storage.EvidencePaths.from_home(self.home)
        record = pending_record()
        with self.assertRaises(RuntimeError):
            storage.create_pending(
                paths, record,
                interruption_hook=lambda point, _path: (
                    (_ for _ in ()).throw(RuntimeError("stop"))
                    if point == "pending-fsynced" else None
                ),
            )
        staging = paths.runs / f".staging-{record['run_id']}"
        staged_bytes = (staging / ".pending.json").read_bytes()
        command = [
            "record-outcome", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ]
        key = self.home / "identity.key"
        original_key = key.read_bytes()
        original_times = (key.stat().st_atime_ns, key.stat().st_mtime_ns)
        key.write_bytes(b"short")
        if hasattr(key, "chmod"):
            key.chmod(0o600)
        code, output, error = self.run_cli(command, json.dumps(self.outcome_semantic()))
        self.assertNotEqual(code, 0); self.assertEqual(output, "")
        self.assertEqual((staging / ".pending.json").read_bytes(), staged_bytes)
        self.assertFalse(paths.run_directory(str(record["run_id"]), str(record["started_at"])).exists())

        key.write_bytes(original_key)
        os.utime(key, ns=original_times)
        if hasattr(key, "chmod"):
            key.chmod(0o600)
        code, output, error = self.run_cli(command, json.dumps(self.outcome_semantic()))
        self.assertEqual((code, error), (0, ""))
        self.assertFalse(staging.exists())
        self.assertTrue(paths.run_directory(str(record["run_id"]), str(record["started_at"])).exists())

    def test_outcome_stdin_rejects_computed_fields_and_no_amendment_command_exists(self) -> None:
        started = self.finalized()
        semantic = self.outcome_semantic()
        for field, value in (("repo_id", "x"), ("plan_hash_matched", True)):
            changed = dict(semantic); changed[field] = value
            code, output, error = self.run_cli([
                "record-outcome", "--run-id", str(started["run_id"]),
                "--repo", str(self.repo), "--from-stdin",
            ], json.dumps(changed))
            self.assertNotEqual(code, 0); self.assertEqual(output, "")
            self.assertEqual(json.loads(error)["error"]["code"], "schema-invalid")
        code, output, error = self.run_cli(["amend-outcome", "--run-id", str(started["run_id"])])
        self.assertNotEqual(code, 0); self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["error"]["code"], "invalid-arguments")

    def test_malformed_outcome_stdin_reaches_bounded_schema_failure(self) -> None:
        started = self.finalized()
        for field, value in (
            ("status", []),
            ("escaped_findings", None),
            ("recorder", "not-an-object"),
        ):
            semantic = self.outcome_semantic()
            semantic[field] = value
            with self.subTest(field=field):
                code, output, error = self.run_cli([
                    "record-outcome", "--run-id", str(started["run_id"]),
                    "--repo", str(self.repo), "--from-stdin",
                ], json.dumps(semantic))
                self.assertNotEqual(code, 0)
                self.assertEqual(output, "")
                self.assertEqual(set(json.loads(error)), {"error"})

    def test_json_and_utf8_failures_are_bounded_and_create_no_outcome(self) -> None:
        started = self.finalized()
        command = [
            "record-outcome", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ]
        oversized_integer = "1" * 5000
        huge_stdin = json.dumps(self.outcome_semantic()).replace(
            '"implementation-completed"', oversized_integer
        )
        surrogate_semantic = self.outcome_semantic()
        surrogate_semantic["recorder"]["model"] = "\ud800"  # type: ignore[index]
        surrogate_stdin = json.dumps(surrogate_semantic, ensure_ascii=False)
        scalar_base = [
            "record-outcome", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--client", "codex",
            "--status", "implementation-completed", "--basis", "agent-inferred",
            "--confidence", "low",
        ]
        cases = (
            (command, huge_stdin, "invalid-json"),
            (command, surrogate_stdin, "invalid-json"),
            (
                scalar_base + [
                    "--escaped-finding-json",
                    '{"extra":' + oversized_integer + "}",
                ],
                "",
                "invalid-json",
            ),
            (scalar_base + ["--model", "\ud800"], "", "invalid-string"),
        )
        run_dir = next(self.home.glob(f"runs/*/*/{started['run_id']}"))
        for argv, stdin, expected_code in cases:
            with self.subTest(expected_code=expected_code, argv=argv[-2:]):
                code, output, error = self.run_cli(argv, stdin)
                self.assertNotEqual(code, 0)
                self.assertEqual(output, "")
                failure = json.loads(error)
                self.assertEqual(failure["error"]["code"], expected_code)
                self.assertLessEqual(len(error.encode("utf-8")), 1024)
                self.assertFalse((run_dir / "outcome.json").exists())

    def test_unknown_surrogate_object_key_has_bounded_error_and_no_outcome(self) -> None:
        started = self.finalized()
        semantic = self.outcome_semantic()
        semantic["recorder"]["\ud800"] = "private"  # type: ignore[index]
        code, output, error = self.run_cli([
            "record-outcome", "--run-id", str(started["run_id"]),
            "--repo", str(self.repo), "--from-stdin",
        ], json.dumps(semantic))

        self.assertEqual(code, 2)
        self.assertEqual(output, "")
        self.assertEqual(json.loads(error), {
            "error": {
                "code": "invalid-keys",
                "message": "recorder has unknown keys",
            },
        })
        self.assertLessEqual(len(error.encode("utf-8")), 1024)
        run_dir = next(self.home.glob(f"runs/*/*/{started['run_id']}"))
        self.assertFalse((run_dir / "outcome.json").exists())

    def test_doctor_reports_identity_damage_without_repairing_it(self) -> None:
        self.start()
        key = self.home / "identity.key"
        original = key.read_bytes()
        key.write_bytes(b"short")
        if hasattr(key, "chmod"):
            key.chmod(0o600)
        code, output, error = self.run_cli(["doctor"])
        self.assertEqual((code, error), (0, ""))
        report = json.loads(output)
        self.assertIn("identity-state-invalid", {item["code"] for item in report["issues"]})
        self.assertEqual(key.read_bytes(), b"short")
        self.assertNotEqual(key.read_bytes(), original)

    def test_mutators_recover_staging_and_read_only_commands_leave_it_unchanged(self) -> None:
        def strand(paths: storage.EvidencePaths) -> tuple[dict[str, object], Path, Path, bytes]:
            record = pending_record()
            with self.assertRaises(RuntimeError):
                storage.create_pending(
                    paths,
                    record,
                    interruption_hook=lambda point, _path: (
                        (_ for _ in ()).throw(RuntimeError("stop"))
                        if point == "pending-fsynced" else None
                    ),
                )
            staging = paths.runs / f".staging-{record['run_id']}"
            destination = paths.run_directory(str(record["run_id"]), str(record["started_at"]))
            return record, staging, destination, (staging / ".pending.json").read_bytes()

        for command in ("start", "finish-review", "abandon"):
            with self.subTest(mutator=command):
                self.home = self.workspace / f"mutator-{command}"
                target = self.start()
                paths = storage.EvidencePaths.from_home(self.home)
                _record, staging, destination, _bytes = strand(paths)
                if command == "start":
                    code, _output, error = self.run_cli([
                        "start", "--skill-root", str(self.skill), "--plan", "docs/plan.md",
                        "--client", "cursor", "--mode", "default",
                    ])
                elif command == "finish-review":
                    code, _output, error = self.run_cli([
                        "finish-review", "--run-id", str(target["run_id"]),
                        "--repo", str(self.repo), "--from-stdin",
                    ], json.dumps(self.semantic()))
                else:
                    code, _output, error = self.run_cli([
                        "abandon", "--run-id", str(target["run_id"]),
                        "--reason", "client-interrupted",
                    ])
                self.assertEqual((code, error), (0, ""))
                self.assertFalse(staging.exists())
                self.assertTrue((destination / ".pending.json").exists())

        self.home = self.workspace / "read-only-matrix"
        target = self.start()
        paths = storage.EvidencePaths.from_home(self.home)
        _record, staging, destination, staged_bytes = strand(paths)
        read_commands = (
            ["--version"],
            ["show", "--run-id", str(target["run_id"])],
            ["pending"],
            ["doctor"],
        )
        for command in read_commands:
            with self.subTest(read_only=command[0]):
                self.run_cli(command)
                self.assertTrue(staging.exists())
                self.assertFalse(destination.exists())
                self.assertEqual((staging / ".pending.json").read_bytes(), staged_bytes)
        storage.scan_runs(paths)
        self.assertTrue(staging.exists())
        self.assertFalse(destination.exists())
        self.assertEqual((staging / ".pending.json").read_bytes(), staged_bytes)

    def test_failures_are_one_bounded_json_object_without_absolute_paths(self) -> None:
        code, output, error = self.run_cli(["show", "--run-id", "00000000-0000-4000-8000-000000000000"])
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        failure = json.loads(error)
        self.assertEqual(set(failure), {"error"})
        self.assertEqual(set(failure["error"]), {"code", "message"})
        self.assertNotIn(str(self.workspace), error)
        code, output, error = self.run_cli([
            "start", "--skill-root", str(self.skill), "--plan", "docs/plan.md",
            "--client", str(self.workspace / "SECRET-CLIENT"), "--mode", "default",
        ])
        self.assertNotEqual(code, 0)
        self.assertEqual(output, "")
        self.assertNotIn(str(self.workspace), error)


if __name__ == "__main__":
    unittest.main()
