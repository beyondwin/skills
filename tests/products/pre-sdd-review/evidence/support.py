from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = ROOT / "skills" / "pre-sdd-review" / "evidence"
if str(EVIDENCE_DIR) not in sys.path:
    sys.path.insert(0, str(EVIDENCE_DIR))

import evidence  # noqa: E402

SKILL_MD = (
    "---\n"
    "name: pre-sdd-review\n"
    "description: synthetic\n"
    "metadata:\n"
    '  version: "2.0.0"\n'
    "---\n\n# Pre-SDD Review\n"
)
PROTOCOL_MD = "# Reviewer protocol\n\nRead-only.\n"


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_git_repo(workspace: Path, name: str = "repo") -> Path:
    repo = workspace / name
    repo.mkdir(parents=True)
    for args in (
        ("init", "--quiet"),
        ("config", "user.name", "Evidence Tests"),
        ("config", "user.email", "evidence@example.invalid"),
    ):
        result = run_git(repo, *args)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    write(repo / "docs/design.md", "# Design\n")
    write(repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n")
    write(repo / "src/app.ts", "export const app = 1;\n")
    for args in (("add", "."), ("commit", "--quiet", "-m", "initial")):
        result = run_git(repo, *args)
        if result.returncode != 0:
            raise AssertionError(result.stderr)
    return repo


def commit_all(repo: Path, message: str = "change") -> None:
    for args in (("add", "."), ("commit", "--quiet", "-m", message)):
        result = run_git(repo, *args)
        if result.returncode != 0:
            raise AssertionError(result.stderr)


def make_skill_root(workspace: Path, version: str = "2.0.0") -> Path:
    root = workspace / "skill"
    write(root / "SKILL.md", SKILL_MD.replace('"2.0.0"', f'"{version}"'))
    write(root / "references/reviewer-protocol.md", PROTOCOL_MD)
    return root


def run(argv: list[str], *, home: Path, cwd: Path, stdin_text: str = "") -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = evidence.main(
        list(argv),
        stdin=io.StringIO(stdin_text),
        stdout=out,
        stderr=err,
        environ={"PRE_SDD_REVIEW_HOME": str(home)},
        cwd=cwd,
    )
    return code, out.getvalue(), err.getvalue()


def error_code(stderr_text: str) -> str:
    return json.loads(stderr_text)["error"]["code"]


def start(
    home: Path,
    repo: Path,
    skill_root: Path,
    *,
    design: bool = True,
    client: str = "codex",
    model: str = "gpt-test",
    mode: str = "default",
) -> str:
    argv = [
        "start",
        "--skill-root", str(skill_root),
        "--repo", str(repo),
        "--plan", str(repo / "docs/plan.md"),
        "--client", client,
        "--model", model,
        "--mode", mode,
    ]
    if design:
        argv += ["--design", str(repo / "docs/design.md")]
    code, out, err = run(argv, home=home, cwd=repo)
    if code != 0:
        raise AssertionError(err)
    return json.loads(out)["run_id"]


def finding(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "id": "PSDR-001",
        "severity": "IMPORTANT",
        "class": "verification-gap",
        "pattern": "build-only-acceptance",
        "status": "repaired",
        "repair_pass": 1,
        "location": {"path": "docs/plan.md", "locator": "Task 2"},
        "evidence": ["src/app.ts"],
        "consequence": "A build-only check passes a wrong implementation.",
        "fix": "Add a behavioral unit test to Task 2.",
    }
    value.update(overrides)
    return value


def finish_payload(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "execution": "full",
        "reviewers": 1,
        "trigger": None,
        "degraded_reasons": [],
        "verdict": "READY",
        "block_reason": None,
        "review_passes": 1,
        "repair_passes": 0,
        "findings": [],
    }
    value.update(overrides)
    return value


def finish(home: Path, repo: Path, run_id: str, payload: dict[str, object]) -> tuple[int, str, str]:
    return run(
        ["finish", "--run-id", run_id, "--repo", str(repo)],
        home=home,
        cwd=repo,
        stdin_text=json.dumps(payload),
    )


def load(home: Path, run_id: str) -> dict[str, object]:
    return json.loads((home / "runs" / f"{run_id}.json").read_text(encoding="utf-8"))
