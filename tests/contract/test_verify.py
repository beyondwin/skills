from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
VERIFY_PATH = ROOT / "scripts" / "verify.py"
FULL_STAGE_NAMES = (
    "contract",
    "korean-offline",
    "image-contract",
    "image-inspector",
    "korean-live-unit",
    "korean-live-dry-run",
    "python-compile",
)
WINDOWS_STAGE_NAMES = (
    "contract",
    "korean-offline",
    "korean-live-unit",
    "korean-live-dry-run",
    "python-compile",
)


def load_verify() -> ModuleType:
    name = "scripts.verify"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, VERIFY_PATH)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(VERIFY_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class VerifyModuleTests(unittest.TestCase):
    def test_verify_module_exists(self) -> None:
        self.assertTrue(VERIFY_PATH.is_file(), "scripts.verify does not exist")


class VerifyStageTests(unittest.TestCase):
    def _load(self) -> ModuleType:
        self.assertTrue(VERIFY_PATH.is_file(), "scripts.verify does not exist")
        return load_verify()

    def test_full_profile_contains_all_provider_free_gates(self) -> None:
        verify = self._load()
        names = [stage.name for stage in verify.stages("full")]
        self.assertEqual(names, list(FULL_STAGE_NAMES))

    def test_windows_profile_excludes_codex_only_image_gate(self) -> None:
        verify = self._load()
        names = [stage.name for stage in verify.stages("windows-portable")]
        self.assertNotIn("image-contract", names)
        self.assertNotIn("image-inspector", names)

    def test_windows_profile_contains_portable_gates_in_order(self) -> None:
        verify = self._load()
        names = [stage.name for stage in verify.stages("windows-portable")]
        self.assertEqual(names, list(WINDOWS_STAGE_NAMES))

    def test_unknown_profile_is_rejected(self) -> None:
        verify = self._load()
        with self.assertRaises(ValueError):
            verify.stages("linux")

    def test_contract_discovery_runs_first(self) -> None:
        verify = self._load()
        for profile in ("full", "windows-portable"):
            stages = verify.stages(profile)
            self.assertTrue(stages)
            self.assertEqual(stages[0].name, "contract")
            argv = stages[0].argv
            self.assertEqual(argv[0], sys.executable)
            self.assertEqual(argv[1:4], ("-m", "unittest", "discover"))
            self.assertIn("tests/contract", argv)

    def test_every_stage_uses_sys_executable_and_list_argv(self) -> None:
        verify = self._load()
        for profile in ("full", "windows-portable"):
            for stage in verify.stages(profile):
                self.assertIsInstance(stage.argv, tuple)
                self.assertTrue(stage.argv, stage.name)
                self.assertEqual(stage.argv[0], sys.executable)
                self.assertEqual(stage.cwd, verify.ROOT)
                joined = " ".join(stage.argv)
                self.assertNotIn("&&", joined)
                self.assertNotIn("|", joined)
                self.assertNotIn(";", joined)

    def test_korean_offline_runs_full_scope_evaluator(self) -> None:
        stage = self._stage("full", "korean-offline")
        self.assertEqual(stage.argv[0], sys.executable)
        self.assertTrue(stage.argv[1].replace("\\", "/").endswith(
            "tests/korean-writing-editor/offline/run.py"
        ))
        self.assertIn("--scope", stage.argv)
        self.assertIn("full", stage.argv)

    def test_image_contract_runs_full_scope_evaluator(self) -> None:
        stage = self._stage("full", "image-contract")
        self.assertTrue(stage.argv[1].replace("\\", "/").endswith(
            "tests/image-workbench/run.py"
        ))
        self.assertIn("--scope", stage.argv)
        self.assertIn("full", stage.argv)

    def test_image_inspector_discovers_external_inspector_tests(self) -> None:
        stage = self._stage("full", "image-inspector")
        self.assertEqual(stage.argv[1:4], ("-m", "unittest", "discover"))
        self.assertIn("tests/image-workbench", stage.argv)

    def test_korean_live_unit_discovers_live_tests(self) -> None:
        stage = self._stage("windows-portable", "korean-live-unit")
        self.assertEqual(stage.argv[1:4], ("-m", "unittest", "discover"))
        self.assertIn("tests/korean-writing-editor/live", stage.argv)

    def test_korean_live_dry_run_is_dry_run_only(self) -> None:
        stage = self._stage("full", "korean-live-dry-run")
        self.assertTrue(stage.argv[1].replace("\\", "/").endswith(
            "tests/korean-writing-editor/live/live_matrix.py"
        ))
        self.assertIn("--dry-run", stage.argv)
        self.assertNotIn("--execute", stage.argv)
        self.assertNotIn("--preflight", stage.argv)

    def test_no_stage_invokes_live_execute(self) -> None:
        verify = self._load()
        for profile in ("full", "windows-portable"):
            for stage in verify.stages(profile):
                self.assertNotIn("--execute", stage.argv)
                self.assertNotIn("--preflight", stage.argv)

    def test_python_compile_covers_scripts_skill_scripts_and_tests(self) -> None:
        stage = self._stage("full", "python-compile")
        self.assertEqual(stage.argv[1:3], ("-m", "compileall"))
        paths = [part.replace("\\", "/") for part in stage.argv[3:]]
        self.assertTrue(any(part == "scripts" or part.endswith("/scripts") for part in paths))
        self.assertIn("tests", paths)
        self.assertTrue(
            any(part.endswith("skills/image-workbench/scripts") for part in paths),
            paths,
        )
        self.assertFalse(any("*" in part for part in stage.argv))

    def test_run_stage_returns_subprocess_exit_code(self) -> None:
        verify = self._load()
        ok = verify.Stage(
            "contract",
            (sys.executable, "-c", "raise SystemExit(0)"),
            cwd=ROOT,
        )
        failed = verify.Stage(
            "korean-offline",
            (sys.executable, "-c", "raise SystemExit(5)"),
            cwd=ROOT,
        )
        self.assertEqual(verify.run_stage(ok), 0)
        self.assertEqual(verify.run_stage(failed), 5)

    def test_fail_fast_stops_and_names_the_failed_stage(self) -> None:
        verify = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "later-stage-ran"
            stages = (
                verify.Stage(
                    "contract",
                    (sys.executable, "-c", "raise SystemExit(0)"),
                    cwd=ROOT,
                ),
                verify.Stage(
                    "korean-offline",
                    (sys.executable, "-c", "raise SystemExit(3)"),
                    cwd=ROOT,
                ),
                verify.Stage(
                    "python-compile",
                    (
                        sys.executable,
                        "-c",
                        "from pathlib import Path; Path(r'%s').write_text('ran', encoding='utf-8')"
                        % marker,
                    ),
                    cwd=ROOT,
                ),
            )
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                code = verify.run_stages(stages)
            self.assertEqual(code, 3)
            self.assertIn("korean-offline", stderr.getvalue())
            self.assertFalse(marker.exists())

    def test_cli_rejects_unknown_profile(self) -> None:
        verify = self._load()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                verify.main(["--profile", "linux"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_cli_defaults_to_full_profile(self) -> None:
        verify = self._load()
        recorded: list[str] = []
        original = verify.stages

        def fake_stages(profile: str):
            recorded.append(profile)
            return ()

        verify.stages = fake_stages  # type: ignore[method-assign]
        try:
            self.assertEqual(verify.main([]), 0)
        finally:
            verify.stages = original  # type: ignore[method-assign]
        self.assertEqual(recorded, ["full"])

    def _stage(self, profile: str, name: str):
        verify = self._load()
        for stage in verify.stages(profile):
            if stage.name == name:
                return stage
        self.fail(f"profile {profile!r} is missing stage {name!r}")


if __name__ == "__main__":
    unittest.main()
