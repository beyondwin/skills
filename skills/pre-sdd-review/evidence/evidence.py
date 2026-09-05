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

CLI_VERSION = "2.0.0"
SCHEMA = 2
SKILL_NAME = "pre-sdd-review"
RECORD_LIMIT = 64 * 1024
DOCUMENT_LIMIT = 8 * 1024 * 1024
SKILL_DOCUMENT_LIMIT = 256 * 1024

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
FINISH_KEYS = frozenset({
    "execution", "reviewers", "trigger", "degraded_reasons", "verdict",
    "block_reason", "review_passes", "repair_passes", "findings",
})
FINDING_KEYS = frozenset({
    "id", "severity", "class", "pattern", "status", "repair_pass",
    "location", "evidence", "consequence", "fix",
})

_PATTERN = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}\Z")
_FINDING_ID = re.compile(r"PSDR-[0-9]{3,}\Z")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")
_VERSION_LINE = re.compile(r'^\s*version:\s*["\']?([^\s"\']+)["\']?\s*$', re.MULTILINE)
_DRIVE = re.compile(r"^[A-Za-z]:")


class EvidenceError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


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
    # Microsecond precision keeps `started_at` ordering stable for runs started in the same second.
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def elapsed_seconds(start: str, end: str) -> int:
    begin = dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
    finish = dt.datetime.fromisoformat(end.replace("Z", "+00:00"))
    return max(0, int((finish - begin).total_seconds()))


# ---------------------------------------------------------------- storage

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


# -------------------------------------------------------------------- git

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


# ------------------------------------------------------------- validation

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


# --------------------------------------------------------------- commands

def cmd_start(args: argparse.Namespace, home: Path, cwd: Path) -> dict[str, object]:
    root = git_root(locator(cwd, args.repo))
    plan = repository_relative(root, args.plan, cwd)
    design = None if args.design is None else repository_relative(root, args.design, cwd)
    head, dirty = git_state(root)
    skill = skill_snapshot(locator(cwd, args.skill_root))
    model = _string(args.model, "model", 100)
    run_id = str(uuid.uuid4())
    record: dict[str, object] = {
        "schema": SCHEMA,
        "run_id": run_id,
        "status": "pending",
        "started_at": utc_now(),
        "completed_at": None,
        "elapsed_s": None,
        "skill": skill,
        "client": {"id": args.client, "model": model},
        "repo": root.name,
        "mode": args.mode,
        "plan": {"path": plan, "sha_start": document_hash(root, plan), "sha_end": None},
        "design": None if design is None else {"path": design, "sha_start": document_hash(root, design), "sha_end": None},
        "git": {"head_start": head, "head_end": None, "dirty_start": dirty, "dirty_end": None},
        "execution": None,
        "reviewers": None,
        "trigger": None,
        "degraded_reasons": [],
        "review_passes": None,
        "repair_passes": None,
        "verdict": None,
        "block_reason": None,
        "abandon_reason": None,
        "findings": [],
        "outcome": None,
    }
    write_record(run_path(home, run_id), record)
    return {"run_id": run_id, "status": "pending"}


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: D401 - argparse hook
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
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
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
        else:
            fail("invalid-arguments", f"{args.command} is not implemented")
        stdout.write(canonical(result).decode("utf-8"))
        return 0
    except EvidenceError as exc:
        message = exc.message[:300].replace("\n", " ").replace("\r", " ")
        stderr.write(canonical({"error": {"code": exc.code, "message": message}}).decode("utf-8"))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
