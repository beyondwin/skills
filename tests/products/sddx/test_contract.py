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
    "near-miss-native-sdd",
    "near-miss-waygent",
    "near-miss-pre-sdd-review",
    "near-miss-executing-plans",
    "near-miss-writing-plans",
    "near-miss-stay-orchestrator",
    "near-miss-grok-implementer-without-slash",
    "near-miss-named-sddx-without-slash",
    "waygent-is-the-base",
    "missing-waygent-blocks",
    "no-plan-asks-once",
    "unplanned-work-ask-once",
    "orchestrator-is-this-session",
    "picker-grok-cli-vs-cursor-agent",
    "implementer-effort-per-task-high",
    "implementer-effort-per-task-xhigh",
    "implementer-effort-not-session",
    "effort-increase-fresh-worker",
    "fix-resumes-same-session",
    "retry-is-fresh-xhigh-worker",
    "reviewer-follows-waygent-models",
    "one-available-backend-still-confirms",
    "worker-no-host-outside-side-effects",
    "no-credentials-in-worker-prompt",
    "grok-linked-worktree-profile",
    "exit-zero-blocked-is-not-done",
    "missing-report-is-not-done",
    "worker-brief-only-no-skills",
    "successful-prohibited-read",
    "missing-tool-evidence",
    "worker-plan-link",
    "worker-report-deviations",
    "test-wrapper-exit",
    "worker-filename-inspection",
    "worker-task-configuration-read",
    "inspection-does-not-permit-plan-content",
    "worker-commits-with-trailer",
    "worker-stops-its-processes",
    "record-observed-models",
    "unconfirmed-model-marked-requested",
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
        "description_must": ("writing-plans", "executing-plans", "pre-sdd-review", "/waygent"),
        "description_must_not": ("stay orchestrator", "grok as implementer"),
        "skill_must": ("Do not activate on /waygent",),
        "skill_must_not": ("explicit external implementer request",),
    },
    "waygent_base": {
        "skill_must": ("Follow the installed waygent skill at `<skill-root>/../waygent/SKILL.md` as the base loop",),
    },
    "no_copy_waygent": {"skill_must": ("Do not copy waygent into this skill.",)},
    "waygent_missing_blocked": {
        "skill_must": ("If `<skill-root>/../waygent/SKILL.md` is missing, stop as BLOCKED",),
    },
    "plan_required": {"skill_must": ("SDDx always needs a plan file",)},
    "unplanned_work_ask_once": {
        "skill_must": ("Ask once before dispatching the first task the plan does not name",),
    },
    "orchestrator_is_this_session": {
        "skill_must": ("The session that received `/sddx` or `$sddx` is the orchestrator",),
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
    "fix_resumes_session": {"skill_must": ("`--resume <session_id>` at the same effort",)},
    "retry_fresh_xhigh": {"skill_must": ("a fresh worker at XHigh (the worker model stays Grok 4.7)",)},
    "reviewer_waygent_models": {"skill_must": ("native, as waygent's Models section says",)},
    "backend_cursor": {"skill_must": ("`c` means `cursor`.",)},
    "skip_picker": {"skill_must": ("An explicit choice needs no re-approval on later tasks.",)},
    "backend_grok": {"skill_must": ("`g` means `grok`.",)},
    "picker_once": {"skill_must": ("Ask once",)},
    "backend_recorded": {"current_state_must": ("Backend: grok — argument",)},
    "no_failover": {"skill_must": ("Do not automatically switch backends.",)},
    "agent_not_cursor": {"skill_must": ("PATH `agent` as Cursor",)},
    "no_worktree_flag": {"skill_must": ("Do not pass `--worktree` to the worker.",)},
    "ruling_not_xhigh": {"skill_must": ("Architecture ambiguity is a ruling, not XHigh.",)},
    "confirm_even_if_one": {"skill_must": ("Do not auto-select the only CLI.",)},
    "stop_no_push_publish": {"skill_must": ("stop and return BLOCKED",)},
    "no_host_secrets": {"skill_must": ("Do not copy host credentials",)},
    "prepare_profile": {"dispatch_must": ("prepare_grok_sandbox.py",)},
    "replace_sandbox_value": {"dispatch_must": ("--sandbox-profile",)},
    "cleanup_after_worker_exit": {"dispatch_must": ("cleanup",)},
    "not_done": {"skill_must": ("Process exit 0 is not task completion.",)},
    "inspect_blocker": {
        "skill_must": ("BLOCKED, NEEDS_CONTEXT, a missing report, or an unclear result is not DONE.",)
    },
    "no_external_skills": {
        "worker_must": ("Do not read or invoke external skills, including Superpowers and waygent.",)
    },
    "no_full_plan": {"skill_must": ("The worker cannot read the plan",)},
    "no_mcp_tools": {"dispatch_must": ("search_tool,use_tool",)},
    "role_fail": {"skill_must": ("prohibited read (the plan, credentials, secrets) is FAIL",)},
    "report_discrepancy": {"skill_must": ("any discrepancy with the worker report",)},
    "not_clean_done": {"skill_must": ("Neither permits a clean DONE.",)},
    "role_unverified": {
        "skill_must": ("Missing or incomplete tool evidence is UNVERIFIED, never PASS.",)
    },
    "use_brief": {"skill_must": ("every brief carries the plan's run-wide constraints",)},
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
    "allowed_inspection": {"skill_must": ("Filename-only listings inside the worktree",)},
    "scope_deviations_none": {"skill_must": ("Scope deviations: none",)},
    "worker_trailer": {"worker_must": ("(`Waygent-Task: N`)",)},
    "worker_stops_processes": {"worker_must": ("Do not\nleave a process you started running",)},
    "progress_models": {
        "skill_must": ("impl=<backend>:<reported_model>/<effort>", "reviewer=<model>/<effort>"),
    },
    "observed_reviewer": {"skill_must": ("observed_model.py",), "dispatch_must": ("--agent-id <agentId>",)},
    "requested_marker": {"skill_must": ("Add `(requested)` after a value that no transcript or stream confirmed.",)},
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
        current_state = (SKILL / "references" / "current-state.md").read_text(encoding="utf-8")
        description = str(
            parse_skill_frontmatter(skill).get("description", "")
        )
        sources = {
            "current_state": current_state,
            "skill": skill,
            "dispatch": dispatch,
            "worker": worker,
            "description": description,
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

    def test_waygent_is_the_base_and_superpowers_is_gone(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("<skill-root>/../waygent/SKILL.md", skill)
        self.assertIn("resolve_backend.py", skill)
        self.assertIn("AskUserQuestion", skill)
        self.assertIn("Backend", skill)
        self.assertIn("NEEDS_CONTEXT", skill)
        self.assertIn("do not automatically switch", skill.lower())
        body = skill.split("\n---\n", 1)[1]
        for path in (
            SKILL / "references" / "dispatch.md",
            SKILL / "references" / "current-state.md",
        ):
            body += path.read_text(encoding="utf-8")
        for removed in (
            "Superpowers",
            "subagent-driven-development",
            "sdd-workspace",
            "review-package",
            "ledger",
            "fix round",
            "sddx-reviewer-xhigh",
            ".superpowers",
            "task-brief",
        ):
            self.assertNotIn(removed, body, removed)
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        self.assertIn("--disable-web-search", dispatch)

    def test_waygent_sections_sddx_relies_on_exist(self) -> None:
        waygent = (ROOT / "skills" / "waygent" / "SKILL.md").read_text(encoding="utf-8")
        for needed in (
            "## Start or resume",
            "## Per task",
            "## When a task fails",
            "## Final review, once",
            "## Models",
            "Waygent-Task:",
            ".waygent/",
            "guide.md",
        ):
            self.assertIn(needed, waygent, needed)

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

    def test_current_state_block_lives_in_waygent_progress(self) -> None:
        reference = SKILL / "references" / "current-state.md"
        text = reference.read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/current-state.md", skill)
        for marker in ("<!-- sddx:current:start -->", "<!-- sddx:current:end -->"):
            self.assertIn(marker, text)
            self.assertIn(marker, skill)
        self.assertIn("progress.md", skill)
        self.assertIn("progress.md", text)
        for field in (
            "Backend",
            "Orchestrator",
            "Task",
            "Worker session",
            "Worker effort",
            "Open findings",
            "Authorized scope",
            "Host checks pending",
            "Next plan",
            "Next action",
        ):
            self.assertIn(f"{field}:", text, field)
        self.assertIn("impl=grok:grok-4.7/high", text)
        self.assertIn("reviewer=claude-opus-5-5/high", text)

    def test_no_parallel_controller_state_file(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Do not create any other state file.", skill)
        self.assertEqual(
            sorted(path.name for path in (SKILL / "references").iterdir()),
            ["current-state.md", "dispatch.md", "worker-prompt.md"],
        )

    def test_helper_scripts_are_named_where_they_are_used(self) -> None:
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for name in (
            "extract_task.py",
            "observed_model.py",
            "resolve_backend.py",
            "prepare_grok_sandbox.py",
            "run_worker.py",
        ):
            self.assertTrue((SKILL / "scripts" / name).is_file(), name)
            self.assertIn(name, dispatch, name)
        self.assertIn("run_worker.py", skill)
        self.assertIn("resolve_backend.py", skill)
        self.assertIn("observed_model.py", skill)

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
        self.assertIn("reported_model", text)

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
        self.assertNotIn("does not kill the tree", fold(contract))

    def test_idle_timeout_is_on_every_face(self) -> None:
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        readme = (SKILL / "README.md").read_text(encoding="utf-8")
        readme_ko = (SKILL / "README.ko.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        fold = lambda value: re.sub(r"\s+", " ", value)
        faces = {
            "dispatch.md": fold(dispatch),
            "SKILL.md": fold(skill),
            "README.md": fold(readme),
            "README.ko.md": fold(readme_ko),
            "contract.md": fold(contract),
        }
        for name, text in faces.items():
            with self.subTest(face=name):
                self.assertIn("--idle-timeout", text)
                self.assertIn("the worker wrote no output for", text)
                self.assertNotIn("no output within", text)
                self.assertNotIn("7200", text)
        self.assertIn("the worker wrote no output for <N> seconds", faces["dispatch.md"])
        self.assertIn("the worker wrote no output for <N> seconds", faces["SKILL.md"])
        self.assertIn("the worker wrote no output for <N> seconds", faces["contract.md"])
        self.assertIn("It defaults to 900", faces["dispatch.md"])
        self.assertIn("defaults to 0, which waits without a bound", faces["dispatch.md"])
        self.assertIn("defaults to 900", faces["contract.md"])
        self.assertIn("defaults to 0", faces["contract.md"])
        self.assertIn("[--idle-timeout <seconds>]", dispatch)
        # 7.0.1 live check LT4: a backgrounded wait is as silent as a
        # foreground one, so the "run it in the background" advice is gone.
        for name in ("dispatch.md", "SKILL.md", "contract.md"):
            with self.subTest(face=name, rule="raise-above-duration"):
                self.assertNotIn("records right away", faces[name])
                self.assertIn("background", faces[name])
                self.assertRegex(faces[name], r"does not keep (the|an) attempt alive")
                self.assertIn("above that command's expected duration", faces[name])
        for name in ("dispatch.md", "contract.md"):
            with self.subTest(face=name, process="worker-server"):
                self.assertTrue("`worker-server`" in faces[name], f"worker-server missing from {name}")

    def test_foreground_wait_is_on_every_face(self) -> None:
        fold = lambda value: re.sub(r"\s+", " ", value)
        skill = fold((SKILL / "SKILL.md").read_text(encoding="utf-8"))
        dispatch = fold((SKILL / "references" / "dispatch.md").read_text(encoding="utf-8"))
        contract = fold((
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8"))
        self.assertIn("Never end your turn while a worker runs", skill)
        self.assertIn("run_worker.py wait", skill)
        self.assertIn("Never end your turn while an attempt runs.", dispatch)
        self.assertIn('run_worker.py" wait --attempt-dir', dispatch)
        self.assertIn("never ends its turn while a worker runs", contract)
        self.assertIn("$CLAUDE_CODE_SESSION_ID", skill)

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
        self.assertIn("bounded tools index for both the Cursor and Grok log shapes", fold(testing))

    def test_runner_limits_are_on_every_face(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        fold = lambda value: re.sub(r"\s+", " ", value)
        faces = {"dispatch.md": fold(dispatch), "contract.md": fold(contract)}
        shared = (
            # G1: an interrupted record's exit can be null.
            "could not be confirmed ended",
            "check `pid_alive` before cleanup",
            # G9: a foreground Grok shell is indexed only once it returns.
            "is not in the index yet",
            # G10: the limits the runner deliberately keeps.
            "build daemon",
            "end them by pid",
        )
        expected = {
            "dispatch.md": shared,
            # G6: one continuation-brief rule.
            "contract.md": shared + ("the previous `report.md` and the commits already made",),
        }
        for name, phrases in expected.items():
            for phrase in phrases:
                with self.subTest(face=name, phrase=phrase):
                    self.assertTrue(phrase in faces[name], f"{phrase!r} missing from {name}")
        paragraphs = [fold(part) for part in re.split(r"\n\s*\n", skill)]
        continuation = [part for part in paragraphs if "continuation brief" in part]
        self.assertEqual(len(continuation), 1)
        self.assertIn("`report.md`", continuation[0])
        self.assertIn("the commits already made", continuation[0])

    def test_improvised_rules_are_on_every_face(self) -> None:
        skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        dispatch = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        worker = (SKILL / "references" / "worker-prompt.md").read_text(encoding="utf-8")
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        fold = lambda value: re.sub(r"\s+", " ", value)
        skill, dispatch, worker, contract = map(fold, (skill, dispatch, worker, contract))
        # R6: no implementer XHigh trigger that every fix round meets.
        self.assertNotIn("High already failed review", skill)
        self.assertNotIn("High already failed review", contract)
        # R5: fix briefs start from the extracted constraints section.
        for text in (dispatch, contract):
            self.assertIn('--heading "Global Constraints"', text)
        # R7: report timing, provider session stores, host-check timing.
        self.assertIn("Write the report right after that commit", worker)
        self.assertIn("provider's session directories", worker)
        for text in (skill, dispatch):
            self.assertIn("before that task's review", text)
        self.assertIn("before that task's review", contract)
        # R7: attempt parent, no masking pipe, waiting and stopping.
        self.assertIn("$P/attempts/", dispatch)
        self.assertIn("`tail`", dispatch)
        for text in (dispatch, contract):
            self.assertIn("pkill -f", text)
            self.assertIn("ps -o ppid= -p", text)
        # The ppid route when the runner is already gone.
        self.assertIn("If that parent is pid 1", dispatch)
        self.assertIn("If that parent is pid 1", contract)
        changelog = fold((SKILL / "CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertIn("never the recorded worker pid unless its parent is pid 1", changelog)
        self.assertIn("previous attempt's `pid_alive` is true", skill)
        self.assertIn("signalling `run.json.pid` while its runner is alive", skill)

    def test_dispatch_opens_with_controller_procedure(self) -> None:
        text = (SKILL / "references" / "dispatch.md").read_text(encoding="utf-8")
        self.assertIn("## Controller procedure", text)
        self.assertIn("<repo root>/.waygent/<plan-slug>/", text)
        self.assertIn("--global-constraints", text)
        self.assertIn("## Runner already does this", text)
        procedure, _, rest = text.partition("## Runner already does this")
        self.assertTrue(rest)
        self.assertLess(procedure.find("## Controller procedure"), procedure.find("python3 \"<skill-root>/scripts/extract_task.py\""))
        for key in ("session_id", "timed_out", "pending_bytes", "pid_alive", "launch_failed"):
            self.assertIn(key, rest, key)

    def test_contract_owns_extraction_and_the_split_with_waygent(self) -> None:
        contract = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "contract.md"
        ).read_text(encoding="utf-8")
        contract = re.sub(r"\s+", " ", contract)
        self.assertIn("only when the user message contains `/sddx` or `$sddx`", contract)
        self.assertIn("`--global-constraints`", contract)
        self.assertIn("one worker never bundles several plan tasks", contract)
        self.assertIn("waygent owns", contract)
        self.assertIn("`reported_model`", contract)
        self.assertIn("observed_model.py", contract)
        self.assertNotIn("explicit external implementer request", contract)

    def test_readme_when_to_use_is_slash_dollar_only(self) -> None:
        korean = (SKILL / "README.ko.md").read_text(encoding="utf-8")
        english = (SKILL / "README.md").read_text(encoding="utf-8")
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
        self.assertIn("Keep one active plan at a time", text)
        self.assertIn("never pass the previous provider's session ID", text)

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
            "skills/sddx/README.ko.md",
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

    def test_no_claude_plugin_or_agent_definition_ships(self) -> None:
        self.assertFalse((SKILL / ".claude-plugin").exists())
        self.assertEqual(
            sorted(path.name for path in (SKILL / "agents").iterdir()),
            ["openai.yaml"],
        )
        registry = load_registry(ROOT / "products.toml")
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "sddx"
            shutil.copytree(SKILL, copied, ignore=shutil.ignore_patterns("__pycache__"))
            plugin_dir = copied / ".claude-plugin"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.json").write_text('{"name": "sddx"}\n', encoding="utf-8")
            self.assertIn("unexpected top-level file: .claude-plugin",
                          validate_product(copied, registry))

    def test_testing_doc_records_win32_fixtures_as_deleted(self) -> None:
        testing = (
            ROOT / "docs" / "maintainers" / "products" / "sddx" / "testing.md"
        ).read_text(encoding="utf-8")
        testing = re.sub(r"\s+", " ", testing)
        self.assertNotIn("to be deleted", testing)
        self.assertIn("The Win32 transport fixtures were deleted", testing)
        self.assertIn(
            'The Windows `.cmd` round-trip check (`skipUnless(os.name == "nt")`) was deleted.',
            testing,
        )
        self.assertIn("Windows is unsupported", testing)

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
