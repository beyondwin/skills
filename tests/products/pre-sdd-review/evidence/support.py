from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
EVIDENCE_ROOT = ROOT / "skills" / "pre-sdd-review" / "evidence"
if str(EVIDENCE_ROOT) not in sys.path:
    sys.path.insert(0, str(EVIDENCE_ROOT))


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_git_repo(workspace: Path, *, initial_commit: bool = True) -> Path:
    repo = workspace / "repo"
    repo.mkdir(parents=True)
    result = run_git(repo, "init", "--quiet")
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    for key, value in (
        ("user.name", "Pre SDD Evidence Tests"),
        ("user.email", "pre-sdd-evidence@example.invalid"),
    ):
        result = run_git(repo, "config", key, value)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    if initial_commit:
        write(repo / ".gitignore", "\n")
        result = run_git(repo, "add", ".gitignore")
        if result.returncode != 0:
            raise AssertionError(result.stderr)
        result = run_git(repo, "commit", "--quiet", "-m", "initial")
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    return repo
