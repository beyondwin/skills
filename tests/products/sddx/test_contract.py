from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.lib.product_contract import (
    load_product_release,
    parse_skill_frontmatter,
    validate_product,
)
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
    "near-miss-executing-plans",
    "near-miss-writing-plans",
    "near-miss-stay-orchestrator",
    "near-miss-grok-implementer-without-slash",
    "near-miss-named-sddx-without-slash",
    "no-task-brief",
    "no-batch-same-shape",
    "no-nested-native-sdd",
    "unplanned-work-ask-once",
    "orchestrator-is-this-session",
    "picker-grok-cli-vs-cursor-agent",
    "implementer-effort-per-task-high",
    "implementer-effort-per-task-xhigh",
    "implementer-effort-not-session",
    "effort-increase-fresh-worker",
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
    "reviewer-large-mechanical-rename-high",
    "reviewer-small-lock-order-xhigh",
    "reviewer-worker-xhigh-does-not-escalate",
    "reviewer-input-validation-is-not-security-boundary",
    "reviewer-final-review-is-not-a-trigger",
    "reviewer-round-four-re-review-xhigh",
    "reviewer-session-already-xhigh-no-escalation",
)
DESCRIPTION_FORBIDDEN = (
    "fresh implementer",
    "fix loop",
    "whole-branch",
    "stay orchestrator",
    "grok as implementer",
    "external cursor or grok cli implementer",
)

EXPECT_LOCK = {
    "activate": {
        "description_must": ("/sddx", "$sddx"),
        "skill_must": ("Activate only when the user message contains /sddx or $sddx",),
    },
    "do_not_activate": {
        "description_must": ("writing-plans", "executing-plans", "pre-sdd-review"),
        "description_must_not": ("stay orchestrator", "grok as implementer"),
        "skill_must": ("Activate only when the user message contains /sddx or $sddx",),
        "skill_must_not": ("explicit external implementer request",),
    },
    "no_task_brief": {
        "skill_must": ("Do not run Superpowers `task-brief` or `task-start`.",),
        "dispatch_must": ("Do not run Superpowers `task-brief` or `task-start`.",),
        "dispatch_must_not": ("use SDD's task-brief output",),
    },
    "no_batch_same_shape": {
        "skill_must": ("Do not batch same-shape plan tasks into one worker.",),
    },
    "no_nested_native_sdd": {
        "skill_must": (
            "Do not dispatch a nested controller that runs subagent-driven-development",
        ),
    },
    "unplanned_work_ask_once": {
        "skill_must": (
            "Ask once before dispatching the first task the plan does not name.",
        ),
    },
    "orchestrator_is_this_session": {
        "skill_must": ("The session that received `/sddx` or `$sddx` is the orchestrator.",),
    },
    "picker_grok_cli_vs_cursor_agent": {
        "skill_must": (
            "Grok CLI — pass `--model grok-4.7` from the resolver's `model_ids`.",
            "Cursor Agent (Grok)",
        ),
    },
    "implementer_effort_per_task_high": {
        "skill_must": ("Clear local or mechanical change, straightforward integration | High",),
    },
    "implementer_effort_per_task_xhigh": {
        "skill_must": ("concurrency, races, locking, ordering, or shared state",),
    },
    "implementer_effort_not_session": {
        "skill_must": ("Do not copy the session effort onto the implementer.",),
    },
    "effort_increase_fresh_worker": {
        "skill_must": ("When implementer effort increases, dispatch a fresh worker.",),
    },
    "backend_cursor": {"skill_must": ("`c` means `cursor`.",)},
    "skip_picker": {"skill_must": ("An explicit choice needs no re-approval on later tasks.",)},
    "backend_grok": {"skill_must": ("`g` means `grok`.",)},
    "picker_once": {"skill_must": ("Ask once",)},
    "ledger_backend": {"skill_must": ("`Backend: cursor|grok",)},
    "no_failover": {"skill_must": ("Do not automatically switch backends.",)},
    "agent_not_cursor": {"skill_must": ("PATH `agent` as Cursor",)},
    "no_worktree_flag": {"skill_must": ("Do not pass `--worktree` to the worker.",)},
    "ruling_not_xhigh": {"skill_must": ("Architecture ambiguity is a ruling, not XHigh.",)},
    "native_reviewer": {
        "skill_must": ("Task reviewers, scoped re-reviewers, and the final reviewer stay native",)
    },
    "not_in_catalog": {"catalog_must_not": ("sddx",)},
    "confirm_even_if_one": {"skill_must": ("Do not auto-select the only CLI.",)},
    "stop_no_push_publish": {"skill_must": ("stop and return BLOCKED",)},
    "no_host_secrets": {"skill_must": ("Do not copy host credentials",)},
    "prepare_profile": {"dispatch_must": ("prepare_grok_sandbox.py",)},
    "replace_sandbox_value": {"dispatch_must": ("--sandbox-profile",)},
    "cleanup_after_worker_exit": {"dispatch_must": ("cleanup",)},
    "not_done": {"skill_must": ("Process exit 0 is not task completion.",)},
    "inspect_blocker": {
        "skill_must": ("BLOCKED, NEEDS_CONTEXT, a missing report, or an unclear result must not become",)
    },
    "no_external_skills": {
        "worker_must": ("Do not read or invoke external skills, including Superpowers.",)
    },
    "no_full_plan": {"skill_must": ("The worker cannot read the plan",)},
    "no_mcp_tools": {"dispatch_must": ("search_tool,use_tool",)},
    "same_orchestrator_model": {"skill_must": ("use the active orchestrator's",)},
    "review_effort_high": {"skill_must": ("Task N review: sddx default — high",)},
    "review_effort_xhigh": {"skill_must": ("subagent_type: sddx:sddx-reviewer-xhigh",)},
    "role_fail": {"skill_must": ("prohibited read is FAIL",)},
    "report_discrepancy": {"skill_must": ("any discrepancy with the worker report",)},
    "not_clean_done": {"skill_must": ("permits a clean DONE.",)},
    "role_unverified": {
        "skill_must": ("Missing or incomplete tool evidence is UNVERIFIED, never PASS.",)
    },
    "use_brief": {"skill_must": ("Every brief carries the plan's run-wide constraints",)},
    "no_plan_link_following": {"worker_must": ("Do not open the full implementation plan",)},
    "no_shell_search_bypass": {
        "worker_must": ("Do not retrieve its contents through shell",)
    },
    "scope_deviations_reported": {
        "dispatch_must": ("Report actual scope deviations even if tests pass",)
    },
    "full_command": {"worker_must": ("include the full wrapper command",)},
    "actual_test_exit": {"worker_must": ("actual test exit codes",)},
    "wrapper_exit_separate": {
        "worker_must": ("distinguish its exit\nfrom the test exit",)
    },
    "allowed_inspection": {"skill_must": ("Filename-only listings inside the",)},
    "scope_deviations_none": {"skill_must": ("Scope deviations: none",)},
    "no_size_based_escalation": {"skill_must": ("File count, line count",)},
    "ledger_trigger_and_path": {"skill_must": ("XHigh must name a trigger and a",)},
    "worker_effort_not_cited": {
        "skill_must": ("Reviewer XHigh because the worker ran XHigh",)
    },
    "no_security_boundary_claim": {
        "skill_must": ("an auth, permission, secret, or sandbox boundary",)
    },
    "fresh_xhigh_worker": {"skill_must": ("Rounds 4-5 use a fresh worker at XHigh.",)},
    "no_escalation_agent": {"skill_must": ("do not use the escalation",)},
    "session_effort_not_lowered": {"skill_must": ("do not lower the session",)},
}


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
        self.assertIn("/sddx", description)
        self.assertIn("$sddx", description)
        self.assertIn("writing-plans", description.lower())
        self.assertIn("executing-plans", description.lower())

    def test_every_expect_tag_is_locked_to_source(self) -> None:
        data = json.loads(CASES.read_text(encoding="utf-8"))
        used = {tag for item in data["cases"] for tag in item["expect"]}
        self.assertEqual(used, set(EXPECT_LOCK))
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        worker = (SKILL / "references" / "worker-prompt.md").read_text(encoding="utf-8")
        description = str(
            parse_skill_frontmatter(skill).get("description", "")
        )
        catalog = (ROOT / "catalog" / "catalog.lock.json").read_text(encoding="utf-8")
        sources = {
            "skill": skill,
            "dispatch": dispatch,
            "worker": worker,
            "description": description,
            "catalog": catalog,
        }
        fold = lambda value: re.sub(r"\s+", " ", value)
        for tag, lock in EXPECT_LOCK.items():
            for key, phrases in lock.items():
                if key.endswith("_must_not"):
                    doc = key[: -len("_must_not")]
                    haystack = sources[doc].lower() if doc == "description" else sources[doc]
                    for phrase in phrases:
                        self.assertNotIn(fold(phrase).lower() if doc == "description" else fold(phrase), fold(haystack), f"{tag} {key}: {phrase}")
                elif key.endswith("_must"):
                    doc = key[: -len("_must")]
                    for phrase in phrases:
                        self.assertIn(fold(phrase), fold(sources[doc]), f"{tag} {key}: {phrase}")
                else:
                    self.fail(key)

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

    def test_current_state_block_is_the_single_controller_record(self) -> None:
        reference = SKILL / "references" / "current-state.md"
        self.assertTrue(reference.is_file())
        text = reference.read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/current-state.md", skill)
        for marker in ("<!-- sddx:current:start -->", "<!-- sddx:current:end -->"):
            self.assertIn(marker, text)
            self.assertIn(marker, skill)
        self.assertIn("# SDD ledger — plan:", text)
        self.assertIn("# SDD ledger — plan:", skill)
        self.assertIn("Task <ID>: complete", skill)
        for field in (
            "Next plan",
            "Backend",
            "Worker session",
            "Orchestrator",
            "Worker effort",
            "Review host",
            "Open findings",
            "Authorized scope",
            "Host checks pending",
            "Next action",
            "Evidence",
        ):
            self.assertIn(field, text, field)

    def test_no_parallel_controller_state_file(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in ("controller-current-state.md", "controller-recovery.md"):
            self.assertFalse((SKILL / "references" / name).exists(), name)
            self.assertIn(f"`{name}`", skill, name)
        self.assertIn(
            "Do not create `controller-current-state.md`, "
            "`controller-recovery.md`, or any",
            skill,
        )

    def test_helper_scripts_are_named_where_they_are_used(self) -> None:
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in (
            "extract_task.py",
            "resolve_backend.py",
            "prepare_grok_sandbox.py",
            "run_worker.py",
        ):
            self.assertTrue((SKILL / "scripts" / name).is_file(), name)
            self.assertIn(name, dispatch, name)
        self.assertIn("run_worker.py", skill)
        self.assertIn("resolve_backend.py", skill)

    def test_dispatch_runs_the_worker_through_the_runner(self) -> None:
        text = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        self.assertIn("--attempt-dir", text)
        self.assertIn("--sandbox-profile", text)
        self.assertIn("run.json", text)
        self.assertIn("launch_failed", text)
        self.assertIn("timed_out", text)
        self.assertIn("session_id", text)
        self.assertIn("skill_version", text)
        self.assertIn("--stream", text)
        self.assertIn("pending_bytes", text)
        self.assertIn("output_format", text)
        self.assertIn("report.md", text)
        self.assertIn("pid_alive", text)
        self.assertIn("bounded tools index", text)

    def test_interrupt_ends_the_worker_on_every_face(self) -> None:
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        fold = lambda value: re.sub(r"\s+", " ", value)
        for text in (dispatch, contract):
            self.assertIn("the runner was interrupted (SIGTERM or Ctrl-C)", fold(text))
        self.assertNotIn("does not kill the tree", fold(dispatch))
        self.assertNotIn("leaves the worker running", fold(dispatch))
        self.assertNotIn("프로세스 트리는 죽이지 않습니다", fold(contract))

    def test_first_output_deadline_is_on_every_face(self) -> None:
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        fold = lambda value: re.sub(r"\s+", " ", value)
        for text in (dispatch, skill, contract):
            self.assertIn("no output within 300 seconds", fold(text))
        self.assertIn("It defaults to 7200", fold(dispatch))
        self.assertIn("기본값은 7200", fold(contract))
        self.assertNotIn("defaults to 3600", fold(dispatch))

    def test_grok_tools_index_is_on_every_face(self) -> None:
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        testing = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "testing.md"
        ).read_text(encoding="utf-8")
        fold = lambda value: re.sub(r"\s+", " ", value)
        self.assertIn("Grok `tool_use`", fold(dispatch))
        self.assertIn("Grok `tool_use`", fold(contract))
        self.assertIn("Cursor·Grok 두 로그 형태의 bounded tools index", fold(testing))

    def test_dispatch_opens_with_controller_procedure(self) -> None:
        text = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        self.assertIn("## Controller procedure", text)
        self.assertIn("bash scripts/sdd-workspace", text)
        self.assertIn("--global-constraints", text)
        self.assertIn("## Runner already does this", text)
        procedure, _, rest = text.partition("## Runner already does this")
        self.assertTrue(rest)
        self.assertLess(procedure.find("## Controller procedure"), procedure.find("python3 \"<skill-root>/scripts/extract_task.py\""))
        for key in ("session_id", "timed_out", "pending_bytes", "pid_alive", "launch_failed"):
            self.assertIn(key, rest, key)

    def test_contract_owns_extraction_not_task_brief(self) -> None:
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        self.assertIn("사용자 메시지에 `/sddx` 또는 `$sddx`가 있을 때만", contract)
        self.assertIn("`--global-constraints`", contract)
        self.assertIn("한 워커가 여러 계획 과제를 묶지 않습니다", contract)
        self.assertIn("중첩 native SDD", contract)
        self.assertIn("워크스페이스", contract)
        self.assertNotIn("명시적인 외부 implementer 요청이 없으면", contract)

    def test_readme_when_to_use_is_slash_dollar_only(self) -> None:
        korean = (SKILL / "README.md").read_text(encoding="utf-8")
        english = (SKILL / "README.en.md").read_text(encoding="utf-8")
        self.assertIn("`/sddx`", korean)
        self.assertIn("`$sddx`", korean)
        self.assertNotIn("외부 Grok 또는 Cursor implementer", korean.split("## 사용할 때와 사용하지 않을 때")[1].split("## ")[0])
        self.assertIn("/sddx", english)
        self.assertIn("$sddx", english)
        when = english.split("## When to use and not use")[1].split("## ")[0]
        self.assertNotIn("external Grok or Cursor implementer", when)

    def test_input_and_backend_order_ask_once(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("An explicit choice in this request", text)
        self.assertIn("The current state of this same run", text)
        self.assertIn("Ask once", text)
        self.assertIn("one active plan and one ledger at a time", text)
        self.assertIn("Never pass the previous provider's session ID", text)
        lowered = text.lower()
        self.assertIn("does not reset the fix-round count", lowered)

    def test_host_checks_use_the_existing_statuses(self) -> None:
        worker = (SKILL / "references" / "worker-prompt.md").read_text(encoding="utf-8")
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for text in (worker, dispatch, skill):
            self.assertIn("Worker checks", text)
            self.assertIn("Host checks", text)
        self.assertIn("There is\nno other status", worker)
        self.assertIn("nothing else writes it for you", worker)
        self.assertIn("402", skill)
        self.assertIn("do not re-run under the same condition", skill)
        self.assertIn("no automatic retry", dispatch.lower())

    def test_both_hosts_share_the_same_tooling(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("spawn_agent", text)
        self.assertIn("the same product Python scripts", text)
        self.assertIn(
            "The supported OS is macOS. Do not add Windows transport. Refuse Windows at the product CLIs.",
            text,
        )

    def test_replaced_instructions_are_gone(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        for removed in (
            "If the plan path is missing or is not a file, stop",
            "One plan per invocation",
            "Keep that backend for every later task",
            "report that the requested effort cannot be set",
            "Do not replace\nWindows support with POSIX-only code",
        ):
            self.assertNotIn(removed, skill, removed)
        self.assertNotIn("POSIX-only code", re.sub(r"\s+", " ", skill))
        for removed in (
            "For Grok, use `--output-format streaming-messages-json`",
            "Compose the worker command from `argv_prefix`",
            'argv.index("--sandbox")',
            "already in `argv_prefix`",
        ):
            self.assertNotIn(removed, dispatch, removed)

    def test_hosts_are_not_backends(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        self.assertEqual(registry.require("sddx").supported_hosts, ("claude-code", "codex"))
        lock = (ROOT / "catalog" / "catalog.lock.json").read_text(encoding="utf-8")
        self.assertNotIn("sddx", lock)

    def test_near_miss_phrases_are_explicit(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("pre-sdd-review", text)
        self.assertIn("Do not activate", text)
        self.assertNotIn("explicit external implementer request", text)

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

    def test_claude_plugin_directory_is_allowed_for_sddx(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "sddx"
            shutil.copytree(SKILL, copied, ignore=shutil.ignore_patterns("__pycache__"))
            plugin_dir = copied / ".claude-plugin"
            plugin_dir.mkdir(exist_ok=True)
            (plugin_dir / "plugin.json").write_text('{"name": "sddx"}\n', encoding="utf-8")
            self.assertEqual(validate_product(copied, registry), [])

    def test_claude_plugin_directory_is_allowed_only_for_sddx(self) -> None:
        registry = load_registry(ROOT / "products.toml")
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "how-it-works"
            shutil.copytree(ROOT / "skills" / "how-it-works", copied,
                            ignore=shutil.ignore_patterns("__pycache__"))
            plugin_dir = copied / ".claude-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text('{"name": "how-it-works"}\n', encoding="utf-8")
            self.assertIn("unexpected top-level file: .claude-plugin",
                          validate_product(copied, registry))

    def test_plugin_manifest_names_the_product(self) -> None:
        manifest = json.loads((SKILL / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "sddx")
        self.assertIn("description", manifest)
        self.assertIn("version", manifest)

    def test_plugin_manifest_registers_the_xhigh_agent_file(self) -> None:
        manifest = json.loads((SKILL / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertNotIn("agents", manifest)
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("subagent_type: sddx:sddx-reviewer-xhigh", skill)
        self.assertNotIn("subagent_type: sddx-reviewer-xhigh`", skill)
        self.assertNotIn("subagent_type: sddx:claude-code:sddx-reviewer-xhigh", skill)

    def test_claude_code_agents_are_closed_and_escalation_only(self) -> None:
        directory = SKILL / "agents"
        self.assertFalse((directory / "claude-code").exists())
        definitions = sorted(
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*.md")
        )
        self.assertEqual(definitions, ["sddx-reviewer-xhigh.md"])
        frontmatter = parse_skill_frontmatter(
            (directory / "sddx-reviewer-xhigh.md").read_text(encoding="utf-8")
        )
        self.assertEqual(frontmatter.get("name"), "sddx-reviewer-xhigh")
        self.assertEqual(frontmatter.get("effort"), "xhigh")
        self.assertNotIn("model", frontmatter)
        disallowed = str(frontmatter.get("disallowedTools", ""))
        for tool in ("Edit", "Write", "NotebookEdit"):
            self.assertIn(tool, disallowed)

    def test_plugin_manifest_version_matches_the_release(self) -> None:
        manifest = json.loads((SKILL / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        release = load_product_release(SKILL)
        self.assertEqual(manifest["version"], release.version)

    def test_testing_doc_records_win32_fixtures_as_deleted(self) -> None:
        testing = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "testing.md"
        ).read_text(encoding="utf-8")
        self.assertNotIn("삭제 대상", testing)
        self.assertIn("Win32 전송 픽스처는 삭제했습니다", testing)
        self.assertIn(
            'Windows `.cmd` 왕복 검사(`skipUnless(os.name == "nt")`)는 삭제했습니다.',
            testing,
        )
        self.assertIn("Windows는 지원하지 않습니다", testing)

    def test_changelog_records_windows_refusal_as_breaking(self) -> None:
        # Pinned to the entry, not to `Unreleased`: cutting a release moves the
        # section without changing what the entry has to say. What must hold is
        # that dropping Windows is recorded as Breaking and never as a fix.
        changelog = (SKILL / "CHANGELOG.md").read_text(encoding="utf-8")
        entry = "Windows is unsupported; product CLIs refuse it."
        self.assertIn(entry, changelog)
        # `[^\n]*` on the heading: with re.S a `.+` there swallows the whole
        # file into one section and every assertion below passes vacuously.
        sections = re.findall(
            r"^(### [^\n]*)\n(.*?)(?=^#{2,3} |\Z)", changelog, re.S | re.M
        )
        owners = [heading for heading, body in sections if entry in body]
        self.assertEqual(owners, ["### Breaking"])
        for heading, body in sections:
            if heading == "### Fixed":
                self.assertNotIn("Windows is unsupported", body)


def _python_fence_after(relative: str, marker: str) -> str:
    text = (ROOT / relative).read_text(encoding="utf-8")
    tail = text.split(marker, 1)[1]
    match = re.match(r"\s*```python\n(.*?)\n```", tail, re.S)
    if match is None:
        raise AssertionError(f"Python block must follow marker: {relative}")
    return match.group(1)
