from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "grok-video" / "SKILL.md"
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---", re.DOTALL)


def _frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    data: dict[str, str] = {}
    if not match:
        return data
    for line in match.group(1).splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


class GrokVideoContractTests(unittest.TestCase):
    def test_description_is_trigger_only(self) -> None:
        description = _frontmatter(SKILL.read_text(encoding="utf-8"))["description"]
        self.assertTrue(description.startswith("Use when"))
        self.assertIn("Do not use", description)
        self.assertIn("image-workbench", description)
        self.assertNotIn("Locked camera", description)
        self.assertLessEqual(len(description), 280)

    def test_body_follows_the_planner_and_the_measured_pins(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        for phrase in (
            "scripts/plan_shot.py",
            "status` is `ask`",
            "first_frame",
            "last_frame",
            "pose or size",
            "reference_to_video",
            "image_gen",
            "moderation block",
            "middle keyframe",
        ):
            self.assertIn(phrase, text, phrase)


if __name__ == "__main__":
    unittest.main()
