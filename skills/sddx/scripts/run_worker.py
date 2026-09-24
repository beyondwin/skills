"""Launch one sddx worker attempt and preserve the evidence it will be judged on.

This is not an orchestrator. It has no scheduler, no retry, no backend failover,
and no process-tree management. The provider events it reads are the session ID
the worker reports in its own stream, and on `status` a bounded tools index
copied from `tool_call` JSON objects. It still does not judge DONE, 402, or role
compliance, and it still does not put log bodies in the default status payload.
It never decides whether a task succeeded: a process exit of 0 is not task
completion, and the files written here prove only what was handed to the CLI,
never that OS isolation held or that the model obeyed its instructions.

The `status` subcommand is the read-only half of the same file: it reports what
an attempt directory holds, a bounded tools index, and, on request, one
explicitly bounded byte window of a raw log. It launches nothing and writes
nothing.

The controller prepares the Grok sandbox profile before calling this runner and
cleans it up afterwards, once it has confirmed the worker and anything it
started have exited. The runner neither prepares nor cleans up, and it does not
guarantee process-tree exit.
"""

from __future__ import annotations

import argparse
import codecs
import contextlib
import decimal
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from resolve_backend import ALIASES, _subprocess_args, refuse_windows, resolve  # noqa: E402

# Resolved against this script, never against the caller's working directory.
WORKER_RULES_PATH = SCRIPT_DIR.parent / "references" / "worker-prompt.md"

SCHEMA_VERSION = 2
EVIDENCE_DIR_NAME = ".superpowers"
BRIEF_NAME = "brief.md"
DISPATCH_NAME = "dispatch.md"
STDOUT_NAME = "worker.jsonl"
STDERR_NAME = "stderr.log"
METADATA_NAME = "run.json"
REPORT_NAME = "report.md"

# The two bounds on one attempt, and how long a child gets to leave on a
# SIGTERM before it is killed. `--idle-timeout` ends a worker when neither raw
# log has grown for that many seconds, from launch onward, so a worker that
# never prints and one that stalls after printing are ended the same way.
# `--timeout` is an optional wall-clock bound and is off by default, because a
# worker that keeps writing is working. For both, 0 disables the bound.
DEFAULT_TIMEOUT_SECONDS = 0.0
DEFAULT_IDLE_TIMEOUT_SECONDS = 900.0
TERMINATE_GRACE_SECONDS = 10.0
TIMEOUT_EXIT = 124
TIMEOUT_ERROR = "the attempt exceeded its timeout"

INTERRUPTED_ERROR = "the runner was interrupted (SIGTERM or Ctrl-C)"

# The reading bounds from the design spec's R4. A window is a byte range, not a
# line, a JSON event, or a call/result pair: nothing here promises that a preview
# contains anything whole except the characters it decoded.
STREAM_FILES = {"stdout": STDOUT_NAME, "stderr": STDERR_NAME}
DEFAULT_WINDOW_BYTES = 2048
MAX_WINDOW_BYTES = 8192
MAX_RESPONSE_BYTES = 64 * 1024
TOOLS_READ_CAP = 64
TOOLS_SEARCH_CAP = 32
TOOLS_SHELL_CAP = 32
TOOLS_COMMAND_CHARS = 200

# A worker log can reach many megabytes, and the init event that names the
# session is the first line of every stream measured so far. These bounds keep
# the session scan to that prefix instead of the whole provider log.
SESSION_SCAN_BYTES = 64 * 1024
SESSION_SCAN_LINES = 200
# Wait is sliced so the first stream id can be copied while the child is still
# running. `--timeout 0` still means no bound; never `wait(timeout=0)`.
WAIT_SLICE_SECONDS = 1.0
# Both measured providers use session_id. The others are accepted because a
# rule written to one provider's shape is exactly what this runner keeps getting
# wrong, not because any of them has been seen.
SESSION_ID_KEYS = ("session_id", "sessionId", "chatId", "chat_id")

# The reading boundary from the design spec's R4, repeated in every dispatch so a
# resumed attempt carries it too.
BOUNDARY = """Read the brief first. Use its requirements and explicitly listed task
references. The controller owns the full plan; do not read it or follow
links to it, including through shell/search tools. Missing decisions go
back as NEEDS_CONTEXT. Read named source/test files directly first; content
searches must target the brief's Search paths, not the whole workspace.
Within this worktree, filename-only listings and direct reads of repository
ignore/build/test configuration needed for this task are allowed and are
not scope deviations. Never read full-plan content, credentials, or secrets
through these inspections. Report actual scope deviations even if tests pass."""


@dataclass(frozen=True)
class RunOptions:
    backend: str
    worktree: Path
    brief: Path
    attempt_dir: Path
    effort: str
    model: str | None = None
    resume_id: str | None = None
    sandbox_profile: str | None = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    idle_timeout: float = DEFAULT_IDLE_TIMEOUT_SECONDS


def utc_now() -> str:
    """A timezone-aware UTC timestamp, so attempts stay comparable across hosts."""
    return datetime.now(timezone.utc).isoformat()


def read_skill_version(root: Path | None = None) -> str:
    """The installed skill's release.toml version, or a short refusal.

    The runner lives next to the rest of the skill, including when the tree was
    copied without git. A missing or unreadable version is not guessed.
    """
    unavailable = "skill version is unavailable"
    skill_root = SCRIPT_DIR.parent if root is None else root
    try:
        data = tomllib.loads((skill_root / "release.toml").read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError(unavailable) from error
    version = data.get("version")
    if type(version) is not str:
        raise ValueError(unavailable)
    version = version.strip()
    if not version:
        raise ValueError(unavailable)
    return version


def write_metadata(path: Path, value: dict[str, Any]) -> None:
    """Replace `path` atomically from a temporary file in the same directory."""
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def _validated_attempt_dir(worktree: Path, attempt_dir: Path) -> tuple[Path, Path]:
    """Locate a brand new attempt directory inside this worktree's evidence tree.

    Containment is checked twice: lexically, so the symlink walk below has a
    terminating bound, and again after resolution, so a link that leaves the
    evidence tree cannot slip past. The walk itself inspects the literal path the
    caller supplied, because that is the path the launch will actually traverse.
    This mirrors `prepare_grok_sandbox._validated_paths`, which solves the same
    problem for the sandbox restoration record.
    """
    worktree_abs = Path(os.path.abspath(worktree))
    if not worktree_abs.is_dir():
        raise ValueError("worktree must be an existing directory")
    if worktree_abs.is_symlink():
        raise ValueError("worktree must not be a symbolic link")
    attempt_abs = Path(os.path.abspath(attempt_dir))
    evidence = worktree_abs / EVIDENCE_DIR_NAME
    try:
        relative = attempt_abs.relative_to(evidence)
    except ValueError as error:
        raise ValueError(
            f"attempt directory must be inside the worktree {EVIDENCE_DIR_NAME} directory"
        ) from error
    if not relative.parts:
        raise ValueError("attempt directory must be a new path below the evidence directory")
    if attempt_abs.exists() or attempt_abs.is_symlink():
        raise ValueError("attempt directory must not already exist")
    if not attempt_abs.parent.is_dir():
        raise ValueError("attempt directory parent must be an existing directory")

    current = attempt_abs
    while current != worktree_abs:
        if current.is_symlink():
            raise ValueError("attempt path must not contain symbolic links")
        current = current.parent

    resolved_parent = attempt_abs.parent.resolve()
    resolved_evidence = worktree_abs.resolve() / EVIDENCE_DIR_NAME
    if not resolved_parent.is_relative_to(resolved_evidence):
        raise ValueError(
            f"attempt directory must resolve inside the worktree {EVIDENCE_DIR_NAME} directory"
        )
    return worktree_abs, attempt_abs


# The effort tokens the real Cursor listing actually spells in its model IDs. A
# segment outside this set is not read as an effort.
EFFORT_TOKENS = frozenset({"none", "minimal", "low", "medium", "high", "xhigh", "max"})


def model_effort(model_id: str) -> str | None:
    """The effort a model ID declares, or `None` when it declares none.

    Some backends carry effort in the ID rather than on a flag. One trailing
    `-fast` is stripped first, because it is a serving variant and not an effort;
    only one, so `...-high-fast-fast` ends on `fast` and declares nothing. What
    remains is read at its final `-` segment and adopted only if it is a known
    effort token.

    A two-segment effort such as `extra-high` is refused rather than misread as
    `high`: reporting a wrong effort is worse than reporting none, and inventing a
    mapping onto a neighbouring token would be a guess. This reads effort segments
    only and knows no vendor.
    """
    segments = model_id.split("-")
    if len(segments) > 1 and segments[-1] == "fast":
        segments = segments[:-1]
    token = segments[-1]
    if token not in EFFORT_TOKENS:
        return None
    if len(segments) >= 2 and segments[-2] == "extra":
        return None
    return token


def _validated_backend(options: RunOptions) -> str:
    """Reject the option combinations this runner cannot honestly launch.

    Those are the backend pairings the resolver contract cannot express, and
    the attempt's own two bounds. Both are refused from here, before the attempt
    directory exists, so a rejected option leaves nothing behind to read.
    """
    if options.backend not in ALIASES:
        raise ValueError(f"unknown backend: {options.backend}")
    backend = ALIASES[options.backend]
    if not options.effort:
        raise ValueError("effort must be a non-empty value")
    if backend == "grok":
        if not options.sandbox_profile:
            raise ValueError("grok requires a prepared sandbox profile")
        if not options.model:
            raise ValueError("grok requires the confirmed grok-4.7 model id")
    else:
        if options.sandbox_profile is not None:
            raise ValueError("cursor uses its own sandbox mode; --sandbox-profile is not accepted")
        if not options.model:
            raise ValueError("cursor requires an explicit confirmed model id")
        declared = model_effort(options.model)
        if declared is not None and declared != options.effort:
            # The ID states the effort the provider will apply, so a differing
            # `--effort` is a contradiction, not a preference to reconcile.
            raise ValueError(
                f"cursor model {options.model} declares effort {declared}, "
                f"which contradicts --effort {options.effort}"
            )
    if options.resume_id is not None and not options.resume_id:
        raise ValueError("resume id must be a known non-empty session id")
    # Refused here rather than at `wait`: a NaN compares false against every
    # bound, and an infinity would be a second, undocumented spelling of "no
    # timeout" when `--timeout 0` already owns that meaning.
    if not math.isfinite(options.timeout) or options.timeout < 0:
        raise ValueError("timeout must be a finite, non-negative number of seconds")
    if not math.isfinite(options.idle_timeout) or options.idle_timeout < 0:
        raise ValueError("idle timeout must be a finite, non-negative number of seconds")
    return backend


def _worker_rules() -> str:
    return WORKER_RULES_PATH.read_text(encoding="utf-8")


def build_dispatch(backend: str, brief_path: Path, report_path: Path, rules: str) -> str:
    """The instruction text for this attempt, recorded verbatim in `dispatch.md`.

    Grok receives the worker rules through `--rules`, so they are not repeated
    here. Cursor has no such flag, so its dispatch carries them inline.
    """
    sections = [
        "# sddx worker dispatch",
        "",
        f"Task brief: {brief_path}",
        f"Report file: {report_path}",
        "",
        BOUNDARY,
        "",
        f"Write your report to {report_path} yourself. Nothing else writes it for you.",
    ]
    if backend != "grok":
        sections += ["", "## Worker rules", "", rules.rstrip("\n")]
    return "\n".join(sections) + "\n"


def build_argv(
    resolved: dict[str, Any], options: RunOptions, dispatch: Path, rules: str
) -> list[str]:
    """The command shape for one attempt, built from the resolver's own findings."""
    backend = resolved["backend"]
    launch = resolved["launch"]
    argv = list(resolved["argv_prefix"])
    if backend == "grok":
        # Replace the resolver's sandbox value so `--sandbox` appears exactly once.
        argv[argv.index("--sandbox") + 1] = str(options.sandbox_profile)
    # The same absolute path the child is started in; a relative `--cwd` would be
    # re-resolved against the worktree itself.
    argv += [launch["cwd_flag"], os.path.abspath(options.worktree)]
    argv += ["--output-format", launch["output_format"]]
    if backend == "grok":
        argv += ["--rules", rules]
    argv += ["--model", str(options.model)]
    if launch["effort_flag"] is not None:
        argv += [launch["effort_flag"], options.effort]
    if options.resume_id is not None:
        argv += ["--resume", options.resume_id]

    prompt_flag = launch["prompt_flag"]
    if prompt_flag == "--prompt-file":
        argv += [prompt_flag, str(dispatch)]
        return argv
    text = dispatch.read_text(encoding="utf-8")
    if prompt_flag is None:
        argv.append(text)
    else:
        argv += [prompt_flag, text]
    return argv


def _blocked(message: str) -> int:
    print(f"BLOCKED: {message}", file=sys.stderr)
    return 2


def read_session_id(path: Path) -> str | None:
    """The session ID the worker reported in its own stream, or `None`.

    The stream belongs to the provider, so a line that is not a JSON object is
    skipped rather than treated as an error and a truncated final line is
    normal. Within a line the keys are tried in their listed order and the first
    non-empty string wins. This never raises: an ID that cannot be recovered is
    a fact to record, not a failure to report.
    """
    try:
        with path.open("rb") as handle:
            head = handle.read(SESSION_SCAN_BYTES)
    except OSError:
        return None
    lines = head.decode("utf-8", errors="replace").splitlines()[:SESSION_SCAN_LINES]
    for line in lines:
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            continue
        if not isinstance(event, dict):
            continue
        for key in SESSION_ID_KEYS:
            value = event.get(key)
            # A number or a list is not an ID, and neither is an empty string.
            if isinstance(value, str) and value:
                return value
    return None


def remember_session_id(metadata: dict[str, Any], path: Path) -> bool:
    """Copy the first stream session id into the record. Never replace one."""
    if isinstance(metadata.get("session_id"), str) and metadata["session_id"]:
        return False
    found = read_session_id(path)
    if not found:
        return False
    metadata["session_id"] = found
    return True


def run_worker(options: RunOptions) -> int:
    """Run one attempt and return the wrapper exit for it.

    A normally awaited worker's exit is returned as-is; a POSIX signal death
    becomes `128 + signal` while `run.json` keeps the real negative returncode.
    A launch failure is 2, a runner interrupt handled here is 130, and an
    attempt ended by its wall-clock or idle timeout is 124.
    """
    try:
        worktree, attempt_dir = _validated_attempt_dir(options.worktree, options.attempt_dir)
        backend = _validated_backend(options)
        brief_bytes = options.brief.read_bytes()
        rules = _worker_rules()
        skill_version = read_skill_version()
        attempt_dir.mkdir()
        (attempt_dir / BRIEF_NAME).write_bytes(brief_bytes)
    except (OSError, ValueError) as error:
        return _blocked(str(error))

    metadata_path = attempt_dir / METADATA_NAME
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "skill_version": skill_version,
        "backend": backend,
        "identity": None,
        "model": None,
        "worktree": str(worktree),
        "attempt_dir": str(attempt_dir),
        "brief_sha256": hashlib.sha256(brief_bytes).hexdigest(),
        "resume_id": options.resume_id,
        "session_id": None,
        "requested_effort": options.effort,
        "configured_effort": None,
        "state": "starting",
        "pid": None,
        "exit_code": None,
        "started_at": utc_now(),
        "ended_at": None,
        "error": None,
    }
    write_metadata(metadata_path, metadata)

    def fail(message: str) -> int:
        # `message` is a short reason only: never the environment, the dispatch,
        # the rules, or the brief.
        metadata.update(state="launch_failed", error=message, ended_at=utc_now())
        write_metadata(metadata_path, metadata)
        return _blocked(message)

    try:
        resolved = resolve(backend)
    except (OSError, ValueError):
        # The resolver is total by contract; this keeps that contract total for the
        # runner too, so a raise is a recorded `launch_failed` rather than a
        # traceback over a `run.json` frozen at `starting`. The original message can
        # quote an executable path, so it is not kept.
        return fail("could not resolve the backend")
    if not resolved["available"]:
        return fail(f"{backend} backend is unavailable: {resolved['reason']}")
    if options.model not in resolved["model_ids"]:
        return fail("model is not one of the backend's confirmed model ids")

    metadata["identity"] = resolved["identity"]
    # Recorded because it was named on the command line, not because the
    # model was proven to apply it.
    metadata["model"] = options.model
    if resolved["launch"]["effort_flag"] is not None:
        metadata["configured_effort"] = options.effort
    elif options.model is not None:
        # No flag carries the effort, so the only evidence is the ID itself.
        # `None` stays `null`: the applied effort is then genuinely unknown.
        metadata["configured_effort"] = model_effort(options.model)

    dispatch_path = attempt_dir / DISPATCH_NAME
    dispatch_text = build_dispatch(
        backend, attempt_dir / BRIEF_NAME, attempt_dir / REPORT_NAME, rules
    )
    try:
        with dispatch_path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(dispatch_text)
        argv = build_argv(resolved, options, dispatch_path, rules)
    except (OSError, ValueError):
        return fail("could not build the backend command from the resolver result")
    # Session-scoped discovery switches: never rewrite user MCP configuration or
    # relocate authentication/session storage. Native Grok MCP configuration may
    # still initialize; the resolver separately removes MCP invocation tools.
    worker_env = None
    if backend == "grok":
        worker_env = dict(os.environ)
        worker_env.update(GROK_CURSOR_MCPS_ENABLED="0", GROK_CLAUDE_MCPS_ENABLED="0")
    command = _subprocess_args(argv[0], argv[1:])

    stdout_path = attempt_dir / STDOUT_NAME
    stderr_path = attempt_dir / STDERR_NAME
    with contextlib.ExitStack() as stack:
        try:
            out = stack.enter_context(stdout_path.open("xb"))
            err = stack.enter_context(stderr_path.open("xb"))
        except OSError:
            return fail("could not create the raw worker output files")
        process: subprocess.Popen[bytes] | None = None

        def interrupted(already_signalled: bool = False) -> int:
            # Recorded first, so a second interrupt can never leave `running`.
            # Then this one child is ended the way a timeout ends it: a worker
            # left alive keeps editing the worktree after the record says it
            # stopped, and the next attempt shares that tree. Its descendants
            # and Grok cleanup stay the controller's call. An interrupted
            # attempt may still be resumable, so keep the first ID already found.
            # Further interrupts are held off until that record is on disk. Any
            # held meanwhile are taken while still blocked, so none is left to
            # arrive at the restore, and they count as a second request to stop.
            # Not around `Popen`: the child would inherit the mask.
            stop_signals = {signal.SIGINT, signal.SIGTERM}
            held = False
            old_mask = None
            try:
                if hasattr(signal, "pthread_sigmask"):
                    # Read first, so a signal the block call raises still
                    # leaves a mask to restore.
                    try:
                        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, set())
                        signal.pthread_sigmask(signal.SIG_BLOCK, stop_signals)
                    except KeyboardInterrupt:
                        held = True
                remember_session_id(metadata, stdout_path)
                metadata.update(
                    state="interrupted",
                    exit_code=process.poll(),
                    ended_at=utc_now(),
                    error=INTERRUPTED_ERROR,
                )
                write_metadata(metadata_path, metadata)
            finally:
                if old_mask is not None:
                    try:
                        for signum in signal.sigpending() & stop_signals:
                            signal.sigwait({signum})
                            held = True
                        signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
                    except KeyboardInterrupt:
                        held = True
            # The record already says `interrupted`; the re-record only refines
            # `exit_code`. A further interrupt here must not turn the 130 into
            # a traceback, so it is absorbed and `exit_code` stays what it was.
            with contextlib.suppress(KeyboardInterrupt):
                if process.poll() is None:
                    if already_signalled or held:
                        # The timeout was already ending the child (SIGTERM
                        # sent, or about to be), or another interrupt was held
                        # during the record, so this second request to stop
                        # skips the grace and kills.
                        _kill_child(process)
                    else:
                        _stop_child(process)
                    metadata["exit_code"] = process.poll()
                    write_metadata(metadata_path, metadata)
            return 130

        def timed_out(error: str = TIMEOUT_ERROR) -> int:
            try:
                # Only this child is pursued. It shares the controller's process
                # group on purpose, so there is no group signal to send and
                # anything the worker started is left exactly where it is.
                _end_process(process)
                remember_session_id(metadata, stdout_path)
                metadata.update(
                    state="timed_out",
                    exit_code=process.poll(),
                    ended_at=utc_now(),
                    error=error,
                )
                write_metadata(metadata_path, metadata)
            except KeyboardInterrupt:
                # Ending the child can take twenty seconds, and a Ctrl-C inside
                # that window must not leave `run.json` frozen at `running`.
                # What is recorded is what actually happened: an interrupt that
                # arrived while the timeout was still being carried out.
                return interrupted(already_signalled=True)
            return TIMEOUT_EXIT

        def _raise_keyboard_interrupt(signum, frame):
            raise KeyboardInterrupt

        # SIGTERM to this runner is the same request as Ctrl-C: record
        # interrupted and end the child. Installed just before the launch, so
        # no SIGTERM can land between `Popen` and the handler and leave the
        # worker running unrecorded; restored on every way out, a launch
        # failure included.
        previous = signal.signal(signal.SIGTERM, _raise_keyboard_interrupt)
        try:
            try:
                process = subprocess.Popen(
                    command,
                    cwd=str(worktree),
                    env=worker_env,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                )
            except OSError as error:
                return fail(f"could not start the backend process: {error.strerror or 'OSError'}")

            metadata.update(state="running", pid=process.pid)
            write_metadata(metadata_path, metadata)
            if remember_session_id(metadata, stdout_path):
                write_metadata(metadata_path, metadata)

            # `wait(timeout=0)` expires immediately, so a zero timeout must not
            # reach it: zero is the documented way to ask for no bound at all.
            deadline = time.monotonic() + options.timeout if options.timeout else None
            # Idleness is growth of either raw log, sampled once per wait slice.
            last_sizes = (_log_size(stdout_path), _log_size(stderr_path))
            last_activity = time.monotonic()
            while True:
                if deadline is None:
                    slice_timeout = WAIT_SLICE_SECONDS
                else:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return timed_out()
                    slice_timeout = min(WAIT_SLICE_SECONDS, remaining)
                try:
                    code = process.wait(timeout=slice_timeout)
                    break
                except subprocess.TimeoutExpired:
                    if remember_session_id(metadata, stdout_path):
                        write_metadata(metadata_path, metadata)
                    now = time.monotonic()
                    if deadline is not None and now >= deadline:
                        return timed_out()
                    sizes = (_log_size(stdout_path), _log_size(stderr_path))
                    if sizes != last_sizes:
                        last_sizes, last_activity = sizes, now
                    elif options.idle_timeout and now - last_activity >= options.idle_timeout:
                        return timed_out(idle_error(options.idle_timeout))
            remember_session_id(metadata, stdout_path)
            metadata.update(
                state="exited",
                exit_code=code,
                ended_at=utc_now(),
            )
            write_metadata(metadata_path, metadata)
        except KeyboardInterrupt:
            # One raised inside `Popen` itself has no child handle to end yet.
            if process is None:
                raise
            return interrupted()
        finally:
            signal.signal(signal.SIGTERM, previous)
    return code if code >= 0 else 128 - code


def _end_process(process: subprocess.Popen[bytes]) -> None:
    """Ask this one child to leave, then insist, then stop waiting on it.

    Neither wait is unbounded, because a process that answers neither signal
    must not turn a timeout into the hang it was added to prevent. What was
    actually recovered is whatever `poll()` reports afterwards, `None` included.
    """
    process.terminate()
    try:
        process.wait(timeout=TERMINATE_GRACE_SECONDS)
        return
    except subprocess.TimeoutExpired:
        pass
    process.kill()
    with contextlib.suppress(subprocess.TimeoutExpired):
        process.wait(timeout=TERMINATE_GRACE_SECONDS)


def _stop_child(process: subprocess.Popen[bytes]) -> None:
    """End the child even when another interrupt arrives while doing it.

    A second Ctrl-C or SIGTERM during the grace period skips straight to kill;
    what was recovered is whatever `poll()` reports afterwards.
    """
    try:
        _end_process(process)
    except KeyboardInterrupt:
        _kill_child(process)


def _kill_child(process: subprocess.Popen[bytes]) -> None:
    """Kill this one child now and wait for it, but never without a bound."""
    with contextlib.suppress(ProcessLookupError):
        process.kill()
    with contextlib.suppress(subprocess.TimeoutExpired, KeyboardInterrupt):
        process.wait(timeout=TERMINATE_GRACE_SECONDS)


def idle_error(seconds: float) -> str:
    """The `error` of an attempt ended by its idle timeout.

    The seconds are a plain number: an integer when integral (`900`, never
    `900.0` or `1e+06`), else a positional decimal (`0.5`).
    """
    if float(seconds).is_integer():
        text = str(int(seconds))
    else:
        text = format(decimal.Decimal(repr(float(seconds))), "f")
    return f"the worker wrote no output for {text} seconds"


def _log_size(path: Path) -> int:
    """The current byte size of a log, or 0 when the runner never created it."""
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def read_metadata(path: Path) -> dict[str, Any] | None:
    """The attempt record, or `None` when the runner never wrote one.

    An absent `run.json` is reported as absent rather than as a failure: an
    interrupted runner is exactly when the controller most needs the raw
    evidence. A record that exists but cannot be read honestly is an error,
    because reporting its contents would be a guess.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except UnicodeDecodeError as error:
        raise ValueError(f"{METADATA_NAME} is not UTF-8 text") from error
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"{METADATA_NAME} is not readable JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{METADATA_NAME} must hold a JSON object")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"{METADATA_NAME} schema_version must be {SCHEMA_VERSION}")
    return value


def read_window(path: Path, stream: str, offset: int, max_bytes: int) -> dict[str, Any]:
    """One bounded byte window of a growing log, read without consuming a partial character.

    The size comes from the same handle the bytes come from, so both describe one
    view of a file that may still be growing. This call's end of file is not the
    end of the input: an incomplete UTF-8 suffix is reported through
    `pending_bytes` and left where it is, so the next call can read that
    character whole once the rest of it lands.
    """
    try:
        handle = path.open("rb")
    except FileNotFoundError as error:
        raise ValueError(f"{path.name} does not exist in this attempt directory") from error
    with handle:
        size = os.fstat(handle.fileno()).st_size
        if offset > size:
            raise ValueError(f"offset is past the {size} byte end of {path.name}")
        handle.seek(offset)
        chunk = handle.read(min(max_bytes, size - offset))

    decoder = codecs.getincrementaldecoder("utf-8")("replace")
    preview = decoder.decode(chunk, final=False)
    pending, _ = decoder.getstate()
    consumed = len(chunk) - len(pending)
    next_offset = offset + consumed
    if consumed == 0 and pending and offset + len(chunk) < size:
        # Bytes already follow this window, so the character is not merely
        # unfinished: the window is too small to hold it. Reporting it as a wait
        # would stall a caller on a file that has nothing left to deliver.
        raise ValueError(
            f"max_bytes {max_bytes} is too small to decode a character at offset {offset}"
        )

    decode_errors = False
    if consumed:
        try:
            chunk[:consumed].decode("utf-8")
        except UnicodeDecodeError:
            # The invalid bytes stay on disk exactly as written; only this
            # preview shows them replaced.
            decode_errors = True

    return {
        "stream": stream,
        "offset": offset,
        "next_offset": next_offset,
        "size": size,
        "preview": preview,
        "has_more": next_offset < size,
        "decode_errors": decode_errors,
        "pending_bytes": len(pending),
    }


def _first_str(values: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = values.get(key)
        if isinstance(value, str):
            return value
    return None


def _shell_exit_code(result: object) -> int | None:
    if not isinstance(result, dict):
        return None
    candidates: list[object] = [result.get("exitCode")]
    for nested_key in ("success", "failure"):
        nested = result.get(nested_key)
        if isinstance(nested, dict):
            candidates.append(nested.get("exitCode"))
    for value in candidates:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _append_capped(items: list[Any], item: Any, cap: int, index: dict[str, Any]) -> bool:
    if len(items) >= cap:
        index["truncated"] = True
        return False
    items.append(item)
    return True


GROK_SHELL_TOOL = "run_terminal_command"


def _message_items(event: dict[str, Any]) -> list[Any]:
    """The content items of a Grok `assistant`/`user` event, or none."""
    message = event.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    return content if isinstance(content, list) else []


def _grok_exit_code(content: object) -> int | None:
    """The integer `exit_code` inside a Grok shell result, never its body."""
    if isinstance(content, list):
        texts = [
            item.get("text")
            for item in content
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        content = texts[0] if texts else None
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, RecursionError):
            return None
    if not isinstance(content, dict):
        return None
    value = content.get("exit_code")
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _index_grok_items(
    items: list[Any],
    index: dict[str, Any],
    seen_reads: set[str],
    shells_by_id: dict[str, dict[str, Any]],
) -> None:
    """Add Grok `tool_use` calls, and the exit of a shell's `tool_result`.

    A shell is known by its tool name alone: grep results carry `exit_code`
    too. A shell whose result never arrives, or carries no integer exit (a
    background task), keeps `exit_code: None`.
    """
    for item in items:
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind == "tool_use":
            name = item.get("name")
            args = item.get("input")
            if not isinstance(args, dict):
                continue
            if name == "read_file":
                path_value = args.get("target_file")
                if isinstance(path_value, str) and path_value not in seen_reads:
                    if _append_capped(index["reads"], path_value, TOOLS_READ_CAP, index):
                        seen_reads.add(path_value)
            elif name == "grep":
                _append_capped(
                    index["searches"],
                    {"pattern": _first_str(args, "pattern"), "path": _first_str(args, "path")},
                    TOOLS_SEARCH_CAP,
                    index,
                )
            elif name == "list_dir":
                _append_capped(
                    index["searches"],
                    {"pattern": None, "path": _first_str(args, "target_directory")},
                    TOOLS_SEARCH_CAP,
                    index,
                )
            elif name == GROK_SHELL_TOOL:
                command = args.get("command")
                if not isinstance(command, str):
                    command = ""
                entry: dict[str, Any] = {
                    "exit_code": None,
                    "command": command[:TOOLS_COMMAND_CHARS],
                }
                if _append_capped(index["shells"], entry, TOOLS_SHELL_CAP, index):
                    tool_id = item.get("id")
                    if isinstance(tool_id, str):
                        shells_by_id[tool_id] = entry
        elif kind == "tool_result":
            tool_id = item.get("tool_use_id")
            if not isinstance(tool_id, str):
                continue
            entry = shells_by_id.pop(tool_id, None)
            if entry is not None:
                entry["exit_code"] = _grok_exit_code(item.get("content"))


def read_tools_index(path: Path) -> dict[str, Any]:
    """Copy a bounded index of read, search, and shell tool calls from a log.

    Two shapes are read: Cursor `type == tool_call` objects, and Grok
    `assistant`/`user` events whose `message.content` holds `tool_use` and
    `tool_result` items. Result bodies, thinking text, and unknown tool shapes
    are skipped. A missing file is an empty index, not an error. Caps are hard:
    extra entries set `truncated` and are not appended. This projection is not
    a judgement of DONE, 402, or role compliance.
    """
    index: dict[str, Any] = {
        "reads": [],
        "searches": [],
        "shells": [],
        "truncated": False,
    }
    if not path.is_file():
        return index
    seen_reads: set[str] = set()
    shells_by_id: dict[str, dict[str, Any]] = {}
    try:
        handle = path.open("rb")
    except FileNotFoundError:
        return index
    with handle:
        for raw in handle:
            try:
                event = json.loads(raw)
            except (json.JSONDecodeError, UnicodeDecodeError, RecursionError):
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") in ("assistant", "user"):
                _index_grok_items(_message_items(event), index, seen_reads, shells_by_id)
                continue
            if event.get("type") != "tool_call":
                continue
            tool_call = event.get("tool_call")
            if not isinstance(tool_call, dict):
                continue
            subtype = event.get("subtype")
            for name, payload in tool_call.items():
                if not isinstance(name, str) or not name.endswith("ToolCall"):
                    continue
                if not isinstance(payload, dict):
                    continue
                args = payload.get("args")
                if not isinstance(args, dict):
                    continue
                lowered = name.lower()
                if subtype == "started" and "read" in lowered:
                    path_value = args.get("path")
                    if not isinstance(path_value, str) or path_value in seen_reads:
                        continue
                    if _append_capped(index["reads"], path_value, TOOLS_READ_CAP, index):
                        seen_reads.add(path_value)
                elif subtype == "started" and any(
                    token in lowered for token in ("grep", "glob", "search")
                ):
                    _append_capped(
                        index["searches"],
                        {
                            "pattern": _first_str(args, "pattern", "globPattern"),
                            "path": _first_str(
                                args, "path", "targetDirectory", "target_directory"
                            ),
                        },
                        TOOLS_SEARCH_CAP,
                        index,
                    )
                elif subtype == "completed" and "shell" in lowered:
                    exit_code = _shell_exit_code(payload.get("result"))
                    if exit_code is None:
                        continue
                    command = args.get("command")
                    if not isinstance(command, str):
                        command = ""
                    _append_capped(
                        index["shells"],
                        {
                            "exit_code": exit_code,
                            "command": command[:TOOLS_COMMAND_CHARS],
                        },
                        TOOLS_SHELL_CAP,
                        index,
                    )
    return index


def pid_alive(pid: int | None) -> bool | None:
    """Whether `os.kill(pid, 0)` can still see that process.

    This is a live probe of the recorded pid, not a field in `run.json`. A
    missing or non-integer pid is unknown. A dead pid is reported as false
    without rewriting the record.
    """
    if not isinstance(pid, int) or isinstance(pid, bool):
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _recoverable_session_id(metadata: dict[str, Any] | None, path: Path) -> str | None:
    """The log's session ID, only when the record does not already hold one.

    Read from the same bounded prefix the runner scans, so this costs no more
    than the record already paid for. Answering `None` when the record has an ID
    keeps `session_id` the single value to resume from: two fields that could
    disagree would be a question, not an answer.
    """
    if metadata is None:
        return None
    recorded = metadata.get("session_id")
    if isinstance(recorded, str) and recorded:
        return None
    return read_session_id(path)


def read_status(
    attempt_dir: Path,
    *,
    stream: str | None = None,
    offset: int = 0,
    max_bytes: int = DEFAULT_WINDOW_BYTES,
) -> dict[str, Any]:
    """Read-only facts about one attempt, plus one bounded log window on request.

    Nothing here launches, writes, retries, or checks a billing state. The
    default payload copies a bounded tools index from `tool_call` objects; it
    does not judge DONE, 402, or role compliance, and it never carries a log
    body, because a controller asking how an attempt is doing must not pay for
    the transcript to find out.
    """
    if stream is not None and stream not in STREAM_FILES:
        raise ValueError(f"stream must be one of {sorted(STREAM_FILES)}")
    if offset < 0:
        raise ValueError("offset must not be negative")
    if not 1 <= max_bytes <= MAX_WINDOW_BYTES:
        raise ValueError(f"max_bytes must be between 1 and {MAX_WINDOW_BYTES}")

    # Resolved against the caller's working directory: unlike `run`, a query is
    # not confined to a worktree, because the controller names the directory it
    # already owns.
    attempt = Path(os.path.abspath(attempt_dir))
    if not attempt.is_dir():
        raise ValueError("attempt directory does not exist")

    metadata = read_metadata(attempt / METADATA_NAME)
    alive = pid_alive(metadata.get("pid") if metadata else None)
    payload: dict[str, Any] = {
        "attempt_dir": str(attempt),
        "metadata": metadata,
        # Surfaced beside the record so a controller can read the session the
        # attempt reported without opening the raw log. It is still the record's
        # value: nothing here interprets a log body to produce it.
        "session_id": metadata.get("session_id") if metadata is not None else None,
        # The session the log reports, offered only when the record has none. A
        # runner killed before its first re-read leaves `run.json` at null while
        # the ID is already on line one, and a controller that cannot see it
        # re-runs a task whose worker session is still resumable. The record's own
        # value is never overwritten or second-guessed, and nothing is written.
        "session_id_in_log": _recoverable_session_id(metadata, attempt / STDOUT_NAME),
        "pid_alive": alive,
        # The rule SKILL.md states for a controller, answered here instead of
        # remembered there: a record left at `running` by a runner that could not
        # write a terminal state is stale, not a live worker.
        "stale": bool(metadata) and metadata.get("state") == "running" and not alive,
        "tools": read_tools_index(attempt / STDOUT_NAME),
        "stdout_bytes": _log_size(attempt / STDOUT_NAME),
        "stderr_bytes": _log_size(attempt / STDERR_NAME),
        "report_exists": (attempt / REPORT_NAME).is_file(),
    }
    if stream is None:
        return payload

    window = read_window(attempt / STREAM_FILES[stream], stream, offset, max_bytes)
    # The streamed log's reported size is the one the window was cut from, so the
    # two cannot disagree about a file that grew between two stat calls.
    payload[f"{stream}_bytes"] = window["size"]
    payload.update(window)
    return payload


def render_status(payload: dict[str, Any]) -> str:
    """Serialize a status payload, refusing to answer over the response limit.

    An over-limit answer is an error, never a quiet truncation: a controller that
    received a trimmed preview would take it for the whole window and advance
    past bytes it never saw.
    """
    document = json.dumps(payload, ensure_ascii=False, indent=2)
    measured = len(document.encode("utf-8"))
    if measured > MAX_RESPONSE_BYTES:
        raise ValueError(
            f"the response is {measured} bytes, over the {MAX_RESPONSE_BYTES} byte limit; "
            "ask for a smaller --max-bytes"
        )
    return document


def status_command(attempt_dir: Path, stream: str | None, offset: int, max_bytes: int) -> int:
    """Print one status document, or report an input error as exit 2."""
    try:
        document = render_status(
            read_status(attempt_dir, stream=stream, offset=offset, max_bytes=max_bytes)
        )
    except (OSError, ValueError) as error:
        return _blocked(str(error))
    print(document)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_worker.py", description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run", help="launch one worker attempt and wait for it")
    run.add_argument("--backend", required=True, choices=sorted(ALIASES))
    run.add_argument("--worktree", required=True, type=Path)
    run.add_argument("--brief", required=True, type=Path)
    run.add_argument("--attempt-dir", required=True, type=Path)
    run.add_argument("--effort", required=True)
    run.add_argument("--model")
    run.add_argument("--resume", dest="resume_id")
    run.add_argument("--sandbox-profile")
    run.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="wall-clock seconds before the attempt is ended; 0 (default) waits without a bound",
    )
    run.add_argument(
        "--idle-timeout",
        type=float,
        default=DEFAULT_IDLE_TIMEOUT_SECONDS,
        help="seconds without stdout or stderr growth before the attempt is ended; 0 disables",
    )
    status = subcommands.add_parser(
        "status", help="report attempt facts and, on request, one bounded log window"
    )
    status.add_argument("--attempt-dir", required=True, type=Path)
    status.add_argument("--stream", help="stdout or stderr; omit for facts and sizes only")
    status.add_argument("--offset", type=int, default=0)
    status.add_argument("--max-bytes", type=int, default=DEFAULT_WINDOW_BYTES)
    return parser


def main(argv: list[str] | None = None) -> int:
    refused = refuse_windows()
    if refused is not None:
        return refused
    args = build_parser().parse_args(argv)
    if args.command == "status":
        return status_command(args.attempt_dir, args.stream, args.offset, args.max_bytes)
    options = RunOptions(
        backend=args.backend,
        worktree=args.worktree,
        brief=args.brief,
        attempt_dir=args.attempt_dir,
        effort=args.effort,
        model=args.model,
        resume_id=args.resume_id,
        sandbox_profile=args.sandbox_profile,
        timeout=args.timeout,
        idle_timeout=args.idle_timeout,
    )
    return run_worker(options)


if __name__ == "__main__":
    raise SystemExit(main())
