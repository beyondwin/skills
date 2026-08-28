from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "skills" / "how-it-works"
CASES = ROOT / "tests" / "products" / "how-it-works" / "cases.json"


class HowItWorksPayloadTests(unittest.TestCase):
    def test_name_matches_directory(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: how-it-works\n", text.split("---")[1])
        self.assertEqual(SKILL.name, "how-it-works")

    def test_description_excludes_eli5_and_workflow(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        fm = text.split("---", 2)[1]
        self.assertNotIn("eli5", fm.lower())
        self.assertNotIn("바로 / 하나", fm)
        self.assertIn("Use when", fm)
        self.assertIn("/how-it-works", fm)

    def test_payload_files_exist(self) -> None:
        for rel in (
            "SKILL.md",
            "LICENSE.txt",
            "agents/openai.yaml",
            "references/output.md",
            "references/visuals.md",
            "references/korean.md",
            "references/stakes.md",
            "references/sources.md",
        ):
            self.assertTrue((SKILL / rel).is_file(), rel)

    def test_payload_excludes_eval_and_html_templates(self) -> None:
        names = {p.name for p in SKILL.rglob("*") if p.is_file()}
        self.assertNotIn("test_contract.py", names)
        self.assertNotIn("cases.json", names)
        joined = "\n".join(
            p.read_text(encoding="utf-8") for p in SKILL.rglob("*.md")
        )
        self.assertNotIn("<html", joined.lower())

    def test_cases_file_parses(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        ids = [c["id"] for c in data["cases"]]
        self.assertEqual(
            ids,
            ["gate-dump-01", "html-01", "type-cmp-01", "scope-01", "ko-gloss-01"],
        )


if __name__ == "__main__":
    unittest.main()
