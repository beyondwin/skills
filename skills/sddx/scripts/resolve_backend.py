"""Resolve an sddx implementer backend without launching a worker."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Any

ALIASES = {"c": "cursor", "g": "grok", "cursor": "cursor", "grok": "grok"}


def _run(executable: str, arguments: list[str], timeout: float = 5.0) -> str:
    try:
        completed = subprocess.run(
            [executable, *arguments],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return f"{completed.stdout or ''}\n{completed.stderr or ''}"


def _is_grok_identity(text: str) -> bool:
    blob = text.lower()
    return "grok build" in blob or "xai-grok" in blob or "grok " in blob


def _is_cursor_identity(text: str) -> bool:
    if _is_grok_identity(text):
        return False
    blob = text.lower()
    return "cursor-agent" in blob or "cursor agent" in blob or "cursor cli" in blob


def _grok_flags_ok(help_text: str) -> bool:
    return (
        "--cwd" in help_text
        and "--no-plan" in help_text
        and "--no-subagents" in help_text
        and "--always-approve" in help_text
        and ("--reasoning-effort" in help_text or "--effort" in help_text)
        and ("--single" in help_text or "-p" in help_text)
        and "--resume" in help_text
    )


def _cursor_flags_ok(help_text: str) -> bool:
    return (
        ("--print" in help_text or "-p" in help_text)
        and ("--force" in help_text or "--yolo" in help_text)
        and "--trust" in help_text
        and ("--workspace" in help_text or "--cwd" in help_text)
        and "--model" in help_text
        and "--resume" in help_text
    )


def _unavailable(backend: str, reason: str) -> dict[str, Any]:
    return {
        "backend": backend,
        "available": False,
        "executable": None,
        "identity": None,
        "argv_prefix": None,
        "reason": reason,
    }


def _available(backend: str, executable: str, identity: str, argv: list[str]) -> dict[str, Any]:
    line = identity.strip().splitlines()[0] if identity.strip() else identity
    return {
        "backend": backend,
        "available": True,
        "executable": executable,
        "identity": line,
        "argv_prefix": argv,
        "reason": None,
    }


def resolve(backend_arg: str) -> dict[str, Any]:
    if backend_arg not in ALIASES:
        raise ValueError(f"unknown backend: {backend_arg}")
    backend = ALIASES[backend_arg]
    if backend == "grok":
        executable = shutil.which("grok")
        if executable is None:
            return _unavailable(backend, "not_found")
        identity = _run(executable, ["--version"]) or _run(executable, ["-v"])
        help_text = _run(executable, ["--help"])
        if not _is_grok_identity(f"{identity}\n{help_text}"):
            return _unavailable(backend, "identity_mismatch")
        if not _grok_flags_ok(help_text):
            return _unavailable(backend, "missing_flags")
        argv = [
            executable,
            "--no-plan",
            "--no-subagents",
            "--always-approve",
            "--disable-web-search",
        ]
        if "--sandbox" in help_text:
            argv.extend(["--sandbox", "workspace"])
        return _available(backend, executable, identity, argv)

    executable = shutil.which("cursor-agent")
    if executable is None:
        cursor = shutil.which("cursor")
        if cursor is not None:
            probe = f"{_run(cursor, ['--version'])}\n{_run(cursor, ['--help'])}"
            if _is_cursor_identity(probe):
                executable = cursor
    if executable is None:
        return _unavailable(backend, "not_found")
    identity = _run(executable, ["--version"]) or _run(executable, ["-v"])
    help_text = _run(executable, ["--help"])
    blob = f"{identity}\n{help_text}"
    if _is_grok_identity(blob) or not _is_cursor_identity(blob):
        return _unavailable(backend, "identity_mismatch")
    if not _cursor_flags_ok(help_text):
        return _unavailable(backend, "missing_flags")
    models = _run(executable, ["models"]) + _run(executable, ["--list-models"])
    if "grok" not in models.lower():
        return _unavailable(backend, "no_grok_model")
    force = "--force" if "--force" in help_text else "--yolo"
    print_flag = "--print" if "--print" in help_text else "-p"
    argv = [executable, print_flag, force, "--trust"]
    return _available(backend, executable, identity, argv)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resolve_backend.py")
    parser.add_argument("--backend", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.backend not in ALIASES:
        print(f"unknown backend: {args.backend}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(resolve(args.backend), ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
