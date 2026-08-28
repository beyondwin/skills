from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter  # noqa: E402

SKILL = ROOT / "skills" / "how-it-works"
CASES = ROOT / "tests" / "products" / "how-it-works" / "cases.json"
PORTABLE_FIELDS = {"name", "description", "license", "compatibility", "metadata"}


class HowItWorksPayloadTests(unittest.TestCase):
    def test_frontmatter_uses_portable_intersection(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(set(frontmatter), PORTABLE_FIELDS)
        self.assertEqual(frontmatter["name"], "how-it-works")
        self.assertEqual(frontmatter["license"], "Apache-2.0")
        self.assertEqual(frontmatter["metadata"]["version"], "1.0.0")

    def test_frontmatter_has_no_host_tool_requirement(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        compatibility = str(frontmatter["compatibility"]).lower()
        for forbidden in ("artifact", "canvas", "browser", "imagegen", "artifact-design"):
            self.assertNotIn(forbidden, compatibility)

    def test_documentation_includes_four_host_invocations(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        body = text.split("---", 2)[-1]
        self.assertIn("$how-it-works", body)
        self.assertIn("/how-it-works", body)
        self.assertIn("@how-it-works", body)
        self.assertIn("Codex", body)
        self.assertIn("Claude Code", body)
        self.assertIn("Grok", body)
        self.assertIn("Cursor", body)

    def test_release_smoke_accepts_portable_frontmatter(self) -> None:
        from scripts.release import _smoke_how_it_works

        self.assertEqual(_smoke_how_it_works(SKILL), [])

    def test_runtime_does_not_require_openai_yaml(self) -> None:
        runtime_paths = [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]
        runtime = "\n".join(path.read_text(encoding="utf-8") for path in runtime_paths)
        self.assertNotRegex(
            runtime,
            r"(?is)agents/openai\.yaml.{0,80}required|required.{0,80}agents/openai\.yaml",
        )

    def test_name_matches_directory(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: how-it-works\n", text.split("---")[1])
        self.assertEqual(SKILL.name, "how-it-works")

    def test_description_excludes_eli5_and_workflow(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        description = str(frontmatter["description"])
        self.assertNotIn("/eli5", description.lower())
        self.assertNotIn("바로 / 하나", description)
        self.assertIn("Use when", description)
        self.assertIn("Do not use", description)
        self.assertIn("ELI5", description)

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
