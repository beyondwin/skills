from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter  # noqa: E402

SKILL_ROOT = REPOSITORY_ROOT / "skills" / "image-workbench"


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
        frontmatter = parse_skill_frontmatter(
            (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        )
        description = str(frontmatter.get("description", ""))
        self.assertTrue(description)
        self.assertEqual(trigger_only_errors(description), [])
        summarized = description + " Inspect the project and compile an ImageSpec."
        self.assertTrue(trigger_only_errors(summarized))
        self.assertTrue(trigger_only_errors("Plans raster images. " + description))


if __name__ == "__main__":
    unittest.main()
