from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import parse_skill_frontmatter
from scripts.lib.product_registry import load_registry
from tests.repository.test_installation_contract import installation_block

SKILL = ROOT / "skills" / "sddx"
CASES = ROOT / "tests" / "products" / "sddx" / "cases.json"
CASE_IDS = (
    "explicit-slash-sddx",
    "explicit-codex-sddx",
    "argv-cursor",
    "argv-grok",
    "argv-alias-c",
    "argv-alias-g",
    "picker-once-per-plan",
    "missing-requested-backend-no-failover",
    "agent-binary-is-not-cursor",
    "worker-no-nested-worktree",
    "ambiguity-is-ruling-not-xhigh",
    "reviewer-stays-native",
    "near-miss-native-sdd",
    "near-miss-pre-sdd-review",
    "catalog-excludes-sddx",
    "one-available-backend-still-confirms",
    "worker-no-host-outside-side-effects",
    "no-credentials-in-worker-prompt",
    "grok-linked-worktree-profile",
    "exit-zero-blocked-is-not-done",
    "missing-report-is-not-done",
    "worker-brief-only-no-skills",
    "reviewer-inherits-orchestrator",
    "reviewer-risk-xhigh",
    "successful-prohibited-read",
    "missing-tool-evidence",
    "worker-plan-link",
    "worker-report-deviations",
    "test-wrapper-exit",
    "worker-filename-inspection",
    "worker-task-configuration-read",
    "inspection-does-not-permit-plan-content",
)
DESCRIPTION_FORBIDDEN = ("fresh implementer", "fix loop", "whole-branch")


class SddxContractTests(unittest.TestCase):
    def test_case_ids_match_spec(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(tuple(item["id"] for item in data["cases"]), CASE_IDS)

    def test_description_is_trigger_only(self) -> None:
        frontmatter = parse_skill_frontmatter((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        description = str(frontmatter.get("description", ""))
        self.assertTrue(description.startswith("Use when"))
        lowered = description.lower()
        for fragment in DESCRIPTION_FORBIDDEN:
            self.assertNotIn(fragment, lowered)

    def test_skill_does_not_copy_sdd_and_overrides_dispatch(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8") for path in SKILL.rglob("*.md"))
        self.assertIn("subagent-driven-development", text)
        self.assertIn("resolve_backend.py", text)
        self.assertIn("/sddx", text)
        self.assertIn("$sddx", text)
        self.assertIn("AskUserQuestion", text)
        self.assertIn("Backend:", text)
        self.assertIn("XHigh", text)
        self.assertIn("NEEDS_CONTEXT", text)
        self.assertIn("do not copy", text.lower())
        self.assertIn("do not automatically switch", text.lower())
        self.assertIn("--disable-web-search", text)
        self.assertIn("agent", text.lower())
        self.assertNotIn("plugins/superpowers/skills/subagent-driven-development/SKILL.md", text)

    def test_worker_prompt_forbids_nested_orchestration(self) -> None:
        text = (SKILL / "references" / "worker-prompt.md").read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertIn("do not", lowered)
        self.assertIn("subagent", lowered)
        self.assertIn("worktree", lowered)
        self.assertIn("DONE", text)
        self.assertIn("NEEDS_CONTEXT", text)

    def test_dispatch_never_passes_worktree_flag(self) -> None:
        text = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        self.assertIn("resolve_backend.py", text)
        self.assertIn("--resume", text)
        self.assertIn("Do not pass `--worktree`", text)

    def test_dispatch_prepares_and_cleans_grok_profile(self):
        text = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        self.assertIn("prepare_grok_sandbox.py", text)
        self.assertIn("--state", text)
        self.assertIn("cleanup", text)
        self.assertIn("--rules", text)

    def test_hosts_are_not_backends(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(registry.require("sddx").supported_hosts, ("claude-code", "codex"))
        lock = (ROOT / "catalog" / "catalog.lock.json").read_text(encoding="utf-8")
        self.assertNotIn("sddx", lock)

    def test_near_miss_phrases_are_explicit(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("pre-sdd-review", text)
        self.assertIn("Do not activate", text)

    def test_one_available_backend_still_confirms(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertIn("only one backend", text)
        self.assertTrue("confirm" in text or "확인" in text)

    def test_worker_prompt_forbids_push_publish_and_host_secrets(self) -> None:
        worker = (SKILL / "references" / "worker-prompt.md").read_text(encoding="utf-8").lower()
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8").lower()
        self.assertIn("push", worker)
        self.assertIn("publish", worker)
        self.assertIn("blocked", worker)
        self.assertIn("credentials", skill)
        self.assertIn("credentials", dispatch)

    def test_sddx_local_link_marker_and_invocations(self) -> None:
        marker = "<!-- sddx-local-links -->"
        agents = 'python3 - "$PWD/skills/sddx" "$HOME/.agents/skills/sddx" <<\'PY\''
        claude = 'python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx" <<\'PY\''
        unlink_agents = "unlink ~/.agents/skills/sddx"
        unlink_claude = "unlink ~/.claude/skills/sddx"
        for relative in (
            "skills/sddx/README.md",
            "skills/sddx/README.en.md",
            "docs/users/ko/install-local.md",
            "docs/users/en/install-local.md",
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertEqual(text.count(marker), 1, relative)
            self.assertIn(agents, text)
            self.assertIn(claude, text)
            self.assertIn(unlink_agents, text)
            self.assertIn(unlink_claude, text)
            self.assertNotIn("ln -s", text)
            self.assertEqual(
                _python_fence_after(relative, marker),
                installation_block("skills/how-it-works/README.md"),
                relative,
            )


def _python_fence_after(relative: str, marker: str) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    tail = text.split(marker, 1)[1]
    match = re.match(r"\s*```python\n(.*?)\n```", tail, re.S)
    if match is None:
        raise AssertionError(f"Python block must follow marker: {relative}")
    return match.group(1)
