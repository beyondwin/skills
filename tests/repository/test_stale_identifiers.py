from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.stale_identifiers import (  # noqa: E402
    IdentifierHit,
    tracked_identifier_hits,
)


STALE_ID = "gra" + "spic"
CHANGELOG = "skills/how-it-works/CHANGELOG.md"


def run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def make_git_fixture(root: Path) -> Path:
    run_git(root, "init", "-b", "main")
    run_git(root, "config", "user.email", "stale-id-test@example.com")
    run_git(root, "config", "user.name", "Stale Identifier Test")
    run_git(root, "config", "commit.gpgsign", "false")
    return root


def write_and_commit(repository: Path, relative: str, content: str | bytes) -> None:
    path = repository / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    run_git(repository, "add", "--", relative)
    run_git(repository, "commit", "-m", f"add {relative}")


class StaleIdentityGateTests(unittest.TestCase):
    def test_active_tree_has_no_stale_identity(self) -> None:
        self.assertEqual(tracked_identifier_hits(ROOT, STALE_ID), ())

    def test_history_and_migration_note_are_the_only_allowances(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = make_git_fixture(Path(directory))
            write_and_commit(repository, "docs/history/plans/old.md", STALE_ID)
            write_and_commit(repository, CHANGELOG, STALE_ID)
            self.assertEqual(tracked_identifier_hits(repository, STALE_ID), ())
            write_and_commit(repository, "README.md", STALE_ID)
            self.assertEqual(
                tracked_identifier_hits(repository, STALE_ID)[0].path,
                "README.md",
            )

    def test_changelog_migration_note_is_under_dated_heading(self) -> None:
        text = (ROOT / CHANGELOG).read_text(encoding="utf-8")
        heading = "## 1.0.0 - 2026-08-28"
        self.assertIn(heading, text)
        section = text.split(heading, 1)[1]
        next_heading = section.find("\n## ")
        body = section if next_heading < 0 else section[:next_heading]
        self.assertIn(STALE_ID, body)
        lowered = body.lower()
        self.assertIn("unpublished working identity", lowered)
        self.assertIn("no alias", lowered)
        self.assertIn("how-it-works", body)
        self.assertIn("install", lowered)
        self.assertIn("invoke", lowered)


class TrackedIdentifierScannerTests(unittest.TestCase):
    def test_path_and_content_hits_are_reported_sorted_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = make_git_fixture(Path(directory))
            write_and_commit(repository, CHANGELOG, "ok\n")
            write_and_commit(
                repository,
                "notes/b.md",
                f"once {STALE_ID} twice {STALE_ID}\n",
            )
            write_and_commit(
                repository,
                f"notes/{STALE_ID}.md",
                f"also {STALE_ID}\n",
            )
            hits = tracked_identifier_hits(repository, STALE_ID)
            self.assertEqual(
                hits,
                (
                    IdentifierHit(path="notes/b.md", location="content"),
                    IdentifierHit(path=f"notes/{STALE_ID}.md", location="content"),
                    IdentifierHit(path=f"notes/{STALE_ID}.md", location="path"),
                ),
            )

    def test_binary_files_are_tolerated_and_untracked_files_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = make_git_fixture(Path(directory))
            write_and_commit(repository, CHANGELOG, "ok\n")
            write_and_commit(
                repository,
                "assets/blob.bin",
                b"\x00\xff" + STALE_ID.encode("ascii") + b"\x00",
            )
            untracked = repository / "UNTRACKED.md"
            untracked.write_text(STALE_ID, encoding="utf-8")
            self.assertEqual(tracked_identifier_hits(repository, STALE_ID), ())

    def test_missing_allowlisted_changelog_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = make_git_fixture(Path(directory))
            write_and_commit(repository, "README.md", "ok\n")
            with self.assertRaises(ValueError) as raised:
                tracked_identifier_hits(repository, STALE_ID)
            self.assertIn(CHANGELOG, str(raised.exception))

    def test_leading_dot_github_paths_are_content_scanned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = make_git_fixture(Path(directory))
            write_and_commit(repository, CHANGELOG, "ok\n")
            write_and_commit(
                repository,
                ".github/ISSUE_TEMPLATE/bug.yml",
                f"body: {STALE_ID}\n",
            )
            self.assertEqual(
                tracked_identifier_hits(repository, STALE_ID),
                (
                    IdentifierHit(
                        path=".github/ISSUE_TEMPLATE/bug.yml",
                        location="content",
                    ),
                ),
            )


if __name__ == "__main__":
    unittest.main()
