from __future__ import annotations

import datetime as dt
import hashlib
import json
import multiprocessing
import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from support import ROOT, make_git_repo, run_git, write

from pre_sdd_review_evidence import repository
from pre_sdd_review_evidence.schema import EvidenceError


def _identity_worker(arguments: tuple[str, str]) -> tuple[str, str]:
    evidence_home, repo_root = arguments
    key = repository.load_or_create_identity(Path(evidence_home))
    return hashlib.sha256(key).hexdigest(), repository.repository_id(Path(repo_root), key)


def _write_private(path: Path, payload: bytes) -> None:
    path.write_bytes(payload)
    if os.name == "posix":
        path.chmod(0o600)


class RepositoryResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)

    def test_root_relative_spec_resolves_and_stores_only_relative_paths(self) -> None:
        repo = make_git_repo(self.workspace)
        write(repo / "docs/plan.md", "# Plan\n\n**Spec:** `docs/design.md`\n")
        write(repo / "docs/design.md", "# Design\n")

        target = repository.resolve_target(repo, Path("docs/plan.md"), b"k" * 32)

        self.assertEqual(target.resolution_status, "resolved")
        self.assertEqual(target.plan_path, "docs/plan.md")
        self.assertEqual(target.design_path, "docs/design.md")
        self.assertNotIn(str(repo), repr(target))

    def test_spec_syntax_and_resolution_axes_are_independent(self) -> None:
        cases = (
            ("plain-root", "docs/design.md", "docs/design.md"),
            ("inline-root", "`docs/design.md`", "docs/design.md"),
            ("plain-plan", "./design.md", "docs/plans/design.md"),
            ("inline-plan", "`./design.md`", "docs/plans/design.md"),
        )
        for name, field_value, expected in cases:
            with self.subTest(name=name):
                workspace = self.workspace / name
                workspace.mkdir()
                repo = make_git_repo(workspace)
                write(repo / "docs/plans/plan.md", f"# Plan\n\n**Spec:** {field_value}\n")
                write(repo / expected, "# Design\n")

                target = repository.resolve_target(
                    repo, Path("docs/plans/plan.md"), b"k" * 32
                )

                self.assertEqual(target.resolution_status, "resolved")
                self.assertEqual(target.design_path, expected)
                self.assertNotIn("`", target.design_path or "")

    def test_invalid_spec_field_forms_fail_closed(self) -> None:
        cases = {
            "empty": "**Spec:**   \n",
            "duplicate": "**Spec:** docs/design.md\n**Spec:** docs/design.md\n",
            "multiple-tokens": "**Spec:** docs/design.md extra.md\n",
            "trailing-prose": "**Spec:** docs/design.md is authoritative\n",
            "multiline": "**Spec:**\n`docs/design.md`\n",
            "fenced": "**Spec:** ```docs/design.md```\n",
            "unbalanced-open": "**Spec:** `docs/design.md\n",
            "unbalanced-close": "**Spec:** docs/design.md`\n",
            "nested-backticks": "**Spec:** `docs/`design.md``\n",
            "absolute": "**Spec:** /tmp/design.md\n",
            "tilde": "**Spec:** ~/design.md\n",
            "parent": "**Spec:** docs/../design.md\n",
        }
        for name, plan_body in cases.items():
            with self.subTest(name=name):
                workspace = self.workspace / name
                workspace.mkdir()
                repo = make_git_repo(workspace)
                write(repo / "docs/plan.md", plan_body)

                target = repository.resolve_target(
                    repo, Path("docs/plan.md"), b"k" * 32
                )

                self.assertEqual(target.resolution_status, "spec-path-invalid")
                self.assertIsNone(target.design_path)

    def test_missing_and_outside_targets_have_exact_safe_projections(self) -> None:
        repo = make_git_repo(self.workspace)
        missing_plan = repository.resolve_target(repo, Path("docs/missing.md"), b"k" * 32)
        self.assertEqual(missing_plan.resolution_status, "plan-missing")
        self.assertEqual(missing_plan.plan_path, "docs/missing.md")
        self.assertIsNone(missing_plan.plan_initial_sha256)

        write(repo / "docs/no-spec.md", "# Plan\n")
        no_spec = repository.resolve_target(repo, Path("docs/no-spec.md"), b"k" * 32)
        self.assertEqual(no_spec.resolution_status, "spec-field-missing")
        self.assertIsNotNone(no_spec.plan_initial_sha256)

        write(repo / "docs/missing-design.md", "**Spec:** docs/absent.md\n")
        missing_design = repository.resolve_target(
            repo, Path("docs/missing-design.md"), b"k" * 32
        )
        self.assertEqual(missing_design.resolution_status, "design-missing")
        self.assertEqual(missing_design.design_path, "docs/absent.md")
        self.assertIsNone(missing_design.design_initial_sha256)

        outside_plan = self.workspace / "outside-plan.md"
        write(outside_plan, "**Spec:** docs/design.md\n")
        outside = repository.resolve_target(repo, outside_plan, b"k" * 32)
        self.assertEqual(outside.resolution_status, "outside-repository")
        self.assertIsNone(outside.plan_path)
        self.assertNotIn(str(outside_plan), repr(outside))

    def test_relative_parent_and_symlink_escapes_are_not_persisted(self) -> None:
        repo = make_git_repo(self.workspace)
        outside = self.workspace / "outside"
        outside.mkdir()
        write(outside / "design.md", "# Outside\n")
        write(repo / "docs/plan.md", "**Spec:** docs/design-link.md\n")
        (repo / "docs/design-link.md").symlink_to(outside / "design.md")

        design_escape = repository.resolve_target(repo, Path("docs/plan.md"), b"k" * 32)
        self.assertEqual(design_escape.resolution_status, "outside-repository")
        self.assertIsNone(design_escape.design_path)

        plan_link = repo / "docs/plan-link.md"
        plan_link.symlink_to(outside / "plan.md")
        write(outside / "plan.md", "**Spec:** docs/design.md\n")
        plan_escape = repository.resolve_target(repo, Path("docs/plan-link.md"), b"k" * 32)
        self.assertEqual(plan_escape.resolution_status, "outside-repository")
        self.assertIsNone(plan_escape.plan_path)

        parent_plan = repository.resolve_target(repo, Path("../outside/plan.md"), b"k" * 32)
        self.assertEqual(parent_plan.resolution_status, "outside-repository")
        self.assertIsNone(parent_plan.plan_path)

    def test_absolute_plan_inside_repository_is_normalized_to_relative(self) -> None:
        repo = make_git_repo(self.workspace)
        write(repo / "docs/plan.md", "**Spec:** docs/design.md\n")
        write(repo / "docs/design.md", "# Design\n")

        target = repository.resolve_target(
            repo / "docs", (repo / "docs/plan.md").resolve(), b"k" * 32
        )

        self.assertEqual(target.resolution_status, "resolved")
        self.assertEqual(target.plan_path, "docs/plan.md")

    def test_non_git_repository_has_no_fabricated_facts(self) -> None:
        target = repository.resolve_target(
            self.workspace, Path("docs/plan.md"), b"k" * 32
        )
        self.assertEqual(target.resolution_status, "not-git-repository")
        self.assertTrue(
            all(
                value is None
                for value in (
                    target.repo_id,
                    target.initial_head,
                    target.initial_dirty,
                    target.plan_path,
                    target.plan_initial_sha256,
                    target.design_path,
                    target.design_initial_sha256,
                )
            )
        )

    def test_git_snapshot_reports_unborn_clean_and_tracked_or_untracked_dirty(self) -> None:
        repo = make_git_repo(self.workspace, initial_commit=False)
        self.assertEqual(repository.git_snapshot(repo), repository.GitSnapshot("unborn", False))

        write(repo / "untracked.txt", "new\n")
        self.assertTrue(repository.git_snapshot(repo).dirty)
        result = run_git(repo, "add", "untracked.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run_git(repo, "commit", "--quiet", "-m", "tracked")
        self.assertEqual(result.returncode, 0, result.stderr)
        write(repo / "untracked.txt", "changed\n")
        self.assertTrue(repository.git_snapshot(repo).dirty)

    def test_document_hashes_and_repository_ids_are_sha256_and_hmac_stable(self) -> None:
        repo = make_git_repo(self.workspace)
        plan = b"**Spec:** docs/design.md\n"
        design = b"# Design\n"
        (repo / "docs").mkdir()
        (repo / "docs/plan.md").write_bytes(plan)
        (repo / "docs/design.md").write_bytes(design)

        first = repository.resolve_target(repo, Path("docs/plan.md"), b"a" * 32)
        second = repository.resolve_target(repo, Path("docs/plan.md"), b"a" * 32)
        different_key = repository.resolve_target(repo, Path("docs/plan.md"), b"b" * 32)
        other_workspace = self.workspace / "other"
        other_workspace.mkdir()
        other_repo = make_git_repo(other_workspace)

        self.assertEqual(first.plan_initial_sha256, hashlib.sha256(plan).hexdigest())
        self.assertEqual(first.design_initial_sha256, hashlib.sha256(design).hexdigest())
        self.assertEqual(len(first.plan_initial_sha256 or ""), 64)
        self.assertEqual(first.repo_id, second.repo_id)
        self.assertNotEqual(first.repo_id, different_key.repo_id)
        self.assertNotEqual(
            repository.repository_id(repo, b"a" * 32),
            repository.repository_id(other_repo, b"a" * 32),
        )

    def test_loaded_skill_snapshot_has_exact_versions_hashes_and_no_root(self) -> None:
        skill_root = ROOT / "skills/pre-sdd-review"

        snapshot = repository.load_skill_snapshot(skill_root)

        self.assertEqual(snapshot.name, "pre-sdd-review")
        self.assertEqual(snapshot.declared_version, "1.3.1")
        self.assertEqual(snapshot.release_version, "1.3.1")
        self.assertEqual(snapshot.cli_version, "1.0.0")
        self.assertEqual(snapshot.schema_version, 1)
        for attribute, relative in (
            ("skill_sha256", "SKILL.md"),
            ("reviewer_protocol_sha256", "references/reviewer-protocol.md"),
            ("release_manifest_sha256", "release.toml"),
        ):
            expected = hashlib.sha256((skill_root / relative).read_bytes()).hexdigest()
            self.assertEqual(getattr(snapshot, attribute), expected)
        self.assertNotIn(str(skill_root), repr(snapshot))

    def test_loaded_skill_snapshot_rejects_version_mismatch(self) -> None:
        copied = self.workspace / "skill"
        shutil.copytree(ROOT / "skills/pre-sdd-review", copied)
        release = copied / "release.toml"
        release.write_text(
            release.read_text(encoding="utf-8").replace('version = "1.3.1"', 'version = "9.9.9"'),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(EvidenceError, "versions"):
            repository.load_skill_snapshot(copied)


class IdentityInitializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.workspace = Path(self.temporary.name)
        self.evidence_home = self.workspace / "evidence"

    def _config(self) -> dict[str, object]:
        return json.loads((self.evidence_home / "config.json").read_text(encoding="utf-8"))

    def test_empty_root_creates_private_key_and_canonical_matching_config(self) -> None:
        key = repository.load_or_create_identity(self.evidence_home)
        config_bytes = (self.evidence_home / "config.json").read_bytes()
        config = json.loads(config_bytes)

        self.assertEqual(len(key), 32)
        self.assertEqual((self.evidence_home / "identity.key").read_bytes(), key)
        self.assertEqual(config["schema_version"], 1)
        self.assertEqual(config["identity_key_sha256"], hashlib.sha256(key).hexdigest())
        self.assertRegex(str(config["created_at"]), r"^\d{4}-\d{2}-\d{2}T.*Z$")
        self.assertEqual(config_bytes, repository.canonical_json_bytes(config))
        if os.name == "posix":
            mode = stat.S_IMODE((self.evidence_home / "identity.key").stat().st_mode)
            self.assertEqual(mode, 0o600)

    def test_concurrent_home_creation_loser_revalidates_winning_directory(self) -> None:
        original_mkdir = Path.mkdir
        canonical_home = self.evidence_home.resolve()

        def racing_mkdir(path: Path, *args: object, **kwargs: object) -> None:
            if Path(path) == canonical_home and not canonical_home.exists():
                os.mkdir(canonical_home, 0o700)
                raise FileExistsError(str(canonical_home))
            original_mkdir(path, *args, **kwargs)

        with mock.patch.object(Path, "mkdir", new=racing_mkdir):
            key = repository.load_or_create_identity(self.evidence_home)

        self.assertEqual(len(key), 32)
        self.assertEqual((self.evidence_home / "identity.key").read_bytes(), key)

    def test_key_only_state_recovers_without_replacing_key(self) -> None:
        self.evidence_home.mkdir()
        self.evidence_home.chmod(0o700)
        key_path = self.evidence_home / "identity.key"
        key = bytes(range(32))
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(key)
            stream.flush()
            os.fsync(stream.fileno())
        before = key_path.stat()

        loaded = repository.load_or_create_identity(self.evidence_home)

        after = key_path.stat()
        self.assertEqual(loaded, key)
        self.assertEqual(after.st_ino, before.st_ino)
        self.assertEqual(after.st_mtime_ns, before.st_mtime_ns)
        self.assertEqual(self._config()["identity_key_sha256"], hashlib.sha256(key).hexdigest())

    def test_interruption_after_key_publication_recovers_same_key(self) -> None:
        with mock.patch.object(
            repository, "_publish_config", side_effect=RuntimeError("interrupted")
        ):
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                repository.load_or_create_identity(self.evidence_home)
        winning_key = (self.evidence_home / "identity.key").read_bytes()
        self.assertFalse((self.evidence_home / "config.json").exists())

        recovered = repository.load_or_create_identity(self.evidence_home)

        self.assertEqual(recovered, winning_key)
        self.assertEqual(self._config()["identity_key_sha256"], hashlib.sha256(winning_key).hexdigest())

    def test_config_only_malformed_wrong_length_mismatch_and_symlinks_fail_closed(self) -> None:
        cases = {
            "config-only": (
                "identity-key-missing",
                "identity config exists without an identity key",
            ),
            "malformed-config": (
                "identity-state-invalid",
                "identity config is unreadable or malformed",
            ),
            "wrong-length": (
                "identity-state-invalid",
                "identity key must contain exactly 32 bytes",
            ),
            "mismatch": (
                "identity-state-invalid",
                "identity config does not match the active key",
            ),
            "key-symlink": (
                "identity-state-invalid",
                "identity.key must be a private regular file",
            ),
            "config-symlink": (
                "identity-state-invalid",
                "config.json must be a private regular file",
            ),
        }
        for name, (expected_code, expected_message) in cases.items():
            with self.subTest(name=name):
                home = self.workspace / name
                home.mkdir()
                home.chmod(0o700)
                key = b"k" * 32
                key_path = home / "identity.key"
                if name != "config-only":
                    key_payload = b"short" if name == "wrong-length" else key
                    key_target = home / "key-target"
                    if name == "key-symlink":
                        _write_private(key_target, key_payload)
                        key_path.symlink_to(key_target)
                    else:
                        _write_private(key_path, key_payload)
                if key_path.is_file() and not key_path.is_symlink():
                    timestamp = dt.datetime(
                        1970, 1, 1, tzinfo=dt.timezone.utc
                    ) + dt.timedelta(microseconds=key_path.stat().st_mtime_ns // 1_000)
                    created_at = timestamp.isoformat(timespec="microseconds").replace(
                        "+00:00", "Z"
                    )
                else:
                    created_at = "2026-08-30T00:00:00.000000Z"
                valid_config = {
                    "schema_version": 1,
                    "created_at": created_at,
                    "identity_key_sha256": hashlib.sha256(key).hexdigest(),
                }
                if name in {"config-only", "malformed-config", "mismatch", "config-symlink"}:
                    payload = repository.canonical_json_bytes(valid_config)
                    if name == "malformed-config":
                        payload = b"{not json"
                    if name == "mismatch":
                        payload = repository.canonical_json_bytes(
                            {**valid_config, "identity_key_sha256": "0" * 64}
                        )
                    config_target = home / "config-target.json"
                    if name == "config-symlink":
                        _write_private(config_target, payload)
                        (home / "config.json").symlink_to(config_target)
                    else:
                        _write_private(home / "config.json", payload)

                with self.assertRaises(EvidenceError) as raised:
                    repository.load_or_create_identity(home)

                self.assertEqual(raised.exception.code, expected_code)
                self.assertEqual(raised.exception.message, expected_message)

    @unittest.skipUnless(os.name == "posix", "POSIX permission proof")
    def test_non_private_identity_entry_has_its_own_explicit_row(self) -> None:
        self.evidence_home.mkdir(mode=0o700)
        key_path = self.evidence_home / "identity.key"
        key_path.write_bytes(b"k" * 32)
        key_path.chmod(0o644)

        with self.assertRaises(EvidenceError) as raised:
            repository.load_or_create_identity(self.evidence_home)

        self.assertEqual(raised.exception.code, "identity-state-invalid")
        self.assertEqual(
            raised.exception.message,
            "identity.key must be a private regular file",
        )

    def test_corrupt_existing_identity_uses_stable_state_error(self) -> None:
        cases = (
            ("malformed-config", b"k" * 32, b"{not json"),
            ("oversized-config", b"k" * 32, b"x" * (repository.IDENTITY_CONFIG_LIMIT + 1)),
            ("oversized-key", b"k" * 33, None),
        )
        for name, key_payload, config_payload in cases:
            with self.subTest(name=name):
                home = self.workspace / f"stable-{name}"
                home.mkdir(mode=0o700)
                key_path = home / "identity.key"
                key_path.write_bytes(key_payload)
                key_path.chmod(0o600)
                if config_payload is not None:
                    config_path = home / "config.json"
                    config_path.write_bytes(config_payload)
                    config_path.chmod(0o600)

                with self.assertRaises(EvidenceError) as raised:
                    repository.load_or_create_identity(home)

                self.assertEqual(raised.exception.code, "identity-state-invalid")

    def test_existing_identity_loads_only_through_shared_bounded_readers(self) -> None:
        expected = repository.load_or_create_identity(self.evidence_home)
        real_open = Path.open
        calls: list[tuple[str, int]] = []

        class BoundedReadProxy:
            def __init__(self, path: Path, stream: object, expected_size: int) -> None:
                self.path = path
                self.stream = stream
                self.expected_size = expected_size
                self.read_count = 0

            def __enter__(self) -> "BoundedReadProxy":
                self.stream.__enter__()  # type: ignore[attr-defined]
                return self

            def __exit__(self, *args: object) -> object:
                return self.stream.__exit__(*args)  # type: ignore[attr-defined]

            def read(self, size: int = -1) -> bytes:
                self.read_count += 1
                self.assert_single_exact_read(size)
                calls.append((self.path.name, size))
                return self.stream.read(size)  # type: ignore[attr-defined,no-any-return]

            def assert_single_exact_read(self, size: int) -> None:
                if self.read_count != 1:
                    raise AssertionError(f"{self.path.name} was read more than once")
                if size != self.expected_size:
                    raise AssertionError(
                        f"{self.path.name} read({size}) != read({self.expected_size})"
                    )

        expected_sizes = {
            "identity.key": repository.IDENTITY_KEY_LIMIT + 1,
            "config.json": repository.IDENTITY_CONFIG_LIMIT + 1,
        }

        def open_spy(path: Path, *args: object, **kwargs: object) -> object:
            stream = real_open(path, *args, **kwargs)
            expected_size = expected_sizes.get(Path(path).name)
            if expected_size is None:
                raise AssertionError(f"unexpected identity read: {path}")
            return BoundedReadProxy(Path(path), stream, expected_size)

        with mock.patch.object(Path, "read_bytes", side_effect=AssertionError("unbounded read_bytes")), mock.patch.object(
            Path, "read_text", side_effect=AssertionError("unbounded read_text")
        ), mock.patch.object(Path, "open", new=open_spy):
            loaded = repository.load_or_create_identity(self.evidence_home)

        self.assertEqual(loaded, expected)
        self.assertCountEqual(
            calls,
            [
                ("identity.key", repository.IDENTITY_KEY_LIMIT + 1),
                ("config.json", repository.IDENTITY_CONFIG_LIMIT + 1),
            ],
        )

    def test_concurrent_empty_root_has_one_fingerprint_and_repository_id(self) -> None:
        repo = make_git_repo(self.workspace)
        arguments = [(str(self.evidence_home), str(repo))] * 12
        context = multiprocessing.get_context("spawn")

        with context.Pool(processes=6) as pool:
            results = pool.map(_identity_worker, arguments)

        self.assertEqual(len({fingerprint for fingerprint, _ in results}), 1)
        self.assertEqual(len({repo_id for _, repo_id in results}), 1)
        key = (self.evidence_home / "identity.key").read_bytes()
        self.assertEqual(self._config()["identity_key_sha256"], hashlib.sha256(key).hexdigest())


if __name__ == "__main__":
    unittest.main()
