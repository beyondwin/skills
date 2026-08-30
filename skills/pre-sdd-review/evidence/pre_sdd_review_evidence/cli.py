from __future__ import annotations

import argparse
import copy
import dataclasses
import datetime as dt
import hashlib
import hmac
import os
import re
import stat
import sys
import time
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import TextIO

from . import CLI_VERSION, SCHEMA_VERSION
from . import reporting, repository, storage
from .schema import (
    CLIENT_IDS,
    OUTCOME_HARD_LIMIT,
    REVIEW_HARD_LIMIT,
    EvidenceError,
    canonical_json_bytes,
    derive_assessment,
    parse_json_text,
    read_bounded_bytes,
    validate_review,
)


_FINISH_FIELDS = {
    "mode", "execution", "reviewer_count", "fresh_reviewer",
    "read_only_enforced", "conditional_trigger", "degraded_reasons", "verdict",
    "block_reason", "review_passes", "repair_passes", "findings", "token_usage",
}
_OUTCOME_FIELDS = {
    "recorder", "status", "replan_count", "evaluated_finding_ids",
    "escaped_findings", "disputed_findings", "prevented_rework", "basis",
    "confidence",
}
_PRUNE_INPUT_HARD_LIMIT = 4 * 1024 * 1024


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise EvidenceError("invalid-arguments", "command arguments are invalid")


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _milliseconds(started_at: str, completed_at: str) -> int:
    start = dt.datetime.fromisoformat(started_at[:-1] + "+00:00")
    end = dt.datetime.fromisoformat(completed_at[:-1] + "+00:00")
    return max(0, int((end - start).total_seconds() * 1000))


def _json_line(stream: TextIO, value: object) -> None:
    payload = canonical_json_bytes(value)
    binary = getattr(stream, "buffer", None)
    if binary is not None:
        binary.write(payload)
        binary.flush()
        return
    stream.write(payload.decode("utf-8"))


def _bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise argparse.ArgumentTypeError("expected true or false")


def _parser() -> _Parser:
    parser = _Parser(prog="pre-sdd-review-evidence", add_help=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start")
    start.add_argument("--skill-root", required=True)
    start.add_argument("--plan", required=True)
    start.add_argument("--client", required=True, choices=sorted(CLIENT_IDS))
    start.add_argument("--client-version")
    start.add_argument("--model")
    start.add_argument("--mode", required=True, choices=("default", "review-only"))

    finish = subparsers.add_parser("finish-review")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--repo", required=True)
    finish.add_argument("--from-stdin", action="store_true")
    finish.add_argument("--mode", choices=("default", "review-only"))
    finish.add_argument("--execution", choices=("full", "degraded", "blocked", "unknown"))
    finish.add_argument("--reviewer-count", type=int)
    finish.add_argument("--fresh-reviewer", type=_bool)
    finish.add_argument("--read-only-enforced", type=_bool)
    finish.add_argument("--conditional-trigger")
    finish.add_argument("--degraded-reason", action="append")
    finish.add_argument("--verdict", choices=("READY", "REVISE", "BLOCKED"))
    finish.add_argument("--block-reason")
    finish.add_argument("--review-passes", type=int)
    finish.add_argument("--repair-passes", type=int)
    finish.add_argument("--finding-json", action="append")
    finish.add_argument("--token-usage-json")

    show = subparsers.add_parser("show")
    show.add_argument("--run-id", required=True)
    subparsers.add_parser("pending")
    abandon = subparsers.add_parser("abandon")
    abandon.add_argument("--run-id", required=True)
    abandon.add_argument("--reason", required=True)
    subparsers.add_parser("doctor")
    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--repo", required=True)
    resolve.add_argument("--plan", required=True)
    outcome = subparsers.add_parser("record-outcome")
    outcome.add_argument("--run-id", required=True)
    outcome.add_argument("--repo", required=True)
    outcome.add_argument("--from-stdin", action="store_true")
    outcome.add_argument("--client", choices=sorted(CLIENT_IDS))
    outcome.add_argument("--client-version")
    outcome.add_argument("--model")
    outcome.add_argument(
        "--status",
        choices=(
            "sdd-completed", "implementation-completed",
            "implementation-abandoned", "cancelled",
        ),
    )
    outcome.add_argument("--replan-count", type=int)
    outcome.add_argument("--evaluated-finding", action="append")
    outcome.add_argument("--escaped-finding-json", action="append")
    outcome.add_argument("--disputed-finding-json", action="append")
    outcome.add_argument("--prevented-rework-json", action="append")
    outcome.add_argument(
        "--basis",
        choices=(
            "verified-repository-evidence", "user-reported", "agent-observed",
            "agent-inferred", "unknown",
        ),
    )
    outcome.add_argument("--confidence", choices=("low", "medium", "high"))
    summary = subparsers.add_parser("summary")
    summary.add_argument("--format", choices=("json", "text"), default="json")
    candidates = subparsers.add_parser("candidates")
    candidates.add_argument("action", nargs="?", choices=("export",))
    candidates.add_argument("candidate_id", nargs="?")
    candidates.add_argument("--format", choices=("json", "text"), default="json")
    prune = subparsers.add_parser("prune")
    prune.add_argument("--older-than", required=True)
    prune.add_argument("--include-without-outcome", action="store_true")
    prune.add_argument("--dry-run", action="store_true")
    prune.add_argument("--confirm-selection")
    prune.add_argument("--from-stdin", action="store_true")
    return parser


def _read_stdin(stream: TextIO, limit: int) -> object:
    payload = stream.read(limit + 1)
    return parse_json_text(payload, byte_limit=limit, name="standard input")


def _structured(value: str, name: str) -> object:
    return parse_json_text(value, name=name)


def _normalize_finish(args: argparse.Namespace, input_stream: TextIO) -> dict[str, object]:
    scalar_names = (
        "mode", "execution", "reviewer_count", "fresh_reviewer", "read_only_enforced",
        "conditional_trigger", "degraded_reason", "verdict", "block_reason",
        "review_passes", "repair_passes", "finding_json", "token_usage_json",
    )
    has_scalar = any(getattr(args, name) is not None for name in scalar_names)
    if args.from_stdin:
        if has_scalar:
            raise EvidenceError("invalid-arguments", "stdin and scalar semantic arguments cannot be mixed")
        value = _read_stdin(input_stream, REVIEW_HARD_LIMIT)
        if not isinstance(value, dict) or set(value) != _FINISH_FIELDS:
            raise EvidenceError("schema-invalid", "finish input must contain the exact semantic fields")
        return value.copy()
    required = ("mode", "execution", "reviewer_count", "fresh_reviewer", "read_only_enforced", "verdict", "review_passes", "repair_passes")
    if any(getattr(args, name) is None for name in required):
        raise EvidenceError("invalid-arguments", "all required finish semantic arguments must be supplied")
    value: dict[str, object] = {
        "mode": args.mode,
        "execution": args.execution,
        "reviewer_count": args.reviewer_count,
        "fresh_reviewer": args.fresh_reviewer,
        "read_only_enforced": args.read_only_enforced,
        "conditional_trigger": args.conditional_trigger,
        "degraded_reasons": args.degraded_reason or [],
        "verdict": args.verdict,
        "block_reason": args.block_reason,
        "review_passes": args.review_passes,
        "repair_passes": args.repair_passes,
        "findings": [_structured(item, "finding") for item in (args.finding_json or [])],
        "token_usage": None if args.token_usage_json is None else _structured(args.token_usage_json, "token usage"),
    }
    return value


def _normalize_outcome(
    args: argparse.Namespace, input_stream: TextIO
) -> dict[str, object]:
    scalar_names = (
        "client", "client_version", "model", "status", "replan_count",
        "evaluated_finding", "escaped_finding_json", "disputed_finding_json",
        "prevented_rework_json", "basis", "confidence",
    )
    has_scalar = any(getattr(args, name) is not None for name in scalar_names)
    if args.from_stdin:
        if has_scalar:
            raise EvidenceError(
                "invalid-arguments",
                "stdin and scalar semantic arguments cannot be mixed",
            )
        value = _read_stdin(input_stream, OUTCOME_HARD_LIMIT)
        if not isinstance(value, dict) or set(value) != _OUTCOME_FIELDS:
            raise EvidenceError(
                "schema-invalid",
                "outcome input must contain the exact semantic fields",
            )
        return value.copy()
    if any(
        getattr(args, name) is None
        for name in ("client", "status", "basis", "confidence")
    ):
        raise EvidenceError(
            "invalid-arguments",
            "all required outcome semantic arguments must be supplied",
        )
    return {
        "recorder": {
            "client": args.client,
            "version": args.client_version,
            "model": args.model,
        },
        "status": args.status,
        "replan_count": 0 if args.replan_count is None else args.replan_count,
        "evaluated_finding_ids": args.evaluated_finding or [],
        "escaped_findings": [
            _structured(item, "escaped finding")
            for item in (args.escaped_finding_json or [])
        ],
        "disputed_findings": [
            _structured(item, "disputed finding")
            for item in (args.disputed_finding_json or [])
        ],
        "prevented_rework": [
            _structured(item, "prevented rework")
            for item in (args.prevented_rework_json or [])
        ],
        "basis": args.basis,
        "confidence": args.confidence,
    }


def _locator_binding(key: bytes, locator: Path) -> str:
    canonical = os.fsencode(Path(locator).resolve())
    return hmac.new(key, b"pre-sdd-review:start-locator:v1\0" + canonical, hashlib.sha256).hexdigest()


def _paths(environ: Mapping[str, str]) -> storage.EvidencePaths:
    try:
        user_home = Path.home()
    except RuntimeError as exc:
        raise EvidenceError("invalid-evidence-home", "user home is unavailable") from exc
    return storage.EvidencePaths.from_home(storage.evidence_home(environ, user_home))


def _start(args: argparse.Namespace, paths: storage.EvidencePaths, cwd: Path) -> dict[str, object]:
    key_info = repository._validate_identity_entry(paths.identity_key)
    config_info = repository._validate_identity_entry(paths.config)
    if key_info is None and config_info is None:
        runs_info = storage._lstat(paths.runs)
        if runs_info is not None:
            if stat.S_ISLNK(runs_info.st_mode) or not stat.S_ISDIR(runs_info.st_mode):
                raise EvidenceError("identity-state-invalid", "runs root is unsafe")
            if any(paths.runs.iterdir()):
                raise EvidenceError("identity-key-missing", "identity key is unavailable")
        key = repository.load_or_create_identity(paths.home)
    else:
        key = reporting.load_existing_identity(paths)
    skill = repository.load_skill_snapshot(Path(args.skill_root))
    target = repository.resolve_target(cwd, Path(args.plan), key)
    run_id = str(uuid.uuid4())
    started_at = _utc_now()
    pending = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "pending",
        "run_id": run_id,
        "started_at": started_at,
        "skill": dataclasses.asdict(skill),
        "client": {"id": args.client, "version": args.client_version, "model": args.model},
        "target": dataclasses.asdict(target),
        "intended_mode": args.mode,
        "start_locator_binding": _locator_binding(key, cwd),
    }
    storage.create_pending(paths, pending)
    return {
        "status": "started",
        "run_id": run_id,
        "resolution_status": target.resolution_status,
        "plan_path": target.plan_path,
        "design_path": target.design_path,
    }


def _verified_freshness(
    pending: dict[str, object], repo_locator: Path, key: bytes
) -> dict[str, object]:
    target = pending["target"]
    assert isinstance(target, dict)
    _verify_repository(target, repo_locator, key, pending=pending)
    if target["resolution_status"] == "not-git-repository":
        return {"final_head": None, "final_dirty": None, "plan_final_sha256": None, "design_final_sha256": None}
    root = repository._git_root(repo_locator)
    git = repository.git_snapshot(root)

    def persisted_hash(path_value: object, initial_hash: object) -> str | None:
        if initial_hash is None:
            return None
        if not isinstance(path_value, str):
            raise EvidenceError("schema-invalid", "recorded document path is unavailable")
        candidate = (root / Path(path_value)).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise EvidenceError("outside-repository", "recorded document escaped the repository") from exc
        if not candidate.is_file():
            raise EvidenceError("target-unavailable", "recorded document is unavailable")
        return hashlib.sha256(
            read_bounded_bytes(candidate, repository.DOCUMENT_LIMIT)
        ).hexdigest()

    return {
        "final_head": git.head,
        "final_dirty": git.dirty,
        "plan_final_sha256": persisted_hash(
            target["plan_path"], target["plan_initial_sha256"]
        ),
        "design_final_sha256": persisted_hash(
            target["design_path"], target["design_initial_sha256"]
        ),
    }


def _verify_repository(
    target: dict[str, object],
    repo_locator: Path,
    key: bytes,
    *,
    pending: dict[str, object] | None,
) -> None:
    if target["resolution_status"] == "not-git-repository":
        try:
            repository._git_root(repo_locator)
        except EvidenceError as exc:
            if exc.code != "not-git-repository":
                raise
        else:
            raise EvidenceError("wrong-repository", "repository identity does not match")
        if pending is None:
            raise EvidenceError(
                "wrong-repository", "repository identity cannot be authenticated"
            )
        if not hmac.compare_digest(
            str(pending["start_locator_binding"]), _locator_binding(key, repo_locator)
        ):
            raise EvidenceError("wrong-repository", "repository identity does not match")
        return
    try:
        root = repository._git_root(repo_locator)
    except EvidenceError as exc:
        raise EvidenceError("wrong-repository", "repository identity does not match") from exc
    if not hmac.compare_digest(str(target["repo_id"]), repository.repository_id(root, key)):
        raise EvidenceError("wrong-repository", "repository identity does not match")


def _review_semantics(review: dict[str, object]) -> dict[str, object]:
    protocol = review["protocol"]
    result = review["result"]
    metrics = review["metrics"]
    assert isinstance(protocol, dict) and isinstance(result, dict) and isinstance(metrics, dict)
    return {
        "mode": protocol["mode"],
        "execution": protocol["execution"],
        "reviewer_count": protocol["reviewer_count"],
        "fresh_reviewer": protocol["fresh_reviewer"],
        "read_only_enforced": protocol["read_only_enforced"],
        "conditional_trigger": protocol["conditional_trigger"],
        "degraded_reasons": protocol["degraded_reasons"],
        "verdict": result["verdict"],
        "block_reason": result["block_reason"],
        "review_passes": result["review_passes"],
        "repair_passes": result["repair_passes"],
        "findings": result["findings"],
        "token_usage": metrics["token_usage"],
    }


def _candidate_retry_review(
    existing: dict[str, object], semantic: dict[str, object]
) -> dict[str, object]:
    candidate = copy.deepcopy(existing)
    protocol = candidate["protocol"]
    result = candidate["result"]
    metrics = candidate["metrics"]
    assert isinstance(protocol, dict) and isinstance(result, dict) and isinstance(metrics, dict)
    for key in (
        "mode", "execution", "reviewer_count", "fresh_reviewer",
        "read_only_enforced", "conditional_trigger", "degraded_reasons",
    ):
        protocol[key] = semantic[key]
    for key in ("verdict", "block_reason", "review_passes", "repair_passes", "findings"):
        result[key] = semantic[key]
    for key in ("reviewer_count", "review_passes", "repair_passes", "token_usage"):
        metrics[key] = semantic[key]
    return validate_review(candidate)


def _finish(args: argparse.Namespace, paths: storage.EvidencePaths, input_stream: TextIO) -> dict[str, object]:
    started = time.monotonic_ns()
    key = reporting.load_existing_identity(paths)
    storage.recover_staging(paths)
    semantic = _normalize_finish(args, input_stream)
    try:
        existing = storage.load_review(paths, args.run_id)
    except EvidenceError as exc:
        if exc.code != "run-not-found":
            raise
        existing = None
    if existing is not None:
        try:
            pending_for_retry = storage.load_pending(paths, args.run_id)
        except EvidenceError as exc:
            if exc.code != "run-not-found":
                raise
            pending_for_retry = None
        target = existing["target"]
        assert isinstance(target, dict)
        _verify_repository(
            target, Path(args.repo), key, pending=pending_for_retry
        )
        candidate = _candidate_retry_review(existing, semantic)
        if _review_semantics(candidate) != _review_semantics(existing):
            raise EvidenceError("already-finalized", "conflicting retry")
        result = storage.finish_review(paths, args.run_id, existing)
        return {"status": "recorded", "run_id": args.run_id, "sha256": result.sha256}
    pending = storage.load_pending(paths, args.run_id)
    if semantic["mode"] != pending["intended_mode"]:
        raise EvidenceError("schema-invalid", "finish mode does not match pending mode")
    freshness = _verified_freshness(pending, Path(args.repo), key)
    target = pending["target"]
    assert isinstance(target, dict)
    if target["resolution_status"] == "not-git-repository":
        expected = {
            "execution": "blocked", "reviewer_count": 0, "fresh_reviewer": False,
            "read_only_enforced": False, "verdict": "BLOCKED",
        }
        if any(semantic[key_name] != value for key_name, value in expected.items()):
            raise EvidenceError("schema-invalid", "non-Git finalization requires a blocked review")
    completed_at = _utc_now()
    review = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "review",
        "run_id": args.run_id,
        "started_at": pending["started_at"],
        "completed_at": completed_at,
        "skill": pending["skill"],
        "client": pending["client"],
        "protocol": {
            "mode": semantic["mode"], "execution": semantic["execution"],
            "reviewer_count": semantic["reviewer_count"],
            "fresh_reviewer": semantic["fresh_reviewer"],
            "read_only_enforced": semantic["read_only_enforced"],
            "conditional_trigger": semantic["conditional_trigger"],
            "degraded_reasons": semantic["degraded_reasons"],
        },
        "target": target,
        "result": {
            "completion": "completed", "verdict": semantic["verdict"],
            "block_reason": semantic["block_reason"], "completion_reason": None,
            "review_passes": semantic["review_passes"], "repair_passes": semantic["repair_passes"],
            "findings": semantic["findings"],
        },
        "freshness": freshness,
        "metrics": {
            "elapsed_ms": _milliseconds(str(pending["started_at"]), completed_at),
            "recorder_elapsed_ms": max(0, (time.monotonic_ns() - started) // 1_000_000),
            "reviewer_count": semantic["reviewer_count"],
            "review_passes": semantic["review_passes"],
            "repair_passes": semantic["repair_passes"],
            "token_usage": semantic["token_usage"],
        },
    }
    result = storage.finish_review(paths, args.run_id, review)
    return {"status": "recorded", "run_id": args.run_id, "sha256": result.sha256}


def _abandon(args: argparse.Namespace, paths: storage.EvidencePaths) -> dict[str, object]:
    started = time.monotonic_ns()
    reporting.load_existing_identity(paths)
    storage.recover_staging(paths)
    result = storage.abandon_run(
        paths, args.run_id, args.reason, completed_at=_utc_now(),
        recorder_elapsed_ms=max(0, (time.monotonic_ns() - started) // 1_000_000),
    )
    return {"status": "abandoned", "run_id": args.run_id, "sha256": result.sha256}


def _resolve(args: argparse.Namespace, paths: storage.EvidencePaths) -> dict[str, object]:
    return dataclasses.asdict(
        reporting.resolve_review(paths, Path(args.repo), Path(args.plan))
    )


def _require_current_plan(
    review: dict[str, object], repo_locator: Path
) -> None:
    target = review["target"]
    freshness = review["freshness"]
    assert isinstance(target, dict) and isinstance(freshness, dict)
    plan_path = target["plan_path"]
    recorded_hash = freshness["plan_final_sha256"]
    if not isinstance(plan_path, str) or not isinstance(recorded_hash, str):
        raise EvidenceError("stale-plan", "recorded plan is unavailable")
    root = repository._git_root(repo_locator)
    candidate = (root / Path(plan_path)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise EvidenceError("stale-plan", "recorded plan is unavailable") from exc
    if not candidate.is_file():
        raise EvidenceError("stale-plan", "recorded plan is unavailable")
    current_hash = hashlib.sha256(
        read_bounded_bytes(candidate, repository.DOCUMENT_LIMIT)
    ).hexdigest()
    if not hmac.compare_digest(recorded_hash, current_hash):
        raise EvidenceError("stale-plan", "current plan does not match the review")


def _record_outcome(
    args: argparse.Namespace,
    paths: storage.EvidencePaths,
    input_stream: TextIO,
) -> dict[str, object]:
    key = reporting.load_existing_identity(paths)
    storage.recover_staging(paths)
    semantic = _normalize_outcome(args, input_stream)
    review = storage.load_review(paths, args.run_id)
    target = review["target"]
    assert isinstance(target, dict)
    _verify_repository(target, Path(args.repo), key, pending=None)
    _require_current_plan(review, Path(args.repo))
    downstream = {
        "status": semantic["status"],
        "plan_hash_matched": True,
        "replan_count": semantic["replan_count"],
        "evaluated_finding_ids": semantic["evaluated_finding_ids"],
        "escaped_findings": semantic["escaped_findings"],
        "disputed_findings": semantic["disputed_findings"],
        "prevented_rework": semantic["prevented_rework"],
    }
    outcome = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "outcome",
        "run_id": args.run_id,
        "recorded_at": _utc_now(),
        "recorder": semantic["recorder"],
        "downstream": downstream,
        "assessment": {
            "label": derive_assessment(review, downstream),
            "basis": semantic["basis"],
            "confidence": semantic["confidence"],
        },
    }
    result = storage.record_outcome(paths, args.run_id, outcome)
    return {"status": "recorded", "run_id": args.run_id, "sha256": result.sha256}


def _pending(paths: storage.EvidencePaths) -> dict[str, object]:
    scan = storage.scan_runs(paths)
    runs = [
        {
            "run_id": item.run_id,
            "started_at": item.started_at,
            "resolution_status": item.resolution_status,
            "plan_path": item.plan_path,
            "design_path": item.design_path,
            "age_class": item.age_class,
        }
        for item in scan.pending
    ]
    return {"status": "ok", "runs": runs}


def _doctor(paths: storage.EvidencePaths) -> dict[str, object]:
    issues: list[dict[str, str]] = list(storage.doctor(paths))
    try:
        key_info = repository._validate_identity_entry(paths.identity_key)
        config_info = repository._validate_identity_entry(paths.config)
        if key_info is None:
            raise EvidenceError(
                "identity-key-missing",
                "identity key is unavailable" if config_info is None else "identity config exists without a key",
            )
        key = repository._load_key(paths.identity_key)
        if config_info is None:
            raise EvidenceError("identity-state-invalid", "identity config is unavailable")
        repository._load_and_validate_config(
            paths.config, repository._expected_config(key, key_info)
        )
    except (EvidenceError, OSError) as exc:
        code = exc.code if isinstance(exc, EvidenceError) else "identity-state-invalid"
        issues.append({"code": code, "run_id": "identity"})
    return {"status": "ok", "issues": issues}


def _summary(args: argparse.Namespace, paths: storage.EvidencePaths) -> object:
    records = reporting.load_records(paths)
    pending = storage.scan_runs(paths).pending
    value = reporting.summarize(records, pending)
    if args.format == "text":
        coverage = value["outcome_coverage"]
        false_ready = value["verified_false_ready"]
        assert isinstance(coverage, dict) and isinstance(false_ready, dict)
        return (
            f"Completed reviews: {value['completed_reviews']}\n"
            f"Outcome coverage: {coverage['numerator']}/{coverage['denominator']} ({coverage['interpretation']})\n"
            f"Verified false READY: {false_ready['numerator']}/{false_ready['denominator']} ({false_ready['interpretation']})\n"
            "Boundary: observer-supplied self-improvement evidence; not audit-grade proof\n"
        )
    return value


def _candidates(args: argparse.Namespace, paths: storage.EvidencePaths) -> object:
    candidates = reporting.select_candidates(reporting.load_records(paths))
    if args.action is None:
        if args.candidate_id is not None:
            raise EvidenceError("invalid-arguments", "candidate ID requires export")
        payloads = [item.payload() for item in candidates]
        if args.format == "text":
            if not payloads:
                return "No heuristic candidates.\n"
            return "".join(
                f"{item['candidate_id']} {item['kind']} runs={item['source_run_count']}\n"
                for item in payloads
            )
        return payloads
    if args.candidate_id is None or args.format != "json":
        raise EvidenceError("invalid-arguments", "candidate export requires one ID and JSON output")
    candidate = next(
        (item for item in candidates if item.candidate_id == args.candidate_id), None
    )
    if candidate is None:
        raise EvidenceError("run-not-found", "candidate was not found")
    reporting.load_existing_identity(paths)
    storage.recover_staging(paths)
    storage._ensure_private_directory(paths.exports)
    reporting.export_candidate(candidate, paths.exports)
    return {
        "status": "exported",
        "candidate_id": candidate.candidate_id,
        "files": ["candidate.json", *candidate.required_synthetic_files],
    }


def _prune_cutoff(older_than: str) -> str:
    match = re.fullmatch(r"([1-9][0-9]*)d", older_than)
    if match is None:
        raise EvidenceError("invalid-arguments", "older-than must be a positive day duration")
    try:
        days = int(match.group(1))
        now = dt.datetime.fromisoformat(_utc_now()[:-1] + "+00:00")
        cutoff = now - dt.timedelta(days=days)
    except (ValueError, OverflowError) as exc:
        raise EvidenceError(
            "invalid-arguments", "older-than must be a positive day duration"
        ) from exc
    return cutoff.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _prune(
    args: argparse.Namespace,
    paths: storage.EvidencePaths,
    input_stream: TextIO,
) -> dict[str, object]:
    if args.dry_run:
        if args.from_stdin or args.confirm_selection is not None:
            raise EvidenceError("invalid-arguments", "dry-run cannot confirm a selection")
        selection = reporting.preview_prune(
            reporting.load_records(paths),
            _prune_cutoff(args.older_than),
            args.include_without_outcome,
        )
        return {
            "status": "preview",
            "selection": selection.payload(),
            "selection_digest": selection.digest,
        }
    if not args.from_stdin or args.confirm_selection is None:
        raise EvidenceError("invalid-arguments", "prune mutation requires a confirmed stdin selection")
    supplied = _read_stdin(input_stream, _PRUNE_INPUT_HARD_LIMIT)
    deleted = reporting.confirm_prune(paths, supplied, args.confirm_selection)
    return {"status": "pruned", "run_ids": list(deleted), "count": len(deleted)}


def main(
    argv: list[str] | None = None,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    error_stream: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    input_stream = sys.stdin if input_stream is None else input_stream
    output_stream = sys.stdout if output_stream is None else output_stream
    error_stream = sys.stderr if error_stream is None else error_stream
    environ = os.environ if environ is None else environ
    cwd = Path.cwd() if cwd is None else Path(cwd)
    try:
        if arguments == ["--version"]:
            _json_line(output_stream, {"cli_version": CLI_VERSION, "schema_version": SCHEMA_VERSION, "skill_name": "pre-sdd-review"})
            return 0
        if "--version" in arguments:
            raise EvidenceError("invalid-arguments", "--version accepts no other arguments")
        args = _parser().parse_args(arguments)
        paths = _paths(environ)
        if args.command == "start":
            result = _start(args, paths, cwd)
        elif args.command == "finish-review":
            result = _finish(args, paths, input_stream)
        elif args.command == "show":
            result = storage.load_review(paths, args.run_id)
        elif args.command == "pending":
            result = _pending(paths)
        elif args.command == "abandon":
            result = _abandon(args, paths)
        elif args.command == "doctor":
            result = _doctor(paths)
        elif args.command == "resolve":
            result = _resolve(args, paths)
        elif args.command == "record-outcome":
            result = _record_outcome(args, paths, input_stream)
        elif args.command == "summary":
            result = _summary(args, paths)
        elif args.command == "candidates":
            result = _candidates(args, paths)
        elif args.command == "prune":
            result = _prune(args, paths, input_stream)
        else:
            raise EvidenceError("invalid-arguments", "unknown command")
        if isinstance(result, str):
            output_stream.write(result)
        else:
            _json_line(output_stream, result)
        return 0
    except EvidenceError as exc:
        message = exc.message[:300].replace("\n", " ").replace("\r", " ")
        _json_line(error_stream, {"error": {"code": exc.code, "message": message}})
        return 2
    except OSError:
        _json_line(error_stream, {"error": {"code": "evidence-home-unwritable", "message": "evidence storage is unavailable"}})
        return 2
