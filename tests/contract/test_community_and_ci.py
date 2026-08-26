from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "verify.yml"
CONTRIBUTING_PATH = ROOT / "CONTRIBUTING.md"
SECURITY_PATH = ROOT / "SECURITY.md"
CONDUCT_PATH = ROOT / "CODE_OF_CONDUCT.md"
CODEOWNERS_PATH = ROOT / ".github" / "CODEOWNERS"
DEPENDABOT_PATH = ROOT / ".github" / "dependabot.yml"
PR_TEMPLATE_PATH = ROOT / ".github" / "pull_request_template.md"
BUG_TEMPLATE_PATH = ROOT / ".github" / "ISSUE_TEMPLATE" / "bug.yml"
DOCS_TEMPLATE_PATH = ROOT / ".github" / "ISSUE_TEMPLATE" / "documentation.yml"
ISSUE_CONFIG_PATH = ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml"
CHECKOUT_SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
SETUP_PYTHON_SHA = "42375524e23c412d93fb67b49958b491fce71c38"
CREDENTIAL_MARKERS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CURSOR_API_KEY")
PERSONAL_MARKERS = ("/Users/", "source/private", "SKILLS_ARCHIVE_CHECKOUT")
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
VERIFIER_COMMAND = 'python scripts/verify.py --profile "${{ matrix.profile }}"'


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _assert_exists(test: unittest.TestCase, path: Path) -> None:
    test.assertTrue(path.is_file(), f"{path.relative_to(ROOT).as_posix()} is absent")


class CiWorkflowTests(unittest.TestCase):
    def test_ci_is_read_only_provider_free_and_sha_pinned(self) -> None:
        _assert_exists(self, WORKFLOW_PATH)
        workflow = WORKFLOW_PATH.read_text()
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("pull_request_target", workflow)
        self.assertNotRegex(workflow, r"uses: [^\n]+@(v|main|master)")
        for secret_name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CURSOR_API_KEY"):
            self.assertNotIn(secret_name, workflow)

    def test_ci_pins_required_actions_timeout_python_and_matrix(self) -> None:
        _assert_exists(self, WORKFLOW_PATH)
        workflow = _read(WORKFLOW_PATH)
        self.assertIn(f"actions/checkout@{CHECKOUT_SHA}", workflow)
        self.assertIn(f"actions/setup-python@{SETUP_PYTHON_SHA}", workflow)
        self.assertIn("timeout-minutes: 20", workflow)
        self.assertRegex(workflow, r"python-version:\s*['\"]?3\.11['\"]?")
        self.assertIn("fail-fast: false", workflow)
        self.assertRegex(workflow, r"os:\s*ubuntu-latest\s*\n\s*profile:\s*full")
        self.assertRegex(workflow, r"os:\s*macos-latest\s*\n\s*profile:\s*full")
        self.assertRegex(workflow, r"os:\s*windows-latest\s*\n\s*profile:\s*windows-portable")
        self.assertIn("pull_request", workflow)
        self.assertRegex(workflow, r"branches:\s*\[main\]|-\s*main")

    def test_ci_runs_only_the_provider_free_verifier(self) -> None:
        _assert_exists(self, WORKFLOW_PATH)
        workflow = _read(WORKFLOW_PATH)
        self.assertIn(VERIFIER_COMMAND, workflow)
        run_commands = re.findall(r"(?m)^\s+run:\s*\|?\s*(.+)$", workflow)
        self.assertEqual(run_commands, [VERIFIER_COMMAND])
        self.assertNotIn("--execute", workflow)
        self.assertNotIn("--preflight", workflow)
        self.assertNotIn("${{ secrets", workflow)
        self.assertNotIn("secrets.", workflow)
        lowered = workflow.lower()
        self.assertNotIn("openai ", lowered)
        self.assertNotIn("anthropic", lowered)
        self.assertNotIn("images.generate", lowered)
        self.assertNotIn("remote image", lowered)


class CommunityPolicyTests(unittest.TestCase):
    def test_contributions_reject_third_skill_by_default(self) -> None:
        _assert_exists(self, CONTRIBUTING_PATH)
        text = CONTRIBUTING_PATH.read_text()
        self.assertIn("new skills are not accepted by default", text.lower())

    def test_contributions_accept_focused_fixes_under_apache(self) -> None:
        _assert_exists(self, CONTRIBUTING_PATH)
        text = _read(CONTRIBUTING_PATH)
        lowered = text.lower()
        self.assertIn("behavior", lowered)
        self.assertIn("security", lowered)
        self.assertTrue("documentation" in lowered or "docs" in lowered)
        self.assertIn("compatibility", lowered)
        self.assertIn("synthetic", lowered)
        self.assertIn("apache-2.0", lowered)
        self.assertIn("reproduction", lowered)
        self.assertIn("deterministic", lowered)
        self.assertIn("korean-writing-editor", text)
        self.assertIn("image-workbench", text)
        self.assertIn("private", lowered)
        self.assertTrue("prompt" in lowered and "image" in lowered)

    def test_security_policy_supports_2x_and_private_github_reporting(self) -> None:
        _assert_exists(self, SECURITY_PATH)
        text = _read(SECURITY_PATH)
        lowered = text.lower()
        self.assertRegex(text, r"\b2\.x\b")
        self.assertIn("private vulnerability reporting", lowered)
        self.assertIn("github", lowered)
        self.assertNotRegex(text, EMAIL_RE)
        self.assertIn("do not", lowered)
        self.assertTrue(
            "issue" in lowered,
            "SECURITY.md must tell reporters not to use public issues",
        )

    def test_code_of_conduct_is_present(self) -> None:
        _assert_exists(self, CONDUCT_PATH)
        text = _read(CONDUCT_PATH)
        lowered = text.lower()
        self.assertTrue(
            "contributor covenant" in lowered or "code of conduct" in lowered,
            "CODE_OF_CONDUCT.md must state a code of conduct",
        )
        self.assertNotRegex(text, EMAIL_RE)

    def test_codeowners_assigns_beyondwin(self) -> None:
        _assert_exists(self, CODEOWNERS_PATH)
        text = _read(CODEOWNERS_PATH)
        self.assertIn("* @beyondwin", text)

    def test_dependabot_tracks_github_actions_weekly(self) -> None:
        _assert_exists(self, DEPENDABOT_PATH)
        text = _read(DEPENDABOT_PATH)
        self.assertIn("package-ecosystem:", text)
        self.assertIn("github-actions", text)
        self.assertIn("interval:", text)
        self.assertIn("weekly", text)

    def test_issue_forms_prohibit_personal_content_and_route_security_privately(self) -> None:
        for path in (BUG_TEMPLATE_PATH, DOCS_TEMPLATE_PATH, ISSUE_CONFIG_PATH):
            _assert_exists(self, path)
        bug = _read(BUG_TEMPLATE_PATH).lower()
        docs = _read(DOCS_TEMPLATE_PATH).lower()
        config = _read(ISSUE_CONFIG_PATH).lower()
        for text in (bug, docs):
            self.assertTrue("personal" in text or "private" in text)
            self.assertTrue("image" in text or "images" in text)
            self.assertTrue("text" in text or "prompt" in text)
        self.assertIn("blank_issues_enabled: false", config)
        self.assertIn("contact_links", config)
        self.assertIn("security", config)
        self.assertIn("advisories", config)
        self.assertTrue(
            "private" in config or "do not" in config or "not file" in config,
            "issue config must route security away from public issues",
        )

    def test_pull_request_template_requires_curated_evidence(self) -> None:
        _assert_exists(self, PR_TEMPLATE_PATH)
        text = _read(PR_TEMPLATE_PATH).lower()
        self.assertIn("apache-2.0", text)
        self.assertTrue("third skill" in text or "new skill" in text)
        self.assertTrue("personal" in text or "private" in text)
        self.assertTrue("image" in text or "prompt" in text)
        self.assertTrue("deterministic" in text or "reproduction" in text)

    def test_governance_files_omit_personal_paths_and_credentials(self) -> None:
        paths = (
            CONTRIBUTING_PATH,
            SECURITY_PATH,
            CONDUCT_PATH,
            CODEOWNERS_PATH,
            DEPENDABOT_PATH,
            PR_TEMPLATE_PATH,
            BUG_TEMPLATE_PATH,
            DOCS_TEMPLATE_PATH,
            ISSUE_CONFIG_PATH,
            WORKFLOW_PATH,
        )
        for path in paths:
            _assert_exists(self, path)
            text = _read(path)
            for marker in PERSONAL_MARKERS:
                self.assertNotIn(marker, text)
            for secret_name in CREDENTIAL_MARKERS:
                self.assertNotIn(secret_name, text)


if __name__ == "__main__":
    unittest.main()
