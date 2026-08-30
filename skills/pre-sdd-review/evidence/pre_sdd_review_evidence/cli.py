from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import TextIO

from . import CLI_VERSION, SCHEMA_VERSION
from . import repository, storage
from .schema import CLIENT_IDS, REVIEW_HARD_LIMIT, EvidenceError, canonical_json_bytes


_FINISH_FIELDS = {
    "mode", "execution", "reviewer_count", "fresh_reviewer",
    "read_only_enforced", "conditional_trigger", "degraded_reasons", "verdict",
    "block_reason", "review_passes", "repair_passes", "findings", "token_usage",
}


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
    stream.write(canonical_json_bytes(value).decode("utf-8"))


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
    return parser


def _read_stdin(stream: TextIO) -> object:
    payload = stream.read(REVIEW_HARD_LIMIT + 1)
    if len(payload.encode("utf-8")) > REVIEW_HARD_LIMIT:
        raise EvidenceError("record-too-large", "standard input exceeds the hard size limit")
    try:
        return json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("invalid-json", "standard input is not valid JSON") from exc


def _structured(value: str, name: str) -> object:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise EvidenceError("invalid-json", f"{name} is not valid JSON") from exc


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
        value = _read_stdin(input_stream)
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
    key = repository.load_or_create_identity(paths.home)
    storage.recover_staging(paths)
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
    if target["resolution_status"] == "not-git-repository":
        try:
            repository._git_root(repo_locator)
        except EvidenceError as exc:
            if exc.code != "not-git-repository":
                raise
        else:
            raise EvidenceError("wrong-repository", "repository identity does not match")
        if not hmac.compare_digest(str(pending["start_locator_binding"]), _locator_binding(key, repo_locator)):
            raise EvidenceError("wrong-repository", "repository identity does not match")
        return {"final_head": None, "final_dirty": None, "plan_final_sha256": None, "design_final_sha256": None}
    try:
        root = repository._git_root(repo_locator)
    except EvidenceError as exc:
        raise EvidenceError("wrong-repository", "repository identity does not match") from exc
    if not hmac.compare_digest(str(target["repo_id"]), repository.repository_id(root, key)):
        raise EvidenceError("wrong-repository", "repository identity does not match")
    plan_path = target["plan_path"]
    current = repository.resolve_target(root, Path(str(plan_path)) if plan_path is not None else Path("."), key)
    git = repository.git_snapshot(root)
    return {
        "final_head": git.head,
        "final_dirty": git.dirty,
        "plan_final_sha256": current.plan_initial_sha256 if target["plan_initial_sha256"] is not None else None,
        "design_final_sha256": current.design_initial_sha256 if target["design_initial_sha256"] is not None else None,
    }


def _finish(args: argparse.Namespace, paths: storage.EvidencePaths, input_stream: TextIO) -> dict[str, object]:
    started = time.monotonic_ns()
    key = repository.load_or_create_identity(paths.home)
    storage.recover_staging(paths)
    pending = storage.load_pending(paths, args.run_id)
    semantic = _normalize_finish(args, input_stream)
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
    repository.load_or_create_identity(paths.home)
    storage.recover_staging(paths)
    result = storage.abandon_run(
        paths, args.run_id, args.reason, completed_at=_utc_now(),
        recorder_elapsed_ms=max(0, (time.monotonic_ns() - started) // 1_000_000),
    )
    return {"status": "abandoned", "run_id": args.run_id, "sha256": result.sha256}


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
        else:
            raise EvidenceError("invalid-arguments", "unknown command")
        _json_line(output_stream, result)
        return 0
    except EvidenceError as exc:
        message = exc.message[:300].replace("\n", " ").replace("\r", " ")
        _json_line(error_stream, {"error": {"code": exc.code, "message": message}})
        return 2
    except OSError:
        _json_line(error_stream, {"error": {"code": "evidence-home-unwritable", "message": "evidence storage is unavailable"}})
        return 2
