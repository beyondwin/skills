"""Synthetic coverage for the sddx worker runner.

Every executable these tests launch is written by the test itself onto a PATH the
test controls. No real `cursor-agent`, `cursor`, or `grok` binary is ever invoked,
no account is used, and no network call is made. The evidence asserted here proves
only what the runner handed the CLI; it says nothing about OS isolation actually
holding or about a model obeying its instructions.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS = ROOT / "skills" / "sddx" / "scripts"
WORKER_PROMPT = ROOT / "skills" / "sddx" / "references" / "worker-prompt.md"

GROK_VERSION = "grok 1.0.25 (deadbeef) [stable]\n"
GROK_HELP = """
Usage: grok [OPTIONS]
      --cwd <CWD>
      --no-plan
      --no-subagents
      --always-approve
      --reasoning-effort <EFFORT>
      --disable-web-search
      --sandbox <PROFILE>
      --rules <RULES>
      --output-format <streaming-messages-json>
  -p, --single <PROMPT>
  -r, --resume [<SESSION_ID>]
"""
GROK_HELP_WITH_PROMPT_FILE = GROK_HELP.replace(
    "  -p, --single <PROMPT>",
    "      --prompt-file <PATH>\n  -p, --single <PROMPT>",
)

CURSOR_VERSION = "cursor-agent 2026.08.07\n"
CURSOR_HELP = """
Usage: cursor-agent [options]

Commands:
  models                    Print the model identifiers this account may use

Options:
  -p, --print
  -f, --force
      --yolo
      --trust
      --auto-review
      --sandbox <mode>
      --workspace <path>
      --model <id>
      --resume <id>
      --output-format <stream-json>
"""
CURSOR_MODELS = "grok-4\ngrok-4-fast\n"

# Synthetic worker behaviours. Each one is the tail of a generated script whose
# header has already logged the argv it received.
BEHAVIOUR_EXIT_7 = (
    "sys.stdout.write(json.dumps({'type': 'assistant', 'text': 'reported success'}) + '\\n')\n"
    "sys.stderr.write('synthetic failure\\n')\n"
    "raise SystemExit(7)\n"
)
BEHAVIOUR_MALFORMED_JSON = (
    "sys.stdout.write('{\"type\": \"assistant\", \"text\": \"trunca')\n"
    "sys.stdout.write('\\nnot json at all\\n')\n"
    "raise SystemExit(0)\n"
)
BEHAVIOUR_PROVIDER_402 = (
    "sys.stdout.write('{\"type\": \"error\", \"status\": 402}\\n')\n"
    "sys.stderr.write('HTTP 402 Payment Required\\n')\n"
    "raise SystemExit(1)\n"
)
BEHAVIOUR_DELAYED = (
    "time.sleep(0.4)\n"
    "sys.stdout.write('{\"type\": \"assistant\", \"text\": \"late\"}\\n')\n"
    "raise SystemExit(0)\n"
)
BEHAVIOUR_LARGE = (
    "chunk = 'x' * 1024\n"
    "for index in range(512):\n"
    "    sys.stdout.write(chunk + '\\n')\n"
    "    sys.stderr.write(chunk + '\\n')\n"
    "raise SystemExit(0)\n"
)
BEHAVIOUR_SIGNAL = (
    "sys.stdout.flush()\n"
    "os.kill(os.getpid(), signal.SIGTERM)\n"
    "time.sleep(10)\n"
)
BEHAVIOUR_SLEEP = "time.sleep(10)\nraise SystemExit(0)\n"
BEHAVIOUR_OK = "sys.stdout.write('{\"type\": \"assistant\"}\\n')\nraise SystemExit(0)\n"

# Arguments a controller may legitimately need to hand a worker. `%SYNTHETIC_VALUE%`
# is a made-up name that must survive as literal text; none of these are secrets.
HOSTILE_ARGUMENTS = (
    "with space",
    "한글 naïve",
    'embedded "quote" here',
    "amp & pipe | lt < gt > caret ^ open ( close )",
    "%SYNTHETIC_VALUE%",
    "C:\\trailing\\\\",
)

METADATA_FIELDS = {
    "schema_version",
    "backend",
    "identity",
    "model",
    "worktree",
    "attempt_dir",
    "brief_sha256",
    "resume_id",
    "requested_effort",
    "configured_effort",
    "state",
    "pid",
    "exit_code",
    "started_at",
    "ended_at",
    "error",
}
ATTEMPT_FILES = {"brief.md", "dispatch.md", "worker.jsonl", "stderr.log", "run.json"}


def _cli_body(version: str, help_text: str, models: str, argv_log: Path,
              marker: Path, behaviour: str) -> str:
    """A synthetic CLI that answers probes and logs only real worker invocations."""
    return (
        "import json\n"
        "import os\n"
        "import signal\n"
        "import sys\n"
        "import time\n"
        f"VERSION = {version!r}\n"
        f"HELP = {help_text!r}\n"
        f"MODELS = {models!r}\n"
        f"ARGV_LOG = {str(argv_log)!r}\n"
        f"MARKER = {str(marker)!r}\n"
        "args = sys.argv[1:]\n"
        "if args[:1] in (['--version'], ['-v']):\n"
        "    sys.stdout.write(VERSION)\n"
        "    raise SystemExit(0)\n"
        "if args[:1] in (['--help'], ['-h']) or not args:\n"
        "    sys.stdout.write(HELP)\n"
        "    raise SystemExit(0)\n"
        "if args in (['models'], ['--list-models']):\n"
        "    sys.stdout.write(MODELS)\n"
        "    raise SystemExit(0)\n"
        "with open(ARGV_LOG, 'a', encoding='utf-8') as handle:\n"
        "    handle.write(json.dumps(args, ensure_ascii=False) + '\\n')\n"
        "with open(MARKER, 'a', encoding='utf-8') as handle:\n"
        "    handle.write('worker\\n')\n"
        + behaviour
    )


class RunnerFixture(unittest.TestCase):
    """Temporary worktree, synthetic PATH, and a freshly imported runner."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.base = Path(self.tmpdir.name).resolve()
        self.bindir = self.base / "bin"
        self.bindir.mkdir()
        self.worktree = self.base / "worktree"
        self.worktree.mkdir()
        subprocess.run(
            ["git", "init", "-q", str(self.worktree)],
            check=False,
            capture_output=True,
        )
        self.evidence = self.worktree / ".superpowers"
        self.evidence.mkdir()
        self.attempt = self.evidence / "attempt-1"
        self.brief = self.base / "task-brief.md"
        self.brief.write_text(
            "# Synthetic brief\n\nImplement the synthetic thing.\n", encoding="utf-8"
        )
        self.argv_log = self.base / "worker-argv.jsonl"
        self.marker = self.base / "worker-invocations.log"
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

    def write_cli(self, name: str, version: str, help_text: str, models: str,
                  behaviour: str) -> Path:
        body = _cli_body(version, help_text, models, self.argv_log, self.marker, behaviour)
        if os.name == "nt":
            script = self.bindir / f"{name}.py"
            script.write_text(body, encoding="utf-8")
            path = self.bindir / f"{name}.cmd"
            path.write_text(
                f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8"
            )
            return path
        path = self.bindir / name
        path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def write_grok(self, behaviour: str = BEHAVIOUR_OK, help_text: str = GROK_HELP) -> Path:
        return self.write_cli("grok", GROK_VERSION, help_text, "", behaviour)

    def write_cursor(self, behaviour: str = BEHAVIOUR_OK) -> Path:
        return self.write_cli("cursor-agent", CURSOR_VERSION, CURSOR_HELP, CURSOR_MODELS, behaviour)

    def options(self, module, **overrides):
        values = {
            "backend": "grok",
            "worktree": self.worktree,
            "brief": self.brief,
            "attempt_dir": self.attempt,
            "effort": "high",
            "sandbox_profile": "sddx-worktree",
        }
        values.update(overrides)
        return module.RunOptions(**values)

    def invoke(self, module, options) -> int:
        with self.on_synthetic_path():
            return module.run_worker(options)

    @contextlib.contextmanager
    def on_synthetic_path(self):
        """Only the synthetic CLIs are reachable, and BLOCKED lines are captured."""
        self.stderr = io.StringIO()
        with mock.patch.dict(os.environ, {"PATH": str(self.bindir)}, clear=False):
            with contextlib.redirect_stderr(self.stderr):
                yield

    def worker_invocations(self) -> list[list[str]]:
        if not self.argv_log.exists():
            return []
        return [
            json.loads(line)
            for line in self.argv_log.read_text(encoding="utf-8").splitlines()
            if line
        ]

    def worker_argv(self) -> list[str]:
        invocations = self.worker_invocations()
        self.assertEqual(len(invocations), 1, "expected exactly one worker invocation")
        return invocations[0]

    def metadata(self) -> dict:
        return json.loads((self.attempt / "run.json").read_text(encoding="utf-8"))

    def assert_no_worker_invocation(self) -> None:
        self.assertEqual(self.worker_invocations(), [])


class BuildArgvTests(RunnerFixture):
    """`build_argv` is pinned against synthetic resolver payloads only."""

    RULES = "SYNTHETIC RULES: do the one task, then report."

    def dispatch_file(self, text: str = "SYNTHETIC DISPATCH") -> Path:
        path = self.base / "dispatch.md"
        path.write_text(text, encoding="utf-8")
        return path

    def grok_resolved(self, prompt_flag: str = "--single") -> dict:
        return {
            "backend": "grok",
            "available": True,
            "executable": "/synthetic/grok",
            "identity": GROK_VERSION.strip(),
            "argv_prefix": [
                "/synthetic/grok",
                "--no-plan",
                "--no-subagents",
                "--always-approve",
                "--disable-web-search",
                "--sandbox",
                "workspace",
            ],
            "reason": None,
            "launch": {
                "cwd_flag": "--cwd",
                "prompt_flag": prompt_flag,
                "effort_flag": "--reasoning-effort",
                "output_format": "streaming-messages-json",
            },
            "model_ids": [],
        }

    def cursor_resolved(self) -> dict:
        return {
            "backend": "cursor",
            "available": True,
            "executable": "/synthetic/cursor-agent",
            "identity": CURSOR_VERSION.strip(),
            "argv_prefix": [
                "/synthetic/cursor-agent",
                "--print",
                "--trust",
                "--auto-review",
                "--sandbox",
                "enabled",
            ],
            "reason": None,
            "launch": {
                "cwd_flag": "--workspace",
                "prompt_flag": None,
                "effort_flag": None,
                "output_format": "stream-json",
            },
            "model_ids": ["grok-4", "grok-4-fast"],
        }

    def test_grok_argv_replaces_the_sandbox_value_and_carries_rules(self) -> None:
        module = self.load()
        dispatch = self.dispatch_file()
        argv = module.build_argv(
            self.grok_resolved(), self.options(module), dispatch, self.RULES
        )
        self.assertEqual(argv.count("--sandbox"), 1)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "sddx-worktree")
        self.assertEqual(argv[argv.index("--rules") + 1], self.RULES)
        self.assertEqual(argv[argv.index("--cwd") + 1], str(self.worktree))
        self.assertEqual(argv[argv.index("--reasoning-effort") + 1], "high")
        self.assertEqual(argv[argv.index("--output-format") + 1], "streaming-messages-json")
        for flag in ("--no-plan", "--no-subagents", "--disable-web-search", "--always-approve"):
            self.assertIn(flag, argv)

    def test_grok_argv_passes_the_dispatch_path_for_prompt_file(self) -> None:
        module = self.load()
        dispatch = self.dispatch_file()
        argv = module.build_argv(
            self.grok_resolved("--prompt-file"), self.options(module), dispatch, self.RULES
        )
        self.assertEqual(argv[argv.index("--prompt-file") + 1], str(dispatch))
        self.assertNotIn("SYNTHETIC DISPATCH", argv)

    def test_grok_argv_passes_the_dispatch_text_for_an_inline_prompt_flag(self) -> None:
        module = self.load()
        dispatch = self.dispatch_file("INLINE DISPATCH BODY")
        argv = module.build_argv(
            self.grok_resolved("--single"), self.options(module), dispatch, self.RULES
        )
        self.assertEqual(argv[argv.index("--single") + 1], "INLINE DISPATCH BODY")

    def test_grok_argv_never_names_a_model(self) -> None:
        module = self.load()
        argv = module.build_argv(
            self.grok_resolved(), self.options(module), self.dispatch_file(), self.RULES
        )
        self.assertNotIn("--model", argv)

    def test_cursor_argv_ends_with_the_dispatch_text(self) -> None:
        module = self.load()
        dispatch = self.dispatch_file("CURSOR DISPATCH BODY")
        options = self.options(
            module, backend="cursor", model="grok-4", sandbox_profile=None
        )
        argv = module.build_argv(self.cursor_resolved(), options, dispatch, self.RULES)
        self.assertEqual(argv[-1], "CURSOR DISPATCH BODY")
        self.assertEqual(argv[argv.index("--model") + 1], "grok-4")
        self.assertEqual(argv[argv.index("--workspace") + 1], str(self.worktree))
        self.assertEqual(argv[argv.index("--output-format") + 1], "stream-json")
        self.assertEqual(argv.count("--sandbox"), 1)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "enabled")

    def test_cursor_argv_has_no_rules_or_effort_flag(self) -> None:
        module = self.load()
        options = self.options(
            module, backend="cursor", model="grok-4", sandbox_profile=None
        )
        argv = module.build_argv(
            self.cursor_resolved(), options, self.dispatch_file(), self.RULES
        )
        self.assertNotIn("--rules", argv)
        self.assertNotIn("--reasoning-effort", argv)
        self.assertNotIn("--effort", argv)

    def test_absent_resume_adds_neither_a_bare_resume_nor_continue(self) -> None:
        module = self.load()
        for resolved, extra in (
            (self.grok_resolved(), {}),
            (self.cursor_resolved(), {"backend": "cursor", "model": "grok-4",
                                      "sandbox_profile": None}),
        ):
            with self.subTest(backend=resolved["backend"]):
                argv = module.build_argv(
                    resolved, self.options(module, **extra), self.dispatch_file(), self.RULES
                )
                self.assertNotIn("--resume", argv)
                self.assertNotIn("--continue", argv)

    def test_resume_string_is_passed_through_unchanged(self) -> None:
        module = self.load()
        resume = "not-a-uuid/session:42 한글"
        for resolved, extra in (
            (self.grok_resolved(), {}),
            (self.cursor_resolved(), {"backend": "cursor", "model": "grok-4",
                                      "sandbox_profile": None}),
        ):
            with self.subTest(backend=resolved["backend"]):
                argv = module.build_argv(
                    resolved,
                    self.options(module, resume_id=resume, **extra),
                    self.dispatch_file(),
                    self.RULES,
                )
                self.assertEqual(argv[argv.index("--resume") + 1], resume)

    def test_argv_never_carries_forbidden_controller_flags(self) -> None:
        module = self.load()
        for resolved, extra in (
            (self.grok_resolved(), {}),
            (self.cursor_resolved(), {"backend": "cursor", "model": "grok-4",
                                      "sandbox_profile": None}),
        ):
            with self.subTest(backend=resolved["backend"]):
                argv = module.build_argv(
                    resolved,
                    self.options(module, resume_id="known-id", **extra),
                    self.dispatch_file(),
                    self.RULES,
                )
                for flag in ("--worktree", "--continue", "--plugin-dir", "--force", "--yolo"):
                    self.assertNotIn(flag, argv)


class AttemptDirectoryTests(RunnerFixture):
    """Every rejection happens before a single process is started."""

    def test_existing_attempt_directory_is_refused_and_left_untouched(self) -> None:
        module = self.load()
        self.write_grok()
        self.attempt.mkdir()
        sentinel = self.attempt / "sentinel.txt"
        sentinel.write_text("earlier attempt", encoding="utf-8")
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "earlier attempt")
        self.assertEqual({path.name for path in self.attempt.iterdir()}, {"sentinel.txt"})

    def test_attempt_directory_outside_the_worktree_is_refused(self) -> None:
        module = self.load()
        self.write_grok()
        outside = self.base / "elsewhere"
        outside.mkdir()
        code = self.invoke(module, self.options(module, attempt_dir=outside / "attempt-1"))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        self.assertFalse((outside / "attempt-1").exists())

    def test_attempt_directory_beside_superpowers_is_refused(self) -> None:
        module = self.load()
        self.write_grok()
        target = self.worktree / "not-superpowers"
        target.mkdir()
        code = self.invoke(module, self.options(module, attempt_dir=target / "attempt-1"))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks are unavailable here")
    def test_symlinked_attempt_path_is_refused(self) -> None:
        module = self.load()
        self.write_grok()
        outside = self.base / "outside-store"
        outside.mkdir()
        link = self.evidence / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as error:  # pragma: no cover - platform gate
            self.skipTest(f"symlink creation is unavailable: {error}")
        code = self.invoke(module, self.options(module, attempt_dir=link / "attempt-1"))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        self.assertEqual(list(outside.iterdir()), [])

    def test_missing_attempt_parent_is_refused(self) -> None:
        module = self.load()
        self.write_grok()
        missing = self.evidence / "absent" / "attempt-1"
        code = self.invoke(module, self.options(module, attempt_dir=missing))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        self.assertFalse(missing.parent.exists())

    def test_superpowers_root_itself_is_not_an_attempt_directory(self) -> None:
        module = self.load()
        self.write_grok()
        code = self.invoke(module, self.options(module, attempt_dir=self.evidence))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()

    def test_grok_without_a_prepared_profile_never_starts_a_worker(self) -> None:
        module = self.load()
        self.write_grok()
        code = self.invoke(module, self.options(module, sandbox_profile=None))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        self.assertFalse(self.attempt.exists())

    def test_grok_with_an_explicit_model_never_starts_a_worker(self) -> None:
        module = self.load()
        self.write_grok()
        code = self.invoke(module, self.options(module, model="grok-4"))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()

    def test_cursor_with_a_sandbox_profile_never_starts_a_worker(self) -> None:
        module = self.load()
        self.write_cursor()
        options = self.options(
            module, backend="cursor", model="grok-4", sandbox_profile="sddx-worktree"
        )
        code = self.invoke(module, options)
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()

    def test_cursor_model_outside_the_confirmed_list_never_starts_a_worker(self) -> None:
        module = self.load()
        self.write_cursor()
        options = self.options(
            module, backend="cursor", model="grok-unlisted", sandbox_profile=None
        )
        code = self.invoke(module, options)
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        self.assertEqual(self.metadata()["state"], "launch_failed")

    def test_empty_resume_id_never_starts_a_worker(self) -> None:
        module = self.load()
        self.write_grok()
        # An empty value would reach the CLI as the forbidden bare `--resume`.
        code = self.invoke(module, self.options(module, resume_id=""))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        self.assertFalse(self.attempt.exists())

    def test_unavailable_backend_is_a_launch_failure(self) -> None:
        module = self.load()
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        metadata = self.metadata()
        self.assertEqual(metadata["state"], "launch_failed")
        self.assertIsNone(metadata["exit_code"])
        self.assertIsNotNone(metadata["error"])


class WorkerExecutionTests(RunnerFixture):
    """One attempt, launched for real, with its evidence preserved."""

    def test_exit_seven_worker_preserves_every_raw_stream(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_EXIT_7)
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 7)
        metadata = self.metadata()
        self.assertEqual(metadata["schema_version"], 1)
        self.assertEqual(metadata["state"], "exited")
        self.assertEqual(metadata["exit_code"], 7)
        self.assertEqual(metadata["backend"], "grok")
        self.assertIsNone(metadata["model"])
        self.assertEqual(metadata["requested_effort"], "high")
        self.assertEqual(metadata["configured_effort"], "high")
        self.assertIsNone(metadata["resume_id"])
        self.assertIsInstance(metadata["pid"], int)
        self.assertIsNone(metadata["error"])
        self.assertEqual(
            (self.attempt / "worker.jsonl").read_bytes(),
            json.dumps({"type": "assistant", "text": "reported success"}).encode() + b"\n",
        )
        self.assertEqual(
            (self.attempt / "stderr.log").read_bytes(), b"synthetic failure\n"
        )
        self.assertFalse((self.attempt / "report.md").exists())
        self.assertEqual({path.name for path in self.attempt.iterdir()}, ATTEMPT_FILES)

    def test_attempt_records_the_exact_brief_and_its_digest(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        self.invoke(module, self.options(module))
        copied = (self.attempt / "brief.md").read_bytes()
        self.assertEqual(copied, self.brief.read_bytes())
        self.assertEqual(self.metadata()["brief_sha256"], hashlib.sha256(copied).hexdigest())

    def test_metadata_fields_match_the_specification(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        self.invoke(module, self.options(module))
        self.assertEqual(set(self.metadata()), METADATA_FIELDS)

    def test_metadata_is_written_at_starting_running_and_terminal_state(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        observed: list[dict] = []
        real = module.write_metadata

        def spy(path, value):
            observed.append(dict(value))
            real(path, value)

        with mock.patch.object(module, "write_metadata", spy):
            self.invoke(module, self.options(module))
        self.assertEqual([entry["state"] for entry in observed], ["starting", "running", "exited"])
        self.assertIsNone(observed[0]["pid"])
        self.assertIsInstance(observed[1]["pid"], int)
        self.assertIsNone(observed[1]["ended_at"])
        self.assertIsNotNone(observed[2]["ended_at"])

    def test_malformed_stdout_is_preserved_rather_than_discarded(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_MALFORMED_JSON)
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 0)
        raw = (self.attempt / "worker.jsonl").read_bytes()
        self.assertEqual(raw, b'{"type": "assistant", "text": "trunca\nnot json at all\n')
        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw.splitlines()[0])

    def test_provider_error_is_attempted_exactly_once(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_PROVIDER_402)
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 1)
        self.assertEqual(len(self.worker_invocations()), 1)
        self.assertIn(b"402", (self.attempt / "stderr.log").read_bytes())
        self.assertEqual(self.metadata()["state"], "exited")

    def test_runner_waits_for_a_delayed_exit(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_DELAYED)
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 0)
        self.assertEqual(
            (self.attempt / "worker.jsonl").read_bytes(),
            b'{"type": "assistant", "text": "late"}\n',
        )
        metadata = self.metadata()
        self.assertLessEqual(metadata["started_at"], metadata["ended_at"])

    def test_large_streams_are_written_whole(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_LARGE)
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 0)
        expected = (b"x" * 1024 + b"\n") * 512
        self.assertEqual((self.attempt / "worker.jsonl").read_bytes(), expected)
        self.assertEqual((self.attempt / "stderr.log").read_bytes(), expected)

    @unittest.skipUnless(os.name != "nt", "negative returncodes are a POSIX signal convention")
    def test_signal_termination_keeps_the_negative_returncode(self) -> None:
        import signal

        module = self.load()
        self.write_grok(BEHAVIOUR_SIGNAL)
        code = self.invoke(module, self.options(module))
        self.assertEqual(code, 128 + signal.SIGTERM)
        metadata = self.metadata()
        self.assertEqual(metadata["exit_code"], -signal.SIGTERM)
        self.assertEqual(metadata["state"], "exited")

    def test_oserror_before_exec_is_a_launch_failure(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        with self.on_synthetic_path():
            resolved = module.resolve("grok")
        resolved = dict(resolved)
        resolved["executable"] = str(self.base / "definitely-absent-binary")
        resolved["argv_prefix"] = [resolved["executable"], *resolved["argv_prefix"][1:]]
        with mock.patch.object(module, "resolve", return_value=resolved):
            code = self.invoke(module, self.options(module))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        metadata = self.metadata()
        self.assertEqual(metadata["state"], "launch_failed")
        self.assertIsNone(metadata["exit_code"])
        self.assertIsNotNone(metadata["error"])
        self.assertEqual((self.attempt / "worker.jsonl").read_bytes(), b"")

    def test_controller_interrupt_is_recorded_without_killing_the_tree(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_SLEEP)
        with self.on_synthetic_path():
            resolved = module.resolve("grok")
        started: list[subprocess.Popen] = []

        class InterruptingPopen(subprocess.Popen):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                started.append(self)

            def wait(self, timeout=None):  # noqa: D102 - controller pressed Ctrl-C
                raise KeyboardInterrupt

        with mock.patch.object(module, "resolve", return_value=resolved):
            with mock.patch.object(module.subprocess, "Popen", InterruptingPopen):
                code = self.invoke(module, self.options(module))
        self.assertEqual(len(started), 1)
        process = started[0]
        # The override above raises on every call, so drain with the base method.
        self.addCleanup(lambda: subprocess.Popen.wait(process))
        self.addCleanup(process.kill)
        self.assertEqual(code, 130)
        metadata = self.metadata()
        self.assertEqual(metadata["state"], "interrupted")
        self.assertIsNone(metadata["exit_code"])
        self.assertIsNone(process.poll(), "runner must not kill the worker process tree")

    def test_no_environment_value_reaches_the_prompt_or_the_metadata(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        secret = "synthetic-sentinel-value-9d1f"
        with mock.patch.dict(os.environ, {"SDDX_SYNTHETIC_MARKER": secret}, clear=False):
            self.invoke(module, self.options(module))
        for name in ("dispatch.md", "run.json", "brief.md"):
            self.assertNotIn(secret, (self.attempt / name).read_text(encoding="utf-8"))
        self.assertNotIn(secret, json.dumps(self.worker_argv(), ensure_ascii=False))


class WorkerArgvTests(RunnerFixture):
    """What the worker child actually received, not the prefix computed for it."""

    def test_grok_child_receives_the_prepared_profile_and_the_full_rules(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        self.invoke(module, self.options(module, sandbox_profile="sddx-worktree"))
        received = self.worker_argv()
        rules = WORKER_PROMPT.read_text(encoding="utf-8")
        self.assertEqual(received.count("--sandbox"), 1)
        self.assertEqual(received[received.index("--sandbox") + 1], "sddx-worktree")
        self.assertEqual(received[received.index("--rules") + 1], rules)
        for flag in ("--no-plan", "--no-subagents", "--disable-web-search", "--always-approve"):
            self.assertIn(flag, received)
        self.assertNotIn("--worktree", received)
        self.assertNotIn("--continue", received)
        self.assertNotIn("--plugin-dir", received)
        self.assertEqual(received[received.index("--cwd") + 1], str(self.worktree))
        self.assertEqual(
            received[received.index("--output-format") + 1], "streaming-messages-json"
        )
        prompt = received[received.index("--single") + 1]
        self.assertEqual(prompt, (self.attempt / "dispatch.md").read_text(encoding="utf-8"))
        self.assertIn(str(self.attempt / "brief.md"), prompt)
        self.assertIn(str(self.attempt / "report.md"), prompt)

    def test_grok_child_receives_the_dispatch_path_when_prompt_file_exists(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK, help_text=GROK_HELP_WITH_PROMPT_FILE)
        self.invoke(module, self.options(module))
        received = self.worker_argv()
        self.assertEqual(
            received[received.index("--prompt-file") + 1], str(self.attempt / "dispatch.md")
        )

    def test_cursor_child_receives_a_single_enabled_sandbox_and_the_named_model(self) -> None:
        module = self.load()
        self.write_cursor(BEHAVIOUR_OK)
        options = self.options(
            module, backend="cursor", model="grok-4-fast", sandbox_profile=None
        )
        self.invoke(module, options)
        received = self.worker_argv()
        self.assertIn("--print", received)
        self.assertIn("--trust", received)
        self.assertIn("--auto-review", received)
        self.assertNotIn("--force", received)
        self.assertNotIn("--yolo", received)
        self.assertEqual(received.count("--sandbox"), 1)
        self.assertEqual(received[received.index("--sandbox") + 1], "enabled")
        self.assertEqual(received[received.index("--model") + 1], "grok-4-fast")
        self.assertEqual(received[received.index("--output-format") + 1], "stream-json")
        self.assertEqual(received[received.index("--workspace") + 1], str(self.worktree))
        self.assertNotIn("--rules", received)
        prompt = received[-1]
        self.assertEqual(prompt, (self.attempt / "dispatch.md").read_text(encoding="utf-8"))
        self.assertIn(WORKER_PROMPT.read_text(encoding="utf-8"), prompt)
        self.assertIn(str(self.attempt / "brief.md"), prompt)
        self.assertIn(str(self.attempt / "report.md"), prompt)
        self.assertEqual(self.metadata()["model"], "grok-4-fast")
        self.assertIsNone(self.metadata()["configured_effort"])
        self.assertEqual(self.metadata()["requested_effort"], "high")

    def test_relative_worktree_reaches_the_child_as_an_absolute_path(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        relative = Path(os.path.relpath(self.worktree, Path.cwd()))
        self.assertFalse(relative.is_absolute())
        self.invoke(module, self.options(module, worktree=relative))
        received = self.worker_argv()
        # A relative `--cwd` would be re-resolved against the worktree the child
        # was started in, which is the worktree itself.
        self.assertEqual(received[received.index("--cwd") + 1], str(self.worktree))
        self.assertEqual(self.metadata()["worktree"], str(self.worktree))

    def test_resume_reaches_the_child_unchanged(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        resume = "session-not-a-uuid_42"
        self.invoke(module, self.options(module, resume_id=resume))
        received = self.worker_argv()
        self.assertEqual(received[received.index("--resume") + 1], resume)
        self.assertEqual(self.metadata()["resume_id"], resume)

    def test_child_sees_no_resume_or_continue_without_a_known_id(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        self.invoke(module, self.options(module))
        received = self.worker_argv()
        self.assertNotIn("--resume", received)
        self.assertNotIn("--continue", received)
        self.assertIsNone(self.metadata()["resume_id"])


class TransportTests(RunnerFixture):
    """The launch transport carries hostile arguments or fails the launch outright."""

    def _round_trip(self, arguments: list[str]) -> list[str]:
        module = self.load()
        executable = self.write_cli("echoer", "x\n", "x\n", "", BEHAVIOUR_OK)
        command = module._subprocess_args(str(executable), arguments)
        completed = subprocess.run(command, check=False, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return self.worker_argv()

    def test_hostile_arguments_survive_the_launch_transport(self) -> None:
        received = self._round_trip(list(HOSTILE_ARGUMENTS))
        self.assertEqual(received, list(HOSTILE_ARGUMENTS))

    def test_built_argv_round_trips_through_the_real_launch_path(self) -> None:
        module = self.load()
        executable = self.write_cli("echoer", "x\n", "x\n", "", BEHAVIOUR_OK)
        dispatch = self.base / "dispatch.md"
        dispatch.write_text(" | ".join(HOSTILE_ARGUMENTS), encoding="utf-8")
        resolved = {
            "backend": "grok",
            "available": True,
            "executable": str(executable),
            "identity": "grok synthetic",
            "argv_prefix": [
                str(executable),
                "--no-plan",
                "--no-subagents",
                "--always-approve",
                "--disable-web-search",
                "--sandbox",
                "workspace",
            ],
            "reason": None,
            "launch": {
                "cwd_flag": "--cwd",
                "prompt_flag": "--single",
                "effort_flag": "--reasoning-effort",
                "output_format": "streaming-messages-json",
            },
            "model_ids": [],
        }
        options = self.options(module, resume_id=HOSTILE_ARGUMENTS[2])
        argv = module.build_argv(resolved, options, dispatch, " ".join(HOSTILE_ARGUMENTS))
        command = module._subprocess_args(argv[0], argv[1:])
        completed = subprocess.run(command, check=False, capture_output=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(self.worker_argv(), argv[1:])

    @unittest.skipUnless(os.name == "nt", "a .cmd wrapper round trip needs a real cmd.exe")
    def test_cmd_wrapper_round_trips_hostile_arguments(self) -> None:  # pragma: no cover
        received = self._round_trip(list(HOSTILE_ARGUMENTS))
        self.assertEqual(received, list(HOSTILE_ARGUMENTS))

    def test_untransportable_argument_is_a_launch_failure(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        with mock.patch.object(
            module, "_subprocess_args", side_effect=ValueError("argument cannot cross")
        ):
            code = self.invoke(module, self.options(module))
        self.assertEqual(code, 2)
        self.assert_no_worker_invocation()
        metadata = self.metadata()
        self.assertEqual(metadata["state"], "launch_failed")
        self.assertIsNotNone(metadata["error"])

    def test_launch_failure_error_never_quotes_the_rules_or_the_brief(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_OK)
        rules = WORKER_PROMPT.read_text(encoding="utf-8")
        with mock.patch.object(
            module,
            "_subprocess_args",
            side_effect=ValueError(f"argument cannot cross a cmd.exe wrapper: {rules!r}"),
        ):
            self.invoke(module, self.options(module))
        error = self.metadata()["error"]
        self.assertNotIn(rules.splitlines()[0], error)
        self.assertNotIn("Implement the synthetic thing", error)
        printed = self.stderr.getvalue()
        self.assertTrue(printed.startswith("BLOCKED: "), printed)
        self.assertNotIn(rules.splitlines()[0], printed)


class CliTests(RunnerFixture):
    """The command line stays shaped for a sibling subcommand."""

    def test_run_subcommand_dispatches_to_the_runner(self) -> None:
        module = self.load()
        self.write_grok(BEHAVIOUR_EXIT_7)
        with self.on_synthetic_path():
            code = module.main(
                [
                    "run",
                    "--backend",
                    "grok",
                    "--worktree",
                    str(self.worktree),
                    "--brief",
                    str(self.brief),
                    "--attempt-dir",
                    str(self.attempt),
                    "--effort",
                    "high",
                    "--sandbox-profile",
                    "sddx-worktree",
                ]
            )
        self.assertEqual(code, 7)
        self.assertEqual(self.metadata()["exit_code"], 7)

    def test_cursor_run_subcommand_accepts_model_and_resume(self) -> None:
        module = self.load()
        self.write_cursor(BEHAVIOUR_OK)
        with self.on_synthetic_path():
            code = module.main(
                [
                    "run",
                    "--backend",
                    "cursor",
                    "--worktree",
                    str(self.worktree),
                    "--brief",
                    str(self.brief),
                    "--attempt-dir",
                    str(self.attempt),
                    "--effort",
                    "high",
                    "--model",
                    "grok-4",
                    "--resume",
                    "known-session-id",
                ]
            )
        self.assertEqual(code, 0)
        received = self.worker_argv()
        self.assertEqual(received[received.index("--resume") + 1], "known-session-id")

    def test_unknown_subcommand_is_rejected(self) -> None:
        module = self.load()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            module.main(["sprint"])
        self.assertEqual(raised.exception.code, 2)

    def test_subcommand_is_required(self) -> None:
        module = self.load()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            module.main([])
        self.assertEqual(raised.exception.code, 2)

    def test_worker_rules_come_from_the_skill_reference_file(self) -> None:
        module = self.load()
        self.assertEqual(
            module.WORKER_RULES_PATH,
            SCRIPTS.parent / "references" / "worker-prompt.md",
        )
        self.assertEqual(module._worker_rules(), WORKER_PROMPT.read_text(encoding="utf-8"))


class MetadataWriteTests(RunnerFixture):
    """`write_metadata` replaces atomically and leaves no temporary file behind."""

    def test_metadata_replacement_leaves_no_temporary_file(self) -> None:
        module = self.load()
        target = self.evidence / "run.json"
        module.write_metadata(target, {"state": "starting"})
        module.write_metadata(target, {"state": "exited"})
        self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"state": "exited"})
        self.assertEqual({path.name for path in self.evidence.iterdir()}, {"run.json"})

    def test_utc_now_is_timezone_aware_utc(self) -> None:
        from datetime import datetime

        module = self.load()
        stamp = module.utc_now()
        parsed = datetime.fromisoformat(stamp)
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.utcoffset().total_seconds(), 0)


if __name__ == "__main__":
    unittest.main()
