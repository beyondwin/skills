"""Resolve an sddx implementer backend without launching a worker."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from typing import Any, Mapping

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

_UNTRANSPORTABLE = ("\n", "\r", "\x00")

# `cmd.exe` pairs `%` signs left to right and substitutes any name that resolves.
_PERCENT_NAME = re.compile(r"%([^%\r\n]+)%")


def _expandable_percent_name(argument: str, env: Mapping[str, str] | None = None) -> str | None:
    names = {name.upper() for name in (os.environ if env is None else env)}
    for name in _PERCENT_NAME.findall(argument):
        # Windows upper-cases environment names; `os.environ` mirrors that.
        if name.upper() in names:
            return name
    return None


def _quote_for_cmd(argument: str, env: Mapping[str, str] | None = None) -> str:
    """Quote one argument so `cmd.exe` and the child's CRT both read it back whole.

    A `.cmd`/`.bat` wrapper is parsed twice: once by `cmd.exe` for the `/c` command
    line and once by the batch file when it forwards `%*`. Only double quotes are
    inert across both layers, so every argument is quoted unconditionally and an
    embedded quote is doubled (`""`) rather than backslash-escaped: doubling keeps
    the quote count balanced, which keeps `& | < > ^ ( )` inside a quoted region at
    both layers, and the CRT argv parser reads `""` inside quotes as one literal
    quote. Backslashes that run into a quote are doubled because the CRT treats a
    backslash run before a quote as an escape. `subprocess.list2cmdline` handles
    only the CRT layer, which is why it is not enough here.

    `%NAME%` cannot be escaped inside quotes, so an argument naming a variable that
    actually resolves is rejected rather than silently rewritten. Undefined names are
    inert to `cmd.exe` and pass through as literal text.

    This rests on two documented conventions rather than OS guarantees. Batch `%*`
    substitution is a single left-to-right pass whose inserted text is not rescanned
    for `%` — without that, an undefined `%NAME%` would be deleted at the batch layer
    (batch deletes undefined names, unlike the `/c` line, which leaves them literal).
    And reading `""` inside a quoted region as one literal quote is the MSVC CRT /
    `CommandLineToArgvW` convention, which a child using its own argv parser need not
    follow.
    """
    for forbidden in _UNTRANSPORTABLE:
        if forbidden in argument:
            raise ValueError(f"argument cannot cross a cmd.exe wrapper: {argument!r}")
    name = _expandable_percent_name(argument, env)
    if name is not None:
        raise ValueError(
            f"argument cannot cross a cmd.exe wrapper: {argument!r} "
            f"(cmd.exe would expand %{name}%)"
        )
    quoted = ['"']
    backslashes = 0
    for char in argument:
        if char == "\\":
            backslashes += 1
            continue
        if char == '"':
            quoted.append("\\" * (backslashes * 2))
            quoted.append('""')
        else:
            quoted.append("\\" * backslashes)
            quoted.append(char)
        backslashes = 0
    quoted.append("\\" * (backslashes * 2))
    quoted.append('"')
    return "".join(quoted)


def _is_cmd_wrapper(executable: str) -> bool:
    return os.name == "nt" and os.path.splitext(executable)[1].lower() in {".cmd", ".bat"}


def _command(executable: str, arguments: list[str], *, env: Mapping[str, str] | None = None) -> list[str]:
    command = [executable, *arguments]
    if _is_cmd_wrapper(executable):
        comspec = os.environ.get("ComSpec") or "cmd.exe"
        # `/s` strips the outermost quote pair, so wrap the whole line in one more.
        line = " ".join(_quote_for_cmd(part, env) for part in command)
        return [comspec, "/d", "/s", "/c", f'"{line}"']
    return command


def _subprocess_args(
    executable: str, arguments: list[str], *, env: Mapping[str, str] | None = None
) -> list[str] | str:
    """What to hand `subprocess`; use this rather than `_command` to launch.

    On Windows `subprocess` joins a list with `list2cmdline`, which escapes every
    `"` as `\\"`. `cmd.exe` does not unescape backslashes, so a line already escaped
    for `cmd.exe` must reach `subprocess` as a string or the wrapper is mangled.
    """
    command = _command(executable, arguments, env=env)
    if _is_cmd_wrapper(executable):
        return f"{subprocess.list2cmdline(command[:4])} {command[4]}"
    return command


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
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _run(executable: str, arguments: list[str], timeout: float = 5.0) -> str:
    # `_run` is total by contract: it reports failure as an empty string and never
    # raises. `_probe` deliberately lets an untransportable argument surface, so that
    # one failure mode is absorbed here rather than in `_probe`.
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
    `cursor-Grok-4.6-high` is adopted and returned with its capitals intact.

    Deciding on the ID column is what rejects a description: `composer-2.5 - Grok-like
    reasoning` and its column-gap twin mention grok only after the separator, which is
    never examined, so neither yields a candidate. Prose and banners (`Available
    models`, `Available models include grok and others`, the `Tip: use --model ...`
    paragraph) carry no separator at all — single spaces join their words — so the whole
    line becomes the candidate and fails the single-token test on those spaces.
    """
    model_ids: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        separator = _COLUMN_SEPARATOR.search(stripped)
        candidate = stripped[: separator.start()] if separator is not None else stripped
        if not _MODEL_ID.fullmatch(candidate):
            continue
        if "grok" not in candidate.lower() or candidate in model_ids:
            continue
        model_ids.append(candidate)
    return model_ids


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
        "--resume",
    )
    return (
        all(_declares(help_text, flag) for flag in required)
        and _declares_value_option(help_text, "--disallowed-tools")
        and _declares_value_option(help_text, "--deny")
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
        and _declares(help_text, "--resume")
        # Both halves, for the same reason as the Grok gate above.
        and _declares(help_text, "--output-format")
        and _declares(help_text, CURSOR_OUTPUT_FORMAT)
    )


def _cursor_model_ids(executable: str, help_text: str) -> list[str]:
    for arguments in model_list_commands(help_text):
        probe = _probe(executable, arguments)
        if probe is not None and probe.returncode == 0:
            model_ids = parse_model_ids(probe.stdout)
            if model_ids:
                return model_ids
    return []


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
    model_ids = _cursor_model_ids(executable, help_text)
    if not model_ids:
        return _unavailable(backend, "no_grok_model")
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
