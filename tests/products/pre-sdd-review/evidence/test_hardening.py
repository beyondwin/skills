from __future__ import annotations

import builtins
import copy
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
    run_git,
    start,
)

import evidence


class RecorderFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.workspace = Path(self.directory.name)
        self.home = self.workspace / "evidence home"
        self.repo = make_git_repo(self.workspace / "first", "same")
        self.skill = make_skill_root(self.workspace)

    def put(self, run_id: str, record: dict[str, object]) -> Path:
        path = self.home / "runs" / f"{run_id}.json"
        path.write_bytes(evidence.canonical(record))
        return path

    def key(self, run_id: str) -> str:
        record = load(self.home, run_id)
        self.assertIn("repo_key", record)
        return str(record["repo_key"])


class IdentityTests(RecorderFixture):
    def test_same_basename_cannot_finish_another_checkout(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        other = make_git_repo(self.workspace / "second", "same")
        before = (self.home / "runs" / f"{run_id}.json").read_bytes()
        code, out, err = finish(self.home, other, run_id, finish_payload())
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(error_code(err), "outside-repository")
        self.assertEqual((self.home / "runs" / f"{run_id}.json").read_bytes(), before)

    def test_start_binds_without_storing_identity_paths(self) -> None:
        first = start(self.home, self.repo, self.skill)
        second = start(self.home, self.repo, self.skill)
        record = load(self.home, first)
        self.assertEqual(record["schema"], 3)
        self.assertRegex(record["repo_key"], r"^[0-9a-f]{64}$")
        self.assertEqual(record["repo_key"], load(self.home, second)["repo_key"])
        encoded = evidence.canonical(record)
        self.assertNotIn(str(self.repo).encode(), encoded)
        self.assertNotIn(str(self.home).encode(), encoded)
        salt = self.home / ".identity-salt"
        self.assertEqual(len(salt.read_bytes()), 32)
        self.assertEqual(stat.S_IMODE(salt.stat().st_mode), 0o600)
        self.assertNotIn(salt.read_bytes().hex().encode(), encoded)

    def test_worktree_move_changes_identity_even_with_same_git_directory(self) -> None:
        worktree = self.workspace / "linked checkout"
        result = run_git(self.repo, "worktree", "add", "--detach", str(worktree))
        self.assertEqual(result.returncode, 0, result.stderr)
        before_git_dir = run_git(
            worktree, "rev-parse", "--absolute-git-dir"
        ).stdout.strip()
        run_id = start(self.home, worktree, self.skill)
        moved = self.workspace / "moved checkout"
        result = run_git(self.repo, "worktree", "move", str(worktree), str(moved))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            run_git(moved, "rev-parse", "--absolute-git-dir").stdout.strip(),
            before_git_dir,
        )
        code, _, err = finish(self.home, moved, run_id, finish_payload())
        self.assertEqual((code, error_code(err)), (2, "outside-repository"))
        new_run = start(self.home, moved, self.skill)
        self.assertNotEqual(self.key(run_id), self.key(new_run))

    def test_two_worktrees_of_one_repository_have_different_keys(self) -> None:
        linked = self.workspace / "linked"
        result = run_git(self.repo, "worktree", "add", "--detach", str(linked))
        self.assertEqual(result.returncode, 0, result.stderr)
        original_run = start(self.home, self.repo, self.skill)
        linked_run = start(self.home, linked, self.skill)
        self.assertNotEqual(self.key(original_run), self.key(linked_run))

    def test_local_clone_at_another_path_has_a_different_key(self) -> None:
        clone = self.workspace / "clone"
        completed = subprocess.run(
            ["git", "clone", "--local", str(self.repo), str(clone)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        original_run = start(self.home, self.repo, self.skill)
        clone_run = start(self.home, clone, self.skill)
        self.assertNotEqual(self.key(original_run), self.key(clone_run))

    def test_directory_rename_changes_checkout_identity(self) -> None:
        before = start(self.home, self.repo, self.skill)
        moved = self.repo.with_name("renamed")
        self.repo.rename(moved)
        after = start(self.home, moved, self.skill)
        self.assertNotEqual(self.key(before), self.key(after))

    def test_symlink_alias_keeps_checkout_identity(self) -> None:
        alias = self.workspace / "same alias"
        alias.symlink_to(self.repo, target_is_directory=True)
        direct = start(self.home, self.repo, self.skill)
        through_alias = start(self.home, alias, self.skill)
        self.assertEqual(self.key(direct), self.key(through_alias))

    def test_matching_checkout_can_finish(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        code, out, err = finish(self.home, self.repo, run_id, finish_payload())
        self.assertEqual(code, 0, err)
        self.assertEqual(
            json.loads(out),
            {"run_id": run_id, "status": "completed", "verdict": "READY"},
        )

    def test_concurrent_starts_share_one_private_identity_salt(self) -> None:
        command = [
            sys.executable,
            str(EVIDENCE_DIR / "evidence.py"),
            "start",
            "--skill-root",
            str(self.skill),
            "--repo",
            str(self.repo),
            "--plan",
            str(self.repo / "docs/plan.md"),
            "--design",
            str(self.repo / "docs/design.md"),
            "--client",
            "codex",
            "--model",
            "gpt-test",
            "--mode",
            "default",
        ]
        environ = os.environ.copy()
        environ["PRE_SDD_REVIEW_HOME"] = str(self.home)
        environ["PYTHONDONTWRITEBYTECODE"] = "1"
        processes = [
            subprocess.Popen(
                command,
                cwd=self.repo,
                env=environ,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(4)
        ]
        completed = [process.communicate(timeout=15) for process in processes]
        for process, (stdout, stderr) in zip(processes, completed, strict=True):
            self.assertEqual(process.returncode, 0, stderr)
            self.assertTrue(stdout)
        records = [
            load(self.home, json.loads(stdout)["run_id"]) for stdout, _ in completed
        ]
        self.assertEqual(len({str(record["run_id"]) for record in records}), 4)
        for record in records:
            self.assertIn("repo_key", record)
        self.assertEqual(len({str(record["repo_key"]) for record in records}), 1)
        self.assertEqual(len((self.home / ".identity-salt").read_bytes()), 32)
        self.assertEqual(list(self.home.glob(".identity-salt-*")), [])


class TransitionTests(RecorderFixture):
    def child(self, arguments: list[str], payload: str = "") -> subprocess.Popen[str]:
        worker = (
            "import sys; sys.path.insert(0, sys.argv.pop(1)); "
            "import evidence; print('ready', flush=True); "
            "raise SystemExit(evidence.main())"
        )
        process = subprocess.Popen(
            [sys.executable, "-c", worker, str(EVIDENCE_DIR), *arguments],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.repo,
            env={**os.environ, "PRE_SDD_REVIEW_HOME": str(self.home),
                 "PYTHONDONTWRITEBYTECODE": "1"},
        )

        def cleanup() -> None:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=15)

        self.addCleanup(cleanup)
        self.assertEqual(process.stdout.readline(), "ready\n")
        if payload:
            process.stdin.write(payload)
        process.stdin.close()
        process.stdin = None
        return process

    def assert_waiting(self, processes: list[subprocess.Popen[str]]) -> None:
        for process in processes:
            with self.assertRaises(subprocess.TimeoutExpired):
                process.communicate(timeout=0.2)

    def test_terminal_commands_wait_for_lock_and_have_one_winner(self) -> None:
        for second_command in ("finish", "abandon"):
            with self.subTest(second_command=second_command):
                run_id = start(self.home, self.repo, self.skill)
                with evidence._file_lock(self.home / "locks" / f"{run_id}.lock"):
                    processes = []
                    for command in ("finish", second_command):
                        arguments = [command, "--run-id", run_id]
                        arguments += (["--repo", str(self.repo)] if command == "finish"
                                      else ["--reason", "other"])
                        processes.append(self.child(
                            arguments, json.dumps(finish_payload()) if command == "finish" else ""
                        ))
                    self.assert_waiting(processes)
                results = []
                for process in processes:
                    out, err = process.communicate(timeout=15)
                    results.append((process.returncode, out, err))
                self.assertEqual(sorted(code for code, _, _ in results), [0, 2])
                loser = next(err for code, _, err in results if code == 2)
                self.assertEqual(error_code(loser), "already-finished")
                final = load(self.home, run_id)
                self.assertIn(final["status"], ("completed", "abandoned"))
                self.assertEqual(len(list((self.home / "runs").glob("*.json"))),
                                 1 if second_command == "finish" else 2)

    def test_outcomes_wait_for_lock_and_preserve_complete_updates(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, run_id, finish_payload())[0], 0)
        before = load(self.home, run_id)
        pairs = [("good", "first observation"), ("false-ready", "second observation")]
        with evidence._file_lock(self.home / "locks" / f"{run_id}.lock"):
            processes = [self.child([
                "outcome", "--run-id", run_id, "--label", label, "--note", note
            ]) for label, note in pairs]
            self.assert_waiting(processes)
            # A holder's latest record must survive both queued writers. Reading
            # before acquiring the lock would restore the old client snapshot.
            before["client"]["model"] = "updated-while-queued"
            self.put(run_id, before)
        for process in processes:
            out, err = process.communicate(timeout=15)
            self.assertEqual(process.returncode, 0, err)
            self.assertEqual(json.loads(out)["run_id"], run_id)
        final = load(self.home, run_id)
        outcome = final.pop("outcome")
        self.assertIn((outcome["label"], outcome["note"]), pairs)
        self.assertTrue(outcome["recorded_at"])
        before.pop("outcome")
        self.assertEqual(final, before)

    def test_write_failure_preserves_record_and_removes_own_temporary_file(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        path = self.home / "runs" / f"{run_id}.json"
        before = path.read_bytes()
        # Another writer's old temporary file must never be reused or removed.
        other_temp = path.with_name(path.name + ".tmp")
        other_temp.write_bytes(b"another writer")
        changed = load(self.home, run_id)
        changed["status"] = "abandoned"
        with mock.patch.object(evidence.os, "replace", side_effect=OSError("synthetic failure")):
            with self.assertRaises(evidence.EvidenceError) as raised:
                evidence.write_record(path, changed)
        self.assertEqual(raised.exception.code, "evidence-home-unwritable")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(list(path.parent.glob(path.name + ".*.tmp")), [])
        self.assertEqual(other_temp.read_bytes(), b"another writer")


class UnsupportedLockingTests(RecorderFixture):
    def test_mutation_fails_cleanly_but_read_only_commands_need_no_locking(self) -> None:
        original_import = builtins.__import__

        def without_fcntl(name, *args, **kwargs):
            if name == "fcntl":
                raise ImportError("synthetic unsupported platform")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=without_fcntl):
            for command in (["--version"], ["summary"]):
                code, out, err = run(command, home=self.home, cwd=self.repo)
                self.assertEqual((code, err), (0, ""))
                self.assertIsInstance(json.loads(out), dict)
                self.assertFalse(self.home.exists())
            code, out, err = run([
                "start", "--skill-root", str(self.skill), "--repo", str(self.repo),
                "--plan", str(self.repo / "docs/plan.md"), "--client", "codex",
                "--mode", "default",
            ], home=self.home, cwd=self.repo)
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(error_code(err), "locking-unavailable")
        self.assertEqual(len(err.splitlines()), 1)
        self.assertNotIn("Traceback", err)
        self.assertFalse(self.home.exists())


class LegacyTests(RecorderFixture):
    def test_legacy_pending_is_readable_but_not_mutated(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        old = load(self.home, run_id)
        old["schema"] = 2
        old.pop("repo_key", None)
        path = self.put(run_id, old)
        before = path.read_bytes()
        code, out, err = run(
            ["show", "--run-id", run_id], home=self.home, cwd=self.repo
        )
        self.assertEqual((code, out.encode(), err), (0, before, ""))
        code, _, err = finish(self.home, self.repo, run_id, finish_payload())
        self.assertEqual(code, 2)
        self.assertEqual(error_code(err), "legacy-record-read-only")
        code, _, err = run(
            ["abandon", "--run-id", run_id, "--reason", "other"],
            home=self.home,
            cwd=self.repo,
        )
        self.assertEqual(code, 2)
        self.assertEqual(error_code(err), "legacy-record-read-only")
        self.assertEqual(path.read_bytes(), before)

    def test_legacy_completed_outcome_is_refused_without_mutation(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        self.assertEqual(
            finish(self.home, self.repo, run_id, finish_payload())[0], 0
        )
        old = load(self.home, run_id)
        old["schema"] = 2
        old.pop("repo_key", None)
        path = self.put(run_id, old)
        before = path.read_bytes()
        code, out, err = run(
            ["show", "--run-id", run_id], home=self.home, cwd=self.repo
        )
        self.assertEqual((code, out.encode(), err), (0, before, ""))
        code, _, err = run(
            ["outcome", "--run-id", run_id, "--label", "good"],
            home=self.home,
            cwd=self.repo,
        )
        self.assertEqual(code, 2)
        self.assertEqual(error_code(err), "legacy-record-read-only")
        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn("repo_key", load(self.home, run_id))


if __name__ == "__main__":
    unittest.main()
