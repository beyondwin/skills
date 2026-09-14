from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS = ROOT / "skills" / "sddx" / "scripts"

GROK_VERSION = "grok 1.0.25 (deadbeef) [stable]\n"
GROK_HELP = """
Usage: grok [OPTIONS]
      --cwd <CWD>
      --no-plan
      --no-subagents
      --disallowed-tools <TOOLS>
      --deny <RULE>
      --always-approve
      --reasoning-effort <EFFORT>
      --disable-web-search
      --sandbox <PROFILE>
      --rules <RULES>
      --output-format <streaming-messages-json>
  -p, --single <PROMPT>
  -r, --resume [<SESSION_ID>]
"""
GROK_HELP_WITHOUT_CWD = """
Usage: grok [OPTIONS]
      --no-plan
      --no-subagents
      --disallowed-tools <TOOLS>
      --deny <RULE>
      --always-approve
      --reasoning-effort <EFFORT>
      --disable-web-search
      --sandbox <PROFILE>
      --rules <RULES>
      --output-format <streaming-messages-json>
  -p, --single <PROMPT>
  -r, --resume [<SESSION_ID>]
"""
GROK_HELP_WITHOUT_OUTPUT_FORMAT = GROK_HELP.replace(
    "      --output-format <streaming-messages-json>\n", ""
)
# Declares the format value under a differently named option and no
# `--output-format`, so only checking both halves rejects this.
GROK_HELP_FORMAT_VALUE_UNDER_OTHER_OPTION = GROK_HELP.replace(
    "      --output-format <streaming-messages-json>",
    "      --json-mode <text|streaming-messages-json>",
)
GROK_HELP_WITH_PROMPT_FILE = GROK_HELP.replace(
    "  -p, --single <PROMPT>",
    "      --prompt-file <PATH>\n  -p, --single <PROMPT>",
)
GROK_HELP_WITH_EFFORT_ALIAS = GROK_HELP.replace("--reasoning-effort", "--effort")
GROK_HELP_WITH_SHORT_PROMPT_ONLY = GROK_HELP.replace(
    "  -p, --single <PROMPT>", "  -p <PROMPT>"
)
GROK_HELP_PROMPT_FILE_ONLY = GROK_HELP.replace(
    "  -p, --single <PROMPT>\n", "      --prompt-file <PATH>\n"
)
# No prompt flag at all. `--no-plan` survives, so a substring test still "finds" `-p`.
GROK_HELP_WITHOUT_PROMPT_FLAG = GROK_HELP.replace("  -p, --single <PROMPT>\n", "")

CURSOR_VERSION = "cursor-agent 2026.08.07\n"
CURSOR_HELP = """
Usage: cursor-agent [options]

Commands:
  models                    Print the models this account may use
  update                    Update the installed build

Options:
  -p, --print
  -f, --force
      --yolo
      --trust
      --auto-review
      --sandbox <mode>
      --workspace <path>
      --model <model>
      --output-format <text|json|stream-json>
      --resume [chatId]
      --list-models
"""
CURSOR_HELP_MODELS_SUBCOMMAND_ONLY = CURSOR_HELP.replace("      --list-models\n", "")
CURSOR_HELP_LIST_MODELS_ONLY = CURSOR_HELP.replace(
    "  models                    Print the models this account may use\n", ""
)
CURSOR_HELP_WITHOUT_MODEL_LIST = CURSOR_HELP_MODELS_SUBCOMMAND_ONLY.replace(
    "  models                    Print the models this account may use\n",
    "  Run cursor-agent to see which models are available to you.\n",
)
CURSOR_HELP_WITHOUT_AUTO_REVIEW = CURSOR_HELP.replace("      --auto-review\n", "")
CURSOR_HELP_WITHOUT_SANDBOX = CURSOR_HELP.replace("      --sandbox <mode>\n", "")
CURSOR_HELP_WITHOUT_STREAM_JSON = CURSOR_HELP.replace(
    "      --output-format <text|json|stream-json>\n",
    "      --output-format <text|json>\n",
)
CURSOR_HELP_WITH_CWD = CURSOR_HELP.replace("--workspace <path>", "--cwd <path>")
# Declares the format value under a differently named option and no
# `--output-format`, so only checking both halves rejects this.
CURSOR_HELP_FORMAT_VALUE_UNDER_OTHER_OPTION = CURSOR_HELP.replace(
    "      --output-format <text|json|stream-json>",
    "      --json-mode <text|json|stream-json>",
)
# Declares only the short print flag; the resolver must fall back to `-p`.
CURSOR_HELP_SHORT_PRINT_ONLY = CURSOR_HELP.replace("  -p, --print", "  -p")
# Declares the plural `--models` and no `--model`, so a substring test still "finds" it.
CURSOR_HELP_PLURAL_MODEL_ONLY = CURSOR_HELP.replace(
    "      --model <model>\n", "      --models\n"
)

CURSOR_MODELS = "gpt-5\ncomposer\ngrok-4\n"
NO_GROK_MODELS = "gpt-5\ncomposer\n"
PROSE_ONLY_MODELS = "Available models include grok and others\ngpt-5\n"

# The shape the shipped CLI actually prints: a header, one `<id> - <Description>` line
# per model, and a trailing tip paragraph. Every value here is synthetic — only the
# format is taken from the real listing. `composer-2.5 - Grok-like reasoning` is the
# description trap: "grok" appears after the separator and must not yield an ID.
CURSOR_MODELS_LISTING = """Available models

auto - Auto (default)
gpt-5.3-codex-low - Codex 5.3 Low
cursor-grok-9.1-high-fast - Cursor Grok 9.1 Fast
composer-2.5 - Grok-like reasoning
cursor-grok-9.0-high - Cursor Grok 9.0
cursor-grok-9.1-low - Cursor Grok 9.1 Low
cursor-grok-9.1-high - Cursor Grok 9.1
cursor-grok-9.1-xhigh-fast - Cursor Grok 9.1 Extra High Fast
kimi-k3-low - Kimi K3 Low

Tip: use --model <id> (or /model <id> in interactive mode) to switch. \
Parameterized models also accept quoted overrides, \
e.g. --model 'claude-opus-4-8[context=1m,effort=high,fast=false]'.
"""
# Source order, and the `-fast` variant deliberately precedes the plain high tier.
CURSOR_MODELS_LISTING_IDS = [
    "cursor-grok-9.1-high-fast",
    "cursor-grok-9.0-high",
    "cursor-grok-9.1-low",
    "cursor-grok-9.1-high",
    "cursor-grok-9.1-xhigh-fast",
]

MARKER_NAME = "worker-invocations.log"
CALL_LOG_NAME = "model-list-calls.log"


def _cli_body(version: str, help_text: str, responses: dict[str, tuple[int, str, str]],
              marker: Path, call_log: Path) -> str:
    """Body of a synthetic CLI that answers only what its own help declares."""
    return (
        "import sys\n"
        f"VERSION = {version!r}\n"
        f"HELP = {help_text!r}\n"
        f"RESPONSES = {responses!r}\n"
        f"MARKER = {str(marker)!r}\n"
        f"CALL_LOG = {str(call_log)!r}\n"
        "args = sys.argv[1:]\n"
        "if args[:1] in (['--version'], ['-v']):\n"
        "    sys.stdout.write(VERSION)\n"
        "    raise SystemExit(0)\n"
        "if args[:1] in (['--help'], ['-h']) or not args:\n"
        "    sys.stdout.write(HELP)\n"
        "    raise SystemExit(0)\n"
        "key = '\\x1f'.join(args)\n"
        "if key in RESPONSES:\n"
        "    code, out, err = RESPONSES[key]\n"
        "    with open(CALL_LOG, 'a', encoding='utf-8') as handle:\n"
        "        handle.write(key + '\\n')\n"
        "    sys.stdout.write(out)\n"
        "    sys.stderr.write(err)\n"
        "    raise SystemExit(code)\n"
        "with open(MARKER, 'a', encoding='utf-8') as handle:\n"
        "    handle.write(key + '\\n')\n"
        "sys.stderr.write('unsupported invocation\\n')\n"
        "raise SystemExit(2)\n"
    )


class ResolveBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.bindir = Path(self.tmpdir.name)
        self.marker = self.bindir / MARKER_NAME
        self.call_log = self.bindir / CALL_LOG_NAME
        sys.path.insert(0, str(SCRIPTS))
        self.addCleanup(lambda: sys.path.remove(str(SCRIPTS)) if str(SCRIPTS) in sys.path else None)
        self.addCleanup(self._assert_no_worker_invocation)

    def _assert_no_worker_invocation(self) -> None:
        self.assertEqual(self._lines(self.marker), [], "resolver launched a worker")

    @staticmethod
    def _lines(path: Path) -> list[str]:
        if not path.exists():
            return []
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line]

    def _calls(self) -> list[str]:
        return self._lines(self.call_log)

    def _write_cli(
        self,
        name: str,
        version: str,
        help_text: str,
        responses: dict[str, tuple[int, str, str]] | None = None,
    ) -> Path:
        body = _cli_body(version, help_text, responses or {}, self.marker, self.call_log)
        if os.name == "nt":
            script = self.bindir / f"{name}.py"
            script.write_text(body, encoding="utf-8")
            path = self.bindir / f"{name}.cmd"
            path.write_text(
                f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
                encoding="utf-8",
            )
            return path
        path = self.bindir / name
        path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def _path(self, *names: str) -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = str(self.bindir)
        return env

    def _load(self):
        import importlib

        if "resolve_backend" in sys.modules:
            del sys.modules["resolve_backend"]
        return importlib.import_module("resolve_backend")

    def _resolve(self, backend: str):
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            return module.resolve(backend)

    def assert_cursor_contract(self, resolved) -> None:
        self.assertIs(resolved["available"], True)
        argv = resolved["argv_prefix"]
        self.assertNotIn("--force", argv)
        self.assertNotIn("--yolo", argv)
        self.assertIn("--auto-review", argv)
        self.assertIn("--trust", argv)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "enabled")
        self.assertEqual(resolved["launch"]["output_format"], "stream-json")
        self.assertIsNone(resolved["launch"]["prompt_flag"])
        self.assertIsNone(resolved["launch"]["effort_flag"])
        self.assertEqual(resolved["model_ids"], ["grok-4"])

    # ------------------------------------------------------------------
    # fixture sanity
    # ------------------------------------------------------------------

    def test_fixture_cli_is_discoverable_on_path(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP)
        with mock.patch.dict(os.environ, self._path(), clear=False):
            found = shutil.which("grok")
        self.assertIsNotNone(found)
        self.assertEqual(Path(found).stem, "grok")

    def test_fixture_records_undeclared_invocations(self) -> None:
        # Proves the marker every other test asserts on is not silently inert: a
        # worker-shaped invocation the fixture never declared has to be recorded.
        path = self._write_cli("cursor-agent", CURSOR_VERSION, CURSOR_HELP)
        module = self._load()
        module._run(str(path), ["--print", "do the work"])
        self.assertEqual(self._lines(self.marker), ["--print\x1fdo the work"])
        self.marker.unlink()

    def test_main_refuses_windows_before_resolve(self) -> None:
        module = self._load()
        stderr = io.StringIO()
        with mock.patch.object(module.os, "name", "nt"):
            with contextlib.redirect_stderr(stderr):
                code = module.main(["--backend", "grok", "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(stderr.getvalue(), "BLOCKED: Windows is not a supported OS\n")

    def test_resolve_does_not_refuse_when_os_name_is_nt(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.object(module.os, "name", "nt"):
            with mock.patch.dict(os.environ, self._path(), clear=False):
                resolved = module.resolve("grok")
        self.assertIn(resolved["available"], (True, False))

    def test_subprocess_args_keep_direct_commands_as_a_list(self) -> None:
        module = self._load()
        with mock.patch.object(module.os, "name", "posix"):
            self.assertEqual(
                module._subprocess_args("/usr/bin/grok", ["--version"]),
                ["/usr/bin/grok", "--version"],
            )

    # ------------------------------------------------------------------
    # probe primitives
    # ------------------------------------------------------------------

    def test_probe_keeps_streams_and_exit_code_apart(self) -> None:
        path = self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP,
            {"models": (7, CURSOR_MODELS, "boom\n")},
        )
        module = self._load()
        probe = module._probe(str(path), ["models"])
        self.assertEqual(probe.returncode, 7)
        self.assertEqual(probe.stdout, CURSOR_MODELS)
        self.assertEqual(probe.stderr, "boom\n")

    def test_probe_returns_none_for_unusable_executable(self) -> None:
        module = self._load()
        self.assertIsNone(module._probe(str(self.bindir / "absent"), ["models"]))

    def test_run_keeps_merged_string_contract(self) -> None:
        path = self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP,
            {"models": (0, "out\n", "err\n")},
        )
        module = self._load()
        self.assertEqual(module._run(str(path), ["models"]), "out\n\nerr\n")
        self.assertEqual(module._run(str(self.bindir / "absent"), ["models"]), "")
        # _run is total: an argument _probe refuses is reported as failure, not raised.
        with mock.patch.object(module.os, "name", "nt"):
            self.assertEqual(module._run(r"C:\tools\grok.cmd", ["line\nbreak"]), "")

    # ------------------------------------------------------------------
    # help parsing helpers
    # ------------------------------------------------------------------

    def test_declares_requires_a_standalone_token(self) -> None:
        # Substring matching would confirm flags that the CLI never declared: `-p`
        # hides inside `--no-plan`, and `--model` inside the plural `--models`.
        module = self._load()
        self.assertIs(module._declares("      --no-plan\n", "-p"), False)
        self.assertIs(module._declares("      --models\n", "--model"), False)
        self.assertIs(module._declares("      --prompt-file <PATH>\n", "-p"), False)
        self.assertIs(module._declares("  -p, --single <PROMPT>\n", "-p"), True)
        self.assertIs(module._declares("      --model <model>\n", "--model"), True)
        self.assertIs(module._declares("      --no-plan\n", "--no-plan"), True)

    def test_model_list_commands_reads_declarations_only(self) -> None:
        module = self._load()
        self.assertEqual(module.model_list_commands(CURSOR_HELP), [["models"], ["--list-models"]])
        self.assertEqual(
            module.model_list_commands(CURSOR_HELP_MODELS_SUBCOMMAND_ONLY), [["models"]]
        )
        self.assertEqual(
            module.model_list_commands(CURSOR_HELP_LIST_MODELS_ONLY), [["--list-models"]]
        )
        self.assertEqual(module.model_list_commands(CURSOR_HELP_WITHOUT_MODEL_LIST), [])

    def test_parse_model_ids_keeps_the_bare_token_fixtures(self) -> None:
        # None of these inputs carries a column separator, so every line is judged
        # whole. This is the plan's original listing shape and it must keep working.
        module = self._load()
        self.assertEqual(module.parse_model_ids(CURSOR_MODELS), ["grok-4"])
        self.assertEqual(module.parse_model_ids(NO_GROK_MODELS), [])
        self.assertEqual(module.parse_model_ids(PROSE_ONLY_MODELS), [])
        self.assertEqual(
            module.parse_model_ids("grok-4-fast\n  grok-3 \ngrok-4-fast\nGrok 4\n"),
            ["grok-4-fast", "grok-3"],
        )

    def test_parse_model_ids_accepts_described_and_bare_ids(self) -> None:
        module = self._load()
        for text, expected in (
            # The shipped `<id> - <Description>` shape, ID returned exactly as printed.
            ("cursor-grok-4.6-high - Cursor Grok 4.6\n", ["cursor-grok-4.6-high"]),
            (
                "cursor-grok-4.6-xhigh-fast - Cursor Grok 4.6 Extra High Fast\n",
                ["cursor-grok-4.6-xhigh-fast"],
            ),
            # A bare token on its own line is still a legitimate listing shape.
            ("grok-4\n", ["grok-4"]),
            ("grok-4 - Grok 4\n", ["grok-4"]),
        ):
            with self.subTest(text=text):
                self.assertEqual(module.parse_model_ids(text), expected)

    def test_parse_model_ids_accepts_a_whitespace_column_gap(self) -> None:
        # A listing may separate the columns by alignment rather than by ` - `.
        # Catches: narrowing the separator back to ` - ` alone (either alternative
        # removed leaves one of these lines unparsed and the backend unusable).
        module = self._load()
        for label, text, expected in (
            ("aligned spaces", "cursor-grok-4.6-high    Cursor Grok 4.6\n", ["cursor-grok-4.6-high"]),
            ("single tab", "cursor-grok-4.6-low\tCursor Grok 4.6 Low\n", ["cursor-grok-4.6-low"]),
            ("tab run", "grok-4\t\tGrok 4\n", ["grok-4"]),
            # Whitespace before a ` - ` is part of the column gap, not part of the ID.
            ("padded dash", "cursor-grok-4.6-high  - Cursor Grok 4.6\n", ["cursor-grok-4.6-high"]),
            ("tab then dash", "cursor-grok-4.6-xhigh\t - Cursor Grok 4.6 XHigh\n",
             ["cursor-grok-4.6-xhigh"]),
        ):
            with self.subTest(gap=label):
                self.assertEqual(module.parse_model_ids(text), expected)
        self.assertEqual(
            module.parse_model_ids(
                "Available models\n"
                "\n"
                "auto            Auto (default)\n"
                "cursor-grok-9.1-high-fast   Cursor Grok 9.1 Fast\n"
                "composer-2.5    Grok-like reasoning\n"
                "cursor-grok-9.1-low         Cursor Grok 9.1 Low\n"
            ),
            ["cursor-grok-9.1-high-fast", "cursor-grok-9.1-low"],
        )

    def test_parse_model_ids_ignores_a_description_behind_a_whitespace_gap(self) -> None:
        # The widened separator must not widen what is read: the description is still
        # never examined. Catches: testing the whole line for `grok` instead of the ID
        # column, which the column-gap shape would otherwise make easy to slip in.
        module = self._load()
        for label, text in (
            ("aligned spaces", "composer-2.5    Grok-like reasoning\n"),
            ("single tab", "composer-2.5\tGrok-like reasoning\n"),
            ("grok late in the description", "auto      Auto, unlike grok models\n"),
        ):
            with self.subTest(rejects=label):
                self.assertEqual(module.parse_model_ids(text), [])

    def test_parse_model_ids_rejects_option_shaped_candidates(self) -> None:
        # `_MODEL_ID` must start alphanumeric: an ID beginning with `-` would be read
        # as an option rather than a value by the CLI it is handed to, and `.`/`_`
        # starts are listing decoration, not identifiers. Catches: dropping the
        # mandatory leading character class from `_MODEL_ID`.
        module = self._load()
        for candidate in ("-grok-4", ".grok-4", "_grok-4", "--grok-4"):
            with self.subTest(rejects=candidate):
                self.assertEqual(module.parse_model_ids(f"{candidate} - Grok 4\n"), [])
                self.assertEqual(module.parse_model_ids(f"{candidate}\n"), [])
        # The same line without the leading punctuation is accepted, so the rejection
        # above is the leading class and nothing else.
        self.assertEqual(module.parse_model_ids("grok-4 - Grok 4\n"), ["grok-4"])

    def test_parse_model_ids_matches_grok_case_insensitively_and_keeps_the_text(self) -> None:
        # Catches: deleting `.lower()` from the containment test, and any mutation that
        # stores a case-folded copy instead of the ID the CLI printed.
        module = self._load()
        self.assertEqual(
            module.parse_model_ids("cursor-Grok-4.6-high - Cursor Grok 4.6\n"),
            ["cursor-Grok-4.6-high"],
        )
        self.assertEqual(module.parse_model_ids("GROK-4\n"), ["GROK-4"])

    def test_parse_model_ids_rejects_descriptions_headers_and_prose(self) -> None:
        module = self._load()
        for label, text in (
            # No `grok` in the ID column.
            ("auto", "auto - Auto (default)\n"),
            ("gpt", "gpt-5.3-codex-low - Codex 5.3 Low\n"),
            ("composer", "composer-2.5 - Composer 2.5\n"),
            ("kimi", "kimi-k3-low - Kimi K3 Low\n"),
            # `grok` only in the description: the ID column is all the rule ever sees.
            ("description mentions grok", "composer-2.5 - Grok-like reasoning\n"),
            ("header", "Available models\n"),
            ("prose", "Available models include grok and others\n"),
            (
                "tip paragraph",
                "Tip: use --model <id> (or /model <id> in interactive mode) to switch."
                " Parameterized models also accept quoted overrides, e.g."
                " --model 'claude-opus-4-8[context=1m,effort=high,fast=false]'.\n",
            ),
            ("blank lines", "\n   \n\n"),
        ):
            with self.subTest(rejects=label):
                self.assertEqual(module.parse_model_ids(text), [])

    def test_parse_model_ids_keeps_source_order_without_duplicates(self) -> None:
        module = self._load()
        self.assertEqual(
            module.parse_model_ids(CURSOR_MODELS_LISTING), CURSOR_MODELS_LISTING_IDS
        )
        self.assertEqual(
            module.parse_model_ids(
                "cursor-grok-9.1-high - Cursor Grok 9.1\n"
                "cursor-grok-9.1-low - Cursor Grok 9.1 Low\n"
                "cursor-grok-9.1-high - Cursor Grok 9.1\n"
            ),
            ["cursor-grok-9.1-high", "cursor-grok-9.1-low"],
        )

    # ------------------------------------------------------------------
    # grok backend
    # ------------------------------------------------------------------

    def test_grok_available_uses_grok_binary_only(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP)
        self._write_cli("agent", GROK_VERSION, GROK_HELP)
        result = self._resolve("g")
        self.assertTrue(result["available"])
        self.assertEqual(result["backend"], "grok")
        self.assertEqual(result["reason"], None)
        self.assertEqual(Path(result["executable"]).stem, "grok")
        self.assertIn("--no-plan", result["argv_prefix"])
        self.assertIn("--no-subagents", result["argv_prefix"])
        self.assertIn("--always-approve", result["argv_prefix"])
        self.assertIn("--disable-web-search", result["argv_prefix"])
        self.assertNotIn("--worktree", result["argv_prefix"])

    def test_grok_removes_mcp_tools(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP)
        argv = self._resolve("grok")["argv_prefix"]
        self.assertIn("--disallowed-tools", argv)
        self.assertEqual(argv[argv.index("--disallowed-tools") + 1], "search_tool,use_tool")
        self.assertIn("--deny", argv)
        self.assertEqual(argv[argv.index("--deny") + 1], "MCPTool(*)")

    def test_grok_without_value_taking_tool_filters_is_unavailable(self) -> None:
        for declaration in ("--disallowed-tools <TOOLS>", "--deny <RULE>"):
            for replacement in ("", declaration.split()[0]):
                with self.subTest(declaration=declaration, replacement=replacement):
                    help_text = GROK_HELP.replace(declaration, replacement)
                    self._write_cli("grok", GROK_VERSION, help_text)
                    result = self._resolve("grok")
                    self.assertFalse(result["available"])
                    self.assertEqual(result["reason"], "missing_flags")

    def test_grok_launch_contract(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP)
        result = self._resolve("grok")
        self.assertEqual(
            result["launch"],
            {
                "cwd_flag": "--cwd",
                "prompt_flag": "--single",
                "effort_flag": "--reasoning-effort",
                "output_format": "streaming-messages-json",
            },
        )
        self.assertEqual(result["model_ids"], [])

    def test_grok_prefers_prompt_file(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP_WITH_PROMPT_FILE)
        self.assertEqual(self._resolve("grok")["launch"]["prompt_flag"], "--prompt-file")

    def test_grok_falls_back_to_short_prompt_flag(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP_WITH_SHORT_PROMPT_ONLY)
        self.assertEqual(self._resolve("grok")["launch"]["prompt_flag"], "-p")

    def test_grok_prompt_file_without_short_flag(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP_PROMPT_FILE_ONLY)
        self.assertEqual(self._resolve("grok")["launch"]["prompt_flag"], "--prompt-file")

    def test_grok_without_any_prompt_flag_is_missing_flags(self) -> None:
        # `--no-plan` is still declared, so only standalone-token matching rejects this.
        self._write_cli("grok", GROK_VERSION, GROK_HELP_WITHOUT_PROMPT_FLAG)
        result = self._resolve("grok")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "missing_flags")

    def test_grok_uses_confirmed_effort_alias(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP_WITH_EFFORT_ALIAS)
        self.assertEqual(self._resolve("grok")["launch"]["effort_flag"], "--effort")

    def test_grok_without_streaming_output_is_missing_flags(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP_WITHOUT_OUTPUT_FORMAT)
        result = self._resolve("grok")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "missing_flags")

    def test_grok_format_value_without_the_option_is_missing_flags(self) -> None:
        # The value token alone does not prove `--output-format` exists, and
        # `build_argv` emits that option on every launch.
        self._write_cli(
            "grok", GROK_VERSION, GROK_HELP_FORMAT_VALUE_UNDER_OTHER_OPTION
        )
        result = self._resolve("grok")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "missing_flags")
        self.assertIsNone(result["launch"])
        self.assertIsNone(result["argv_prefix"])

    def test_agent_only_grok_is_not_found_for_grok_backend(self) -> None:
        self._write_cli("agent", GROK_VERSION, GROK_HELP)
        result = self._resolve("grok")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "not_found")
        self.assertIsNone(result["executable"])
        self.assertIsNone(result["argv_prefix"])

    def test_agent_is_never_cursor(self) -> None:
        self._write_cli("agent", GROK_VERSION, GROK_HELP)
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "not_found")

    def test_missing_flags(self) -> None:
        self._write_cli("grok", GROK_VERSION, "Usage: grok\n")
        result = self._resolve("grok")
        self.assertEqual(result["reason"], "missing_flags")
        self.assertFalse(result["available"])

    def test_grok_help_without_cwd_is_missing_flags(self) -> None:
        self._write_cli("grok", GROK_VERSION, GROK_HELP_WITHOUT_CWD)
        result = self._resolve("grok")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "missing_flags")

    def test_required_execution_flags_cannot_be_missing(self):
        for flag in ("--rules", "--sandbox", "--disable-web-search"):
            help_text = "\n".join(
                line for line in GROK_HELP.splitlines() if flag not in line
            )
            with self.subTest(flag=flag):
                self._write_cli("grok", GROK_VERSION, help_text)
                result = self._resolve("grok")
                self.assertFalse(result["available"])
                self.assertEqual(result["reason"], "missing_flags")

    # ------------------------------------------------------------------
    # cursor backend
    # ------------------------------------------------------------------

    def test_cursor_available_requires_grok_model(self) -> None:
        self._write_cli(
            "cursor-agent", CURSOR_VERSION, CURSOR_HELP, {"models": (0, CURSOR_MODELS, "")}
        )
        result = self._resolve("cursor")
        self.assertTrue(result["available"])
        self.assertEqual(result["backend"], "cursor")
        self.assertIn("--print", result["argv_prefix"])
        self.assertNotIn("--force", result["argv_prefix"])
        self.assertNotIn("--yolo", result["argv_prefix"])
        self.assertIn("--trust", result["argv_prefix"])
        self.assertNotIn("--plugin-dir", result["argv_prefix"])
        self.assertNotIn("--worktree", result["argv_prefix"])
        self.assertEqual(
            result["argv_prefix"][1:],
            ["--print", "--trust", "--auto-review", "--sandbox", "enabled"],
        )

    def test_cursor_contract(self) -> None:
        self._write_cli(
            "cursor-agent", CURSOR_VERSION, CURSOR_HELP, {"models": (0, CURSOR_MODELS, "")}
        )
        result = self._resolve("cursor")
        self.assert_cursor_contract(result)
        self.assertEqual(result["launch"]["cwd_flag"], "--workspace")

    def test_cursor_accepts_the_real_listing_format(self) -> None:
        # Regression: the shipped parser required the whole stripped line to be one
        # bare `grok...` token, so every `<id> - <Description>` line the real CLI
        # prints was dropped and the backend resolved `no_grok_model`.
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP,
            {
                "models": (0, CURSOR_MODELS_LISTING, ""),
                "--list-models": (0, CURSOR_MODELS_LISTING, ""),
            },
        )
        result = self._resolve("cursor")
        self.assertIs(result["available"], True)
        self.assertIsNone(result["reason"])
        self.assertEqual(result["model_ids"], CURSOR_MODELS_LISTING_IDS)
        self.assertEqual(
            result["argv_prefix"][1:],
            ["--print", "--trust", "--auto-review", "--sandbox", "enabled"],
        )
        self.assertEqual(result["launch"]["output_format"], "stream-json")
        self.assertEqual(self._calls(), ["models"])

    def test_cursor_cwd_flag_falls_back_to_cwd(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_WITH_CWD,
            {"models": (0, CURSOR_MODELS, "")},
        )
        self.assertEqual(self._resolve("cursor")["launch"]["cwd_flag"], "--cwd")

    def test_cursor_unavailable_payload_is_empty(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP,
            {"models": (0, NO_GROK_MODELS, ""), "--list-models": (0, NO_GROK_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_grok_model")
        self.assertIsNone(result["launch"])
        self.assertEqual(result["model_ids"], [])
        self.assertEqual(self._calls(), ["models", "--list-models"])

    def test_cursor_without_grok_model(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_MODELS_SUBCOMMAND_ONLY,
            {"models": (0, NO_GROK_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_grok_model")

    def test_cursor_rejects_prose_mentioning_grok(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_MODELS_SUBCOMMAND_ONLY,
            {"models": (0, PROSE_ONLY_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_grok_model")

    def test_cursor_plural_models_option_is_not_a_model_flag(self) -> None:
        # `--models` is not `--model`; only standalone-token matching rejects this.
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_PLURAL_MODEL_ONLY,
            {"models": (0, CURSOR_MODELS, ""), "--list-models": (0, CURSOR_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "missing_flags")
        self.assertEqual(self._calls(), [])

    def test_cursor_format_value_without_the_option_is_missing_flags(self) -> None:
        # The value token alone does not prove `--output-format` exists, and
        # `build_argv` emits that option on every launch.
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_FORMAT_VALUE_UNDER_OTHER_OPTION,
            {"models": (0, CURSOR_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "missing_flags")
        self.assertIsNone(result["launch"])
        self.assertEqual(result["model_ids"], [])
        self.assertEqual(self._calls(), [], "probed models despite missing flags")

    def test_cursor_print_flag_falls_back_to_short_flag(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_SHORT_PRINT_ONLY,
            {"models": (0, CURSOR_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertTrue(result["available"])
        self.assertEqual(
            result["argv_prefix"][1:],
            ["-p", "--trust", "--auto-review", "--sandbox", "enabled"],
        )
        self.assertNotIn("--print", result["argv_prefix"])

    def test_cursor_named_binary_with_grok_identity_is_mismatch(self) -> None:
        self._write_cli("cursor-agent", GROK_VERSION, GROK_HELP)
        result = self._resolve("c")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "identity_mismatch")
        self.assertIsNone(result["executable"])
        self.assertIsNone(result["launch"])
        self.assertEqual(result["model_ids"], [])

    def test_cursor_binary_with_cursor_identity_is_available(self) -> None:
        self._write_cli(
            "cursor", CURSOR_VERSION, CURSOR_HELP, {"models": (0, CURSOR_MODELS, "")}
        )
        result = self._resolve("cursor")
        self.assertTrue(result["available"])
        self.assertEqual(Path(result["executable"]).stem, "cursor")

    def test_cursor_binary_with_grok_identity_is_not_adopted(self) -> None:
        self._write_cli("cursor", GROK_VERSION, GROK_HELP)
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertIn(result["reason"], ("not_found", "identity_mismatch"))

    def test_cursor_missing_narrow_flags_is_missing_flags(self) -> None:
        cases = {
            "auto-review": CURSOR_HELP_WITHOUT_AUTO_REVIEW,
            "sandbox": CURSOR_HELP_WITHOUT_SANDBOX,
            "stream-json": CURSOR_HELP_WITHOUT_STREAM_JSON,
        }
        for label, help_text in cases.items():
            with self.subTest(missing=label):
                self._write_cli(
                    "cursor-agent",
                    CURSOR_VERSION,
                    help_text,
                    {"models": (0, CURSOR_MODELS, "")},
                )
                result = self._resolve("cursor")
                self.assertFalse(result["available"])
                self.assertEqual(result["reason"], "missing_flags")
                self.assertIsNone(result["launch"])
                self.assertEqual(result["model_ids"], [])
                self.assertEqual(self._calls(), [], "probed models despite missing flags")

    # ------------------------------------------------------------------
    # model list adjudication
    # ------------------------------------------------------------------

    def test_model_list_failure_exit_code_is_rejected(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_MODELS_SUBCOMMAND_ONLY,
            {"models": (7, CURSOR_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_grok_model")
        self.assertEqual(self._calls(), ["models"])

    def test_model_list_stderr_is_not_adopted(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_MODELS_SUBCOMMAND_ONLY,
            {"models": (0, "", CURSOR_MODELS)},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_grok_model")

    def test_model_list_falls_back_to_second_declared_alias(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP,
            {
                "models": (7, "", "not supported here\n"),
                "--list-models": (0, CURSOR_MODELS, ""),
            },
        )
        result = self._resolve("cursor")
        self.assert_cursor_contract(result)
        self.assertEqual(self._calls(), ["models", "--list-models"])

    def test_model_list_stops_after_first_success(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP,
            {
                "models": (0, CURSOR_MODELS, ""),
                "--list-models": (0, CURSOR_MODELS, ""),
            },
        )
        result = self._resolve("cursor")
        self.assert_cursor_contract(result)
        self.assertEqual(self._calls(), ["models"])

    def test_undeclared_list_models_option_is_never_probed(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_MODELS_SUBCOMMAND_ONLY,
            {"models": (0, CURSOR_MODELS, ""), "--list-models": (0, CURSOR_MODELS, "")},
        )
        self.assert_cursor_contract(self._resolve("cursor"))
        self.assertEqual(self._calls(), ["models"])

    def test_undeclared_models_subcommand_is_never_probed(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_LIST_MODELS_ONLY,
            {"models": (0, CURSOR_MODELS, ""), "--list-models": (0, CURSOR_MODELS, "")},
        )
        self.assert_cursor_contract(self._resolve("cursor"))
        self.assertEqual(self._calls(), ["--list-models"])

    def test_no_declared_model_list_command_skips_the_probe(self) -> None:
        self._write_cli(
            "cursor-agent",
            CURSOR_VERSION,
            CURSOR_HELP_WITHOUT_MODEL_LIST,
            {"models": (0, CURSOR_MODELS, ""), "--list-models": (0, CURSOR_MODELS, "")},
        )
        result = self._resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_grok_model")
        self.assertEqual(self._calls(), [])

    # ------------------------------------------------------------------
    # cli
    # ------------------------------------------------------------------

    def test_cli_unknown_backend_exits_2(self) -> None:
        from io import StringIO

        module = self._load()
        with mock.patch("sys.stderr", new=StringIO()):
            self.assertEqual(module.main(["--backend", "warp", "--json"]), 2)

    def test_cli_json_line_for_missing_backend(self) -> None:
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            from io import StringIO
            buf = StringIO()
            with mock.patch("sys.stdout", buf):
                code = module.main(["--backend", "grok", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["available"], False)
        self.assertEqual(payload["reason"], "not_found")
        self.assertIsNone(payload["launch"])
        self.assertEqual(payload["model_ids"], [])
        self.assertTrue(buf.getvalue().endswith("\n"))
