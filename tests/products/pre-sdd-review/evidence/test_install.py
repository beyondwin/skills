from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr
from unittest import mock
from pathlib import Path

from support import ROOT

from scripts import release


SKILL = ROOT / "skills" / "pre-sdd-review"
INSTALL_PATH = SKILL / "evidence" / "install.py"
EXPECTED_VERSION_BYTES = (
    b'{"cli_version":"1.0.0","schema_version":1,'
    b'"skill_name":"pre-sdd-review"}\n'
)
EXPECTED_VERSION = {
    "cli_version": "1.0.0",
    "schema_version": 1,
    "skill_name": "pre-sdd-review",
}


def _load_installer():
    spec = importlib.util.spec_from_file_location("pre_sdd_review_installer", INSTALL_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load evidence installer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = _load_installer()
EvidenceError = installer.EvidenceError


class EvidenceInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory(prefix="pre sdd install ")
        self.workspace = Path(self._tempdir.name)
        self.skill = self.workspace / "skill copy"
        shutil.copytree(
            SKILL,
            self.skill,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        self.bin_dir = self.workspace / "bin with spaces"
        self.bin_dir.mkdir()
        self.evidence_home = self.workspace / "must stay absent"

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _run_version(self, *command: str) -> subprocess.CompletedProcess[bytes]:
        environ = os.environ.copy()
        environ["PRE_SDD_REVIEW_HOME"] = str(self.evidence_home)
        environ["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            env=environ,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode(errors="replace"))
        self.assertEqual(completed.stdout, EXPECTED_VERSION_BYTES)
        self.assertEqual(completed.stderr, b"")
        parsed = json.loads(completed.stdout)
        self.assertEqual(parsed, EXPECTED_VERSION)
        self.assertEqual(set(parsed), {"cli_version", "schema_version", "skill_name"})
        self.assertFalse(self.evidence_home.exists())
        return completed

    def test_runtime_manifest_is_exact(self) -> None:
        self.assertEqual(
            installer.RUNTIME_PACKAGE_FILES,
            (
                "__init__.py",
                "__main__.py",
                "cli.py",
                "schema.py",
                "repository.py",
                "storage.py",
                "reporting.py",
            ),
        )
        prefix = "evidence/pre_sdd_review_evidence/"
        release_runtime = {
            relative.removeprefix(prefix)
            for relative in release.PRE_SDD_REVIEW_PAYLOAD_FILES
            if relative.startswith(prefix)
        }
        self.assertEqual(release_runtime, set(installer.RUNTIME_PACKAGE_FILES))

    def test_posix_install_creates_executable_zipapp_command(self) -> None:
        installed = installer.install(
            self.skill,
            self.bin_dir,
            platform="posix",
            python_executable=Path(sys.executable),
        )
        command = self.bin_dir / "pre-sdd-review-evidence"
        self.assertEqual(installed, (command,))
        self.assertTrue(command.stat().st_mode & stat.S_IXUSR)
        self._run_version(str(command), "--version")

    def test_windows_install_creates_quoted_wrapper_and_runnable_zipapp(self) -> None:
        installed = installer.install(
            self.skill,
            self.bin_dir,
            platform="windows",
            python_executable=Path(sys.executable),
        )
        archive = self.bin_dir / "pre-sdd-review-evidence.pyz"
        wrapper = self.bin_dir / "pre-sdd-review-evidence.cmd"
        self.assertEqual(installed, (archive, wrapper))
        self.assertEqual(
            wrapper.read_bytes(),
            f'@"{sys.executable}" "%~dp0pre-sdd-review-evidence.pyz" %*\r\n'.encode(
                "utf-8"
            ),
        )
        self._run_version(sys.executable, str(archive), "--version")

    @unittest.skipIf(os.name == "nt", "TZ and POSIX umask matrix requires POSIX")
    def test_zipapp_bytes_are_independent_of_timezone_and_umask(self) -> None:
        script = """
import importlib.util
import os
import sys
from pathlib import Path

installer_path, skill_root, posix_bin, windows_bin, mask = sys.argv[1:]
os.umask(int(mask, 8))
spec = importlib.util.spec_from_file_location("isolated_installer", installer_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.install(Path(skill_root), Path(posix_bin), "posix", Path(sys.executable))
module.install(Path(skill_root), Path(windows_bin), "windows", Path(sys.executable))
"""
        posix_bytes: list[bytes] = []
        windows_bytes: list[bytes] = []
        commands: list[Path] = []
        archives: list[Path] = []
        for timezone in ("UTC", "Asia/Seoul"):
            for mask in ("022", "077"):
                label = f"{timezone.replace('/', '-')}-{mask}"
                posix_bin = self.workspace / f"posix-{label}"
                windows_bin = self.workspace / f"windows-{label}"
                posix_bin.mkdir()
                windows_bin.mkdir()
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        script,
                        str(INSTALL_PATH),
                        str(self.skill),
                        str(posix_bin),
                        str(windows_bin),
                        mask,
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={
                        **os.environ,
                        "TZ": timezone,
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                command = posix_bin / "pre-sdd-review-evidence"
                archive = windows_bin / "pre-sdd-review-evidence.pyz"
                commands.append(command)
                archives.append(archive)
                posix_bytes.append(command.read_bytes())
                windows_bytes.append(archive.read_bytes())
        self.assertEqual(len(set(posix_bytes)), 1)
        self.assertEqual(len(set(windows_bytes)), 1)
        expected_names = [
            "__main__.py",
            *(f"pre_sdd_review_evidence/{name}" for name in installer.RUNTIME_PACKAGE_FILES),
        ]
        with zipfile.ZipFile(commands[0]) as archive:
            self.assertEqual(archive.namelist(), expected_names)
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
                self.assertEqual((info.external_attr >> 16) & 0o170000, stat.S_IFREG)
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)
        self._run_version(str(commands[0]), "--version")
        self._run_version(sys.executable, str(archives[0]), "--version")

    def test_identical_reinstall_is_idempotent(self) -> None:
        first = installer.install(
            self.skill,
            self.bin_dir,
            platform="posix",
            python_executable=Path(sys.executable),
        )
        before = first[0].read_bytes()
        second = installer.install(
            self.skill,
            self.bin_dir,
            platform="posix",
            python_executable=Path(sys.executable),
        )
        self.assertEqual(second, first)
        self.assertEqual(first[0].read_bytes(), before)

        windows_dir = self.workspace / "windows bin"
        windows_dir.mkdir()
        windows_first = installer.install(
            self.skill,
            windows_dir,
            platform="windows",
            python_executable=Path(sys.executable),
        )
        windows_bytes = tuple(path.read_bytes() for path in windows_first)
        windows_second = installer.install(
            self.skill,
            windows_dir,
            platform="windows",
            python_executable=Path(sys.executable),
        )
        self.assertEqual(windows_second, windows_first)
        self.assertEqual(tuple(path.read_bytes() for path in windows_second), windows_bytes)

    def test_installer_refuses_nonidentical_existing_launcher(self) -> None:
        target = self.bin_dir / "pre-sdd-review-evidence"
        target.write_text("foreign\n", encoding="utf-8")
        with self.assertRaisesRegex(EvidenceError, "install target exists"):
            installer.install(
                self.skill,
                self.bin_dir,
                platform="posix",
                python_executable=Path(sys.executable),
            )
        self.assertEqual(target.read_text(encoding="utf-8"), "foreign\n")

    def test_windows_conflict_is_rejected_before_either_target_is_created(self) -> None:
        wrapper = self.bin_dir / "pre-sdd-review-evidence.cmd"
        wrapper.write_text("foreign\n", encoding="utf-8")
        with self.assertRaisesRegex(EvidenceError, "install target exists"):
            installer.install(
                self.skill,
                self.bin_dir,
                platform="windows",
                python_executable=Path(sys.executable),
            )
        self.assertFalse((self.bin_dir / "pre-sdd-review-evidence.pyz").exists())
        self.assertEqual(wrapper.read_text(encoding="utf-8"), "foreign\n")

    def test_installer_requires_an_existing_directory_selected_for_path(self) -> None:
        missing = self.workspace / "missing bin"
        with self.assertRaisesRegex(EvidenceError, "bin directory"):
            installer.install(
                self.skill,
                missing,
                platform="posix",
                python_executable=Path(sys.executable),
            )
        not_directory = self.workspace / "not a directory"
        not_directory.write_text("file\n", encoding="utf-8")
        with self.assertRaisesRegex(EvidenceError, "bin directory"):
            installer.install(
                self.skill,
                not_directory,
                platform="posix",
                python_executable=Path(sys.executable),
            )

    def test_install_does_not_change_path_or_shell_profiles(self) -> None:
        fake_home = self.workspace / "fake home"
        fake_home.mkdir()
        sentinel_path = str(self.bin_dir)
        with mock.patch.dict(
            os.environ,
            {"HOME": str(fake_home), "PATH": sentinel_path},
            clear=False,
        ):
            installer.install(
                self.skill,
                self.bin_dir,
                platform="posix",
                python_executable=Path(sys.executable),
            )
            self.assertEqual(os.environ.get("PATH"), sentinel_path)
        self.assertEqual(tuple(fake_home.iterdir()), ())
        for name in (".profile", ".bash_profile", ".bashrc", ".zprofile", ".zshrc"):
            self.assertFalse((fake_home / name).exists())

    def test_generated_bytecode_cache_is_rejected_as_an_unexpected_package_entry(self) -> None:
        cache = self.skill / "evidence/pre_sdd_review_evidence/__pycache__"
        cache.mkdir()
        (cache / "cli.cpython-311.pyc").write_bytes(b"generated-bytecode")
        with self.assertRaisesRegex(EvidenceError, "runtime package manifest"):
            installer.install(
                self.skill,
                self.bin_dir,
                platform="posix",
                python_executable=Path(sys.executable),
            )

    def test_source_validation_rejects_manifest_and_identity_drift(self) -> None:
        mutations = (
            (
                "extra runtime module",
                lambda root: (root / "evidence/pre_sdd_review_evidence/network.py").write_text(
                    "# forbidden extra module\n", encoding="utf-8"
                ),
                "runtime package manifest",
            ),
            (
                "missing runtime module",
                lambda root: (root / "evidence/pre_sdd_review_evidence/reporting.py").unlink(),
                "runtime package manifest",
            ),
            (
                "release version mismatch",
                lambda root: (root / "release.toml").write_text(
                    (root / "release.toml")
                    .read_text(encoding="utf-8")
                    .replace('version = "1.2.0"', 'version = "1.2.1"'),
                    encoding="utf-8",
                ),
                "release identity",
            ),
            (
                "release name mismatch",
                lambda root: (root / "release.toml").write_text(
                    (root / "release.toml")
                    .read_text(encoding="utf-8")
                    .replace('name = "pre-sdd-review"', 'name = "other"'),
                    encoding="utf-8",
                ),
                "release identity",
            ),
            (
                "CLI version mismatch",
                lambda root: (root / "evidence/pre_sdd_review_evidence/__init__.py").write_text(
                    (root / "evidence/pre_sdd_review_evidence/__init__.py")
                    .read_text(encoding="utf-8")
                    .replace('CLI_VERSION = "1.0.0"', 'CLI_VERSION = "2.0.0"'),
                    encoding="utf-8",
                ),
                "CLI_VERSION",
            ),
            (
                "schema version mismatch",
                lambda root: (root / "evidence/pre_sdd_review_evidence/__init__.py").write_text(
                    (root / "evidence/pre_sdd_review_evidence/__init__.py")
                    .read_text(encoding="utf-8")
                    .replace("SCHEMA_VERSION = 1", "SCHEMA_VERSION = 2"),
                    encoding="utf-8",
                ),
                "SCHEMA_VERSION",
            ),
            (
                "nonliteral CLI version",
                lambda root: (root / "evidence/pre_sdd_review_evidence/__init__.py").write_text(
                    (root / "evidence/pre_sdd_review_evidence/__init__.py")
                    .read_text(encoding="utf-8")
                    .replace(
                        'CLI_VERSION = "1.0.0"',
                        'CLI_VERSION = ".".join(("1", "0", "0"))',
                    ),
                    encoding="utf-8",
                ),
                "CLI_VERSION must be a literal",
            ),
        )
        for label, mutate, message in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                copied = Path(directory) / "pre-sdd-review"
                shutil.copytree(
                    self.skill,
                    copied,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
                mutate(copied)
                with self.assertRaisesRegex(EvidenceError, message):
                    installer.install(
                        copied,
                        self.bin_dir,
                        platform="posix",
                        python_executable=Path(sys.executable),
                    )

    def test_validation_does_not_import_or_execute_supplied_runtime(self) -> None:
        marker = self.workspace / "supplied-source-executed"
        schema = self.skill / "evidence/pre_sdd_review_evidence/schema.py"
        original = schema.read_text(encoding="utf-8")
        schema.write_text(
            original.replace(
                "from __future__ import annotations\n",
                "from __future__ import annotations\n"
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n",
                1,
            ),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(self.skill / "evidence/install.py"),
                "--skill-root",
                str(self.skill),
                "--bin-dir",
                str(self.bin_dir),
            ],
            check=False,
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")
        self.assertFalse(marker.exists())

    def test_readme_closes_install_privacy_and_evidence_boundaries(self) -> None:
        readme = (self.skill / "evidence/README.md").read_text(encoding="utf-8")
        normalized = " ".join(readme.split())
        for phrase in (
            "already intended for `PATH`",
            "neither creates a PATH directory nor edits `PATH` or a shell profile",
            "Do not pipe a remote download to a shell",
            "Removing a launcher does not remove `~/.pre-sdd-review/`",
            "Do not put source or document text",
            "prompts, provider transcripts, command output, credentials",
            "does not perform automatic secret detection",
            "not a signed audit log",
            "observer-supplied",
            "no correction or amendment command",
            "inspection heuristics",
            "do not mutate the skill, judge quality automatically, or rank clients",
        ):
            self.assertIn(phrase, normalized)
        self.assertNotRegex(readme, r"curl[^\n|]*\|\s*(?:ba)?sh")

    @unittest.skipIf(os.name == "nt", "symlink fixture requires POSIX semantics")
    def test_source_validation_rejects_symlinked_runtime_module(self) -> None:
        source = self.skill / "evidence/pre_sdd_review_evidence/schema.py"
        replacement = self.workspace / "replacement-schema.py"
        shutil.copyfile(source, replacement)
        source.unlink()
        source.symlink_to(replacement)
        with self.assertRaisesRegex(EvidenceError, "regular non-symlink"):
            installer.install(
                self.skill,
                self.bin_dir,
                platform="posix",
                python_executable=Path(sys.executable),
            )

    def test_cli_requires_bin_dir(self) -> None:
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            installer.main([])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
