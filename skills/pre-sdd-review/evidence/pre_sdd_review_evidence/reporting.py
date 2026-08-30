from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

from . import repository, storage
from .schema import EvidenceError, read_bounded_bytes


@dataclasses.dataclass(frozen=True)
class MatchResult:
    status: str
    run_id: str | None
    candidate_run_ids: tuple[str, ...]


def _not_found() -> MatchResult:
    return MatchResult("not-found", None, ())


def resolve_review(
    paths: storage.EvidencePaths, repo_root: Path, plan_path: Path
) -> MatchResult:
    key = repository.load_or_create_identity(paths.home)
    try:
        root = repository._git_root(Path(repo_root))
        plan_file, relative = repository._plan_candidate(root, Path(plan_path))
    except EvidenceError:
        return _not_found()
    if plan_file is None or relative is None:
        return _not_found()
    resolved = plan_file.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return _not_found()
    if not resolved.is_file():
        return _not_found()
    try:
        current_hash = hashlib.sha256(
            read_bounded_bytes(resolved, repository.DOCUMENT_LIMIT)
        ).hexdigest()
    except (EvidenceError, OSError):
        return _not_found()

    repo_id = repository.repository_id(root, key)
    same_target: list[str] = []
    exact: list[str] = []
    for review in storage.scan_runs(paths).reviews:
        target = review["target"]
        freshness = review["freshness"]
        if not isinstance(target, dict) or not isinstance(freshness, dict):
            continue
        if target["repo_id"] != repo_id or target["plan_path"] != relative:
            continue
        run_id = str(review["run_id"])
        same_target.append(run_id)
        if freshness["plan_final_sha256"] == current_hash:
            exact.append(run_id)
    exact = sorted(exact)
    if len(exact) == 1:
        return MatchResult("matched", exact[0], tuple(exact))
    if len(exact) > 1:
        return MatchResult("ambiguous", None, tuple(exact))
    if same_target:
        return MatchResult("stale", None, ())
    return _not_found()
