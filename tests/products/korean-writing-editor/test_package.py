from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / "korean-writing-editor"
RUNNER = (
    REPOSITORY_ROOT
    / "tests"
    / "products"
    / "korean-writing-editor"
    / "offline"
    / "run.py"
)
CASES = RUNNER.with_name("cases.json")
EXPECTED_SUMMARY = (
    "34 cases: normative=10 preservation=8 noop=6 voice=4 trigger=6"
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
        self.assertIn("34 cases:", result.stdout)
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

    def test_standalone_readme_relative_links_stay_inside_payload(self) -> None:
        with tempfile.TemporaryDirectory(prefix="korean payload ") as directory:
            staged = Path(directory) / "korean-writing-editor"
            shutil.copytree(SKILL_ROOT, staged)
            for name in ("README.md", "README.en.md"):
                text = (staged / name).read_text(encoding="utf-8")
                for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
                    if target.startswith(("https://", "http://", "#")):
                        continue
                    resolved = (staged / target.split("#", 1)[0]).resolve()
                    with self.subTest(file=name, target=target):
                        self.assertTrue(resolved.is_relative_to(staged.resolve()))
                        self.assertTrue(resolved.is_file())

    def test_release_target_and_skill_version_are_203(self) -> None:
        release = tomllib.loads(
            (SKILL_ROOT / "release.toml").read_text(encoding="utf-8")
        )
        self.assertEqual(release["version"], "2.0.3")
        self.assertIn(
            'version: "2.0.3"',
            (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"),
        )
        changelog = (SKILL_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertRegex(changelog, r"(?m)^## 2\.0\.3 - \d{4}-\d{2}-\d{2}$")

    def test_full_scope_rejects_a_broken_readme_link_in_a_copied_payload(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            staged = Path(directory) / "korean-writing-editor"
            shutil.copytree(SKILL_ROOT, staged)
            readme = staged / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\n[missing](missing.md)\n",
                encoding="utf-8",
            )
            result = run_offline("--scope", "full", "--skill-root", str(staged))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("broken relative link", result.stdout + result.stderr)

    def test_payload_declares_canonical_name_license_and_version(self) -> None:
        skill_md = SKILL_ROOT / "SKILL.md"
        self.assertTrue(skill_md.is_file(), "SKILL.md is absent")
        text = skill_md.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        self.assertIn("name: korean-writing-editor", text)
        self.assertIn("license: Apache-2.0", text)
        self.assertIn("compatibility:", text)
        self.assertIn('version: "2.0.3"', text)
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
        self.assertEqual(len(payload["cases"]), 34)
        runner_text = RUNNER.read_text(encoding="utf-8")
        self.assertIn("--skill-root", runner_text)
        self.assertIn('with_name("cases.json")', runner_text)

    def test_required_local_grammar_is_shared_by_correct_and_polish(self):
        cases = {
            case["id"]: case
            for case in json.loads(CASES.read_text(encoding="utf-8"))["cases"]
        }
        expected = "나는 3월 4일에 김민수의 글을 읽었지만, 다시 읽을지는 모르겠다."
        for mode in ("correct", "polish"):
            with self.subTest(mode=mode):
                case = cases[f"norm-grammar-particle-{mode}-{'09' if mode == 'correct' else '10'}"]
                self.assertEqual(case["candidate"], expected)
                self.assertEqual(case["expected_mode"], mode)
                self.assertIn("다시 읽을지는 모르겠다", case["must_preserve"])
                self.assertIn("글을을", case["forbidden_substrings"])

    def test_default_skill_root_is_repository_payload(self) -> None:
        result = run_offline("--scope", "full")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(EXPECTED_SUMMARY, result.stdout)


if __name__ == "__main__":
    unittest.main()
