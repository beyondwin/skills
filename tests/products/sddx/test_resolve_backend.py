from __future__ import annotations

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
      --always-approve
      --reasoning-effort <EFFORT>
      --disable-web-search
      --sandbox <PROFILE>
      --rules <RULES>
  -p, --single <PROMPT>
  -r, --resume [<SESSION_ID>]
"""
GROK_HELP_WITHOUT_CWD = """
Usage: grok [OPTIONS]
      --no-plan
      --no-subagents
      --always-approve
      --reasoning-effort <EFFORT>
      --disable-web-search
      --sandbox <PROFILE>
      --rules <RULES>
  -p, --single <PROMPT>
  -r, --resume [<SESSION_ID>]
"""
CURSOR_VERSION = "cursor-agent 2026.08.07\n"
CURSOR_HELP = """
Usage: cursor-agent [options]
  -p, --print
  -f, --force
      --yolo
      --trust
      --workspace <path>
      --model <model>
      --resume [chatId]
      --list-models
"""
CURSOR_MODELS = "gpt-5\ncomposer\ngrok-4\n"
NO_GROK_MODELS = "gpt-5\ncomposer\n"


def _cli_body(version: str, help_text: str, models: str) -> str:
    return (
        "import sys\n"
        f"VERSION = {version!r}\n"
        f"HELP = {help_text!r}\n"
        f"MODELS = {models!r}\n"
        "args = sys.argv[1:]\n"
        "if args[:1] in (['--version'], ['-v']):\n"
        "    sys.stdout.write(VERSION)\n"
        "    raise SystemExit(0)\n"
        "if args[:1] in (['--help'], ['-h']) or not args:\n"
        "    sys.stdout.write(HELP)\n"
        "    raise SystemExit(0)\n"
        "if args[:1] == ['models'] or args[:1] == ['--list-models']:\n"
        "    sys.stdout.write(MODELS)\n"
        "    raise SystemExit(0)\n"
        "sys.stderr.write('unexpected\\n')\n"
        "raise SystemExit(2)\n"
    )


def _write_cli(directory: Path, name: str, version: str, help_text: str, models: str = "") -> Path:
    body = _cli_body(version, help_text, models)
    if os.name == "nt":
        script = directory / f"{name}.py"
        script.write_text(body, encoding="utf-8")
        path = directory / f"{name}.cmd"
        path.write_text(
            f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n',
            encoding="utf-8",
        )
        return path
    path = directory / name
    path.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class ResolveBackendTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.bindir = Path(self.tmpdir.name)
        sys.path.insert(0, str(SCRIPTS))
        self.addCleanup(lambda: sys.path.remove(str(SCRIPTS)) if str(SCRIPTS) in sys.path else None)

    def _path(self, *names: str) -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = str(self.bindir)
        return env

    def _load(self):
        import importlib

        if "resolve_backend" in sys.modules:
            del sys.modules["resolve_backend"]
        return importlib.import_module("resolve_backend")

    def test_fixture_cli_is_discoverable_on_path(self) -> None:
        _write_cli(self.bindir, "grok", GROK_VERSION, GROK_HELP)
        with mock.patch.dict(os.environ, self._path(), clear=False):
            found = shutil.which("grok")
        self.assertIsNotNone(found)
        self.assertEqual(Path(found).stem, "grok")

    def test_windows_cmd_wrapper_is_invoked_through_comspec(self) -> None:
        module = self._load()
        with mock.patch.object(module.os, "name", "nt"):
            with mock.patch.dict(module.os.environ, {"ComSpec": r"C:\Windows\system32\cmd.exe"}, clear=False):
                command = module._command(r"C:\tools\grok.cmd", ["--version"])
        self.assertEqual(command[:4], [r"C:\Windows\system32\cmd.exe", "/d", "/s", "/c"])
        self.assertIn("grok.cmd", command[4])
        self.assertIn("--version", command[4])

    def test_windows_exe_is_invoked_directly(self) -> None:
        module = self._load()
        with mock.patch.object(module.os, "name", "nt"):
            command = module._command(r"C:\tools\grok.exe", ["--version"])
        self.assertEqual(command, [r"C:\tools\grok.exe", "--version"])

    @unittest.skipUnless(os.name == "nt", "cmd.exe PATH wrappers are a Windows lookup")
    def test_windows_cmd_fixture_prints_grok_version(self) -> None:
        path = _write_cli(self.bindir, "grok", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            text = module._run(str(path), ["--version"])
        self.assertIn("grok 1.0.25", text)

    def test_grok_available_uses_grok_binary_only(self) -> None:
        _write_cli(self.bindir, "grok", GROK_VERSION, GROK_HELP)
        _write_cli(self.bindir, "agent", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("g")
        self.assertTrue(result["available"])
        self.assertEqual(result["backend"], "grok")
        self.assertEqual(result["reason"], None)
        self.assertEqual(Path(result["executable"]).stem, "grok")
        self.assertIn("--no-plan", result["argv_prefix"])
        self.assertIn("--no-subagents", result["argv_prefix"])
        self.assertIn("--always-approve", result["argv_prefix"])
        self.assertIn("--disable-web-search", result["argv_prefix"])
        self.assertNotIn("--worktree", result["argv_prefix"])

    def test_agent_only_grok_is_not_found_for_grok_backend(self) -> None:
        _write_cli(self.bindir, "agent", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("grok")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "not_found")
        self.assertIsNone(result["executable"])
        self.assertIsNone(result["argv_prefix"])

    def test_agent_is_never_cursor(self) -> None:
        _write_cli(self.bindir, "agent", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "not_found")

    def test_cursor_named_binary_with_grok_identity_is_mismatch(self) -> None:
        _write_cli(self.bindir, "cursor-agent", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("c")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "identity_mismatch")
        self.assertIsNone(result["executable"])

    def test_cursor_available_requires_grok_model(self) -> None:
        _write_cli(self.bindir, "cursor-agent", CURSOR_VERSION, CURSOR_HELP, CURSOR_MODELS)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("cursor")
        self.assertTrue(result["available"])
        self.assertEqual(result["backend"], "cursor")
        self.assertIn("--print", result["argv_prefix"])
        self.assertTrue("--force" in result["argv_prefix"] or "--yolo" in result["argv_prefix"])
        self.assertIn("--trust", result["argv_prefix"])
        self.assertNotIn("--plugin-dir", result["argv_prefix"])
        self.assertNotIn("--worktree", result["argv_prefix"])

    def test_cursor_without_grok_model(self) -> None:
        _write_cli(self.bindir, "cursor-agent", CURSOR_VERSION, CURSOR_HELP, NO_GROK_MODELS)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("cursor")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "no_grok_model")

    def test_missing_flags(self) -> None:
        _write_cli(self.bindir, "grok", GROK_VERSION, "Usage: grok\n")
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("grok")
        self.assertEqual(result["reason"], "missing_flags")
        self.assertFalse(result["available"])

    def test_grok_help_without_cwd_is_missing_flags(self) -> None:
        _write_cli(self.bindir, "grok", GROK_VERSION, GROK_HELP_WITHOUT_CWD)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("grok")
        self.assertFalse(result["available"])
        self.assertEqual(result["reason"], "missing_flags")

    def test_required_execution_flags_cannot_be_missing(self):
        module = self._load()
        for flag in ("--rules", "--sandbox", "--disable-web-search"):
            help_text = "\n".join(
                line for line in GROK_HELP.splitlines() if flag not in line
            )
            with self.subTest(flag=flag):
                _write_cli(self.bindir, "grok", GROK_VERSION, help_text)
                with mock.patch.dict(os.environ, self._path(), clear=False):
                    result = module.resolve("grok")
                self.assertFalse(result["available"])
                self.assertEqual(result["reason"], "missing_flags")

    def test_cursor_binary_with_cursor_identity_is_available(self) -> None:
        _write_cli(self.bindir, "cursor", CURSOR_VERSION, CURSOR_HELP, CURSOR_MODELS)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("cursor")
        self.assertTrue(result["available"])
        self.assertEqual(Path(result["executable"]).stem, "cursor")

    def test_cursor_binary_with_grok_identity_is_not_adopted(self) -> None:
        _write_cli(self.bindir, "cursor", GROK_VERSION, GROK_HELP)
        module = self._load()
        with mock.patch.dict(os.environ, self._path(), clear=False):
            result = module.resolve("cursor")
        self.assertFalse(result["available"])
        self.assertIn(result["reason"], ("not_found", "identity_mismatch"))

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
        self.assertTrue(buf.getvalue().endswith("\n"))
