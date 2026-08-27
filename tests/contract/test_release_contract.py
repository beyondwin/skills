from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_contract import (  # noqa: E402
    PRODUCT_NAMES,
    ProductRelease,
    load_product_release,
    payload_sha256,
    validate_product,
)

EXPECTED = {
    "korean-writing-editor": "2.0.1",
    "image-workbench": "2.0.1",
    "graspic": "3.0.0",
}


class ProductReleaseTests(unittest.TestCase):
    def test_each_product_owns_an_independent_release_manifest(self) -> None:
        self.assertEqual(set(PRODUCT_NAMES), set(EXPECTED))
        for name, version in EXPECTED.items():
            release = load_product_release(ROOT / "skills" / name)
            self.assertIsInstance(release, ProductRelease)
            self.assertEqual(release.name, name)
            self.assertEqual(release.version, version)
            self.assertEqual(release.tag, f"{name}-v{version}")
            self.assertEqual(validate_product(release.root), [])

    def test_one_product_version_can_change_without_changing_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "graspic"
            shutil.copytree(ROOT / "skills" / "graspic", root)
            manifest = root / "release.toml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace('version = "3.0.0"', 'version = "3.0.1"'),
                encoding="utf-8",
            )
            errors = validate_product(root)
            self.assertIn("release.toml version 3.0.1 != SKILL.md version 3.0.0", errors)

    def test_payload_hash_changes_with_bytes_but_is_stable_across_copies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            original = ROOT / "skills" / "image-workbench"
            copy = Path(directory) / "image-workbench"
            shutil.copytree(original, copy)
            self.assertEqual(payload_sha256(original), payload_sha256(copy))
            before = payload_sha256(copy)
            skill_md = copy / "SKILL.md"
            skill_md.write_text(skill_md.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertNotEqual(before, payload_sha256(copy))


class ProductReleaseRejectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _copy(self, name: str) -> Path:
        destination = self.workspace / name
        shutil.copytree(ROOT / "skills" / name, destination)
        return destination

    def test_rejects_invalid_semver(self) -> None:
        root = self._copy("korean-writing-editor")
        manifest = root / "release.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                'version = "2.0.1"',
                'version = "2.0"',
            ),
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(root))
        self.assertIn("invalid SemVer: 2.0", errors)

    def test_rejects_mismatched_directory_name(self) -> None:
        root = self._copy("image-workbench")
        manifest = root / "release.toml"
        manifest.write_text(
            manifest.read_text(encoding="utf-8").replace(
                'name = "image-workbench"',
                'name = "other-skill"',
            ),
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(root))
        self.assertIn("directory/release.toml name mismatch", errors)

    def test_rejects_missing_changelog(self) -> None:
        root = self._copy("graspic")
        (root / "CHANGELOG.md").unlink()
        errors = "\n".join(validate_product(root))
        self.assertIn("missing CHANGELOG.md", errors)

    def test_rejects_missing_license(self) -> None:
        root = self._copy("korean-writing-editor")
        (root / "LICENSE.txt").unlink()
        errors = "\n".join(validate_product(root))
        self.assertIn("missing Apache license", errors)

    @unittest.skipIf(
        os.name == "nt" or not hasattr(os, "mkfifo"),
        "symlink and FIFO fixtures require Unix",
    )
    def test_rejects_symlink_and_special_file(self) -> None:
        root = self._copy("graspic")
        (root / "link.md").symlink_to("SKILL.md")
        os.mkfifo(root / "pipe")
        errors = "\n".join(validate_product(root))
        self.assertIn("symlink is not allowed: link.md", errors)
        self.assertIn("special file is not allowed: pipe", errors)

    def test_rejects_unsafe_relative_link(self) -> None:
        root = self._copy("korean-writing-editor")
        skill_md = root / "SKILL.md"
        skill_md.write_text(
            skill_md.read_text(encoding="utf-8") + "\n[escape](../LICENSE)\n",
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(root))
        self.assertIn("broken relative link", errors)

    def test_rejects_unexpected_top_level_file(self) -> None:
        root = self._copy("image-workbench")
        (root / "notes.txt").write_text("not part of the product\n", encoding="utf-8")
        errors = "\n".join(validate_product(root))
        self.assertIn("unexpected top-level file: notes.txt", errors)

    def test_dated_release_validation_is_opt_in(self) -> None:
        from scripts.release_contract import require_dated_changelog

        source = ROOT / "skills" / "graspic"
        self.assertEqual(validate_product(source), [])
        self.assertIn(
            "CHANGELOG.md missing dated release heading for 3.0.0",
            require_dated_changelog(source),
        )
        root = self._copy("graspic")
        changelog = root / "CHANGELOG.md"
        changelog.write_text(
            changelog.read_text(encoding="utf-8").replace(
                "## Unreleased\n",
                "## Unreleased\n\n## 3.0.0 - 2026-08-27\n",
                1,
            ),
            encoding="utf-8",
        )
        self.assertEqual(require_dated_changelog(root), [])
        self.assertEqual(validate_product(root), [])


class PayloadEntryTests(unittest.TestCase):
    def test_payload_entries_are_sorted_with_normalized_modes(self) -> None:
        from scripts.release_contract import payload_entries

        entries = payload_entries(ROOT / "skills" / "image-workbench")
        paths = [entry["path"] for entry in entries]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(paths, sorted(set(paths)))
        for entry in entries:
            self.assertEqual(set(entry), {"path", "mode", "size", "sha256"})
            self.assertIn(entry["mode"], {"0644", "0755"})
            self.assertIsInstance(entry["size"], int)
            self.assertGreaterEqual(entry["size"], 0)
            self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
        by_path = {entry["path"]: entry for entry in entries}
        self.assertEqual(by_path["scripts/inspect_asset.py"]["mode"], "0755")
        self.assertEqual(by_path["SKILL.md"]["mode"], "0644")
        self.assertIn("release.toml", by_path)
        self.assertIn("CHANGELOG.md", by_path)


if __name__ == "__main__":
    unittest.main()
