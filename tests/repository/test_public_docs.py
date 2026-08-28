from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.documentation import (  # noqa: E402
    active_markdown_paths,
    broken_markdown_links,
    markdown_links,
)
from scripts.lib.product_contract import validate_product  # noqa: E402
from scripts.lib.product_registry import load_registry  # noqa: E402

REGISTRY = load_registry(ROOT / "products.toml")

VERSION_LITERAL_RE = re.compile(r"\b[0-9]+\.[0-9]+\.[0-9]+\b")

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
    product.name: (
        "$skill-installer https://github.com/beyondwin/skills/tree/main/"
        f"{product.skill_path.as_posix()}"
    )
    for product in REGISTRY.products
}
KOREAN_SUPPORT = (
    "korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke."
)
IMAGE_SUPPORT = (
    "image-workbench: Codex-only; generate/edit requires Codex image generation and local image viewing."
)
HOW_IT_WORKS_SUPPORT = (
    "how-it-works: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke."
)
SUPPORT_BY_PRODUCT = {
    "korean-writing-editor": KOREAN_SUPPORT,
    "image-workbench": IMAGE_SUPPORT,
    "how-it-works": HOW_IT_WORKS_SUPPORT,
}
OFFLINE_EVIDENCE = "Offline fixtures: deterministic contract evidence only."
LIVE_EVIDENCE = (
    "Live execution: local, explicit, optional, potentially billable, and never required by CI."
)
PRIMARY_INSTALL_PATHS = tuple(
    "https://github.com/beyondwin/skills/tree/main/"
    f"{product.skill_path.as_posix()}"
    for product in REGISTRY.products
)
OPTIONAL_NPX = "npx skills add beyondwin/skills --skill korean-writing-editor"
GIT_CLONE = "git clone https://github.com/beyondwin/skills"
LIVE_BUDGETS = ("119", "3", "122", "38", "160")
README_PATHS = (ROOT / "README.md", ROOT / "README.en.md")
PRODUCT_README_PATHS = tuple(
    ROOT / product.skill_path / filename
    for product in REGISTRY.products
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
DOCS_INDEX = ROOT / "docs" / "README.md"
HISTORY_README = ROOT / "docs" / "history" / "README.md"
MAINTAINER_INDEX = ROOT / "docs" / "maintainers" / "README.md"
REPOSITORY_DOCS = (
    ROOT / "docs" / "maintainers" / "repository" / "architecture.md",
    ROOT / "docs" / "maintainers" / "repository" / "versioning.md",
    ROOT / "docs" / "maintainers" / "repository" / "products-registry.md",
    ROOT / "docs" / "maintainers" / "repository" / "release.md",
    ROOT / "docs" / "maintainers" / "repository" / "catalog.md",
    ROOT / "docs" / "maintainers" / "repository" / "migrations.md",
)
ARCHIVE_MANIFEST = (
    ROOT / "docs" / "maintainers" / "repository" / "archive-source-manifest.json"
)
PRODUCT_PROTOCOL_FILES = ("contract.md", "testing.md", "compatibility.md", "release.md")
REGISTRY_SCHEMA_FIELDS = (
    "schema_version",
    "name",
    "display_name",
    "skill_path",
    "test_path",
    "maintainer_docs",
    "supported_hosts",
    "owned_paths",
    "verify_stages",
)
MAINTAINER_DOCS = (MAINTAINER_INDEX,) + REPOSITORY_DOCS + tuple(
    ROOT / product.maintainer_docs / filename
    for product in REGISTRY.products
    for filename in PRODUCT_PROTOCOL_FILES
)
CATALOG_DOCS = (
    ROOT / "catalog" / "README.md",
    ROOT / "catalog" / "CHANGELOG.md",
)
ACTIVE_USER_DOCS = README_PATHS + PRODUCT_README_PATHS + USER_GUIDES + (DOCS_INDEX,)
PUBLIC_DOC_PATHS = ACTIVE_USER_DOCS + MAINTAINER_DOCS + CATALOG_DOCS + (HISTORY_README,)
OBSOLETE_MAINTAINER_RELATIVE = (
    "docs/maintainers/architecture.md",
    "docs/maintainers/release-process.md",
    *("docs/maintainers/" + name + ".md" for name in REGISTRY.names),
    "docs/maintainers/archive-migration.md",
    "docs/maintainers/archive-source-manifest.json",
)
HISTORY_PREFIXES = (
    "docs/history/",
    "catalog/CHANGELOG.md",
)
ACTIVE_ROUTING_SURFACES = (
    README_PATHS
    + PRODUCT_README_PATHS
    + USER_GUIDES
    + MAINTAINER_DOCS
    + (
        DOCS_INDEX,
        ROOT / "catalog" / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        ROOT / "CODE_OF_CONDUCT.md",
        ROOT / "NOTICE",
        ROOT / ".github" / "ISSUE_TEMPLATE" / "bug.yml",
        ROOT / ".github" / "ISSUE_TEMPLATE" / "documentation.yml",
        ROOT / ".github" / "pull_request_template.md",
    )
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
    REGISTRY.names[0],
    "$skill-installer",
    "python3 scripts/verify.py",
    "CONTRIBUTING.md",
)
README_ORDER_KO = (
    "beyondwin-skills",
    "actions/workflows/verify.yml",
    REGISTRY.names[0],
    "$skill-installer",
    "python3 scripts/verify.py",
    "CONTRIBUTING.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_exists(test: unittest.TestCase, path: Path) -> None:
    test.assertTrue(path.is_file(), f"{path.relative_to(ROOT).as_posix()} is absent")


class ProductReadmeOwnershipTests(unittest.TestCase):
    def test_every_product_owns_a_korean_english_readme_pair(self) -> None:
        for product in REGISTRY.products:
            korean = ROOT / product.skill_path / "README.md"
            english = ROOT / product.skill_path / "README.en.md"
            self.assertTrue(korean.is_file(), f"{product.name} missing README.md")
            self.assertTrue(english.is_file(), f"{product.name} missing README.en.md")
            self.assertRegex(_read(korean), r"[가-힣]", product.name)
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
            errors = "\n".join(validate_product(root, REGISTRY))
            self.assertIn("missing README.md", errors)
            readme.write_text("# Korean Writing Editor\n", encoding="utf-8")
            if not english.is_file():
                english.write_text("# Korean Writing Editor\n", encoding="utf-8")
            english.unlink()
            errors = "\n".join(validate_product(root, REGISTRY))
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
        for product in REGISTRY.products:
            self.assertIn(f"{product.skill_path.as_posix()}/README.md", korean)
            self.assertIn(f"{product.skill_path.as_posix()}/README.en.md", english)

    def test_korean_product_readmes_use_required_heading_order(self) -> None:
        for product in REGISTRY.products:
            path = ROOT / product.skill_path / "README.md"
            _assert_exists(self, path)
            text = _read(path)
            self.assertTrue(
                text.startswith(f"# {product.display_name}\n"),
                f"{product.name} title",
            )
            last = -1
            for heading in KOREAN_PRODUCT_HEADINGS:
                marker = f"## {heading}"
                pos = text.find(marker)
                self.assertGreaterEqual(pos, 0, f"{product.name} missing {marker!r}")
                self.assertGreater(pos, last, f"{product.name} out of order: {marker!r}")
                last = pos

    def test_product_readmes_include_installer_support_and_maintainer_link(self) -> None:
        for product in REGISTRY.products:
            for filename in ("README.md", "README.en.md"):
                path = ROOT / product.skill_path / filename
                _assert_exists(self, path)
                text = _read(path)
                self.assertIn(INSTALLER_COMMANDS[product.name], text)
                self.assertIn(SUPPORT_BY_PRODUCT[product.name], text)
                self.assertIn("CHANGELOG.md", text)
                maintainer = product.maintainer_docs.as_posix()
                self.assertIn(f"{maintainer}/contract.md", text)
                self.assertIn(f"{maintainer}/testing.md", text)
                self.assertIn(f"{maintainer}/compatibility.md", text)
                self.assertIn(f"{maintainer}/release.md", text)
                self.assertNotIn(f"docs/maintainers/{product.name}.md", text)
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
            "docs/README.md",
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
            "docs/README.md",
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
            for product in REGISTRY.products:
                self.assertIn(f"{product.skill_path.as_posix()}/{filename}", text)

    def test_compatibility_owns_the_three_support_sentences(self) -> None:
        for document in (
            ROOT / "docs" / "users" / "ko" / "compatibility.md",
            ROOT / "docs" / "users" / "en" / "compatibility.md",
        ):
            _assert_exists(self, document)
            text = _read(document)
            for product in REGISTRY.products:
                self.assertIn(SUPPORT_BY_PRODUCT[product.name], text)

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

    def test_safety_docs_name_how_it_works_in_high_stakes_slices(self) -> None:
        korean = _read(ROOT / "docs" / "users" / "ko" / "safety-and-privacy.md")
        english = _read(ROOT / "docs" / "users" / "en" / "safety-and-privacy.md")
        self.assertIn("`how-it-works`의 해당 슬라이스", korean)
        self.assertIn("`how-it-works` slices", english)
        self.assertNotIn("Gra" + "spic slices", english)

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


class DocumentationArchitectureTests(unittest.TestCase):
    def test_only_four_user_guides_exist_per_language(self) -> None:
        expected = {"installation.md", "compatibility.md", "safety-and-privacy.md", "verification.md"}
        for language in ("ko", "en"):
            self.assertEqual({p.name for p in (ROOT / "docs/users" / language).glob("*.md")}, expected)
            self.assertFalse((ROOT / "docs" / language).exists())

    def test_history_is_visibly_non_authoritative(self) -> None:
        text = (ROOT / "docs/history/README.md").read_text(encoding="utf-8")
        self.assertIn("현재 계약을 정의하지", text)
        self.assertFalse((ROOT / "docs" / "superpowers").exists())
        self.assertRegex(text, r"[A-Za-z]")
        lowered = text.lower()
        self.assertTrue("point-in-time" in lowered or "point in time" in lowered)
        self.assertTrue("old" in lowered and ("name" in lowered or "path" in lowered))

    def test_docs_index_routes_install_use_maintain_and_history(self) -> None:
        _assert_exists(self, DOCS_INDEX)
        text = _read(DOCS_INDEX)
        self.assertRegex(text, r"[가-힣]")
        self.assertIn("docs/users/", text)
        for product in REGISTRY.products:
            self.assertIn(f"{product.skill_path.as_posix()}/README.md", text)
            self.assertIn(f"{product.skill_path.as_posix()}/README.en.md", text)
        self.assertIn("docs/maintainers/", text)
        self.assertIn("docs/history/", text)

    def test_repository_guides_cover_registry_release_catalog_and_migrations(self) -> None:
        registry_doc = ROOT / "docs" / "maintainers" / "repository" / "products-registry.md"
        release_doc = ROOT / "docs" / "maintainers" / "repository" / "release.md"
        catalog_doc = ROOT / "docs" / "maintainers" / "repository" / "catalog.md"
        migrations_doc = ROOT / "docs" / "maintainers" / "repository" / "migrations.md"
        for path in (registry_doc, release_doc, catalog_doc, migrations_doc):
            _assert_exists(self, path)
            self.assertRegex(_read(path), r"[가-힣]")
        self.assertFalse(
            (ROOT / "docs" / "maintainers" / "repository" / "catalog-release.md").exists()
        )
        self.assertFalse(
            (ROOT / "docs" / "maintainers" / "repository" / "archive-migration.md").exists()
        )
        registry_text = _read(registry_doc)
        for field in REGISTRY_SCHEMA_FIELDS:
            self.assertIn(field, registry_text, field)
        self.assertIn("python3 scripts/verify.py", registry_text)
        release_text = _read(release_doc)
        self.assertIn("python3 scripts/release.py check --product", release_text)
        self.assertIn("python3 scripts/release.py build --product", release_text)
        self.assertIn("python3 scripts/release.py verify-download --product", release_text)
        self.assertNotRegex(release_text, VERSION_LITERAL_RE)
        catalog_text = _read(catalog_doc)
        self.assertIn("Registry products do not automatically enter v2.0.0", catalog_text)
        migrations_text = _read(migrations_doc)
        self.assertIn("76e6bf4ebbc9430aee9a04a5b780ae38330f3021", migrations_text)
        self.assertIn(
            "docs/maintainers/repository/archive-source-manifest.json",
            migrations_text,
        )

    def test_maintainer_index_links_task_routes(self) -> None:
        _assert_exists(self, MAINTAINER_INDEX)
        index = _read(MAINTAINER_INDEX)
        self.assertRegex(index, r"[가-힣]")
        for href in (
            "products/",
            "repository/products-registry.md",
            "repository/release.md",
            "repository/catalog.md",
            "repository/migrations.md",
            "../history/",
        ):
            self.assertIn(href, index)


def _linked_path(document: Path, href: str) -> Path | None:
    target = href.strip()
    if not target or re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
        return None
    path_part = target.split("#", 1)[0].split("?", 1)[0]
    if not path_part:
        return None
    return (document.parent / path_part).resolve()


class RegistryDrivenPublicDocTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = load_registry(ROOT / "products.toml")

    def test_root_readmes_cover_registered_products(self) -> None:
        for relative in ("README.md", "README.en.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for product in self.registry.products:
                self.assertIn(product.name, text, relative)
                self.assertIn(product.skill_path.as_posix(), text, relative)

    def test_product_readmes_match_registry_hosts(self) -> None:
        for product in self.registry.products:
            for filename in ("README.md", "README.en.md"):
                text = (ROOT / product.skill_path / filename).read_text(encoding="utf-8")
                for host in product.supported_hosts:
                    self.assertIn(host, text.lower(), f"{product.name}/{filename}")

    def test_all_active_markdown_links_resolve(self) -> None:
        self.assertEqual(broken_markdown_links(ROOT, active_markdown_paths(ROOT)), [])

    def test_active_markdown_paths_match_public_doc_inventory(self) -> None:
        self.assertEqual(
            {path.resolve() for path in active_markdown_paths(ROOT)},
            {path.resolve() for path in PUBLIC_DOC_PATHS},
        )


class MarkdownLinkHelperTests(unittest.TestCase):
    def test_markdown_links_extract_relative_angle_bracket_and_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "doc.md"
            path.write_text(
                "[a](../x.md) [b](<y z.md>) [c](https://example.com) "
                "[d](#local) [e](found.md?raw=1#title)\n",
                encoding="utf-8",
            )
            self.assertEqual(
                markdown_links(path),
                (
                    "../x.md",
                    "y z.md",
                    "https://example.com",
                    "#local",
                    "found.md?raw=1#title",
                ),
            )

    def test_broken_markdown_links_ignore_http_https_mailto_and_in_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "found.md").write_text("# Found\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text(
                "[web](https://example.com/a) [plain](http://example.com) "
                "[mail](mailto:a@b.com) [here](#missing) [ok](found.md)\n",
                encoding="utf-8",
            )
            self.assertEqual(broken_markdown_links(root, [doc]), [])

    def test_broken_markdown_links_report_missing_files_in_sorted_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            doc = root / "doc.md"
            doc.write_text("[z](z.md) [a](a.md)\n", encoding="utf-8")
            self.assertEqual(
                broken_markdown_links(root, [doc]),
                [
                    "broken relative link in doc.md: a.md",
                    "broken relative link in doc.md: z.md",
                ],
            )

    def test_broken_markdown_links_strip_query_and_fragment_and_resolve_angles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "found.md").write_text("# Title\n", encoding="utf-8")
            (root / "my file.md").write_text("# Hi\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text(
                "[ok](found.md?raw=1#title) [space](<my file.md>)\n",
                encoding="utf-8",
            )
            self.assertEqual(broken_markdown_links(root, [doc]), [])

    def test_broken_markdown_links_report_missing_fragments_on_relative_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "found.md").write_text("# Title\n", encoding="utf-8")
            doc = root / "doc.md"
            doc.write_text("[bad](found.md#missing)\n", encoding="utf-8")
            self.assertEqual(
                broken_markdown_links(root, [doc]),
                ["missing anchor in doc.md: found.md#missing"],
            )


class ReachabilityTests(unittest.TestCase):
    def test_public_relative_links_and_anchors_resolve(self) -> None:
        self.assertEqual(broken_markdown_links(ROOT, PUBLIC_DOC_PATHS), [])

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
            for href in markdown_links(resolved):
                linked = _linked_path(resolved, href)
                if linked is not None and linked in targets and linked not in reachable:
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


class MaintainerStructureTests(unittest.TestCase):
    def test_every_product_has_contract_testing_and_release(self) -> None:
        for product in REGISTRY.products:
            directory = ROOT / product.maintainer_docs
            self.assertTrue(directory.is_dir(), f"{product.name} maintainer directory is absent")
            for filename in PRODUCT_PROTOCOL_FILES:
                path = directory / filename
                _assert_exists(self, path)
                self.assertRegex(_read(path), r"[가-힣]")

    def test_repository_trio_and_archive_evidence_live_under_repository(self) -> None:
        for path in REPOSITORY_DOCS:
            _assert_exists(self, path)
            self.assertRegex(_read(path), r"[가-힣]")
        _assert_exists(self, ARCHIVE_MANIFEST)
        self.assertEqual(
            json.loads(_read(ARCHIVE_MANIFEST))["manifest_sha256"],
            "6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78",
        )

    def test_maintainer_index_reaches_every_maintainer_document(self) -> None:
        _assert_exists(self, MAINTAINER_INDEX)
        index = _read(MAINTAINER_INDEX)
        self.assertRegex(index, r"[가-힣]")
        for href in (
            "repository/architecture.md",
            "repository/versioning.md",
            "repository/products-registry.md",
            "repository/release.md",
            "repository/catalog.md",
            "repository/migrations.md",
        ):
            self.assertIn(href, index)
        for product in REGISTRY.products:
            for filename in PRODUCT_PROTOCOL_FILES:
                self.assertIn(f"{product.name}/{filename}", index)
        targets = {path.resolve() for path in MAINTAINER_DOCS}
        reachable: set[Path] = set()
        stack = [MAINTAINER_INDEX]
        while stack:
            document = stack.pop()
            resolved = document.resolve()
            if resolved in reachable or not resolved.is_file():
                continue
            reachable.add(resolved)
            for href in markdown_links(resolved):
                linked = _linked_path(resolved, href)
                if linked is not None and linked in targets and linked not in reachable:
                    stack.append(linked)
        missing = sorted(
            path.relative_to(ROOT).as_posix()
            for path in MAINTAINER_DOCS
            if path.resolve() not in reachable
        )
        self.assertEqual(missing, [])

    def test_obsolete_flat_maintainer_paths_are_absent(self) -> None:
        for relative in OBSOLETE_MAINTAINER_RELATIVE:
            path = ROOT / relative
            self.assertFalse(path.exists(), f"{relative} must not remain after migration")


class MaintainerProtocolTests(unittest.TestCase):
    def test_architecture_owns_payload_and_test_separation(self) -> None:
        path = ROOT / "docs" / "maintainers" / "repository" / "architecture.md"
        _assert_exists(self, path)
        text = _read(path)
        self.assertRegex(text, r"[가-힣]")
        self.assertIn("skills/", text)
        self.assertIn("tests/", text)
        self.assertIn("beyondwin-skills", text)
        self.assertIn("python3 scripts/verify.py", text)
        self.assertIn("2.0.0", text)
        self.assertIn("catalog/plugin/.codex-plugin/plugin.json", text)
        self.assertIn("catalog/catalog.lock.json", text)
        self.assertIn("does not own plugin metadata", text)
        self.assertIn("README.md", text)
        self.assertIn("CHANGELOG.md", text)
        self.assertIn("release.toml", text)
        self.assertIn("docs/README.md", text)
        self.assertIn("docs/history/", text)
        self.assertIn("catalog.md", text)
        self.assertIn("migrations.md", text)

    def test_versioning_owns_the_semver_table(self) -> None:
        path = ROOT / "docs" / "maintainers" / "repository" / "versioning.md"
        _assert_exists(self, path)
        text = _read(path)
        self.assertRegex(text, r"[가-힣]")
        self.assertIn("PATCH", text)
        self.assertIn("MINOR", text)
        self.assertIn("MAJOR", text)
        self.assertIn("release.toml", text)
        self.assertIn("기본 모드", text)
        self.assertIn("카탈로그", text)
        self.assertIn("catalog.md", text)

    def test_catalog_release_owns_lock_adoption_and_remote_byte_gates(self) -> None:
        path = ROOT / "docs" / "maintainers" / "repository" / "catalog.md"
        _assert_exists(self, path)
        text = _read(path)
        self.assertRegex(text, r"[가-힣]")
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
        self.assertIn("verify-download", text)

    def test_korean_protocol_preserves_fixture_sync_and_live_budgets(self) -> None:
        contract = ROOT / "docs" / "maintainers" / "products" / "korean-writing-editor" / "contract.md"
        testing = ROOT / "docs" / "maintainers" / "products" / "korean-writing-editor" / "testing.md"
        release = ROOT / "docs" / "maintainers" / "products" / "korean-writing-editor" / "release.md"
        for path in (contract, testing, release):
            _assert_exists(self, path)
        contract_text = _read(contract)
        testing_text = _read(testing)
        release_text = _read(release)
        for token in ("trigger", "mode", "output", "tier"):
            self.assertIn(token, contract_text.lower())
        for budget in LIVE_BUDGETS:
            self.assertIn(budget, testing_text)
        self.assertIn("119", testing_text)
        self.assertIn("producer", testing_text.lower())
        self.assertIn("reviewer", testing_text.lower())
        self.assertIn("release.toml", release_text)
        self.assertIn("python3 scripts/release.py check --product korean-writing-editor", release_text)

    def test_image_protocol_preserves_route_authorization_spec_and_inspector(self) -> None:
        contract = ROOT / "docs" / "maintainers" / "products" / "image-workbench" / "contract.md"
        testing = ROOT / "docs" / "maintainers" / "products" / "image-workbench" / "testing.md"
        release = ROOT / "docs" / "maintainers" / "products" / "image-workbench" / "release.md"
        for path in (contract, testing, release):
            _assert_exists(self, path)
        contract_text = _read(contract).lower()
        testing_text = _read(testing).lower()
        release_text = _read(release)
        self.assertIn("route", contract_text)
        self.assertIn("authorization", contract_text)
        self.assertIn("imagespec", contract_text)
        self.assertIn("rubric", contract_text)
        self.assertIn("inspector", testing_text)
        self.assertIn("inspect_asset.py", testing_text)
        self.assertIn("release.toml", release_text)
        self.assertIn("python3 scripts/release.py check --product image-workbench", release_text)

    def test_how_it_works_protocol_preserves_rung_fixtures_and_artifact_page(self) -> None:
        contract = ROOT / "docs" / "maintainers" / "products" / "how-it-works" / "contract.md"
        testing = ROOT / "docs" / "maintainers" / "products" / "how-it-works" / "testing.md"
        release = ROOT / "docs" / "maintainers" / "products" / "how-it-works" / "release.md"
        for path in (contract, testing, release):
            _assert_exists(self, path)
        contract_text = _read(contract)
        testing_text = _read(testing)
        release_text = _read(release)
        self.assertIn("artifact", contract_text.lower())
        self.assertIn("mermaid", contract_text.lower())
        self.assertNotIn("Do not add HTML artifacts", contract_text)
        self.assertNotIn("chat-only", contract_text.lower())
        for fixture_id in (
            "gate-dump-01",
            "html-01",
            "type-cmp-01",
            "scope-01",
            "ko-gloss-01",
        ):
            self.assertIn(fixture_id, testing_text)
        self.assertIn("/eli5", testing_text)
        self.assertIn("release.toml", release_text)
        self.assertIn("python3 scripts/release.py check --product how-it-works", release_text)

    def test_archive_migration_freeze_record_is_preserved(self) -> None:
        path = ROOT / "docs" / "maintainers" / "repository" / "migrations.md"
        _assert_exists(self, path)
        text = _read(path)
        self.assertIn("76e6bf4ebbc9430aee9a04a5b780ae38330f3021", text)
        self.assertIn(
            "6917f68e6e0d81226e50195d58a884373d23ffbbbe48363ef2428c8cbcb83f78",
            text,
        )
        self.assertIn(
            "docs/maintainers/repository/archive-source-manifest.json",
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
        for document in ACTIVE_USER_DOCS:
            _assert_exists(self, document)
            lowered = _read(document).lower()
            for claim in STALE_TWO_SKILL:
                self.assertNotIn(claim, lowered)

    def test_active_surfaces_omit_stale_two_skill_claims_and_obsolete_paths(self) -> None:
        for document in ACTIVE_ROUTING_SURFACES:
            _assert_exists(self, document)
            text = _read(document)
            lowered = text.lower()
            for claim in STALE_TWO_SKILL:
                self.assertNotIn(claim, lowered)
            for relative in OBSOLETE_MAINTAINER_RELATIVE:
                self.assertNotIn(relative, text)
            relative = document.relative_to(ROOT).as_posix()
            self.assertFalse(
                relative.startswith(HISTORY_PREFIXES),
                f"{relative} is history and should not be in the active routing scan",
            )

    def test_public_docs_omit_personal_paths(self) -> None:
        for document in PUBLIC_DOC_PATHS + (ARCHIVE_MANIFEST,):
            _assert_exists(self, document)
            text = _read(document)
            for marker in PERSONAL_MARKERS:
                self.assertNotIn(marker, text)


if __name__ == "__main__":
    unittest.main()
