from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter  # noqa: E402


SKILL = ROOT / "skills" / "pre-sdd-review"
CASES = ROOT / "tests" / "products" / "pre-sdd-review" / "cases.json"
FIXTURES = ROOT / "tests" / "products" / "pre-sdd-review" / "fixtures"
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
    "near-miss-write-spec",
    "near-miss-write-plan",
    "near-miss-code-review",
    "near-miss-release-review",
)
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
FINDING_RECORD = (
    "ID: PSDR-001",
    "Severity: BLOCKER | IMPORTANT",
    "Class: authority-drift | repo-reality | coverage | ordering | verification-gap",
    "Location: exact document path and heading or line",
    "Evidence: repository or cross-document fact",
    "Consequence: concrete implementation failure",
    "Minimal document fix: smallest authority-preserving correction",
)


def section(text: str, start: str, end: str) -> str:
    return text[text.index(start) : text.index(end, text.index(start) + len(start))]


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
                r"-> authority-preserving document repair -> scoped re-review\s*"
                r"-> optional second repair -> fresh scoped re-review\s*"
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
        self.assertIn("may edit only the resolved design specification", repair_rules)
        self.assertIn("resolved implementation plan", repair_rules)
        self.assertIn("The mutation allowlist excludes", repair_rules)
        self.assertIn("Any correction that changes approved product intent is forbidden", repair_rules)
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


class PreSddReviewFixtureTests(unittest.TestCase):
    def test_case_ids_and_near_misses_are_exact(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(tuple(case["id"] for case in data["cases"]), CASE_IDS)
        near_misses = [
            case for case in data["cases"] if case["id"].startswith("near-miss-")
        ]
        self.assertTrue(near_misses)
        self.assertTrue(
            all(case["expect"] == ["not_activated"] for case in near_misses)
        )

    def test_ready_fixture_allows_zero_findings(self) -> None:
        expected = json.loads(
            (FIXTURES / "ready/expected.json").read_text(encoding="utf-8")
        )
        self.assertEqual(expected, {"verdict": "READY", "findings": []})

    def test_runtime_removal_requires_focused_second_reviewer(self) -> None:
        expected = json.loads(
            (FIXTURES / "runtime-removal/expected.json").read_text(encoding="utf-8")
        )
        self.assertEqual(expected["risk_reviewer_required"], True)
        self.assertEqual(expected["risk_trigger"], "framework-or-runtime-removal")

    def test_fixtures_contain_no_personal_paths_or_credentials(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8") for path in FIXTURES.rglob("*.*")
        )
        for forbidden in (
            "/Users/",
            "source/private",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ):
            self.assertNotIn(forbidden, text)
