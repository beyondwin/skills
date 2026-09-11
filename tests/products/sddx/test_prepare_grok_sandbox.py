import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills/sddx/scripts/prepare_grok_sandbox.py"


def git(cwd, *args):
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
        env={
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        },
    ).stdout.strip()


class SandboxTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="sddx sandbox ")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.repo = self.base / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "--initial-branch=main")
        git(self.repo, "config", "user.name", "SDDx Fixture")
        git(self.repo, "config", "user.email", "sddx@example.invalid")
        hooks = self.base / "empty-hooks"
        hooks.mkdir()
        git(self.repo, "config", "core.hooksPath", str(hooks))
        git(
            self.repo,
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "-m",
            "fixture",
        )
        self.wt = self.base / "linked worktree"
        git(self.repo, "worktree", "add", "-b", "codex/smoke", str(self.wt))
        evidence = self.wt / ".superpowers/sdd/probe"
        evidence.mkdir(parents=True)
        self.state = evidence / "grok-sandbox.json"
        self.config = self.wt / ".grok/sandbox.toml"
        spec = importlib.util.spec_from_file_location("sddx_sandbox", SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def linked_profile(self):
        return {
            "extends": "workspace",
            "read_write": sorted(
                {
                    str((self.repo / ".git").resolve()),
                    git(self.wt, "rev-parse", "--absolute-git-dir"),
                }
            ),
        }

    def test_linked_worktree_prepares_and_cleans(self):
        self.assertEqual(self.module.prepare(self.wt, self.state), "sddx-worktree")
        profile = tomllib.loads(self.config.read_text())["profiles"][
            "sddx-worktree"
        ]
        self.assertEqual(profile, self.linked_profile())
        self.module.cleanup(self.wt, self.state)
        self.assertFalse(self.config.exists())
        self.assertFalse(self.state.exists())
        self.assertFalse(self.config.parent.exists())

    def test_existing_bytes_survive_repeated_prepare(self):
        self.config.parent.mkdir()
        before = b'# user comment\r\n[profiles.review]\r\nextends = "read-only"\r\n'
        self.config.write_bytes(before)
        self.module.prepare(self.wt, self.state)
        journal = self.state.read_bytes()
        self.module.prepare(self.wt, self.state)
        self.assertEqual(self.state.read_bytes(), journal)
        self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), before)

    def test_cleanup_preserves_intervening_edit(self):
        self.module.prepare(self.wt, self.state)
        changed = self.config.read_bytes() + b"\n# user changed this\n"
        self.config.write_bytes(changed)
        with self.assertRaises(ValueError):
            self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), changed)
        self.assertTrue(self.state.exists())

    def test_bad_or_conflicting_toml_is_untouched(self):
        self.config.parent.mkdir()
        cases = (
            b"[broken",
            b"profiles = 7\n",
            b'[profiles.sddx-worktree]\nextends = "off"\n',
        )
        for before in cases:
            with self.subTest(before=before):
                self.config.write_bytes(before)
                with self.assertRaises(ValueError):
                    self.module.prepare(self.wt, self.state)
                self.assertEqual(self.config.read_bytes(), before)
                self.assertFalse(self.state.exists())

    def test_regular_checkout_needs_no_extra_git_write_paths(self):
        evidence = self.repo / ".superpowers/sdd/probe"
        evidence.mkdir(parents=True)
        state = evidence / "grok-sandbox.json"
        config = self.repo / ".grok/sandbox.toml"

        self.module.prepare(self.repo, state)

        profile = tomllib.loads(config.read_text())["profiles"]["sddx-worktree"]
        self.assertEqual(profile["read_write"], [])
        self.module.cleanup(self.repo, state)
        self.assertFalse(config.exists())
        self.assertFalse(state.exists())
        self.assertFalse(config.parent.exists())

    def test_matching_existing_profile_is_reused_without_rewrite(self):
        self.config.parent.mkdir()
        before = (
            "# keep this exact text\r\n"
            "[profiles.sddx-worktree]\r\n"
            'extends = "workspace"\r\n'
            f"read_write = {json.dumps(self.linked_profile()['read_write'])}\r\n"
        ).encode()
        self.config.write_bytes(before)

        self.module.prepare(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), before)
        self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), before)

    def test_existing_profile_with_extra_field_is_rejected(self):
        self.config.parent.mkdir()
        before = (
            "[profiles.sddx-worktree]\n"
            'extends = "workspace"\n'
            f"read_write = {json.dumps(self.linked_profile()['read_write'])}\n"
            "restrict_network = true\n"
        ).encode()
        self.config.write_bytes(before)

        with self.assertRaises(ValueError):
            self.module.prepare(self.wt, self.state)

        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.state.exists())

    def test_config_symlink_is_rejected_without_touching_target(self):
        sentinel = self.base / "sentinel.toml"
        before = b"sentinel bytes\n"
        sentinel.write_bytes(before)
        self.config.parent.mkdir()
        self.config.symlink_to(sentinel)

        with self.assertRaises(ValueError):
            self.module.prepare(self.wt, self.state)
        with self.assertRaises(ValueError):
            self.module.cleanup(self.wt, self.state)

        self.assertEqual(sentinel.read_bytes(), before)
        self.assertFalse(self.state.exists())

    def test_grok_directory_symlink_is_rejected_without_touching_target(self):
        sentinel_dir = self.base / "sentinel grok"
        sentinel_dir.mkdir()
        sentinel = sentinel_dir / "sandbox.toml"
        before = b"sentinel bytes\n"
        sentinel.write_bytes(before)
        (self.wt / ".grok").symlink_to(sentinel_dir, target_is_directory=True)

        with self.assertRaises(ValueError):
            self.module.prepare(self.wt, self.state)
        with self.assertRaises(ValueError):
            self.module.cleanup(self.wt, self.state)

        self.assertEqual(sentinel.read_bytes(), before)
        self.assertFalse(self.state.exists())

    def test_state_symlink_is_rejected_without_touching_target(self):
        sentinel = self.base / "sentinel.json"
        before = b"sentinel bytes\n"
        sentinel.write_bytes(before)
        self.state.symlink_to(sentinel)

        with self.assertRaises(ValueError):
            self.module.prepare(self.wt, self.state)
        with self.assertRaises(ValueError):
            self.module.cleanup(self.wt, self.state)

        self.assertEqual(sentinel.read_bytes(), before)

    def test_state_parent_symlink_is_rejected_without_touching_target(self):
        outside = self.base / "outside evidence"
        outside.mkdir()
        sentinel = outside / "sentinel"
        before = b"sentinel bytes\n"
        sentinel.write_bytes(before)
        linked_parent = self.wt / ".superpowers/sdd/linked"
        linked_parent.symlink_to(outside, target_is_directory=True)
        state = linked_parent / "grok-sandbox.json"

        with self.assertRaises(ValueError):
            self.module.prepare(self.wt, state)
        with self.assertRaises(ValueError):
            self.module.cleanup(self.wt, state)

        self.assertEqual(sentinel.read_bytes(), before)
        self.assertFalse((outside / "grok-sandbox.json").exists())

    def test_non_regular_config_and_state_are_rejected(self):
        self.config.parent.mkdir()
        self.config.mkdir()
        with self.subTest(path="config"):
            with self.assertRaises(ValueError):
                self.module.prepare(self.wt, self.state)
            with self.assertRaises(ValueError):
                self.module.cleanup(self.wt, self.state)
        self.config.rmdir()

        self.state.mkdir()
        with self.subTest(path="state"):
            with self.assertRaises(ValueError):
                self.module.prepare(self.wt, self.state)
            with self.assertRaises(ValueError):
                self.module.cleanup(self.wt, self.state)

    def test_short_write_during_prepare_preserves_original_and_recovery(self):
        self.config.parent.mkdir()
        before = b"# original config\r\n"
        self.config.write_bytes(before)
        real_write = os.write
        writes = 0

        def short_then_fail(fd, data):
            nonlocal writes
            writes += 1
            if writes == 1:
                return real_write(fd, data[: max(1, len(data) // 2)])
            raise OSError("injected write failure")

        with mock.patch.object(self.module.os, "write", side_effect=short_then_fail):
            with self.assertRaises(OSError):
                self.module.prepare(self.wt, self.state)

        self.assertGreaterEqual(writes, 2)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertTrue(self.state.exists())
        self.assertEqual(list(self.config.parent.glob(".sandbox.toml.*.tmp")), [])

        self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.state.exists())

    def test_atomic_restore_failure_keeps_applied_config_and_journal(self):
        self.config.parent.mkdir()
        before = b"# original config\r\n"
        self.config.write_bytes(before)
        self.module.prepare(self.wt, self.state)
        applied = self.config.read_bytes()

        with mock.patch.object(
            self.module.os, "replace", side_effect=OSError("injected replace failure")
        ):
            with self.assertRaises(OSError):
                self.module.cleanup(self.wt, self.state)

        self.assertEqual(self.config.read_bytes(), applied)
        self.assertTrue(self.state.exists())
        self.assertEqual(list(self.config.parent.glob(".sandbox.toml.*.tmp")), [])

        self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.state.exists())

    def test_invalid_journal_is_rejected_without_changing_config(self):
        self.config.parent.mkdir()
        before = b"# user config\n"
        self.config.write_bytes(before)
        cases = (
            {
                "worktree": str(self.repo),
                "before": before.decode(),
                "after": before.decode(),
                "created_dir": False,
            },
            {
                "worktree": str(self.wt),
                "before": 7,
                "after": before.decode(),
                "created_dir": False,
            },
        )
        for journal in cases:
            with self.subTest(journal=journal):
                self.state.write_text(json.dumps(journal))
                with self.assertRaises(ValueError):
                    self.module.cleanup(self.wt, self.state)
                self.assertEqual(self.config.read_bytes(), before)
                self.state.unlink()

    def test_cleanup_after_interrupted_prepare_keeps_original_bytes(self):
        self.config.parent.mkdir()
        before = b"# original\r\n"
        self.config.write_bytes(before)
        after = self.module.profile_text(before.decode(), self.linked_profile())
        self.state.write_text(
            json.dumps(
                {
                    "worktree": str(self.wt),
                    "before": before.decode(),
                    "after": after,
                    "created_dir": False,
                }
            )
        )

        self.module.cleanup(self.wt, self.state)

        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.state.exists())

    def test_prepare_resumes_after_journal_was_written_first(self):
        self.config.parent.mkdir()
        before = b"# original\r\n"
        self.config.write_bytes(before)
        after = self.module.profile_text(before.decode(), self.linked_profile())
        journal = {
            "worktree": str(self.wt),
            "before": before.decode(),
            "after": after,
            "created_dir": False,
        }
        self.state.write_text(json.dumps(journal))

        self.assertEqual(self.module.prepare(self.wt, self.state), "sddx-worktree")

        self.assertEqual(self.config.read_bytes().decode("utf-8"), after)
        self.assertEqual(json.loads(self.state.read_text()), journal)
        self.module.cleanup(self.wt, self.state)
        self.assertEqual(self.config.read_bytes(), before)

    def test_cleanup_can_run_twice(self):
        self.config.parent.mkdir()
        before = b"# original\n"
        self.config.write_bytes(before)
        self.module.prepare(self.wt, self.state)

        self.module.cleanup(self.wt, self.state)
        self.module.cleanup(self.wt, self.state)

        self.assertEqual(self.config.read_bytes(), before)

    def test_state_parent_must_exist_inside_worktree_superpowers(self):
        outside = self.base / "outside"
        outside.mkdir()
        cases = (
            outside / "grok-sandbox.json",
            self.wt / ".superpowers/sdd/missing/grok-sandbox.json",
        )
        for state in cases:
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.module.prepare(self.wt, state)
        self.assertFalse(self.config.exists())

    def test_cli_success_prints_exact_json(self):
        prepare = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "prepare",
                "--worktree",
                str(self.wt),
                "--state",
                str(self.state),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(prepare.returncode, 0)
        self.assertEqual(prepare.stdout, '{"profile": "sddx-worktree"}\n')
        self.assertEqual(prepare.stderr, "")

        cleanup = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "cleanup",
                "--worktree",
                str(self.wt),
                "--state",
                str(self.state),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(cleanup.returncode, 0)
        self.assertEqual(cleanup.stdout, '{"cleaned": true}\n')
        self.assertEqual(cleanup.stderr, "")

    def test_cli_failure_has_no_success_json(self):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "prepare",
                "--worktree",
                str(self.base),
                "--state",
                str(self.state),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.startswith("BLOCKED:"))


if __name__ == "__main__":
    unittest.main()
