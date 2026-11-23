from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter  # noqa: E402

SKILL = ROOT / "skills" / "kws-book-writer"
SCRIPT = SKILL / "scripts" / "book_check.py"
REFERENCES = ("workflow.md", "plan.md", "voice.md", "chapter.md", "acceptance.md")
PHASE_OUTPUTS = (
    "`brief.md`",
    "`research/ledger.md`",
    "`plan.md`, `voice.md`, `book.json`",
    "`chapters/01.md`",
    "`checks/factcheck.md`",
    "`manuscript.md`",
    "`checks/acceptance.json`",
)


def skill_text() -> str:
    return (SKILL / "SKILL.md").read_text(encoding="utf-8")


def markers() -> list[str]:
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "markers"], capture_output=True, text=True, encoding="utf-8", check=True
    ).stdout
    return [line for line in out.splitlines() if line]


class FrontmatterTests(unittest.TestCase):
    def test_explicit_only_frontmatter(self) -> None:
        meta = parse_skill_frontmatter(skill_text())
        self.assertEqual(meta["name"], "kws-book-writer")
        self.assertEqual(meta["disable-model-invocation"], "true")
        self.assertTrue(meta["description"].startswith("Use when explicitly invoked"))
        self.assertIn("Do not use for", meta["description"])
        self.assertIn("/kws-book-writer", skill_text())

    def test_version_matches_release(self) -> None:
        release = (SKILL / "release.toml").read_text(encoding="utf-8")
        version = re.search(r'^version = "([^"]+)"', release, re.M).group(1)
        self.assertIn('version: "{}"'.format(version), skill_text())


class StructureTests(unittest.TestCase):
    def test_entry_lists_every_phase_output(self) -> None:
        text = skill_text()
        for output in PHASE_OUTPUTS:
            with self.subTest(output=output):
                self.assertIn(output, text)

    def test_every_reference_exists_and_is_linked(self) -> None:
        text = skill_text()
        for name in REFERENCES:
            with self.subTest(name=name):
                self.assertTrue((SKILL / "references" / name).is_file())
                self.assertIn("references/" + name, text)

    def test_markers_are_defined_only_in_the_script(self) -> None:
        found = markers()
        self.assertTrue(found)
        for path in SKILL.rglob("*"):
            if not path.is_file() or path == SCRIPT or path.suffix not in {".md", ".py", ".yaml", ".toml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for marker in found:
                with self.subTest(path=path.relative_to(SKILL).as_posix(), marker=marker):
                    self.assertNotIn(marker, text)

    def test_writer_brief_takes_markers_from_the_script(self) -> None:
        text = (SKILL / "references" / "chapter.md").read_text(encoding="utf-8")
        self.assertIn("book_check.py markers", text)

    def test_gate_brief_is_the_plain_review_with_workspace_inputs(self) -> None:
        # The 2026-11-20 seeded-defect run found no measured difference for the
        # eight-criterion brief, so the gate is the plain review plus these inputs.
        text = (SKILL / "references" / "acceptance.md").read_text(encoding="utf-8")
        brief = text.split("## Gate brief", 1)[1].split("## After the verdict", 1)[0]
        self.assertIn("출판 전에 반드시 고쳐야 할 오류", brief)
        for name in ("brief.md", "plan.md", "research/ledger.md", "checks/check-report.md",
                     "checks/factcheck.md", "chapters/", "checks/acceptance.md"):
            with self.subTest(name=name):
                self.assertIn(name, brief)
        self.assertNotIn("(h)", brief)
        self.assertIn("USER_APPROVED", text)

    def test_script_avoids_syntax_newer_than_39(self) -> None:
        import ast

        source = SCRIPT.read_text(encoding="utf-8")
        ast.parse(source, feature_version=(3, 9))
        self.assertIn("from __future__ import annotations", source)


if __name__ == "__main__":
    unittest.main()
