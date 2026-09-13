"""Launch one sddx worker attempt and preserve the evidence it will be judged on.

This is not an orchestrator. It has no scheduler, no retry, no backend failover,
no provider-event parsing, and no process-tree management. It never decides
whether a task succeeded: a process exit of 0 is not task completion, and the
files written here prove only what was handed to the CLI, never that OS
isolation held or that the model obeyed its instructions.

The controller prepares the Grok sandbox profile before calling this runner and
cleans it up afterwards, once it has confirmed the worker and anything it
started have exited. The runner neither prepares nor cleans up, and it does not
guarantee process-tree exit.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from resolve_backend import ALIASES, _subprocess_args, resolve  # noqa: E402

# Resolved against this script, never against the caller's working directory.
WORKER_RULES_PATH = SCRIPT_DIR.parent / "references" / "worker-prompt.md"

SCHEMA_VERSION = 1
EVIDENCE_DIR_NAME = ".superpowers"
BRIEF_NAME = "brief.md"
DISPATCH_NAME = "dispatch.md"
STDOUT_NAME = "worker.jsonl"
STDERR_NAME = "stderr.log"
METADATA_NAME = "run.json"
REPORT_NAME = "report.md"

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


def utc_now() -> str:
    """A timezone-aware UTC timestamp, so attempts stay comparable across hosts."""
    return datetime.now(timezone.utc).isoformat()


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


def _validated_backend(options: RunOptions) -> str:
    """Reject backend/option combinations the resolver contract cannot express."""
    if options.backend not in ALIASES:
        raise ValueError(f"unknown backend: {options.backend}")
    backend = ALIASES[options.backend]
    if not options.effort:
        raise ValueError("effort must be a non-empty value")
    if backend == "grok":
        if not options.sandbox_profile:
            raise ValueError("grok requires a prepared sandbox profile")
        if options.model is not None:
            raise ValueError("grok selects its own model; --model is not accepted")
    else:
        if options.sandbox_profile is not None:
            raise ValueError("cursor uses its own sandbox mode; --sandbox-profile is not accepted")
        if not options.model:
            raise ValueError("cursor requires an explicit confirmed model id")
    if options.resume_id is not None and not options.resume_id:
        raise ValueError("resume id must be a known non-empty session id")
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
    else:
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


def run_worker(options: RunOptions) -> int:
    """Run one attempt and return the wrapper exit for it.

    A normally awaited worker's exit is returned as-is; a POSIX signal death
    becomes `128 + signal` while `run.json` keeps the real negative returncode.
    A launch failure is 2 and a controller interrupt handled here is 130.
    """
    try:
        worktree, attempt_dir = _validated_attempt_dir(options.worktree, options.attempt_dir)
        backend = _validated_backend(options)
        brief_bytes = options.brief.read_bytes()
        rules = _worker_rules()
        attempt_dir.mkdir()
        (attempt_dir / BRIEF_NAME).write_bytes(brief_bytes)
    except (OSError, ValueError) as error:
        return _blocked(str(error))

    metadata_path = attempt_dir / METADATA_NAME
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "backend": backend,
        "identity": None,
        "model": None,
        "worktree": str(worktree),
        "attempt_dir": str(attempt_dir),
        "brief_sha256": hashlib.sha256(brief_bytes).hexdigest(),
        "resume_id": options.resume_id,
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

    resolved = resolve(backend)
    if not resolved["available"]:
        return fail(f"{backend} backend is unavailable: {resolved['reason']}")
    if backend != "grok" and options.model not in resolved["model_ids"]:
        return fail("model is not one of the backend's confirmed model ids")

    metadata["identity"] = resolved["identity"]
    if backend != "grok":
        # Recorded because it was named on the command line, not because the
        # model was proven to apply it.
        metadata["model"] = options.model
    if resolved["launch"]["effort_flag"] is not None:
        metadata["configured_effort"] = options.effort

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
    try:
        command = _subprocess_args(argv[0], argv[1:])
    except ValueError:
        # The transport rejected an argument. Its own message quotes the whole
        # argument, which can be the rules or the dispatch, so it is not kept.
        return fail("an argument cannot cross the backend command transport")

    stdout_path = attempt_dir / STDOUT_NAME
    stderr_path = attempt_dir / STDERR_NAME
    with contextlib.ExitStack() as stack:
        try:
            out = stack.enter_context(stdout_path.open("xb"))
            err = stack.enter_context(stderr_path.open("xb"))
        except OSError:
            return fail("could not create the raw worker output files")
        try:
            # No custom `env`: the transport's `%NAME%` guard reads `os.environ`,
            # which is exactly what the child inherits.
            process = subprocess.Popen(
                command,
                cwd=str(worktree),
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
            )
        except OSError as error:
            return fail(f"could not start the backend process: {error.strerror or 'OSError'}")

        metadata.update(state="running", pid=process.pid)
        write_metadata(metadata_path, metadata)
        try:
            code = process.wait()
        except KeyboardInterrupt:
            # Record only the exit actually recovered. The process tree is left
            # alone and Grok cleanup stays the controller's call.
            metadata.update(
                state="interrupted",
                exit_code=process.poll(),
                ended_at=utc_now(),
                error="the controller interrupted the attempt",
            )
            write_metadata(metadata_path, metadata)
            return 130
        metadata.update(state="exited", exit_code=code, ended_at=utc_now())
        write_metadata(metadata_path, metadata)
    return code if code >= 0 else 128 - code


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
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    options = RunOptions(
        backend=args.backend,
        worktree=args.worktree,
        brief=args.brief,
        attempt_dir=args.attempt_dir,
        effort=args.effort,
        model=args.model,
        resume_id=args.resume_id,
        sandbox_profile=args.sandbox_profile,
    )
    return run_worker(options)


if __name__ == "__main__":
    raise SystemExit(main())
