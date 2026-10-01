from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "sddx" / "scripts" / "observed_model.py"
sys.path.insert(0, str(SCRIPT.parent))
import observed_model  # noqa: E402

# Every id and model name below is invented for this file.
AGENT_ID = "a0synthetic0agent"
SESSION_ID = "00000000-synthetic-session"
THREAD_ID = "019f0000-synthetic-thread"


def write_jsonl(path: Path, *events: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join((e if isinstance(e, str) else json.dumps(e)) + "\n" for e in events),
        encoding="utf-8",
    )
    return path


def claude_turn(model: str, effort: str | None = "high") -> dict:
    event = {"type": "assistant", "message": {"role": "assistant", "model": model}}
    if effort is not None:
        event["effort"] = effort
    return event


def codex_turn(model: str, effort: str | None) -> dict:
    return {"type": "turn_context", "payload": {"model": model, "effort": effort}}


class ObservedModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.claude_root = self.base / "claude-projects"
        self.codex_root = self.base / "codex-sessions"

    def run_main(self, *argv: str) -> tuple[int, dict | None, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = observed_model.main(list(argv))
        text = out.getvalue()
        return code, (json.loads(text) if text else None), err.getvalue()

    def test_claude_code_subagent_models_and_efforts_are_counted(self) -> None:
        path = write_jsonl(
            self.claude_root / "-proj" / SESSION_ID / "subagents" / f"agent-{AGENT_ID}.jsonl",
            {"type": "user", "message": {"role": "user", "content": "review"}},
            claude_turn("claude-synthetic-a", "high"),
            claude_turn("claude-synthetic-a", "high"),
            claude_turn("<synthetic>", None),
            "not json",
            {"type": "assistant", "advisorModel": "claude-not-this-one"},
        )
        code, payload, _ = self.run_main(
            "claude-code", "--agent-id", AGENT_ID, "--root", str(self.claude_root)
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["found"], True)
        self.assertEqual(payload["source"], str(path))
        self.assertEqual(payload["models"], {"claude-synthetic-a": 2})
        self.assertEqual(payload["efforts"], {"high": 2})
        self.assertIsNone(payload["reason"])

    def test_claude_code_main_session_is_found_by_session_id(self) -> None:
        write_jsonl(
            self.claude_root / "-proj" / f"{SESSION_ID}.jsonl",
            claude_turn("claude-synthetic-b", "xhigh"),
        )
        code, payload, _ = self.run_main(
            "claude-code", "--session-id", SESSION_ID, "--root", str(self.claude_root)
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["models"], {"claude-synthetic-b": 1})
        self.assertEqual(payload["efforts"], {"xhigh": 1})

    def test_a_turn_without_effort_is_counted_as_unknown(self) -> None:
        write_jsonl(
            self.claude_root / "-proj" / SESSION_ID / "subagents" / f"agent-{AGENT_ID}.jsonl",
            claude_turn("claude-synthetic-a", None),
        )
        _, payload, _ = self.run_main(
            "claude-code", "--agent-id", AGENT_ID, "--root", str(self.claude_root)
        )
        self.assertEqual(payload["efforts"], {"unknown": 1})

    def test_codex_rollout_is_found_by_thread_id(self) -> None:
        path = write_jsonl(
            self.codex_root / "2026" / "09" / "30" / f"rollout-2026-09-30T10-00-00-{THREAD_ID}.jsonl",
            {"type": "session_meta", "payload": {"id": THREAD_ID, "model": "codex-not-this"}},
            codex_turn("gpt-synthetic", "high"),
            codex_turn("gpt-synthetic", "xhigh"),
            codex_turn("gpt-synthetic", None),
        )
        code, payload, _ = self.run_main(
            "codex", "--thread-id", THREAD_ID, "--root", str(self.codex_root)
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["source"], str(path))
        self.assertEqual(payload["models"], {"gpt-synthetic": 3})
        self.assertEqual(payload["efforts"], {"high": 1, "xhigh": 1, "unknown": 1})

    def test_missing_transcript_is_not_found_not_an_error(self) -> None:
        self.claude_root.mkdir()
        code, payload, _ = self.run_main(
            "claude-code", "--agent-id", AGENT_ID, "--root", str(self.claude_root)
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["found"], False)
        self.assertEqual(payload["reason"], "not_found")
        self.assertEqual(payload["models"], {})

    def test_two_matching_transcripts_are_ambiguous(self) -> None:
        for project in ("-one", "-two"):
            write_jsonl(
                self.claude_root / project / SESSION_ID / "subagents" / f"agent-{AGENT_ID}.jsonl",
                claude_turn("claude-synthetic-a"),
            )
        code, payload, _ = self.run_main(
            "claude-code", "--agent-id", AGENT_ID, "--root", str(self.claude_root)
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["found"], False)
        self.assertEqual(payload["reason"], "ambiguous")
        self.assertEqual(len(payload["candidates"]), 2)

    def test_a_transcript_with_no_model_turns_says_so(self) -> None:
        write_jsonl(
            self.claude_root / "-proj" / SESSION_ID / "subagents" / f"agent-{AGENT_ID}.jsonl",
            {"type": "user", "message": {"role": "user", "content": "x"}},
        )
        _, payload, _ = self.run_main(
            "claude-code", "--agent-id", AGENT_ID, "--root", str(self.claude_root)
        )
        self.assertEqual(payload["found"], True)
        self.assertEqual(payload["reason"], "no_model_turns")

    def test_ids_that_could_escape_the_root_are_refused(self) -> None:
        for bad in ("../x", "a/b", "*", "", "a?b"):
            with self.subTest(bad=bad):
                code, payload, err = self.run_main(
                    "claude-code", "--agent-id", bad, "--root", str(self.claude_root)
                )
                self.assertEqual(code, 2)
                self.assertIsNone(payload)
                self.assertIn("BLOCKED:", err)

    def test_each_host_takes_only_its_own_id(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                observed_model.main(["codex", "--agent-id", AGENT_ID])
            with self.assertRaises(SystemExit):
                observed_model.main(["claude-code", "--thread-id", THREAD_ID])
            with self.assertRaises(SystemExit):
                observed_model.main(["claude-code"])

    def test_windows_is_refused_with_the_shared_message(self) -> None:
        with mock.patch.object(os, "name", "nt"):
            code, payload, err = self.run_main("codex", "--thread-id", THREAD_ID)
        self.assertEqual(code, 2)
        self.assertIsNone(payload)
        self.assertEqual(err, "BLOCKED: Windows is not a supported OS\n")

    def test_output_carries_no_transcript_text(self) -> None:
        write_jsonl(
            self.claude_root / "-proj" / SESSION_ID / "subagents" / f"agent-{AGENT_ID}.jsonl",
            {"type": "user", "message": {"role": "user", "content": "SECRET-PROMPT-TEXT"}},
            claude_turn("claude-synthetic-a"),
        )
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "claude-code", "--agent-id", AGENT_ID,
             "--root", str(self.claude_root)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertNotIn("SECRET-PROMPT-TEXT", completed.stdout)
        self.assertEqual(completed.stdout.count("\n"), 1)
        self.assertEqual(json.loads(completed.stdout)["models"], {"claude-synthetic-a": 1})


if __name__ == "__main__":
    unittest.main()
