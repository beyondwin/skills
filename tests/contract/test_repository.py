from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
import unittest
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[2]
SKILLS = (
    ROOT / "skills" / "korean-writing-editor",
    ROOT / "skills" / "image-workbench",
)
ALLOWED_SKILLS = {skill.name for skill in SKILLS}
PLUGIN_PATH = ROOT / ".codex-plugin" / "plugin.json"
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
FORBIDDEN_PAYLOAD_NAMES = frozenset({"README.md", "CHANGE_PROTOCOL.md", "evals", "tests"})
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
EXPECTED_VERSION = "2.0.0"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HOME_PREFIX = "/Users/"
ARCHIVE_MARKERS = ("SKILLS_ARCHIVE_CHECKOUT", "source/private")
CREDENTIAL_MARKERS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CURSOR_API_KEY")
IGNORE_NAMES = frozenset({"__pycache__"})
BYTECODE_SUFFIXES = {".pyc", ".pyo"}


def load_plugin_manifest() -> dict[str, object]:
    return json.loads(PLUGIN_PATH.read_text(encoding="utf-8"))


def validate_skill(skill_root: Path) -> list[str]:
    errors: list[str] = []
    skill_root = Path(skill_root)
    if skill_root.name not in ALLOWED_SKILLS:
        errors.append(f"third skill is not accepted: {skill_root.name}")
        return errors

    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        errors.append("missing SKILL.md")
        return errors

    skill_text = skill_md.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(skill_text)
    if frontmatter.get("name") != skill_root.name:
        errors.append("directory/frontmatter name mismatch")
    if frontmatter.get("license") != "Apache-2.0":
        errors.append("missing Apache declaration")
    metadata = frontmatter.get("metadata")
    version = metadata.get("version") if isinstance(metadata, dict) else None
    if version != EXPECTED_VERSION:
        errors.append("version mismatch")

    license_path = skill_root / "LICENSE.txt"
    if not license_path.is_file():
        errors.append("missing Apache license")
    else:
        license_text = license_path.read_text(encoding="utf-8")
        if "Apache License" not in license_text or "Version 2.0" not in license_text:
            errors.append("missing Apache license")

    openai_path = skill_root / "agents" / "openai.yaml"
    if not openai_path.is_file():
        errors.append("missing agents/openai.yaml")
    else:
        errors.extend(_validate_openai_yaml(openai_path, skill_root.name))

    for path in _iter_payload_paths(skill_root):
        relative = path.relative_to(skill_root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            errors.append(f"symlink is not allowed: {relative}")
            continue
        if any(part in FORBIDDEN_PAYLOAD_NAMES for part in path.relative_to(skill_root).parts):
            errors.append(f"payload test/eval/maintainer file: {relative}")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            errors.append(f"special file is not allowed: {relative}")
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if HOME_PREFIX in content:
            errors.append(f"personal macOS home-prefix path in {relative}")
        if any(marker in content for marker in ARCHIVE_MARKERS):
            errors.append(f"Archive checkout assumption in {relative}")
        if any(marker in content for marker in CREDENTIAL_MARKERS):
            errors.append(f"credential-like token in {relative}")
        if any(identifier in content for identifier in LEGACY_IDENTIFIERS):
            errors.append(f"legacy prefixed identifier in {relative}")
        if path.suffix.lower() in {".md", ".markdown"}:
            errors.extend(_check_relative_links(skill_root, relative, content))
    return errors


def stage_skill(skill_root: Path, destination: Path) -> Path:
    errors = validate_skill(skill_root)
    if errors:
        raise ValueError("\n".join(errors))
    target = Path(destination) / skill_root.name
    shutil.copytree(
        skill_root,
        target,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        symlinks=False,
    )
    staged_errors = validate_skill(target)
    if staged_errors:
        raise ValueError("\n".join(staged_errors))
    return target


def _parse_frontmatter(text: str) -> dict[str, object]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, object] = {}
    metadata: dict[str, str] = {}
    in_metadata = False
    for raw_line in match.group(1).splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line == "metadata:":
            in_metadata = True
            continue
        if in_metadata and line.startswith("  ") and ":" in line:
            key, value = line.strip().split(":", 1)
            metadata[key.strip()] = value.strip().strip("\"'")
            continue
        in_metadata = False
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    if metadata:
        data["metadata"] = metadata
    return data


def _validate_openai_yaml(path: Path, skill_name: str) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for field in ("display_name:", "short_description:", "default_prompt:"):
        if field not in text:
            errors.append(f"missing {field[:-1]} in agents/openai.yaml")
    if f"${skill_name}" not in text:
        errors.append("default_prompt must mention the skill")
    if "allow_implicit_invocation: true" not in text:
        errors.append("invocation policy must match the skill activation gate")
    if "allow_implicit_invocation: false" in text:
        errors.append("invocation policy bypasses excluded near misses")
    return errors


def _check_relative_links(skill_root: Path, relative_path: str, text: str) -> list[str]:
    errors: list[str] = []
    base = (skill_root / relative_path).parent
    for href in MARKDOWN_LINK_RE.findall(text):
        target = href.strip()
        if not target or target.startswith("#"):
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (base / path_part).resolve()
        try:
            resolved.relative_to(skill_root.resolve())
        except ValueError:
            errors.append(f"broken relative link in {relative_path}: {target}")
            continue
        if not resolved.exists():
            errors.append(f"broken relative link in {relative_path}: {target}")
    return errors


def _iter_payload_paths(skill_root: Path):
    for path in skill_root.rglob("*"):
        parts = path.relative_to(skill_root).parts
        if any(part in IGNORE_NAMES or Path(part).suffix in BYTECODE_SUFFIXES for part in parts):
            continue
        yield path


def _copy_skill(source: Path, destination: Path) -> Path:
    staged = destination / source.name
    shutil.copytree(
        source,
        staged,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return staged


class PluginManifestTests(unittest.TestCase):
    def test_plugin_discovers_exactly_two_skills(self) -> None:
        self.assertTrue(PLUGIN_PATH.is_file(), "plugin manifest is absent")
        manifest = load_plugin_manifest()
        self.assertEqual(manifest["name"], "beyondwin-skills")
        self.assertEqual(manifest["version"], "2.0.0")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(
            {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()},
            {"korean-writing-editor", "image-workbench"},
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
            self.assertEqual(validate_skill(skill), [])


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
        errors = "\n".join(validate_skill(staged))
        self.assertIn("directory/frontmatter name mismatch", errors)

    def test_rejects_version_mismatch(self) -> None:
        source = SKILLS[1]
        staged = self._mutated(
            source,
            lambda skill: (skill / "SKILL.md").write_text(
                (skill / "SKILL.md").read_text(encoding="utf-8").replace(
                    'version: "2.0.0"',
                    'version: "1.0.0"',
                    1,
                ),
                encoding="utf-8",
            ),
        )
        errors = "\n".join(validate_skill(staged))
        self.assertIn("version mismatch", errors)

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
        errors = "\n".join(validate_skill(staged))
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
        errors = "\n".join(validate_skill(staged))
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
        errors = "\n".join(validate_skill(staged))
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
        errors = "\n".join(validate_skill(staged))
        self.assertIn("Archive checkout assumption", errors)

    def test_rejects_payload_test_eval_or_maintainer_file(self) -> None:
        source = SKILLS[0]
        staged = self._mutated(
            source,
            lambda skill: (skill / "README.md").write_text("maintainer notes\n", encoding="utf-8"),
        )
        errors = "\n".join(validate_skill(staged))
        self.assertIn("payload test/eval/maintainer file", errors)

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
        errors = "\n".join(validate_skill(staged))
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
        errors = "\n".join(validate_skill(staged))
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
        errors = "\n".join(validate_skill(skill))
        self.assertIn("third skill", errors)

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
        errors = "\n".join(validate_skill(staged))
        self.assertIn("legacy prefixed identifier", errors)


class StageSkillTests(unittest.TestCase):
    def test_stage_skill_copies_a_valid_payload(self) -> None:
        source = SKILLS[0]
        self.assertTrue(
            (source / "LICENSE.txt").is_file(),
            "korean-writing-editor LICENSE.txt is absent",
        )
        with tempfile.TemporaryDirectory() as directory:
            staged = stage_skill(source, Path(directory))
            self.assertEqual(staged.name, source.name)
            self.assertTrue((staged / "SKILL.md").is_file())
            self.assertTrue((staged / "LICENSE.txt").is_file())
            self.assertTrue((staged / "agents" / "openai.yaml").is_file())
            self.assertFalse((staged / "README.md").exists())
            self.assertFalse((staged / "evals").exists())
            self.assertEqual(validate_skill(staged), [])

    def test_stage_skill_rejects_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            mutated = _copy_skill(SKILLS[0], workspace / "source")
            (mutated / "README.md").write_text("maintainer notes\n", encoding="utf-8")
            with self.assertRaises(ValueError) as raised:
                stage_skill(mutated, workspace / "dest")
            self.assertIn("payload test/eval/maintainer file", str(raised.exception))


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
            ROOT / "docs" / "maintainers" / "archive-source-manifest.json"
        ).read_text(encoding="utf-8")
        notes = (ROOT / "docs" / "maintainers" / "archive-migration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("kws-korean-writing-editor", manifest)
        self.assertIn("kws-image-workbench", manifest)
        self.assertIn("kws-korean-writing-editor", notes)
        self.assertIn("kws-image-workbench", notes)


if __name__ == "__main__":
    unittest.main()
