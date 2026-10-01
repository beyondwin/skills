#!/usr/bin/env python3
"""Report the model and effort a native subagent actually ran on.

The controller names a reviewer's model when it dispatches one, and on Codex it
names none at all, so the dispatch is not evidence of what ran. The host's own
transcript is. This reads one transcript and prints the distinct model names
and efforts on its model turns, with counts, as one JSON line:

- Claude Code: `<root>/*/<session>/subagents/agent-<id>.jsonl` for a subagent
  (the `agentId` the Agent tool returns), or `<root>/*/<session>.jsonl` for a
  main session. Model turns are `assistant` events: `message.model`, `effort`.
- Codex: `<root>/*/*/*/rollout-*-<thread>.jsonl`. Model turns are
  `turn_context` events: `payload.model`, `payload.effort`.

It is read-only, calls no provider, and prints no transcript text. A missing or
ambiguous transcript is an answer (`found: false` with a `reason`), not an error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from resolve_backend import refuse_windows  # noqa: E402

# Claude Code writes this for turns no model produced (an API error, a notice).
SYNTHETIC_MODEL = "<synthetic>"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def _checked_id(value: str) -> str:
    # The id goes into a glob, so anything but a plain token could widen it.
    if not ID_RE.match(value):
        raise ValueError("id must be letters, digits, '-' or '_'")
    return value


def candidates(host: str, root: Path, agent_id: str | None,
               session_id: str | None, thread_id: str | None) -> list[Path]:
    if host == "claude-code":
        if agent_id is not None:
            pattern = f"*/*/subagents/agent-{_checked_id(agent_id)}.jsonl"
        else:
            pattern = f"*/{_checked_id(str(session_id))}.jsonl"
    else:
        pattern = f"*/*/*/rollout-*-{_checked_id(str(thread_id))}.jsonl"
    return sorted(path for path in root.glob(pattern) if path.is_file())


def model_turns(host: str, path: Path) -> tuple[Counter, Counter]:
    models: Counter = Counter()
    efforts: Counter = Counter()
    with path.open("rb") as handle:
        for raw in handle:
            try:
                event = json.loads(raw)
            except (ValueError, RecursionError):
                continue
            if not isinstance(event, dict):
                continue
            if host == "claude-code":
                if event.get("type") != "assistant":
                    continue
                message = event.get("message")
                model = message.get("model") if isinstance(message, dict) else None
                effort = event.get("effort")
            else:
                if event.get("type") != "turn_context":
                    continue
                payload = event.get("payload")
                if not isinstance(payload, dict):
                    continue
                model = payload.get("model")
                effort = payload.get("effort")
            if not isinstance(model, str) or not model or model == SYNTHETIC_MODEL:
                continue
            models[model] += 1
            efforts[effort if isinstance(effort, str) and effort else "unknown"] += 1
    return models, efforts


def observe(host: str, root: Path, agent_id: str | None = None,
            session_id: str | None = None, thread_id: str | None = None) -> dict[str, Any]:
    found = candidates(host, root, agent_id, session_id, thread_id)
    payload: dict[str, Any] = {
        "host": host,
        "found": False,
        "source": None,
        "models": {},
        "efforts": {},
        "reason": None,
    }
    if not found:
        payload["reason"] = "not_found"
        return payload
    if len(found) > 1:
        payload["reason"] = "ambiguous"
        payload["candidates"] = [str(path) for path in found]
        return payload
    models, efforts = model_turns(host, found[0])
    payload.update(found=True, source=str(found[0]), models=dict(models), efforts=dict(efforts))
    if not models:
        payload["reason"] = "no_model_turns"
    return payload


def default_root(host: str) -> Path:
    if host == "claude-code":
        return Path.home() / ".claude" / "projects"
    return Path.home() / ".codex" / "sessions"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    hosts = parser.add_subparsers(dest="host", required=True)
    claude = hosts.add_parser("claude-code", help="a Claude Code subagent or session")
    which = claude.add_mutually_exclusive_group(required=True)
    which.add_argument("--agent-id", help="the agentId the Agent tool returned")
    which.add_argument("--session-id", help="a main session id (CLAUDE_CODE_SESSION_ID)")
    claude.add_argument("--root", type=Path, help="default: ~/.claude/projects")
    codex = hosts.add_parser("codex", help="a Codex thread")
    codex.add_argument("--thread-id", required=True, help="the thread id spawn_agent returned")
    codex.add_argument("--root", type=Path, help="default: ~/.codex/sessions")
    return parser


def main(argv: list[str] | None = None) -> int:
    refused = refuse_windows()
    if refused is not None:
        return refused
    args = build_parser().parse_args(argv)
    root = args.root if args.root is not None else default_root(args.host)
    try:
        payload = observe(
            args.host,
            root,
            agent_id=getattr(args, "agent_id", None),
            session_id=getattr(args, "session_id", None),
            thread_id=getattr(args, "thread_id", None),
        )
    except (OSError, ValueError) as error:
        print(f"BLOCKED: {error}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
