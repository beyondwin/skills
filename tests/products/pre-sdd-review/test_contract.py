from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter, validate_product  # noqa: E402
from scripts.lib.product_registry import load_registry  # noqa: E402


SKILL = ROOT / "skills" / "pre-sdd-review"
CASES = ROOT / "tests" / "products" / "pre-sdd-review" / "cases.json"
FIXTURES = ROOT / "tests" / "products" / "pre-sdd-review" / "fixtures"
PRE_SDD_REVIEW_PAYLOAD_FILES = frozenset(
    {
        "CHANGELOG.md",
        "LICENSE.txt",
        "README.en.md",
        "README.md",
        "SKILL.md",
        "agents/openai.yaml",
        "evidence/README.md",
        "evidence/install.py",
        "evidence/pre_sdd_review_evidence/__init__.py",
        "evidence/pre_sdd_review_evidence/__main__.py",
        "evidence/pre_sdd_review_evidence/cli.py",
        "evidence/pre_sdd_review_evidence/repository.py",
        "evidence/pre_sdd_review_evidence/reporting.py",
        "evidence/pre_sdd_review_evidence/schema.py",
        "evidence/pre_sdd_review_evidence/storage.py",
        "references/reviewer-protocol.md",
        "release.toml",
    }
)
INSTRUCTION_DOCUMENT_SHA256 = {
    "SKILL.md": "1471ddc7b09c80803f51908277d1f4196419ad48996a9ebffdbafc2cce6e67b6",
    "references/reviewer-protocol.md": (
        "e8a361b36bb261c98887bef8df549b9d6c59519dfdb618cfb7e54646e052aa6d"
    ),
}
CASE_IDS = (
    "default-auto-improve",
    "explicit-review-only",
    "ready-zero-findings",
    "missing-spec-coverage",
    "nonexistent-command",
    "extension-collision",
    "false-positive-smoke",
    "task-interface-order",
    "runtime-removal-risk-review",
    "stale-document-hash",
    "ambiguous-multiple-plans",
    "near-miss-write-spec",
    "near-miss-write-plan",
    "near-miss-code-review",
    "near-miss-release-review",
)
FIXTURE_NAMES = (
    "conditional-edit-surface",
    "repair-induced-schema-consumer",
    "ready",
    "missing-coverage",
    "false-verification",
    "runtime-removal",
    "state-machine-vacuous-pass",
)
FIXTURE_FILES = (
    "design.md",
    "plan.md",
    "repository.json",
    "expected.json",
)
REPOSITORY_MANIFEST = {
    "head": "0123456789abcdef0123456789abcdef01234567",
    "dirty": False,
    "paths": ["package.json", "src/app.ts", "tests/app.test.ts"],
    "commands": ["npm test", "npm run build"],
}
FIXTURE_CONTENTS = {
    "ready": {
        "design.md": """# sample-app message rendering

## Requirements

- Implement `renderMessage(input: string): string` in `src/app.ts`.
- The function returns the rendered string for the supplied input.
""",
        "plan.md": """# sample-app message rendering plan

**Spec:** design.md

## Implementation

1. Create `renderMessage(input: string): string` in `src/app.ts`.
2. Add a unit test in `tests/app.test.ts` that calls `renderMessage(\"hello\")`
   and verifies that it returns `\"hello\"`.
3. Add a unit test in `tests/app.test.ts` that calls `renderMessage(\"bye\")`
   and verifies that it returns `\"bye\"`.
4. Run `npm test` and `npm run build`.
""",
        "repository.json": """{
  \"head\": \"0123456789abcdef0123456789abcdef01234567\",
  \"dirty\": false,
  \"paths\": [\"package.json\", \"src/app.ts\", \"tests/app.test.ts\"],
  \"commands\": [\"npm test\", \"npm run build\"]
}
""",
        "expected.json": """{
  \"verdict\": \"READY\",
  \"findings\": []
}
""",
    },
    "missing-coverage": {
        "design.md": """# sample-app message rendering

## Requirements

- Implement `renderMessage(input: string): string` in `src/app.ts`.
- The function returns the rendered string for the supplied input.
- Empty input is rejected.
""",
        "plan.md": """# sample-app message rendering plan

**Spec:** design.md

## Implementation

1. Create `renderMessage(input: string): string` in `src/app.ts`.
2. Add a unit test in `tests/app.test.ts` that calls `renderMessage(\"hello\")`
   and verifies that it returns `\"hello\"`.
3. Run `npm test` and `npm run build`.
""",
        "repository.json": """{
  \"head\": \"0123456789abcdef0123456789abcdef01234567\",
  \"dirty\": false,
  \"paths\": [\"package.json\", \"src/app.ts\", \"tests/app.test.ts\"],
  \"commands\": [\"npm test\", \"npm run build\"]
}
""",
        "expected.json": """{
  \"verdict\": \"REVISE\",
  \"findings\": [
    {
      \"id\": \"PSDR-001\",
      \"severity\": \"BLOCKER\",
      \"class\": \"coverage\"
    }
  ]
}
""",
    },
    "false-verification": {
        "design.md": """# sample-app message rendering

## Requirements

- Implement `renderMessage(input: string): string` in `src/app.ts`.
- `renderMessage(\"hello\")` returns the rendered string `\"hello\"`.
""",
        "plan.md": """# sample-app message rendering plan

**Spec:** design.md

## Implementation

1. Create `renderMessage(input: string): string` in `src/app.ts`.
2. Run `npm run build` and treat a successful build as acceptance.
""",
        "repository.json": """{
  \"head\": \"0123456789abcdef0123456789abcdef01234567\",
  \"dirty\": false,
  \"paths\": [\"package.json\", \"src/app.ts\", \"tests/app.test.ts\"],
  \"commands\": [\"npm test\", \"npm run build\"]
}
""",
        "expected.json": """{
  \"verdict\": \"REVISE\",
  \"findings\": [
    {
      \"id\": \"PSDR-001\",
      \"severity\": \"IMPORTANT\",
      \"class\": \"verification-gap\"
    }
  ]
}
""",
    },
    "runtime-removal": {
        "design.md": """# sample-app runtime replacement

## Requirements

- Replace the sample-app runtime while preserving the message-rendering behavior.
""",
        "plan.md": """# sample-app runtime replacement plan

**Spec:** design.md

## Implementation

1. Remove `src/app.ts`.
2. Replace the application runtime and move message rendering to the new runtime.
3. Run `npm test` and `npm run build`.
""",
        "repository.json": """{
  \"head\": \"0123456789abcdef0123456789abcdef01234567\",
  \"dirty\": false,
  \"paths\": [\"package.json\", \"src/app.ts\", \"tests/app.test.ts\"],
  \"commands\": [\"npm test\", \"npm run build\"]
}
""",
        "expected.json": """{
  \"risk_reviewer_required\": true,
  \"risk_trigger\": \"framework-or-runtime-removal\"
}
""",
    },
}
V1_1_FIXTURE_SHA256 = {
    "conditional-edit-surface": "a4f112034ee3173dcfcef723d73f2c493e45469dcd886931ee91710a62f242f2",
    "repair-induced-schema-consumer": "f96f0462b738542a14ce27db28be219884440613d0c24262a34036d262685e0c",
    "state-machine-vacuous-pass": "dd490c6a092c1ff180e599076372e2006661b22ffbebacfccccf48b44f71d8c0",
}
REQUIRED_SECTIONS = (
    "# Pre-SDD Review",
    "## Hard gate",
    "## Resolve authoritative inputs",
    "## Capture freshness",
    "## Select reviewers",
    "## Default mode: review -> repair documents -> scoped re-review",
    "## Review-only mode",
    "## Repair rules",
    "## Verdict and handoff",
    "## Do not use this skill for",
)
AUTHORITY_ORDER = (
    "User-approved direction and referenced visual authority.",
    "Accepted ADRs and other explicitly binding decision records.",
    "The approved design specification.",
    "The implementation plan.",
    "Current repository reality.",
)
RISK_TRIGGERS = (
    "framework or runtime removal",
    "schema migration or data deletion",
    "authentication, authorization, or security boundaries",
    "public/private data-boundary changes",
    "external side effects such as publishing, billing, messaging, or production mutations",
)
FINDING_SEVERITIES = ("BLOCKER", "IMPORTANT")
FINDING_CLASSES = (
    "authority-drift",
    "repo-reality",
    "coverage",
    "ordering",
    "verification-gap",
)
MUTATION_EXCLUSIONS = (
    "accepted ADRs",
    "approved visual authority",
    "application code",
    "tests",
    "configuration",
    "generated artifacts",
    "unrelated documentation",
)
MUTATION_ALLOWLIST = (
    "resolved design specification",
    "resolved implementation plan",
)
FINDING_RECORD = (
    "ID: PSDR-001",
    "Severity: BLOCKER | IMPORTANT",
    "Class: authority-drift | repo-reality | coverage | ordering | verification-gap",
    "Location: exact document path and heading or line",
    "Evidence: repository or cross-document fact",
    "Consequence: concrete implementation failure",
    "Minimal document fix: smallest authority-preserving correction",
)
KOREAN_FACTS = (
    "$pre-sdd-review",
    "검토 → 문서 개선 → 재검토",
    "review-only",
    "최대 두 번",
    "READY",
    "REVISE",
    "BLOCKED",
    "Codex",
    "not_measured",
)
ENGLISH_FACTS = (
    "$pre-sdd-review",
    "review -> repair documents -> scoped re-review",
    "review-only",
    "at most two repair passes",
    "READY",
    "REVISE",
    "BLOCKED",
    "Codex",
    "not_measured",
)
KOREAN_README_HEADINGS = (
    "## 이 스킬이 해결하는 문제",
    "## 사용해야 할 때와 사용하지 말아야 할 때",
    "## 1분 설치와 첫 호출",
    "## 주요 흐름",
    "## 안전과 개인정보",
    "## 호환성과 검증 수준",
    "## 갱신과 버전 확인",
    "## 변경 이력과 관리자 문서",
)
ENGLISH_README_HEADINGS = (
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
)
MAINTAINERS = ROOT / "docs" / "maintainers" / "products" / "pre-sdd-review"
DEFAULT_FIRST_CALL = (
    "$pre-sdd-review docs/history/specs/<design>.md "
    "docs/history/plans/<plan>.md"
)
README_CONTRACT = (
    ("primary-input", ("plan-primary", "spec-resolves-design")),
    ("plan-cardinality", ("one-plan-per-invocation", "no-aggregate-ready")),
    ("editable-surfaces", ("resolved-design-specification", "resolved-implementation-plan")),
    ("review-only", ("no-mutation",)),
    ("repair-flow", ("review-repair-bounded-impact-re-review",)),
    ("repair-impact", ("structural-trigger-only", "direct-consumers")),
    ("repair-passes", ("at-most-two",)),
    ("verdicts", ("READY", "REVISE", "BLOCKED")),
    ("second-reviewer", ("conditional-only",)),
    (
        "risk-triggers",
        (
            "framework-runtime-removal",
            "schema-data-deletion",
            "auth-security-boundary",
            "data-boundary-change",
            "external-side-effects",
        ),
    ),
    ("freshness", ("fingerprints", "content-change-invalidates")),
    ("handoff", ("unresolved-packet",)),
    ("sdd", ("outer-request-implementation-only",)),
)
README_CANONICAL_SECTION_DIGESTS = {
    "ko": (
        ("## 이 스킬이 해결하는 문제", "059b67628c9931409945145dd628468f62853ad2f502183bad164f15984abb2e"),
        ("## 사용해야 할 때와 사용하지 말아야 할 때", "e561f24683695a2a081dbee9911821fce3a3ccbbbc52a607d96bfe76185e4d8c"),
        ("## 1분 설치와 첫 호출", "20d4ac5b06601ac16c4fd995a652fca8e9162dee28a0278108f7c94fa760d4aa"),
        ("## 주요 흐름", "9afd9373fdc996a0b96b07fc58450b3e92c950696776c6a334a07798faa0a29a"),
        ("## 안전과 개인정보", "dea164c33a94794be32109070c22cfcb05245b599e8bb8712018df995f036845"),
        ("## 호환성과 검증 수준", "32ae6efc3bd8d980262a975e41958de4f49688744e719f4f2a92b85b6e6a5ef1"),
        ("## 갱신과 버전 확인", "cdba0c18b5fa475a30d52f3b8dec1cbeba902873bcfe2ccd64ad1a93a4aa457e"),
        ("## 변경 이력과 관리자 문서", "7e1cb70139ec2f47b67004352fdd0ca739f19515c2c715095501268c5b7405ac"),
    ),
    "en": (
        ("## Purpose", "6a0b1a1ed183aa142b9df51b9c2c8a13696df6ddff410d9e198bbb79bc441c1e"),
        ("## When to use and not use", "7133b17ed84bc5f8e1721b63ec5ffbf63f462f0816014c2bbfd4aeef58925d4d"),
        ("## Supported hosts", "adb46f35ba78974f2c3f4df43deca598c9558480606022f07ccce3626b70edc6"),
        ("## Install", "d5163949c27feaa36279e4bfebb1f6cc9dd269079567b5c96ec1314cf08035b7"),
        ("## First call", "27b7d3681619789c1e0fadff8d1dd802cdc387b70bddde1457adfbead72caff2"),
        ("## Expected result", "df01c48b84b5cf87c7367e20bd7a23bfcd0d92e259d0dff0d12445d1454ca4eb"),
        ("## Safety and privacy", "e654b5ffb7381e162c135673b092b27a62eac49fc2d372c75d840dcd16f9c756"),
        ("## Verification", "602a43f5501e8cb0d77254324bbf8fe72c1de9251a11263e902d02bf0edf791b"),
        ("## Update and remove", "3041985025dea4c4e636368de6d72f214b14f37e2e74b58431fdc74d25d4fb83"),
        ("## Changelog and maintainer docs", "7a5611089ddaf6819881da0ae7d96ec6ce36107f2c0076e9528499437749e7b1"),
    ),
}
README_CANONICAL_DOCUMENT_DIGESTS = {
    "ko": "03374b87d0b99bf60ffad48867e23785b60ba9bd031efa2e27a0e1ee3e9f945c",
    "en": "986634ed74054f7ef7f1f72d8843789652a5babc3acf3069ead49d17e636db5d",
}
MAINTAINER_CANONICAL_SUBSECTION_DIGESTS = (
    ("### Authority order", "3156a43d665d21723ce61b333c7c34f30abd2e6d288c472d5eec5878e5ef8321"),
    ("### Editable paths", "4c7d511afb38f386f06926cfa9b7b6307a7d2fb9e1b69ae0254021ca7fbaba8e"),
    ("### Excluded surfaces", "892b4d931a0e8c7bbf0979e4303e512eaf3af1ebe4e18063b699a05f5f7adaee"),
    ("### Review passes", "85923c91aaadfe1eea3a6dfad1ba81e43e5df9d99ba111b5116c63dbff80e018"),
    ("### Severities", "72c20c936027d62761c1b2dd9ef16b954c0780d7a15b4b1e05cf33e28b383ebd"),
    ("### Finding classes", "2a0892a5aad034ceaf1218606d657f4b22bac89c0d2b67065b7018e811a44352"),
    ("### Conditional risk triggers", "beb83c2728bf4bcc9ee15a353a1391971daa10bd59c45fea6a6fd641333db10c"),
    ("### Verdicts", "6bbc48d01219299cd47b1ae4f6f44952ce497012736b0785551fdb0995aacb00"),
    ("### Freshness", "0aeb0ada39c01280c13124db6cadb057a1748837991e10ceee85e93415e7e3a6"),
    ("### SDD handoff", "8a629dd12d78e2c08e77e7c1d057d0e450b135bc0633d5b62c8c926665976bca"),
)
MAINTAINER_CANONICAL_DIGEST = "1e44e3610721ae1a66b925dc3fefea370dd82564126a45cb84eb1ec8477246b2"
TESTING_CANONICAL_DIGEST = "e119980c8a7c1b7fa20e31aa539e3312aae73a7776076531c8b7cba2b613bec2"
COMPATIBILITY_CANONICAL_DIGEST = "3c40b77eb9a96892a07132d62b99cb43321b87516a0bdc4b0a33d033430828c6"
RELEASE_CANONICAL_DIGEST = "f20fa8ef3504d16125a766433bd7a84686340949ea7704f1946dc8c740006981"


def section(text: str, start: str, end: str) -> str:
    return text[text.index(start) : text.index(end, text.index(start) + len(start))]


def markdown_headings(text: str) -> tuple[tuple[int, str, int], ...]:
    headings: list[tuple[int, str, int]] = []
    fence: str | None = None
    offset = 0
    for line in text.splitlines(keepends=True):
        fence_match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker[0]
            elif marker[0] == fence:
                fence = None
            offset += len(line)
            continue
        if fence is None:
            heading_match = re.match(r"^(#{2,3}) (.+?)\s*$", line.rstrip("\n"))
            if heading_match:
                headings.append(
                    (len(heading_match.group(1)), heading_match.group(0), offset)
                )
        offset += len(line)
    return tuple(headings)


def bounded_markdown_section(text: str, heading: str) -> str:
    candidates = [item for item in markdown_headings(text) if item[1] == heading]
    if len(candidates) != 1:
        return ""
    level, _, start = candidates[0]
    end = len(text)
    for next_level, _, next_start in markdown_headings(text):
        if next_start > start and next_level <= level:
            end = next_start
            break
    return text[start:end]


def markdown_section(text: str, heading: str) -> str:
    return bounded_markdown_section(text, heading)


def subsection(text: str, heading: str) -> str:
    return bounded_markdown_section(text, heading)


def pre_sdd_invocations(text: str) -> tuple[str, ...]:
    return tuple(
        invocation.strip()
        for invocation in re.findall(r"^\s*\$pre-sdd-review[^\n]*$", text, re.MULTILINE)
    )


def canonical_digest(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def whole_document_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def product_payload_contract_errors(skill_root: Path) -> tuple[str, ...]:
    present = {
        path.relative_to(skill_root).as_posix()
        for path in skill_root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.relative_to(skill_root).parts
    }
    errors = [
        f"missing payload member: {relative}"
        for relative in sorted(PRE_SDD_REVIEW_PAYLOAD_FILES - present)
    ]
    errors.extend(
        f"unexpected payload member: {relative}"
        for relative in sorted(present - PRE_SDD_REVIEW_PAYLOAD_FILES)
    )
    for relative, expected_digest in INSTRUCTION_DOCUMENT_SHA256.items():
        document = skill_root / relative
        if document.is_file() and hashlib.sha256(document.read_bytes()).hexdigest() != expected_digest:
            label = "SKILL.md" if relative == "SKILL.md" else "reviewer protocol"
            errors.append(f"{label} differs from the closed canonical document")
    return tuple(errors)


def parse_readme_contract(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    contract = subsection(text, "### Contract")
    entries = re.findall(r"^- `([a-z-]+)`: (.+)$", contract, re.MULTILINE)
    return tuple((name, tuple(re.findall(r"`([A-Za-z0-9-]+)`", value))) for name, value in entries)


def readme_contract_errors(text: str) -> tuple[str, ...]:
    errors: list[str] = []
    language = "en" if markdown_section(text, "## Purpose") else "ko"
    if whole_document_digest(text) != README_CANONICAL_DOCUMENT_DIGESTS[language]:
        errors.append("README differs from the closed canonical document")
    canonical_sections = README_CANONICAL_SECTION_DIGESTS[language]
    actual_headings = tuple(
        heading for level, heading, _ in markdown_headings(text) if level == 2
    )
    if actual_headings != tuple(heading for heading, _ in canonical_sections) or any(
        canonical_digest(markdown_section(text, heading)) != digest
        for heading, digest in canonical_sections
    ):
        errors.append("README sensitive sections differ from the canonical contract")
    first_call_heading = "## First call" if language == "en" else "## 1분 설치와 첫 호출"
    first_call = markdown_section(text, first_call_heading)
    if not first_call:
        errors.append("missing First call section")
    if pre_sdd_invocations(first_call) != (DEFAULT_FIRST_CALL,):
        errors.append("first call must contain only the approved invocation")
    if parse_readme_contract(text) != README_CONTRACT:
        errors.append("bounded README contract differs from the product contract")
    return tuple(errors)


def numbered_items(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"^\d+\. (.+?)[.;]$", text, re.MULTILINE))


def backtick_list(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"^- `([^`]+)`", text, re.MULTILINE))


def maintainer_contract_errors(text: str) -> tuple[str, ...]:
    errors: list[str] = []
    if (
        canonical_digest(text) != MAINTAINER_CANONICAL_DIGEST
        or any(
            canonical_digest(subsection(text, heading)) != digest
            for heading, digest in MAINTAINER_CANONICAL_SUBSECTION_DIGESTS
        )
    ):
        errors.append("maintainer contract differs from the closed canonical contract")
    authority = subsection(text, "### Authority order")
    if tuple(re.findall(r"^\d+\. (.+)$", authority, re.MULTILINE)) != AUTHORITY_ORDER:
        errors.append("authority order differs")
    if numbered_items(subsection(text, "### Editable paths")) != MUTATION_ALLOWLIST:
        errors.append("editable paths differ")
    if backtick_list(subsection(text, "### Excluded surfaces")) != MUTATION_EXCLUSIONS:
        errors.append("excluded surfaces differ")
    if numbered_items(subsection(text, "### Review passes")) != (
        "authority trace",
        "repository grounding",
        "cross-artifact consistency",
        "verification falsification",
        "readiness verdict",
    ):
        errors.append("review passes differ")
    if backtick_list(subsection(text, "### Severities")) != FINDING_SEVERITIES:
        errors.append("severities differ")
    if backtick_list(subsection(text, "### Finding classes")) != FINDING_CLASSES:
        errors.append("finding classes differ")
    risks = subsection(text, "### Conditional risk triggers")
    if backtick_list(risks) != RISK_TRIGGERS or "conditional only" not in risks:
        errors.append("risk triggers must be conditional and exact")
    verdicts = subsection(text, "### Verdicts")
    for verdict, meaning in (
        ("READY", "no unresolved finding requires invention"),
        ("REVISE", "repairable material document defect"),
        ("BLOCKED", "required input, authority, or repository evidence is unavailable"),
    ):
        if f"`{verdict}`" not in verdicts or meaning not in verdicts:
            errors.append(f"{verdict} definition differs")
    freshness = subsection(text, "### Freshness")
    for field in (
        "repository-relative design path and SHA-256",
        "repository-relative plan path and SHA-256",
        "Git `HEAD` (or `unborn`)",
        "worktree was clean or dirty",
        "review timestamp",
        "final verdict",
        "Any content change to either resolved document invalidates `READY`",
    ):
        if field not in freshness:
            errors.append("freshness contract differs")
            break
    handoff = subsection(text, "### SDD handoff")
    if "Do not start SDD unless the outer request explicitly asks for implementation" not in handoff:
        errors.append("SDD handoff differs")
    return tuple(errors)


def fixture_inventory() -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (path.name, tuple(sorted(file.name for file in path.iterdir())))
        for path in sorted(FIXTURES.iterdir())
    )


def parse_fixture_inventory(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    inventory = subsection(text, "### Fixture inventory")
    return tuple(
        (name, tuple(re.findall(r"`([^`]+)`", files)))
        for name, files in re.findall(r"^- `([^`]+)`: (.+)$", inventory, re.MULTILINE)
    )


def testing_document_errors(text: str) -> tuple[str, ...]:
    errors: list[str] = []
    if whole_document_digest(text) != TESTING_CANONICAL_DIGEST:
        errors.append("testing document differs from the closed canonical contract")
    case_ids = tuple(case["id"] for case in json.loads(CASES.read_text(encoding="utf-8"))["cases"])
    if backtick_list(subsection(text, "### Case inventory")) != case_ids:
        errors.append("case inventory differs")
    if parse_fixture_inventory(text) != fixture_inventory():
        errors.append("fixture inventory differs")
    normalized = re.sub(r"\s+", " ", text)
    for required in (
        "fresh Codex session",
        "non-sensitive synthetic design and plan",
        "record only host, client version, date, case identifier, and verdict",
        "user documents",
        "full model responses",
        "optional",
        "billable",
        "CI never",
    ):
        if required not in normalized:
            errors.append("live-check boundary differs")
            break
    return tuple(errors)


def compatibility_document_errors(text: str) -> tuple[str, ...]:
    errors: list[str] = []
    if whole_document_digest(text) != COMPATIBILITY_CANONICAL_DIGEST:
        errors.append("compatibility document differs from the closed canonical contract")
    registry = load_registry(ROOT / "products.toml")
    product = registry.require("pre-sdd-review")
    hosts = tuple(sorted({host for item in registry.products for host in item.supported_hosts}))
    expected = tuple((host, "supported" if host in product.supported_hosts else "not_measured") for host in hosts)
    matrix = subsection(text, "### Host matrix")
    actual = tuple(re.findall(r"^\| `([^`]+)` \| `([^`]+)` \|$", matrix, re.MULTILINE))
    if actual != expected:
        errors.append("host matrix differs from products.toml")
    return tuple(errors)


def fenced_code_blocks(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"```[^\n]*\n(.*?)\n```", text, re.DOTALL))


def release_document_errors(text: str) -> tuple[str, ...]:
    release = tomllib.loads((SKILL / "release.toml").read_text(encoding="utf-8"))
    errors: list[str] = []
    if whole_document_digest(text) != RELEASE_CANONICAL_DIGEST:
        errors.append("release document differs from the closed canonical contract")
    identity = f"`{release['name']}` `version {release['version']}`"
    if identity not in text or f"`skills/{release['name']}/release.toml`" not in text:
        errors.append("release identity or version source differs")
    commands = (
        f"python3 scripts/release.py check --product {release['name']}",
        f"python3 scripts/release.py build --product {release['name']} --output <new-empty-directory>",
        f"python3 scripts/release.py verify-download --product {release['name']} --input <fresh-download-directory>",
    )
    if not all(command in text for command in commands):
        errors.append("release commands differ")
    command_lines = tuple(line for block in fenced_code_blocks(text) for line in block.splitlines())
    if not all(command in command_lines for command in commands):
        errors.append("release commands must be fenced command lines")
    return tuple(errors)


def second_review_risk_triggers(reviewers: str) -> tuple[str, ...]:
    match = re.search(
        r"A second fresh reviewer\s+is conditional, not routine: dispatch one focused "
        r"reviewer only for\s+(.+?)\.\s+It examines only the triggered risk class\.",
        reviewers,
        re.DOTALL,
    )
    if match is None:
        raise AssertionError("missing bounded second-review trigger list")
    return tuple(
        re.sub(r"\s+", " ", trigger).strip().removeprefix("or ")
        for trigger in match.group(1).split(";")
    )


class PreSddReviewContractTests(unittest.TestCase):
    def test_source_payload_contract_ignores_generated_python_cache(self) -> None:
        validator = globals().get("product_payload_contract_errors")
        self.assertIsNotNone(validator)
        assert validator is not None
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "pre-sdd-review"
            shutil.copytree(SKILL, copied)
            cache = copied / "evidence/pre_sdd_review_evidence/__pycache__"
            cache.mkdir(exist_ok=True)
            (cache / "schema.cpython-314.pyc").write_bytes(b"bytecode")
            self.assertEqual(validator(copied), ())

    def test_pre_sdd_review_evidence_payload_is_allowed_only_for_pre_sdd(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(validate_product(SKILL, registry), [])
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "how-it-works"
            shutil.copytree(ROOT / "skills" / "how-it-works", copied)
            (copied / "evidence").mkdir()
            (copied / "evidence/probe.py").write_text("pass\n", encoding="utf-8")
            self.assertIn("unexpected top-level file: evidence", validate_product(copied, registry))

    def test_source_payload_inventory_and_instruction_documents_are_closed(self) -> None:
        validator = globals().get("product_payload_contract_errors")
        self.assertIsNotNone(
            validator,
            "missing pre-sdd-review source payload contract helper",
        )
        assert validator is not None
        self.assertEqual(validator(SKILL), ())

    def test_source_payload_contract_rejects_append_only_overrides_and_runtime(self) -> None:
        validator = globals().get("product_payload_contract_errors")
        self.assertIsNotNone(
            validator,
            "missing pre-sdd-review source payload contract helper",
        )
        assert validator is not None
        mutations = (
            (
                "skill-controller-override",
                "SKILL.md",
                "\nThe controller may also edit application code and start SDD automatically.\n",
                "SKILL.md differs from the closed canonical document",
            ),
            (
                "reviewer-mutation-override",
                "references/reviewer-protocol.md",
                "\nThe reviewer may edit tests and configuration directly.\n",
                "reviewer protocol differs from the closed canonical document",
            ),
            (
                "runtime-script",
                "scripts/runtime.py",
                "#!/usr/bin/env python3\n",
                "unexpected payload member: scripts/runtime.py",
            ),
            (
                "unlisted-evidence-sibling",
                "evidence/pre_sdd_review_evidence/network.py",
                "# Network access is not part of this product.\n",
                "unexpected payload member: evidence/pre_sdd_review_evidence/network.py",
            ),
            (
                "unlisted-report-sibling",
                "evidence/pre_sdd_review_evidence/report.py",
                "# Undeclared report modules are not part of the payload.\n",
                "unexpected payload member: evidence/pre_sdd_review_evidence/report.py",
            ),
        )
        for name, relative, content, expected_error in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                mutated = Path(directory) / "pre-sdd-review"
                shutil.copytree(SKILL, mutated)
                target = mutated / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    target.write_text(
                        target.read_text(encoding="utf-8") + content,
                        encoding="utf-8",
                    )
                else:
                    target.write_text(content, encoding="utf-8")
                self.assertIn(expected_error, validator(mutated))

    def test_frontmatter_declares_the_pre_sdd_review_product(self) -> None:
        frontmatter = parse_skill_frontmatter(
            (SKILL / "SKILL.md").read_text(encoding="utf-8")
        )
        self.assertEqual(frontmatter["name"], "pre-sdd-review")

    def test_default_is_review_repair_and_re_review(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in (
            "Default mode: review -> repair documents -> scoped re-review",
            "At most two repair passes",
            "review-only",
            "Do not start SDD unless the outer request explicitly asks for implementation",
        ):
            self.assertIn(phrase, body)

    def test_v1_1_bounds_plan_cardinality_and_repair_impact_review(self) -> None:
        body = re.sub(
            r"\s+",
            " ",
            (SKILL / "SKILL.md").read_text(encoding="utf-8"),
        )
        for phrase in (
            "One invocation reviews exactly one implementation plan",
            "return `BLOCKED` instead of inventing an aggregate verdict",
            "repair-impact map",
            "modified claim",
            "direct consumers",
            "adjacent task interfaces",
            "verified-no-change",
            "bounded repair-impact regression",
            "final repaired documents",
            "unresolved handoff packet",
        ):
            self.assertIn(phrase, body)
        self.assertNotIn("program mode", body.lower())

    def test_v1_1_protocol_closes_structural_repairs_without_forcing_nonempty_results(self) -> None:
        protocol = re.sub(
            r"\s+",
            " ",
            (SKILL / "references/reviewer-protocol.md").read_text(encoding="utf-8"),
        )
        for phrase in (
            "introduces or changes a state machine",
            "producer domain",
            "partition completeness",
            "An empty domain is valid when the producer proves it is empty",
            "bounded path pattern",
            "modify`, `verified-no-change`, or `unresolved",
        ):
            self.assertIn(phrase, protocol)

    def test_reviewer_is_read_only_and_controller_owns_repairs(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Reviewer mutation policy: read-only", protocol)
        self.assertIn("The controlling agent applies document repairs", protocol)
        self.assertIn("Never edit application code", protocol)

    def test_accepted_authority_cannot_be_auto_edited(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("accepted ADR", "approved visual authority", "BLOCKED"):
            self.assertIn(phrase, body)

    def test_no_minimum_finding_quota(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Zero findings is valid", protocol)
        self.assertNotRegex(protocol, r"(?i)(at least|minimum)\s+[0-9]+\s+findings")

    def test_controller_sections_and_transitions_are_ordered(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        positions = tuple(body.index(heading) for heading in REQUIRED_SECTIONS)
        self.assertEqual(positions, tuple(sorted(positions)))

        workflow = section(
            body,
            "## Default mode: review -> repair documents -> scoped re-review",
            "## Review-only mode",
        )
        self.assertRegex(
            workflow,
            re.compile(
                r"resolve plan -> resolve plan \*\*Spec:\*\* -> read binding references\s*"
                r"-> hash design and plan -> record HEAD and dirty state\s*"
                r"-> fresh read-only review -> controller deduplication\s*"
                r"-> authority-preserving document repair -> original closure review\s*"
                r"-> conditional bounded repair-impact regression -> optional second repair\s*"
                r"-> fresh original closure review \+ conditional bounded repair-impact regression\s*"
                r"-> READY \| REVISE \| BLOCKED"
            ),
        )

    def test_authority_and_risk_selection_are_ordered_and_conditional(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        inputs = section(body, "## Resolve authoritative inputs", "## Capture freshness")
        authority_items = tuple(re.findall(r"^\d+\. (.+)$", inputs, re.MULTILINE))
        self.assertEqual(authority_items, AUTHORITY_ORDER)

        reviewers = section(
            body,
            "## Select reviewers",
            "## Default mode: review -> repair documents -> scoped re-review",
        )
        self.assertEqual(second_review_risk_triggers(reviewers), RISK_TRIGGERS)

    def test_mutation_boundary_retains_every_exclusion(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        repair_rules = section(body, "## Repair rules", "## Verdict and handoff")
        normalized_repair_rules = re.sub(r"\s+", " ", repair_rules)
        self.assertIn("may edit only the resolved design specification", repair_rules)
        self.assertIn("resolved implementation plan", repair_rules)
        self.assertIn("The mutation allowlist excludes", repair_rules)
        self.assertIn("Any correction that changes approved product intent is forbidden", repair_rules)
        self.assertNotIn("proposed decision record", normalized_repair_rules)
        for protected_surface in MUTATION_EXCLUSIONS:
            self.assertIn(protected_surface, repair_rules)
            self.assertNotRegex(
                repair_rules,
                rf"may edit (?:the )?{re.escape(protected_surface)}",
            )

    def test_protocol_finding_schema_and_evidence_classes_are_complete(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(
            encoding="utf-8"
        )
        record = re.search(r"```text\n(.*?)\n```", protocol, re.DOTALL)
        self.assertIsNotNone(record)
        self.assertEqual(tuple(record.group(1).splitlines()), FINDING_RECORD)

    def test_protocol_allows_exactly_two_severities(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(
            encoding="utf-8"
        )
        severities = section(
            protocol,
            "Use only these severities:",
            "Use only these classes:",
        )
        self.assertEqual(
            tuple(re.findall(r"^- `([A-Z]+)`:", severities, re.MULTILINE)),
            FINDING_SEVERITIES,
        )

    def test_protocol_allows_exactly_five_finding_classes(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(
            encoding="utf-8"
        )
        classes = section(
            protocol,
            "Use only these classes:",
            "Return each material finding in this complete record:",
        )
        self.assertEqual(
            tuple(re.findall(r"`([a-z-]+)`", classes)),
            FINDING_CLASSES,
        )

    def test_protocol_falsification_keeps_evidence_classes_distinct(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            protocol,
            re.compile(
                r"static contract evidence, unit behavior\s+evidence, integration behavior evidence,\s+"
                r"browser/device behavior evidence,\s+and external-side-effect evidence"
            ),
        )

    def test_ready_handoff_keeps_freshness_and_explicit_sdd_boundary(self) -> None:
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        freshness = section(body, "## Capture freshness", "## Select reviewers")
        normalized_freshness = re.sub(r"\s+", " ", freshness)
        for field in (
            "repository-relative design and plan paths",
            "SHA-256 hashes",
            "Git `HEAD` (or `unborn`)",
            "worktree is clean or dirty",
            "review timestamp",
            "final verdict",
        ):
            self.assertIn(field, normalized_freshness)

        handoff = section(body, "## Verdict and handoff", "## Do not use this skill for")
        normalized_handoff = re.sub(r"\s+", " ", handoff)
        self.assertIn(
            "For `READY`, print the exact resolved design and plan paths",
            normalized_handoff,
        )
        self.assertIn("final fingerprints", normalized_handoff)
        self.assertIn(
            "Do not start SDD unless the outer request explicitly asks for implementation",
            normalized_handoff,
        )


class PreSddReviewDocumentationTests(unittest.TestCase):
    def test_bilingual_readmes_keep_the_required_order_and_symmetric_contract(self) -> None:
        korean = (SKILL / "README.md").read_text(encoding="utf-8")
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")

        self.assertTrue(korean.startswith("# Pre-SDD Review\n"))
        self.assertTrue(english.startswith("# Pre-SDD Review\n"))
        for text, headings in (
            (korean, KOREAN_README_HEADINGS),
            (english, ENGLISH_README_HEADINGS),
        ):
            positions = tuple(text.index(heading) for heading in headings)
            self.assertEqual(positions, tuple(sorted(positions)))
        for fact in KOREAN_FACTS:
            self.assertIn(fact, korean)
        for fact in ENGLISH_FACTS:
            self.assertIn(fact, english)

        for text in (korean, english):
            self.assertIn("**Spec:**", text)
        for fact in ("계획 경로", "해결된 설계 명세", "변경하지 않습니다", "SDD를 시작하지"):
            self.assertIn(fact, korean)
        normalized_english = re.sub(r"\s+", " ", english)
        for fact in (
            "plan path",
            "resolved design specification",
            "changes nothing",
            "does not start SDD",
        ):
            self.assertIn(fact, normalized_english)

    def test_bilingual_readmes_lock_primary_input_mutation_and_review_semantics(self) -> None:
        korean = (SKILL / "README.md").read_text(encoding="utf-8")
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        default_call = (
            "$pre-sdd-review docs/history/specs/<design>.md "
            "docs/history/plans/<plan>.md"
        )
        review_only_call = (
            "$pre-sdd-review review-only docs/history/specs/<design>.md "
            "docs/history/plans/<plan>.md"
        )
        for text in (korean, english):
            self.assertIn(default_call, text)
            self.assertIn(review_only_call, text)
            self.assertIn("**Spec:**", text)

        for text, purpose, first_call, expected, safety in (
            (
                korean,
                "계획 경로가 주 입력입니다.",
                "`review-only`는 명시 모드입니다.",
                "수정 패스는 최대 두 번입니다.",
                "문서 지문이",
            ),
            (
                english,
                "plan path is primary",
                "Use `review-only` only",
                "There are at most two repair passes.",
                "invalidates its fingerprints",
            ),
        ):
            positions = tuple(text.index(item) for item in (purpose, first_call, expected, safety))
            self.assertEqual(positions, tuple(sorted(positions)))
        for text, verdicts, risk in (
            (korean, ("`READY`:", "`REVISE`:", "`BLOCKED`:"), "두 번째 집중 검토자"),
            (english, ("`READY`:", "`REVISE`:", "`BLOCKED`:"), "focused second reviewer"),
        ):
            positions = tuple(text.index(item) for item in (*verdicts, risk))
            self.assertEqual(positions, tuple(sorted(positions)))

        self.assertNotIn("계획을 먼저 주고", korean)
        self.assertIn("계획 경로가 주 입력", korean)
        normalized_korean = re.sub(r"\s+", " ", korean)
        self.assertIn("`review-only`는 같은 검토를 하지만 아무 파일도 변경하지 않습니다.", normalized_korean)
        self.assertIn("`review-only` changes nothing", re.sub(r"\s+", " ", english))
        for text, allowlist in (
            (normalized_korean, "`editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`"),
            (re.sub(r"\s+", " ", english), "`editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`"),
        ):
            self.assertIn(allowlist, text)
            self.assertNotIn("proposed decision record", text)
            self.assertNotIn("directly referenced", text)

    def test_skill_and_readmes_close_the_default_mutation_allowlist_to_two_documents(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        contract = (MAINTAINERS / "contract.md").read_text(encoding="utf-8")
        repair_rules = section(skill, "## Repair rules", "## Verdict and handoff")
        normalized = re.sub(r"\s+", " ", repair_rules)
        self.assertIn("may edit only the resolved design specification", normalized)
        for editable_document in MUTATION_ALLOWLIST:
            self.assertIn(editable_document, normalized)
        self.assertNotIn("proposed decision record", normalized)
        self.assertNotIn("directly referenced", normalized)
        self.assertEqual(numbered_items(subsection(contract, "### Editable paths")), MUTATION_ALLOWLIST)
        self.assertEqual(backtick_list(subsection(contract, "### Excluded surfaces")), MUTATION_EXCLUSIONS)

    def test_maintainer_contract_owns_the_complete_runtime_boundary(self) -> None:
        contract = (MAINTAINERS / "contract.md").read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", contract)
        authority = section(contract, "## Authority order", "## Reviewer isolation")
        self.assertEqual(
            tuple(re.findall(r"^\d+\. (.+)$", authority, re.MULTILINE)),
            AUTHORITY_ORDER,
        )
        passes = section(contract, "## Review passes and findings", "## Default flow")
        self.assertEqual(
            tuple(re.findall(r"^\d+\. (.+?)[;.]+$", passes, re.MULTILINE)),
            (
                "authority trace",
                "repository grounding",
                "cross-artifact consistency",
                "verification falsification",
                "readiness verdict",
            ),
        )
        self.assertEqual(
            tuple(re.findall(r"`([A-Z]+)`", passes.split("Use only five finding")[0])),
            FINDING_SEVERITIES,
        )
        self.assertEqual(
            tuple(re.findall(r"`([a-z-]+)`", passes.split("A finding")[0])),
            FINDING_CLASSES,
        )
        for trigger in RISK_TRIGGERS:
            self.assertIn(trigger, normalized)
        for fact in (
            "read-only",
            "five passes",
            "SHA-256",
            "Git `HEAD`",
            "worktree",
            "review timestamp",
        ):
            self.assertIn(fact, contract)
        self.assertIn(
            "Do not start SDD unless the outer request explicitly asks for implementation",
            normalized,
        )
        verdicts = subsection(contract, "### Verdicts")
        freshness = subsection(contract, "### Freshness")
        for fact in (
            "`READY`: no unresolved finding requires invention",
            "`REVISE`: a repairable material document defect",
            "`BLOCKED`: required input, authority, or repository evidence is unavailable",
        ):
            self.assertIn(fact, verdicts)
        self.assertIn("Any content change to either resolved document invalidates `READY`", freshness)

    def test_maintainer_testing_compatibility_and_release_stay_role_specific(self) -> None:
        testing = (MAINTAINERS / "testing.md").read_text(encoding="utf-8")
        compatibility = (MAINTAINERS / "compatibility.md").read_text(encoding="utf-8")
        release = (MAINTAINERS / "release.md").read_text(encoding="utf-8")
        normalized_testing = re.sub(r"\s+", " ", testing)

        for fact in (
            "PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover",
            "provider-free",
            "exactly fifteen",
            "`ready`, `missing-coverage`, `false-verification`, `runtime-removal`,",
            "`runtime-removal`",
            "`design.md`, `plan.md`,",
            "`repository.json`, and `expected.json`",
            "optional",
            "fresh Codex session",
            "non-sensitive synthetic design and plan",
            "record only host, client version, date, case identifier, and verdict",
            "billable",
            "CI never",
            "user documents",
            "full model responses",
        ):
            self.assertIn(fact, normalized_testing)
        self.assertIn("Codex is supported", compatibility)
        self.assertIn("Every other host is `not_measured`", compatibility)
        normalized_release = re.sub(r"\s+", " ", release).lower()
        for fact in (
            "version source is `skills/pre-sdd-review/release.toml`",
            "python3 scripts/release.py check --product pre-sdd-review",
            "python3 scripts/release.py build --product pre-sdd-review",
            "python3 scripts/release.py verify-download --product pre-sdd-review",
        ):
            self.assertIn(fact, release)
        self.assertIn("no tag or github release is created by these commands.", normalized_release)

    def test_changelog_records_the_first_independent_release_without_publication_claim(self) -> None:
        changelog = (SKILL / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("## 1.0.0 - 2026-08-29", changelog)
        self.assertIn("first independent product release contract", changelog)
        self.assertIn("does not claim", changelog)

    def test_readme_contract_is_bounded_symmetric_and_has_one_first_call(self) -> None:
        korean = (SKILL / "README.md").read_text(encoding="utf-8")
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        self.assertEqual(readme_contract_errors(korean), ())
        self.assertEqual(readme_contract_errors(english), ())
        self.assertEqual(parse_readme_contract(korean), parse_readme_contract(english))

    def test_readme_validator_rejects_wrong_command_asymmetry_and_third_surface(self) -> None:
        korean = (SKILL / "README.md").read_text(encoding="utf-8")
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        self.assertEqual(readme_contract_errors(korean), ())
        self.assertEqual(readme_contract_errors(english), ())
        wrong_command = english.replace(DEFAULT_FIRST_CALL, "$pre-sdd-review docs/other.md docs/plan.md")
        self.assertIn("first call must contain only the approved invocation", readme_contract_errors(wrong_command))
        asymmetric = korean.replace("`at-most-two`", "`at-most-three`")
        self.assertIn("bounded README contract differs from the product contract", readme_contract_errors(asymmetric))
        third_surface = english.replace(
            "`resolved-implementation-plan`",
            "`resolved-implementation-plan`, `proposed-decision-record`",
        )
        self.assertIn("bounded README contract differs from the product contract", readme_contract_errors(third_surface))
        indented_command = english.replace(
            DEFAULT_FIRST_CALL,
            f"{DEFAULT_FIRST_CALL}\n  $pre-sdd-review docs/extra.md docs/extra-plan.md",
        )
        self.assertIn("first call must contain only the approved invocation", readme_contract_errors(indented_command))
        extra_prose = english + "\nThe controller may also edit release notes.\n"
        self.assertIn(
            "README sensitive sections differ from the canonical contract",
            readme_contract_errors(extra_prose),
        )
        missing_heading = english.replace("## First call", "## Invocation")
        self.assertIn("missing First call section", readme_contract_errors(missing_heading))

    def test_readme_validator_rejects_every_round_four_semantic_bypass(self) -> None:
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        mutations = (
            english + "\nThe controller is authorized to revise release notes.\n",
            english.replace(
                "The plan path is primary.",
                "The design path is primary.",
            ),
            english.replace(
                "`review-only` changes nothing",
                "`review-only` may update the plan",
            ),
            english.replace(
                "There are at most two repair passes.",
                "There are three repair passes.",
            ),
            english.replace("## First call", "## Invocation").replace(
                "```text\n$skill-installer",
                "```text\n## First call\n$skill-installer",
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertIn(
                    "README sensitive sections differ from the canonical contract",
                    readme_contract_errors(mutation),
                )

    def test_readme_validator_rejects_round_five_preamble_authority(self) -> None:
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        anchor = "[한국어](README.md)\n"
        mutations = (
            english.replace(
                anchor,
                anchor + "\nThe design path, not the plan path, is primary.\n",
                1,
            ),
            english.replace(
                anchor,
                anchor + "\nThe controller is authorized to edit release notes.\n",
                1,
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertIn(
                    "README differs from the closed canonical document",
                    readme_contract_errors(mutation),
                )

    def test_whole_document_digest_rejects_indented_readme_h1(self) -> None:
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        indented_h1 = english.replace(
            "# Pre-SDD Review\n",
            "    # Pre-SDD Review\n",
            1,
        )
        self.assertIn(
            "README differs from the closed canonical document",
            readme_contract_errors(indented_h1),
        )

    def test_whole_document_digest_rejects_indented_release_fence(self) -> None:
        release = (MAINTAINERS / "release.md").read_text(encoding="utf-8")
        indented_fence = release.replace("```bash\n", "    ```bash\n", 1)
        self.assertIn(
            "release document differs from the closed canonical contract",
            release_document_errors(indented_fence),
        )

    def test_maintainer_contract_uses_bounded_exact_protocols(self) -> None:
        contract = (MAINTAINERS / "contract.md").read_text(encoding="utf-8")
        self.assertEqual(maintainer_contract_errors(contract), ())

    def test_maintainer_validator_rejects_routine_second_review_stale_ready_and_third_path(self) -> None:
        contract = (MAINTAINERS / "contract.md").read_text(encoding="utf-8")
        self.assertEqual(maintainer_contract_errors(contract), ())
        routine = contract.replace("conditional only", "routine")
        self.assertIn("risk triggers must be conditional and exact", maintainer_contract_errors(routine))
        stale_ready = contract.replace(
            "Any content change to either resolved document invalidates `READY`",
            "A content change preserves `READY`",
        )
        self.assertIn("freshness contract differs", maintainer_contract_errors(stale_ready))
        third_path = contract.replace(
            "2. resolved implementation plan.",
            "2. resolved implementation plan.\n3. proposed decision record.",
        )
        self.assertIn("editable paths differ", maintainer_contract_errors(third_path))
        for contradiction in (
            "The controller may edit application code.",
            "A second reviewer is routine.",
            "READY survives a content change.",
            "Automatically start SDD after READY.",
        ):
            self.assertIn(
                "maintainer contract differs from the closed canonical contract",
                maintainer_contract_errors(contract + f"\n## Contradiction\n\n{contradiction}\n"),
            )

    def test_maintainer_validator_rejects_extra_prose_inside_owned_subsections(self) -> None:
        contract = (MAINTAINERS / "contract.md").read_text(encoding="utf-8")
        mutations = (
            contract.replace(
                "5. Current repository reality.\n",
                "5. Current repository reality.\n\n"
                "The implementation plan overrides the approved design.\n",
            ),
            contract.replace(
                "2. resolved implementation plan.\n",
                "2. resolved implementation plan.\n\n"
                "The controller is authorized to revise release notes.\n",
            ),
            contract.replace(
                "A second reviewer is conditional only, never routine.\n",
                "A second reviewer is conditional only, never routine.\n\n"
                "A second reviewer is routine for every change.\n",
            ),
            contract.replace(
                "- Any content change to either resolved document invalidates `READY`.\n",
                "- Any content change to either resolved document invalidates `READY`.\n\n"
                "A prose-only content change preserves `READY`.\n",
            ),
            contract.replace(
                "Do not start SDD unless the outer request explicitly asks for implementation.\n",
                "Do not start SDD unless the outer request explicitly asks for implementation.\n\n"
                "Start SDD immediately after `READY`.\n",
            ),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertIn(
                    "maintainer contract differs from the closed canonical contract",
                    maintainer_contract_errors(mutation),
                )

    def test_testing_compatibility_and_release_documents_are_derived_from_sources(self) -> None:
        testing = (MAINTAINERS / "testing.md").read_text(encoding="utf-8")
        compatibility = (MAINTAINERS / "compatibility.md").read_text(encoding="utf-8")
        release = (MAINTAINERS / "release.md").read_text(encoding="utf-8")
        self.assertEqual(testing_document_errors(testing), ())
        self.assertEqual(compatibility_document_errors(compatibility), ())
        self.assertEqual(release_document_errors(release), ())

    def test_testing_and_compatibility_reject_append_only_document_drift(self) -> None:
        testing = (MAINTAINERS / "testing.md").read_text(encoding="utf-8")
        compatibility = (MAINTAINERS / "compatibility.md").read_text(encoding="utf-8")
        testing_mutation = testing + "\n## Drift\n\nProvider-free fixtures prove live review quality.\n"
        compatibility_mutation = compatibility + "\n## Drift\n\nEvery host is supported.\n"
        self.assertIn(
            "testing document differs from the closed canonical contract",
            testing_document_errors(testing_mutation),
        )
        self.assertIn(
            "compatibility document differs from the closed canonical contract",
            compatibility_document_errors(compatibility_mutation),
        )

    def test_truth_validators_reject_inventory_host_and_publication_mutations(self) -> None:
        testing = (MAINTAINERS / "testing.md").read_text(encoding="utf-8")
        compatibility = (MAINTAINERS / "compatibility.md").read_text(encoding="utf-8")
        release = (MAINTAINERS / "release.md").read_text(encoding="utf-8")
        missing_case = testing.replace("- `default-auto-improve`\n", "", 1)
        self.assertIn("case inventory differs", testing_document_errors(missing_case))
        changed_host = compatibility.replace("| `codex` | `supported` |", "| `codex` | `not_measured` |")
        self.assertIn("host matrix differs from products.toml", compatibility_document_errors(changed_host))
        for publication in (
            release + "\n```sh\ngit push origin pre-sdd-review-v1.0.0\n```\n",
            release + "\n```bash\nenv git push origin pre-sdd-review-v1.0.0\n```\n",
            release + "\n```text\ntrue && git tag pre-sdd-review-v1.0.0\n```\n",
            release + "\n```sh\ngit -C . push origin pre-sdd-review-v1.0.0\n```\n",
            release
            + "\n```sh\npublisher=git\nverb=push\n"
            '"$publisher" "$verb" origin pre-sdd-review-v1.0.0\n```\n',
            release + "\n```sh\npython3 -m twine upload dist/*\n```\n",
            release + "\n```sh\nuv publish dist/*\n```\n",
        ):
            self.assertIn(
                "release document differs from the closed canonical contract",
                release_document_errors(publication),
            )

        comment_only = release + "\n```sh\n# Do not run git push from this procedure.\n```\n"
        self.assertIn(
            "release document differs from the closed canonical contract",
            release_document_errors(comment_only),
        )
        self.assertNotIn(
            "release document contains a publication instruction",
            release_document_errors(comment_only),
        )

    def test_release_validator_rejects_round_five_command_drift_without_guessing(self) -> None:
        release = (MAINTAINERS / "release.md").read_text(encoding="utf-8")
        mutations = (
            release + "\n~~~sh\ngit push origin pre-sdd-review-v1.0.0\n~~~\n",
            release + "\n    git push origin pre-sdd-review-v1.0.0\n",
            release + "\n```sh\nbash scripts/publish-release.sh\n```\n",
            release
            + "\n```sh\nprintf '%s' 'Z2l0IHB1c2g=' | base64 --decode | sh\n```\n",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertIn(
                    "release document differs from the closed canonical contract",
                    release_document_errors(mutation),
                )

        safe_data = release + "\n```sh\nprintf '%s\\n' 'git push is prohibited'\n```\n"
        self.assertIn(
            "release document differs from the closed canonical contract",
            release_document_errors(safe_data),
        )
        self.assertNotIn(
            "release document contains a publication instruction",
            release_document_errors(safe_data),
        )


class PreSddReviewFixtureTests(unittest.TestCase):
    def test_ready_plan_rejects_the_constant_hello_counterexample(self) -> None:
        plan = (FIXTURES / "ready/plan.md").read_text(encoding="utf-8")
        acceptance_pairs = tuple(
            re.findall(
                r'calls `renderMessage\("([^"]+)"\)`\s+'
                r'and verifies that it returns `"([^"]+)"`',
                plan,
            )
        )
        self.assertEqual(
            acceptance_pairs,
            (("hello", "hello"), ("bye", "bye")),
        )

        def constant_hello(_input: str) -> str:
            return "hello"

        self.assertTrue(
            any(constant_hello(input_value) != expected for input_value, expected in acceptance_pairs),
            "the ready fixture still accepts a constant-return implementation",
        )

    def test_each_fixture_plan_has_one_resolvable_design_spec(self) -> None:
        for name in FIXTURE_NAMES:
            with self.subTest(fixture=name):
                fixture = FIXTURES / name
                plan = (fixture / "plan.md").read_text(encoding="utf-8")
                spec_values = tuple(
                    match.strip()
                    for match in re.findall(r"^\*\*Spec:\*\*\s+(.+)$", plan, re.MULTILINE)
                )
                self.assertEqual(spec_values, ("design.md",))
                resolved = (fixture / spec_values[0]).resolve()
                self.assertEqual(resolved, (fixture / "design.md").resolve())
                self.assertTrue(resolved.is_file())

    def test_case_matrix_has_exact_schema_and_activation_boundaries(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(tuple(case["id"] for case in data["cases"]), CASE_IDS)
        self.assertTrue(
            all(set(case) == {"id", "request", "expect"} for case in data["cases"])
        )
        self.assertEqual(
            data["cases"][0]["expect"],
            ["review", "repair", "re-review", "fingerprints"],
        )
        self.assertEqual(
            data["cases"][1]["expect"],
            ["read_only", "single_verdict"],
        )
        near_misses = [
            case for case in data["cases"] if case["id"].startswith("near-miss-")
        ]
        self.assertTrue(near_misses)
        self.assertTrue(
            all(case["expect"] == ["not_activated"] for case in near_misses)
        )

    def test_fixture_tree_and_repository_manifests_are_exact(self) -> None:
        self.assertEqual(
            tuple(sorted(path.name for path in FIXTURES.iterdir())),
            tuple(sorted(FIXTURE_NAMES)),
        )
        for name in FIXTURE_NAMES:
            fixture = FIXTURES / name
            self.assertTrue(fixture.is_dir())
            self.assertEqual(
                tuple(sorted(path.name for path in fixture.iterdir())),
                tuple(sorted(FIXTURE_FILES)),
            )
            self.assertTrue(all(path.is_file() for path in fixture.iterdir()))
            manifest = json.loads(
                (fixture / "repository.json").read_text(encoding="utf-8")
            )
            expected_manifest = dict(REPOSITORY_MANIFEST)
            if name == "repair-induced-schema-consumer":
                expected_manifest["typedConsumers"] = [
                    {
                        "path": "tests/app.test.ts",
                        "type": "PublicMessageRecord",
                        "shape": "missing required displayName",
                    }
                ]
            self.assertEqual(manifest, expected_manifest)

    def test_fixture_content_is_the_bounded_review_contract(self) -> None:
        for name, expected_files in FIXTURE_CONTENTS.items():
            for filename, expected_content in expected_files.items():
                self.assertEqual(
                    (FIXTURES / name / filename).read_text(encoding="utf-8"),
                    expected_content,
                )

    def test_ready_and_runtime_expected_metadata_are_exact(self) -> None:
        ready = json.loads(
            (FIXTURES / "ready/expected.json").read_text(encoding="utf-8")
        )
        self.assertEqual(ready, {"verdict": "READY", "findings": []})
        runtime = json.loads(
            (FIXTURES / "runtime-removal/expected.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            runtime,
            {
                "risk_reviewer_required": True,
                "risk_trigger": "framework-or-runtime-removal",
            },
        )

    def test_v1_1_regression_fixtures_have_a_scorable_material_consequence(self) -> None:
        for name, expected_digest in V1_1_FIXTURE_SHA256.items():
            with self.subTest(name=name):
                digest = hashlib.sha256()
                for path in sorted((FIXTURES / name).iterdir()):
                    digest.update(path.name.encode("utf-8"))
                    digest.update(b"\0")
                    digest.update(path.read_bytes())
                self.assertEqual(digest.hexdigest(), expected_digest)
                expected = json.loads(
                    (FIXTURES / name / "expected.json").read_text(encoding="utf-8")
                )
                self.assertEqual(expected["verdict"], "REVISE")
                self.assertEqual(len(expected["findings"]), 1)
                finding = expected["findings"][0]
                self.assertTrue(finding["evidence"])
                self.assertTrue(finding["consequence"])
        schema_repository = json.loads(
            (FIXTURES / "repair-induced-schema-consumer/repository.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            schema_repository["typedConsumers"],
            [
                {
                    "path": "tests/app.test.ts",
                    "type": "PublicMessageRecord",
                    "shape": "missing required displayName",
                }
            ],
        )

    def test_fixtures_contain_no_private_or_model_response_payload(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for name in FIXTURE_NAMES
            for path in (FIXTURES / name).iterdir()
        )
        for forbidden in (
            "/Users/",
            "source/private",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            '"model_response"',
            '"transcript"',
        ):
            self.assertNotIn(forbidden, text)
