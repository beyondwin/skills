"""Local evidence recorder for pre-sdd-review (schema 2). Standard library only."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import TextIO

CLI_VERSION, SCHEMA, SKILL_NAME = "2.0.0", 2, "pre-sdd-review"
RECORD_LIMIT, DOCUMENT_LIMIT, SKILL_DOCUMENT_LIMIT = 64 * 1024, 8 * 1024 * 1024, 256 * 1024

CLIENTS = ("codex", "claude-code", "cursor", "grok", "other", "unknown")
MODES = ("default", "review-only")
EXECUTIONS = ("full", "degraded", "blocked")
TRIGGERS = ("runtime-removal", "schema-migration", "auth-boundary", "data-boundary", "external-side-effect")
VERDICTS = ("READY", "REVISE", "BLOCKED")
ABANDON_REASONS = ("user-cancelled", "input-changed", "scope-changed", "input-format-fixed", "other")
OUTCOME_LABELS = ("good", "false-ready", "noisy", "abandoned")
SEVERITIES = ("BLOCKER", "IMPORTANT")
CLASSES = ("authority-drift", "repo-reality", "coverage", "ordering", "verification-gap")
FINDING_STATUSES = ("repaired", "unresolved", "blocked-by-authority", "accepted-as-is")
FINISH_KEYS = frozenset({"execution", "reviewers", "trigger", "degraded_reasons", "verdict", "block_reason", "review_passes", "repair_passes", "findings"})
FINDING_KEYS = frozenset({"id", "severity", "class", "pattern", "status", "repair_pass", "location", "evidence", "consequence", "fix"})

_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}\Z")
_FINDING_ID = re.compile(r"PSDR-[0-9]{3,}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_VERSION_LINE = re.compile(r'^\s*version:\s*["\']?([^\s"\']+)["\']?\s*$', re.MULTILINE)
_DRIVE = re.compile(r"^[A-Za-z]:")


class EvidenceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def fail(code: str, message: str) -> None:
    raise EvidenceError(code, message)


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def read_bounded_bytes(path: Path, limit: int) -> bytes:
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        fail("schema-invalid", f"{Path(path).name} exceeds {limit} bytes")
    return data


def read_stdin(stream: TextIO, limit: int) -> object:
    text = stream.read(limit + 1)
    if len(text.encode("utf-8")) > limit:
        fail("schema-invalid", f"stdin exceeds {limit} bytes")
    return parse_json(text.encode("utf-8"), "stdin")


def parse_json(data: bytes, name: str) -> object:
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        fail("schema-invalid", f"{name} is not valid UTF-8 JSON")
    return None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def elapsed_seconds(start: str, end: str) -> int:
    begin = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
    finish = dt.datetime.fromisoformat(end.replace("Z", "+00:00"))
    return max(0, int((finish - begin).total_seconds()))


def evidence_home(environ: Mapping[str, str]) -> Path:
    override = environ.get("PRE_SDD_REVIEW_HOME")
    if override is None:
        return Path.home() / ".pre-sdd-review"
    candidate = Path(override.strip()).expanduser()
    if not override.strip() or not candidate.is_absolute():
        fail("invalid-arguments", "PRE_SDD_REVIEW_HOME must be a non-empty absolute path")
    return candidate


def validate_run_id(value: str) -> str:
    try:
        parsed = uuid.UUID(str(value))
    except ValueError:
        fail("invalid-arguments", "run_id must be a canonical lowercase UUID")
    if str(parsed) != value:
        fail("invalid-arguments", "run_id must be a canonical lowercase UUID")
    return value


def run_path(home: Path, run_id: str) -> Path:
    return home / "runs" / f"{validate_run_id(run_id)}.json"


def write_record(path: Path, record: dict[str, object]) -> None:
    payload = canonical(record)
    if len(payload) > RECORD_LIMIT:
        fail("schema-invalid", f"record exceeds {RECORD_LIMIT} bytes")
    temp = path.with_name(path.name + ".tmp")
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    except OSError as exc:
        raise EvidenceError("evidence-home-unwritable", "evidence storage is unavailable") from exc


def load_record(home: Path, run_id: str) -> dict[str, object]:
    path = run_path(home, run_id)
    if not path.is_file():
        fail("run-not-found", "run was not found")
    record = parse_json(read_bounded_bytes(path, RECORD_LIMIT), "record")
    if not isinstance(record, dict) or record.get("schema") != SCHEMA:
        fail("schema-invalid", "record is not a schema 2 record")
    return record


def iter_records(home: Path) -> list[dict[str, object]]:
    runs = home / "runs"
    if not runs.is_dir():
        return []
    records: list[dict[str, object]] = []
    for path in runs.glob("*.json"):
        if not path.is_file():
            continue
        try:
            record = parse_json(read_bounded_bytes(path, RECORD_LIMIT), path.name)
        except EvidenceError:
            continue
        if isinstance(record, dict) and record.get("schema") == SCHEMA and isinstance(record.get("started_at"), str):
            records.append(record)
    return sorted(records, key=lambda item: (str(item["started_at"]), str(item["run_id"])))


def git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(root), *args], check=False, capture_output=True, text=True)


def locator(cwd: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else cwd / candidate


def git_root(path: Path) -> Path:
    directory = path if path.is_dir() else path.parent
    if not directory.is_dir():
        fail("not-git-repository", "repository locator does not exist")
    result = git(directory, "rev-parse", "--show-toplevel")
    output = result.stdout.strip()
    if result.returncode != 0 or not output or "\n" in output:
        fail("not-git-repository", "repository locator is not inside a Git repository")
    return Path(output).resolve()


def git_state(root: Path) -> tuple[str, bool]:
    head = git(root, "rev-parse", "--verify", "HEAD")
    head_value = head.stdout.strip().lower() if head.returncode == 0 else "unborn"
    status = git(root, "status", "--porcelain")
    if status.returncode != 0:
        fail("not-git-repository", "git status is unavailable")
    return head_value, bool(status.stdout.strip())


def safe_relative(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or value.startswith("/") or _DRIVE.match(value):
        return False
    return all(part not in ("", ".", "..") for part in value.split("/"))


def repository_relative(root: Path, argument: str, cwd: Path) -> str:
    resolved = locator(cwd, argument).resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError:
        fail("outside-repository", f"{Path(argument).name} is outside the repository")
    if not resolved.is_file() or not safe_relative(relative):
        fail("outside-repository", f"{Path(argument).name} is not a file inside the repository")
    return relative


def document_hash(root: Path, relative: str) -> str:
    path = root / relative
    if not path.is_file():
        fail("outside-repository", f"{relative} is missing")
    return sha256(read_bounded_bytes(path, DOCUMENT_LIMIT))


def skill_snapshot(skill_root: Path) -> dict[str, str]:
    skill_md = skill_root / "SKILL.md"
    protocol = skill_root / "references" / "reviewer-protocol.md"
    if not skill_md.is_file() or not protocol.is_file():
        fail("invalid-arguments", "skill root must contain SKILL.md and references/reviewer-protocol.md")
    skill_bytes = read_bounded_bytes(skill_md, SKILL_DOCUMENT_LIMIT)
    protocol_bytes = read_bounded_bytes(protocol, SKILL_DOCUMENT_LIMIT)
    text = skill_bytes.decode("utf-8", errors="replace")
    if not text.startswith("---\n") or "\n---" not in text[4:]:
        fail("invalid-arguments", "SKILL.md frontmatter is unavailable")
    frontmatter = text[4 : text.index("\n---", 4)]
    match = _VERSION_LINE.search(frontmatter)
    if match is None:
        fail("invalid-arguments", "SKILL.md frontmatter does not declare metadata.version")
    return {"version": match.group(1), "sha256": sha256(skill_bytes + protocol_bytes)}


def _string(value: object, name: str, maximum: int, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or _CONTROL.search(value):
        fail("schema-invalid", f"{name} must be a non-empty single-line string of at most {maximum} characters")
    return value


def _enum(value: object, name: str, allowed: tuple[str, ...], *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if value not in allowed:
        fail("schema-invalid", f"{name} must be one of {', '.join(allowed)}")
    return str(value)


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum or value > maximum:
        fail("schema-invalid", f"{name} must be an integer between {minimum} and {maximum}")
    return int(value)


def _relative(value: object, name: str) -> str:
    if not safe_relative(value) or len(str(value)) > 500:
        fail("schema-invalid", f"{name} must be a safe repository-relative path")
    return str(value)


def validate_finding(item: object, repair_passes: int) -> dict[str, object]:
    if not isinstance(item, dict) or set(item) != FINDING_KEYS:
        fail("schema-invalid", "finding must contain exactly the finding keys")
    identifier = _string(item["id"], "finding.id", 20)
    if identifier is None or not _FINDING_ID.fullmatch(identifier):
        fail("schema-invalid", "finding.id must look like PSDR-001")
    _enum(item["severity"], "finding.severity", SEVERITIES)
    _enum(item["class"], "finding.class", CLASSES)
    pattern = _string(item["pattern"], "finding.pattern", 80)
    if pattern is None or not _PATTERN.fullmatch(pattern):
        fail("schema-invalid", "finding.pattern must be lowercase kebab, dot, or underscore tokens")
    _enum(item["status"], "finding.status", FINDING_STATUSES)
    repair_pass = item["repair_pass"]
    if repair_pass is not None:
        _integer(repair_pass, "finding.repair_pass", 1, 2)
        if repair_pass > repair_passes:
            fail("schema-invalid", "finding.repair_pass exceeds repair_passes")
    location = item["location"]
    if not isinstance(location, dict) or set(location) != {"path", "locator"}:
        fail("schema-invalid", "finding.location must contain path and locator")
    _relative(location["path"], "finding.location.path")
    _string(location["locator"], "finding.location.locator", 200)
    if not isinstance(item["evidence"], list):
        fail("schema-invalid", "finding.evidence must be a list")
    references: list[str] = []
    for reference in item["evidence"]:
        value = _relative(reference, "finding.evidence[]")
        if value not in references:
            references.append(value)
    _string(item["consequence"], "finding.consequence", 300)
    _string(item["fix"], "finding.fix", 300)
    normalized = dict(item)
    normalized["evidence"] = references
    return normalized


def validate_finish(payload: object, mode: str) -> dict[str, object]:
    if not isinstance(payload, dict) or set(payload) != FINISH_KEYS:
        fail("schema-invalid", "finish input must contain exactly the finish keys")
    execution = _enum(payload["execution"], "execution", EXECUTIONS)
    reviewers = _integer(payload["reviewers"], "reviewers", 0, 2)
    trigger = _enum(payload["trigger"], "trigger", TRIGGERS, nullable=True)
    if not isinstance(payload["degraded_reasons"], list):
        fail("schema-invalid", "degraded_reasons must be a list")
    reasons = [str(_string(item, "degraded_reasons[]", 100)) for item in payload["degraded_reasons"]]
    verdict = _enum(payload["verdict"], "verdict", VERDICTS)
    block_reason = _string(payload["block_reason"], "block_reason", 100, nullable=True)
    review_passes = _integer(payload["review_passes"], "review_passes", 1, 3)
    repair_passes = _integer(payload["repair_passes"], "repair_passes", 0, 2)
    if not isinstance(payload["findings"], list):
        fail("schema-invalid", "findings must be a list")
    findings = [validate_finding(item, repair_passes) for item in payload["findings"]]
    identifiers = [str(item["id"]) for item in findings]
    if len(set(identifiers)) != len(identifiers):
        fail("schema-invalid", "finding ids must be unique")
    statuses = [str(item["status"]) for item in findings]
    if verdict == "READY" and any(status != "repaired" for status in statuses):
        fail("schema-invalid", "READY permits only repaired findings")
    if verdict == "REVISE" and "unresolved" not in statuses:
        fail("schema-invalid", "REVISE requires an unresolved finding")
    if verdict == "BLOCKED" and block_reason is None:
        fail("schema-invalid", "BLOCKED requires block_reason")
    if repair_passes > 0 and "repaired" not in statuses:
        fail("schema-invalid", "repair_passes requires at least one repaired finding")
    if mode == "review-only" and repair_passes != 0:
        fail("schema-invalid", "review-only permits no repair pass")
    if execution == "full" and (reasons or reviewers != (2 if trigger is not None else 1)):
        fail("schema-invalid", "full execution requires one reviewer, or two with a trigger, and no degraded reasons")
    if execution == "degraded" and not reasons:
        fail("schema-invalid", "degraded execution requires degraded_reasons")
    return {
        "execution": execution, "reviewers": reviewers, "trigger": trigger,
        "degraded_reasons": reasons, "verdict": verdict, "block_reason": block_reason,
        "review_passes": review_passes, "repair_passes": repair_passes, "findings": findings,
    }


def cmd_start(args: argparse.Namespace, home: Path, cwd: Path) -> dict[str, object]:
    root = git_root(locator(cwd, args.repo))
    plan = repository_relative(root, args.plan, cwd)
    design = None if args.design is None else repository_relative(root, args.design, cwd)
    head, dirty = git_state(root)
    skill = skill_snapshot(locator(cwd, args.skill_root))
    model = _string(args.model, "model", 100)
    run_id = str(uuid.uuid4())
    record: dict[str, object] = {
        "schema": SCHEMA, "run_id": run_id, "status": "pending", "started_at": utc_now(),
        "completed_at": None, "elapsed_s": None, "skill": skill,
        "client": {"id": args.client, "model": model}, "repo": root.name, "mode": args.mode,
        "plan": {"path": plan, "sha_start": document_hash(root, plan), "sha_end": None},
        "design": None if design is None else {"path": design, "sha_start": document_hash(root, design), "sha_end": None},
        "git": {"head_start": head, "head_end": None, "dirty_start": dirty, "dirty_end": None},
        "execution": None, "reviewers": None, "trigger": None, "degraded_reasons": [],
        "review_passes": None, "repair_passes": None, "verdict": None, "block_reason": None,
        "abandon_reason": None, "findings": [], "outcome": None,
    }
    write_record(run_path(home, run_id), record)
    return {"run_id": run_id, "status": "pending"}


def _require_pending(home: Path, run_id: str) -> dict[str, object]:
    record = load_record(home, run_id)
    if record["status"] != "pending":
        fail("already-finished", "run is already finished")
    return record


def cmd_finish(args: argparse.Namespace, home: Path, cwd: Path, stdin: TextIO) -> dict[str, object]:
    record = _require_pending(home, args.run_id)
    root = git_root(locator(cwd, args.repo))
    if root.name != record["repo"]:
        fail("outside-repository", "repository does not match the recorded run")
    semantic = validate_finish(read_stdin(stdin, RECORD_LIMIT), str(record["mode"]))
    head, dirty = git_state(root)
    plan = record["plan"]
    design = record["design"]
    assert isinstance(plan, dict)
    plan["sha_end"] = document_hash(root, str(plan["path"]))
    if isinstance(design, dict):
        design["sha_end"] = document_hash(root, str(design["path"]))
    git_facts = record["git"]
    assert isinstance(git_facts, dict)
    git_facts["head_end"] = head
    git_facts["dirty_end"] = dirty
    completed_at = utc_now()
    record.update(semantic)
    record["status"] = "completed"
    record["completed_at"] = completed_at
    record["elapsed_s"] = elapsed_seconds(str(record["started_at"]), completed_at)
    write_record(run_path(home, args.run_id), record)
    return {"run_id": args.run_id, "status": "completed", "verdict": record["verdict"]}


def cmd_abandon(args: argparse.Namespace, home: Path) -> dict[str, object]:
    record = _require_pending(home, args.run_id)
    completed_at = utc_now()
    record.update({
        "status": "abandoned", "abandon_reason": args.reason, "completed_at": completed_at,
        "elapsed_s": elapsed_seconds(str(record["started_at"]), completed_at),
    })
    write_record(run_path(home, args.run_id), record)
    return {"run_id": args.run_id, "status": "abandoned"}


def cmd_outcome(args: argparse.Namespace, home: Path) -> dict[str, object]:
    record = load_record(home, args.run_id)
    if record["status"] != "completed":
        fail("schema-invalid", "outcome requires a completed run")
    if args.label == "false-ready" and record["verdict"] != "READY":
        fail("schema-invalid", "false-ready requires a READY verdict")
    note = _string(args.note, "note", 300, nullable=True)
    record["outcome"] = {"label": args.label, "note": note, "recorded_at": utc_now()}
    write_record(run_path(home, args.run_id), record)
    return {"run_id": args.run_id, "outcome": args.label}


def cmd_show(args: argparse.Namespace, home: Path) -> str:
    load_record(home, args.run_id)
    return read_bounded_bytes(run_path(home, args.run_id), RECORD_LIMIT).decode("utf-8")


def _count(values: list[str], keys: tuple[str, ...] | None = None) -> dict[str, int]:
    counts: dict[str, int] = {key: 0 for key in keys} if keys else {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    completed = [record for record in records if record["status"] == "completed"]
    runs_index: list[dict[str, object]] = []
    chains: dict[tuple[str, str], list[dict[str, object]]] = {}
    pattern_runs: dict[tuple[str, str], list[str]] = {}
    severities: list[str] = []
    statuses: list[str] = []
    classes: list[str] = []
    anomalies: dict[str, list[object]] = {
        "repair_without_repaired_finding": [], "head_changed_during_review": [],
        "design_unresolved_but_full_execution": [], "repo_reality_citing_documents_only": [],
    }
    for record in records:
        run_id = str(record["run_id"])
        plan = record["plan"]
        design = record["design"]
        assert isinstance(plan, dict)
        findings = record["findings"]
        assert isinstance(findings, list)
        runs_index.append({
            "run_id": run_id, "started_at": record["started_at"], "repo": record["repo"],
            "plan": plan["path"], "status": record["status"], "verdict": record["verdict"],
            "findings": len(findings), "elapsed_s": record["elapsed_s"],
        })
        chains.setdefault((str(record["repo"]), str(plan["path"])), []).append(
            {"run_id": run_id, "status": record["status"], "verdict": record["verdict"]}
        )
        if record["status"] != "completed":
            continue
        documents = {str(plan["path"])}
        if isinstance(design, dict):
            documents.add(str(design["path"]))
        for item in findings:
            assert isinstance(item, dict)
            severities.append(str(item["severity"]))
            statuses.append(str(item["status"]))
            classes.append(str(item["class"]))
            key = (str(item["class"]), str(item["pattern"]))
            runs_for_pattern = pattern_runs.setdefault(key, [])
            if run_id not in runs_for_pattern:
                runs_for_pattern.append(run_id)
            if item["class"] == "repo-reality" and set(item["evidence"]) <= documents:
                anomalies["repo_reality_citing_documents_only"].append({"run_id": run_id, "finding_id": item["id"]})
        if record["repair_passes"] and not any(item["status"] == "repaired" for item in findings):
            anomalies["repair_without_repaired_finding"].append(run_id)
        git_facts = record["git"]
        assert isinstance(git_facts, dict)
        if git_facts["head_start"] != git_facts["head_end"]:
            anomalies["head_changed_during_review"].append(run_id)
        if design is None and record["execution"] == "full":
            anomalies["design_unresolved_but_full_execution"].append(run_id)
    elapsed = [int(record["elapsed_s"]) for record in completed if isinstance(record["elapsed_s"], int)]
    outcomes = [record["outcome"] for record in completed if isinstance(record["outcome"], dict)]
    outcome_counts = {"recorded": len(outcomes)}
    outcome_counts.update(_count([str(item["label"]) for item in outcomes], OUTCOME_LABELS))
    return {
        "schema": SCHEMA,
        "runs": runs_index,
        "counts": {
            "status": _count([str(record["status"]) for record in records], ("completed", "abandoned", "pending")),
            "verdict": _count([str(record["verdict"]) for record in completed], VERDICTS),
            "execution": _count([str(record["execution"]) for record in completed], EXECUTIONS),
            "abandon_reason": _count([str(record["abandon_reason"]) for record in records if record["status"] == "abandoned"]),
            "outcome": outcome_counts,
        },
        "cost": {
            "elapsed_s": {"median": int(statistics.median(elapsed)) if elapsed else None, "max": max(elapsed) if elapsed else None},
            "review_passes_avg": round(statistics.mean(int(record["review_passes"]) for record in completed), 1) if completed else None,
            "repair_passes_avg": round(statistics.mean(int(record["repair_passes"]) for record in completed), 1) if completed else None,
        },
        "chains": [
            {"repo": repo, "plan": plan_path, "runs": runs}
            for (repo, plan_path), runs in chains.items() if len(runs) >= 2
        ],
        "findings": {
            "total": len(severities), "by_severity": _count(severities),
            "by_status": _count(statuses), "by_class": _count(classes),
            "repeated_patterns": [
                {"class": key[0], "pattern": key[1], "count": len(run_ids), "run_ids": run_ids}
                for key, run_ids in sorted(pattern_runs.items()) if len(run_ids) >= 2
            ],
        },
        "anomalies": anomalies,
    }


def cmd_summary(args: argparse.Namespace, home: Path) -> dict[str, object]:
    if args.last is not None and args.last < 1:
        fail("invalid-arguments", "--last must be a positive integer")
    records = iter_records(home)
    if args.repo is not None:
        records = [record for record in records if record["repo"] == args.repo]
    if args.last is not None:
        records = records[-args.last :]
    return summarize(records)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise EvidenceError("invalid-arguments", message)


def build_parser() -> _Parser:
    parser = _Parser(prog="evidence.py", add_help=True)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    start.add_argument("--skill-root", required=True)
    start.add_argument("--repo", required=True)
    start.add_argument("--plan", required=True)
    start.add_argument("--design")
    start.add_argument("--client", required=True, choices=CLIENTS)
    start.add_argument("--model", default="unknown")
    start.add_argument("--mode", required=True, choices=MODES)
    finish = commands.add_parser("finish")
    finish.add_argument("--run-id", required=True)
    finish.add_argument("--repo", required=True)
    abandon = commands.add_parser("abandon")
    abandon.add_argument("--run-id", required=True)
    abandon.add_argument("--reason", required=True, choices=ABANDON_REASONS)
    outcome = commands.add_parser("outcome")
    outcome.add_argument("--run-id", required=True)
    outcome.add_argument("--label", required=True, choices=OUTCOME_LABELS)
    outcome.add_argument("--note")
    show = commands.add_parser("show")
    show.add_argument("--run-id", required=True)
    summary = commands.add_parser("summary")
    summary.add_argument("--repo")
    summary.add_argument("--last", type=int)
    return parser


def main(
    argv: list[str] | None = None, *, stdin: TextIO | None = None, stdout: TextIO | None = None,
    stderr: TextIO | None = None, environ: Mapping[str, str] | None = None, cwd: Path | None = None,
) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr
    environ = os.environ if environ is None else environ
    cwd = Path.cwd() if cwd is None else Path(cwd)
    try:
        if arguments == ["--version"]:
            stdout.write(canonical({"cli_version": CLI_VERSION, "schema": SCHEMA, "skill_name": SKILL_NAME}).decode("utf-8"))
            return 0
        if "--version" in arguments:
            fail("invalid-arguments", "--version accepts no other arguments")
        args = build_parser().parse_args(arguments)
        home = evidence_home(environ)
        if args.command == "start":
            result: object = cmd_start(args, home, cwd)
        elif args.command == "finish":
            result = cmd_finish(args, home, cwd, stdin)
        elif args.command == "abandon":
            result = cmd_abandon(args, home)
        elif args.command == "outcome":
            result = cmd_outcome(args, home)
        elif args.command == "show":
            stdout.write(cmd_show(args, home))
            return 0
        elif args.command == "summary":
            result = cmd_summary(args, home)
        stdout.write(canonical(result).decode("utf-8"))
        return 0
    except EvidenceError as exc:
        message = exc.message[:300].replace("\n", " ").replace("\r", " ")
        stderr.write(canonical({"error": {"code": exc.code, "message": message}}).decode("utf-8"))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
