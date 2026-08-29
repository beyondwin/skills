from __future__ import annotations

import os
import shutil
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

from scripts import release  # noqa: E402
from scripts.lib.archive import (  # noqa: E402
    ArchiveMember,
    ReleaseError,
    extract_archive,
    hashes,
    verify_product_archive,
    write_checksums,
    write_zip,
    zip_names,
)


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
        artifacts = release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        self.assertEqual(
            {path.name for path in artifacts},
            {"how-it-works-v1.0.0.zip", "SHA256SUMS"},
        )
        names = zip_names(self.output / "how-it-works-v1.0.0.zip")
        self.assertTrue(names)
        self.assertEqual({name.split("/", 1)[0] for name in names}, {"how-it-works"})
        self.assertTrue(all(name.startswith("how-it-works/") for name in names))
        self.assertIn("how-it-works/release.toml", names)
        self.assertNotIn("korean-writing-editor/SKILL.md", names)

    def test_how_it_works_archive_extracts_to_product_root(self) -> None:
        archive, _checksums = release.build_product(
            ROOT,
            "how-it-works",
            self.output,
            require_release_entry=False,
        )
        names = zip_names(archive)
        self.assertTrue(names)
        self.assertEqual({name.split("/", 1)[0] for name in names}, {"how-it-works"})
        self.assertTrue(all(name.startswith("how-it-works/") for name in names))
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            self.assertEqual(extract_archive(archive, destination), [])
            children = [path.name for path in destination.iterdir()]
            self.assertEqual(children, ["how-it-works"])
            self.assertTrue((destination / "how-it-works").is_dir())
            self.assertFalse((destination / "how-it-works").is_symlink())
            leftover = [
                path.name
                for path in destination.rglob("*")
                if path.is_file()
                and not path.is_relative_to(destination / "how-it-works")
            ]
            self.assertEqual(leftover, [])

    def test_build_rejects_nonempty_output(self) -> None:
        (self.output / "keep.txt").write_text("keep\n", encoding="utf-8")
        with self.assertRaises(ReleaseError):
            release.build_product(ROOT, "image-workbench", self.output, require_release_entry=False)

    def test_build_requires_dated_changelog_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skill = root / "skills" / "how-it-works"
            shutil.copytree(ROOT / "skills" / "how-it-works", skill)
            changelog = skill / "CHANGELOG.md"
            changelog.write_text(
                changelog.read_text(encoding="utf-8").replace(
                    "## 1.0.0 - 2026-08-28\n",
                    "",
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ReleaseError) as raised:
                release.build_product(root, "how-it-works", self.output)
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
        first = release.build_product(ROOT, "how-it-works", self.one, require_release_entry=False)
        second = release.build_product(ROOT, "how-it-works", self.two, require_release_entry=False)
        self.assertEqual(hashes(first), hashes(second))

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
            self.assertNotIn("how-it-works/SKILL.md", names)
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
        path = self.output / "how-it-works-v1.0.0.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w") as archive:
                for member in members:
                    archive.writestr(member, payload)
        return path

    def test_verify_product_archive_rejects_absolute_paths(self) -> None:
        path = self._zip(["/tmp/evil", "how-it-works/SKILL.md", "how-it-works/LICENSE.txt"])
        errors = "\n".join(verify_product_archive(path, "how-it-works"))
        self.assertIn("absolute", errors.lower())

    def test_verify_product_archive_rejects_parent_segments(self) -> None:
        path = self._zip(["how-it-works/../etc/passwd"])
        errors = "\n".join(verify_product_archive(path, "how-it-works"))
        self.assertIn("..", errors)

    def test_verify_product_archive_rejects_duplicates(self) -> None:
        path = self._zip(["how-it-works/SKILL.md", "how-it-works/SKILL.md"])
        errors = "\n".join(verify_product_archive(path, "how-it-works"))
        self.assertIn("duplicate", errors.lower())

    def test_verify_product_archive_rejects_case_fold_collisions(self) -> None:
        path = self._zip(["how-it-works/SKILL.md", "how-it-works/skill.md", "how-it-works/LICENSE.txt"])
        errors = "\n".join(verify_product_archive(path, "how-it-works"))
        self.assertIn("case-fold", errors.lower())

    def test_write_zip_rejects_absolute_paths(self) -> None:
        with self.assertRaises(ReleaseError):
            write_zip(
                self.output / "out.zip",
                [ArchiveMember("/tmp/evil", b"x\n", False)],
            )

    def test_write_zip_rejects_parent_segments(self) -> None:
        with self.assertRaises(ReleaseError):
            write_zip(
                self.output / "out.zip",
                [ArchiveMember("how-it-works/../SKILL.md", b"x\n", False)],
            )

    def test_write_zip_rejects_duplicates_and_case_fold_collisions(self) -> None:
        with self.assertRaises(ReleaseError):
            write_zip(
                self.output / "dup.zip",
                [
                    ArchiveMember("how-it-works/SKILL.md", b"one\n", False),
                    ArchiveMember("how-it-works/SKILL.md", b"two\n", False),
                ],
            )
        with self.assertRaises(ReleaseError):
            write_zip(
                self.output / "fold.zip",
                [
                    ArchiveMember("how-it-works/SKILL.md", b"one\n", False),
                    ArchiveMember("how-it-works/skill.md", b"two\n", False),
                ],
            )

    @unittest.skipIf(
        sys.platform == "win32" or not hasattr(__import__("os"), "mkfifo"),
        "symlink and FIFO zip members are asserted via Unix mode bits",
    )
    def test_verify_product_archive_rejects_symlink_and_special_file_members(self) -> None:
        symlink = self.output / "symlink.zip"
        with zipfile.ZipFile(symlink, "w") as archive:
            skill = zipfile.ZipInfo("how-it-works/SKILL.md")
            skill.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(skill, b"# skill\n")
            license_info = zipfile.ZipInfo("how-it-works/LICENSE.txt")
            license_info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(license_info, b"Apache License\nVersion 2.0\n")
            link = zipfile.ZipInfo("how-it-works/link.md")
            link.external_attr = (stat.S_IFLNK | 0o644) << 16
            archive.writestr(link, b"SKILL.md")
        errors = "\n".join(verify_product_archive(symlink, "how-it-works"))
        self.assertIn("symlink", errors.lower())

        fifo = self.output / "fifo.zip"
        with zipfile.ZipFile(fifo, "w") as archive:
            skill = zipfile.ZipInfo("how-it-works/SKILL.md")
            skill.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(skill, b"# skill\n")
            license_info = zipfile.ZipInfo("how-it-works/LICENSE.txt")
            license_info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(license_info, b"Apache License\nVersion 2.0\n")
            pipe = zipfile.ZipInfo("how-it-works/pipe")
            pipe.external_attr = (stat.S_IFIFO | 0o644) << 16
            archive.writestr(pipe, b"")
        fifo_errors = "\n".join(verify_product_archive(fifo, "how-it-works"))
        self.assertIn("special", fifo_errors.lower())


class ProductDownloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.output = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _checksums(self, archive: Path) -> None:
        write_checksums((archive,), self.output / "SHA256SUMS")

    def _rewrite_zip(
        self,
        archive: Path,
        rewriter,
    ) -> None:
        with zipfile.ZipFile(archive) as source:
            items = [(info, source.read(info)) for info in source.infolist()]
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as dest:
            for info, data in rewriter(items):
                dest.writestr(info, data)

    def test_verify_product_download_accepts_valid_two_file_directory(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        self.assertEqual(
            {path.name for path in self.output.iterdir()},
            {"how-it-works-v1.0.0.zip", "SHA256SUMS"},
        )
        self.assertEqual(release.verify_product_download(ROOT, "how-it-works", self.output), [])

    def test_verify_product_download_runs_korean_and_image_smokes(self) -> None:
        for name in ("korean-writing-editor", "image-workbench"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                release.build_product(ROOT, name, output, require_release_entry=False)
                self.assertEqual(release.verify_product_download(ROOT, name, output), [])

    def test_verify_product_download_runs_pre_sdd_review_smoke(self) -> None:
        release.build_product(
            ROOT,
            "pre-sdd-review",
            self.output,
            require_release_entry=False,
        )
        self.assertEqual(
            release.verify_product_download(ROOT, "pre-sdd-review", self.output),
            [],
        )

    def test_verify_product_download_rejects_changed_pre_sdd_reviewer_protocol_bytes(self) -> None:
        release.build_product(
            ROOT,
            "pre-sdd-review",
            self.output,
            require_release_entry=False,
        )
        archive = self.output / "pre-sdd-review-v1.0.0.zip"

        def change_protocol_bytes(items):
            for info, data in items:
                if info.filename == "pre-sdd-review/references/reviewer-protocol.md":
                    data += b"\nReviewer mutation policy: read-write.\n"
                yield info, data

        self._rewrite_zip(archive, change_protocol_bytes)
        self._checksums(archive)
        errors = release.verify_product_download(ROOT, "pre-sdd-review", self.output)
        self.assertIn(
            "pre-sdd-review: extracted payload does not match current source payload",
            errors,
        )

    def test_verify_product_download_rejects_executable_pre_sdd_reviewer_protocol(self) -> None:
        release.build_product(
            ROOT,
            "pre-sdd-review",
            self.output,
            require_release_entry=False,
        )
        archive = self.output / "pre-sdd-review-v1.0.0.zip"

        def make_protocol_executable(items):
            for info, data in items:
                if info.filename == "pre-sdd-review/references/reviewer-protocol.md":
                    info.external_attr = (stat.S_IFREG | 0o755) << 16
                yield info, data

        self._rewrite_zip(archive, make_protocol_executable)
        self._checksums(archive)
        errors = release.verify_product_download(ROOT, "pre-sdd-review", self.output)
        self.assertIn(
            "pre-sdd-review: unexpected executable archive member: "
            "pre-sdd-review/references/reviewer-protocol.md",
            errors,
        )

    def test_verify_product_download_rejects_unapproved_pre_sdd_review_members(self) -> None:
        cases = (
            (
                "pre-sdd-review/scripts/runtime.py",
                "pre-sdd-review: unexpected archive member: "
                "pre-sdd-review/scripts/runtime.py",
            ),
            (
                "pre-sdd-review/references/extra.md",
                "pre-sdd-review: unexpected archive member: "
                "pre-sdd-review/references/extra.md",
            ),
        )
        for member, expected_error in cases:
            with self.subTest(member=member), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)
                release.build_product(
                    ROOT,
                    "pre-sdd-review",
                    output,
                    require_release_entry=False,
                )
                archive = output / "pre-sdd-review-v1.0.0.zip"

                def add_member(items):
                    yield from items
                    info = zipfile.ZipInfo(member)
                    info.external_attr = (stat.S_IFREG | 0o644) << 16
                    yield info, b"unexpected\n"

                self._rewrite_zip(archive, add_member)
                write_checksums((archive,), output / "SHA256SUMS")
                errors = release.verify_product_download(
                    ROOT,
                    "pre-sdd-review",
                    output,
                )
                self.assertIn(expected_error, errors)

    def test_verify_product_download_rejects_pre_sdd_review_directory_member(self) -> None:
        release.build_product(
            ROOT,
            "pre-sdd-review",
            self.output,
            require_release_entry=False,
        )
        archive = self.output / "pre-sdd-review-v1.0.0.zip"

        def add_directory(items):
            yield from items
            info = zipfile.ZipInfo("pre-sdd-review/scripts/")
            info.external_attr = (stat.S_IFDIR | 0o755) << 16
            yield info, b""

        self._rewrite_zip(archive, add_directory)
        self._checksums(archive)
        errors = release.verify_product_download(ROOT, "pre-sdd-review", self.output)
        self.assertIn(
            "pre-sdd-review: unexpected archive member: pre-sdd-review/scripts/",
            errors,
        )
        self.assertIn(
            "pre-sdd-review: directory archive member: pre-sdd-review/scripts/",
            errors,
        )

    def test_verify_product_download_rejects_required_member_with_directory_mode(self) -> None:
        release.build_product(
            ROOT,
            "pre-sdd-review",
            self.output,
            require_release_entry=False,
        )
        archive = self.output / "pre-sdd-review-v1.0.0.zip"

        def change_required_member_type(items):
            for info, data in items:
                if info.filename == "pre-sdd-review/agents/openai.yaml":
                    info.external_attr = (stat.S_IFDIR | 0o755) << 16
                yield info, data

        self._rewrite_zip(archive, change_required_member_type)
        self._checksums(archive)
        errors = release.verify_product_download(ROOT, "pre-sdd-review", self.output)
        self.assertIn(
            "pre-sdd-review: archive member type mismatch: "
            "pre-sdd-review/agents/openai.yaml is not a regular file",
            errors,
        )

    def test_verify_product_download_rejects_dos_creator_with_fake_unix_file_mode(self) -> None:
        release.build_product(
            ROOT,
            "pre-sdd-review",
            self.output,
            require_release_entry=False,
        )
        archive = self.output / "pre-sdd-review-v1.0.0.zip"

        def change_required_member_creator(items):
            for info, data in items:
                if info.filename == "pre-sdd-review/agents/openai.yaml":
                    info.create_system = 0
                    info.external_attr = (
                        ((stat.S_IFREG | 0o644) << 16) | 0x10
                    )
                yield info, data

        self._rewrite_zip(archive, change_required_member_creator)
        self._checksums(archive)
        with zipfile.ZipFile(archive) as source:
            changed = source.getinfo("pre-sdd-review/agents/openai.yaml")
        self.assertEqual(changed.create_system, 0)
        self.assertEqual((changed.external_attr >> 16) & 0o170000, stat.S_IFREG)
        self.assertEqual(changed.external_attr & 0x10, 0x10)

        errors = release.verify_product_download(ROOT, "pre-sdd-review", self.output)
        self.assertIn(
            "pre-sdd-review: archive member creator/type mismatch: "
            "pre-sdd-review/agents/openai.yaml requires Unix creator system 3 "
            "with regular-file mode",
            errors,
        )

    def test_verify_product_download_rejects_missing_pre_sdd_review_member(self) -> None:
        release.build_product(
            ROOT,
            "pre-sdd-review",
            self.output,
            require_release_entry=False,
        )
        archive = self.output / "pre-sdd-review-v1.0.0.zip"

        def drop_member(items):
            for info, data in items:
                if info.filename == "pre-sdd-review/agents/openai.yaml":
                    continue
                yield info, data

        self._rewrite_zip(archive, drop_member)
        self._checksums(archive)
        errors = release.verify_product_download(ROOT, "pre-sdd-review", self.output)
        self.assertIn(
            "pre-sdd-review: missing archive member: "
            "pre-sdd-review/agents/openai.yaml",
            errors,
        )

    def test_pre_sdd_review_extracted_smoke_retains_exact_allowlist(self) -> None:
        approved = (
            "CHANGELOG.md",
            "LICENSE.txt",
            "README.en.md",
            "README.md",
            "SKILL.md",
            "agents/openai.yaml",
            "references/reviewer-protocol.md",
            "release.toml",
        )
        with tempfile.TemporaryDirectory() as directory:
            skill_root = Path(directory) / "pre-sdd-review"
            for relative in approved:
                path = skill_root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture\n", encoding="utf-8")
            self.assertEqual(release._smoke_pre_sdd_review(skill_root), [])

            (skill_root / "agents/openai.yaml").unlink()
            runtime = skill_root / "scripts/runtime.py"
            runtime.parent.mkdir(parents=True)
            runtime.write_text("runtime\n", encoding="utf-8")
            self.assertEqual(
                release._smoke_pre_sdd_review(skill_root),
                [
                    "pre-sdd-review: missing payload member: agents/openai.yaml",
                    "pre-sdd-review: unexpected runtime/scripts payload member: "
                    "scripts/runtime.py",
                ],
            )

    def test_verify_product_download_rejects_missing_checksum(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        (self.output / "SHA256SUMS").unlink()
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertIn("missing SHA256SUMS", errors)

    def test_verify_product_download_rejects_malformed_digest(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        (self.output / "SHA256SUMS").write_text(
            "not-a-digest  how-it-works-v1.0.0.zip\n",
            encoding="ascii",
        )
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertTrue(any("malformed digest" in error for error in errors), errors)

    def test_verify_product_download_rejects_another_products_zip(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        (self.output / "image-workbench-v2.0.1.zip").write_bytes(b"not a zip")
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertIn("unexpected zip in download directory: image-workbench-v2.0.1.zip", errors)

    def test_verify_product_download_rejects_renamed_zip(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        (self.output / "how-it-works-v1.0.0.zip").rename(self.output / "how-it-works-renamed.zip")
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertIn("unexpected zip in download directory: how-it-works-renamed.zip", errors)

    def test_verify_product_download_rejects_checksum_mismatch(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        archive = self.output / "how-it-works-v1.0.0.zip"
        archive.write_bytes(archive.read_bytes() + b"\x00")
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertTrue(any("checksum mismatch" in error for error in errors), errors)

    def test_verify_product_download_rejects_unexpected_file(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        (self.output / "notes.txt").write_text("extra\n", encoding="utf-8")
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertIn("unexpected file in download directory: notes.txt", errors)

    def test_verify_product_download_rejects_extra_checksum_row(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        checksums = self.output / "SHA256SUMS"
        checksums.write_text(
            checksums.read_text(encoding="ascii") + ("0" * 64) + "  extra.zip\n",
            encoding="ascii",
        )
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertTrue(
            any("SHA256SUMS must list exactly the expected product zip" in error for error in errors),
            errors,
        )

    def test_verify_product_download_rejects_unsafe_member(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        archive = self.output / "how-it-works-v1.0.0.zip"

        def add_absolute(items):
            yield from items
            evil = zipfile.ZipInfo("/tmp/evil")
            evil.external_attr = (stat.S_IFREG | 0o644) << 16
            yield evil, b"x\n"

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self._rewrite_zip(archive, add_absolute)
        self._checksums(archive)
        errors = "\n".join(release.verify_product_download(ROOT, "how-it-works", self.output))
        self.assertIn("absolute", errors.lower())

    def test_verify_product_download_rejects_metadata_version_mismatch(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        archive = self.output / "how-it-works-v1.0.0.zip"

        def bump_version(items):
            for info, data in items:
                text = data.decode("utf-8")
                if info.filename == "how-it-works/release.toml":
                    text = text.replace('version = "1.0.0"', 'version = "9.9.9"')
                    data = text.encode("utf-8")
                elif info.filename == "how-it-works/SKILL.md":
                    text = text.replace('version: "1.0.0"', 'version: "9.9.9"')
                    data = text.encode("utf-8")
                yield info, data

        self._rewrite_zip(archive, bump_version)
        self._checksums(archive)
        errors = release.verify_product_download(ROOT, "how-it-works", self.output)
        self.assertTrue(any("metadata version mismatch" in error for error in errors), errors)

    def test_verify_product_download_rejects_extracted_validation_failure(self) -> None:
        release.build_product(ROOT, "how-it-works", self.output, require_release_entry=False)
        archive = self.output / "how-it-works-v1.0.0.zip"

        def drop_changelog(items):
            for info, data in items:
                if info.filename == "how-it-works/CHANGELOG.md":
                    continue
                yield info, data

        self._rewrite_zip(archive, drop_changelog)
        self._checksums(archive)
        errors = "\n".join(release.verify_product_download(ROOT, "how-it-works", self.output))
        self.assertIn("CHANGELOG", errors)

    def test_extract_archive_restores_executable_mode(self) -> None:
        artifact, _checksums = release.build_product(
            ROOT,
            "image-workbench",
            self.output,
            require_release_entry=False,
        )
        with zipfile.ZipFile(artifact) as archive:
            info = archive.getinfo("image-workbench/scripts/inspect_asset.py")
            self.assertTrue((info.external_attr >> 16) & 0o111)
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            self.assertEqual(extract_archive(artifact, destination), [])
            inspector = destination / "image-workbench" / "scripts" / "inspect_asset.py"
            self.assertTrue(inspector.is_file())
            if os.name != "nt":
                self.assertTrue(inspector.stat().st_mode & stat.S_IXUSR)

    def test_verify_download_cli_requires_input_and_rejects_output(self) -> None:
        script = ROOT / "scripts" / "release.py"
        missing_input = subprocess.run(
            [sys.executable, str(script), "verify-download", "--product", "how-it-works"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(missing_input.returncode, 0)
        unexpected_output = subprocess.run(
            [
                sys.executable,
                str(script),
                "verify-download",
                "--product",
                "how-it-works",
                "--output",
                str(self.output),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(unexpected_output.returncode, 0)
        unexpected_input = subprocess.run(
            [
                sys.executable,
                str(script),
                "build",
                "--product",
                "how-it-works",
                "--input",
                str(self.output),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(unexpected_input.returncode, 0)


class SharedReleasePathTests(unittest.TestCase):
    def test_shared_release_paths_cover_registry_and_lib(self) -> None:
        expected = {
            "products.toml",
            "scripts/release.py",
            "scripts/lib/archive.py",
            "scripts/lib/catalog.py",
            "scripts/lib/product_contract.py",
            "scripts/lib/product_registry.py",
        }
        self.assertEqual(set(release.SHARED_RELEASE_PATHS), expected)
        for relative in release.SHARED_RELEASE_PATHS:
            self.assertTrue((ROOT / relative).is_file(), relative)
        self.assertNotIn("scripts/release_archive.py", release.SHARED_RELEASE_PATHS)
        self.assertNotIn("scripts/catalog_contract.py", release.SHARED_RELEASE_PATHS)


if __name__ == "__main__":
    unittest.main()
