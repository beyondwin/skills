from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter  # noqa: E402

SKILL = ROOT / "skills" / "kws-api-guide"
SKILL_TEXT = (SKILL / "SKILL.md").read_text(encoding="utf-8")
PAGE_TEXT = (SKILL / "references" / "page.html").read_text(encoding="utf-8")

SKELETON = (
    "Header",
    "To-do",
    "Common rules",
    "API cards",
    "Flows",
    "Shared caller rules",
    "Appendix",
)
CARD_ORDER = ("Request", "Response", "Errors", "Handling")
PAGE_SECTIONS = ('id="todo"', 'id="common"', 'id="api-list"', 'id="flow"', 'id="refs"')
REFERENCES = (
    "references/facts.md",
    "references/consumer.md",
    "references/page.html",
    "references/writing.md",
)
COMMON_TABLES = ("Handle in code", "Formats")
VERIFY_RULES = (
    "search for a counterexample",
    "same rule in both",
    "agree with the field tables",
    "throw sites",
    "names its default",
    "labeled composed",
)
TEMPLATE_PATHS = {"/api/v1", "/api/v1/exports"}


def section(text: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    if match is None:
        raise AssertionError(f"missing {heading}")
    return match.group(1)


class FrontmatterTest(unittest.TestCase):
    def test_explicit_only_and_description_shape(self) -> None:
        data = parse_skill_frontmatter(SKILL_TEXT)
        self.assertEqual(data["name"], "kws-api-guide")
        self.assertEqual(data["disable-model-invocation"], "true")
        description = str(data["description"])
        self.assertTrue(description.startswith("Use when explicitly invoked"))
        self.assertIn("Do not use for", description)
        self.assertIn("how-it-works", description)
        self.assertIn("Artifact tool", str(data["compatibility"]))


class SkillBodyTest(unittest.TestCase):
    def test_references_exist_and_are_named(self) -> None:
        for reference in REFERENCES:
            self.assertTrue((SKILL / reference).is_file(), reference)
            self.assertIn(f"`{reference}`", SKILL_TEXT, reference)

    def test_skeleton_order(self) -> None:
        body = section(SKILL_TEXT, "## Page skeleton")
        positions = [body.find(f"{index}. {name}") for index, name in enumerate(SKELETON, 1)]
        self.assertNotIn(-1, positions, positions)
        self.assertEqual(positions, sorted(positions))

    def test_card_order_is_stated(self) -> None:
        body = section(SKILL_TEXT, "## Page skeleton")
        positions = [body.find(name) for name in CARD_ORDER]
        self.assertNotIn(-1, positions)
        self.assertEqual(positions, sorted(positions))

    def test_common_rules_split_in_order(self) -> None:
        body = section(SKILL_TEXT, "## Page skeleton")
        positions = [body.find(f"{name}:") for name in COMMON_TABLES]
        self.assertNotIn(-1, positions, positions)
        self.assertEqual(positions, sorted(positions))

    def test_writing_rules_cover_measured_patterns(self) -> None:
        writing = " ".join((SKILL / "references" / "writing.md").read_text(encoding="utf-8").split())
        for rule in ("at most two short sentences", "At most one parenthetical", "One register"):
            self.assertIn(rule, writing)
        verify = " ".join(section(SKILL_TEXT, "## Verify").split())
        self.assertIn("reread the page once against `references/writing.md`", verify)

    def test_language_follows_invocation(self) -> None:
        self.assertIn("| language | the language of the invocation text", SKILL_TEXT)
        self.assertIn("In the language of the invocation text", section(SKILL_TEXT, "## Report"))

    def test_verify_rules_present(self) -> None:
        body = " ".join(section(SKILL_TEXT, "## Verify").split())
        for rule in VERIFY_RULES:
            self.assertIn(rule, body)

    def test_consumer_advice_stays_behavior_level(self) -> None:
        consumer = (SKILL / "references" / "consumer.md").read_text(encoding="utf-8")
        consumer = " ".join(consumer.split())
        self.assertIn("Do not put consumer file paths, line numbers, or class names on the page", consumer)


class TemplateTest(unittest.TestCase):
    def test_sections_in_skeleton_order(self) -> None:
        positions = [PAGE_TEXT.find(marker) for marker in PAGE_SECTIONS]
        self.assertNotIn(-1, positions, positions)
        self.assertEqual(positions, sorted(positions))

    def test_common_rules_has_two_tables(self) -> None:
        common = PAGE_TEXT[PAGE_TEXT.find('id="common"'):PAGE_TEXT.find('id="api-list"')]
        headings = re.findall(r"<h3>([^<]+)</h3>", common)
        self.assertEqual(tuple(headings), COMMON_TABLES)

    def test_card_blocks_in_order(self) -> None:
        card = PAGE_TEXT[PAGE_TEXT.find('id="api-list"'):PAGE_TEXT.find('id="api-create"')]
        labels = re.findall(r'<span class="lab(?: err)?">([^<]+)</span>', card)
        self.assertEqual(tuple(labels), CARD_ORDER)

    def test_theme_tokens_cover_dark_mode(self) -> None:
        self.assertIn('@media (prefers-color-scheme: dark)', PAGE_TEXT)
        self.assertIn(':root:not([data-theme="light"])', PAGE_TEXT)
        self.assertIn(':root[data-theme="dark"]', PAGE_TEXT)

    def test_template_uses_only_invented_api(self) -> None:
        paths = set(re.findall(r"/api/[A-Za-z0-9/_{}-]*", PAGE_TEXT))
        self.assertEqual(paths, TEMPLATE_PATHS)
        self.assertNotIn("<script", PAGE_TEXT)


if __name__ == "__main__":
    unittest.main()
