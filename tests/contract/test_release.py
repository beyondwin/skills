from __future__ import annotations

import contextlib
import importlib.util
import io
import stat
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
BUILD_RELEASE_PATH = ROOT / "scripts" / "build_release.py"
VERSION = "2.0.0"
PLUGIN_ZIP = f"beyondwin-skills-v{VERSION}.zip"
KOREAN_ZIP = f"korean-writing-editor-v{VERSION}.zip"
IMAGE_ZIP = f"image-workbench-v{VERSION}.zip"
ARCHIVE_NAMES = {PLUGIN_ZIP, KOREAN_ZIP, IMAGE_ZIP}
EXPECTED_PLUGIN_MEMBERS = {
    ".codex-plugin/plugin.json",
    "LICENSE",
    "NOTICE",
    "skills/korean-writing-editor/LICENSE.txt",
    "skills/korean-writing-editor/SKILL.md",
    "skills/korean-writing-editor/agents/openai.yaml",
    "skills/korean-writing-editor/references/editorial-guide.md",
    "skills/korean-writing-editor/references/sources.md",
    "skills/image-workbench/LICENSE.txt",
    "skills/image-workbench/SKILL.md",
    "skills/image-workbench/agents/openai.yaml",
    "skills/image-workbench/references/image-spec.md",
    "skills/image-workbench/references/quality-rubric.md",
    "skills/image-workbench/references/sources.md",
    "skills/image-workbench/scripts/inspect_asset.py",
}
EXPECTED_KOREAN_MEMBERS = {
    "korean-writing-editor/LICENSE.txt",
    "korean-writing-editor/SKILL.md",
    "korean-writing-editor/agents/openai.yaml",
    "korean-writing-editor/references/editorial-guide.md",
    "korean-writing-editor/references/sources.md",
}
EXPECTED_IMAGE_MEMBERS = {
    "image-workbench/LICENSE.txt",
    "image-workbench/SKILL.md",
    "image-workbench/agents/openai.yaml",
    "image-workbench/references/image-spec.md",
    "image-workbench/references/quality-rubric.md",
    "image-workbench/references/sources.md",
    "image-workbench/scripts/inspect_asset.py",
}
FORBIDDEN_PREFIXES = (
    "tests/",
    "docs/",
    "scripts/",
    ".github/",
    ".evidence/",
    "receipts/",
    "generated-media/",
)
FORBIDDEN_PARTS = frozenset(
    {"tests", "evals", "__pycache__", ".evidence", "receipts", "generated-media"}
)
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def load_build_release() -> ModuleType:
    name = "scripts.build_release"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, BUILD_RELEASE_PATH)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(BUILD_RELEASE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def unix_mode(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0o777


class BuildReleasePresenceTests(unittest.TestCase):
    def test_build_release_module_exists(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")


class ReleaseMembershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")
        self.build_release = load_build_release()
        self._tempdir = tempfile.TemporaryDirectory()
        self.output = Path(self._tempdir.name)
        self.artifacts = self.build_release.build_archives(ROOT, self.output, VERSION)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_release_names_and_membership(self) -> None:
        build_release = self.build_release
        zip_names = build_release.zip_names
        artifacts = self.artifacts
        self.assertEqual({p.name for p in artifacts}, {
            "beyondwin-skills-v2.0.0.zip",
            "korean-writing-editor-v2.0.0.zip",
            "image-workbench-v2.0.0.zip",
        })
        plugin_names = zip_names(self.output / "beyondwin-skills-v2.0.0.zip")
        self.assertIn(".codex-plugin/plugin.json", plugin_names)
        self.assertFalse(any(name.startswith("tests/") for name in plugin_names))

    def test_plugin_zip_contains_complete_payload_only(self) -> None:
        names = self.build_release.zip_names(self.output / PLUGIN_ZIP)
        self.assertEqual(set(names), EXPECTED_PLUGIN_MEMBERS)
        self.assertIn("LICENSE", names)
        self.assertIn("NOTICE", names)
        self.assertTrue(any(name.startswith("skills/korean-writing-editor/") for name in names))
        self.assertTrue(any(name.startswith("skills/image-workbench/") for name in names))

    def test_standalone_zips_are_one_top_level_skill_with_license(self) -> None:
        zip_names = self.build_release.zip_names
        korean = zip_names(self.output / KOREAN_ZIP)
        image = zip_names(self.output / IMAGE_ZIP)
        self.assertEqual(set(korean), EXPECTED_KOREAN_MEMBERS)
        self.assertEqual(set(image), EXPECTED_IMAGE_MEMBERS)
        self.assertEqual({name.split("/")[0] for name in korean}, {"korean-writing-editor"})
        self.assertEqual({name.split("/")[0] for name in image}, {"image-workbench"})
        self.assertIn("korean-writing-editor/LICENSE.txt", korean)
        self.assertIn("image-workbench/LICENSE.txt", image)
        self.assertFalse(any(name.startswith("skills/") for name in korean))
        self.assertFalse(any(name.startswith("skills/") for name in image))

    def test_archives_omit_tests_docs_caches_and_evidence(self) -> None:
        zip_names = self.build_release.zip_names
        for archive in (PLUGIN_ZIP, KOREAN_ZIP, IMAGE_ZIP):
            names = zip_names(self.output / archive)
            for name in names:
                self.assertFalse(
                    name.startswith(FORBIDDEN_PREFIXES),
                    f"{archive} contains {name}",
                )
                parts = Path(name).parts
                self.assertFalse(FORBIDDEN_PARTS.intersection(parts), name)
                self.assertNotIn("__pycache__", name)
                self.assertFalse(name.endswith(".pyc"))


class ReleaseReproducibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")
        self.build_release = load_build_release()
        self._tempdir = tempfile.TemporaryDirectory()
        root = Path(self._tempdir.name)
        self.one = root / "one"
        self.two = root / "two"
        self.one.mkdir()
        self.two.mkdir()

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_two_builds_are_byte_identical(self) -> None:
        build_release = self.build_release
        hashes = build_release.hashes
        first = hashes(build_release.build_archives(ROOT, self.one, "2.0.0"))
        second = hashes(build_release.build_archives(ROOT, self.two, "2.0.0"))
        self.assertEqual(first, second)

    def test_zip_members_are_sorted_epoch_stamped_and_mode_normalized(self) -> None:
        artifact = self.build_release.build_archives(ROOT, self.one, VERSION)[0]
        with zipfile.ZipFile(artifact) as zf:
            names = zf.namelist()
            self.assertEqual(names, sorted(names))
            for info in zf.infolist():
                self.assertEqual(info.date_time, ZIP_EPOCH)
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                mode = unix_mode(info)
                file_type = (info.external_attr >> 16) & 0o170000
                self.assertEqual(file_type, stat.S_IFREG)
                if info.filename.endswith("scripts/inspect_asset.py"):
                    self.assertEqual(mode, 0o755)
                else:
                    self.assertEqual(mode, 0o644)


class ReleaseChecksumTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")
        self.build_release = load_build_release()
        self._tempdir = tempfile.TemporaryDirectory()
        self.output = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_write_checksums_lists_exactly_the_three_zips(self) -> None:
        archives = self.build_release.build_archives(ROOT, self.output, VERSION)
        checksums = self.build_release.write_checksums(
            archives,
            self.output / "SHA256SUMS",
        )
        self.assertEqual(checksums.name, "SHA256SUMS")
        lines = checksums.read_text(encoding="ascii").splitlines()
        self.assertEqual(len(lines), 3)
        parsed: dict[str, str] = {}
        for line in lines:
            digest, name = line.split("  ", 1)
            self.assertRegex(digest, r"^[0-9a-f]{64}$")
            parsed[name] = digest
        self.assertEqual(set(parsed), ARCHIVE_NAMES)
        self.assertEqual(list(parsed), sorted(parsed))
        expected = self.build_release.hashes(archives)
        self.assertEqual(parsed, expected)


class ReleaseVerifyArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")
        self.build_release = load_build_release()
        self._tempdir = tempfile.TemporaryDirectory()
        self.output = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _zip(self, name: str, members: list[str], payload: bytes = b"x\n") -> Path:
        path = self.output / name
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w") as zf:
                for member in members:
                    zf.writestr(member, payload)
        return path

    def test_verify_archive_accepts_built_zips(self) -> None:
        archives = self.build_release.build_archives(ROOT, self.output, VERSION)
        for archive in archives:
            self.assertEqual(self.build_release.verify_archive(archive), [])

    def test_verify_archive_rejects_absolute_paths(self) -> None:
        path = self._zip(PLUGIN_ZIP, ["/tmp/evil", *sorted(EXPECTED_PLUGIN_MEMBERS)])
        errors = "\n".join(self.build_release.verify_archive(path))
        self.assertIn("absolute", errors.lower())

    def test_verify_archive_rejects_parent_segments(self) -> None:
        path = self._zip(KOREAN_ZIP, ["korean-writing-editor/../../etc/passwd"])
        errors = "\n".join(self.build_release.verify_archive(path))
        self.assertIn("..", errors)

    def test_verify_archive_rejects_duplicates(self) -> None:
        path = self._zip(IMAGE_ZIP, ["image-workbench/SKILL.md", "image-workbench/SKILL.md"])
        errors = "\n".join(self.build_release.verify_archive(path))
        self.assertIn("duplicate", errors.lower())

    def test_verify_archive_rejects_case_fold_collisions(self) -> None:
        path = self._zip(
            PLUGIN_ZIP,
            [".codex-plugin/plugin.json", "LICENSE", "license", "NOTICE"],
        )
        errors = "\n".join(self.build_release.verify_archive(path))
        self.assertIn("case-fold", errors.lower())

    def test_verify_archive_rejects_unexpected_members(self) -> None:
        path = self._zip(PLUGIN_ZIP, ["tests/secret.py", "docs/en/evaluation.md"])
        errors = "\n".join(self.build_release.verify_archive(path))
        self.assertIn("unexpected", errors.lower())


class ReleaseDownloadAndSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")
        self.build_release = load_build_release()
        self._tempdir = tempfile.TemporaryDirectory()
        self.output = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_verify_download_rejects_checksum_set_other_than_three_zips(self) -> None:
        archives = self.build_release.build_archives(ROOT, self.output, VERSION)
        checksums = self.output / "SHA256SUMS"
        checksums.write_text(
            "0" * 64 + "  beyondwin-skills-v2.0.0.zip\n",
            encoding="ascii",
        )
        errors = "\n".join(self.build_release.verify_download(self.output, VERSION))
        self.assertTrue(errors)
        extra = self.output / "notes.txt"
        extra.write_text("nope\n", encoding="utf-8")
        self.build_release.write_checksums(archives, checksums)
        checksums.write_text(
            checksums.read_text(encoding="ascii") + "deadbeef" * 8 + "  notes.txt\n",
            encoding="ascii",
        )
        errors = "\n".join(self.build_release.verify_download(self.output, VERSION))
        self.assertTrue(errors)

    def test_cli_builds_artifacts_and_extraction_smokes_pass(self) -> None:
        stderr = io.StringIO()
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.build_release.main(
                ["--version", VERSION, "--output", str(self.output)]
            )
        self.assertEqual(code, 0, stderr.getvalue() or stdout.getvalue())
        names = {path.name for path in self.output.iterdir() if path.is_file()}
        self.assertEqual(names, ARCHIVE_NAMES | {"SHA256SUMS"})
        self.assertEqual(self.build_release.verify_download(self.output, VERSION), [])
        checksums = (self.output / "SHA256SUMS").read_text(encoding="ascii").splitlines()
        listed = [line.split("  ", 1)[1] for line in checksums]
        self.assertEqual(set(listed), ARCHIVE_NAMES)
