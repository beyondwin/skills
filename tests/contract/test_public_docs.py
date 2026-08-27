from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SHARED_FACTS = (
    "2.0.0",
    "korean-writing-editor",
    "image-workbench",
    "graspic",
    "python3 scripts/verify.py",
    "Apache-2.0",
)
KOREAN_SUPPORT = (
    "korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke."
)
IMAGE_SUPPORT = (
    "image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing."
)
GRASPIC_SUPPORT = (
    "graspic: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke."
)
OFFLINE_EVIDENCE = "Offline fixtures: deterministic contract evidence only."
LIVE_EVIDENCE = (
    "Live execution: local, explicit, optional, potentially billable, and never required by CI."
)
SUPPORT_AND_EVIDENCE = (
    KOREAN_SUPPORT,
    IMAGE_SUPPORT,
    GRASPIC_SUPPORT,
    OFFLINE_EVIDENCE,
    LIVE_EVIDENCE,
)
PRIMARY_INSTALL_PATHS = (
    "https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor",
    "https://github.com/beyondwin/skills/tree/main/skills/image-workbench",
    "https://github.com/beyondwin/skills/tree/main/skills/graspic",
)
OPTIONAL_NPX = "npx skills add beyondwin/skills --skill korean-writing-editor"
GIT_CLONE = "git clone https://github.com/beyondwin/skills"
LIVE_BUDGETS = ("119", "3", "122", "38", "160")
README_PATHS = (ROOT / "README.md", ROOT / "README.en.md")
USER_GUIDES = (
    ROOT / "docs" / "ko" / "getting-started.md",
    ROOT / "docs" / "ko" / "compatibility.md",
    ROOT / "docs" / "ko" / "privacy-and-rights.md",
    ROOT / "docs" / "ko" / "evaluation.md",
    ROOT / "docs" / "en" / "getting-started.md",
    ROOT / "docs" / "en" / "compatibility.md",
    ROOT / "docs" / "en" / "privacy-and-rights.md",
    ROOT / "docs" / "en" / "evaluation.md",
)
MAINTAINER_DOCS = (
    ROOT / "docs" / "maintainers" / "architecture.md",
    ROOT / "docs" / "maintainers" / "release-process.md",
    ROOT / "docs" / "maintainers" / "korean-writing-editor.md",
    ROOT / "docs" / "maintainers" / "image-workbench.md",
    ROOT / "docs" / "maintainers" / "graspic.md",
)
CATALOG_DOCS = (
    ROOT / "catalog" / "README.md",
    ROOT / "catalog" / "CHANGELOG.md",
)
ARCHIVE_MIGRATION = ROOT / "docs" / "maintainers" / "archive-migration.md"
PUBLIC_DOC_PATHS = README_PATHS + USER_GUIDES + MAINTAINER_DOCS + CATALOG_DOCS
FUTURE_COMMUNITY_FILES = frozenset(
    {
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
    }
)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
UNSAFE_INSTALL = (
    "curl | sh",
    "curl|sh",
    "rm -rf",
)
FORBIDDEN_CLAIMS = (
    "best quality",
    "human-like",
    "production verified",
    "rights clearance",
    "provider superiority",
    "universal host support",
    "listed in a marketplace",
    "available in the marketplace",
)
PERSONAL_MARKERS = ("/Users/", "source/private", "SKILLS_ARCHIVE_CHECKOUT")
README_ORDER_EN = (
    "beyondwin-skills",
    "actions/workflows/verify.yml",
    "korean-writing-editor",
    "$skill-installer",
    "Exclusions",
    "Offline fixtures",
    "CONTRIBUTING.md",
)
README_ORDER_KO = (
    "beyondwin-skills",
    "actions/workflows/verify.yml",
    "korean-writing-editor",
    "$skill-installer",
    "제외",
    "Offline fixtures",
    "CONTRIBUTING.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_exists(test: unittest.TestCase, path: Path) -> None:
    test.assertTrue(path.is_file(), f"{path.relative_to(ROOT).as_posix()} is absent")


class ReadmeFactTests(unittest.TestCase):
    def test_readmes_share_release_and_command_facts(self) -> None:
        for document in README_PATHS:
            _assert_exists(self, document)
            text = _read(document)
            for fact in SHARED_FACTS:
                self.assertIn(fact, text)

    def test_readmes_state_exact_support_and_evidence_sentences(self) -> None:
        for document in README_PATHS:
            _assert_exists(self, document)
            text = _read(document)
            for sentence in SUPPORT_AND_EVIDENCE:
                self.assertIn(sentence, text)

    def test_readmes_follow_approved_section_order(self) -> None:
        cases = (
            (ROOT / "README.md", README_ORDER_KO),
            (ROOT / "README.en.md", README_ORDER_EN),
        )
        for document, markers in cases:
            _assert_exists(self, document)
            text = _read(document)
            positions = []
            last = -1
            for marker in markers:
                pos = text.find(marker)
                self.assertGreaterEqual(pos, 0, f"{document.name} missing {marker!r}")
                self.assertGreater(pos, last, f"{document.name} out of order: {marker!r}")
                positions.append(pos)
                last = pos
            self.assertEqual(positions, sorted(positions))

    def test_korean_readme_is_korean_and_english_readme_is_complete(self) -> None:
        _assert_exists(self, ROOT / "README.md")
        _assert_exists(self, ROOT / "README.en.md")
        korean = _read(ROOT / "README.md")
        english = _read(ROOT / "README.en.md")
        self.assertRegex(korean, r"[가-힣]")
        self.assertIn("[English](README.en.md)", korean)
        self.assertIn("[한국어](README.md)", english)
        self.assertNotRegex(english.replace("[한국어](README.md)", ""), r"[가-힣]")
        self.assertGreater(len(english), 800)


class UserGuideFactTests(unittest.TestCase):
    def test_paired_user_guides_exist(self) -> None:
        for document in USER_GUIDES:
            _assert_exists(self, document)

    def test_both_languages_state_exact_support_and_evidence_sentences(self) -> None:
        documents = (
            ROOT / "docs" / "ko" / "compatibility.md",
            ROOT / "docs" / "en" / "compatibility.md",
            ROOT / "docs" / "ko" / "evaluation.md",
            ROOT / "docs" / "en" / "evaluation.md",
        )
        for document in documents:
            _assert_exists(self, document)
            text = _read(document)
            for sentence in SUPPORT_AND_EVIDENCE:
                self.assertIn(sentence, text)

    def test_getting_started_covers_install_update_and_inspection(self) -> None:
        for document in (
            ROOT / "docs" / "ko" / "getting-started.md",
            ROOT / "docs" / "en" / "getting-started.md",
        ):
            _assert_exists(self, document)
            text = _read(document)
            self.assertIn("$skill-installer", text)
            for path in PRIMARY_INSTALL_PATHS:
                self.assertIn(path, text)
            self.assertIn(OPTIONAL_NPX, text)
            self.assertIn(GIT_CLONE, text)
            self.assertIn("python3 scripts/verify.py", text)
            lowered = text.lower()
            self.assertTrue(
                "inspect" in lowered or "확인" in text,
                f"{document.name} must inspect the exact target before update/uninstall",
            )

    def test_privacy_docs_distinguish_evidence_types_and_deny_telemetry(self) -> None:
        for document in (
            ROOT / "docs" / "ko" / "privacy-and-rights.md",
            ROOT / "docs" / "en" / "privacy-and-rights.md",
        ):
            _assert_exists(self, document)
            text = _read(document)
            lowered = text.lower()
            self.assertIn("hash", lowered)
            self.assertIn("provenance", lowered)
            self.assertIn("consent", lowered)
            self.assertTrue("rights" in lowered or "권리" in text)
            self.assertTrue("telemetry" in lowered or "텔레메트리" in text)
            self.assertTrue(
                "no telemetry" in lowered or "텔레메트리 없음" in text or "does not include telemetry" in lowered,
                f"{document.name} must state the no-telemetry policy",
            )


class InstallSafetyTests(unittest.TestCase):
    def test_readmes_document_primary_optional_and_clone_installs(self) -> None:
        for document in README_PATHS:
            _assert_exists(self, document)
            text = _read(document)
            self.assertIn("$skill-installer", text)
            for path in PRIMARY_INSTALL_PATHS:
                self.assertIn(path, text)
            self.assertIn(OPTIONAL_NPX, text)
            self.assertTrue(
                "third-party" in text.lower() or "제3자" in text,
                f"{document.name} must label the npx installer as third-party",
            )
            self.assertIn(GIT_CLONE, text)

    def test_public_docs_omit_unsafe_install_and_update_commands(self) -> None:
        for document in PUBLIC_DOC_PATHS:
            _assert_exists(self, document)
            text = _read(document)
            for fragment in UNSAFE_INSTALL:
                self.assertNotIn(fragment, text)
            lowered = text.lower()
            self.assertNotIn("automatic replacement", lowered)
            self.assertNotIn("unchecked overwrite", lowered)


class RelativeLinkTests(unittest.TestCase):
    def test_public_relative_links_resolve(self) -> None:
        errors: list[str] = []
        for document in PUBLIC_DOC_PATHS:
            _assert_exists(self, document)
            text = _read(document)
            errors.extend(_relative_link_errors(document, text))
        self.assertEqual(errors, [])

    def test_readmes_link_to_paired_guides_and_community_files(self) -> None:
        korean = _read(ROOT / "README.md") if (ROOT / "README.md").is_file() else ""
        english = _read(ROOT / "README.en.md") if (ROOT / "README.en.md").is_file() else ""
        _assert_exists(self, ROOT / "README.md")
        _assert_exists(self, ROOT / "README.en.md")
        for href in (
            "docs/ko/getting-started.md",
            "docs/ko/compatibility.md",
            "docs/ko/privacy-and-rights.md",
            "docs/ko/evaluation.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "LICENSE",
        ):
            self.assertIn(f"]({href})", korean)
        for href in (
            "docs/en/getting-started.md",
            "docs/en/compatibility.md",
            "docs/en/privacy-and-rights.md",
            "docs/en/evaluation.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "LICENSE",
        ):
            self.assertIn(f"]({href})", english)


class MaintainerProtocolTests(unittest.TestCase):
    def test_architecture_owns_payload_and_test_separation(self) -> None:
        path = ROOT / "docs" / "maintainers" / "architecture.md"
        _assert_exists(self, path)
        text = _read(path)
        self.assertIn("skills/", text)
        self.assertIn("tests/", text)
        self.assertIn("beyondwin-skills", text)
        self.assertIn("python3 scripts/verify.py", text)
        self.assertIn("2.0.0", text)
        self.assertIn("catalog/plugin/.codex-plugin/plugin.json", text)
        self.assertIn("catalog/catalog.lock.json", text)
        self.assertIn("does not own plugin metadata", text)

    def test_korean_protocol_preserves_fixture_sync_and_live_budgets(self) -> None:
        path = ROOT / "docs" / "maintainers" / "korean-writing-editor.md"
        _assert_exists(self, path)
        text = _read(path)
        for token in ("trigger", "mode", "output", "tier"):
            self.assertIn(token, text.lower())
        for budget in LIVE_BUDGETS:
            self.assertIn(budget, text)
        self.assertIn("119", text)
        self.assertIn("producer", text.lower())
        self.assertIn("reviewer", text.lower())

    def test_image_protocol_preserves_route_authorization_spec_and_inspector(self) -> None:
        path = ROOT / "docs" / "maintainers" / "image-workbench.md"
        _assert_exists(self, path)
        text = _read(path)
        lowered = text.lower()
        self.assertIn("route", lowered)
        self.assertIn("authorization", lowered)
        self.assertIn("imagespec", lowered)
        self.assertIn("rubric", lowered)
        self.assertIn("inspector", lowered)

    def test_release_process_owns_clean_tree_archive_and_deletion_gates(self) -> None:
        path = ROOT / "docs" / "maintainers" / "release-process.md"
        _assert_exists(self, path)
        text = _read(path)
        lowered = text.lower()
        for token in (
            "clean",
            "archive",
            "extract",
            "checksum",
            "download",
            "deletion",
        ):
            self.assertIn(token, lowered)
        self.assertIn("SHA256SUMS", text)
        self.assertIn("v2.0.0", text)
        self.assertIn("catalog/plugin/.codex-plugin/plugin.json", text)
        self.assertIn("catalog.lock.json", text)
        self.assertIn("legacy-bundle", text)

    def test_archive_migration_freeze_record_is_preserved(self) -> None:
        _assert_exists(self, ARCHIVE_MIGRATION)
        text = _read(ARCHIVE_MIGRATION)
        self.assertIn("76e6bf4ebbc9430aee9a04a5b780ae38330f3021", text)
        self.assertIn(
            "6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78",
            text,
        )


class ChangelogPublicationTests(unittest.TestCase):
    def test_changelog_records_published_github_release(self) -> None:
        path = ROOT / "catalog" / "CHANGELOG.md"
        _assert_exists(self, path)
        text = _read(path)
        self.assertIn(
            "https://github.com/beyondwin/skills/releases/tag/v2.0.0",
            text,
        )
        self.assertNotIn(
            "It does not claim that a GitHub tag, GitHub Release",
            text,
        )
        self.assertNotIn("Archive remains read-only", text)
        lowered = text.lower()
        self.assertNotIn("listed in a marketplace", lowered)
        self.assertNotIn("available in the marketplace", lowered)


class PublicClaimTests(unittest.TestCase):
    def test_public_docs_omit_unsupported_quality_and_marketplace_claims(self) -> None:
        for document in PUBLIC_DOC_PATHS:
            _assert_exists(self, document)
            lowered = _read(document).lower()
            for claim in FORBIDDEN_CLAIMS:
                self.assertNotIn(claim, lowered)

    def test_public_docs_omit_personal_paths(self) -> None:
        for document in PUBLIC_DOC_PATHS + (ARCHIVE_MIGRATION,):
            _assert_exists(self, document)
            text = _read(document)
            for marker in PERSONAL_MARKERS:
                self.assertNotIn(marker, text)


def _relative_link_errors(document: Path, text: str) -> list[str]:
    errors: list[str] = []
    base = document.parent
    relative = document.relative_to(ROOT).as_posix()
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
            resolved.relative_to(ROOT.resolve())
        except ValueError:
            errors.append(f"link escapes repository in {relative}: {target}")
            continue
        if resolved.name in FUTURE_COMMUNITY_FILES and resolved.parent == ROOT.resolve():
            continue
        if not resolved.exists():
            errors.append(f"broken relative link in {relative}: {target}")
    return errors


if __name__ == "__main__":
    unittest.main()
