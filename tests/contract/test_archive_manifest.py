from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.capture_archive_manifest import (  # noqa: E402
    CAPTURE_SCRIPT,
    build_manifest,
    canonical_bytes,
    verify_manifest,
)


SKILL_BYTES = b"name: skill-a\n"


def run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def init_repository(root: Path) -> None:
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.email", "manifest-test@example.com")
    run_git(root, "config", "user.name", "Manifest Test")
    run_git(root, "config", "commit.gpgsign", "false")
    run_git(root, "remote", "add", "origin", "https://github.com/beyondwin/Archive.git")


def commit_tree(root: Path, message: str) -> None:
    run_git(root, "add", "-A")
    run_git(root, "commit", "-m", message)
    run_git(root, "update-ref", "refs/remotes/origin/main", "HEAD")


class ArchiveManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.repository = Path(self._tempdir.name)
        init_repository(self.repository)
        skill = self.repository / "skills" / "a" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_bytes(SKILL_BYTES)
        commit_tree(self.repository, "seed skill-a")

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_build_manifest_records_git_and_byte_identity(self) -> None:
        manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
        entry = manifest["entries"][0]
        self.assertEqual(entry["mode"], "100644")
        self.assertRegex(entry["blob_oid"], r"^[0-9a-f]{40}$")
        self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(entry["size"], len(SKILL_BYTES))
        self.assertEqual(entry["path"], "skills/a/SKILL.md")
        self.assertEqual(manifest["source_repository"], "https://github.com/beyondwin/Archive.git")
        self.assertEqual(manifest["source_commit"], run_git(self.repository, "rev-parse", "HEAD"))
        self.assertEqual(manifest["schema_version"], 1)

    def test_verify_manifest_rejects_source_drift(self) -> None:
        manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
        (self.repository / "skills/a/SKILL.md").write_text("changed\n")
        self.assertIn("source tree differs from manifest", verify_manifest(self.repository, manifest))

    def test_manifest_digest_matches_canonical_payload(self) -> None:
        manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
        recorded = manifest["manifest_sha256"]
        payload = dict(manifest)
        del payload["manifest_sha256"]
        self.assertEqual(recorded, hashlib.sha256(canonical_bytes(payload)).hexdigest())
        self.assertRegex(recorded, r"^[0-9a-f]{64}$")
        rebuilt = json.loads(canonical_bytes(manifest).decode())
        self.assertEqual(rebuilt, manifest)

    def test_verify_manifest_rejects_digest_mismatch(self) -> None:
        manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
        manifest["manifest_sha256"] = "0" * 64
        self.assertIn("manifest digest mismatch", verify_manifest(self.repository, manifest))

    def test_identifier_hit_under_prefix_is_source(self) -> None:
        manifest = build_manifest(self.repository, ("skills/a/",), ("skill-a",))
        self.assertEqual(
            manifest["identifier_hits"],
            [{"path": "skills/a/SKILL.md", "class": "source"}],
        )


class IdentifierClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.repository = Path(self._tempdir.name)
        init_repository(self.repository)
        (self.repository / "skills/korean-writing-editor").mkdir(parents=True)
        (self.repository / "skills/korean-writing-editor/SKILL.md").write_text(
            "name: korean-writing-editor\n"
        )
        (self.repository / "AGENTS.md").write_text("mixed korean-writing-editor routing\n")
        (self.repository / "README.md").write_text("catalog korean-writing-editor\n")
        (self.repository / "skills/AGENTS.md").write_text("route korean-writing-editor\n")
        (self.repository / "skills/README.md").write_text("catalog korean-writing-editor\n")
        agent = self.repository / "scripts/agent"
        agent.mkdir(parents=True)
        (agent / "verification-map.ts").write_text('id: "korean-writing-editor"\n')
        (agent / "contract.ts").write_text("skills/korean-writing-editor\n")
        history = self.repository / "docs/superpowers/plans"
        history.mkdir(parents=True)
        (history / "2026-08-22-kws-korean-writing-editor.md").write_text(
            "history of korean-writing-editor\n"
        )
        (self.repository / "docs/operations").mkdir(parents=True)
        (self.repository / "docs/operations/note.md").write_text("korean-writing-editor live\n")
        mixed = (
            self.repository
            / "skills/_legacy/kws-codex-plan-runner/evals/test_skill_contract.py"
        )
        mixed.parent.mkdir(parents=True)
        mixed.write_text("assert korean-writing-editor catalog row\n")
        commit_tree(self.repository, "classified hits")
        residue = (
            self.repository
            / "skills/kws-korean-writing-editor/evals/__pycache__/live_matrix.pyc"
        )
        residue.parent.mkdir(parents=True)
        residue.write_bytes(b"\x00korean-writing-editor")
        worktree = (
            self.repository
            / ".superpowers/worktrees/kws-korean-writing-editor-live-hardening"
        )
        worktree.mkdir(parents=True)
        (worktree / "ignored.txt").write_text("kws-korean-writing-editor residue\n")

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_every_hit_receives_a_known_class(self) -> None:
        manifest = build_manifest(
            self.repository,
            ("skills/korean-writing-editor/", "skills/image-workbench/"),
            (
                "korean-writing-editor",
                "image-workbench",
                "kws-korean-writing-editor",
                "kws-image-workbench",
            ),
        )
        classes = {hit["class"] for hit in manifest["identifier_hits"]}
        self.assertTrue(classes <= {
            "source",
            "active-routing",
            "verification-registration",
            "skill-history-document",
            "mixed-document",
            "generated-residue",
        })
        by_path = {hit["path"]: hit["class"] for hit in manifest["identifier_hits"]}
        self.assertEqual(by_path["skills/korean-writing-editor/SKILL.md"], "source")
        self.assertEqual(by_path["skills/AGENTS.md"], "active-routing")
        self.assertEqual(by_path["skills/README.md"], "active-routing")
        self.assertEqual(by_path["scripts/agent/verification-map.ts"], "verification-registration")
        self.assertEqual(by_path["scripts/agent/contract.ts"], "verification-registration")
        self.assertEqual(
            by_path["docs/superpowers/plans/2026-08-22-kws-korean-writing-editor.md"],
            "skill-history-document",
        )
        self.assertEqual(by_path["docs/operations/note.md"], "skill-history-document")
        self.assertEqual(by_path["AGENTS.md"], "mixed-document")
        self.assertEqual(by_path["README.md"], "mixed-document")
        self.assertEqual(
            by_path["skills/_legacy/kws-codex-plan-runner/evals/test_skill_contract.py"],
            "mixed-document",
        )
        self.assertEqual(
            by_path["skills/kws-korean-writing-editor/evals/__pycache__/live_matrix.pyc"],
            "generated-residue",
        )
        self.assertEqual(
            by_path[".superpowers/worktrees/kws-korean-writing-editor-live-hardening"],
            "generated-residue",
        )
        self.assertNotIn("unclassified", classes)


class CaptureCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        root = Path(self._tempdir.name)
        self.repository = root / "source"
        self.output_dir = root / "output"
        self.repository.mkdir()
        self.output_dir.mkdir()
        init_repository(self.repository)
        skill = self.repository / "skills" / "a" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_bytes(SKILL_BYTES)
        commit_tree(self.repository, "seed skill-a")

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CAPTURE_SCRIPT), *arguments],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
        )

    def test_capture_and_verify_round_trip(self) -> None:
        output = self.output_dir / "manifest.json"
        captured = self._run_cli(
            "capture",
            "--repository",
            str(self.repository),
            "--output",
            str(output),
            "--prefix",
            "skills/a/",
            "--identifier",
            "skill-a",
        )
        self.assertEqual(captured.returncode, 0, captured.stderr)
        verified = self._run_cli(
            "verify",
            "--repository",
            str(self.repository),
            "--manifest",
            str(output),
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["entries"][0]["size"], len(SKILL_BYTES))

    def test_capture_rejects_dirty_source(self) -> None:
        (self.repository / "skills/a/SKILL.md").write_text("dirty\n")
        output = self.output_dir / "manifest.json"
        captured = self._run_cli(
            "capture",
            "--repository",
            str(self.repository),
            "--output",
            str(output),
            "--prefix",
            "skills/a/",
            "--identifier",
            "skill-a",
        )
        self.assertNotEqual(captured.returncode, 0)
        self.assertIn("dirty source", captured.stderr)

    def test_capture_rejects_detached_source(self) -> None:
        run_git(self.repository, "checkout", "--detach", "HEAD")
        output = self.output_dir / "manifest.json"
        captured = self._run_cli(
            "capture",
            "--repository",
            str(self.repository),
            "--output",
            str(output),
            "--prefix",
            "skills/a/",
            "--identifier",
            "skill-a",
        )
        self.assertNotEqual(captured.returncode, 0)
        self.assertIn("detached source", captured.stderr)

    def test_capture_rejects_head_not_origin_main(self) -> None:
        (self.repository / "skills/a/SKILL.md").write_text("ahead of origin\n")
        run_git(self.repository, "add", "skills/a/SKILL.md")
        run_git(self.repository, "commit", "-m", "local-only commit")
        output = self.output_dir / "manifest.json"
        captured = self._run_cli(
            "capture",
            "--repository",
            str(self.repository),
            "--output",
            str(output),
            "--prefix",
            "skills/a/",
            "--identifier",
            "skill-a",
        )
        self.assertNotEqual(captured.returncode, 0)
        self.assertIn("HEAD differs from origin/main", captured.stderr)

    def test_capture_rejects_symlink_in_prefix(self) -> None:
        target = self.repository / "skills/a/SKILL.md"
        link = self.repository / "skills/a/link.md"
        link.symlink_to(target.name)
        run_git(self.repository, "add", "skills/a/link.md")
        run_git(self.repository, "commit", "-m", "add symlink")
        run_git(self.repository, "update-ref", "refs/remotes/origin/main", "HEAD")
        output = self.output_dir / "manifest.json"
        captured = self._run_cli(
            "capture",
            "--repository",
            str(self.repository),
            "--output",
            str(output),
            "--prefix",
            "skills/a/",
            "--identifier",
            "skill-a",
        )
        self.assertNotEqual(captured.returncode, 0)
        self.assertIn("symlink or special file", captured.stderr)


if __name__ == "__main__":
    unittest.main()
