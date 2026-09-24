"""Synthetic coverage for the read-only sddx worker status query.

Every attempt directory here is written by the test itself. No worker is ever
launched, no provider CLI is invoked, and no account or network is touched. The
logs are synthetic bytes chosen to exercise UTF-8 boundaries and Cursor-shaped
`tool_call` objects and Grok-shaped `tool_use`/`tool_result` items; nothing in
them is a real provider transcript. Window tests
assert raw byte positions only. The default payload may copy a bounded tools
index of paths, search patterns, and shell commands, but never log bodies,
result `content`/`stdout`/`stderr`, or thinking text.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS = ROOT / "skills" / "sddx" / "scripts"

DEFAULT_KEYS = {
    "attempt_dir",
    "metadata",
    "session_id",
    "pid_alive",
    "tools",
    "stdout_bytes",
    "stderr_bytes",
    "report_exists",
    "stale",
    "session_id_in_log",
}
WINDOW_KEYS = {
    "stream",
    "offset",
    "next_offset",
    "size",
    "preview",
    "has_more",
    "decode_errors",
    "pending_bytes",
}

HANGUL = "한".encode("utf-8")


class StatusFixture(unittest.TestCase):
    """A temporary attempt directory and a freshly imported runner module."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        # Resolved once, so an echoed absolute path compares equal on hosts where
        # the temporary directory is itself a symbolic link.
        self.base = Path(self.tmpdir.name).resolve()
        self.attempt = self.base / "attempt-1"
        self.attempt.mkdir()
        sys.path.insert(0, str(SCRIPTS))
        self.addCleanup(self._drop_scripts_path)

    @staticmethod
    def _drop_scripts_path() -> None:
        while str(SCRIPTS) in sys.path:
            sys.path.remove(str(SCRIPTS))

    def load(self):
        for name in ("run_worker", "resolve_backend"):
            sys.modules.pop(name, None)
        return importlib.import_module("run_worker")

    def write_metadata(self, **overrides) -> dict[str, object]:
        value: dict[str, object] = {
            "schema_version": 2,
            "backend": "grok",
            "identity": "grok 1.0.25",
            "model": None,
            "session_id": None,
            "worktree": str(self.base / "worktree"),
            "attempt_dir": str(self.attempt),
            "brief_sha256": "0" * 64,
            "resume_id": None,
            "requested_effort": "high",
            "configured_effort": "high",
            "state": "running",
            "pid": 4242,
            "exit_code": None,
            "started_at": "2026-09-13T00:00:00+00:00",
            "ended_at": None,
            "error": None,
        }
        value.update(overrides)
        (self.attempt / "run.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return value

    def write_stdout(self, data: bytes) -> Path:
        path = self.attempt / "worker.jsonl"
        path.write_bytes(data)
        return path

    def write_stderr(self, data: bytes) -> Path:
        path = self.attempt / "stderr.log"
        path.write_bytes(data)
        return path

    def snapshot(self) -> dict[str, tuple[bytes, int, int]]:
        """Bytes, size and modification time of every file below the attempt.

        `st_atime_ns` is deliberately excluded: reading a file legitimately
        changes it on many hosts, and including it would make this a flaky test
        rather than a read-only proof.
        """
        entries: dict[str, tuple[bytes, int, int]] = {}
        for path in sorted(self.attempt.rglob("*")):
            if path.is_file():
                stat = path.stat()
                entries[str(path.relative_to(self.attempt))] = (
                    path.read_bytes(),
                    stat.st_mtime_ns,
                    stat.st_size,
                )
        return entries

    @contextlib.contextmanager
    def no_subprocess(self, module):
        """Any attempt to execute something during a status query fails loudly."""
        failure = AssertionError("status must never execute anything")
        with mock.patch.object(module.subprocess, "Popen", side_effect=failure):
            with mock.patch.object(module.subprocess, "run", side_effect=failure):
                yield

    def cli(self, module, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = module.main(argv)
        return code, out.getvalue(), err.getvalue()


class DefaultStatusTests(StatusFixture):
    """The default query reports facts and sizes, never the log body."""

    def test_default_status_never_carries_the_log_body(self) -> None:
        module = self.load()
        line = json.dumps({"type": "assistant", "text": "z" * (1024 * 1024)}) + "\n"
        body = line.encode("utf-8")
        self.write_stdout(body)
        self.write_stderr(b"warming up\n")
        self.write_metadata()

        payload = module.read_status(self.attempt)

        self.assertEqual(set(payload), DEFAULT_KEYS)
        self.assertEqual(payload["stdout_bytes"], len(body))
        self.assertEqual(payload["stderr_bytes"], len(b"warming up\n"))
        self.assertIs(payload["report_exists"], False)
        self.assertEqual(payload["attempt_dir"], str(self.attempt))
        self.assertEqual(payload["metadata"]["backend"], "grok")
        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn("z" * 64, rendered)
        self.assertLess(len(rendered), 4096)

    def test_relative_attempt_directory_is_resolved(self) -> None:
        module = self.load()
        self.write_metadata()
        self.write_stdout(b"")
        origin = os.getcwd()
        self.addCleanup(os.chdir, origin)
        os.chdir(self.base)
        payload = module.read_status(Path(self.attempt.name))
        self.assertEqual(payload["attempt_dir"], str(self.attempt))

    def test_absent_logs_report_zero_bytes(self) -> None:
        module = self.load()
        self.write_metadata()
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["stdout_bytes"], 0)
        self.assertEqual(payload["stderr_bytes"], 0)

    def test_report_without_an_exit_code_is_not_completion(self) -> None:
        module = self.load()
        self.write_metadata(state="running", exit_code=None)
        (self.attempt / "report.md").write_text("DONE\n", encoding="utf-8")
        self.write_stdout(b'{"type": "result", "text": "DONE"}\n')

        payload = module.read_status(self.attempt)

        self.assertEqual(set(payload), DEFAULT_KEYS)
        self.assertIs(payload["report_exists"], True)
        self.assertIsNone(payload["metadata"]["exit_code"])
        self.assertEqual(payload["metadata"]["state"], "running")

    def test_pid_alive_is_true_for_this_process(self) -> None:
        # Break: status omits pid_alive or reports the current pid as dead.
        module = self.load()
        self.write_metadata(pid=os.getpid())
        payload = module.read_status(self.attempt)
        self.assertIs(payload["pid_alive"], True)

    def test_pid_alive_is_false_when_the_process_is_gone(self) -> None:
        # Break: a missing pid is reported as alive or omitted.
        module = self.load()
        self.write_metadata(pid=2**22)
        payload = module.read_status(self.attempt)
        self.assertIs(payload["pid_alive"], False)

    def test_pid_alive_is_null_when_the_record_has_no_pid(self) -> None:
        # Break: a launch-style record is reported as a boolean.
        module = self.load()
        self.write_metadata(pid=None)
        payload = module.read_status(self.attempt)
        self.assertIsNone(payload["pid_alive"])

    def test_status_does_not_rewrite_a_stale_running_record(self) -> None:
        # Break: status "heals" run.json into interrupted.
        module = self.load()
        before = self.write_metadata(state="running", pid=2**22, session_id=None)
        snapshot = (self.attempt / "run.json").read_bytes()
        payload = module.read_status(self.attempt)
        self.assertIs(payload["pid_alive"], False)
        self.assertEqual((self.attempt / "run.json").read_bytes(), snapshot)
        self.assertEqual(payload["metadata"]["state"], "running")

    def test_tools_index_copies_cursor_read_grep_and_shell_fields(self) -> None:
        # Break: status has no tools index, or looks inside result bodies.
        module = self.load()
        self.write_metadata()
        secret = "SYNTHETIC_PLAN_BODY_SHOULD_NOT_LEAK"
        events = [
            {"type": "thinking", "subtype": "delta", "text": secret},
            {
                "type": "tool_call",
                "subtype": "started",
                "tool_call": {
                    "readToolCall": {"args": {"path": "/work/brief.md"}},
                },
            },
            {
                "type": "tool_call",
                "subtype": "completed",
                "tool_call": {
                    "readToolCall": {
                        "args": {"path": "/work/brief.md"},
                        "result": {"success": {"content": secret}},
                    },
                },
            },
            {
                "type": "tool_call",
                "subtype": "started",
                "tool_call": {
                    "grepToolCall": {
                        "args": {"pattern": "def gate\\(", "path": "/work/src.py"},
                    },
                },
            },
            {
                "type": "tool_call",
                "subtype": "completed",
                "tool_call": {
                    "shellToolCall": {
                        "args": {"command": "python3 -m unittest"},
                        "result": {"failure": {"exitCode": 1, "stderr": secret}},
                    },
                },
            },
            {
                "type": "tool_call",
                "subtype": "completed",
                "tool_call": {
                    "shellToolCall": {
                        "args": {"command": "python3 -m unittest discover -s tests"},
                        "result": {"success": {"exitCode": 0, "stdout": secret}},
                    },
                },
            },
        ]
        self.write_stdout(("\n".join(json.dumps(item) for item in events) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["tools"]["reads"], ["/work/brief.md"])
        self.assertEqual(
            payload["tools"]["searches"],
            [{"pattern": "def gate\\(", "path": "/work/src.py"}],
        )
        self.assertEqual(
            payload["tools"]["shells"],
            [
                {"exit_code": 1, "command": "python3 -m unittest"},
                {"exit_code": 0, "command": "python3 -m unittest discover -s tests"},
            ],
        )
        self.assertIs(payload["tools"]["truncated"], False)
        rendered = json.dumps(payload, ensure_ascii=False)
        self.assertNotIn(secret, rendered)

    def test_unknown_tool_shapes_are_an_empty_index_not_an_error(self) -> None:
        # Break: a non-Cursor event or a broken line fails the query.
        module = self.load()
        self.write_metadata()
        self.write_stdout(
            b"not json\n"
            + json.dumps({"type": "tool_call", "subtype": "started", "tool_call": {"fn": {"args": {"path": "/x"}}}}).encode()
            + b"\n"
        )
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["tools"], {
            "reads": [],
            "searches": [],
            "shells": [],
            "truncated": False,
        })

    def test_a_recursive_json_line_is_skipped_not_a_query_failure(self) -> None:
        # Break: RecursionError from json.loads fails the whole status query.
        # A nested JSON blob is not a portable fixture: CPython 3.14's decoder
        # is iterative, while 3.11 still RecursionErrors. Inject the same
        # exception json.loads raises on a pathological line.
        module = self.load()
        self.write_metadata()
        good = json.dumps({
            "type": "tool_call",
            "subtype": "started",
            "tool_call": {"readToolCall": {"args": {"path": "/work/ok.py"}}},
        })
        self.write_stdout(b'{"pathological":true}\n' + (good + "\n").encode("utf-8"))
        real_loads = module.json.loads

        def loads(raw, *args, **kwargs):
            text = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            if "pathological" in text:
                raise RecursionError
            return real_loads(raw, *args, **kwargs)

        try:
            with mock.patch.object(module.json, "loads", loads):
                payload = module.read_status(self.attempt)
        except RecursionError:
            self.fail("status must skip a RecursionError line, not fail the query")

        self.assertEqual(payload["tools"]["reads"], ["/work/ok.py"])
        self.assertIs(payload["tools"]["truncated"], False)

    def test_tools_index_truncates_instead_of_growing_without_bound(self) -> None:
        # Break: every path is returned, or truncated stays false.
        module = self.load()
        self.write_metadata()
        lines = []
        for index in range(70):
            lines.append(json.dumps({
                "type": "tool_call",
                "subtype": "started",
                "tool_call": {
                    "readToolCall": {"args": {"path": f"/work/file-{index}.py"}},
                },
            }))
        self.write_stdout(("\n".join(lines) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(len(payload["tools"]["reads"]), 64)
        self.assertEqual(payload["tools"]["reads"][0], "/work/file-0.py")
        self.assertEqual(payload["tools"]["reads"][-1], "/work/file-63.py")
        self.assertIs(payload["tools"]["truncated"], True)

    def test_glob_search_uses_globPattern_and_targetDirectory(self) -> None:
        module = self.load()
        self.write_metadata()
        self.write_stdout((json.dumps({
            "type": "tool_call",
            "subtype": "started",
            "tool_call": {
                "globToolCall": {
                    "args": {
                        "globPattern": "tests/*.py",
                        "targetDirectory": "/work",
                    },
                },
            },
        }) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(
            payload["tools"]["searches"],
            [{"pattern": "tests/*.py", "path": "/work"}],
        )

    def grok_line(self, role: str, items: list[dict]) -> str:
        return json.dumps({"type": role, "message": {"role": role, "content": items}})

    def test_grok_tools_index_copies_reads_searches_and_shells(self) -> None:
        # Break: Grok logs index as empty, a grep result's exit_code becomes a
        # shell, or a result body leaks into status.
        module = self.load()
        self.write_metadata()
        secret = "SYNTHETIC_GROK_BODY_SHOULD_NOT_LEAK"
        lines = [
            json.dumps({"type": "system", "subtype": "init", "session_id": "synthetic-grok"}),
            self.grok_line("assistant", [
                {"type": "text", "text": secret},
                {"type": "tool_use", "id": "t1", "name": "read_file", "input": {"target_file": "/work/brief.md"}},
                {"type": "tool_use", "id": "t1b", "name": "read_file", "input": {"target_file": "/work/brief.md"}},
                {"type": "tool_use", "id": "t2", "name": "grep", "input": {"pattern": "def gate\\(", "path": "/work/src"}},
                {"type": "tool_use", "id": "t3", "name": "list_dir", "input": {"target_directory": "/work"}},
                {"type": "tool_use", "id": "t4", "name": "run_terminal_command", "input": {"command": "python3 -m unittest", "description": "tests"}},
                {"type": "tool_use", "id": "t5", "name": "run_terminal_command", "input": {"command": "pnpm e2e", "description": "background"}},
                {"type": "tool_use", "id": "t6", "name": "search_replace", "input": {"file_path": "/work/a.py", "old_string": secret, "new_string": secret}},
            ]),
            self.grok_line("user", [
                {"type": "tool_result", "tool_use_id": "t1", "is_error": False, "content": json.dumps({"type": "FileContent", "content": secret})},
                {"type": "tool_result", "tool_use_id": "t2", "is_error": False, "content": json.dumps({"type": "Grep", "stdout": secret, "exit_code": 0})},
                {"type": "tool_result", "tool_use_id": "t4", "is_error": False, "content": json.dumps({"type": "Shell", "output": secret, "exit_code": 1})},
                {"type": "tool_result", "tool_use_id": "t5", "is_error": False, "content": json.dumps({"type": "BackgroundTaskStarted", "task_id": "b1", "status": "running"})},
            ]),
        ]
        self.write_stdout(("\n".join(lines) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["tools"]["reads"], ["/work/brief.md"])
        self.assertEqual(
            payload["tools"]["searches"],
            [
                {"pattern": "def gate\\(", "path": "/work/src"},
                {"pattern": None, "path": "/work"},
            ],
        )
        self.assertEqual(
            payload["tools"]["shells"],
            [
                {"exit_code": 1, "command": "python3 -m unittest"},
                {"exit_code": None, "command": "pnpm e2e"},
            ],
        )
        self.assertIs(payload["tools"]["truncated"], False)
        self.assertNotIn(secret, json.dumps(payload, ensure_ascii=False))

    def test_grok_results_in_odd_shapes_never_fail_status(self) -> None:
        # Break: a list-shaped, non-JSON, or unhashable-id result fails the query.
        module = self.load()
        self.write_metadata()
        lines = [
            self.grok_line("assistant", [
                {"type": "tool_use", "id": "s1", "name": "run_terminal_command", "input": {"command": "true"}},
                {"type": "tool_use", "id": "s2", "name": "run_terminal_command", "input": {"command": "false"}},
                {"type": "tool_use", "id": "s3", "name": "run_terminal_command", "input": {"command": 7}},
                {"type": "tool_use", "id": "s4", "name": "read_file", "input": "not a dict"},
            ]),
            self.grok_line("user", [
                {"type": "tool_result", "tool_use_id": "s1", "content": [{"type": "text", "text": json.dumps({"exit_code": 0})}]},
                {"type": "tool_result", "tool_use_id": "s2", "content": "not json"},
                {"type": "tool_result", "tool_use_id": {"odd": 1}, "content": "{}"},
                {"type": "tool_result", "tool_use_id": "s3", "content": json.dumps({"exit_code": True})},
            ]),
            json.dumps({"type": "assistant", "message": "plain text"}),
            json.dumps({"type": "user", "message": {"content": "plain text"}}),
        ]
        self.write_stdout(("\n".join(lines) + "\n").encode("utf-8"))
        payload = module.read_status(self.attempt)
        self.assertEqual(
            payload["tools"]["shells"],
            [
                {"exit_code": 0, "command": "true"},
                {"exit_code": None, "command": "false"},
                {"exit_code": None, "command": ""},
            ],
        )
        self.assertEqual(payload["tools"]["reads"], [])

    def test_grok_shells_share_the_cap_and_truncate(self) -> None:
        module = self.load()
        self.write_metadata()
        items = [
            {"type": "tool_use", "id": f"s{n}", "name": "run_terminal_command", "input": {"command": "x" * 300}}
            for n in range(33)
        ]
        self.write_stdout((self.grok_line("assistant", items) + "\n").encode("utf-8"))
        tools = module.read_status(self.attempt)["tools"]
        self.assertEqual(len(tools["shells"]), 32)
        self.assertEqual(len(tools["shells"][0]["command"]), 200)
        self.assertIs(tools["truncated"], True)


class MetadataTests(StatusFixture):
    """Metadata is reported honestly or not at all."""

    def test_absent_metadata_still_reports_the_raw_evidence(self) -> None:
        module = self.load()
        self.write_stdout(b"partial output\n")
        self.write_stderr(b"")

        payload = module.read_status(self.attempt)

        self.assertIsNone(payload["metadata"])
        self.assertEqual(payload["stdout_bytes"], len(b"partial output\n"))
        self.assertEqual(payload["stderr_bytes"], 0)
        self.assertIs(payload["report_exists"], False)

    def test_unparseable_metadata_is_an_error(self) -> None:
        module = self.load()
        (self.attempt / "run.json").write_text('{"schema_version": 1', encoding="utf-8")
        with self.assertRaises(ValueError):
            module.read_status(self.attempt)

    def test_metadata_that_is_not_an_object_is_an_error(self) -> None:
        module = self.load()
        (self.attempt / "run.json").write_text("[1, 2, 3]", encoding="utf-8")
        with self.assertRaises(ValueError):
            module.read_status(self.attempt)

    def test_schema_two_without_skill_version_is_still_readable(self) -> None:
        # Break: status starts requiring skill_version and cannot read older attempts.
        module = self.load()
        recorded = self.write_metadata()
        self.assertNotIn("skill_version", recorded)
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["metadata"], recorded)

    def test_unknown_metadata_schema_version_is_an_error(self) -> None:
        module = self.load()
        # Both directions: a superseded record is as unreadable as a future one,
        # because its fields are not the ones this reader reports.
        for version in (1, 3):
            with self.subTest(schema_version=version):
                self.write_metadata(schema_version=version)
                with self.assertRaises(ValueError):
                    module.read_status(self.attempt)

    def test_status_reports_the_recorded_worker_session(self) -> None:
        module = self.load()
        # Invented here; the controller reads it instead of opening the raw log.
        self.write_metadata(session_id="synthetic-session-0009")
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["session_id"], "synthetic-session-0009")
        self.assertEqual(json.loads(module.render_status(payload))["session_id"],
                         "synthetic-session-0009")

    def test_an_unreported_session_is_null_rather_than_absent(self) -> None:
        module = self.load()
        self.write_metadata(session_id=None)
        self.assertIsNone(module.read_status(self.attempt)["session_id"])

    def test_status_without_metadata_reports_no_session(self) -> None:
        module = self.load()
        self.write_stdout(b'{"session_id": "synthetic-unrecorded"}\n')
        payload = module.read_status(self.attempt)
        self.assertIsNone(payload["metadata"])
        # `status` reports the record, never an opinion about the log body.
        self.assertIsNone(payload["session_id"])

    def test_absent_attempt_directory_is_an_error(self) -> None:
        module = self.load()
        with self.assertRaises(ValueError):
            module.read_status(self.base / "no-such-attempt")


class WindowTests(StatusFixture):
    """The byte window advances only over what it actually decoded."""

    def test_window_advances_only_by_what_it_consumed(self) -> None:
        module = self.load()
        line = json.dumps({"type": "assistant", "text": "가" * 300_000}) + "\n"
        body = line.encode("utf-8")
        self.assertGreater(len(body), 1024 * 1024)
        self.write_stdout(body)
        self.write_metadata()

        first = module.read_status(self.attempt, stream="stdout", offset=0, max_bytes=2048)
        self.assertEqual(set(first), DEFAULT_KEYS | WINDOW_KEYS)
        self.assertEqual(first["stream"], "stdout")
        self.assertEqual(first["offset"], 0)
        self.assertLess(0, first["next_offset"])
        self.assertLessEqual(first["next_offset"], 2048)
        self.assertIs(first["has_more"], True)
        self.assertIs(first["decode_errors"], False)
        self.assertEqual(first["size"], len(body))
        self.assertEqual(
            first["preview"].encode("utf-8"), body[first["offset"]:first["next_offset"]]
        )

        second = module.read_status(
            self.attempt, stream="stdout", offset=first["next_offset"], max_bytes=2048
        )
        self.assertEqual(second["offset"], first["next_offset"])
        self.assertGreater(second["next_offset"], second["offset"])
        self.assertEqual(
            second["preview"].encode("utf-8"), body[second["offset"]:second["next_offset"]]
        )

    def test_growing_file_leaves_a_partial_character_for_the_next_window(self) -> None:
        module = self.load()
        self.write_metadata()
        log = self.write_stdout(HANGUL[:2])

        first = module.read_status(self.attempt, stream="stdout", max_bytes=2048)
        self.assertEqual(
            (first["preview"], first["next_offset"], first["pending_bytes"]), ("", 0, 2)
        )
        self.assertIs(first["has_more"], True)
        self.assertIs(first["decode_errors"], False)
        self.assertEqual(first["size"], 2)

        with log.open("ab") as out:
            out.write(HANGUL[2:])

        second = module.read_status(self.attempt, stream="stdout", offset=first["next_offset"])
        self.assertEqual(
            (second["preview"], second["next_offset"], second["pending_bytes"]), ("한", 3, 0)
        )
        self.assertIs(second["has_more"], False)
        self.assertIs(second["decode_errors"], False)

    def test_temporary_eof_with_one_lead_byte_waits_instead_of_failing(self) -> None:
        module = self.load()
        self.write_stdout(HANGUL[:1])
        window = module.read_status(self.attempt, stream="stdout", max_bytes=1)
        self.assertEqual(window["preview"], "")
        self.assertEqual(window["next_offset"], 0)
        self.assertEqual(window["pending_bytes"], 1)
        self.assertEqual(window["size"], 1)
        self.assertIs(window["has_more"], True)
        self.assertIs(window["decode_errors"], False)

    def test_complete_character_with_too_small_a_window_is_an_input_error(self) -> None:
        module = self.load()
        self.write_stdout(HANGUL)
        with self.assertRaises(ValueError):
            module.read_status(self.attempt, stream="stdout", max_bytes=1)
        with self.assertRaises(ValueError):
            module.read_status(self.attempt, stream="stdout", max_bytes=2)
        whole = module.read_status(self.attempt, stream="stdout", max_bytes=3)
        self.assertEqual(whole["preview"], "한")

    def test_character_straddling_the_window_boundary_mid_file(self) -> None:
        module = self.load()
        body = b"a" * 10 + HANGUL + b"b" * 10
        self.write_stdout(body)

        first = module.read_status(self.attempt, stream="stdout", offset=0, max_bytes=11)
        self.assertEqual(first["preview"], "a" * 10)
        self.assertEqual(first["next_offset"], 10)
        self.assertEqual(first["pending_bytes"], 1)
        self.assertIs(first["has_more"], True)
        self.assertIs(first["decode_errors"], False)

        second = module.read_status(self.attempt, stream="stdout", offset=10, max_bytes=2048)
        self.assertEqual(second["preview"], "한" + "b" * 10)
        self.assertEqual(second["next_offset"], len(body))
        self.assertEqual(second["pending_bytes"], 0)
        self.assertIs(second["has_more"], False)

    def test_invalid_bytes_are_flagged_consumed_and_left_on_disk(self) -> None:
        module = self.load()
        body = b"ok\xff\xfe done\n"
        log = self.write_stdout(body)

        window = module.read_status(self.attempt, stream="stdout", max_bytes=2048)

        self.assertIs(window["decode_errors"], True)
        self.assertEqual(window["next_offset"], len(body))
        self.assertEqual(window["pending_bytes"], 0)
        self.assertIn("�", window["preview"])
        self.assertIs(window["has_more"], False)
        self.assertEqual(log.read_bytes(), body)

    def test_offset_equal_to_size_is_an_empty_window(self) -> None:
        module = self.load()
        body = b"done\n"
        self.write_stdout(body)
        window = module.read_status(self.attempt, stream="stdout", offset=len(body))
        self.assertEqual(window["preview"], "")
        self.assertEqual(window["next_offset"], len(body))
        self.assertEqual(window["pending_bytes"], 0)
        self.assertIs(window["has_more"], False)
        self.assertIs(window["decode_errors"], False)

    def test_empty_log_at_offset_zero_is_an_empty_window(self) -> None:
        module = self.load()
        self.write_stdout(b"")
        window = module.read_status(self.attempt, stream="stdout")
        self.assertEqual((window["preview"], window["next_offset"], window["size"]), ("", 0, 0))
        self.assertIs(window["has_more"], False)

    def test_offset_beyond_size_is_an_error(self) -> None:
        module = self.load()
        self.write_stdout(b"done\n")
        with self.assertRaises(ValueError):
            module.read_status(self.attempt, stream="stdout", offset=6)

    def test_negative_offset_is_an_error(self) -> None:
        module = self.load()
        self.write_stdout(b"done\n")
        with self.assertRaises(ValueError):
            module.read_status(self.attempt, stream="stdout", offset=-1)

    def test_max_bytes_outside_the_allowed_range_is_an_error(self) -> None:
        module = self.load()
        self.write_stdout(b"done\n")
        for value in (0, -1, 8193):
            with self.subTest(max_bytes=value):
                with self.assertRaises(ValueError):
                    module.read_status(self.attempt, stream="stdout", max_bytes=value)
        edge = module.read_status(self.attempt, stream="stdout", max_bytes=8192)
        self.assertEqual(edge["preview"], "done\n")

    def test_unknown_stream_name_is_an_error(self) -> None:
        module = self.load()
        self.write_stdout(b"done\n")
        for name in ("out", "worker.jsonl", "", "STDOUT"):
            with self.subTest(stream=name):
                with self.assertRaises(ValueError):
                    module.read_status(self.attempt, stream=name)

    def test_stream_against_an_absent_log_is_an_error(self) -> None:
        module = self.load()
        self.write_metadata()
        with self.assertRaises((OSError, ValueError)):
            module.read_status(self.attempt, stream="stdout")
        with self.assertRaises((OSError, ValueError)):
            module.read_status(self.attempt, stream="stderr")

    def test_stderr_stream_reads_the_stderr_log(self) -> None:
        module = self.load()
        self.write_stdout(b'{"type": "assistant"}\n')
        self.write_stderr(b"HTTP 402 Payment Required\n")

        window = module.read_status(self.attempt, stream="stderr", max_bytes=2048)

        self.assertEqual(window["stream"], "stderr")
        self.assertEqual(window["preview"], "HTTP 402 Payment Required\n")
        self.assertEqual(window["stderr_bytes"], window["size"])
        self.assertEqual(window["stdout_bytes"], len(b'{"type": "assistant"}\n'))

    def test_non_json_lines_are_returned_as_raw_text(self) -> None:
        module = self.load()
        body = "not json at all\n{\"half\": \n plain prose\n".encode("utf-8")
        self.write_stdout(body)

        window = module.read_status(self.attempt, stream="stdout", max_bytes=2048)

        self.assertEqual(window["preview"], body.decode("utf-8"))
        self.assertIs(window["decode_errors"], False)
        self.assertEqual(window["next_offset"], len(body))


class ReadOnlyTests(StatusFixture):
    """A query changes nothing and executes nothing, however often it is repeated."""

    def test_repeated_status_is_identical_and_touches_nothing(self) -> None:
        module = self.load()
        self.write_metadata()
        self.write_stdout(b'{"type": "assistant", "text": "hello"}\n' + HANGUL[:2])
        self.write_stderr(b"warning\n")
        (self.attempt / "report.md").write_text("# report\n", encoding="utf-8")
        before = self.snapshot()

        with self.no_subprocess(module):
            first = module.read_status(self.attempt)
            second = module.read_status(self.attempt)
            window_one = module.read_status(self.attempt, stream="stdout", max_bytes=2048)
            window_two = module.read_status(self.attempt, stream="stdout", max_bytes=2048)

        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(
            json.dumps(window_one, sort_keys=True), json.dumps(window_two, sort_keys=True)
        )
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(
            {path.name for path in self.attempt.iterdir()},
            {"run.json", "worker.jsonl", "stderr.log", "report.md"},
        )


class StatusCommandTests(StatusFixture):
    """The CLI prints one JSON document and maps every input error to exit 2."""

    def test_default_command_prints_the_status_payload(self) -> None:
        module = self.load()
        self.write_metadata()
        self.write_stdout(b"hello\n")

        code, out, err = self.cli(module, ["status", "--attempt-dir", str(self.attempt)])

        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(set(payload), DEFAULT_KEYS)
        self.assertEqual(payload["stdout_bytes"], 6)

    def test_window_command_prints_the_window_payload(self) -> None:
        module = self.load()
        self.write_metadata()
        self.write_stdout("한글 로그\n".encode("utf-8"))

        code, out, _ = self.cli(
            module,
            [
                "status",
                "--attempt-dir",
                str(self.attempt),
                "--stream",
                "stdout",
                "--offset",
                "0",
                "--max-bytes",
                "2048",
            ],
        )

        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertEqual(payload["preview"], "한글 로그\n")
        self.assertEqual(payload["stream"], "stdout")

    def test_invalid_input_exits_two_without_a_payload(self) -> None:
        module = self.load()
        self.write_stdout(b"hello\n")
        cases = [
            ["status", "--attempt-dir", str(self.attempt), "--stream", "both"],
            ["status", "--attempt-dir", str(self.attempt), "--stream", "stdout", "--offset", "-1"],
            [
                "status",
                "--attempt-dir",
                str(self.attempt),
                "--stream",
                "stdout",
                "--max-bytes",
                "8193",
            ],
            ["status", "--attempt-dir", str(self.base / "no-such-attempt")],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                code, out, err = self.cli(module, argv)
                self.assertEqual(code, 2)
                self.assertEqual(out, "")
                self.assertTrue(err.startswith("BLOCKED:"))

    def test_a_full_sized_window_stays_within_the_response_limit(self) -> None:
        # The cap must sit above a legitimate maximum window: a threshold scaled
        # wrongly would still pass every other case in this suite.
        module = self.load()
        self.write_metadata()
        body = ("l" * 79 + "\n").encode("utf-8") * 120
        self.assertGreater(len(body), 8192)
        self.write_stdout(body)

        code, out, err = self.cli(
            module,
            [
                "status",
                "--attempt-dir",
                str(self.attempt),
                "--stream",
                "stdout",
                "--max-bytes",
                "8192",
            ],
        )

        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertEqual(payload["next_offset"], 8192)
        self.assertIs(payload["has_more"], True)
        self.assertLessEqual(len(out.encode("utf-8")), 65536)

    def test_an_oversized_payload_is_an_error_not_a_silent_truncation(self) -> None:
        module = self.load()
        # A long recorded error plus a control-character window: neither alone
        # reaches the cap, and together they must not be quietly trimmed.
        self.write_metadata(state="launch_failed", error="E" * 20_000)
        self.write_stdout(b"\x01" * 8192)

        code, out, err = self.cli(
            module,
            [
                "status",
                "--attempt-dir",
                str(self.attempt),
                "--stream",
                "stdout",
                "--max-bytes",
                "8192",
            ],
        )

        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("BLOCKED:"))
        payload = module.read_status(self.attempt, stream="stdout", max_bytes=8192)
        self.assertGreater(len(json.dumps(payload, ensure_ascii=False).encode("utf-8")), 65536)

    def test_status_never_executes_anything(self) -> None:
        module = self.load()
        self.write_metadata()
        self.write_stdout(b"hello\n")
        with self.no_subprocess(module):
            code, _, _ = self.cli(module, ["status", "--attempt-dir", str(self.attempt)])
        self.assertEqual(code, 0)


class StaleAttemptTests(StatusFixture):
    """A record left at `running` by a runner that was killed before it could finish."""

    def test_running_without_a_live_pid_is_reported_stale(self) -> None:
        # The live failure: a hard-killed runner leaves `state: running` forever.
        # SKILL.md already tells a controller to treat that as stale; a controller
        # that has to remember the rule is one that can forget it.
        self.write_metadata(state="running", pid=1, exit_code=None, ended_at=None)
        module = self.load()
        with mock.patch.object(module, "pid_alive", return_value=False):
            payload = module.read_status(self.attempt)
        self.assertIs(payload["stale"], True)
        # The record itself is untouched: `status` reports, it never rewrites.
        self.assertEqual(payload["metadata"]["state"], "running")

    def test_running_with_a_live_pid_is_not_stale(self) -> None:
        self.write_metadata(state="running")
        module = self.load()
        with mock.patch.object(module, "pid_alive", return_value=True):
            payload = module.read_status(self.attempt)
        self.assertIs(payload["stale"], False)

    def test_a_terminal_state_is_never_stale(self) -> None:
        for state in ("exited", "interrupted", "timed_out", "launch_failed"):
            with self.subTest(state=state):
                self.write_metadata(state=state, exit_code=0)
                module = self.load()
                with mock.patch.object(module, "pid_alive", return_value=False):
                    payload = module.read_status(self.attempt)
                self.assertIs(payload["stale"], False)

    def test_a_missing_record_is_not_called_stale(self) -> None:
        module = self.load()
        payload = module.read_status(self.attempt)
        self.assertIsNone(payload["metadata"])
        self.assertIs(payload["stale"], False)


class SessionIdRecoveryTests(StatusFixture):
    """The session the worker reported, when the runner was killed before recording it."""

    LINE = (
        b'{"type":"system","subtype":"init","session_id":"6e310188-4ea0-4b5d-8e0e-63adf62f428a"}\n'
    )

    def test_session_id_is_recovered_from_the_log_when_the_record_has_none(self) -> None:
        # Measured on a real abandoned attempt: the ID sat at byte 111 of line 1
        # while `run.json` said null, so a resumable session was thrown away and
        # the task was re-run from scratch.
        self.write_metadata(session_id=None)
        self.write_stdout(self.LINE)
        module = self.load()
        payload = module.read_status(self.attempt)
        self.assertIsNone(payload["session_id"])
        self.assertEqual(
            payload["session_id_in_log"], "6e310188-4ea0-4b5d-8e0e-63adf62f428a"
        )

    def test_the_record_is_not_second_guessed_when_it_holds_a_session(self) -> None:
        self.write_metadata(session_id="recorded-id")
        self.write_stdout(self.LINE)
        module = self.load()
        payload = module.read_status(self.attempt)
        self.assertEqual(payload["session_id"], "recorded-id")
        self.assertIsNone(payload["session_id_in_log"])

    def test_no_log_and_no_record_recovers_nothing(self) -> None:
        self.write_metadata(session_id=None)
        module = self.load()
        payload = module.read_status(self.attempt)
        self.assertIsNone(payload["session_id"])
        self.assertIsNone(payload["session_id_in_log"])


if __name__ == "__main__":
    unittest.main()
