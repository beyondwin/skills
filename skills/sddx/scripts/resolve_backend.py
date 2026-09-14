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

# These names expand even when they are absent from the process environment block.
_CMD_DYNAMIC_NAMES = frozenset({
    "CD",
    "DATE",
    "TIME",
    "RANDOM",
    "ERRORLEVEL",
    "CMDEXTVERSION",
    "CMDCMDLINE",
    "HIGHESTNUMANODENUMBER",
})

_CMD_PROG_TOKEN = re.compile(r"^%_prog%$", re.IGNORECASE)
_CMD_DP0_TOKEN = re.compile(r"%~?dp0%?", re.IGNORECASE)


def _expandable_percent_name(argument: str, env: Mapping[str, str] | None = None) -> str | None:
    names = {name.upper() for name in (os.environ if env is None else env)}
    names |= _CMD_DYNAMIC_NAMES
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
    actually resolves is rejected rather than silently rewritten. `cmd.exe` dynamic
    names (`%CD%`, `%DATE%`, `%TIME%`, `%RANDOM%`, `%ERRORLEVEL%`, `%CMDEXTVERSION%`,
    `%CMDCMDLINE%`, `%HIGHESTNUMANODENUMBER%`) resolve even when they are absent from
    the environment mapping, so they are rejected too. Other undefined names are
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


def _cmd_tokens(command: str) -> list[str]:
    tokens: list[str] = []
    current: list[str] = []
    in_quote = False
    for char in command:
        if char == '"':
            in_quote = not in_quote
            continue
        if char in " \t" and not in_quote:
            if current:
                tokens.append("".join(current))
                current = []
            continue
        current.append(char)
    if in_quote:
        return []
    if current:
        tokens.append("".join(current))
    return tokens


def _last_unquoted_segment(line: str) -> str:
    last = 0
    in_quote = False
    index = 0
    length = len(line)
    while index < length:
        char = line[index]
        if char == '"':
            in_quote = not in_quote
            index += 1
            continue
        if not in_quote:
            if line.startswith("&&", index) or line.startswith("||", index):
                last = index + 2
                index += 2
                continue
            if char in "&|":
                last = index + 1
                index += 1
                continue
        index += 1
    return line[last:].strip()


def _cmd_forwarding_invocation(text: str) -> str | None:
    found: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("@"):
            line = line[1:].lstrip()
        if not line or line.upper().startswith("REM ") or line.startswith("::"):
            continue
        segment = _last_unquoted_segment(line)
        if segment.startswith("@"):
            segment = segment[1:].lstrip()
        tokens = _cmd_tokens(segment)
        if len(tokens) >= 2 and tokens[-1] == "%*":
            found = segment
    return found


def _expand_shim_token(token: str, shim_dir: str) -> str:
    prefix = shim_dir + os.sep
    expanded = _CMD_DP0_TOKEN.sub(lambda _match: prefix, token)
    if os.sep != "\\":
        expanded = expanded.replace("\\", os.sep)
    return os.path.normpath(expanded)


def _win32_executable(candidate: str) -> str | None:
    if not candidate:
        return None
    path = candidate
    if os.path.basename(path) == path:
        names = [path]
        extension = os.path.splitext(path)[1].lower()
        if extension not in {".exe", ".com"}:
            names = [f"{path}.exe", path]
        found = None
        for name in names:
            found = shutil.which(name)
            if found:
                break
        path = found or ""
    if not path or not os.path.isfile(path):
        return None
    if os.path.splitext(path)[1].lower() in {".cmd", ".bat"}:
        return None
    return os.path.abspath(path)


def _resolve_shim_interpreter(token: str, shim_dir: str) -> str | None:
    if _CMD_PROG_TOKEN.fullmatch(token):
        bundled = os.path.join(shim_dir, "node.exe")
        if os.path.isfile(bundled):
            return os.path.abspath(bundled)
        return _win32_executable("node.exe") or _win32_executable("node")
    return _win32_executable(_expand_shim_token(token, shim_dir))


def _unwrap_cmd_wrapper(executable: str) -> list[str] | None:
    """Resolve a forwarding `.cmd`/`.bat` shim to the Win32 image it launches.

    `cmd.exe` cannot carry a newline, so a PATH hit that is only a `exe script %*`
    wrapper (npm cmd-shim, pnpm, or a quoted interpreter plus script) is launched
    as that image instead. Anything that is not this shape stays on `cmd.exe`.
    """
    if not _is_cmd_wrapper(executable):
        return None
    try:
        with open(executable, encoding="utf-8", errors="surrogateescape") as handle:
            text = handle.read()
    except OSError:
        return None
    invocation = _cmd_forwarding_invocation(text)
    if invocation is None:
        return None
    tokens = _cmd_tokens(invocation)
    if len(tokens) < 2 or tokens[-1] != "%*":
        return None
    head = tokens[:-1]
    shim_dir = os.path.abspath(os.path.dirname(executable))
    interpreter = _resolve_shim_interpreter(head[0], shim_dir)
    if interpreter is None:
        return None
    if os.path.abspath(interpreter) == os.path.abspath(executable):
        return None
    prefix = [_expand_shim_token(token, shim_dir) for token in head[1:]]
    if prefix and not os.path.isfile(prefix[-1]):
        return None
    return [interpreter, *prefix]


def _uses_cmd_exe(executable: str, command: list[str]) -> bool:
    return (
        _is_cmd_wrapper(executable)
        and len(command) == 5
        and command[1:4] == ["/d", "/s", "/c"]
    )


def _windows_command_line(command: list[str]) -> str:
    """Join argv the way the MSVC CRT reads it, including quoting newlines.

    `subprocess.list2cmdline` quotes spaces and tabs but leaves `\\n` and `\\r`
    bare, so a list handed to `Popen` splits multiline `--rules` on Windows.
    Returning one string keeps `Popen` from running that conversion.
    """
    result: list[str] = []
    for argument in command:
        if "\x00" in argument:
            raise ValueError("argument cannot cross the process command line")
        need_quotes = (not argument) or any(char in argument for char in ' \t\n\r"')
        pieces: list[str] = ['"'] if need_quotes else []
        backslashes: list[str] = []
        for char in argument:
            if char == "\\":
                backslashes.append(char)
                continue
            if char == '"':
                pieces.append("\\" * (len(backslashes) * 2))
                backslashes = []
                pieces.append('\\"')
                continue
            pieces.extend(backslashes)
            backslashes = []
            pieces.append(char)
        if need_quotes:
            pieces.extend(backslashes)
            pieces.extend(backslashes)
            pieces.append('"')
        else:
            pieces.extend(backslashes)
        result.append("".join(pieces))
    return " ".join(result)


def _command(executable: str, arguments: list[str], *, env: Mapping[str, str] | None = None) -> list[str]:
    unwrapped = _unwrap_cmd_wrapper(executable)
    if unwrapped is not None:
        return [*unwrapped, *arguments]
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
    `"` as `\\"` and does not quote newlines. `cmd.exe` does not unescape
    backslashes, so a line already escaped for `cmd.exe` must reach `subprocess`
    as a string or the wrapper is mangled. A Win32 image uses the same string
    form, with newlines quoted, so multiline `--rules` survive. A forwarding
    `.cmd` shim is unwrapped to that Win32 image before quoting.
    """
    command = _command(executable, arguments, env=env)
    if _uses_cmd_exe(executable, command):
        return f"{subprocess.list2cmdline(command[:4])} {command[4]}"
    if os.name == "nt":
        return _windows_command_line(command)
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
