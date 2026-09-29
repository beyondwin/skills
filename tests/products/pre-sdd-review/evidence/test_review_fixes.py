from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import (
    EVIDENCE_DIR,
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

EVIDENCE_PY = EVIDENCE_DIR / "evidence.py"


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "home"
        self.repo = make_git_repo(self.workspace / "first", "app")
        self.skill = make_skill_root(self.workspace)

    def cli(self, arguments: list[str], stdin: bytes = b"", env: dict[str, str] | None = None,
            cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(EVIDENCE_PY), *arguments],
            input=stdin,
            capture_output=True,
            cwd=cwd or self.repo,
            env={**os.environ, "PRE_SDD_REVIEW_HOME": str(self.home),
                 "PYTHONDONTWRITEBYTECODE": "1", **(env or {})},
            timeout=30,
        )


class LockTests(Fixture):
    def holder(self, lock: Path) -> subprocess.Popen[str]:
        worker = (
            "import sys; sys.path.insert(0, sys.argv[1]); import evidence; "
            "from pathlib import Path\n"
            "with evidence._file_lock(Path(sys.argv[2])):\n"
            "    print('held', flush=True); sys.stdin.read()\n"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", worker, str(EVIDENCE_DIR), str(lock)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
        )

        def cleanup() -> None:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=15)

        self.addCleanup(cleanup)
        return process

    def assert_blocked(self, process: subprocess.Popen[str]) -> None:
        import select

        ready, _, _ = select.select([process.stdout], [], [], 0.5)
        self.assertEqual(ready, [], "a second process entered a held lock")

    def test_a_released_lock_never_admits_two_holders(self) -> None:
        lock = self.home / "locks" / "run.lock"
        with evidence._file_lock(lock):
            waiter = self.holder(lock)
            self.assert_blocked(waiter)
        self.assertEqual(waiter.stdout.readline(), "held\n")
        newcomer = self.holder(lock)
        self.assert_blocked(newcomer)
        waiter.stdin.close()
        self.assertEqual(newcomer.stdout.readline(), "held\n")
        newcomer.stdin.close()


class AbandonBindingTests(Fixture):
    def test_abandon_requires_the_recorded_checkout(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        other = make_git_repo(self.workspace / "second", "app")
        code, _, err = run(["abandon", "--run-id", run_id, "--repo", str(other), "--reason", "other"],
                           home=self.home, cwd=other)
        self.assertEqual((code, error_code(err)), (2, "outside-repository"))
        self.assertEqual(load(self.home, run_id)["status"], "pending")
        code, _, err = run(["abandon", "--run-id", run_id, "--reason", "other"], home=self.home, cwd=self.repo)
        self.assertEqual((code, error_code(err)), (2, "invalid-arguments"))
        code, out, err = run(["abandon", "--run-id", run_id, "--repo", str(self.repo), "--reason", "other"],
                             home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["status"], "abandoned")


class StartValidationTests(Fixture):
    def test_start_refuses_a_record_it_could_not_read_back(self) -> None:
        odd = make_git_repo(self.workspace / "third", "a\\b")
        code, _, err = run(["start", "--skill-root", str(self.skill), "--repo", str(odd),
                            "--plan", str(odd / "docs/plan.md"), "--client", "codex", "--mode", "default"],
                           home=self.home, cwd=odd)
        self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
        self.assertEqual(list((self.home / "runs").glob("*.json")) if (self.home / "runs").exists() else [], [])


class CrashTests(Fixture):
    def test_non_utf8_stdin_is_a_schema_error_not_a_traceback(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        result = self.cli(["finish", "--run-id", run_id, "--repo", str(self.repo)], stdin=b'{"x":"\xff"}')
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stderr)["error"]["code"], "schema-invalid")

    def test_missing_git_is_a_repository_error_not_a_traceback(self) -> None:
        result = self.cli(["start", "--skill-root", str(self.skill), "--repo", str(self.repo),
                           "--plan", "docs/plan.md", "--client", "codex", "--mode", "default"],
                          env={"PATH": "/nonexistent"})
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stderr)["error"]["code"], "not-git-repository")


class FinishShapeTests(Fixture):
    def test_retired_finding_statuses_are_rejected(self) -> None:
        for status in ("accepted-as-is", "blocked-by-authority"):
            with self.subTest(status=status):
                run_id = start(self.home, self.repo, self.skill)
                payload = finish_payload(verdict="BLOCKED", execution="blocked", block_reason="decision",
                                         findings=[finding(severity="BLOCKER", status=status, repair_pass=None)])
                code, _, err = finish(self.home, self.repo, run_id, payload)
                self.assertEqual((code, error_code(err)), (2, "schema-invalid"))

    def test_a_blocked_run_with_no_review_records_zero_review_passes(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        payload = finish_payload(execution="blocked", reviewers=0, verdict="BLOCKED",
                                 block_reason="required base missing", review_passes=0)
        code, out, err = finish(self.home, self.repo, run_id, payload)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["anomalies"], [])

    def test_zero_review_passes_needs_a_blocked_run_with_no_reviewer(self) -> None:
        for overrides in ({"execution": "full", "reviewers": 1}, {"execution": "blocked", "reviewers": 1}):
            with self.subTest(**overrides):
                run_id = start(self.home, self.repo, self.skill)
                payload = finish_payload(verdict="BLOCKED", block_reason="x", review_passes=0, **overrides)
                code, _, err = finish(self.home, self.repo, run_id, payload)
                self.assertEqual((code, error_code(err)), (2, "schema-invalid"))


class CampaignAnomalyTests(Fixture):
    def test_a_design_changed_by_a_preceding_plan_is_not_an_anomaly(self) -> None:
        run_id = start(self.home, self.repo, self.skill, prior_plans=["docs/first-plan.md"])
        write(self.repo / "docs/design.md", "# Design\n\nChanged by the preceding plan's repair.\n")
        code, out, err = finish(self.home, self.repo, run_id, finish_payload(review_passes=1))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["anomalies"], [])

    def test_a_changed_plan_is_still_an_anomaly_in_a_campaign(self) -> None:
        run_id = start(self.home, self.repo, self.skill, prior_plans=["docs/first-plan.md"])
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n\nEdited.\n")
        code, out, err = finish(self.home, self.repo, run_id, finish_payload())
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["anomalies"], ["document_changed_without_repair_pass"])


class AnomalyNameTests(unittest.TestCase):
    def test_summary_buckets_come_from_one_name_list(self) -> None:
        self.assertEqual(set(evidence.summarize([])["anomalies"]), set(evidence.ANOMALY_NAMES))


if __name__ == "__main__":
    unittest.main()
