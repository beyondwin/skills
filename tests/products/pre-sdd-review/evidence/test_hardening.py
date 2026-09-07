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


class ReaderTests(RecorderFixture):
    def assert_damage_isolated(self, good_id: str, bad_id: str) -> None:
        code, out, err = run(["show", "--run-id", bad_id], home=self.home, cwd=self.repo)
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(error_code(err), "schema-invalid")
        self.assertEqual(len(err.splitlines()), 1)
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        summary = json.loads(out)
        self.assertEqual(summary["invalid_records"], 1)
        self.assertEqual([item["run_id"] for item in summary["runs"]], [good_id])
        self.assertNotIn(str(self.home), out)
        self.assertNotIn("Traceback", out)

    def test_schema_shaped_damage_is_rejected_and_counted(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        original = load(self.home, bad_id)
        missing = copy.deepcopy(original)
        del missing["plan"]
        cases = [
            missing,
            {**original, "status": "completed"},
            {**original, "started_at": "not-a-date"},
            {**original, "run_id": good_id},
            {**original, "schema": True},
            {**original, "repo_key": "not-a-key"},
            {**original, "git": {**original["git"], "dirty_start": 1}},
            {**original, "unknown": "extra"},
            {**original, "status": "unknown"},
            {**original, "repo": "../same"},
            {**original, "repo": "same\nother"},
            {**original, "completed_at": original["started_at"]},
            {**original, "elapsed_s": 0},
            {**original, "execution": "full"},
            {**original, "degraded_reasons": ["unfinished"]},
            {**original, "findings": [finding()]},
            {**original, "abandon_reason": "other"},
            {**original, "outcome": {"label": "good", "note": None, "recorded_at": original["started_at"]}},
        ]
        for damaged in cases:
            with self.subTest(damaged=damaged):
                self.put(bad_id, damaged)
                self.assert_damage_isolated(good_id, bad_id)

    def test_missing_plan_cannot_crash_summary(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        damaged = load(self.home, bad_id)
        del damaged["plan"]
        self.put(bad_id, damaged)
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["invalid_records"], 1)
        self.assertEqual([item["run_id"] for item in json.loads(out)["runs"]], [good_id])

    def test_all_statuses_and_legacy_records_preserve_source_bytes(self) -> None:
        expected = []
        for schema in (2, 3):
            for status in ("pending", "completed", "abandoned"):
                with self.subTest(schema=schema, status=status):
                    run_id = start(self.home, self.repo, self.skill, design=False)
                    if status == "completed":
                        self.assertEqual(finish(self.home, self.repo, run_id, finish_payload())[0], 0)
                        self.assertEqual(run(["outcome", "--run-id", run_id, "--label", "good"], home=self.home, cwd=self.repo)[0], 0)
                    elif status == "abandoned":
                        self.assertEqual(run(["abandon", "--run-id", run_id, "--reason", "other"], home=self.home, cwd=self.repo)[0], 0)
                    record = load(self.home, run_id)
                    if schema == 2:
                        record["schema"] = 2
                        del record["repo_key"]
                    raw = (json.dumps(record, indent=2) + "\n\n").encode()
                    path = self.home / "runs" / f"{run_id}.json"
                    path.write_bytes(raw)
                    code, out, err = run(["show", "--run-id", run_id], home=self.home, cwd=self.repo)
                    self.assertEqual((code, err), (0, ""))
                    self.assertEqual(out.encode(), raw)
                    self.assertEqual(path.read_bytes(), raw)
                    expected.append(run_id)
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["invalid_records"], 0)
        self.assertEqual([item["run_id"] for item in json.loads(out)["runs"]], expected)

    def test_missing_nested_fields_rejected_in_current_and_legacy_records(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        pending = load(self.home, bad_id)
        self.assertEqual(finish(self.home, self.repo, bad_id, finish_payload(repair_passes=1, findings=[finding()]))[0], 0)
        self.assertEqual(run(["outcome", "--run-id", bad_id, "--label", "good"], home=self.home, cwd=self.repo)[0], 0)
        completed = load(self.home, bad_id)
        for schema in (2, 3):
            for original in (pending, completed):
                sample = copy.deepcopy(original)
                sample["schema"] = schema
                if schema == 2:
                    del sample["repo_key"]
                objects = [(name,) for name in ("skill", "client", "plan", "design", "git")]
                if sample["status"] == "completed":
                    objects += [("outcome",), ("findings", 0), ("findings", 0, "location")]
                for location in objects:
                    nested = sample
                    for key in location:
                        nested = nested[key]
                    for field in nested:
                        with self.subTest(schema=schema, status=sample["status"], location=location, field=field):
                            damaged = copy.deepcopy(sample)
                            target = damaged
                            for key in location:
                                target = target[key]
                            del target[field]
                            self.put(bad_id, damaged)
                            self.assert_damage_isolated(good_id, bad_id)

    def test_typed_field_status_date_and_path_damage(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, bad_id, finish_payload(repair_passes=1, findings=[finding()]))[0], 0)
        original = load(self.home, bad_id)
        changes = [
            (("schema",), 2), (("schema",), 4), (("schema",), 3.0),
            (("run_id",), bad_id.upper()), (("run_id",), "bad-uuid"), (("run_id",), 12),
            (("started_at",), "2026-02-30T00:00:00.000000Z"),
            (("started_at",), "2026-01-01T00:00:00Z"),
            (("started_at",), "2026-01-01T00:00:00.000000+00:00"),
            (("completed_at",), "0001-01-01T00:00:00.000000Z"),
            (("elapsed_s",), True), (("elapsed_s",), -1), (("elapsed_s",), 1.5),
            (("skill", "version"), ""), (("skill", "sha256"), "A" * 64),
            (("client", "id"), "unlisted"), (("client", "model"), "x" * 101),
            (("mode",), "unlisted"), (("plan", "sha_end"), None),
            (("design", "sha_start"), "x"), (("git", "head_start"), "A" * 40),
            (("git", "head_end"), None), (("git", "dirty_end"), 0),
            (("abandon_reason",), "other"), (("reviewers",), True),
            (("review_passes",), 0), (("repair_passes",), 3),
            (("degraded_reasons",), "text"), (("findings",), {}),
            (("findings",), [finding(), finding()]),
            (("findings", 0, "repair_pass"), True),
            (("findings", 0, "id"), "wrong"),
            (("outcome",), {"label": "unknown", "note": None, "recorded_at": original["completed_at"]}),
            (("outcome",), {"label": "good", "note": "x" * 301, "recorded_at": original["completed_at"]}),
            (("outcome",), {"label": "good", "note": None, "recorded_at": "not-a-date"}),
            (("outcome",), {"label": "good", "note": None, "recorded_at": original["completed_at"], "extra": 1}),
        ]
        for unsafe in ("/tmp/doc", "../doc", "docs/../doc", "C:/doc", "docs\\doc", "docs//doc", "./doc"):
            for location in (("plan", "path"), ("design", "path"), ("findings", 0, "location", "path"), ("findings", 0, "evidence", 0)):
                changes.append((location, unsafe))
        for location, replacement in changes:
            with self.subTest(location=location, replacement=replacement):
                damaged = copy.deepcopy(original)
                target = damaged
                for key in location[:-1]:
                    target = target[key]
                target[location[-1]] = replacement
                self.put(bad_id, damaged)
                self.assert_damage_isolated(good_id, bad_id)

    def test_deep_or_nonfinite_json_cannot_kill_a_healthy_summary(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        bad_path = self.home / "runs" / f"{bad_id}.json"
        payloads = (b"[" * 1200 + b"0" + b"]" * 1200, b"NaN", b"Infinity", b"-Infinity", b"{broken", b"\xff")
        for raw in payloads:
            with self.subTest(prefix=raw[:20]):
                with self.assertRaises(evidence.EvidenceError) as raised:
                    evidence.parse_json(raw, "synthetic record")
                self.assertEqual(raised.exception.code, "schema-invalid")
                bad_path.write_bytes(raw)
                self.assert_damage_isolated(good_id, bad_id)
        bad_path.write_bytes(b" " * (64 * 1024) + b"{}")
        self.assert_damage_isolated(good_id, bad_id)

    def test_invalid_count_precedes_filters_and_ignores_nested_entries(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        self.put(good_id, {**load(self.home, good_id), "started_at": "2020-01-01T00:00:00.000000Z"})
        bad_path = self.home / "runs" / "not-a-uuid.json"
        bad_path.write_bytes((self.home / "runs" / f"{good_id}.json").read_bytes())
        nested = self.home / "runs" / "nested.json"
        nested.mkdir()
        (nested / "bad.json").write_bytes(b"{broken")
        (self.home / "runs" / "ignored.tmp").write_bytes(b"{broken")
        for filters, expected in ((["--last", "1"], [good_id]), (["--repo", "absent", "--last", "1"], [])):
            code, out, err = run(["summary", *filters], home=self.home, cwd=self.repo)
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out)["invalid_records"], 1)
            self.assertEqual([item["run_id"] for item in json.loads(out)["runs"]], expected)

    def test_typed_contradictions_are_readable_and_finish_accepts_them(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, run_id, finish_payload())[0], 0)
        original = load(self.home, run_id)
        payloads = [
            finish_payload(findings=[finding(status="unresolved", repair_pass=None)]),
            finish_payload(verdict="REVISE"), finish_payload(verdict="BLOCKED"),
            finish_payload(repair_passes=1), finish_payload(reviewers=0),
            finish_payload(execution="degraded"),
            finish_payload(findings=[finding(repair_pass=2)]),
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertEqual(evidence.validate_finish(payload, "default"), payload)
                record = {**original, **payload, "schema": 2}
                del record["repo_key"]
                path = self.put(run_id, record)
                before = path.read_bytes()
                code, out, err = run(["show", "--run-id", run_id], home=self.home, cwd=self.repo)
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(out.encode(), before)
                code, out, err = run(["summary"], home=self.home, cwd=self.repo)
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["invalid_records"], 0)
                self.assertEqual(len(json.loads(out)["runs"]), 1)

    def test_read_io_failure_uses_envelope_and_does_not_hide_healthy_run(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        bad_path = self.home / "runs" / f"{bad_id}.json"
        actual_open = Path.open

        def denied(path, *args, **kwargs):
            if path == bad_path:
                raise PermissionError("synthetic denied path")
            return actual_open(path, *args, **kwargs)

        with mock.patch.object(Path, "open", denied):
            code, out, err = run(["show", "--run-id", bad_id], home=self.home, cwd=self.repo)
            self.assertEqual((code, out), (2, ""))
            self.assertEqual(error_code(err), "evidence-home-unwritable")
            self.assertEqual(len(err.splitlines()), 1)
            code, out, err = run(["summary"], home=self.home, cwd=self.repo)
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out)["invalid_records"], 1)
            self.assertEqual([item["run_id"] for item in json.loads(out)["runs"]], [good_id])
        bad_path.unlink()
        code, out, err = run(["show", "--run-id", bad_id], home=self.home, cwd=self.repo)
        self.assertEqual((code, out), (2, ""))
        self.assertEqual(error_code(err), "run-not-found")

    def test_stat_failure_is_counted_and_uses_storage_error_envelope(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        bad_path = self.home / "runs" / f"{bad_id}.json"
        actual_stat = os.stat

        def denied(path, *args, **kwargs):
            if path == bad_path:
                raise PermissionError("synthetic stat denied")
            return actual_stat(path, *args, **kwargs)

        with mock.patch.object(os, "stat", denied):
            code, out, err = run(["show", "--run-id", bad_id], home=self.home, cwd=self.repo)
            self.assertEqual((code, out), (2, ""))
            self.assertEqual(error_code(err), "evidence-home-unwritable")
            code, out, err = run(["summary"], home=self.home, cwd=self.repo)
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(json.loads(out)["invalid_records"], 1)
            self.assertEqual([item["run_id"] for item in json.loads(out)["runs"]], [good_id])

    def test_escaped_unpaired_surrogates_cannot_crash_summary(self) -> None:
        good_id = start(self.home, self.repo, self.skill)
        bad_id = start(self.home, self.repo, self.skill)
        original = load(self.home, bad_id)
        bad_path = self.home / "runs" / f"{bad_id}.json"
        for surrogate in ("\ud800", "\udfff"):
            with self.subTest(surrogate=repr(surrogate)):
                raw = json.dumps({**original, "repo": surrogate}).encode("utf-8")
                bad_path.write_bytes(raw)
                self.assert_damage_isolated(good_id, bad_id)
        for raw in (b'{"\\ud800": 0}', b'["\\udfff"]'):
            with self.subTest(raw=raw):
                with self.assertRaises(evidence.EvidenceError) as raised:
                    evidence.parse_json(raw, "synthetic")
                self.assertEqual(raised.exception.code, "schema-invalid")
        valid = {**original, "repo": "독서📚"}
        raw = json.dumps(valid).encode("utf-8")
        bad_path.write_bytes(raw)
        code, out, err = run(["show", "--run-id", bad_id], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.encode("utf-8"), raw)
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["invalid_records"], 0)
        self.assertEqual([item["repo"] for item in json.loads(out)["runs"]], ["same", "독서📚"])


class ObservationTests(RecorderFixture):
    def test_blocked_ready_is_preserved_and_separated(self) -> None:
        normal = start(self.home, self.repo, self.skill)
        self.assertEqual(finish(self.home, self.repo, normal, finish_payload())[0], 0)
        suspect = start(self.home, self.repo, self.skill)
        payload = finish_payload(execution="blocked", reviewers=0, verdict="READY")
        code, _, err = finish(self.home, self.repo, suspect, payload)
        self.assertEqual(code, 0, err)
        path = self.home / "runs" / f"{suspect}.json"
        before = path.read_bytes()
        self.assertEqual(load(self.home, suspect)["verdict"], "READY")
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        summary = json.loads(out)
        self.assertIn(suspect, summary["anomalies"]["blocked_execution_with_nonblocked_verdict"])
        self.assertEqual(summary["counts"]["observation"], {"normal": 1, "anomalous": 1})
        self.assertEqual(summary["counts"]["normal_verdict"], {"READY": 1, "REVISE": 0, "BLOCKED": 0})
        self.assertEqual(summary["counts"]["anomalous_verdict"], {"READY": 1, "REVISE": 0, "BLOCKED": 0})
        self.assertEqual(summary["counts"]["verdict"]["READY"], 2)
        self.assertEqual(path.read_bytes(), before)

    def test_same_basename_and_legacy_are_not_checkout_chains(self) -> None:
        first = start(self.home, self.repo, self.skill)
        second = start(self.home, self.repo, self.skill)
        other = make_git_repo(self.workspace / "second", "same")
        third = start(self.home, other, self.skill)
        legacy = start(self.home, self.repo, self.skill)
        record = load(self.home, legacy)
        record["schema"] = 2
        record.pop("repo_key")
        path = self.put(legacy, record)
        before = path.read_bytes()
        code, out, err = run(["summary", "--repo", "same"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        summary = json.loads(out)
        self.assertEqual(len(summary["chains"]), 1)
        chain = summary["chains"][0]
        self.assertEqual([row["run_id"] for row in chain["runs"]], [first, second])
        self.assertEqual((chain["repo"], chain["plan"], chain["repo_key"]), ("same", "docs/plan.md", self.key(first)))
        rows = {row["run_id"]: row for row in summary["runs"]}
        self.assertEqual(rows[legacy]["binding"], "historical-unbound")
        self.assertIsNone(rows[legacy]["repo_key"])
        self.assertEqual(rows[first]["binding"], "checkout-bound")
        self.assertNotEqual(rows[first]["repo_key"], rows[third]["repo_key"])
        self.assertEqual(summary["counts"]["binding"], {"checkout-bound": 3, "historical-unbound": 1})
        self.assertEqual(summary["counts"]["observation"], {"normal": 0, "anomalous": 0})
        self.assertEqual(path.read_bytes(), before)

    def test_multiple_anomalies_are_sorted_without_mutating_observations(self) -> None:
        run_id = start(self.home, self.repo, self.skill, mode="review-only")
        self.assertEqual(evidence.observation_anomalies(load(self.home, run_id)), [])
        payload = finish_payload(execution="degraded", repair_passes=1,
                                 findings=[finding(status="unresolved", repair_pass=2)])
        code, _, err = finish(self.home, self.repo, run_id, payload)
        self.assertEqual((code, err), (0, ""))
        record = load(self.home, run_id)
        before = copy.deepcopy(record)
        self.assertEqual(evidence.observation_anomalies(record), [
            "degraded_without_reason", "finding_repair_pass_exceeds_total",
            "ready_with_unresolved_findings", "repair_without_repaired_finding",
            "review_only_with_repair",
        ])
        self.assertEqual(record, before)
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["counts"]["observation"], {"normal": 0, "anomalous": 1})

    def test_document_only_finding_counts_as_anomalous_observation(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        item = finding(**{"class": "repo-reality"}, evidence=["docs/plan.md"])
        self.assertEqual(finish(self.home, self.repo, run_id,
                               finish_payload(repair_passes=1, findings=[item]))[0], 0)
        self.assertEqual(evidence.observation_anomalies(load(self.home, run_id)), [])
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        summary = json.loads(out)
        self.assertEqual(summary["anomalies"]["repo_reality_citing_documents_only"], [
            {"run_id": run_id, "finding_id": "PSDR-001"},
        ])
        self.assertEqual(summary["counts"]["observation"], {"normal": 0, "anomalous": 1})


if __name__ == "__main__":
    unittest.main()
