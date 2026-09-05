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


if __name__ == "__main__":
    unittest.main()
