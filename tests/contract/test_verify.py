from __future__ import annotations

import ast
import builtins
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
LIVE_TEST_PATH = (
    ROOT / "tests" / "korean-writing-editor" / "live" / "test_live_matrix.py"
)
REQUIRED_UNIX_ONLY_LIVE_TESTS = (
    "test_manifest_ignores_only_validated_regenerated_python_cache",
    "test_manifest_rejects_every_unsafe_python_cache_shape",
    "test_fd_relative_manifest_matches_canonical_hash_and_rejects_specials",
    "test_reuse_rechecks_evidence_names_after_intervening_validation",
    "test_first_preflight_rejects_every_incomplete_or_unsafe_install_bootstrap",
    "test_held_evidence_read_rejects_same_size_rewrite_during_validation",
    "test_report_lease_binds_directory_target_inode_hash_and_state",
    "test_manifest_hash_rejects_symlink",
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

    def test_graspic_selection_runs_only_shared_and_graspic_gates(self) -> None:
        verify = self._load()
        names = [stage.name for stage in verify.stages("full", skill="graspic")]
        self.assertEqual(names, ["product-contract", "graspic-contract", "python-compile"])

    def test_catalog_selection_runs_catalog_gates_only(self) -> None:
        verify = self._load()
        names = [stage.name for stage in verify.stages("full", catalog=True)]
        self.assertEqual(
            names,
            [
                "catalog-contract",
                "catalog-release-contract",
                "public-docs",
                "python-compile",
            ],
        )

    def test_skill_and_catalog_are_mutually_exclusive(self) -> None:
        verify = self._load()
        with self.assertRaises(ValueError):
            verify.stages("full", skill="graspic", catalog=True)

    def test_korean_selection_runs_only_shared_and_korean_gates(self) -> None:
        verify = self._load()
        names = [
            stage.name
            for stage in verify.stages("full", skill="korean-writing-editor")
        ]
        self.assertEqual(
            names,
            [
                "product-contract",
                "korean-package",
                "korean-offline",
                "korean-live-unit",
                "korean-live-dry-run",
                "python-compile",
            ],
        )

    def test_image_selection_runs_only_shared_and_image_gates(self) -> None:
        verify = self._load()
        names = [
            stage.name for stage in verify.stages("full", skill="image-workbench")
        ]
        self.assertEqual(
            names,
            [
                "product-contract",
                "image-contract",
                "image-inspector",
                "python-compile",
            ],
        )

    def test_windows_profile_excludes_image_gates_after_skill_selection(self) -> None:
        verify = self._load()
        names = [
            stage.name
            for stage in verify.stages("windows-portable", skill="image-workbench")
        ]
        self.assertEqual(names, ["product-contract", "python-compile"])
        self.assertNotIn("image-contract", names)
        self.assertNotIn("image-inspector", names)

    def test_product_contract_runs_release_contract_module(self) -> None:
        stage = self._stage("full", "product-contract", skill="graspic")
        self.assertEqual(stage.argv[0], sys.executable)
        self.assertEqual(
            stage.argv[1:4],
            ("-m", "unittest", "tests.contract.test_release_contract"),
        )

    def test_catalog_contract_runs_catalog_contract_module(self) -> None:
        stage = self._stage("full", "catalog-contract", catalog=True)
        self.assertEqual(stage.argv[0], sys.executable)
        self.assertEqual(
            stage.argv[1:4],
            ("-m", "unittest", "tests.contract.test_catalog_contract"),
        )

    def test_catalog_release_contract_runs_catalog_release_module(self) -> None:
        stage = self._stage("full", "catalog-release-contract", catalog=True)
        self.assertEqual(stage.argv[0], sys.executable)
        self.assertEqual(
            stage.argv[1:4],
            ("-m", "unittest", "tests.contract.test_catalog_release"),
        )
        self.assertNotIn("gh", stage.argv)
        self.assertNotIn("curl", stage.argv)
        self.assertNotIn("http", " ".join(stage.argv).lower())

    def test_public_docs_runs_public_docs_module(self) -> None:
        stage = self._stage("full", "public-docs", catalog=True)
        self.assertEqual(stage.argv[0], sys.executable)
        self.assertEqual(
            stage.argv[1:4],
            ("-m", "unittest", "tests.contract.test_public_docs"),
        )

    def test_korean_package_runs_korean_package_module(self) -> None:
        stage = self._stage(
            "full", "korean-package", skill="korean-writing-editor"
        )
        self.assertEqual(
            stage.argv[1:4],
            ("-m", "unittest", "tests.contract.test_korean_package"),
        )

    def test_graspic_contract_runs_graspic_module(self) -> None:
        stage = self._stage("full", "graspic-contract", skill="graspic")
        self.assertEqual(
            stage.argv[1:4],
            ("-m", "unittest", "tests.contract.test_graspic"),
        )

    def test_selected_stages_use_sys_executable_and_tuple_argv(self) -> None:
        verify = self._load()
        selections = (
            ("full", "graspic", False),
            ("full", "korean-writing-editor", False),
            ("full", "image-workbench", False),
            ("windows-portable", "image-workbench", False),
            ("full", None, True),
        )
        for profile, skill, catalog in selections:
            for stage in verify.stages(profile, skill=skill, catalog=catalog):
                self.assertIsInstance(stage.argv, tuple)
                self.assertTrue(stage.argv, stage.name)
                self.assertEqual(stage.argv[0], sys.executable)
                self.assertEqual(stage.cwd, verify.ROOT)
                joined = " ".join(stage.argv)
                self.assertNotIn("&&", joined)
                self.assertNotIn("|", joined)
                self.assertNotIn(";", joined)

    def test_cli_rejects_unknown_profile(self) -> None:
        verify = self._load()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                verify.main(["--profile", "linux"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_cli_rejects_unknown_skill(self) -> None:
        verify = self._load()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                verify.main(["--skill", "not-a-skill"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_cli_rejects_conflicting_selectors(self) -> None:
        verify = self._load()
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as raised:
                verify.main(["--skill", "graspic", "--catalog"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_cli_defaults_to_full_profile(self) -> None:
        verify = self._load()
        recorded: list[tuple[str, str | None, bool]] = []
        original = verify.stages

        def fake_stages(
            profile: str, *, skill: str | None = None, catalog: bool = False
        ):
            recorded.append((profile, skill, catalog))
            return ()

        verify.stages = fake_stages  # type: ignore[method-assign]
        try:
            self.assertEqual(verify.main([]), 0)
        finally:
            verify.stages = original  # type: ignore[method-assign]
        self.assertEqual(recorded, [("full", None, False)])

    def test_cli_passes_skill_selector(self) -> None:
        verify = self._load()
        recorded: list[tuple[str, str | None, bool]] = []
        original = verify.stages

        def fake_stages(
            profile: str, *, skill: str | None = None, catalog: bool = False
        ):
            recorded.append((profile, skill, catalog))
            return ()

        verify.stages = fake_stages  # type: ignore[method-assign]
        try:
            self.assertEqual(verify.main(["--skill", "graspic"]), 0)
        finally:
            verify.stages = original  # type: ignore[method-assign]
        self.assertEqual(recorded, [("full", "graspic", False)])

    def test_cli_passes_catalog_selector(self) -> None:
        verify = self._load()
        recorded: list[tuple[str, str | None, bool]] = []
        original = verify.stages

        def fake_stages(
            profile: str, *, skill: str | None = None, catalog: bool = False
        ):
            recorded.append((profile, skill, catalog))
            return ()

        verify.stages = fake_stages  # type: ignore[method-assign]
        try:
            self.assertEqual(verify.main(["--catalog"]), 0)
        finally:
            verify.stages = original  # type: ignore[method-assign]
        self.assertEqual(recorded, [("full", None, True)])

    def test_windows_profile_keeps_korean_live_unit(self) -> None:
        verify = self._load()
        names = [stage.name for stage in verify.stages("windows-portable")]
        self.assertIn("korean-live-unit", names)

    def test_live_unit_module_is_importable_without_fcntl(self) -> None:
        self.assertTrue(LIVE_TEST_PATH.is_file(), "live unit tests are absent")
        error: BaseException | None = None
        try:
            _load_live_tests_without_fcntl()
        except ModuleNotFoundError as exc:
            error = exc
        self.assertIsNone(
            error,
            f"live unit discovery would ERROR on Windows: {error}",
        )

    def test_unix_only_live_tests_are_skipped_without_unix_specials(self) -> None:
        self.assertTrue(LIVE_TEST_PATH.is_file(), "live unit tests are absent")
        skipped = _unix_skipped_live_test_names(
            LIVE_TEST_PATH.read_text(encoding="utf-8")
        )
        missing = [
            name for name in REQUIRED_UNIX_ONLY_LIVE_TESTS if name not in skipped
        ]
        self.assertEqual(
            missing,
            [],
            "Unix-only live tests must skipIf FIFO/fcntl/dir_fd fixtures on Windows",
        )

    def _stage(
        self,
        profile: str,
        name: str,
        *,
        skill: str | None = None,
        catalog: bool = False,
    ):
        verify = self._load()
        kwargs: dict[str, str | bool] = {}
        if skill is not None:
            kwargs["skill"] = skill
        if catalog:
            kwargs["catalog"] = catalog
        for stage in verify.stages(profile, **kwargs):
            if stage.name == name:
                return stage
        self.fail(f"profile {profile!r} is missing stage {name!r}")


def _load_live_tests_without_fcntl() -> ModuleType:
    name = "live_unit_windows_import_probe"
    spec = importlib.util.spec_from_file_location(name, LIVE_TEST_PATH)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(LIVE_TEST_PATH)
    module = importlib.util.module_from_spec(spec)
    original_import = builtins.__import__

    def guarded_import(
        module_name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ):
        if module_name.split(".")[0] == "fcntl":
            raise ModuleNotFoundError("No module named 'fcntl'")
        return original_import(module_name, globals, locals, fromlist, level)

    sys.modules[name] = module
    builtins.__import__ = guarded_import
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        builtins.__import__ = original_import
        sys.modules.pop(name, None)


def _unix_skipped_live_test_names(source: str) -> set[str]:
    tree = ast.parse(source)
    skipped: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            for decorator in node.decorator_list:
                text = ast.get_source_segment(source, decorator) or ""
                lowered = text.lower()
                if "skipif" in lowered or "unix_only" in lowered or "os.name" in text:
                    skipped.add(node.name)
        if isinstance(node, ast.Assign):
            targets = [
                target.id for target in node.targets if isinstance(target, ast.Name)
            ]
            if "unix_only_test_names" not in targets:
                continue
            for const in ast.walk(node.value):
                if isinstance(const, ast.Constant) and isinstance(const.value, str):
                    skipped.add(const.value)
    return skipped


if __name__ == "__main__":
    unittest.main()
