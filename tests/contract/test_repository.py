from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import (  # noqa: E402
    stage_product,
    validate_product,
)
from scripts.lib.product_registry import load_registry  # noqa: E402

REGISTRY = load_registry(ROOT / "products.toml")
SKILLS = tuple(ROOT / "skills" / name for name in REGISTRY.names)
PLUGIN_PATH = ROOT / "catalog" / "plugin" / ".codex-plugin" / "plugin.json"
LICENSE_PATH = ROOT / "LICENSE"
NOTICE_PATH = ROOT / "NOTICE"
ARCHIVE_REPOSITORY = "https://github.com/beyondwin/Archive.git"
PINNED_SOURCE_COMMIT = "76e6bf4ebbc9430aee9a04a5b780ae38330f3021"
MANIFEST_DIGEST = "6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78"
EXPECTED_PLUGIN: dict[str, object] = {
    "name": "beyondwin-skills",
    "version": "2.0.0",
    "description": "Two conservative, project-aware skills for Korean editing and raster asset work.",
    "author": {"name": "beyondwin", "url": "https://github.com/beyondwin"},
    "homepage": "https://github.com/beyondwin/skills",
    "repository": "https://github.com/beyondwin/skills",
    "license": "Apache-2.0",
    "keywords": ["agent-skills", "codex", "korean-writing", "image-workbench"],
    "skills": "./skills/",
    "interface": {
        "displayName": "Beyondwin Skills",
        "shortDescription": "Korean editing and raster asset workflows",
        "longDescription": (
            "A curated pair of Codex-first skills for conservative Korean text "
            "editing and project-bound raster asset work."
        ),
        "developerName": "beyondwin",
        "category": "Developer Tools",
        "capabilities": ["Interactive", "Read", "Write"],
        "websiteURL": "https://github.com/beyondwin/skills",
        "defaultPrompt": [
            "Polish supplied Korean text",
            "Plan or audit a project raster asset",
        ],
    },
}
FORBIDDEN_PAYLOAD_NAMES = frozenset({"CHANGE_PROTOCOL.md", "evals", "tests"})
UNSUPPORTED_PLUGIN_FIELDS = ("hooks", "mcpServers", "apps")
UNSUPPORTED_INTERFACE_FIELDS = (
    "privacyPolicyURL",
    "termsOfServiceURL",
    "logo",
    "composerIcon",
    "logoDark",
    "screenshots",
    "brandColor",
)
LEGACY_IDENTIFIERS = (
    "kws-korean-writing-editor",
    "kws-image-workbench",
)


def load_plugin_manifest() -> dict[str, object]:
    return json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))


def _copy_skill(source: Path, destination: Path) -> Path:
    staged = destination / source.name
    shutil.copytree(
        source,
        staged,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return staged


class PluginManifestTests(unittest.TestCase):
    def test_plugin_discovers_the_curated_skills(self) -> None:
        self.assertFalse((ROOT / ".codex-plugin" / "plugin.json").exists())
        self.assertTrue(PLUGIN_PATH.is_file(), "plugin manifest is absent")
        manifest = load_plugin_manifest()
        self.assertEqual(manifest["name"], "beyondwin-skills")
        self.assertEqual(manifest["version"], "2.0.0")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("graspic", json.dumps(manifest))

    def test_skill_directories_include_unpublished_current_products(self) -> None:
        self.assertEqual(
            {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()},
            {"graspic", "image-workbench", "korean-writing-editor"},
        )

    def test_plugin_manifest_matches_curated_bundle(self) -> None:
        self.assertTrue(PLUGIN_PATH.is_file(), "plugin manifest is absent")
        self.assertEqual(load_plugin_manifest(), EXPECTED_PLUGIN)

    def test_plugin_omits_unsupported_components(self) -> None:
        self.assertTrue(PLUGIN_PATH.is_file(), "plugin manifest is absent")
        manifest = load_plugin_manifest()
        for field in UNSUPPORTED_PLUGIN_FIELDS:
            self.assertNotIn(field, manifest)
        interface = manifest["interface"]
        self.assertIsInstance(interface, dict)
        for field in UNSUPPORTED_INTERFACE_FIELDS:
            self.assertNotIn(field, interface)


class LicenseNoticeTests(unittest.TestCase):
    def test_root_license_is_apache_2(self) -> None:
        self.assertTrue(LICENSE_PATH.is_file(), "root LICENSE is absent")
        text = LICENSE_PATH.read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)
        self.assertIn("http://www.apache.org/licenses/", text)

    def test_skill_licenses_are_complete_copies_of_root(self) -> None:
        self.assertTrue(LICENSE_PATH.is_file(), "root LICENSE is absent")
        root_text = LICENSE_PATH.read_text(encoding="utf-8")
        for skill in SKILLS:
            license_path = skill / "LICENSE.txt"
            self.assertTrue(license_path.is_file(), f"{skill.name} LICENSE.txt is absent")
            self.assertEqual(license_path.read_text(encoding="utf-8"), root_text)

    def test_notice_records_archive_provenance(self) -> None:
        self.assertTrue(NOTICE_PATH.is_file(), "NOTICE is absent")
        text = NOTICE_PATH.read_text(encoding="utf-8")
        self.assertIn("beyondwin-skills", text)
        self.assertIn("beyondwin", text)
        self.assertIn(ARCHIVE_REPOSITORY, text)
        self.assertIn(PINNED_SOURCE_COMMIT, text)
        self.assertIn(MANIFEST_DIGEST, text)
        self.assertNotIn("manifest path", text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("source/private", text)
        self.assertNotIn("SKILLS_ARCHIVE_CHECKOUT", text)


class InstalledPayloadTests(unittest.TestCase):
    def test_installed_payload_excludes_maintainer_material(self) -> None:
        for skill in SKILLS:
            self.assertTrue(skill.is_dir(), f"{skill.name} payload is absent")
            names = {path.name for path in skill.iterdir()}
            self.assertFalse(FORBIDDEN_PAYLOAD_NAMES.intersection(names))

    def test_installed_payloads_satisfy_package_closure(self) -> None:
        for skill in SKILLS:
            self.assertTrue(
                (skill / "LICENSE.txt").is_file(),
                f"{skill.name} LICENSE.txt is absent",
            )
            self.assertTrue(
                (skill / "agents" / "openai.yaml").is_file(),
                f"{skill.name} openai.yaml is absent",
            )
            self.assertTrue(
                (skill / "CHANGELOG.md").is_file(),
                f"{skill.name} CHANGELOG.md is absent",
            )
            self.assertTrue(
                (skill / "release.toml").is_file(),
                f"{skill.name} release.toml is absent",
            )
            self.assertEqual(validate_product(skill, REGISTRY), [])


class OpenAIMetadataTests(unittest.TestCase):
    def test_openai_yaml_has_display_metadata_and_matching_policy(self) -> None:
        for skill in SKILLS:
            path = skill / "agents" / "openai.yaml"
            self.assertTrue(path.is_file(), f"{skill.name} openai.yaml is absent")
            text = path.read_text(encoding="utf-8")
            self.assertIn("display_name:", text)
            self.assertIn("short_description:", text)
            self.assertIn("default_prompt:", text)
            self.assertIn(f"${skill.name}", text)
            self.assertIn("allow_implicit_invocation: true", text)
            self.assertNotIn("allow_implicit_invocation: false", text)
            for identifier in LEGACY_IDENTIFIERS:
                self.assertNotIn(identifier, text)
            lowered = text.lower()
            self.assertNotIn("translate", lowered)
            self.assertNotIn("detector", lowered)
            self.assertNotIn("prompt gallery", lowered)


class ValidateSkillRejectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tempdir = tempfile.TemporaryDirectory()
        self.workspace = Path(self._tempdir.name)

    def tearDown(self) -> None:
        self._tempdir.cleanup()

    def _mutated(
        self,
        source: Path,
        mutator: Callable[[Path], None],
    ) -> Path:
        staged = _copy_skill(source, self.workspace / source.name)
        mutator(staged)
        return staged

    def test_rejects_directory_frontmatter_name_mismatch(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8").replace(
                    f"name: {skill.name}",
                    "name: other-skill",
                    1,
                ),
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("directory/frontmatter name mismatch", errors)

    def test_rejects_version_mismatch(self) -> None:
        source = SKILLS[1]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8").replace(
                    'version: "2.0.1"',
                    'version: "1.0.0"',
                    1,
                ),
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn(
            "release.toml version 2.0.1 != SKILL.md version 1.0.0",
            errors,
        )

    def test_rejects_missing_apache_declaration_and_license(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (
                (skill / "SKILL.md").write_text(
                    (skill / "SKILL.md").read_text(encoding="utf-8").replace(
                        "license: Apache-2.0",
                        "license: MIT",
                        1,
                    ),
                    encoding="utf-8",
                ),
                (skill / "LICENSE.txt").unlink(missing_ok=True),
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("missing Apache declaration", errors)
        self.assertIn("missing Apache license", errors)

    def test_rejects_broken_relative_link(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\n[missing](references/does-not-exist.md)\n",
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("broken relative link", errors)

    def test_rejects_personal_macos_home_prefix_path(self) -> None:
        source = SKILLS[1]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\nDo not read /Users/someone/secret.png\n",
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("personal macOS home-prefix path", errors)

    def test_rejects_archive_checkout_assumption(self) -> None:
        source = SKILLS[1]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\nResolve SKILLS_ARCHIVE_CHECKOUT before running.\n",
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("Archive checkout assumption", errors)

    def test_rejects_payload_test_eval_or_maintainer_file(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (
                (skill / "evals").mkdir(),
                (skill / "evals" / "case.json").write_text("{}\n", encoding="utf-8"),
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("payload test/eval/maintainer file", errors)

    def test_permits_readme_names(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (
                (skill / "README.md").write_text("# Korean Writing Editor\n", encoding="utf-8"),
                (skill / "README.en.md").write_text("# Korean Writing Editor\n", encoding="utf-8"),
            ),
        )
        self.assertEqual(validate_product(staged, REGISTRY), [])

    @unittest.skipIf(
        os.name == "nt" or not hasattr(os, "mkfifo"),
        "symlink and FIFO fixtures require Unix",
    )
    def test_rejects_symlink_and_special_file(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (
                (skill / "link.md").symlink_to("SKILL.md"),
                os.mkfifo(skill / "pipe"),
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("symlink", errors)
        self.assertIn("special file", errors)

    def test_rejects_credential_like_token(self) -> None:
        source = SKILLS[1]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\nOPENAI_API_KEY=sk-example\n",
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("credential-like token", errors)

    def test_rejects_a_third_skill(self) -> None:
        skill = self.workspace / "unrelated-helper"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: unrelated-helper\nlicense: Apache-2.0\n"
            'metadata:\n  version: "2.0.0"\n---\n# Unrelated\n',
            encoding="utf-8",
        )
        (skill / "LICENSE.txt").write_text("Apache License\nVersion 2.0, January 2004\n")
        (skill / "agents").mkdir()
        (skill / "agents" / "openai.yaml").write_text(
            'interface:\n  display_name: "Unrelated Helper"\n'
            '  short_description: "Not one of the curated skills"\n'
            '  default_prompt: "Use $unrelated-helper."\n'
            "policy:\n  allow_implicit_invocation: true\n",
            encoding="utf-8",
        )
        errors = "\n".join(validate_product(skill, REGISTRY))
        self.assertIn("unlisted skill", errors)

    def test_rejects_legacy_prefixed_identifier_in_payload(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8")
                + "\nActivate $kws-korean-writing-editor instead.\n",
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_product(staged, REGISTRY))
        self.assertIn("legacy prefixed identifier", errors)


class StageProductTests(unittest.TestCase):
    def test_stage_product_copies_a_valid_payload(self) -> None:
        source = SKILLS[0]
        self.assertTrue(
            (source / "LICENSE.txt").is_file(),
            "korean-writing-editor LICENSE.txt is absent",
        )
        with tempfile.TemporaryDirectory() as directory:
            staged = stage_product(source, Path(directory), REGISTRY)
            self.assertEqual(staged.name, source.name)
            self.assertTrue((staged / "SKILL.md").is_file())
            self.assertTrue((staged / "LICENSE.txt").is_file())
            self.assertTrue((staged / "CHANGELOG.md").is_file())
            self.assertTrue((staged / "release.toml").is_file())
            self.assertTrue((staged / "agents" / "openai.yaml").is_file())
            self.assertTrue((staged / "README.md").is_file())
            self.assertTrue((staged / "README.en.md").is_file())
            self.assertFalse((staged / "evals").exists())
            self.assertEqual(validate_product(staged, REGISTRY), [])

    def test_stage_product_rejects_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            mutated = _copy_skill(SKILLS[0], workspace / "source")
            (mutated / "notes.txt").write_text("not part of the product\n", encoding="utf-8")
            with self.assertRaises(ValueError) as raised:
                stage_product(mutated, workspace / "dest", REGISTRY)
            self.assertIn("unexpected top-level file: notes.txt", str(raised.exception))

    def test_stage_product_permits_readme_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            mutated = _copy_skill(SKILLS[0], workspace / "source")
            (mutated / "README.md").write_text("# Korean Writing Editor\n", encoding="utf-8")
            (mutated / "README.en.md").write_text("# Korean Writing Editor\n", encoding="utf-8")
            staged = stage_product(mutated, workspace / "dest", REGISTRY)
            self.assertTrue((staged / "README.md").is_file())
            self.assertTrue((staged / "README.en.md").is_file())
            self.assertEqual(validate_product(staged, REGISTRY), [])


class LegacyIdentifierAllowlistTests(unittest.TestCase):
    def test_legacy_identifiers_remain_in_near_miss_fixtures(self) -> None:
        korean_cases = (
            ROOT / "tests" / "korean-writing-editor" / "offline" / "cases.json"
        ).read_text(encoding="utf-8")
        image_cases = (ROOT / "tests" / "image-workbench" / "cases.json").read_text(
            encoding="utf-8"
        )
        self.assertIn("kws-korean-writing-editor", korean_cases)
        self.assertIn("kws-image-workbench", image_cases)

    def test_legacy_identifiers_remain_in_pinned_migration_evidence(self) -> None:
        manifest = (
            ROOT / "docs" / "maintainers" / "repository" / "archive-source-manifest.json"
        ).read_text(encoding="utf-8")
        notes = (
            ROOT / "docs" / "maintainers" / "repository" / "archive-migration.md"
        ).read_text(encoding="utf-8")
        self.assertIn("kws-korean-writing-editor", manifest)
        self.assertIn("kws-image-workbench", manifest)
        self.assertIn("kws-korean-writing-editor", notes)
        self.assertIn("kws-image-workbench", notes)


if __name__ == "__main__":
    unittest.main()
