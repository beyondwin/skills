from __future__ import annotations

import subprocess
import sys
import datetime as dt
import json
import uuid
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


def fixed_skill() -> dict[str, object]:
    digest = "a" * 64
    return {
        "name": "pre-sdd-review",
        "declared_version": "1.2.0",
        "release_version": "1.2.0",
        "skill_sha256": digest,
        "reviewer_protocol_sha256": "b" * 64,
        "release_manifest_sha256": "c" * 64,
        "cli_version": "1.0.0",
        "schema_version": 1,
    }


def fixed_target(*, status: str = "resolved") -> dict[str, object]:
    if status == "not-git-repository":
        return {
            "repo_id": None,
            "initial_head": None,
            "initial_dirty": None,
            "plan_path": None,
            "plan_initial_sha256": None,
            "design_path": None,
            "design_initial_sha256": None,
            "resolution_status": status,
        }
    return {
        "repo_id": "d" * 64,
        "initial_head": "1" * 40,
        "initial_dirty": False,
        "plan_path": "docs/plan.md",
        "plan_initial_sha256": "e" * 64,
        "design_path": "docs/design.md",
        "design_initial_sha256": "f" * 64,
        "resolution_status": status,
    }


def pending_record(
    *,
    run_id: str | None = None,
    status: str = "resolved",
    mode: str = "default",
    started_at: str = "2026-08-30T10:00:00Z",
    binding: str = "9" * 64,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "record_type": "pending",
        "run_id": run_id or str(uuid.uuid4()),
        "started_at": started_at,
        "skill": fixed_skill(),
        "client": {"id": "cursor", "version": None, "model": None},
        "target": fixed_target(status=status),
        "intended_mode": mode,
        "start_locator_binding": binding,
    }


def completed_review(
    pending: dict[str, object],
    *,
    verdict: str = "READY",
    completed_at: str = "2026-08-30T10:04:12Z",
) -> dict[str, object]:
    target = json.loads(json.dumps(pending["target"]))
    non_git = target["resolution_status"] == "not-git-repository"
    findings: list[dict[str, object]] = []
    if verdict == "REVISE":
        findings = [{
            "id": "PSDR-001",
            "severity": "IMPORTANT",
            "class": "verification-gap",
            "pattern_key": "missing-proof",
            "consequence_category": "avoidable-rework",
            "status": "unresolved",
            "location": {"path": "docs/plan.md", "locator": "Verification"},
            "evidence_refs": ["docs/plan.md#verification"],
            "consequence": "Behavior is not proved.",
            "minimal_fix": "Add focused behavioral proof.",
            "repair_pass": None,
        }]
    block_reason = "repository-unavailable" if verdict == "BLOCKED" else None
    return {
        "schema_version": 1,
        "record_type": "review",
        "run_id": pending["run_id"],
        "started_at": pending["started_at"],
        "completed_at": completed_at,
        "skill": pending["skill"],
        "client": pending["client"],
        "protocol": {
            "mode": pending["intended_mode"],
            "execution": "blocked" if non_git else "full",
            "reviewer_count": 0 if non_git else 1,
            "fresh_reviewer": False if non_git else True,
            "read_only_enforced": False if non_git else True,
            "conditional_trigger": None,
            "degraded_reasons": [],
        },
        "target": target,
        "result": {
            "completion": "completed",
            "verdict": "BLOCKED" if non_git else verdict,
            "block_reason": "repository-unavailable" if non_git else block_reason,
            "completion_reason": None,
            "review_passes": 1,
            "repair_passes": 0,
            "findings": findings,
        },
        "freshness": {
            "final_head": None if non_git else target["initial_head"],
            "final_dirty": None if non_git else target["initial_dirty"],
            "plan_final_sha256": None if non_git else target["plan_initial_sha256"],
            "design_final_sha256": None if non_git else target["design_initial_sha256"],
        },
        "metrics": {
            "elapsed_ms": int((dt.datetime.fromisoformat(completed_at.replace("Z", "+00:00")) - dt.datetime.fromisoformat(str(pending["started_at"]).replace("Z", "+00:00"))).total_seconds() * 1000),
            "recorder_elapsed_ms": 10,
            "reviewer_count": 0 if non_git else 1,
            "review_passes": 1,
            "repair_passes": 0,
            "token_usage": None,
        },
    }
