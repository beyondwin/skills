from __future__ import annotations

import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_contract import PRODUCT_NAMES, validate_product  # noqa: E402

VERSION_LITERAL_RE = re.compile(r"\b[0-9]+\.[0-9]+\.[0-9]+\b")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)

PRODUCT_TITLES = {
    "korean-writing-editor": "Korean Writing Editor",
    "image-workbench": "Image Workbench",
    "graspic": "graspic",
}
KOREAN_PRODUCT_HEADINGS = (
    "이 스킬이 해결하는 문제",
    "사용해야 할 때와 사용하지 말아야 할 때",
    "1분 설치와 첫 호출",
    "주요 흐름",
    "안전과 개인정보",
    "호환성과 검증 수준",
    "갱신과 버전 확인",
    "변경 이력과 관리자 문서",
)
INSTALLER_COMMANDS = {
    "korean-writing-editor": (
        "$skill-installer https://github.com/beyondwin/skills/tree/main/skills/korean-writing-editor"
    ),
    "image-workbench": (
        "$skill-installer https://github.com/beyondwin/skills/tree/main/skills/image-workbench"
    ),
    "graspic": (
        "$skill-installer https://github.com/beyondwin/skills/tree/main/skills/graspic"
    ),
}
KOREAN_SUPPORT = (
    "korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke."
)
IMAGE_SUPPORT = (
    "image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing."
)
GRASPIC_SUPPORT = (
    "graspic: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke."
)
SUPPORT_BY_PRODUCT = {
    "korean-writing-editor": KOREAN_SUPPORT,
    "image-workbench": IMAGE_SUPPORT,
    "graspic": GRASPIC_SUPPORT,
}
OFFLINE_EVIDENCE = "Offline fixtures: deterministic contract evidence only."
LIVE_EVIDENCE = (
    "Live execution: local, explicit, optional, potentially billable, and never required by CI."
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
PRODUCT_README_PATHS = tuple(
    ROOT / "skills" / name / filename
    for name in PRODUCT_NAMES
    for filename in ("README.md", "README.en.md")
)
USER_GUIDES = (
    ROOT / "docs" / "users" / "ko" / "installation.md",
    ROOT / "docs" / "users" / "ko" / "compatibility.md",
    ROOT / "docs" / "users" / "ko" / "safety-and-privacy.md",
    ROOT / "docs" / "users" / "ko" / "verification.md",
    ROOT / "docs" / "users" / "en" / "installation.md",
    ROOT / "docs" / "users" / "en" / "compatibility.md",
    ROOT / "docs" / "users" / "en" / "safety-and-privacy.md",
    ROOT / "docs" / "users" / "en" / "verification.md",
)
OLD_PATHS = (
    ROOT / "docs" / "ko" / "getting-started.md",
    ROOT / "docs" / "ko" / "compatibility.md",
    ROOT / "docs" / "ko" / "privacy-and-rights.md",
    ROOT / "docs" / "ko" / "evaluation.md",
    ROOT / "docs" / "en" / "getting-started.md",
    ROOT / "docs" / "en" / "compatibility.md",
    ROOT / "docs" / "en" / "privacy-and-rights.md",
    ROOT / "docs" / "en" / "evaluation.md",
)
OLD_PATH_TARGETS = {
    ROOT / "docs" / "ko" / "getting-started.md": "../users/ko/installation.md",
    ROOT / "docs" / "ko" / "compatibility.md": "../users/ko/compatibility.md",
    ROOT / "docs" / "ko" / "privacy-and-rights.md": "../users/ko/safety-and-privacy.md",
    ROOT / "docs" / "ko" / "evaluation.md": "../users/ko/verification.md",
    ROOT / "docs" / "en" / "getting-started.md": "../users/en/installation.md",
    ROOT / "docs" / "en" / "compatibility.md": "../users/en/compatibility.md",
    ROOT / "docs" / "en" / "privacy-and-rights.md": "../users/en/safety-and-privacy.md",
    ROOT / "docs" / "en" / "evaluation.md": "../users/en/verification.md",
}
KOREAN_RELOCATION = (
    "이 문서는 독립 제품 문서 구조로 이동했습니다. 한 카탈로그 minor 동안 이 안내를 유지합니다."
)
ENGLISH_RELOCATION = (
    "This guide moved to the independent product documentation structure. This pointer remains for one catalog minor."
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
ACTIVE_USER_DOCS = README_PATHS + PRODUCT_README_PATHS + USER_GUIDES
PUBLIC_DOC_PATHS = ACTIVE_USER_DOCS + OLD_PATHS + MAINTAINER_DOCS + CATALOG_DOCS
FUTURE_COMMUNITY_FILES = frozenset(
    {
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
    }
)
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
STALE_TWO_SKILL = (
    "exactly two skills",
    "two curated skills",
    "two skills only",
)
PERSONAL_MARKERS = ("/Users/", "source/private", "SKILLS_ARCHIVE_CHECKOUT")
README_ORDER_EN = (
    "beyondwin-skills",
    "actions/workflows/verify.yml",
    "korean-writing-editor",
    "$skill-installer",
    "python3 scripts/verify.py",
    "CONTRIBUTING.md",
)
README_ORDER_KO = (
    "beyondwin-skills",
    "actions/workflows/verify.yml",
    "korean-writing-editor",
    "$skill-installer",
    "python3 scripts/verify.py",
    "CONTRIBUTING.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_exists(test: unittest.TestCase, path: Path) -> None:
    test.assertTrue(path.is_file(), f"{path.relative_to(ROOT).as_posix()} is absent")


def _heading_ids(text: str) -> set[str]:
    seen: dict[str, int] = {}
    ids: set[str] = set()
    for match in HEADING_RE.finditer(text):
        heading = match.group(2).replace("`", "")
        slug = heading.strip().lower()
        slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
        slug = re.sub(r"\s+", "-", slug)
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        ids.add(slug if count == 0 else f"{slug}-{count}")
    return ids


def _relative_link_errors(document: Path, text: str) -> list[str]:
    errors: list[str] = []
    base = document.parent
    relative = document.relative_to(ROOT).as_posix()
    heading_ids = _heading_ids(text)
    for href in MARKDOWN_LINK_RE.findall(text):
        target = href.strip()
        if not target:
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
            continue
        path_part, _, anchor = target.partition("#")
        if not path_part:
            if anchor and anchor not in heading_ids:
                errors.append(f"missing anchor in {relative}: #{anchor}")
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
            continue
        if anchor:
            if resolved.is_file():
                target_ids = _heading_ids(_read(resolved))
            else:
                target_ids = set()
            if anchor not in target_ids:
                errors.append(f"missing anchor in {relative}: {target}")
    return errors


class ProductReadmeOwnershipTests(unittest.TestCase):
    def test_every_product_owns_a_korean_english_readme_pair(self) -> None:
        for name in PRODUCT_NAMES:
            korean = ROOT / "skills" / name / "README.md"
            english = ROOT / "skills" / name / "README.en.md"
            self.assertTrue(korean.is_file(), f"{name} missing README.md")
            self.assertTrue(english.is_file(), f"{name} missing README.en.md")
            self.assertRegex(_read(korean), r"[가-힣]")
            english_text = _read(english)
            self.assertIn("[한국어](README.md)", english_text)
            self.assertNotRegex(
                english_text.replace("[한국어](README.md)", ""),
                r"[가-힣]",
            )

    def test_validate_product_rejects_missing_half_of_readme_pair(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "korean-writing-editor"
            shutil.copytree(ROOT / "skills" / "korean-writing-editor", root)
            readme = root / "README.md"
            english = root / "README.en.md"
            if readme.is_file():
                readme.unlink()
            errors = "\n".join(validate_product(root))
            self.assertIn("missing README.md", errors)
            readme.write_text("# Korean Writing Editor\n", encoding="utf-8")
            if not english.is_file():
                english.write_text("# Korean Writing Editor\n", encoding="utf-8")
            english.unlink()
            errors = "\n".join(validate_product(root))
            self.assertIn("missing README.en.md", errors)

    def test_root_and_product_readmes_do_not_own_product_versions(self) -> None:
        for path in README_PATHS + PRODUCT_README_PATHS:
            _assert_exists(self, path)
            text = _read(path)
            self.assertNotRegex(text, VERSION_LITERAL_RE)

    def test_root_readmes_do_not_own_product_versions(self) -> None:
        for path in (ROOT / "README.md", ROOT / "README.en.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"\b[0-9]+\.[0-9]+\.[0-9]+\b")

    def test_every_product_is_reachable_in_one_link_from_root(self) -> None:
        korean = (ROOT / "README.md").read_text(encoding="utf-8")
        english = (ROOT / "README.en.md").read_text(encoding="utf-8")
        for name in PRODUCT_NAMES:
            self.assertIn(f"skills/{name}/README.md", korean)
            self.assertIn(f"skills/{name}/README.en.md", english)

    def test_korean_product_readmes_use_required_heading_order(self) -> None:
        for name, title in PRODUCT_TITLES.items():
            path = ROOT / "skills" / name / "README.md"
            _assert_exists(self, path)
            text = _read(path)
            self.assertTrue(text.startswith(f"# {title}\n"), f"{name} title")
            last = -1
            for heading in KOREAN_PRODUCT_HEADINGS:
                marker = f"## {heading}"
                pos = text.find(marker)
                self.assertGreaterEqual(pos, 0, f"{name} missing {marker!r}")
                self.assertGreater(pos, last, f"{name} out of order: {marker!r}")
                last = pos

    def test_product_readmes_include_installer_support_and_maintainer_link(self) -> None:
        for name in PRODUCT_NAMES:
            for filename in ("README.md", "README.en.md"):
                path = ROOT / "skills" / name / filename
                _assert_exists(self, path)
                text = _read(path)
                self.assertIn(INSTALLER_COMMANDS[name], text)
                self.assertIn(SUPPORT_BY_PRODUCT[name], text)
                self.assertIn("CHANGELOG.md", text)
                self.assertIn(f"docs/maintainers/{name}.md", text)
                self.assertTrue(
                    "inspect" in text.lower() or "확인" in text,
                    f"{path.relative_to(ROOT).as_posix()} must describe the update check",
                )


class RootCatalogTests(unittest.TestCase):
    def test_readmes_follow_catalog_section_order(self) -> None:
        cases = (
            (ROOT / "README.md", README_ORDER_KO),
            (ROOT / "README.en.md", README_ORDER_EN),
        )
        for document, markers in cases:
            _assert_exists(self, document)
            text = _read(document)
            last = -1
            for marker in markers:
                pos = text.find(marker)
                self.assertGreaterEqual(pos, 0, f"{document.name} missing {marker!r}")
                self.assertGreater(pos, last, f"{document.name} out of order: {marker!r}")
                last = pos

    def test_korean_readme_is_korean_and_english_readme_is_complete(self) -> None:
        _assert_exists(self, ROOT / "README.md")
        _assert_exists(self, ROOT / "README.en.md")
        korean = _read(ROOT / "README.md")
        english = _read(ROOT / "README.en.md")
        self.assertRegex(korean, r"[가-힣]")
        self.assertIn("[English](README.en.md)", korean)
        self.assertIn("[한국어](README.md)", english)
        self.assertNotRegex(english.replace("[한국어](README.md)", ""), r"[가-힣]")
        self.assertIn("Apache-2.0", korean)
        self.assertIn("Apache-2.0", english)
        self.assertIn("python3 scripts/verify.py", korean)
        self.assertIn("python3 scripts/verify.py", english)

    def test_root_readmes_link_to_shared_guides_and_community_files(self) -> None:
        korean = _read(ROOT / "README.md")
        english = _read(ROOT / "README.en.md")
        for href in (
            "docs/users/ko/installation.md",
            "docs/users/ko/compatibility.md",
            "docs/users/ko/safety-and-privacy.md",
            "docs/users/ko/verification.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "LICENSE",
        ):
            self.assertIn(f"]({href})", korean)
        for href in (
            "docs/users/en/installation.md",
            "docs/users/en/compatibility.md",
            "docs/users/en/safety-and-privacy.md",
            "docs/users/en/verification.md",
            "CONTRIBUTING.md",
            "SECURITY.md",
            "CODE_OF_CONDUCT.md",
            "LICENSE",
        ):
            self.assertIn(f"]({href})", english)


class UserGuideFactTests(unittest.TestCase):
    def test_paired_user_guides_exist(self) -> None:
        for document in USER_GUIDES:
            _assert_exists(self, document)

    def test_shared_user_docs_link_back_to_all_product_readmes(self) -> None:
        for document in USER_GUIDES:
            _assert_exists(self, document)
            text = _read(document)
            language = "en" if "docs/users/en/" in document.as_posix() else "ko"
            filename = "README.en.md" if language == "en" else "README.md"
            for name in PRODUCT_NAMES:
                self.assertIn(f"skills/{name}/{filename}", text)

    def test_compatibility_owns_the_three_support_sentences(self) -> None:
        for document in (
            ROOT / "docs" / "users" / "ko" / "compatibility.md",
            ROOT / "docs" / "users" / "en" / "compatibility.md",
        ):
            _assert_exists(self, document)
            text = _read(document)
            self.assertIn(KOREAN_SUPPORT, text)
            self.assertIn(IMAGE_SUPPORT, text)
            self.assertIn(GRASPIC_SUPPORT, text)

    def test_installation_covers_install_update_and_inspection(self) -> None:
        for document in (
            ROOT / "docs" / "users" / "ko" / "installation.md",
            ROOT / "docs" / "users" / "en" / "installation.md",
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
            self.assertTrue(
                "third-party" in lowered or "제3자" in text,
                f"{document.name} must label the npx installer as third-party",
            )

    def test_safety_docs_own_telemetry_text_images_rights_and_high_stakes(self) -> None:
        for document in (
            ROOT / "docs" / "users" / "ko" / "safety-and-privacy.md",
            ROOT / "docs" / "users" / "en" / "safety-and-privacy.md",
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
                "no telemetry" in lowered
                or "텔레메트리 없음" in text
                or "does not include telemetry" in lowered
                or "텔레메트리를 넣지 않습니다" in text
                or "has no telemetry" in lowered,
                f"{document.name} must state the no-telemetry policy",
            )
            self.assertTrue("legal" in lowered or "법률" in text)
            self.assertTrue("medical" in lowered or "의료" in text)
            self.assertTrue("financial" in lowered or "금융" in text)

    def test_verification_owns_offline_live_evidence_and_profiles(self) -> None:
        for document in (
            ROOT / "docs" / "users" / "ko" / "verification.md",
            ROOT / "docs" / "users" / "en" / "verification.md",
        ):
            _assert_exists(self, document)
            text = _read(document)
            self.assertIn(OFFLINE_EVIDENCE, text)
            self.assertIn(LIVE_EVIDENCE, text)
            self.assertIn("python3 scripts/verify.py", text)
            self.assertIn("--profile full", text)
            self.assertIn("--profile windows-portable", text)
            self.assertTrue(
                "does not prove" in text.lower() or "증명하지 않습니다" in text,
                f"{document.name} must not treat offline fixtures as live quality evidence",
            )


class RelocationStubTests(unittest.TestCase):
    def test_old_paths_are_one_minor_relocation_stubs(self) -> None:
        for path, target in OLD_PATH_TARGETS.items():
            _assert_exists(self, path)
            text = _read(path)
            self.assertIn(target, text)
            if path.parts[-2] == "ko":
                self.assertIn(KOREAN_RELOCATION, text)
                self.assertNotIn(ENGLISH_RELOCATION, text)
            else:
                self.assertIn(ENGLISH_RELOCATION, text)
                self.assertNotIn(KOREAN_RELOCATION, text)
            self.assertNotIn("$skill-installer https://github.com/beyondwin/skills", text)
            self.assertNotIn(KOREAN_SUPPORT, text)
            self.assertNotIn(IMAGE_SUPPORT, text)
            self.assertNotIn(GRASPIC_SUPPORT, text)


class ReachabilityTests(unittest.TestCase):
    def test_public_relative_links_and_anchors_resolve(self) -> None:
        errors: list[str] = []
        for document in PUBLIC_DOC_PATHS:
            _assert_exists(self, document)
            errors.extend(_relative_link_errors(document, _read(document)))
        self.assertEqual(errors, [])

    def test_no_user_document_is_orphaned_from_the_root_catalog(self) -> None:
        targets = {path.resolve() for path in ACTIVE_USER_DOCS}
        reachable: set[Path] = set()
        stack = [ROOT / "README.md", ROOT / "README.en.md"]
        while stack:
            document = stack.pop()
            resolved = document.resolve()
            if resolved in reachable or not resolved.is_file():
                continue
            reachable.add(resolved)
            for href in MARKDOWN_LINK_RE.findall(_read(resolved)):
                target = href.strip()
                if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue
                path_part = target.split("#", 1)[0]
                if not path_part:
                    continue
                linked = (resolved.parent / path_part).resolve()
                if linked in targets and linked not in reachable:
                    stack.append(linked)
        missing = sorted(
            path.relative_to(ROOT).as_posix()
            for path in ACTIVE_USER_DOCS
            if path.resolve() not in reachable
        )
        self.assertEqual(missing, [])


class InstallSafetyTests(unittest.TestCase):
    def test_root_readmes_document_primary_installs(self) -> None:
        for document in README_PATHS:
            _assert_exists(self, document)
            text = _read(document)
            self.assertIn("$skill-installer", text)
            for path in PRIMARY_INSTALL_PATHS:
                self.assertIn(path, text)

    def test_public_docs_omit_unsafe_install_and_update_commands(self) -> None:
        for document in PUBLIC_DOC_PATHS:
            _assert_exists(self, document)
            text = _read(document)
            for fragment in UNSAFE_INSTALL:
                self.assertNotIn(fragment, text)
            lowered = text.lower()
            self.assertNotIn("automatic replacement", lowered)
            self.assertNotIn("unchecked overwrite", lowered)


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

    def test_active_user_docs_omit_stale_two_skill_claims(self) -> None:
        for document in ACTIVE_USER_DOCS + OLD_PATHS:
            _assert_exists(self, document)
            lowered = _read(document).lower()
            for claim in STALE_TWO_SKILL:
                self.assertNotIn(claim, lowered)

    def test_public_docs_omit_personal_paths(self) -> None:
        for document in PUBLIC_DOC_PATHS + (ARCHIVE_MIGRATION,):
            _assert_exists(self, document)
            text = _read(document)
            for marker in PERSONAL_MARKERS:
                self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
