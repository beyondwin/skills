from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import (
    EVIDENCE_DIR,
    commit_all,
    error_code,
    finding,
    finish,
    finish_payload,
    load,
    make_git_repo,
    make_skill_root,
    run,
    start,
    write,
)

import evidence


VERSION_LINE = b'{"cli_version":"2.0.0","schema":2,"skill_name":"pre-sdd-review"}\n'


class VersionTests(unittest.TestCase):
    def test_version_is_canonical_and_touches_no_home(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            code, out, err = run(["--version"], home=home, cwd=Path(directory))
            self.assertEqual((code, out.encode("utf-8"), err), (0, VERSION_LINE, ""))
            self.assertFalse(home.exists())

    def test_version_rejects_extra_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = run(["--version", "summary"], home=Path(directory), cwd=Path(directory))
            self.assertEqual((code, out), (2, ""))
            self.assertEqual(error_code(err), "invalid-arguments")

    def test_unknown_command_uses_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, out, err = run(["prune"], home=Path(directory), cwd=Path(directory))
            self.assertEqual((code, out), (2, ""))
            envelope = json.loads(err)
            self.assertEqual(set(envelope), {"error"})
            self.assertEqual(set(envelope["error"]), {"code", "message"})
            self.assertEqual(envelope["error"]["code"], "invalid-arguments")

    def test_script_runs_as_a_file_without_installation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            completed = subprocess.run(
                [sys.executable, str(EVIDENCE_DIR / "evidence.py"), "--version"],
                check=False,
                capture_output=True,
                env={"PRE_SDD_REVIEW_HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1", "PATH": ""},
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, VERSION_LINE)
            self.assertFalse(home.exists())


class StartTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.skill = make_skill_root(self.workspace)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_start_writes_a_pending_record_with_git_and_document_facts(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        record = load(self.home, run_id)
        head = subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(record["schema"], 2)
        self.assertEqual(record["status"], "pending")
        self.assertEqual(record["repo"], "repo")
        self.assertEqual(record["client"], {"id": "codex", "model": "gpt-test"})
        self.assertEqual(record["mode"], "default")
        self.assertEqual(record["skill"]["version"], "2.0.0")
        self.assertRegex(record["skill"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(record["plan"]["path"], "docs/plan.md")
        self.assertRegex(record["plan"]["sha_start"], r"^[0-9a-f]{64}$")
        self.assertIsNone(record["plan"]["sha_end"])
        self.assertEqual(record["design"]["path"], "docs/design.md")
        self.assertEqual(record["git"], {"head_start": head, "head_end": None, "dirty_start": False, "dirty_end": None})
        for key in ("completed_at", "elapsed_s", "execution", "reviewers", "trigger", "review_passes", "repair_passes", "verdict", "block_reason", "abandon_reason", "outcome"):
            self.assertIsNone(record[key], key)
        self.assertEqual(record["degraded_reasons"], [])
        self.assertEqual(record["findings"], [])
        self.assertRegex(record["started_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
        path = self.home / "runs" / f"{run_id}.json"
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE((self.home / "runs").stat().st_mode), 0o700)
        self.assertNotIn(str(self.repo), path.read_text(encoding="utf-8"))

    def test_start_without_design_records_null_and_dirty_worktree(self) -> None:
        write(self.repo / "docs/plan.md", "# Plan\n\nno spec\n")
        run_id = start(self.home, self.repo, self.skill, design=False)
        record = load(self.home, run_id)
        self.assertIsNone(record["design"])
        self.assertTrue(record["git"]["dirty_start"])

    def test_start_accepts_relative_paths_from_cwd(self) -> None:
        code, out, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", ".", "--plan", "docs/plan.md",
             "--design", "./docs/design.md", "--client", "claude-code", "--model", "unknown", "--mode", "review-only"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual(code, 0, err)
        record = load(self.home, json.loads(out)["run_id"])
        self.assertEqual((record["plan"]["path"], record["design"]["path"], record["mode"]), ("docs/plan.md", "docs/design.md", "review-only"))

    def test_start_rejects_plan_outside_repository(self) -> None:
        outside = self.workspace / "elsewhere.md"
        write(outside, "# Plan\n")
        code, _, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", str(self.repo), "--plan", str(outside),
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual((code, error_code(err)), (2, "outside-repository"))

    def test_start_rejects_non_git_repository(self) -> None:
        plain = self.workspace / "plain"
        write(plain / "plan.md", "# Plan\n")
        code, _, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", str(plain), "--plan", str(plain / "plan.md"),
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=plain,
        )
        self.assertEqual((code, error_code(err)), (2, "not-git-repository"))

    def test_start_rejects_skill_root_without_protocol_or_version(self) -> None:
        broken = self.workspace / "broken"
        write(broken / "SKILL.md", "---\nname: pre-sdd-review\n---\n")
        code, _, err = run(
            ["start", "--skill-root", str(broken), "--repo", str(self.repo), "--plan", "docs/plan.md",
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))

    def test_start_rejects_unknown_client_and_invalid_home(self) -> None:
        code, _, err = run(
            ["start", "--skill-root", str(self.skill), "--repo", str(self.repo), "--plan", "docs/plan.md",
             "--client", "gemini", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))
        code, _, err = run(["summary"], home=Path("relative/home"), cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))

    def test_start_reads_the_real_skill_root_version(self) -> None:
        real_skill = EVIDENCE_DIR.parent
        code, out, err = run(
            ["start", "--skill-root", str(real_skill), "--repo", str(self.repo), "--plan", "docs/plan.md",
             "--client", "codex", "--model", "m", "--mode", "default"],
            home=self.home, cwd=self.repo,
        )
        self.assertEqual(code, 0, err)
        import tomllib
        release = tomllib.loads((real_skill / "release.toml").read_text(encoding="utf-8"))
        self.assertEqual(load(self.home, json.loads(out)["run_id"])["skill"]["version"], release["version"])


class FinishTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.skill = make_skill_root(self.workspace)
        self.run_id = start(self.home, self.repo, self.skill)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_finish_completes_the_record_with_end_state(self) -> None:
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n\nrepaired\n")
        commit_all(self.repo)
        payload = finish_payload(verdict="READY", review_passes=2, repair_passes=1, findings=[finding()])
        code, out, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"run_id": self.run_id, "status": "completed", "verdict": "READY"})
        record = load(self.home, self.run_id)
        self.assertEqual(record["status"], "completed")
        self.assertEqual((record["execution"], record["reviewers"], record["verdict"]), ("full", 1, "READY"))
        self.assertEqual((record["review_passes"], record["repair_passes"]), (2, 1))
        self.assertEqual(record["findings"], [finding()])
        self.assertNotEqual(record["plan"]["sha_start"], record["plan"]["sha_end"])
        self.assertEqual(record["design"]["sha_start"], record["design"]["sha_end"])
        self.assertNotEqual(record["git"]["head_start"], record["git"]["head_end"])
        self.assertFalse(record["git"]["dirty_end"])
        self.assertIsInstance(record["elapsed_s"], int)
        self.assertRegex(record["completed_at"], r"Z$")

    def test_finish_rejects_each_invariant_violation(self) -> None:
        cases = {
            "ready-with-unresolved": finish_payload(findings=[finding(status="unresolved", repair_pass=None)]),
            "revise-without-unresolved": finish_payload(verdict="REVISE", repair_passes=1, findings=[finding()]),
            "blocked-without-reason": finish_payload(verdict="BLOCKED", execution="blocked", reviewers=0),
            "repair-without-repaired": finish_payload(repair_passes=1),
            "full-two-reviewers-no-trigger": finish_payload(reviewers=2),
            "full-one-reviewer-with-trigger": finish_payload(trigger="schema-migration"),
            "full-with-degraded-reason": finish_payload(degraded_reasons=["fresh-reviewer-unavailable"]),
            "degraded-without-reason": finish_payload(execution="degraded"),
            "duplicate-finding-id": finish_payload(repair_passes=1, findings=[finding(), finding(pattern="other")]),
            "repair-pass-exceeds": finish_payload(repair_passes=1, findings=[finding(repair_pass=2)]),
            "absolute-evidence-path": finish_payload(repair_passes=1, findings=[finding(evidence=["/etc/passwd"])]),
            "parent-location-path": finish_payload(repair_passes=1, findings=[finding(location={"path": "../x.md", "locator": "L1"})]),
            "long-consequence": finish_payload(repair_passes=1, findings=[finding(consequence="x" * 301)]),
            "bad-finding-id": finish_payload(repair_passes=1, findings=[finding(id="F-1")]),
            "unknown-key": {**finish_payload(), "token_usage": None},
            "missing-key": {key: value for key, value in finish_payload().items() if key != "findings"},
            "review-passes-zero": finish_payload(review_passes=0),
        }
        for name, payload in cases.items():
            with self.subTest(name=name):
                code, out, err = finish(self.home, self.repo, self.run_id, payload)
                self.assertEqual((code, out), (2, ""), name)
                self.assertEqual(error_code(err), "schema-invalid", name)
                self.assertEqual(load(self.home, self.run_id)["status"], "pending")

    def test_finish_accepts_blocked_degraded_and_triggered_full_runs(self) -> None:
        for payload in (
            finish_payload(verdict="BLOCKED", block_reason="spec-unresolved", execution="blocked", reviewers=0),
            finish_payload(verdict="REVISE", execution="degraded", degraded_reasons=["fresh-reviewer-unavailable"], findings=[finding(status="unresolved", repair_pass=None)]),
            finish_payload(reviewers=2, trigger="data-boundary"),
        ):
            with self.subTest(payload=payload["verdict"] + payload["execution"]):
                run_id = start(self.home, self.repo, self.skill)
                code, _, err = finish(self.home, self.repo, run_id, payload)
                self.assertEqual(code, 0, err)

    def test_review_only_rejects_repair_passes(self) -> None:
        run_id = start(self.home, self.repo, self.skill, mode="review-only")
        code, _, err = finish(self.home, self.repo, run_id, finish_payload(repair_passes=1, findings=[finding()]))
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))

    def test_finish_rejects_wrong_repository_and_second_finish(self) -> None:
        other = make_git_repo(self.workspace, name="other")
        code, _, err = finish(self.home, other, self.run_id, finish_payload())
        self.assertEqual((code, error_code(err)), (2, "outside-repository"))
        self.assertEqual(finish(self.home, self.repo, self.run_id, finish_payload())[0], 0)
        code, _, err = finish(self.home, self.repo, self.run_id, finish_payload())
        self.assertEqual((code, error_code(err)), (2, "already-finished"))

    def test_finish_rejects_unknown_run_and_invalid_json(self) -> None:
        code, _, err = finish(self.home, self.repo, "00000000-0000-4000-8000-000000000000", finish_payload())
        self.assertEqual((code, error_code(err)), (2, "run-not-found"))
        code, _, err = run(["finish", "--run-id", self.run_id, "--repo", str(self.repo)], home=self.home, cwd=self.repo, stdin_text="{not json")
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))

    def test_finish_rejects_records_over_the_size_limit(self) -> None:
        findings = [
            finding(id=f"PSDR-{index:03d}", pattern=f"pattern-{index}", consequence="c" * 300, fix="f" * 300)
            for index in range(1, 130)
        ]
        code, _, err = finish(self.home, self.repo, self.run_id, finish_payload(repair_passes=1, findings=findings))
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
        self.assertEqual(load(self.home, self.run_id)["status"], "pending")


class AbandonOutcomeShowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.skill = make_skill_root(self.workspace)
        self.run_id = start(self.home, self.repo, self.skill)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_abandon_closes_a_pending_run_with_each_reason(self) -> None:
        for reason in ("user-cancelled", "input-changed", "scope-changed", "input-format-fixed", "other"):
            with self.subTest(reason=reason):
                run_id = start(self.home, self.repo, self.skill)
                code, out, err = run(["abandon", "--run-id", run_id, "--reason", reason], home=self.home, cwd=self.repo)
                self.assertEqual(code, 0, err)
                self.assertEqual(json.loads(out), {"run_id": run_id, "status": "abandoned"})
                record = load(self.home, run_id)
                self.assertEqual((record["status"], record["abandon_reason"]), ("abandoned", reason))
                self.assertIsInstance(record["elapsed_s"], int)
                self.assertIsNone(record["verdict"])

    def test_abandon_rejects_invalid_reason_and_finished_runs(self) -> None:
        code, _, err = run(["abandon", "--run-id", self.run_id, "--reason", "bored"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))
        self.assertEqual(finish(self.home, self.repo, self.run_id, finish_payload())[0], 0)
        code, _, err = run(["abandon", "--run-id", self.run_id, "--reason", "other"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "already-finished"))

    def test_outcome_records_and_overwrites_a_label(self) -> None:
        self.assertEqual(finish(self.home, self.repo, self.run_id, finish_payload())[0], 0)
        code, out, err = run(["outcome", "--run-id", self.run_id, "--label", "good", "--note", "SDD completed"], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out), {"run_id": self.run_id, "outcome": "good"})
        first = load(self.home, self.run_id)["outcome"]
        self.assertEqual((first["label"], first["note"]), ("good", "SDD completed"))
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "false-ready"], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        second = load(self.home, self.run_id)["outcome"]
        self.assertEqual((second["label"], second["note"]), ("false-ready", None))

    def test_outcome_rejects_pending_runs_false_ready_without_ready_and_long_notes(self) -> None:
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "good"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
        revise = finish_payload(verdict="REVISE", findings=[finding(status="unresolved", repair_pass=None)])
        self.assertEqual(finish(self.home, self.repo, self.run_id, revise)[0], 0)
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "false-ready"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
        code, _, err = run(["outcome", "--run-id", self.run_id, "--label", "noisy", "--note", "n" * 301], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))

    def test_show_prints_the_record_verbatim(self) -> None:
        code, out, err = run(["show", "--run-id", self.run_id], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        self.assertEqual(out, (self.home / "runs" / f"{self.run_id}.json").read_text(encoding="utf-8"))
        code, _, err = run(["show", "--run-id", "00000000-0000-4000-8000-000000000000"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "run-not-found"))
        code, _, err = run(["show", "--run-id", "not-a-uuid"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))


class SummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace)
        self.other = make_git_repo(self.workspace, name="other")
        self.skill = make_skill_root(self.workspace)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _summary(self, *extra: str) -> dict:
        code, out, err = run(["summary", *extra], home=self.home, cwd=self.repo)
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def _mutate(self, run_id: str, **changes: object) -> None:
        record = load(self.home, run_id)
        record.update(changes)
        evidence.write_record(self.home / "runs" / f"{run_id}.json", record)

    def test_summary_on_empty_home_has_exact_keys(self) -> None:
        summary = self._summary()
        self.assertEqual(set(summary), {"schema", "runs", "counts", "cost", "chains", "findings", "anomalies"})
        self.assertEqual(summary["runs"], [])
        self.assertEqual(summary["counts"]["status"], {"completed": 0, "abandoned": 0, "pending": 0})
        self.assertEqual(summary["counts"]["verdict"], {"READY": 0, "REVISE": 0, "BLOCKED": 0})
        self.assertEqual(summary["counts"]["outcome"], {"recorded": 0, "good": 0, "false-ready": 0, "noisy": 0, "abandoned": 0})
        self.assertEqual(summary["cost"], {"elapsed_s": {"median": None, "max": None}, "review_passes_avg": None, "repair_passes_avg": None})
        self.assertEqual(summary["anomalies"], {
            "repair_without_repaired_finding": [],
            "head_changed_during_review": [],
            "design_unresolved_but_full_execution": [],
            "repo_reality_citing_documents_only": [],
        })
        self.assertFalse(self.home.exists())

    def test_summary_aggregates_chains_patterns_outcomes_and_anomalies(self) -> None:
        repo_reality = finding(id="PSDR-001", **{"class": "repo-reality"}, pattern="demo-npm-cwd", status="unresolved", repair_pass=None, evidence=["docs/plan.md"])
        first = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, first, finish_payload(verdict="REVISE", review_passes=2, findings=[repo_reality]))[0], 0)
        second = start(self.home, self.repo, self.skill)
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n\nfixed\n")
        commit_all(self.repo)
        repaired = finding(id="PSDR-002", **{"class": "repo-reality"}, pattern="demo-npm-cwd", evidence=["src/app.ts"])
        self.assertEqual(finish(self.home, self.repo, second, finish_payload(verdict="READY", review_passes=2, repair_passes=1, findings=[repaired]))[0], 0)
        self.assertEqual(run(["outcome", "--run-id", second, "--label", "good"], home=self.home, cwd=self.repo)[0], 0)
        abandoned = start(self.home, self.repo, self.skill)
        self.assertEqual(run(["abandon", "--run-id", abandoned, "--reason", "input-changed"], home=self.home, cwd=self.repo)[0], 0)
        pending = start(self.home, self.other, self.skill)
        unresolved_design = start(self.home, self.other, self.skill, design=False)
        self.assertEqual(finish(self.home, self.other, unresolved_design, finish_payload())[0], 0)
        self._mutate(unresolved_design, repair_passes=1, findings=[])
        legacy = self.home / "runs" / "2026" / "09" / "abc" / "review.json"
        legacy.parent.mkdir(parents=True)
        legacy.write_text('{"schema_version":1}\n', encoding="utf-8")
        (self.home / "runs" / "garbage.json").write_text("{not json", encoding="utf-8")
        (self.home / "runs" / "old.json").write_text('{"schema":1,"run_id":"x"}\n', encoding="utf-8")

        summary = self._summary()
        self.assertEqual([item["run_id"] for item in summary["runs"]], [first, second, abandoned, pending, unresolved_design])
        self.assertEqual(set(summary["runs"][0]), {"run_id", "started_at", "repo", "plan", "status", "verdict", "findings", "elapsed_s"})
        self.assertEqual(summary["counts"]["status"], {"completed": 3, "abandoned": 1, "pending": 1})
        self.assertEqual(summary["counts"]["verdict"], {"READY": 2, "REVISE": 1, "BLOCKED": 0})
        self.assertEqual(summary["counts"]["execution"], {"full": 3, "degraded": 0, "blocked": 0})
        self.assertEqual(summary["counts"]["abandon_reason"], {"input-changed": 1})
        self.assertEqual(summary["counts"]["outcome"], {"recorded": 1, "good": 1, "false-ready": 0, "noisy": 0, "abandoned": 0})
        self.assertEqual(summary["cost"]["review_passes_avg"], round((2 + 2 + 1) / 3, 1))
        self.assertEqual(summary["cost"]["repair_passes_avg"], round((0 + 1 + 1) / 3, 1))
        self.assertIsInstance(summary["cost"]["elapsed_s"]["median"], int)
        self.assertEqual(len(summary["chains"]), 2)
        repo_chain = next(chain for chain in summary["chains"] if chain["repo"] == "repo")
        self.assertEqual(repo_chain["plan"], "docs/plan.md")
        self.assertEqual(
            repo_chain["runs"],
            [
                {"run_id": first, "status": "completed", "verdict": "REVISE"},
                {"run_id": second, "status": "completed", "verdict": "READY"},
                {"run_id": abandoned, "status": "abandoned", "verdict": None},
            ],
        )
        self.assertEqual(summary["findings"]["total"], 2)
        self.assertEqual(summary["findings"]["by_severity"], {"IMPORTANT": 2})
        self.assertEqual(summary["findings"]["by_status"], {"unresolved": 1, "repaired": 1})
        self.assertEqual(summary["findings"]["by_class"], {"repo-reality": 2})
        self.assertEqual(
            summary["findings"]["repeated_patterns"],
            [{"class": "repo-reality", "pattern": "demo-npm-cwd", "count": 2, "run_ids": [first, second]}],
        )
        self.assertEqual(summary["anomalies"]["repair_without_repaired_finding"], [unresolved_design])
        self.assertEqual(summary["anomalies"]["head_changed_during_review"], [second])
        self.assertEqual(summary["anomalies"]["design_unresolved_but_full_execution"], [unresolved_design])
        self.assertEqual(summary["anomalies"]["repo_reality_citing_documents_only"], [{"run_id": first, "finding_id": "PSDR-001"}])

    def test_summary_filters_by_repo_and_last(self) -> None:
        first = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, first, finish_payload())[0], 0)
        second = start(self.home, self.other, self.skill)
        self.assertEqual(finish(self.home, self.other, second, finish_payload())[0], 0)
        third = start(self.home, self.other, self.skill)
        self.assertEqual([item["run_id"] for item in self._summary("--repo", "other")["runs"]], [second, third])
        self.assertEqual([item["run_id"] for item in self._summary("--last", "1")["runs"]], [third])
        self.assertEqual(self._summary("--last", "1")["counts"]["status"], {"completed": 0, "abandoned": 0, "pending": 1})
        code, _, err = run(["summary", "--last", "0"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))


if __name__ == "__main__":
    unittest.main()
