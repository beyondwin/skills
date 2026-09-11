# SDDx Reviewer Effort Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship SDDx 1.1.0 so native reviewers inherit the orchestrator's model and can be escalated to XHigh effort through a bundled agent definition, with no new install step.

**Architecture:** `skills/sddx` gains a `.claude-plugin/plugin.json`, which makes the already-linked `~/.claude/skills/sddx` directory load as a skills-dir plugin and bundle `agents/claude-code/sddx-reviewer-xhigh.md`. High reviews dispatch normally (inheriting model and session effort); XHigh reviews dispatch that `subagent_type`. No `model` argument is ever passed, which is how model inheritance is enforced. The uncommitted 1.0.2 work in the sibling worktree is absorbed into this same release.

**Tech Stack:** Markdown skill payload, YAML frontmatter, Python 3.11+ stdlib, `unittest`.

**Spec:** `docs/history/specs/2026-09-11-sddx-reviewer-effort-design.md`

## Global Constraints

- Product is `skills/sddx`. Target version is `1.1.0`. There is no 1.0.2 release.
- Python 3.11+ standard library only. No third-party imports in tests or scripts.
- Verification command, run from the repository root: `python3 scripts/verify.py --skill sddx`.
- Do NOT modify `products.toml`. The `sddx-contract` stage already globs `tests/products/sddx/test_*.py`; adding a stage breaks `tests/repository/test_verify.py` and `docs/users/*/verification.md`.
- Do NOT modify the shared installer block, the `<!-- sddx-local-links -->` marker, `docs/users/{ko,en}/install-local.md`, or `tests/repository/test_installation_contract.py`. The install stays two links.
- Do NOT change `supported_hosts`; it stays `["claude-code", "codex"]`.
- Do NOT change the registered support sentence `sddx: Claude Code and Codex supported for local or repository-based use.` It is asserted byte-for-byte in `tests/repository/test_public_docs.py`.
- Maintainer docs under `docs/maintainers/` are Korean prose. Payload `.md` files must contain no relative markdown links, no `/Users/` paths, and no credential-like tokens.
- Never pass a `model` argument when dispatching a reviewer.
- Work happens on branch `feat/sddx-reviewer-effort` in `.worktrees/sddx-reviewer-effort`. Do not push. Do not touch the sibling worktree's files except to read them.

---

### Task 1: Absorb the uncommitted 1.0.2 work

The sibling worktree `.worktrees/sddx-review-inheritance` (branch `codex/sddx-review-inheritance`) holds 15 modified files that never got committed: worker-context boundaries, tool-evidence completion checks, test wrapper exit reporting, and a first attempt at reviewer model/effort rules. All of it ships in 1.1.0. Absorb it verbatim first, so later tasks edit one coherent base instead of racing a second design.

**Files:**
- Modify (all via patch): `skills/sddx/SKILL.md`, `skills/sddx/README.md`, `skills/sddx/README.en.md`, `skills/sddx/CHANGELOG.md`, `skills/sddx/release.toml`, `skills/sddx/references/dispatch.md`, `skills/sddx/references/worker-prompt.md`, `docs/maintainers/products/sddx/{compatibility,contract,release,testing}.md`, `tests/products/sddx/{behavior-probes.md,cases.json,test_contract.py}`, `tests/repository/test_release_contract.py`

**Interfaces:**
- Consumes: nothing.
- Produces: a working tree at version `1.0.2` with a `## Reviewers` section in `SKILL.md`, seven new ids in `tests/products/sddx/cases.json`, and `EXPECTED["sddx"] == "1.0.2"` in `tests/repository/test_release_contract.py`. Task 4 rewrites the reviewer rule. Task 6 retargets the version.

- [ ] **Step 1: Confirm the source worktree is still where the plan expects and is still uncommitted**

```bash
git -C ../sddx-review-inheritance status --short --untracked-files=all
```

Expected: exactly 15 lines, each starting with ` M `, no `??` lines. If the output is empty the work was already committed or discarded — stop and report; do not invent the content.

- [ ] **Step 2: Capture the patch**

```bash
git -C ../sddx-review-inheritance diff > ../../.git/sddx-1.0.2-absorb.patch
wc -l ../../.git/sddx-1.0.2-absorb.patch
```

Expected: about 579 lines. Writing it under `.git/` keeps it out of the working tree and out of any commit.

- [ ] **Step 3: Verify the patch applies cleanly before touching anything**

```bash
git apply --check ../../.git/sddx-1.0.2-absorb.patch && echo APPLIES_CLEAN
```

Expected: `APPLIES_CLEAN`. Both worktrees are based on the same commit, so a conflict means the base moved — stop and report.

- [ ] **Step 4: Apply the patch**

```bash
git apply ../../.git/sddx-1.0.2-absorb.patch
git status --short
```

Expected: the same 15 modified files.

- [ ] **Step 5: Run the suite to confirm the absorbed state is self-consistent**

```bash
python3 scripts/verify.py --skill sddx
echo "EXIT=$?"
```

Expected: `EXIT=0`. The version moves in lockstep across `release.toml`, `SKILL.md` metadata, `CHANGELOG.md`, and `test_release_contract.py`, so a failure here means the patch was partial.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: absorb sddx worker evidence and reviewer rules from 1.0.2 work"
```

---

### Task 2: Allow a `.claude-plugin` payload directory for sddx

`scripts/lib/product_contract.py` rejects any top-level entry outside `ALLOWED_TOP_LEVEL`, so `skills/sddx/.claude-plugin/` would fail `validate_product` with `unexpected top-level file: .claude-plugin`. Allow it for sddx only, following the existing per-product precedent that allows `evidence` for `pre-sdd-review`.

**Files:**
- Modify: `scripts/lib/product_contract.py:238-240`
- Test: `tests/products/sddx/test_contract.py`

**Interfaces:**
- Consumes: `validate_product(skill_root, registry)` and `load_registry(path)`, both already imported in `tests/products/sddx/test_contract.py`.
- Produces: `validate_product` returns `[]` for an sddx tree containing `.claude-plugin/plugin.json`, and still reports `unexpected top-level file: .claude-plugin` for any other product. Task 3 depends on this.

- [ ] **Step 1: Write the failing test**

Add these imports at the top of `tests/products/sddx/test_contract.py` if they are not already present:

```python
import shutil
import tempfile
```

Add these two methods to `class SddxContractTests`:

```python
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
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.products.sddx.test_contract -v 2>&1 | tail -20`
Expected: `test_claude_plugin_directory_is_allowed_for_sddx` FAILS because `validate_product` returns `['unexpected top-level file: .claude-plugin']` instead of `[]`. The second test passes already.

- [ ] **Step 3: Write the minimal implementation**

In `scripts/lib/product_contract.py`, replace:

```python
    allowed_top_level = ALLOWED_TOP_LEVEL
    if skill_root.name == "pre-sdd-review":
        allowed_top_level = allowed_top_level | {"evidence"}
```

with:

```python
    allowed_top_level = ALLOWED_TOP_LEVEL
    if skill_root.name == "pre-sdd-review":
        allowed_top_level = allowed_top_level | {"evidence"}
    if skill_root.name == "sddx":
        allowed_top_level = allowed_top_level | {".claude-plugin"}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python3 -m unittest tests.products.sddx.test_contract -v 2>&1 | tail -5`
Expected: OK.

- [ ] **Step 5: Run the full sddx suite**

Run: `python3 scripts/verify.py --skill sddx`
Expected: exit 0.

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/product_contract.py tests/products/sddx/test_contract.py
git commit -m "feat: allow a claude-plugin payload directory for sddx"
```

---

### Task 3: Ship the plugin manifest and the XHigh reviewer definition

**Files:**
- Create: `skills/sddx/.claude-plugin/plugin.json`
- Create: `skills/sddx/agents/claude-code/sddx-reviewer-xhigh.md`
- Test: `tests/products/sddx/test_contract.py`

**Interfaces:**
- Consumes: the `.claude-plugin` allowance from Task 2.
- Produces: the agent name `sddx-reviewer-xhigh`, referenced by `SKILL.md` in Task 4 and by the probe rows in Task 5.

- [ ] **Step 1: Write the failing tests**

Add to `class SddxContractTests` in `tests/products/sddx/test_contract.py`:

```python
    def test_plugin_manifest_names_the_product(self) -> None:
        manifest = json.loads((SKILL / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "sddx")
        self.assertIn("description", manifest)
        self.assertIn("version", manifest)

    def test_claude_code_agents_are_closed_and_escalation_only(self) -> None:
        directory = SKILL / "agents" / "claude-code"
        definitions = sorted(path.name for path in directory.glob("*.md"))
        self.assertEqual(definitions, ["sddx-reviewer-xhigh.md"])
        self.assertEqual(
            sorted(path.name for path in directory.iterdir() if path.is_file()),
            ["sddx-reviewer-xhigh.md"],
        )
        frontmatter = parse_skill_frontmatter(
            (directory / "sddx-reviewer-xhigh.md").read_text(encoding="utf-8")
        )
        self.assertEqual(frontmatter.get("name"), "sddx-reviewer-xhigh")
        self.assertEqual(frontmatter.get("effort"), "xhigh")
        self.assertNotIn("model", frontmatter)
        disallowed = str(frontmatter.get("disallowedTools", ""))
        for tool in ("Edit", "Write", "NotebookEdit"):
            self.assertIn(tool, disallowed)
```

`json` and `parse_skill_frontmatter` are already imported in that file.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.products.sddx.test_contract -v 2>&1 | tail -20`
Expected: both new tests FAIL with `FileNotFoundError` — the files do not exist yet.

- [ ] **Step 3: Create the plugin manifest**

`skills/sddx/.claude-plugin/plugin.json`:

```json
{
  "name": "sddx",
  "description": "Superpowers SDD with an external implementer and native reviewer effort escalation.",
  "version": "1.1.0"
}
```

- [ ] **Step 4: Create the reviewer definition**

`skills/sddx/agents/claude-code/sddx-reviewer-xhigh.md`:

```markdown
---
name: sddx-reviewer-xhigh
description: SDDx XHigh review escalation. The SDDx orchestrator dispatches this explicitly. Not for use outside an SDDx run.
effort: xhigh
disallowedTools: Edit, Write, NotebookEdit
---

You are a reviewer in an SDDx run.

The dispatching prompt carries your role, your scope, and the review package
to read. Follow it. Do not edit files, do not implement, and do not widen the
review beyond the scope you were given.
```

No `model` key: omitting it is what makes the reviewer inherit the orchestrator's model.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python3 -m unittest tests.products.sddx.test_contract -v 2>&1 | tail -5`
Expected: OK.

- [ ] **Step 6: Run the full sddx suite**

Run: `python3 scripts/verify.py --skill sddx`
Expected: exit 0. This also proves the payload contract accepts the new files.

- [ ] **Step 7: Verify the definition actually loads from the real product files**

The spec's spike used throwaway probe files. This step repeats it with the shipped files, which is the only evidence that the plugin path works for this product.

```bash
ls -ld ~/.claude/skills/sddx
```

If that link points at the main checkout rather than this worktree, link this worktree's copy under a temporary name instead so the test reads the new files:

```bash
python3 - "$PWD/skills/sddx" "$HOME/.claude/skills/sddx-effort-check" <<'PY'
import os, sys
from pathlib import Path
source = Path(sys.argv[1]).resolve(strict=True)
target = Path(os.path.abspath(os.path.expanduser(sys.argv[2])))
if target.exists() or target.is_symlink():
    raise SystemExit("target already exists; inspect it before retrying")
target.symlink_to(source, target_is_directory=True)
print("linked")
PY
```

Then, from a directory outside this repository:

```bash
claude -p --agent sddx-reviewer-xhigh "Reply with exactly: SDDX_REVIEWER_LOADED"
```

Expected: `SDDX_REVIEWER_LOADED`. A `not found` error lists the available agents and means the plugin did not load — stop and report; do not proceed to Task 4 on an unproven mechanism.

Remove the temporary link whether or not it succeeded:

```bash
unlink ~/.claude/skills/sddx-effort-check
```

- [ ] **Step 8: Commit**

```bash
git add skills/sddx/.claude-plugin/plugin.json skills/sddx/agents/claude-code/sddx-reviewer-xhigh.md tests/products/sddx/test_contract.py
git commit -m "feat: bundle the sddx xhigh reviewer agent as a skills-dir plugin"
```

---

### Task 4: Replace the reviewer rule in SKILL.md

Task 1 brought in a `## Reviewers` section whose effort selection has no mechanism behind it on Claude Code. Replace its effort half with the agent-backed rule, keep its model-inheritance half, and harden the triggers.

**Files:**
- Modify: `skills/sddx/SKILL.md` (the `## Reviewers` section and the `## Red flags` list)

**Interfaces:**
- Consumes: the agent name `sddx-reviewer-xhigh` from Task 3.
- Produces: the ledger line formats `Task N review: sddx default — high` and `Task N review: sddx-reviewer-xhigh — <trigger>: <path>`, asserted by the probes in Task 5.

- [ ] **Step 1: Replace the effort half of the `## Reviewers` section**

Keep the first paragraph (model inheritance) exactly as Task 1 left it. Replace everything from `Select reviewer effort separately, including on re-review and final review:` through the end of that section with:

```markdown
Select reviewer effort separately, including on re-review and final review.
On Claude Code, High means dispatching the reviewer the way SDD already does,
with no `model` argument, so model and session effort are both inherited.
XHigh means dispatching `subagent_type: sddx-reviewer-xhigh`, still with no
`model` argument. Never pass a `model` override to a reviewer.

| Review scope | Effort |
| --- | --- |
| Clear requirements, local changes, straightforward integration | High |
| Changes to locking, ordering, or concurrently shared state; changes to an auth, permission, secret, or sandbox boundary; a round 4-5 re-review; a defect the reviews keep missing | XHigh |

Decide from the review-package stat, the task brief, the changed paths, and
the ledger. Do not read the diff body to pick effort; that is reviewing the
task yourself and it pollutes controller context. File count, line count, a
hard implementation, a short diff, and "this is the final review" are not
triggers. A re-review keeps the original defect's risk; a smaller diff alone
does not lower it.

Escalation is a floor, not a ceiling. If the session already runs at XHigh or
above, the plain dispatch already satisfies it, so do not use the escalation
agent and do not lower the session.

Record every review dispatch in the ledger. High is one line,
`Task N review: sddx default — high`. XHigh must name a trigger and a
referent, `Task N review: sddx-reviewer-xhigh — <trigger>: <path or brief
phrase>`. A trigger you cannot tie to a path is not a trigger; use High.

This section's effort escalation is Claude Code only. On Codex the definition
is absent, so report that the requested effort cannot be set and continue. A
missing definition never blocks the run.
```

- [ ] **Step 2: Extend the `## Red flags` list**

Append these lines to the existing bullet list, before its closing paragraph:

```markdown
- Reviewer XHigh because the diff is long
- Reviewer High because the diff is short
- Reviewer XHigh because the worker ran XHigh
- Final review XHigh because it is final
- Reviewer XHigh to be safe
- Reading the diff body to pick reviewer effort
- Re-dispatching at XHigh to clear `Cannot verify from diff`
- Lowering the reviewer model because effort is XHigh
- `sddx-reviewer-xhigh` in the ledger without a trigger and a path
- Passing a `model` override to a reviewer
- Escalating when the session already runs at XHigh or above
- Writing or editing an agent definition during a run
```

- [ ] **Step 3: Add a second closing sentence for the reviewer flags**

The list currently ends with `All of these mean: stop, restore the overlay, continue SDD with the external worker.` That remedy does not fit the reviewer flags. Add immediately after it:

```markdown
For the reviewer flags the remedy is different: stop, re-dispatch the review
with the correct definition and no `model` override, and record it in the
ledger.
```

- [ ] **Step 4: Verify**

Run: `python3 scripts/verify.py --skill sddx`
Expected: exit 0. `test_skill_does_not_copy_sdd_and_overrides_dispatch` scans every `.md` under the skill, so a stray Superpowers path in the new text would fail here.

- [ ] **Step 5: Commit**

```bash
git add skills/sddx/SKILL.md
git commit -m "feat: back reviewer effort selection with the xhigh agent definition"
```

---

### Task 5: Lock the behavior with cases and probes

**Files:**
- Modify: `tests/products/sddx/cases.json`
- Modify: `tests/products/sddx/test_contract.py` (the `CASE_IDS` tuple)
- Modify: `tests/products/sddx/behavior-probes.md`

**Interfaces:**
- Consumes: the ledger formats and rule wording from Task 4.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Append these seven ids to the end of the `CASE_IDS` tuple in `tests/products/sddx/test_contract.py`, after the ids Task 1 brought in:

```python
    "reviewer-large-mechanical-rename-high",
    "reviewer-small-lock-order-xhigh",
    "reviewer-worker-xhigh-does-not-escalate",
    "reviewer-input-validation-is-not-security-boundary",
    "reviewer-final-review-is-not-a-trigger",
    "reviewer-round-four-re-review-xhigh",
    "reviewer-session-already-xhigh-no-escalation",
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 -m unittest tests.products.sddx.test_contract.SddxContractTests.test_case_ids_match_spec -v`
Expected: FAIL — the tuple and `cases.json` no longer match.

- [ ] **Step 3: Add the matching cases**

Append these entries to the `cases` array in `tests/products/sddx/cases.json`, in the same order, keeping the file's existing one-object-per-line style:

```json
    {"id":"reviewer-large-mechanical-rename-high","request":"review package stat shows 42 files and 1900 changed lines; brief says identifier rename","expect":["review_effort_high","no_size_based_escalation"]},
    {"id":"reviewer-small-lock-order-xhigh","request":"review package stat shows 1 file and 24 changed lines; brief says lock acquisition order changed","expect":["review_effort_xhigh","ledger_trigger_and_path"]},
    {"id":"reviewer-worker-xhigh-does-not-escalate","request":"worker ran XHigh for implementation difficulty; diff only changes string formatting","expect":["review_effort_high","worker_effort_not_cited"]},
    {"id":"reviewer-input-validation-is-not-security-boundary","request":"diff adds a length check to a CLI argument; no auth, permission, or sandbox file changes","expect":["review_effort_high","no_security_boundary_claim"]},
    {"id":"reviewer-final-review-is-not-a-trigger","request":"whole-branch final review over five CRUD and documentation tasks","expect":["review_effort_high","inherits_orchestrator_model"]},
    {"id":"reviewer-round-four-re-review-xhigh","request":"entering fix round 4 with the same finding open after three scoped re-reviews","expect":["review_effort_xhigh","fresh_xhigh_worker"]},
    {"id":"reviewer-session-already-xhigh-no-escalation","request":"session effort is already max and a lock ordering change needs review","expect":["no_escalation_agent","session_effort_not_lowered"]}
```

Remember the comma on the line that was previously last.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 -m unittest tests.products.sddx.test_contract.SddxContractTests.test_case_ids_match_spec -v`
Expected: OK.

- [ ] **Step 5: Add the probe rows**

Append these rows to the scenario table in `tests/products/sddx/behavior-probes.md`, matching the existing Korean two-column style:

```markdown
| review package stat 42 파일 1,900줄, brief는 식별자 일괄 rename | `sddx-reviewer-xhigh`를 쓰지 않고 High로 dispatch한다. 파일 수나 줄 수를 승급 근거로 쓰지 않는다. |
| review package stat 1 파일 24줄, brief에 lock 획득 순서 변경 명시 | `sddx-reviewer-xhigh`로 dispatch하고 ledger에 trigger와 파일 경로를 적는다. diff가 짧다는 이유로 High를 택하지 않는다. |
| 같은 task의 worker가 구현 난이도로 XHigh, diff는 문자열 포맷 변경만 | High. worker effort를 reviewer effort의 근거로 인용하지 않는다. |
| diff가 CLI 인자에 길이 검증을 추가, 인증·권한·sandbox 파일 무변경 | High. 입력 검증 일반을 security boundary로 확대하지 않는다. |
| 최종 whole-branch review, task 5개, diff는 CRUD와 문서 | High. 모델은 오케스트레이터 상속. 최종 리뷰라는 사실을 승급 근거로 쓰지 않는다. |
| fix round 4 진입, 이전 3회 재리뷰에서 같은 finding이 open | fresh XHigh worker와 함께 재리뷰도 `sddx-reviewer-xhigh`로 dispatch한다. |
| 세션 effort가 이미 max이고 lock 순서 변경 리뷰 | 승급 정의를 쓰지 않는다. 세션 effort를 낮추지 않는다. |
```

- [ ] **Step 6: Record the measurement honestly**

Add this paragraph at the end of `tests/products/sddx/behavior-probes.md`:

```markdown
리뷰어 effort probe는 오케스트레이터가 어떤 `subagent_type`을 dispatch하고 ledger에
무엇을 적는지로 판정합니다. 문자열 포함 검사는 통과로 치지 않습니다. baseline과
안내 적용본을 각각 독립 문맥에서 받아 비교하며, baseline이 이미 같은 선택을 하면 그
행은 행동 변화의 증거가 아닙니다. Claude Code는 서브에이전트에 실제 적용된 effort를
관측시키지 않으므로 적용 effort는 `not_measured`입니다.
```

- [ ] **Step 7: Verify**

Run: `python3 scripts/verify.py --skill sddx`
Expected: exit 0.

- [ ] **Step 8: Commit**

```bash
git add tests/products/sddx/cases.json tests/products/sddx/test_contract.py tests/products/sddx/behavior-probes.md
git commit -m "test: lock reviewer effort selection cases and probes"
```

---

### Task 6: Retarget the release to 1.1.0 and update maintainer docs

**Files:**
- Modify: `skills/sddx/release.toml`
- Modify: `skills/sddx/SKILL.md` (frontmatter `metadata.version`)
- Modify: `skills/sddx/CHANGELOG.md`
- Modify: `tests/repository/test_release_contract.py` (`EXPECTED["sddx"]`)
- Modify: `docs/maintainers/products/sddx/release.md` (the hardcoded current-version sentence)
- Modify: `docs/maintainers/products/sddx/contract.md`
- Modify: `docs/maintainers/products/sddx/testing.md`
- Modify: `docs/maintainers/products/sddx/compatibility.md`

**Interfaces:**
- Consumes: everything from Tasks 1 through 5.
- Produces: the shipped 1.1.0 release.

- [ ] **Step 1: Find every place the version appears**

```bash
grep -rn "1\.0\.2" skills/sddx docs/maintainers/products/sddx tests | grep -v __pycache__
```

Expected: `release.toml`, `SKILL.md` metadata, the `CHANGELOG.md` heading, `tests/repository/test_release_contract.py`, and `docs/maintainers/products/sddx/release.md`. Every hit must become `1.1.0`; the `release.md` sentence is the one that is easy to miss.

- [ ] **Step 2: Retarget each of them to 1.1.0**

Change `version = "1.0.2"` to `version = "1.1.0"` in `skills/sddx/release.toml`; `version: "1.0.2"` to `version: "1.1.0"` in the `SKILL.md` frontmatter; `EXPECTED["sddx"]` to `"1.1.0"`; and the current-version sentence in `release.md`. In `skills/sddx/.claude-plugin/plugin.json` the version is already `1.1.0`.

- [ ] **Step 3: Rewrite the changelog entry**

Replace the `## 1.0.2 - 2026-09-11` heading and its body with:

```markdown
## 1.1.0 - 2026-09-11

### Added

- A bundled Claude Code reviewer agent raises review effort to XHigh without a new install step; the existing skill link carries it.

### Changed

- Native reviewers follow the active orchestrator model, and effort is High unless a named trigger in the diff calls for XHigh. This overrides generic SDD model selection.

### Fixed

- Worker dispatch supplies complete task context and repeats the boundary against retrieving the full plan, including through shell and search tools.
- Completion checks compare tool-call and results evidence with the worker's required scope-deviations report; missing evidence cannot count as verified compliance.
- Test reports preserve full wrapper commands and distinguish test exits from wrapper exits.
```

Leave the `## Unreleased` heading above it empty.

- [ ] **Step 4: Update `contract.md`**

In the reviewer section Task 1 introduced, replace the effort paragraph with this text:

```markdown
리뷰 effort는 세션 effort와 별도로 지정합니다. Claude Code에서 High는 SDD가 쓰던
방식 그대로 `model` 인자 없이 dispatch하는 것이고, XHigh는 `model` 인자 없이
`subagent_type`을 `sddx-reviewer-xhigh`로 지정하는 것입니다. 리뷰어에 `model`
오버라이드를 넘기지 않습니다.

XHigh trigger는 lock·순서·공유 상태 변경, auth·권한·secret·sandbox 경계 변경,
round 4–5 재리뷰, 반복해서 놓친 결함입니다. 판단 근거는 review-package stat, task
brief, 변경 파일 경로, ledger이며 diff 본문을 읽어 정하지 않습니다. 파일 수, 줄 수,
구현 난이도, 짧은 diff, 최종 리뷰라는 사실은 trigger가 아닙니다. 재리뷰는 원래
결함의 위험도를 유지합니다.

승급은 바닥이지 천장이 아닙니다. 세션 effort가 이미 XHigh 이상이면 승급 정의를
쓰지 않고 세션을 낮추지도 않습니다.

ledger에는 모든 리뷰 dispatch를 적습니다. High는 한 줄이고, XHigh는 trigger와
구체 경로를 함께 적습니다. 대지 못하면 High입니다.

정의는 `.claude-plugin/plugin.json`과 `agents/claude-code/`를 통해 skills-dir
플러그인으로 Claude Code에 전달됩니다. 설치 링크는 두 개 그대로이며 새 설치 단계를
추가하지 않습니다. Codex에는 정의가 없으므로 요청 effort를 지정할 수 없다고 보고한
뒤 진행하며, 정의 부재로 실행을 BLOCKED로 세우지 않습니다.
```

- [ ] **Step 5: Update `compatibility.md`**

Add this text to the section that currently describes `agents/openai.yaml`:

```markdown
`agents/openai.yaml`은 Codex 표시 메타데이터이며 선택적입니다.
`agents/claude-code/sddx-reviewer-xhigh.md`는 성격이 다릅니다. Claude Code 런타임
정의이고, skills-dir 플러그인 로딩을 통해 전달됩니다. 로딩은 배포되는 제품 파일로
한 번 확인했으며, 서브에이전트에 실제 적용된 effort는 `not_measured`입니다.

사용자 프로젝트의 `.claude/agents/`에 같은 이름의 정의가 있으면 그쪽이 우선합니다.
제품 접두사를 붙인 이름 외에 방어 수단이 없습니다.
```

- [ ] **Step 6: Update `testing.md`**

Add this section:

```markdown
## 리뷰어 effort 증거

공급자 없는 증거는 `tests/products/sddx/test_contract.py`의 세 검사입니다.
`.claude-plugin` 페이로드가 sddx에만 허용되는지, `plugin.json`이 제품명을
가리키는지, `agents/claude-code/`에 정의가 정확히 하나이고 `name`이 파일명과 같고
`effort`가 `xhigh`이며 `model` 키가 없고 `disallowedTools`가 Edit·Write·
NotebookEdit를 막는지 확인합니다.

라이브 확인은 하나입니다. 배포되는 제품 파일을 링크한 상태에서
`claude -p --agent sddx-reviewer-xhigh`를 실행해 정의가 로드되는지 봅니다. 이
확인은 로딩만 증명하며 적용된 effort를 증명하지 않습니다.

계약 검사는 파일이 존재한다는 것까지만 증명합니다. Claude Code가 skills-dir
플러그인에서 agents를 계속 싣는지는 증명하지 못하므로, 릴리스마다 위 라이브 확인을
반복합니다. 확인에 실패하면 정의가 조용히 사라진 상태이므로 릴리스를 멈춥니다.
```

- [ ] **Step 7: Verify the whole repository, not just sddx**

```bash
python3 scripts/verify.py
echo "EXIT=$?"
```

Expected: `EXIT=0`. The full suite is required here because Task 2 changed shared repository code in `scripts/lib/product_contract.py`.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "docs: release sddx 1.1.0 with reviewer effort escalation"
```
