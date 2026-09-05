from __future__ import annotations

import hashlib
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
from scripts.lib.verification import WINDOWS_EXCLUDED_STAGES  # noqa: E402

REGISTRY = load_registry(ROOT / "products.toml")

VERSION_LITERAL_RE = re.compile(r"\b[0-9]+\.[0-9]+\.[0-9]+\b")

PRE_SDD_PRODUCT_HEADINGS = {
    "README.md": (
        "## 이 스킬이 해결하는 문제",
        "## 사용해야 할 때와 사용하지 말아야 할 때",
        "## 설치",
        "## 첫 호출",
        "## 결과와 기본 흐름",
        "## 안전과 개인정보",
        "## 운영과 한계",
        "## 호환성과 검증 수준",
        "## 변경 이력과 관리자 문서",
    ),
    "README.en.md": (
        "## Purpose",
        "## When to use and not use",
        "## Install",
        "## First call",
        "## Expected result",
        "## Safety and privacy",
        "## Operations and limits",
        "## Supported hosts and verification",
        "## Changelog and maintainer docs",
    ),
}
PRODUCT_README_HEADINGS = {
    "README.md": (
        "## 목적",
        "## 사용할 때와 사용하지 않을 때",
        "## 지원 호스트",
        "## 설치",
        "## 첫 호출",
        "## 예상 결과",
        "## 안전과 개인정보",
        "## 검증",
        "## 업데이트와 제거",
        "## 변경 이력과 관리자 문서",
    ),
    "README.en.md": (
        "## Purpose",
        "## When to use and not use",
        "## Supported hosts",
        "## Install",
        "## First call",
        "## Expected result",
        "## Safety and privacy",
        "## Verification",
        "## Update and remove",
        "## Changelog and maintainer docs",
    ),
}
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
    "how-it-works: Codex and Claude Code supported for local or repository-based use."
)
PRE_SDD_REVIEW_SUPPORT = (
    "pre-sdd-review: Codex supported; other hosts not_measured."
)
PRE_SDD_SHARED_SECTION_DIGESTS = {
    ("ko", "safety"): "86b0b7c6020984699af0a8dec3ff4d79fcd6f605cf2f4c647d17d31d1ddbcd7e",
    ("en", "safety"): "72ee48897fe1255e3d1227e31553ad56e9aa81c4614c634a13876255756d28ec",
    ("ko", "verification"): "2d24cb850c897d8bf90dd883d3fc38f0366ef5a1bb71eadcb2870485dba67be9",
    ("en", "verification"): "a06cdb79bd2f5b77ac540ea03a65a42eba6266d9f7994147a0265626c5a81177",
}
SUPPORT_BY_PRODUCT = {
    "korean-writing-editor": KOREAN_SUPPORT,
    "image-workbench": IMAGE_SUPPORT,
    "how-it-works": HOW_IT_WORKS_SUPPORT,
    "pre-sdd-review": PRE_SDD_REVIEW_SUPPORT,
}
HOW_IT_WORKS_MKDIR = "mkdir -p ~/.agents/skills ~/.claude/skills"
HOW_IT_WORKS_AGENTS_LINK = (
    'ln -s "$PWD/skills/how-it-works" ~/.agents/skills/how-it-works'
)
HOW_IT_WORKS_CLAUDE_LINK = (
    'ln -s "$PWD/skills/how-it-works" ~/.claude/skills/how-it-works'
)
HOW_IT_WORKS_UNLINK_AGENTS = "unlink ~/.agents/skills/how-it-works"
HOW_IT_WORKS_UNLINK_CLAUDE = "unlink ~/.claude/skills/how-it-works"
HOW_IT_WORKS_EXPECTED_EN = (
    "one-sentence claim",
    "Mermaid",
    "numbered hop list",
    "rung-specific body",
    "adjacent slices",
    "one next move",
)
HOW_IT_WORKS_FIXTURE_IDS = (
    "broad-slice",
    "missing-rung",
    "explicit-dns-path",
    "implicit-positive",
    "near-miss-debug",
    "near-miss-eli5",
    "jargon-rung",
    "no-renderer",
    "no-fetched-source",
)
RELEASE_NO_PUBLICATION = (
    "no tag or GitHub Release is created by these commands."
)
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
DEAD_RECORDER_STRINGS = (
    "install.py",
    "--bin-dir",
    "record-outcome",
    "finish-review",
    "~/.local/bin/pre-sdd-review-evidence",
)
DEAD_LAUNCHER_PHRASES = (
    "pre-sdd-review-evidence launcher",
    "`pre-sdd-review-evidence` launcher",
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
STALE_THREE_PRODUCT = (
    "three current standalone products",
    "three curated products",
    "adds a fourth skill",
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


_WINDOWS_PORTABLE_STAGE_RE = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)*)`")


def _windows_portable_exclusion_sentence(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("`windows-portable`"):
            continue
        if "exclude" in stripped.lower() or "뺍니다" in stripped:
            return stripped
    raise AssertionError("missing windows-portable exclusion sentence")


def _windows_portable_excluded_stages(sentence: str) -> frozenset[str]:
    if "뺍니다" in sentence:
        exclude_part, _, keep_part = sentence.partition("뺍니다")
    else:
        parts = re.split(r"(?i)\bkeeps?\b", sentence, maxsplit=1)
        if "exclude" not in parts[0].lower():
            raise AssertionError("windows-portable sentence does not exclude stages")
        exclude_part = parts[0]
        keep_part = parts[1] if len(parts) > 1 else ""
    excluded = {
        name
        for name in _WINDOWS_PORTABLE_STAGE_RE.findall(exclude_part)
        if name != "windows-portable"
    }
    kept = {
        name
        for name in _WINDOWS_PORTABLE_STAGE_RE.findall(keep_part)
        if name != "windows-portable"
    }
    overlap = excluded & kept
    if overlap:
        raise AssertionError(
            "windows-portable lists stages as both excluded and kept: "
            + ", ".join(sorted(overlap))
        )
    return frozenset(excluded)


def _assert_exists(test: unittest.TestCase, path: Path) -> None:
    test.assertTrue(path.is_file(), f"{path.relative_to(ROOT).as_posix()} is absent")


def _owned_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^{re.escape(heading)}\s*$.*?(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = pattern.findall(text)
    return matches[0] if len(matches) == 1 else ""


def _append_to_owned_section(text: str, heading: str, contradiction: str) -> str:
    owned = _owned_section(text, heading)
    if not owned:
        return text
    replacement = owned.rstrip() + f"\n\n{contradiction}\n\n"
    return text.replace(owned, replacement, 1)


def _is_backtick_escaped(text: str, index: int) -> bool:
    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def _matching_inline_code_end(text: str, start: int, run_end: int) -> int | None:
    paragraph_break = re.search(r"\n[ \t]*\n", text[run_end:])
    paragraph_end = (
        run_end + paragraph_break.start() if paragraph_break is not None else len(text)
    )
    width = run_end - start
    cursor = run_end
    while cursor < paragraph_end:
        closing_start = text.find("`", cursor, paragraph_end)
        if closing_start == -1:
            return None
        closing_end = closing_start
        while closing_end < paragraph_end and text[closing_end] == "`":
            closing_end += 1
        if closing_end - closing_start == width:
            return closing_end
        cursor = closing_end
    return None


def _rendered_markdown_lines(text: str) -> tuple[str, ...]:
    structural = list(text)
    cursor = 0
    fence_marker: str | None = None
    fence_width = 0
    in_comment = False

    def mask(start: int, end: int) -> None:
        for index in range(start, end):
            if structural[index] not in "\r\n":
                structural[index] = " "

    while cursor < len(text):
        at_line_start = cursor == 0 or text[cursor - 1] == "\n"
        if fence_marker is not None:
            line_end = text.find("\n", cursor)
            line_end = len(text) if line_end == -1 else line_end + 1
            content = text[cursor:line_end].rstrip("\r\n")
            closing = re.match(r"^ {0,3}(`{3,}|~{3,})\s*$", content)
            if (
                closing is not None
                and closing.group(1)[0] == fence_marker
                and len(closing.group(1)) >= fence_width
            ):
                fence_marker = None
                fence_width = 0
            mask(cursor, line_end)
            cursor = line_end
            continue
        if in_comment:
            if text.startswith("-->", cursor):
                mask(cursor, cursor + 3)
                cursor += 3
                in_comment = False
                continue
            mask(cursor, cursor + 1)
            cursor += 1
            continue
        if at_line_start:
            line_end = text.find("\n", cursor)
            line_end = len(text) if line_end == -1 else line_end + 1
            content = text[cursor:line_end].rstrip("\r\n")
            opening = re.match(r"^ {0,3}(`{3,}|~{3,})", content)
            if opening is not None:
                fence_marker = opening.group(1)[0]
                fence_width = len(opening.group(1))
                mask(cursor, line_end)
                cursor = line_end
                continue
        if text.startswith("<!--", cursor):
            mask(cursor, cursor + 4)
            cursor += 4
            in_comment = True
            continue
        if text[cursor] == "`":
            run_end = cursor
            while run_end < len(text) and text[run_end] == "`":
                run_end += 1
            if not _is_backtick_escaped(text, cursor):
                code_end = _matching_inline_code_end(text, cursor, run_end)
                if code_end is not None:
                    mask(cursor, code_end)
                    cursor = code_end
                    continue
            cursor = run_end
            continue
        cursor += 1
    return tuple("".join(structural).splitlines())


def maintainer_korean_source_errors(text: str) -> tuple[str, ...]:
    errors: list[str] = []
    lines = _rendered_markdown_lines(text)
    h1_index = next(
        (index for index, line in enumerate(lines) if re.match(r"^# (?!#)", line)),
        None,
    )
    if h1_index is None or not re.search(r"[가-힣]{2,}", lines[h1_index]):
        errors.append("maintainer H1 must include a substantive Korean label")

    paragraph_lines: list[str] = []
    if h1_index is not None:
        for line in lines[h1_index + 1 :]:
            stripped = line.strip()
            if not stripped:
                if paragraph_lines:
                    break
                continue
            if stripped.startswith(("#", "- ", "* ", ">", "```", "~~~")):
                break
            paragraph_lines.append(stripped)
    paragraph = " ".join(paragraph_lines)
    has_korean_clause = bool(
        re.search(r"[가-힣]+(?:은|는|이|가|을|를|의|에서|으로)", paragraph)
    )
    has_korean_ending = bool(re.search(r"[가-힣]+(?:니다|세요)\.", paragraph))
    if not paragraph or not has_korean_clause or not has_korean_ending:
        errors.append("maintainer first explanatory paragraph must be substantive Korean prose")
    return tuple(errors)


def pre_sdd_shared_contract_errors(
    text: str,
    *,
    language: str,
    document: str,
) -> tuple[str, ...]:
    headings = {
        ("ko", "safety"): "## SDD 전 문서 검토",
        ("en", "safety"): "## Pre-SDD document review",
        ("ko", "verification"): "## 오프라인 픽스처",
        ("en", "verification"): "## Offline fixtures",
    }
    clauses = {
        ("ko", "safety"): (
            "`pre-sdd-review`는 로컬 설계, 구현 계획, 참조된 ADR, 저장소 파일을 읽습니다.",
            "기본 모드에서는 확인된 설계와 계획만 수정합니다.",
            "저장소 소유 테스트는 사용자 문서를 전송하거나 지속 저장하거나 픽스처로 수집하지 않습니다.",
            "이 제품은 텔레메트리나 업로드 경로를 추가하지 않습니다.",
            "라이브 처리와 보존은 Codex 호스트의 데이터 제어를 따릅니다.",
            "명시적인 외부 요청 없이는 구현이나 SDD를 시작하지 않습니다.",
            "원자적 로컬 저장은 협력하는 client 사이의 일관성을 제공할 뿐, 악의적인 로컬 변조를 막는 서명된 audit log가 아닙니다.",
        ),
        ("en", "safety"): (
            "`pre-sdd-review` reads local design, implementation plan, referenced ADR, and repository files.",
            "In default mode it edits only the resolved design and plan.",
            "Repository-owned tests do not transmit, persist, or capture user documents as fixtures.",
            "This product adds no telemetry or upload path.",
            "Live processing and retention follow the Codex host's data controls.",
            "It never starts implementation or SDD without an explicit outer request.",
            "Atomic local storage gives cooperating clients consistency; it is not a signed audit log resistant to malicious local tampering.",
        ),
        ("ko", "verification"): (
            "`pre-sdd-review`의 공급자 없는 픽스처는 지시와 패키지 계약만 검증합니다.",
            "리뷰어 독립성, 의미 완전성, 라이브 리뷰 품질을 증명하지 않습니다.",
            "비-Windows의 `windows-portable` 통과는 native Windows 지원을 증명하지 않습니다.",
        ),
        ("en", "verification"): (
            "Provider-free fixtures validate only instruction and package contracts.",
            "They do not prove reviewer independence, semantic completeness, or live review quality.",
            "A non-Windows `windows-portable` pass does not prove native Windows support.",
        ),
    }
    key = (language, document)
    owned = _owned_section(text, headings[key])
    if not owned:
        return ("pre-sdd shared section is missing or duplicated",)
    errors: list[str] = []
    if any(owned.count(clause) != 1 for clause in clauses[key]):
        errors.append("pre-sdd shared exact clauses differ")
    if hashlib.sha256(owned.encode("utf-8")).hexdigest() != PRE_SDD_SHARED_SECTION_DIGESTS[key]:
        errors.append("pre-sdd shared section differs from canonical contract")
    return tuple(errors)


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

    def test_product_readmes_follow_common_information_order(self) -> None:
        for product in REGISTRY.products:
            for filename in ("README.md", "README.en.md"):
                path = ROOT / product.skill_path / filename
                _assert_exists(self, path)
                text = _read(path)
                self.assertTrue(
                    text.startswith(f"# {product.display_name}\n"),
                    f"{product.name}/{filename} title",
                )
                if product.name == "pre-sdd-review":
                    headings = PRE_SDD_PRODUCT_HEADINGS[filename]
                else:
                    headings = PRODUCT_README_HEADINGS[filename]
                last = -1
                for heading in headings:
                    pos = text.find(heading)
                    self.assertGreaterEqual(
                        pos, 0, f"{product.name}/{filename} missing {heading!r}"
                    )
                    self.assertGreater(
                        pos, last, f"{product.name}/{filename} out of order: {heading!r}"
                    )
                    last = pos

    def test_how_it_works_readmes_include_supported_host_install_call_and_result(self) -> None:
        for filename in ("README.md", "README.en.md"):
            path = ROOT / "skills/how-it-works" / filename
            text = _read(path)
            self.assertIn(HOW_IT_WORKS_MKDIR, text)
            self.assertIn(HOW_IT_WORKS_AGENTS_LINK, text)
            self.assertIn(HOW_IT_WORKS_CLAUDE_LINK, text)
            self.assertIn(HOW_IT_WORKS_UNLINK_AGENTS, text)
            self.assertIn(HOW_IT_WORKS_UNLINK_CLAUDE, text)
            self.assertIn("$how-it-works", text)
            self.assertIn("/how-it-works", text)
            self.assertNotIn("@how-it-works", text)
            for host in ("codex", "claude-code"):
                self.assertIn(host, text.lower(), f"{filename} {host}")
            for phrase in HOW_IT_WORKS_EXPECTED_EN:
                self.assertIn(phrase, text, f"{filename} {phrase}")
            self.assertNotIn("Registered hosts:", text)
            self.assertNotIn("artifact-design", text)
            self.assertNotIn("브라우저에서 여는 페이지", text)
            self.assertNotIn("page you open in a browser", text.lower())
            self.assertTrue(
                "fails instead of overwriting" in text.lower() or "덮어쓰지 않고 실패" in text,
                f"{filename} must say ln -s fails instead of overwriting",
            )

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
    def test_root_readmes_do_not_treat_every_product_as_codex_only(self) -> None:
        korean = _read(ROOT / "README.md")
        english = _read(ROOT / "README.en.md")
        self.assertNotIn("Codex에서 설치해 쓰는 스킬 세 개", korean)
        self.assertNotIn("three skills you can install in Codex", english)
        self.assertIn("current standalone products", english)
        self.assertIn("현재 독립 제품", korean)
        for document in (korean, english):
            self.assertIn("Claude Code", document)
            self.assertIn("Codex", document)

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

    def test_compatibility_owns_the_registered_support_sentences(self) -> None:
        for document in (
            ROOT / "docs" / "users" / "ko" / "compatibility.md",
            ROOT / "docs" / "users" / "en" / "compatibility.md",
        ):
            _assert_exists(self, document)
            text = _read(document)
            for product in REGISTRY.products:
                self.assertIn(SUPPORT_BY_PRODUCT[product.name], text)
            lowered = text.lower()
            self.assertIn("claude.ai", lowered)
            self.assertIn("cowork", lowered)
            self.assertIn("skills api", lowered)
            self.assertTrue("marketplace" in lowered or "마켓플레이스" in text)
            self.assertTrue("catalog" in lowered or "카탈로그" in text)
            self.assertNotIn(
                "how-it-works: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.",
                text,
            )

    def test_docs_exclude_cloud_upload_support(self) -> None:
        active = "\n".join(path.read_text(encoding="utf-8") for path in active_markdown_paths(ROOT))
        for unsupported in ("skills api upload supported", "cowork supported", "claude.ai supported"):
            self.assertNotIn(unsupported, active.lower())

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
            self.assertIn(HOW_IT_WORKS_MKDIR, text)
            self.assertIn(HOW_IT_WORKS_AGENTS_LINK, text)
            self.assertIn(HOW_IT_WORKS_CLAUDE_LINK, text)
            self.assertIn(HOW_IT_WORKS_UNLINK_AGENTS, text)
            self.assertIn(HOW_IT_WORKS_UNLINK_CLAUDE, text)

    def test_how_it_works_install_and_remove_share_agents_destination(self) -> None:
        installer = INSTALLER_COMMANDS["how-it-works"]
        codex_home_targets = (
            "${CODEX_HOME:-$HOME/.codex}/skills/how-it-works",
            "$CODEX_HOME/skills/how-it-works",
        )
        guides = (
            (
                ROOT / "docs" / "users" / "en" / "installation.md",
                "## Primary install (Codex)",
                "## How It Works local links",
            ),
            (
                ROOT / "docs" / "users" / "ko" / "installation.md",
                "## 기본 설치 (Codex)",
                "## How It Works 로컬 링크",
            ),
        )
        for path, start, end in guides:
            text = _read(path)
            start_at = text.index(start)
            end_at = text.index(end)
            self.assertLess(start_at, end_at, path.name)
            primary = text[start_at:end_at]
            self.assertNotIn(installer, primary, f"{path.name} primary Codex block")
            for dest in codex_home_targets:
                self.assertNotIn(dest, text)
            if "~/.codex/skills/how-it-works" in text:
                self.assertIn("unlink ~/.codex/skills/how-it-works", text)
            self.assertIn("~/.agents/skills/how-it-works", text)
            self.assertIn(HOW_IT_WORKS_UNLINK_AGENTS, text)
            self.assertIn(HOW_IT_WORKS_UNLINK_CLAUDE, text)
        for filename in ("README.md", "README.en.md"):
            text = _read(ROOT / "skills/how-it-works" / filename)
            self.assertIn(installer, text)
            self.assertIn("~/.agents/skills/how-it-works", text)
            self.assertIn(HOW_IT_WORKS_UNLINK_AGENTS, text)
            for dest in codex_home_targets:
                self.assertNotIn(dest, text)
            if "~/.codex/skills/how-it-works" in text:
                self.assertIn("unlink ~/.codex/skills/how-it-works", text)
        for path in README_PATHS:
            text = _read(path)
            if installer in text:
                self.assertIn(
                    "~/.agents/skills/how-it-works",
                    text,
                    f"{path.name} lists $skill-installer for how-it-works without the agents destination",
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

    def test_windows_portable_user_guides_match_orchestrator_exclusions(self) -> None:
        for document in (
            ROOT / "docs" / "users" / "ko" / "verification.md",
            ROOT / "docs" / "users" / "en" / "verification.md",
        ):
            sentence = _windows_portable_exclusion_sentence(_read(document))
            self.assertEqual(
                _windows_portable_excluded_stages(sentence),
                WINDOWS_EXCLUDED_STAGES,
                document.name,
            )

    def test_pre_sdd_review_shared_guides_preserve_scope_and_evidence_limits(self) -> None:
        korean_installation = _read(ROOT / "docs/users/ko/installation.md")
        english_installation = _read(ROOT / "docs/users/en/installation.md")
        installer = INSTALLER_COMMANDS["pre-sdd-review"]
        self.assertIn(installer, korean_installation)
        self.assertIn(installer, english_installation)
        for text in (korean_installation, english_installation):
            self.assertIn("python3 skills/pre-sdd-review/evidence/evidence.py --version", text)
            self.assertIn("~/.pre-sdd-review/", text)
            self.assertNotIn("--bin-dir", text)
            self.assertNotIn("install.py", text)
            self.assertNotIn("pre-sdd-review-evidence launcher", text)
            self.assertNotIn("~/.local/bin/pre-sdd-review-evidence", text)

        korean_safety = _read(ROOT / "docs/users/ko/safety-and-privacy.md")
        english_safety = _read(ROOT / "docs/users/en/safety-and-privacy.md")
        self.assertEqual(
            pre_sdd_shared_contract_errors(korean_safety, language="ko", document="safety"),
            (),
        )
        self.assertEqual(
            pre_sdd_shared_contract_errors(english_safety, language="en", document="safety"),
            (),
        )

        korean_verification = _read(ROOT / "docs/users/ko/verification.md")
        english_verification = _read(ROOT / "docs/users/en/verification.md")
        self.assertIn("python3 scripts/verify.py --skill pre-sdd-review", korean_verification)
        self.assertIn("python3 scripts/verify.py --skill pre-sdd-review", english_verification)
        self.assertIn("pre-sdd-review-evidence", korean_verification)
        self.assertIn("pre-sdd-review-evidence", english_verification)
        self.assertIn("evidence.py", korean_verification)
        self.assertIn("evidence.py", english_verification)
        self.assertEqual(
            pre_sdd_shared_contract_errors(
                korean_verification,
                language="ko",
                document="verification",
            ),
            (),
        )
        self.assertEqual(
            pre_sdd_shared_contract_errors(
                english_verification,
                language="en",
                document="verification",
            ),
            (),
        )

    def test_pre_sdd_evidence_docs_forbid_sensitive_bounded_values_and_audit_claims(self) -> None:
        korean = _read(ROOT / "docs/users/ko/safety-and-privacy.md")
        english = _read(ROOT / "docs/users/en/safety-and-privacy.md")
        combined = re.sub(r"\s+", " ", korean + "\n" + english)
        for phrase in (
            "source text",
            "absolute paths",
            "prompts",
            "provider transcripts",
            "credentials",
            "automatic secret detection",
            "not a signed audit log",
            "bounded note, consequence, or fix",
            "may be re-recorded",
            "self-improvement evidence",
            "anomalies",
            "chains",
            "run_id",
        ):
            self.assertIn(phrase, combined)
        for phrase in (
            "The recorder does not promise automatic secret detection.",
            "Atomic local storage gives cooperating clients consistency; it is not a signed audit log resistant to malicious local tampering.",
            "An `outcome` label (`good`, `false-ready`, `noisy`, `abandoned`) is an observation recorded by a person or the SDD worker after SDD or implementation ends and may be re-recorded to correct it.",
            "Labels are self-improvement evidence, not objective quality judgments or audit-grade proof.",
            "Reading the log is an agent's task: `summary` returns JSON whose anomalies and chains carry run_id values.",
        ):
            self.assertIn(phrase, re.sub(r"\s+", " ", english))

    def test_pre_sdd_shared_clause_validator_rejects_reversed_polarities(self) -> None:
        cases = (
            (
                "ko",
                "safety",
                _read(ROOT / "docs/users/ko/safety-and-privacy.md"),
                (
                    ("확인된 설계와 계획만 수정합니다", "확인된 설계와 계획뿐 아니라 application code도 수정합니다"),
                    (
                        "저장소 소유 테스트는 사용자 문서를 전송하거나 지속 저장하거나 픽스처로 수집하지 않습니다",
                        "저장소 소유 테스트는 사용자 문서를 전송하고 지속 저장하고 픽스처로 수집합니다",
                    ),
                    (
                        "이 제품은 텔레메트리나 업로드 경로를 추가하지 않습니다",
                        "이 제품은 텔레메트리와 업로드 경로를 추가합니다",
                    ),
                    (
                        "라이브 처리와 보존은 Codex 호스트의 데이터 제어를 따릅니다",
                        "저장소 소유 테스트가 라이브 처리와 보존을 제어합니다",
                    ),
                    (
                        "저장소 소유 테스트는 사용자 문서를 전송하거나 지속 저장하거나 픽스처로 수집하지 않습니다",
                        "사용자 문서를 전송하거나 지속 저장하거나 저장소 소유 테스트 픽스처로 수집하지 않습니다",
                    ),
                    ("명시적인 외부 요청 없이는 구현이나 SDD를 시작하지 않습니다", "명시적인 외부 요청 없이도 구현이나 SDD를 시작합니다"),
                ),
            ),
            (
                "en",
                "safety",
                _read(ROOT / "docs/users/en/safety-and-privacy.md"),
                (
                    ("edits only the resolved design and plan", "edits not only the resolved design and plan but also application code"),
                    (
                        "Repository-owned tests do not transmit, persist, or capture user documents as fixtures",
                        "Repository-owned tests transmit, persist, and capture user documents as fixtures",
                    ),
                    (
                        "This product adds no telemetry or upload path",
                        "This product adds telemetry and an upload path",
                    ),
                    (
                        "Live processing and retention follow the Codex host's data controls",
                        "Repository-owned tests control live processing and retention",
                    ),
                    (
                        "Repository-owned tests do not transmit, persist, or capture user documents as fixtures",
                        "It does not transmit or persist user documents or capture them as repository-owned test fixtures",
                    ),
                    ("never starts implementation or SDD without an explicit outer request", "starts implementation or SDD without an explicit outer request"),
                ),
            ),
            (
                "ko",
                "verification",
                _read(ROOT / "docs/users/ko/verification.md"),
                (
                    ("지시와 패키지 계약만 검증합니다", "지시와 패키지 계약뿐 아니라 라이브 동작도 검증합니다"),
                    ("라이브 리뷰 품질을 증명하지 않습니다", "라이브 리뷰 품질을 증명합니다"),
                ),
            ),
            (
                "en",
                "verification",
                _read(ROOT / "docs/users/en/verification.md"),
                (
                    ("validate only instruction and package contracts", "validate instruction and package contracts plus live behavior"),
                    ("They do not prove reviewer independence, semantic completeness, or live review quality", "They prove reviewer independence, semantic completeness, and live review quality"),
                ),
            ),
        )
        for language, document, source, mutations in cases:
            for old, new in mutations:
                with self.subTest(language=language, document=document, mutation=new):
                    mutation = source.replace(old, new, 1)
                    self.assertNotEqual(mutation, source)
                    self.assertIn(
                        "pre-sdd shared exact clauses differ",
                        pre_sdd_shared_contract_errors(
                            mutation,
                            language=language,
                            document=document,
                        ),
                    )

    def test_pre_sdd_shared_validator_rejects_append_only_contradictions(self) -> None:
        cases = (
            (
                "ko",
                "safety",
                "## SDD 전 문서 검토",
                ROOT / "docs/users/ko/safety-and-privacy.md",
                "기본 모드에서도 application code를 수정해도 됩니다.",
            ),
            (
                "en",
                "safety",
                "## Pre-SDD document review",
                ROOT / "docs/users/en/safety-and-privacy.md",
                "In default mode, application code may also be edited.",
            ),
            (
                "ko",
                "verification",
                "## 오프라인 픽스처",
                ROOT / "docs/users/ko/verification.md",
                "이 픽스처 통과는 라이브 리뷰 품질도 증명합니다.",
            ),
            (
                "en",
                "verification",
                "## Offline fixtures",
                ROOT / "docs/users/en/verification.md",
                "Passing these fixtures also proves live review quality.",
            ),
        )
        for language, document, heading, path, contradiction in cases:
            with self.subTest(language=language, document=document):
                source = _read(path)
                mutation = _append_to_owned_section(source, heading, contradiction)
                self.assertNotEqual(mutation, source)
                self.assertIn(
                    "pre-sdd shared section differs from canonical contract",
                    pre_sdd_shared_contract_errors(
                        mutation,
                        language=language,
                        document=document,
                    ),
                )


class DocumentationArchitectureTests(unittest.TestCase):
    def test_only_four_user_guides_exist_per_language(self) -> None:
        expected = {"installation.md", "compatibility.md", "safety-and-privacy.md", "verification.md"}
        for language in ("ko", "en"):
            self.assertEqual({p.name for p in (ROOT / "docs/users" / language).glob("*.md")}, expected)
            self.assertFalse((ROOT / "docs" / language).exists())

    def test_live_docs_omit_removed_evidence_installer_names(self) -> None:
        documents = PUBLIC_DOC_PATHS + (ROOT / "skills/pre-sdd-review/CHANGELOG.md",)
        for document in documents:
            relative = document.relative_to(ROOT).as_posix()
            if relative.startswith("docs/history/"):
                continue
            text = _read(document)
            if document.name == "CHANGELOG.md":
                dated = re.search(
                    r"^## \S+ - [0-9]{4}-[0-9]{2}-[0-9]{2}\s*$",
                    text,
                    re.MULTILINE,
                )
                if dated is not None:
                    text = text[: dated.start()]
            for fragment in DEAD_RECORDER_STRINGS:
                self.assertNotIn(fragment, text, f"{relative} contains {fragment!r}")
            for phrase in DEAD_LAUNCHER_PHRASES:
                self.assertNotIn(phrase, text, f"{relative} contains {phrase!r}")

    def test_maintainer_index_owns_docs_maintenance_rules(self) -> None:
        text = _read(MAINTAINER_INDEX)
        normalized = re.sub(r"\s+", " ", text)
        for fact in (
            "제품 README",
            "docs/users/",
            "docs/maintainers/",
            "사실 하나",
            "한국어가 원본",
            "digest",
            "함께 고칠 파일",
            "진행 중",
        ):
            self.assertIn(fact, normalized)
        self.assertIn("docs/history/", text)

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
                self.assertEqual(maintainer_korean_source_errors(_read(path)), ())

    def test_korean_source_validator_requires_korean_h1_and_explanatory_prose(self) -> None:
        contract = _read(ROOT / "docs/maintainers/products/pre-sdd-review/contract.md")
        mutations = (
            (
                contract.replace("# pre-sdd-review 계약", "# pre-sdd-review contract", 1),
                "maintainer H1 must include a substantive Korean label",
            ),
            (
                contract.replace(
                    "이 문서는 Pre-SDD Review의 활성화 조건, 권위 순서, 리뷰어 격리,\n"
                    "문서 수정 경계, finding, freshness, verdict, SDD handoff를 소유합니다.",
                    "한.",
                    1,
                ),
                "maintainer first explanatory paragraph must be substantive Korean prose",
            ),
        )
        for mutation, expected_error in mutations:
            with self.subTest(mutation=mutation.splitlines()[:4]):
                self.assertNotEqual(mutation, contract)
                self.assertIn(expected_error, maintainer_korean_source_errors(mutation))

    def test_korean_source_validator_ignores_hidden_korean_markdown(self) -> None:
        cases = (
            (
                ROOT / "docs/maintainers/products/pre-sdd-review/testing.md",
                "# pre-sdd-review 테스트",
                "# pre-sdd-review testing",
                "이 문서는 provider-free contract evidence, 제한된 합성 픽스처, 선택적\n"
                "live-check 경계를 소유합니다. 모델의 실제 리뷰 품질을 측정했다고 주장하지\n"
                "않습니다.",
                "This document owns provider-free evidence and optional live checks.",
            ),
            (
                ROOT / "docs/maintainers/products/pre-sdd-review/compatibility.md",
                "# pre-sdd-review 호환성",
                "# pre-sdd-review compatibility",
                "이 문서는 Pre-SDD Review의 측정된 호스트 경계를 소유합니다.",
                "This document owns the measured-host boundary.",
            ),
            (
                ROOT / "docs/maintainers/products/how-it-works/testing.md",
                "# how-it-works 테스트",
                "# how-it-works testing",
                "공급자 없는 계약과 선택적 유료 smoke를 섞지 마세요. 사용자 주제, 공급자 트랜스크립트, 비공개 로그를 Git 픽스처로 커밋하지 마세요.",
                "Do not mix provider-free contracts with optional paid smoke checks.",
            ),
        )
        hidden_blocks = (
            "<!--\n# 숨겨진 한국어 제목\n이 문서는 숨겨진 한국어 설명을 제공합니다.\n-->\n",
            "<!--\n# 숨겨진 한국어 제목\n이 문서는 숨겨진 한국어 설명을 제공합니다.\n",
            "```text\n# 숨겨진 한국어 제목\n이 문서는 숨겨진 한국어 설명을 제공합니다.\n```\n",
            "```text\n# 숨겨진 한국어 제목\n이 문서는 숨겨진 한국어 설명을 제공합니다.\n",
            "~~~text\n# 숨겨진 한국어 제목\n이 문서는 숨겨진 한국어 설명을 제공합니다.\n",
        )
        expected = (
            "maintainer H1 must include a substantive Korean label",
            "maintainer first explanatory paragraph must be substantive Korean prose",
        )
        for path, source_h1, english_h1, source_prose, english_prose in cases:
            source = _read(path)
            rendered_english = source.replace(source_h1, english_h1, 1).replace(
                source_prose,
                english_prose,
                1,
            )
            self.assertNotEqual(rendered_english, source)
            for hidden_block in hidden_blocks:
                with self.subTest(path=path, hidden=hidden_block.splitlines()[0]):
                    mutation = hidden_block + rendered_english
                    self.assertEqual(maintainer_korean_source_errors(mutation), expected)

    def test_korean_source_validator_accepts_korean_after_literal_comment_fences(self) -> None:
        documents = (
            ROOT / "docs/maintainers/products/pre-sdd-review/testing.md",
            ROOT / "docs/maintainers/products/pre-sdd-review/compatibility.md",
            ROOT / "docs/maintainers/products/how-it-works/testing.md",
        )
        fenced_examples = (
            "```html\n<!-- literal comment -->\n```\n\n",
            "```text\n<!-- literal unclosed comment\n```\n\n",
            "~~~html\n<!-- literal comment -->\n~~~\n\n",
            "~~~text\n<!-- literal unclosed comment\n~~~\n\n",
        )
        for path in documents:
            source = _read(path)
            for fenced_example in fenced_examples:
                with self.subTest(path=path, fence=fenced_example.splitlines()[0]):
                    self.assertEqual(
                        maintainer_korean_source_errors(fenced_example + source),
                        (),
                    )

    def test_korean_source_validator_accepts_inline_code_comment_literal(self) -> None:
        documents = (
            ROOT / "docs/maintainers/products/pre-sdd-review/testing.md",
            ROOT / "docs/maintainers/products/pre-sdd-review/compatibility.md",
            ROOT / "docs/maintainers/products/how-it-works/testing.md",
        )
        for path in documents:
            source = _read(path)
            h1, remainder = source.split("\n", 1)
            _, following_sections = remainder.lstrip("\n").split("\n\n", 1)
            mutation = (
                f"{h1}\n\n"
                "이 문서는 inline code의 `<!--` 리터럴을 설명하며 한국어 원문을 유지합니다.\n\n"
                f"{following_sections}"
            )
            with self.subTest(path=path):
                self.assertEqual(maintainer_korean_source_errors(mutation), ())

    def test_korean_source_validator_accepts_multiline_code_comment_literal(self) -> None:
        documents = (
            ROOT / "docs/maintainers/products/pre-sdd-review/testing.md",
            ROOT / "docs/maintainers/products/pre-sdd-review/compatibility.md",
            ROOT / "docs/maintainers/products/how-it-works/testing.md",
        )
        code_spans = (
            "`literal\n<!-- remains literal\nspan`\n\n",
            "``literal\n<!-- remains literal\nspan``\n\n",
            "`literal\n<!-- remains literal\nspan\\`\n\n",
            "``literal\n<!-- remains literal\nspan\\``\n\n",
        )
        for path in documents:
            source = _read(path)
            for code_span in code_spans:
                with self.subTest(path=path, delimiter=code_span.split("literal", 1)[0]):
                    self.assertEqual(
                        maintainer_korean_source_errors(code_span + source),
                        (),
                    )

    def test_korean_source_validator_removes_comments_after_non_code_backticks(self) -> None:
        non_code_lines = (
            "\\`<!-- 이 문서는 숨겨진 한국어 설명을 제공합니다. -->\\`",
            "\\``<!-- 이 문서는 숨겨진 한국어 설명을 제공합니다. -->\\``",
            "`<!-- 이 문서는 숨겨진 한국어 설명을 제공합니다. -->",
            "``<!-- 이 문서는 숨겨진 한국어 설명을 제공합니다. -->",
        )
        expected = (
            "maintainer H1 must include a substantive Korean label",
            "maintainer first explanatory paragraph must be substantive Korean prose",
        )
        for non_code_line in non_code_lines:
            mutation = (
                "# rendered English\n\n"
                f"{non_code_line}\n\n"
                "This rendered explanatory paragraph is English.\n"
            )
            with self.subTest(non_code_line=non_code_line):
                self.assertEqual(maintainer_korean_source_errors(mutation), expected)

    def test_korean_source_validator_accepts_korean_after_comments_with_fence_literals(self) -> None:
        documents = (
            ROOT / "docs/maintainers/products/pre-sdd-review/testing.md",
            ROOT / "docs/maintainers/products/pre-sdd-review/compatibility.md",
            ROOT / "docs/maintainers/products/how-it-works/testing.md",
        )
        comments = (
            "<!--\n```text\nliteral unclosed fence\n-->\n\n",
            "<!--\n~~~text\nliteral unclosed fence\n-->\n\n",
        )
        for path in documents:
            source = _read(path)
            for comment in comments:
                with self.subTest(path=path, fence=comment.splitlines()[1]):
                    self.assertEqual(
                        maintainer_korean_source_errors(comment + source),
                        (),
                    )

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
        for product in REGISTRY.products:
            self.assertIn(product.name, text)
            self.assertIn(f"tests/products/{product.name}/", text)

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
        self.assertIn("동의가 불명확하면", contract_text)
        self.assertIn("`hold`", _read(contract))
        self.assertIn("inspector", testing_text)
        self.assertIn("inspect_asset.py", testing_text)
        self.assertIn("release.toml", release_text)
        self.assertIn("python3 scripts/release.py check --product image-workbench", release_text)

    def test_how_it_works_protocol_maps_contract_testing_compatibility_and_release(self) -> None:
        contract = ROOT / "docs" / "maintainers" / "products" / "how-it-works" / "contract.md"
        testing = ROOT / "docs" / "maintainers" / "products" / "how-it-works" / "testing.md"
        compatibility = (
            ROOT / "docs" / "maintainers" / "products" / "how-it-works" / "compatibility.md"
        )
        release = ROOT / "docs" / "maintainers" / "products" / "how-it-works" / "release.md"
        for path in (contract, testing, compatibility, release):
            _assert_exists(self, path)
        contract_text = _read(contract)
        testing_text = _read(testing)
        compatibility_text = _read(compatibility)
        release_text = _read(release)
        for token in ("trigger", "slice", "type", "rung", "language", "mermaid"):
            self.assertIn(token, contract_text.lower(), token)
        self.assertIn("$how-it-works", contract_text)
        self.assertIn("/how-it-works", contract_text)
        self.assertNotIn("@how-it-works", contract_text)
        self.assertNotIn("artifact-design", contract_text)
        self.assertNotIn("chat-only", contract_text.lower())
        for phrase in HOW_IT_WORKS_EXPECTED_EN:
            self.assertIn(phrase, contract_text, phrase)
        for fixture_id in HOW_IT_WORKS_FIXTURE_IDS:
            self.assertIn(fixture_id, testing_text)
        self.assertIn("/eli5", testing_text)
        self.assertIn("발견", testing_text)
        self.assertIn("명시", testing_text)
        self.assertIn("암묵", testing_text)
        self.assertIn("near-miss", testing_text)
        self.assertIn("~/.agents/skills/how-it-works", compatibility_text)
        self.assertIn("~/.claude/skills/how-it-works", compatibility_text)
        self.assertIn("$how-it-works", compatibility_text)
        self.assertIn("/how-it-works", compatibility_text)
        self.assertNotIn("@how-it-works", compatibility_text)
        self.assertIn("tests/products/how-it-works/live/smoke-record.json", compatibility_text)
        self.assertIn("release.toml", release_text)
        self.assertIn("1.0.0", release_text)
        self.assertIn("python3 scripts/release.py check --product how-it-works", release_text)
        self.assertIn("python3 scripts/release.py build --product how-it-works", release_text)
        self.assertIn(
            "python3 scripts/release.py verify-download --product how-it-works",
            release_text,
        )
        self.assertTrue(
            release_text.rstrip().endswith(RELEASE_NO_PUBLICATION),
            "release.md must end with the no-publication sentence",
        )

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
            for claim in STALE_TWO_SKILL + STALE_THREE_PRODUCT:
                self.assertNotIn(claim, lowered)

    def test_active_surfaces_omit_stale_two_skill_claims_and_obsolete_paths(self) -> None:
        for document in ACTIVE_ROUTING_SURFACES:
            _assert_exists(self, document)
            text = _read(document)
            lowered = text.lower()
            for claim in STALE_TWO_SKILL + STALE_THREE_PRODUCT:
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
