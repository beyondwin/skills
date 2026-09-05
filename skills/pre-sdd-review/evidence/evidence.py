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


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # noqa: D401 - argparse hook
        raise EvidenceError("invalid-arguments", message)


def build_parser() -> _Parser:
    parser = _Parser(prog="evidence.py", add_help=True)
    parser.add_subparsers(dest="command", required=True)
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
        build_parser().parse_args(arguments)
        fail("invalid-arguments", "unknown command")
    except EvidenceError as exc:
        message = exc.message[:300].replace("\n", " ").replace("\r", " ")
        stderr.write(canonical({"error": {"code": exc.code, "message": message}}).decode("utf-8"))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
