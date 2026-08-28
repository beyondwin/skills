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

from scripts.lib.product_contract import (  # noqa: E402
    ProductRelease,
    load_product_release,
    payload_sha256,
    validate_product,
)
from scripts.lib.product_registry import load_registry  # noqa: E402

EXPECTED = {
    "korean-writing-editor": "2.0.1",
    "image-workbench": "2.0.1",
    "how-it-works": "1.0.0",
}
REGISTRY = load_registry(ROOT / "products.toml")


class ProductReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = ROOT
        self.registry = REGISTRY

    def test_unregistered_skill_is_rejected(self) -> None:
        errors = validate_product(self.root / "skills" / "not-registered", self.registry)
        self.assertIn("unlisted skill is not accepted: not-registered", errors)

    def test_registered_names_come_only_from_products_toml(self) -> None:
        source = (ROOT / "scripts/lib/product_contract.py").read_text(encoding="utf-8")
        self.assertNotIn("PRODUCT_NAMES =", source)
        self.assertEqual(self.registry.names, tuple(product.name for product in self.registry.products))

    def test_each_product_owns_an_independent_release_manifest(self) -> None:
        self.assertEqual(set(self.registry.names), set(EXPECTED))
        for name, version in EXPECTED.items():
            release = load_product_release(ROOT / "skills" / name)
            self.assertIsInstance(release, ProductRelease)
            self.assertEqual(release.name, name)
            self.assertEqual(release.version, version)
            self.assertEqual(release.tag, f"{name}-v{version}")
            self.assertEqual(validate_product(release.root, self.registry), [])

    def test_one_product_version_can_change_without_changing_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "how-it-works"
            shutil.copytree(ROOT / "skills" / "how-it-works", root)
            manifest = root / "release.toml"
            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace('version = "1.0.0"', 'version = "1.0.1"'),
                encoding="utf-8",
            )
            errors = validate_product(root, self.registry)
            self.assertIn("release.toml version 1.0.1 != SKILL.md version 1.0.0", errors)

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
        errors = "\n".join(validate_product(root, REGISTRY))
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
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("directory/release.toml name mismatch", errors)

    def test_rejects_missing_changelog(self) -> None:
        root = self._copy("how-it-works")
        (root / "CHANGELOG.md").unlink()
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("missing CHANGELOG.md", errors)

    def test_rejects_missing_korean_readme(self) -> None:
        root = self._copy("how-it-works")
        readme = root / "README.md"
        if readme.is_file():
            readme.unlink()
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("missing README.md", errors)

    def test_rejects_missing_english_readme(self) -> None:
        root = self._copy("image-workbench")
        readme = root / "README.en.md"
        if readme.is_file():
            readme.unlink()
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("missing README.en.md", errors)

    def test_rejects_missing_license(self) -> None:
        root = self._copy("korean-writing-editor")
        (root / "LICENSE.txt").unlink()
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("missing Apache license", errors)

    @unittest.skipIf(
        os.name == "nt" or not hasattr(os, "mkfifo"),
        "symlink and FIFO fixtures require Unix",
    )
    def test_rejects_symlink_and_special_file(self) -> None:
        root = self._copy("how-it-works")
        (root / "link.md").symlink_to("SKILL.md")
        os.mkfifo(root / "pipe")
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("symlink is not allowed: link.md", errors)
        self.assertIn("special file is not allowed: pipe", errors)

    def test_rejects_unsafe_relative_link(self) -> None:
        root = self._copy("korean-writing-editor")
        skill_md = root / "SKILL.md"
        skill_md.write_text(
            skill_md.read_text(encoding="utf-8") + "\n[escape](../LICENSE)\n",
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("broken relative link", errors)

    def test_rejects_unexpected_top_level_file(self) -> None:
        root = self._copy("image-workbench")
        (root / "notes.txt").write_text("not part of the product\n", encoding="utf-8")
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("unexpected top-level file: notes.txt", errors)

    def test_rejects_directory_frontmatter_name_mismatch(self) -> None:
        root = self._copy("how-it-works")
        skill_md = root / "SKILL.md"
        skill_md.write_text(
            skill_md.read_text(encoding="utf-8").replace(
                "name: how-it-works\n",
                "name: other-skill\n",
                1,
            ),
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("directory/frontmatter name mismatch", errors)

    def test_multi_host_product_rejects_non_portable_frontmatter(self) -> None:
        root = self._copy("how-it-works")
        skill_md = root / "SKILL.md"
        skill_md.write_text(
            skill_md.read_text(encoding="utf-8").replace(
                "license: Apache-2.0\n",
                'license: Apache-2.0\nargument-hint: "<topic>"\n',
                1,
            ),
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("non-portable frontmatter field: argument-hint", errors)

    def test_single_host_product_allows_non_portable_frontmatter(self) -> None:
        root = self._copy("korean-writing-editor")
        skill_md = root / "SKILL.md"
        skill_md.write_text(
            skill_md.read_text(encoding="utf-8").replace(
                "license: Apache-2.0\n",
                'license: Apache-2.0\nargument-hint: "<text>"\n',
                1,
            ),
            encoding="utf-8",
        )
        self.assertEqual(validate_product(root, REGISTRY), [])

    def test_openai_yaml_is_optional_presentation_metadata(self) -> None:
        root = self._copy("how-it-works")
        (root / "agents" / "openai.yaml").unlink()
        errors = validate_product(root, REGISTRY)
        self.assertNotIn("missing agents/openai.yaml", errors)
        self.assertEqual(errors, [])

    def test_openai_yaml_default_prompt_must_use_current_product_name(self) -> None:
        root = self._copy("how-it-works")
        (root / "agents" / "openai.yaml").write_text(
            'interface:\n'
            '  display_name: "How It Works"\n'
            '  short_description: "Use $how-it-works in presentation copy"\n'
            '  default_prompt: "Explain this mechanism."\n'
            "policy:\n"
            "  allow_implicit_invocation: true\n",
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(root, REGISTRY))
        self.assertIn("default_prompt must mention the skill", errors)

    def test_dated_release_validation_is_opt_in(self) -> None:
        from scripts.lib.product_contract import require_dated_changelog

        source = ROOT / "skills" / "how-it-works"
        self.assertEqual(validate_product(source, REGISTRY), [])
        self.assertIn(
            "CHANGELOG.md missing dated release heading for 1.0.0",
            require_dated_changelog(source),
        )
        root = self._copy("how-it-works")
        changelog = root / "CHANGELOG.md"
        changelog.write_text(
            changelog.read_text(encoding="utf-8").replace(
                "## Unreleased\n",
                "## Unreleased\n\n## 1.0.0 - 2026-08-27\n",
                1,
            ),
            encoding="utf-8",
        )
        self.assertEqual(require_dated_changelog(root), [])
        self.assertEqual(validate_product(root, REGISTRY), [])


class PayloadEntryTests(unittest.TestCase):
    def test_payload_entries_are_sorted_with_normalized_modes(self) -> None:
        from scripts.lib.product_contract import payload_entries

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
