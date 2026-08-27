from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import release, release_archive  # noqa: E402
from scripts.release_archive import ArchiveMember  # noqa: E402


BUILD_RELEASE_PATH = ROOT / "scripts" / "build_release.py"
WRAPPER_MESSAGE = (
    "scripts/build_release.py no longer builds a shared-version bundle. "
    "Use scripts/release.py after the independent release pipeline lands.\n"
)
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def unix_mode(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0o777


class BuildReleaseWrapperTests(unittest.TestCase):
    def test_build_release_module_exists(self) -> None:
        self.assertTrue(BUILD_RELEASE_PATH.is_file(), "scripts.build_release does not exist")

    def test_wrapper_prints_exact_message_exits_2_and_creates_no_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(BUILD_RELEASE_PATH),
                    "--version",
                    "2.0.0",
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(completed.stderr, WRAPPER_MESSAGE)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(list(output.iterdir()), [])


class ProductBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.output = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_build_product_emits_only_requested_product_and_checksums(self) -> None:
        artifacts = release.build_product(ROOT, "graspic", self.output, require_release_entry=False)
        self.assertEqual(
            {path.name for path in artifacts},
            {"graspic-v3.0.0.zip", "SHA256SUMS"},
        )
        names = release_archive.zip_names(self.output / "graspic-v3.0.0.zip")
        self.assertTrue(all(name.startswith("graspic/") for name in names))
        self.assertIn("graspic/release.toml", names)
        self.assertNotIn("korean-writing-editor/SKILL.md", names)

    def test_build_rejects_nonempty_output(self) -> None:
        (self.output / "keep.txt").write_text("keep\n", encoding="utf-8")
        with self.assertRaises(release_archive.ReleaseError):
            release.build_product(ROOT, "image-workbench", self.output, require_release_entry=False)

    def test_build_requires_dated_changelog_by_default(self) -> None:
        with self.assertRaises(release_archive.ReleaseError) as raised:
            release.build_product(ROOT, "graspic", self.output)
        self.assertIn("dated release heading", str(raised.exception))
        self.assertEqual(list(self.output.iterdir()), [])


class ReleaseReproducibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        root = Path(self._tempdir.name)
        self.one = root / "one"
        self.two = root / "two"
        self.one.mkdir()
        self.two.mkdir()

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def test_two_builds_are_byte_identical(self) -> None:
        first = release.build_product(ROOT, "graspic", self.one, require_release_entry=False)
        second = release.build_product(ROOT, "graspic", self.two, require_release_entry=False)
        self.assertEqual(release_archive.hashes(first), release_archive.hashes(second))

    def test_zip_members_are_sorted_epoch_stamped_and_mode_normalized(self) -> None:
        artifact, _checksums = release.build_product(
            ROOT,
            "image-workbench",
            self.one,
            require_release_entry=False,
        )
        with zipfile.ZipFile(artifact) as archive:
            names = archive.namelist()
            self.assertEqual(names, sorted(names))
            self.assertTrue(all(name.startswith("image-workbench/") for name in names))
            self.assertNotIn("graspic/SKILL.md", names)
            for info in archive.infolist():
                self.assertEqual(info.date_time, ZIP_EPOCH)
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                mode = unix_mode(info)
                file_type = (info.external_attr >> 16) & 0o170000
                self.assertEqual(file_type, stat.S_IFREG)
                if info.filename.endswith("scripts/inspect_asset.py"):
                    self.assertEqual(mode, 0o755)
                else:
                    self.assertEqual(mode, 0o644)


class ArchiveSafetyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.output = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _zip(self, members: list[str], payload: bytes = b"x\n") -> Path:
        path = self.output / "graspic-v3.0.0.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w") as archive:
                for member in members:
                    archive.writestr(member, payload)
        return path

    def test_verify_product_archive_rejects_absolute_paths(self) -> None:
        path = self._zip(["/tmp/evil", "graspic/SKILL.md", "graspic/LICENSE.txt"])
        errors = "\n".join(release_archive.verify_product_archive(path, "graspic"))
        self.assertIn("absolute", errors.lower())

    def test_verify_product_archive_rejects_parent_segments(self) -> None:
        path = self._zip(["graspic/../etc/passwd"])
        errors = "\n".join(release_archive.verify_product_archive(path, "graspic"))
        self.assertIn("..", errors)

    def test_verify_product_archive_rejects_duplicates(self) -> None:
        path = self._zip(["graspic/SKILL.md", "graspic/SKILL.md"])
        errors = "\n".join(release_archive.verify_product_archive(path, "graspic"))
        self.assertIn("duplicate", errors.lower())

    def test_verify_product_archive_rejects_case_fold_collisions(self) -> None:
        path = self._zip(["graspic/SKILL.md", "graspic/skill.md", "graspic/LICENSE.txt"])
        errors = "\n".join(release_archive.verify_product_archive(path, "graspic"))
        self.assertIn("case-fold", errors.lower())

    def test_write_zip_rejects_absolute_paths(self) -> None:
        with self.assertRaises(release_archive.ReleaseError):
            release_archive.write_zip(
                self.output / "out.zip",
                [ArchiveMember("/tmp/evil", b"x\n", False)],
            )

    def test_write_zip_rejects_parent_segments(self) -> None:
        with self.assertRaises(release_archive.ReleaseError):
            release_archive.write_zip(
                self.output / "out.zip",
                [ArchiveMember("graspic/../SKILL.md", b"x\n", False)],
            )

    def test_write_zip_rejects_duplicates_and_case_fold_collisions(self) -> None:
        with self.assertRaises(release_archive.ReleaseError):
            release_archive.write_zip(
                self.output / "dup.zip",
                [
                    ArchiveMember("graspic/SKILL.md", b"one\n", False),
                    ArchiveMember("graspic/SKILL.md", b"two\n", False),
                ],
            )
        with self.assertRaises(release_archive.ReleaseError):
            release_archive.write_zip(
                self.output / "fold.zip",
                [
                    ArchiveMember("graspic/SKILL.md", b"one\n", False),
                    ArchiveMember("graspic/skill.md", b"two\n", False),
                ],
            )

    @unittest.skipIf(
        sys.platform == "win32" or not hasattr(__import__("os"), "mkfifo"),
        "symlink and FIFO zip members are asserted via Unix mode bits",
    )
    def test_verify_product_archive_rejects_symlink_and_special_file_members(self) -> None:
        symlink = self.output / "symlink.zip"
        with zipfile.ZipFile(symlink, "w") as archive:
            skill = zipfile.ZipInfo("graspic/SKILL.md")
            skill.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(skill, b"# skill\n")
            license_info = zipfile.ZipInfo("graspic/LICENSE.txt")
            license_info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(license_info, b"Apache License\nVersion 2.0\n")
            link = zipfile.ZipInfo("graspic/link.md")
            link.external_attr = (stat.S_IFLNK | 0o644) << 16
            archive.writestr(link, b"SKILL.md")
        errors = "\n".join(release_archive.verify_product_archive(symlink, "graspic"))
        self.assertIn("symlink", errors.lower())

        fifo = self.output / "fifo.zip"
        with zipfile.ZipFile(fifo, "w") as archive:
            skill = zipfile.ZipInfo("graspic/SKILL.md")
            skill.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(skill, b"# skill\n")
            license_info = zipfile.ZipInfo("graspic/LICENSE.txt")
            license_info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(license_info, b"Apache License\nVersion 2.0\n")
            pipe = zipfile.ZipInfo("graspic/pipe")
            pipe.external_attr = (stat.S_IFIFO | 0o644) << 16
            archive.writestr(pipe, b"")
        fifo_errors = "\n".join(release_archive.verify_product_archive(fifo, "graspic"))
        self.assertIn("special", fifo_errors.lower())


if __name__ == "__main__":
    unittest.main()
