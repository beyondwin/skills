"""Resolve an sddx implementer backend without launching a worker."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any

ALIASES = {"c": "cursor", "g": "grok", "cursor": "cursor", "grok": "grok"}

GROK_OUTPUT_FORMAT = "streaming-messages-json"
CURSOR_OUTPUT_FORMAT = "stream-json"
CURSOR_SANDBOX_MODE = "enabled"
# Do not exclude Agent/task: Grok also removes background shell get/kill tools.
GROK_DISALLOWED_TOOLS = "search_tool,use_tool"

# A help entry counts as declared only when the token stands on its own. Plain
# substring tests confuse `-p` with `--prompt-file` and `--model` with `--models`.
_TOKEN_BOUNDARY = r"(?<![\w-]){token}(?![\w-])"

# A subcommand listing indents the command name and separates the description by
# a column gap. Prose such as "  models are listed below" keeps a single space and
# is therefore never taken as a declaration.
_SUBCOMMAND_LINE = re.compile(r"^\s+(?P<name>[A-Za-z][\w-]*)(?:\s{2,}\S.*)?\s*$")

# A model identifier is a bare token: it starts alphanumeric and then holds only
# letters, digits, `.`, `_` and `-`. Anything carrying a space, quote, bracket, comma
# or `=` is prose from the CLI's own banner and is not a usable `--model` value. The
# leading character class is what refuses `-grok-4`, `.grok-4` and `_grok-4`: an
# identifier starting with `-` would be read as an option rather than a value by the
# CLI it is handed to, and `.`/`_` starts are listing decoration, not identifiers.
_MODEL_ID = re.compile(r"[0-9A-Za-z][0-9A-Za-z._-]*")

# A listing separates the ID from its description either by ` - ` or by a column gap.
# `_SUBCOMMAND_LINE` above already reads the CLI's other listing that way, so the two
# rules agree. A tab is a column gap on its own; spaces need a run of two, because a
# single space is how prose joins words.
_COLUMN_SEPARATOR = re.compile(r" - |\t|\s{2,}")
# A CLI may colour the ID column even when its output is a pipe, and an escape
# sequence is a terminal instruction, not part of the ID it wraps. The full CSI
# form is matched, not just SGR, so a cursor-positioning sequence cannot survive
# as an ID character either.
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")
# Asked of every probe so a CLI that honours any of these never emits the
# sequences at all. Measured on `cursor-agent --list-models`: `FORCE_COLOR=0` is
# the one it reads. The rest cost nothing and cover the CLIs that read them.
_COLOUR_FREE_ENV = {"FORCE_COLOR": "0", "NO_COLOR": "1", "CLICOLOR": "0"}

WINDOWS_UNSUPPORTED = "Windows is not a supported OS"


def refuse_windows() -> int | None:
    if os.name == "nt":
        print(f"BLOCKED: {WINDOWS_UNSUPPORTED}", file=sys.stderr)
        return 2
    return None


def _subprocess_args(executable: str, arguments: list[str]) -> list[str]:
    return [executable, *arguments]


def _probe(
    executable: str, arguments: list[str], timeout: float = 5.0
) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            _subprocess_args(executable, arguments),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, **_COLOUR_FREE_ENV},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _run(executable: str, arguments: list[str], timeout: float = 5.0) -> str:
    # `_run` is total by contract: it reports failure as an empty string and never
    # raises. `_probe` lets ValueError through so this handler can absorb it;
    # subprocess.run can still raise ValueError (for example an embedded NUL).
    try:
        completed = _probe(executable, arguments, timeout)
    except ValueError:
        return ""
    if completed is None:
        return ""
    return f"{completed.stdout or ''}\n{completed.stderr or ''}"


def _declares(help_text: str, token: str) -> bool:
    return re.search(_TOKEN_BOUNDARY.format(token=re.escape(token)), help_text) is not None


def _declares_value_option(help_text: str, flag: str) -> bool:
    """Require an option declaration with a value placeholder, not prose."""
    pattern = rf"^\s+(?:-\w,\s+)?{re.escape(flag)}[ \t]+(?:<[^>\n]+>|\[[^]\n]+\])"
    return re.search(pattern, help_text, re.MULTILINE) is not None


def _declares_positional_prompt(help_text: str) -> bool:
    """Require a Usage-line positional prompt, not a named `--prompt` option."""
    return (
        re.search(
            r"^Usage:.*\[prompt(?:\.\.\.)?\]",
            help_text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        is not None
    )


def _declares_subcommand(help_text: str, name: str) -> bool:
    for line in help_text.splitlines():
        match = _SUBCOMMAND_LINE.match(line)
        if match is not None and match.group("name") == name:
            return True
    return False


def model_list_commands(help_text: str) -> list[list[str]]:
    """Read-only model listing commands the CLI declares, in probe order."""
    commands: list[list[str]] = []
    if _declares_subcommand(help_text, "models"):
        commands.append(["models"])
    if _declares(help_text, "--list-models"):
        commands.append(["--list-models"])
    return commands


def parse_listed_ids(text: str) -> list[str]:
    """Every model ID a listing printed, in source order, without duplicates.

    This owns the column rule that `parse_model_ids` documents; the only thing it
    does not do is ask whether an ID is Grok. Reading the whole ID column is what
    lets `resolve` tell "no ID could be read at all" apart from "IDs were read and
    none is Grok" — two failures that look identical from a Grok-only list and need
    opposite responses from a controller.

    Escape sequences are removed before the line is read, because a CLI that
    colours its ID column is still printing the same IDs.
    """
    model_ids: list[str] = []
    for line in text.splitlines():
        stripped = _ANSI_ESCAPE.sub("", line).strip()
        separator = _COLUMN_SEPARATOR.search(stripped)
        candidate = stripped[: separator.start()] if separator is not None else stripped
        if not _MODEL_ID.fullmatch(candidate) or candidate in model_ids:
            continue
        model_ids.append(candidate)
    return model_ids


def parse_model_ids(text: str) -> list[str]:
    """Grok model IDs a listing actually printed, in source order, without duplicates.

    The rule reads the ID column and nothing else. A listing line is `<id>` alone, or
    `<id>` followed by a description behind a column separator — ` - `, a tab, or a run
    of two or more whitespace characters, whichever occurs first. The candidate is
    everything before that separator, or the whole stripped line when the line holds
    none; whitespace next to the separator belongs to the gap, so a padded
    `id  - description` still yields `id`. The candidate is adopted only when it is a
    single bare token of model-id shape (`_MODEL_ID`) that contains `grok`. The ID is
    returned exactly as printed — never synthesised, mutated or given an effort suffix;
    only the containment test is case-insensitive, so an ID printed as
    `cursor-Grok-4.6-high` is adopted and returned with its capitals intact. Colour
    escape sequences are not part of what was printed: `parse_listed_ids` removes
    them first, so a coloured listing reads exactly like its plain twin.

    Deciding on the ID column is what rejects a description: `composer-2.5 - Grok-like
    reasoning` and its column-gap twin mention grok only after the separator, which is
    never examined, so neither yields a candidate. Prose and banners (`Available
    models`, `Available models include grok and others`, the `Tip: use --model ...`
    paragraph) carry no separator at all — single spaces join their words — so the whole
    line becomes the candidate and fails the single-token test on those spaces.
    """
    return [name for name in parse_listed_ids(text) if "grok" in name.lower()]


def _is_grok_identity(text: str) -> bool:
    blob = text.lower()
    if "grok build" in blob or "xai-grok" in blob:
        return True
    return any(line.startswith("grok ") for line in blob.splitlines())


def _is_cursor_identity(text: str) -> bool:
    if _is_grok_identity(text):
        return False
    blob = text.lower()
    return "cursor-agent" in blob or "cursor agent" in blob or "cursor cli" in blob


def _grok_prompt_flag(help_text: str) -> str | None:
    for flag in ("--prompt-file", "--single", "-p"):
        if _declares(help_text, flag):
            return flag
    return None


def _grok_effort_flag(help_text: str) -> str | None:
    for flag in ("--reasoning-effort", "--effort"):
        if _declares(help_text, flag):
            return flag
    return None


def _grok_flags_ok(help_text: str) -> bool:
    required = (
        "--sandbox",
        "--rules",
        "--disable-web-search",
        "--cwd",
        "--no-plan",
        "--no-subagents",
        "--always-approve",
    )
    return (
        all(_declares(help_text, flag) for flag in required)
        and _declares_value_option(help_text, "--disallowed-tools")
        and _declares_value_option(help_text, "--deny")
        and _declares_value_option(help_text, "--resume")
        and _grok_effort_flag(help_text) is not None
        and _grok_prompt_flag(help_text) is not None
        # Both halves: `build_argv` always emits `--output-format <value>`, so a CLI
        # that spells the value under some other option cannot carry that argv.
        and _declares(help_text, "--output-format")
        and _declares(help_text, GROK_OUTPUT_FORMAT)
    )


def _cursor_flags_ok(help_text: str) -> bool:
    return (
        (_declares(help_text, "--print") or _declares(help_text, "-p"))
        and _declares(help_text, "--trust")
        and _declares(help_text, "--auto-review")
        and _declares(help_text, "--sandbox")
        and (_declares(help_text, "--workspace") or _declares(help_text, "--cwd"))
        and _declares(help_text, "--model")
        and _declares_value_option(help_text, "--resume")
        and _declares_positional_prompt(help_text)
        # Both halves, for the same reason as the Grok gate above.
        and _declares(help_text, "--output-format")
        and _declares(help_text, CURSOR_OUTPUT_FORMAT)
    )


# Why no Grok ID was adopted, weakest evidence first. A later listing may only
# replace an earlier reason with a better-evidenced one, so the answer does not
# depend on which alias the CLI happens to declare first.
_MODEL_LIST_REASONS = ("no_model_list", "model_list_unreadable", "no_grok_model")


def _cursor_model_ids(executable: str, help_text: str) -> tuple[list[str], str | None]:
    """Grok model IDs from the first usable listing, and why none was adopted.

    The reason separates three failures that one empty list used to hide: no
    listing was obtained at all, a listing came back that no ID could be read
    from, and IDs were read and none is Grok. Only the third is about Grok. The
    other two say nothing about which models exist, and reporting them as
    `no_grok_model` is what sent a controller hunting for a model that was never
    missing while the real fault was the reading.
    """
    reason = _MODEL_LIST_REASONS[0]

    def note(candidate: str) -> None:
        nonlocal reason
        if _MODEL_LIST_REASONS.index(candidate) > _MODEL_LIST_REASONS.index(reason):
            reason = candidate

    for arguments in model_list_commands(help_text):
        probe = _probe(executable, arguments)
        if probe is None or probe.returncode != 0:
            continue
        if not parse_listed_ids(probe.stdout):
            note("model_list_unreadable")
            continue
        model_ids = parse_model_ids(probe.stdout)
        if model_ids:
            return model_ids, None
        note("no_grok_model")
    return [], reason


def _unavailable(backend: str, reason: str) -> dict[str, Any]:
    return {
        "backend": backend,
        "available": False,
        "executable": None,
        "identity": None,
        "argv_prefix": None,
        "reason": reason,
        "launch": None,
        "model_ids": [],
    }


def _available(
    backend: str,
    executable: str,
    identity: str,
    argv: list[str],
    launch: dict[str, Any],
    model_ids: list[str],
) -> dict[str, Any]:
    line = identity.strip().splitlines()[0] if identity.strip() else identity
    return {
        "backend": backend,
        "available": True,
        "executable": executable,
        "identity": line,
        "argv_prefix": argv,
        "reason": None,
        "launch": launch,
        "model_ids": model_ids,
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
            "--disallowed-tools",
            GROK_DISALLOWED_TOOLS,
            "--deny",
            "MCPTool(*)",
            "--always-approve",
            "--disable-web-search",
            "--sandbox",
            "workspace",
        ]
        launch = {
            "cwd_flag": "--cwd",
            "prompt_flag": _grok_prompt_flag(help_text),
            "effort_flag": _grok_effort_flag(help_text),
            "output_format": GROK_OUTPUT_FORMAT,
        }
        # The Grok CLI selects its own model; `model_ids` exists for Cursor.
        return _available(backend, executable, identity, argv, launch, [])

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
    model_ids, reason = _cursor_model_ids(executable, help_text)
    if not model_ids:
        return _unavailable(backend, reason)
    print_flag = "--print" if _declares(help_text, "--print") else "-p"
    cwd_flag = "--workspace" if _declares(help_text, "--workspace") else "--cwd"
    argv = [executable, print_flag, "--trust", "--auto-review", "--sandbox", CURSOR_SANDBOX_MODE]
    launch = {
        "cwd_flag": cwd_flag,
        "prompt_flag": None,
        "effort_flag": None,
        "output_format": CURSOR_OUTPUT_FORMAT,
    }
    return _available(backend, executable, identity, argv, launch, model_ids)


def main(argv: list[str] | None = None) -> int:
    refused = refuse_windows()
    if refused is not None:
        return refused
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
