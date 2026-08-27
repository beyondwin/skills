from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "korean-writing-editor"
RUNNER = REPOSITORY_ROOT / "tests" / "korean-writing-editor" / "offline" / "run.py"
CASES = RUNNER.with_name("cases.json")
EXPECTED_SUMMARY = (
    "31 cases: normative=8 preservation=8 noop=6 voice=4 trigger=5"
)
PAYLOAD_FILES = (
    "SKILL.md",
    "references/editorial-guide.md",
    "references/sources.md",
)


def run_offline(*extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), *extra],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
    )


class KoreanPackageTests(unittest.TestCase):
    def test_korean_offline_runner_accepts_explicit_skill_root(self) -> None:
        result = run_offline("--scope", "full", "--skill-root", str(SKILL_ROOT))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("31 cases:", result.stdout)
        self.assertIn(EXPECTED_SUMMARY, result.stdout)
        self.assertIn("mutation checks: PASS", result.stdout)

    def test_staged_copy_passes_full_scope(self) -> None:
        self.assertTrue(SKILL_ROOT.is_dir(), "installed payload is absent")
        with tempfile.TemporaryDirectory() as directory:
            staged = Path(directory) / "korean-writing-editor"
            shutil.copytree(SKILL_ROOT, staged)
            result = run_offline("--scope", "full", "--skill-root", str(staged))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(EXPECTED_SUMMARY, result.stdout)
            self.assertIn("mutation checks: PASS", result.stdout)
            self.assertTrue((staged / "README.md").is_file())
            self.assertTrue((staged / "README.en.md").is_file())
            self.assertFalse((staged / "CHANGE_PROTOCOL.md").exists())
            self.assertFalse((staged / "evals").exists())

    def test_payload_declares_canonical_name_license_and_version(self) -> None:
        skill_md = SKILL_ROOT / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "SKILL.md is absent")
        text = skill_md.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: korean-writing-editor", text)
        self.assertIn("license: Apache-2.0", text)
        self.assertIn("compatibility:", text)
        self.assertIn('version: "2.0.1"', text)
        for relative in PAYLOAD_FILES:
            self.assertTrue(
                (SKILL_ROOT / relative).is_file(),
                f"payload missing {relative}",
            )
        payload_names = {path.name for path in SKILL_ROOT.iterdir()}
        self.assertIn("README.md", payload_names)
        self.assertIn("README.en.md", payload_names)
        self.assertNotIn("CHANGE_PROTOCOL.md", payload_names)
        self.assertNotIn("evals", payload_names)

    def test_cases_live_beside_the_runner(self) -> None:
        self.assertTrue(RUNNER.is_file(), "offline runner is absent")
        self.assertTrue(CASES.is_file(), "cases.json is absent")
        payload = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(payload["version"], "1")
        self.assertEqual(len(payload["cases"]), 31)
        runner_text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("--skill-root", runner_text)
        self.assertIn('with_name("cases.json")', runner_text)

    def test_default_skill_root_is_repository_payload(self) -> None:
        result = run_offline("--scope", "full")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(EXPECTED_SUMMARY, result.stdout)


if __name__ == "__main__":
    unittest.main()
