"""Phrase-level contract checks for waygent.

SKILL.md is still being edited, so these checks pin a few load-bearing
phrases and the line ceiling, not wording or a digest.
"""

from __future__ import annotations

import sys
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import (  # noqa: E402
    parse_skill_frontmatter,
    validate_product,
)
from scripts.lib.product_registry import load_registry  # noqa: E402

SKILL = ROOT / "skills" / "waygent"
MAX_SKILL_LINES = 140


def _fold(text: str) -> str:
    return " ".join(text.split())


class WaygentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cls.text = _fold(cls.raw)
        cls.lowered = cls.text.lower()
        cls.frontmatter = parse_skill_frontmatter(cls.raw)
        cls.release = tomllib.loads((SKILL / "release.toml").read_text(encoding="utf-8"))

    def test_product_validates(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(validate_product(SKILL, registry), [])

    def test_frontmatter_matches_release(self) -> None:
        self.assertEqual(self.frontmatter.get("name"), self.release["name"])
        self.assertEqual(self.frontmatter.get("license"), self.release["license"])
        metadata = self.frontmatter.get("metadata")
        self.assertIsInstance(metadata, dict)
        self.assertEqual(metadata.get("version"), self.release["version"])

    def test_description_gates_on_slash_command_and_names_near_misses(self) -> None:
        description = str(self.frontmatter.get("description", ""))
        lowered = description.lower()
        self.assertIn("/waygent", description)
        self.assertIn("/sddx", description)
        self.assertIn("subagent-driven-development", lowered)
        self.assertIn("brainstorming", lowered)
        self.assertIn("spec", lowered)
        self.assertIn("single small fix", lowered)

    def test_progress_and_resume_contract(self) -> None:
        self.assertIn(".waygent/<plan-slug>/", self.text)
        self.assertIn("`.waygent/.gitignore`", self.text)
        self.assertIn("single line `*`", self.text)
        self.assertIn("Waygent-Task:", self.text)

    def test_review_contract(self) -> None:
        self.assertIn("no re-review", self.lowered)
        self.assertIn("final review, once", self.lowered)

    def test_final_review_and_check_contract(self) -> None:
        self.assertIn("contract drift between layers", self.lowered)
        self.assertIn("failure paths", self.lowered)
        self.assertIn("config needed at startup", self.lowered)
        self.assertIn("real data, not fixtures", self.lowered)
        self.assertIn("fast check", self.lowered)
        self.assertIn("say so in every brief, reviewers' included", self.lowered)
        self.assertIn("only the task's last one carries the trailer", self.lowered)
        self.assertIn("starting or deploying", self.lowered)
        self.assertIn("is never outside the task", self.lowered)
        self.assertIn("stops what it started", self.lowered)

    def test_branch_and_model_contract(self) -> None:
        self.assertIn("never commit to `main` or `master`", self.lowered)
        self.assertIn("same model", self.lowered)
        self.assertIn("cheaper model", self.lowered)
        self.assertIn("one tier up", self.lowered)
        self.assertIn("the final reviewer, and the retry after a failure", self.lowered)

    def test_codex_contract(self) -> None:
        description = str(self.frontmatter.get("description", ""))
        self.assertIn("$waygent", description)
        self.assertIn('`fork_turns: "none"`', self.text)
        self.assertIn("do not guess your model name", self.lowered)
        self.assertIn("no subagent spawns subagents of its own", self.lowered)

    def test_grok_contract(self) -> None:
        # The controller must wait for each child and let it inherit the model.
        self.assertIn("`spawn_subagent` with `run_in_background: false`, no `model`", self.text)
        registry = load_registry(ROOT / "products.toml")
        product = next(p for p in registry.products if p.name == "waygent")
        self.assertIn("grok", product.supported_hosts)

    def test_skill_stays_light(self) -> None:
        self.assertLess(len(self.raw.splitlines()), MAX_SKILL_LINES)


if __name__ == "__main__":
    unittest.main()
