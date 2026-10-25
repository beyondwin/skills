from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter  # noqa: E402

SKILL = REPOSITORY_ROOT / "skills" / "grok-image" / "SKILL.md"


def trigger_only_errors(description: str) -> list[str]:
    errors: list[str] = []
    if not description.startswith(("Use when", "Use only when")):
        errors.append("description does not start with 'Use when' or 'Use only when'")
    for sentence in re.split(r"(?<=[.!?])\s+", description.strip()):
        if not sentence.startswith(("Use ", "Do not use ")):
            errors.append(f"sentence is not a trigger: {sentence}")
    return errors


class ContractTests(unittest.TestCase):
    def test_description_is_trigger_only(self) -> None:
        frontmatter = parse_skill_frontmatter(SKILL.read_text(encoding="utf-8"))
        description = str(frontmatter.get("description", ""))
        self.assertEqual(trigger_only_errors(description), [])
        self.assertIn("image-workbench", description)
        self.assertIn("video", description)

    def test_prompt_shape_and_ask_gate(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        for phrase in (
            "what it is, its form, what holds it",
            "Ask one question and do not generate",
            "a depictable subject",
            "named real person",
            "Do not add a quality stack",
            "full original prompt plus that one fix",
            "image_gen",
            "image_edit",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
