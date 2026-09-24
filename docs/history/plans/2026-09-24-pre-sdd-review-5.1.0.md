# pre-sdd-review 5.1.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the review loop continue from closure instead of restarting discovery, finish small residuals in one invocation, and stop recording closures that never happened.

**Architecture:** Rule-text changes in `SKILL.md` and `references/reviewer-protocol.md`, mirrored in the maintainer contract, both READMEs, the case matrix, and `testing.md`. The recorder `evidence/evidence.py` gets widened pass ranges, two new observation anomalies, one narrowed anomaly, and loses the costless-repair counter. Record schema stays 4.

**Tech Stack:** Python 3 stdlib (`unittest`), Markdown, JSON.

**Spec:** `docs/history/specs/2026-09-24-pre-sdd-review-5.1.0-design.md`

## Global Constraints

- Version `5.1.0`; record schema stays `4`; handshake line `{"cli_version":"5.1.0","schema":4,"skill_name":"pre-sdd-review"}` + LF.
- No new record field, no schema 5, no closure-only input schema, no cache.
- Anomalies never change a verdict and `finish` never rejects a record for an anomaly.
- The recorder stays optional; without a recorded run for the plan, continuation is unavailable and discovery runs.
- Commit no private source text, provider receipts, or model responses. Live model calls only in Task 6, which the user explicitly requested; Tasks 1-5 stay offline.
- Run all commands from the worktree root `/Users/kws/source/private/skills/.claude/worktrees/pre-sdd-review-5.1.0`.
- A declared set has several faces (memory: one-face defect shape). Before editing any name, `grep -rn` it across `skills/pre-sdd-review/`, `docs/maintainers/products/pre-sdd-review/`, `tests/products/pre-sdd-review/`, `scripts/`, `tests/repository/` and fix every face in the same commit.
- Pinned text: `tests/products/pre-sdd-review/test_contract.py` pins exact phrases, whole-document SHA-256 of `SKILL.md` and `references/reviewer-protocol.md`, a canonical digest of `contract.md` and 12 of its `###` subsections, and the whole-file digest of `testing.md`. After editing any of those documents, refresh the constants with the helper below and paste its output into `test_contract.py`.

Digest helper (prints current value and whether it matches the pinned constant):

```bash
python3 - <<'EOF'
import hashlib, sys
from pathlib import Path
sys.path.insert(0, 'tests/products/pre-sdd-review'); sys.path.insert(0, '.')
import test_contract as t
S = Path('skills/pre-sdd-review'); M = Path('docs/maintainers/products/pre-sdd-review')
for rel, pinned in t.INSTRUCTION_DOCUMENT_SHA256.items():
    now = hashlib.sha256((S / rel).read_bytes()).hexdigest(); print('INSTRUCTION', rel, now, now == pinned)
c = (M / 'contract.md').read_text(encoding='utf-8')
now = t.canonical_digest(c); print('MAINTAINER_CANONICAL_DIGEST', now, now == t.MAINTAINER_CANONICAL_DIGEST)
for heading, pinned in t.MAINTAINER_CANONICAL_SUBSECTION_DIGESTS:
    now = t.canonical_digest(t.subsection(c, heading)); print('SUBSECTION', heading, now, now == pinned)
for name, pinned in (('testing', t.TESTING_CANONICAL_DIGEST), ('compatibility', t.COMPATIBILITY_CANONICAL_DIGEST), ('release', t.RELEASE_CANONICAL_DIGEST)):
    now = t.whole_document_digest((M / f'{name}.md').read_text(encoding='utf-8')); print(name.upper(), now, now == pinned)
EOF
```

Product check: `python3 scripts/verify.py --skill pre-sdd-review` (expected tail: `OK`, exit 0). Recorder tests alone: `cd tests/products/pre-sdd-review/evidence && python3 -m unittest -q test_evidence test_hardening`.

## Review Focus

- A 5.0.0-shaped record (`review_passes: 3`, `repair_passes: 2`, every finding `repaired` with `repair_pass` 1 or 2) must still read cleanly with no new anomaly. Test in Task 1.
- Range edges: `repair_passes` 3 and `review_passes` 4 and `finding.repair_pass` 3 accepted; 4, 5, 4 rejected as `schema-invalid`. Test in Task 1.
- A `BLOCKER` that is `blocked-by-authority` or `repaired` must not raise `open_blocker_without_blocked_verdict`; only `unresolved`/`partially-closed` under a non-`BLOCKED` verdict does. Test in Task 1.
- A review-only or zero-repair run (`repair_passes: 0`, `review_passes: 1`) must not raise `repair_after_last_review`. Test in Task 1.
- A user who commits the repaired documents between invocations still gets a continuation (the predicate is `git diff --name-only <head_end> HEAD`, not `HEAD` equality). Pinned by case `continuation-after-committed-docs` in Task 3.

---

### Task 1: Recorder: pass ranges, anomalies, costless counter

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py` (lines ~498, ~536-537, `observation_anomalies` ~569-595, `summary` ~915-1006)
- Modify: `skills/pre-sdd-review/evidence/README.md` (lines ~72, ~76, ~121-123)
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md` (recorder paragraph containing ``0..2, `0`은 패스를 먹지 않은 수리``)
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`, `tests/products/pre-sdd-review/test_contract.py` (digests only)

**Interfaces:**
- Produces: anomaly names `repair_after_last_review` and `open_blocker_without_blocked_verdict` in `observation_anomalies(record)`, in `finish` output `anomalies`, and as keys of `summary["anomalies"]`. `summary["counts"]` no longer has `costless_repairs`. Later tasks cite these names in prose.

- [ ] **Step 1: Write the failing tests** — append to the class that holds `test_finish_preserves_contradictions_as_anomalies` in `test_evidence.py` (it has `self.home`, `self.repo`, `self.skill`, `self.run_id` set up; reuse the same `setUp`):

```python
    def test_new_anomalies_fire_only_on_their_contradiction(self) -> None:
        cases = {
            "repair-last": (finish_payload(verdict="REVISE", review_passes=1, repair_passes=1, findings=[finding(status="unresolved", repair_pass=1)]), ["repair_after_last_review"]),
            "open-blocker-revise": (finish_payload(verdict="REVISE", review_passes=2, repair_passes=1, findings=[finding(severity="BLOCKER", status="unresolved", repair_pass=1)]), ["open_blocker_without_blocked_verdict"]),
            "partial-blocker-revise": (finish_payload(verdict="REVISE", review_passes=2, repair_passes=1, findings=[finding(severity="BLOCKER", status="partially-closed", repair_pass=1)]), ["open_blocker_without_blocked_verdict"]),
            "blocker-by-authority": (finish_payload(verdict="BLOCKED", block_reason="decision", findings=[finding(severity="BLOCKER", status="blocked-by-authority", repair_pass=None)]), []),
            "blocker-repaired-ready": (finish_payload(review_passes=2, repair_passes=1, findings=[finding(severity="BLOCKER")]), []),
            "zero-repair": (finish_payload(), []),
            "v5-0-shape": (finish_payload(review_passes=3, repair_passes=2, findings=[finding(id="PSDR-001", repair_pass=1), finding(id="PSDR-002", repair_pass=2)]), []),
        }
        for name, (payload, expected) in cases.items():
            with self.subTest(name=name):
                run_id = start(self.home, self.repo, self.skill)
                code, out, err = finish(self.home, self.repo, run_id, payload)
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(json.loads(out)["anomalies"], expected)

    def test_an_applied_but_unclosed_repair_is_not_repair_without_repaired_finding(self) -> None:
        payload = finish_payload(verdict="REVISE", review_passes=2, repair_passes=1, findings=[finding(status="unresolved", repair_pass=1)])
        code, out, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["anomalies"], [])

    def test_widened_pass_ranges_accept_the_residual_pass(self) -> None:
        accepted = finish_payload(review_passes=4, repair_passes=3, findings=[finding(repair_pass=3)])
        code, _, err = finish(self.home, self.repo, self.run_id, accepted)
        self.assertEqual((code, err), (0, ""))
        for name, payload in {
            "repair-passes-4": finish_payload(review_passes=4, repair_passes=4),
            "review-passes-5": finish_payload(review_passes=5, repair_passes=3),
            "finding-repair-pass-4": finish_payload(review_passes=4, repair_passes=3, findings=[finding(repair_pass=4)]),
        }.items():
            with self.subTest(name=name):
                run_id = start(self.home, self.repo, self.skill)
                code, _, err = finish(self.home, self.repo, run_id, payload)
                self.assertEqual((code, error_code(err)), (2, "schema-invalid"))
```

- [ ] **Step 2: Run to verify they fail**

Run: `cd tests/products/pre-sdd-review/evidence && python3 -m unittest -q test_evidence 2>&1 | tail -5`
Expected: FAIL/ERROR in the three new tests (unknown anomaly names absent, `repair_without_repaired_finding` present, rp=3 rejected).

- [ ] **Step 3: Implement in `evidence.py`**

Ranges:

```python
        _integer(repair_pass, "finding.repair_pass", 0, 3)
```
```python
    review_passes = _integer(payload["review_passes"], "review_passes", 1, 4)
    repair_passes = _integer(payload["repair_passes"], "repair_passes", 0, 3)
```

In `observation_anomalies`, replace the `repair_without_repaired_finding` entry and add two entries (keep the dict otherwise unchanged; the function sorts names):

```python
        "repair_without_repaired_finding": bool(record["repair_passes"])
        and not any(item["repair_pass"] is not None and item["repair_pass"] >= 1 for item in findings),
        "repair_after_last_review": record["repair_passes"] > 0
        and record["repair_passes"] >= record["review_passes"],
        "open_blocker_without_blocked_verdict": record["verdict"] != "BLOCKED"
        and any(
            item["severity"] == "BLOCKER" and item["status"] in ("unresolved", "partially-closed")
            for item in findings
        ),
```

In `summary`, add the two keys to the `anomalies` dict literal right after `"repair_without_repaired_finding": [],`:

```python
        "repair_after_last_review": [],
        "open_blocker_without_blocked_verdict": [],
```

Delete the costless counter: the `costless_repairs = 0` line, the `if item["repair_pass"] == 0 and item["status"] == "repaired": costless_repairs += 1` block (keep the surrounding loop intact), and the `"costless_repairs": costless_repairs,` entry in `counts`.

- [ ] **Step 4: Fix existing tests the new anomaly touches**

`repair_after_last_review` fires whenever a payload sets `repair_passes: N > 0` and leaves the default `review_passes: 1`. For every existing `finish_payload(...)` in `test_evidence.py` and `test_hardening.py` that sets `repair_passes=N` (N ≥ 1) without `review_passes`, add `review_passes=N+1`. Find them with: `grep -n "repair_passes=[1-9]" tests/products/pre-sdd-review/evidence/*.py | grep -v review_passes`. Known exact-list assertions that need it: in `test_finish_preserves_contradictions_as_anomalies` the `revise-without-unresolved`, `repair-without-repaired`, `repair-pass-exceeds` payloads; `test_review_only_preserves_repair_passes_as_anomaly`.

Delete `test_summary_counts_costless_repairs`. In `test_summary_on_empty_home_has_exact_keys` delete the `costless_repairs` assertion and add `"repair_after_last_review": [], "open_blocker_without_blocked_verdict": [],` after `"repair_without_repaired_finding": [],` in the expected `anomalies` dict. Rename `test_finish_accepts_a_costless_repair_and_a_partial_closure` → `test_finish_accepts_an_intake_repair_and_a_partial_closure` and `test_a_costless_repair_clears_the_document_change_anomaly` → `test_an_intake_repair_clears_the_document_change_anomaly` (bodies unchanged).

- [ ] **Step 5: Update recorder docs**

`evidence/README.md`: `` `review_passes` (1–3), `repair_passes` (0–2)`` → `` `review_passes` (1–4), `repair_passes` (0–3)``; ``0–2, where `0` means the repair consumed no pass`` → ``0–3, where `0` marks a pre-pass ledger or machine-check repair``; delete the sentence beginning ``counts.costless_repairs` counts findings`` through ``the run's `repair_passes`.`` and keep the following sentence ``Historical records do not form `chains` ...``.

`contract.md` recorder paragraph: ``(`null` 또는 0..2, `0`은 패스를 먹지 않은 수리이고 `null`은
미해결 발견입니다)`` → ``(`null` 또는 0..3, `0`은 사전 패스의 원장·기계 점검 수리이고 `null`은
이 호출이 수리하지 않은 발견입니다)``.

- [ ] **Step 6: Refresh digests and run**

Run the digest helper; paste every `False` value into `test_contract.py` (`MAINTAINER_CANONICAL_DIGEST` and any changed subsection). Then run `python3 scripts/verify.py --skill pre-sdd-review`.
Expected: exit 0.

- [ ] **Step 7: Commit**

```bash
git add skills/pre-sdd-review/evidence docs/maintainers/products/pre-sdd-review/contract.md tests/products/pre-sdd-review
git commit -m "fix(pre-sdd-review): observe repair-last and open-blocker runs, widen passes for the residual pass"
```

---

### Task 2: Pass accounting, residual pass, open BLOCKER, scope freeze

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md` (Default mode ~221-310, Verdict and handoff ~364-385, Red flags)
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md` (기본 흐름 ~158-190, `### Verdicts`, reuse paragraph ~226-230, `### Contract`)
- Modify: `skills/pre-sdd-review/README.md`, `skills/pre-sdd-review/README.en.md`
- Modify: `tests/products/pre-sdd-review/cases.json`, `docs/maintainers/products/pre-sdd-review/testing.md` (`### Case inventory`)
- Test: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: anomaly names from Task 1.
- Produces: SKILL phrases later tasks keep intact: "`repair_passes` counts every repair pass the controller applied", "At most two repair passes are permitted, plus one residual pass", "An open `BLOCKER`", "dispatch no reviewer and make no repair".

- [ ] **Step 1: Update the pins first (failing tests)** in `test_contract.py`:
  - `test_default_is_review_repair_and_re_review`: `"At most two repair passes"` → `"At most two repair passes are permitted, plus one residual pass"`.
  - `test_unreleased_convergence_contract_has_one_bounded_terminal_loop`: replace the `repair_passes counts only passes...` assertion with `self.assertIn("`repair_passes` counts every repair pass the controller applied", skill)`; replace the contract assertion with `self.assertIn("`repair_passes`는 컨트롤러가 적용한 수리 패스를 모두 셉니다", contract)`; add `self.assertIn("An open `BLOCKER`, including one still `partially-closed`, forces `BLOCKED`", skill)`, `self.assertIn("dispatch no reviewer and make no repair", skill)`, `self.assertIn("열린 `BLOCKER`가 있으면", contract)`.
  - `README_CONTRACT`: `("repair-passes", ("at-most-two", "costless-repairs-uncounted"))` → `("repair-passes", ("at-most-two", "residual-pass-once", "applied-passes-counted"))`.
  - `CASE_IDS`: remove `"costless-repair-consumes-no-pass"`; append `"residual-pass-closes-small-remainder"`, `"open-blocker-forces-blocked"`, `"repair-last-no-ready"`, `"unanswered-decision-no-redispatch"`, `"three-new-decisions-return-to-design"`. Change `self.assertEqual(len(CASE_IDS), 41)` → `45`.
  - In `test_evidence_cases_cover_recorded_failure_review_only_blocked_and_handoff`: `cases["repair-pass-accounting"]` expected → `("repair_passes_count_applied_passes", "no_copied_repair_pass", "unresolved_repair_pass_null")`; add:

```python
        self.assertEqual(cases["residual-pass-closes-small-remainder"], ("residual_pass", "closure_of_those_ids_only", "new_shape_ends_invocation"))
        self.assertEqual(cases["open-blocker-forces-blocked"], ("BLOCKED", "no_revise_with_open_blocker"))
        self.assertEqual(cases["repair-last-no-ready"], ("no_ready_after_repair", "closure_or_revise"))
        self.assertEqual(cases["unanswered-decision-no-redispatch"], ("reprint_checkpoint", "no_reviewer_dispatch", "no_repair"))
        self.assertEqual(cases["three-new-decisions-return-to-design"], ("BLOCKED", "return_to_design"))
```
  - Red flags list: add `"Dispatch a reviewer while the plan waits on an unanswered user decision"` and `"Return `READY` when the last action was a repair"`.

Run: `python3 -m unittest -q tests/products/pre-sdd-review/test_contract.py 2>&1 | tail -3` — Expected: FAIL.

- [ ] **Step 2: Edit `SKILL.md`**

Line ~221: `One invocation has one discovery stage, at most two repair passes, and a` / `terminal scoped closure.` → `One invocation has one discovery stage, at most two repair passes plus one` / `residual pass, and a terminal scoped closure.`

Replace the block from `` `repair_passes` counts only passes that produced at least one `repaired` finding.`` through `repair with `repair_pass: 0`. Group them into one pass.` with:

```text
`repair_passes` counts every repair pass the controller applied, whether or not
its closure closed anything. Pre-pass ledger and machine-check repairs keep
`repair_pass: 0` and are not a pass. Write `repaired` only when a closure
reviewer closed that record; a record the controller repaired but no closure
reviewer closed stays `unresolved`. Never return `READY` when the last action
was a repair: close it with one more closure review, or return `REVISE`.
```

Replace `A finding still `partially-closed` at the end counts as unresolved for the verdict and forces `REVISE`. A record's `repair_pass` is the pass that last changed its status.` with:

```text
A finding still `partially-closed` at the end counts as unresolved for the
verdict: it forces `REVISE`, or `BLOCKED` when it is a `BLOCKER`. A record's
`repair_pass` is the last pass that repaired it.
```

Replace `re-review. At most two repair passes are permitted. If a material issue remains,` / `return `REVISE` with its evidence; do not downgrade it to finish the loop.` with:

```text
re-review. At most two repair passes are permitted, plus one residual pass:
when everything the second closure leaves open is an original record,
`IMPORTANT`, at most two records, each with a recorded fix at one site within
the reviewed documents, and the repair-impact map is empty, repair those
records once more and dispatch one fresh closure reviewer for those IDs only.
A new defect shape found there ends the invocation. If a material issue
remains, return `REVISE` with its evidence; do not downgrade it to finish the
loop.
```

In `## Verdict and handoff`, after the sentence ending `a `BLOCKED` run with a null `block_reason` is an anomaly.` add:

```text
An open `BLOCKER`, including one still `partially-closed`, forces `BLOCKED`,
never `REVISE`.
```

After the paragraph that starts `Do not automatically start another invocation after `REVISE` or `BLOCKED`.` add:

```text
When this plan's previous run is `BLOCKED` on a user decision that no
authority document records yet, dispatch no reviewer and make no repair: print
the same checkpoint and stop. Other plans continue. When this run would end
`BLOCKED` on a new product decision and the two preceding runs of this plan in
the recorder's chain did too, the handoff sends the design back to be finished
with all remaining decisions at once, and says the next invocation should wait
for that. Without a chain, report the count you know and do not stop on it.
```

Red flags: append two bullets:

```text
- Dispatch a reviewer while the plan waits on an unanswered user decision
- Return `READY` when the last action was a repair
```

- [ ] **Step 3: Edit `contract.md`**
  - `한 호출은 발견 단계 한 번과 수정 최대 두 번, 범위 제한 재검토로` → `한 호출은 발견 단계 한 번과 수정 최대 두 번과 작은 잔여 패스 한 번, 범위 제한 재검토로`.
  - Replace `` `repair_passes`는 실제로 `repaired` 발견이 나온 패스만`` / ``셉니다. `partially-closed`로 남은 발견은 판정에서 미해결로 계산되어`` / `` `REVISE`를 강제합니다.`` with `` `repair_passes`는 컨트롤러가 적용한 수리 패스를 모두 셉니다. `repaired`는 종결 검토자가 닫은 기록에만 씁니다. 마지막 동작이 수리이면 `READY`를 내지 않습니다. `partially-closed`로 남은 발견은 판정에서 미해결로 계산되어 `REVISE`를 강제하고, `BLOCKER`이면 `BLOCKED`입니다.``
  - `수정 패스는 최대 두` / `번입니다.` → `수정 패스는 최대 두 번입니다. 두 번째 종결 뒤 원래 기록의 `IMPORTANT` 2건 이하가 한 자리 수정으로 남고 영향 표가 비어 있으면, 그 ID만 한 번 더 고치고 종결합니다.`
  - `### Verdicts` BLOCKED bullet: append `열린 `BLOCKER`가 있으면 `BLOCKED`입니다.` to its end.
  - After `` `blocked`인 run의 인계는 재사용하지 않습니다.`` (end of the paragraph with `승인 요청 하나로 묶습니다`) add: `직전 run이 아직 권위 문서에 없는 사용자 결정 때문에 `BLOCKED`이면 검토자를 부르지 않고 수리하지 않으며 같은 체크포인트를 다시 보여 줍니다. 같은 계획의 연속 세 run이 새 제품 결정으로 `BLOCKED`이면 인계가 설계를 되돌려 보내 남은 결정을 한 번에 정하게 합니다.`
  - `### Contract`: `- `repair-passes`: `at-most-two`, `costless-repairs-uncounted`` → `- `repair-passes`: `at-most-two`, `residual-pass-once`, `applied-passes-counted``.

- [ ] **Step 4: Edit READMEs** (the first sentence is an order anchor; keep it verbatim)
  - `README.md`: after `수정 패스는 최대 두 번입니다.` insert ` 원래 지적의 작은 잔여만 남으면 한 번 더 고치고 그 지적만 다시 봅니다.` After the verdict bullets' `BLOCKED` line leave text; after `이상이 판정을 바꾸지는 않습니다.` add a new sentence ` 마지막 동작이 수리이면 `READY`가 아니고, 열린 `BLOCKER`가 있으면 `BLOCKED`입니다.`
  - `README.en.md`: after `There are at most two repair passes.` insert ` One residual pass follows when only a small remainder of the original findings is left.`; after `Anomalies do not change the verdict.` add ` A run whose last action was a repair is never `READY`, and an open `BLOCKER` makes it `BLOCKED`.`

- [ ] **Step 5: Edit `cases.json` and `testing.md`**

In `cases.json` delete the `costless-repair-consumes-no-pass` object; set `repair-pass-accounting`'s `expect` to `["repair_passes_count_applied_passes", "no_copied_repair_pass", "unresolved_repair_pass_null"]`; append:

```json
    {"id": "residual-pass-closes-small-remainder", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md whose second closure leaves one original IMPORTANT finding with a recorded one-site fix", "expect": ["residual_pass", "closure_of_those_ids_only", "new_shape_ends_invocation"]},
    {"id": "open-blocker-forces-blocked", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md whose closure leaves a BLOCKER partially-closed", "expect": ["BLOCKED", "no_revise_with_open_blocker"]},
    {"id": "repair-last-no-ready", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md whose last action was a repair no closure reviewer saw", "expect": ["no_ready_after_repair", "closure_or_revise"]},
    {"id": "unanswered-decision-no-redispatch", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md after a BLOCKED run whose user decision is not yet in any authority document", "expect": ["reprint_checkpoint", "no_reviewer_dispatch", "no_repair"]},
    {"id": "three-new-decisions-return-to-design", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md whose two preceding runs each ended BLOCKED on a new product decision and whose closure finds another", "expect": ["BLOCKED", "return_to_design"]}
```

Keep the file's existing indentation style (reformat with `python3 -c "import json;p='tests/products/pre-sdd-review/cases.json';d=json.load(open(p));open(p,'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')"` only if the original is `indent=2`; check with `head -5` first). In `testing.md` `### Case inventory`, delete the `- `costless-repair-consumes-no-pass`` line and append the five new ids as `- `<id>`` lines in the same order.

- [ ] **Step 6: Refresh digests, run, commit**

Run the digest helper, paste changed values (`SKILL.md` instruction digest, maintainer digest, `### Verdicts` subsection, `testing` digest). Run `python3 scripts/verify.py --skill pre-sdd-review` — Expected: exit 0. Then `grep -rn "costless" skills/pre-sdd-review docs/maintainers/products/pre-sdd-review tests/products/pre-sdd-review | grep -v CHANGELOG` — Expected: no output.

```bash
git add skills/pre-sdd-review docs/maintainers/products/pre-sdd-review tests/products/pre-sdd-review
git commit -m "feat(pre-sdd-review): count applied passes, add the residual pass, freeze undecided plans"
```

---

### Task 3: Continuation and focused-role degraded

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md` (Optional local evidence ~141-152, Select reviewers ~203-217, new `###` at end of Default mode, Red flags)
- Modify: `skills/pre-sdd-review/references/reviewer-protocol.md` (`### Closure dispatch`)
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md` (`### Degraded reasons` paragraph, reuse paragraph ~226-230, recorder paragraph ~243-247, `### Contract`)
- Modify: `skills/pre-sdd-review/README.md`, `skills/pre-sdd-review/README.en.md`
- Modify: `tests/products/pre-sdd-review/cases.json`, `docs/maintainers/products/pre-sdd-review/testing.md`
- Test: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: Task 2 phrases (unchanged here).
- Produces: SKILL heading `### Continuation after `REVISE` or `BLOCKED`` and phrase "A continuation replaces discovery with closure".

- [ ] **Step 1: Update pins first**
  - `test_unreleased_convergence_contract_has_one_bounded_terminal_loop`: add `self.assertIn("A continuation replaces discovery with closure", skill)`, `self.assertIn("git diff --name-only <git.head_end> HEAD", skill)`, `self.assertIn("Without a recorded run for this plan there is no continuation", skill)`, `self.assertIn("that reason alone does not bar reuse or continuation", skill)`, `self.assertIn("stand in for the verbatim records", protocol)`, `self.assertIn("이어 검토", contract)`.
  - README reuse pins (`test_bilingual_readmes_lock_primary_input_mutation_and_review_semantics`, around lines 1615-1621): Korean `"`full`인 run의 인계만 재사용하며, `degraded`나 `blocked`인 run의 인계는 재사용하지 않습니다."` → `"`full`인 run과 사유가 `focused-role-not-obtained`뿐인 `degraded` run의 인계만 재사용하며, 다른 `degraded`나 `blocked`인 run의 인계는 재사용하지 않습니다."`; English → `"Only a `full` run's handoff, or a `degraded` run's whose only reason is `focused-role-not-obtained`, is reused; any other `degraded` or `blocked` run's handoff is never reused."`
  - Red flags: `"Reuse a handoff from a `degraded` run"` → `"Reuse a handoff from a `degraded` run with any reason besides `focused-role-not-obtained`"`; add `"Run a fresh discovery when a continuation applies"`.
  - `README_CONTRACT`: `("handoff", ("unresolved-packet", "full-execution-only"))` → `("handoff", ("unresolved-packet", "reusable-execution-only"))`; insert after it `("continuation", ("docs-only-diff", "closure-first", "recorded-run-required"))`.
  - `CASE_IDS`: append `"continuation-skips-discovery"`, `"continuation-after-committed-docs"`, `"continuation-needs-docs-only-diff"`, `"continuation-needs-recorded-run"`, `"focused-only-degraded-continues"`; count `45` → `50`. Add to the cases test:

```python
        self.assertEqual(cases["continuation-skips-discovery"], ("continuation", "closure_first", "prior_finding_ids", "no_discovery"))
        self.assertEqual(cases["continuation-after-committed-docs"], ("continuation", "docs_only_diff_predicate"))
        self.assertEqual(cases["continuation-needs-docs-only-diff"], ("fresh_discovery",))
        self.assertEqual(cases["continuation-needs-recorded-run"], ("fresh_discovery",))
        self.assertEqual(cases["focused-only-degraded-continues"], ("continuation", "no_focused_role", "degraded_focused_role_not_obtained"))
```
  - `degraded-handoff-not-reused` keeps its id and `expect`; its `request` changes (Step 5).

Run: `python3 -m unittest -q tests/products/pre-sdd-review/test_contract.py 2>&1 | tail -3` — Expected: FAIL.

- [ ] **Step 2: Edit `SKILL.md` Optional local evidence**

Replace from `Never reuse a handoff whose `execution` is` through `evidence. Otherwise call `start` before semantic review with the skill root,` with:

```text
Never reuse a handoff whose `execution` is `blocked`: a `blocked` run
dispatched no reviewer, so re-run the input gates (`**Spec:**` resolution and
the required implementation base) and call `start` if they pass. A run is
reusable when its `execution` is `full`, or `degraded` with
`focused-role-not-obtained` as its only reason; any other `degraded` run's
handoff is never reusable, so call `start` for a fresh full review. For a
reusable run, reuse the prior handoff without a new review only when
`plan.sha_end` and `design.sha_end` match the current documents,
`git.head_end` matches the current `HEAD`, and the outer request does not ask
for a re-review or name changed authority or repository evidence. When only
the documents changed, take the continuation in the default mode. Otherwise
call `start` before semantic review with the skill root,
```

(Keep the pinned phrase "Never reuse a handoff whose `execution` is `blocked`".)

- [ ] **Step 3: Edit `SKILL.md` Select reviewers** — replace the paragraph from `Across the entire invocation, use at most two review roles:` through `A reused role is `execution=degraded`.` with:

```text
Across the entire invocation, use at most two review roles: one primary role
and, when triggered, one focused risk role. The focused risk role is required
only in an invocation that runs discovery; closure rounds and continuations do
not dispatch it. A fresh re-review may replace the agent in either role, but
it does not add a review role or broaden the triggered risk class. Evidence
`reviewer_count` records these logical roles, not cumulative fresh agent
calls, and evidence `reviewers` counts distinct agents obtained for the
logical roles, not intended roles. If a fresh independent primary reviewer
cannot be obtained, return `BLOCKED`. Do not use the controlling agent as a
substitute independent primary and do not run a short degraded round in its
place. If the host can supply only k fresh agents, run discovery in waves of
k. Do not reuse an agent across plans to fill a wave. Do not bind a later
`READY` to a preceding plan. Never reuse one agent across invocations that
review different plans: that is not reuse, it is loss of independence. A
reused role is `execution=degraded` and its handoff is never reusable. When
the focused risk role was triggered but not dispatched or not obtained, the
run is `execution=degraded` with `focused-role-not-obtained`; that reason
alone does not bar reuse or continuation.
```

(This drops the duplicate `A preceding plan that is `BLOCKED` does not stop later discovery.` here; the copy in `## Default mode` stays and is pinned.)

- [ ] **Step 4: Add the continuation subsection** at the end of `## Default mode` (immediately before `## Review-only mode`):

```text
### Continuation after `REVISE` or `BLOCKED`

A continuation replaces discovery with closure. Take it when all hold:

- The recorder's latest completed run for this plan has verdict `REVISE` or
  `BLOCKED` and a reusable `execution`.
- `git diff --name-only <git.head_end> HEAD` lists only the resolved design,
  plan, and ledger paths. This chooses between continuation and discovery; it
  does not narrow `head_changed_during_review` during a review.
- The diff of those documents since the run's `sha_end` can be produced, from
  this conversation or from Git.
- The outer request does not ask for a full re-review.

Otherwise run discovery. Without a recorded run for this plan there is no
continuation. The previous-decision rule in the verdict section still applies
first.

Call `start`, then dispatch one fresh read-only reviewer with the closure
dispatch. Its open records are the prior unresolved handoff packet when this
conversation holds it, else the prior run's recorded findings from `show`;
their `id`, `severity`, `class`, `location`, and `evidence` are exact. Keep the
prior finding IDs. The flow then continues as after an original closure
review: repair, closure, the residual pass, verdict. Continuations are not
capped: text outside the diff already passed one discovery, and closure's
bounded regression covers the diff.
```

Red flags: replace the `degraded` bullet and add one, matching Step 1.

- [ ] **Step 5: Edit protocol, contract, READMEs, cases, testing.md**

`reviewer-protocol.md` `### Closure dispatch`: after the bullet ending `which a summary cannot carry.` add the bullet:

```text
- In a continuation, the prior run's recorded findings stand in for the
  verbatim records; their Location and Evidence are exact.
```

`contract.md`:
  - `### Degraded reasons` paragraph: replace `집중 위험 역할만 못 구하면 `degraded`이고 그 인계는 재사용하지` / `않습니다.` with `집중 위험 역할은 발견하는 호출에서만 부릅니다. 부르지 않았거나 못 구하면 `degraded`와 `focused-role-not-obtained`이며, 이 사유만으로는 인계 재사용과 이어 검토를 막지 않습니다. 다른 사유의 `degraded` 인계는 재사용하지 않습니다.`
  - Reuse paragraph: `바뀌지 않은 `full` run의 인계만 재사용합니다. `execution`이 `degraded` 또는` / `` `blocked`인 run의 인계는 재사용하지 않습니다.`` → `바뀌지 않은 재사용 가능 run(`full`, 또는 사유가 `focused-role-not-obtained`뿐인 `degraded`)의 인계만 재사용합니다. 다른 `degraded`와 `blocked` run의 인계는 재사용하지 않습니다. 직전 run이 `REVISE`나 `BLOCKED`이고 `git diff --name-only <head_end> HEAD`가 설계·계획·원장뿐이면 발견 없이 이어 검토로 닫힘부터 합니다. 이 계획의 기록 run이 없으면 이어 검토는 없고 전체 발견입니다.` (the Task 2 sentence stays after it).
  - Recorder paragraph: `` `execution`이 `degraded`이면`` / ``인계를 재사용하지 않고 새 전체 검토로 `start`합니다.`` → `` `execution`이 `degraded`이고 사유가 `focused-role-not-obtained`뿐이 아니면 인계를 재사용하지 않고 새 전체 검토로 `start`합니다.``; `` `full`이면 문서 해시,`` → ``재사용 가능 run이면 문서 해시,``.
  - `### Contract`: `- `handoff`: `unresolved-packet`, `full-execution-only`` → `- `handoff`: `unresolved-packet`, `reusable-execution-only`` and add the next line `- `continuation`: `docs-only-diff`, `closure-first`, `recorded-run-required``.

READMEs: replace the pinned reuse sentences with the Step 1 strings verbatim, and after each add one sentence — Korean: ` 직전 판이 `REVISE`나 `BLOCKED`이고 그 뒤 바뀐 것이 설계·계획·원장뿐이면 새 발견 없이 닫힘부터 이어 검토합니다.` English: ` When the previous run was `REVISE` or `BLOCKED` and only the design, plan, or ledger changed since, the next invocation continues from closure instead of a fresh discovery.`

`cases.json`: change `degraded-handoff-not-reused`'s `request` to `"$pre-sdd-review sample-app/design.md sample-app/plan.md after a degraded REVISE run whose reason is agent-reused-within-invocation"`; append:

```json
    {"id": "continuation-skips-discovery", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md after a recorded full REVISE run when only sample-app/plan.md changed and HEAD is unchanged", "expect": ["continuation", "closure_first", "prior_finding_ids", "no_discovery"]},
    {"id": "continuation-after-committed-docs", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md after a recorded REVISE run whose repaired plan was then committed", "expect": ["continuation", "docs_only_diff_predicate"]},
    {"id": "continuation-needs-docs-only-diff", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md after a recorded REVISE run when src/app.ts also changed since", "expect": ["fresh_discovery"]},
    {"id": "continuation-needs-recorded-run", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md after a REVISE run with no recorded evidence", "expect": ["fresh_discovery"]},
    {"id": "focused-only-degraded-continues", "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md after a degraded REVISE run whose only reason is focused-role-not-obtained", "expect": ["continuation", "no_focused_role", "degraded_focused_role_not_obtained"]}
```

`testing.md` `### Case inventory`: append the five ids in that order.

- [ ] **Step 6: Refresh digests, run, commit**

Digest helper → paste changed values (`SKILL.md`, `references/reviewer-protocol.md`, maintainer, `### Degraded reasons`, `testing`). `python3 scripts/verify.py --skill pre-sdd-review` — Expected: exit 0. `grep -rn "full-execution-only" skills docs tests` — Expected: no output.

```bash
git add skills/pre-sdd-review docs/maintainers/products/pre-sdd-review tests/products/pre-sdd-review
git commit -m "feat(pre-sdd-review): continue from closure after REVISE or BLOCKED"
```

---

### Task 4: Rule cleanup

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md` (Capture freshness ~121-125, Optional local evidence ~169-172)
- Test: `tests/products/pre-sdd-review/test_contract.py` (digest only)

- [ ] **Step 1: Check pins** — `grep -n "quietly fall back\|does not prove\|historical-unbound\|accepts \`abandon\`" tests/products/pre-sdd-review/test_contract.py`. Expected: only `historical-unbound` is pinned. If another hit appears, keep that phrase in the replacement text.

- [ ] **Step 2: Edit** — replace the paragraph starting `When preceding plans exist, carry that list and their paths in the reviewer` through `it does not prove the reconstruction happened.` with:

```text
When preceding plans exist, carry that list and their paths in the reviewer
instruction and require a baseline-reconstruction statement on the response's
first line, so the reviewer does not quietly fall back to `HEAD`.
```

Replace the paragraph starting `A schema 2 pending run is `historical-unbound`` through `accepts `abandon` so an in-flight run survives the upgrade.` with:

```text
A schema 2 pending run is `historical-unbound` and read-only; a schema 3
pending run accepts only `abandon`. Start a new run if recording is still
wanted, and never infer a checkout identity for a historical record.
```

- [ ] **Step 3: Refresh the `SKILL.md` digest, run, commit**

`python3 scripts/verify.py --skill pre-sdd-review` — Expected: exit 0.

```bash
git add skills/pre-sdd-review/SKILL.md tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): drop self-disclaiming and legacy rule text"
```

---

### Task 5: Release 5.1.0

**Files:**
- Modify: `skills/pre-sdd-review/release.toml`, `skills/pre-sdd-review/SKILL.md` (frontmatter `version`, `updated_at`), `skills/pre-sdd-review/evidence/evidence.py` (`CLI_VERSION`), `skills/pre-sdd-review/evidence/README.md` (handshake line), `docs/maintainers/products/pre-sdd-review/contract.md` (handshake line), `scripts/release.py` (lines ~633-634), `skills/pre-sdd-review/CHANGELOG.md`
- Test: `tests/products/pre-sdd-review/test_contract.py` (`TARGET_VERSION`, changelog date assertion, digests), `tests/products/pre-sdd-review/evidence/test_evidence.py` (`VERSION_LINE`), `tests/repository/test_release_contract.py` (version map and three `pre-sdd-review-v5.0.0` asserts)

- [ ] **Step 1: Bump the tests first** — `TARGET_VERSION = "5.1.0"`; the changelog assertion `f"## {TARGET_VERSION} - 2026-09-19"` → `- 2026-09-24`; `VERSION_LINE` → `b'{"cli_version":"5.1.0","schema":4,"skill_name":"pre-sdd-review"}\n'`; in `test_release_contract.py` `"pre-sdd-review": "5.0.0"` → `"5.1.0"` and the three `5.0.0` asserts → `5.1.0`. Run `python3 scripts/verify.py --skill pre-sdd-review` — Expected: FAIL on version.

- [ ] **Step 2: Bump every source face** — `grep -rn "5\.0\.0" skills/pre-sdd-review docs/maintainers/products/pre-sdd-review scripts/release.py | grep -v CHANGELOG` and change each hit to `5.1.0`; set `updated_at: "2026-09-24"` in `SKILL.md`. Expected after edit: the grep prints nothing.

- [ ] **Step 3: CHANGELOG** — under `## Unreleased` keep it empty and insert:

```markdown
## 5.1.0 - 2026-09-24

### Changed

- `REVISE`나 `BLOCKED` 뒤 바뀐 것이 설계·계획·원장뿐이면 새 발견 없이 닫힘부터 이어 검토합니다. 이 계획의 기록 run이 있어야 합니다.
- 두 번째 종결 뒤 원래 기록의 `IMPORTANT` 2건 이하가 한 자리 수정으로 남으면 같은 호출에서 한 번 더 고칩니다.
- `repair_passes`는 적용한 수리 패스를 셉니다. `repaired`는 종결 검토자가 닫은 기록에만 쓰고, 마지막 동작이 수리이면 `READY`가 아닙니다.
- 열린 `BLOCKER`는 `BLOCKED`입니다. 답이 없는 사용자 결정 앞에서는 검토자를 다시 부르지 않고, 새 결정이 세 판 연속 나오면 설계로 돌려보냅니다.
- 집중 위험 역할은 발견하는 호출에서만 부릅니다. `focused-role-not-obtained`만 있는 `degraded`는 재사용과 이어 검토를 막지 않습니다.

### Removed

- 무비용 수리 회계와 `summary.counts.costless_repairs`.

### Notes

- 기록기에 `repair_after_last_review`와 `open_blocker_without_blocked_verdict` 관찰 이상이 늘었습니다. `repair_without_repaired_finding`은 수리한 기록이 하나도 없을 때만 뜹니다.
- Record schema는 4 그대로이고 `repair_passes` 0..3, `review_passes` 1..4를 받습니다. 5.1.0이 쓴 3회 수리 record는 5.0.0 기록기가 읽지 못합니다. Handshake `cli_version`은 5.1.0입니다. GitHub 태그와 Release는 만들지 않습니다.
```

- [ ] **Step 4: Refresh digests, full verification, commit**

Digest helper → paste. Run `python3 scripts/verify.py` — Expected: exit 0 with every stage `OK`.

```bash
git add skills/pre-sdd-review docs/maintainers/products/pre-sdd-review scripts/release.py tests
git commit -m "chore(pre-sdd-review): release 5.1.0"
```

---

### Task 6: Live behavior check (explicitly requested by the user, 2026-09-24)

Offline tests only prove the text and the recorder. This task runs the changed skill for real and checks it does what the spec says. It makes live model calls; the user asked for them. It runs on macOS, in a throwaway repository with synthetic documents only, and with an isolated evidence home so the user's `~/.pre-sdd-review/` is untouched. Nothing from this task is committed except the short result note in Step 7.

**Files:**
- Create (scratch only, outside the repo): `$S/live/app/` fixture repository, `$S/live/home/` evidence home, `$S/live/*.jsonl` transcripts, where `$S` is the session scratchpad.
- Modify: `docs/history/plans/2026-09-24-pre-sdd-review-5.1.0.md` (append the result table in Step 7).

**Host commands.** Claude Code is primary because the logged failures happened there; Codex (the only `supported` host) repeats scenario L2. Each run gets this instruction prefix so the host loads the worktree copy, not the installed 5.0.0 copy:

```text
Use the pre-sdd-review skill whose root is <WT>/skills/pre-sdd-review. Read <WT>/skills/pre-sdd-review/SKILL.md and follow it exactly; do not use any other installed pre-sdd-review. The evidence recorder is <WT>/skills/pre-sdd-review/evidence/evidence.py.
```

```bash
# Claude Code
PRE_SDD_REVIEW_HOME=$S/live/home claude -p "<prefix> $pre-sdd-review <mode> docs/plan.md" \
  --output-format stream-json --verbose --permission-mode bypassPermissions --add-dir <WT> > $S/live/<run>.jsonl
# Codex
PRE_SDD_REVIEW_HOME=$S/live/home codex exec --json -C $S/live/app "<prefix> \$pre-sdd-review docs/plan.md" > $S/live/<run>.codex.jsonl
```

- [ ] **Step 1: Build the fixture** — `git init $S/live/app`; add `src/app.ts` (`export function renderMessage(input: string): string { return input; }`), `tests/app.test.ts`, `package.json` with `"test": "node --test"`; `docs/design.md` (requirements: `renderMessage` returns input unchanged; `formatCount(n)` returns `"<n> items"`); `docs/plan.md` with `**Spec:** docs/design.md`, a `Files:` section, and three seeded defects: (a) a task cites nonexistent `src/format.ts` as existing, (b) `formatCount` has no plan task, (c) the only check for `renderMessage` is `npm run build` (no behavior test). Commit.

- [ ] **Step 2: L1 discovery baseline (Claude Code, `review-only`)** — Expect: one discovery reviewer dispatched, `REVISE`, record `review_passes: 1`, `repair_passes: 0`, findings `unresolved`, `Anomalies: none`.

- [ ] **Step 3: L2 continuation (Claude Code, default mode)** — Hand-fix defect (b) in `docs/plan.md`, commit it. Invoke default mode. Expect: no discovery instruction (the first reviewer prompt contains the prior finding records and the diff, not a fresh-review instruction); prior finding IDs kept; repairs followed by closure; final record `review_passes > repair_passes`; no `repair_after_last_review`; each `repaired` finding traceable to a closure reviewer response. Repeat L2 on Codex from a fresh copy of the L1 state (`cp -R` of `app` and `home` taken after Step 2).

- [ ] **Step 4: L3 negative (Claude Code)** — From the post-L1 copy, also edit `src/app.ts` and commit. Expect: fresh discovery (the continuation predicate fails on `git diff --name-only`).

- [ ] **Step 5: L4 unanswered decision (Claude Code)** — New fixture branch where `docs/design.md` says `formatCount` pluralization for `n = 1` is "to be decided by the product owner". Run default mode → expect `BLOCKED` with a checkpoint. Run again without changing anything but a typo elsewhere in the plan → expect no reviewer dispatched, the same checkpoint printed.

- [ ] **Step 6: Score each run** from its transcript and record: count reviewer dispatches (Claude Code: `tool_use` with name `Agent`/`Task`; Codex: spawned-agent events), confirm the SKILL.md path read is under `<WT>`, and read the record with `python3 <WT>/skills/pre-sdd-review/evidence/evidence.py summary` under `PRE_SDD_REVIEW_HOME=$S/live/home`. A run passes only when every expectation in its step holds. On a failure, stop, report the transcript evidence, and fix the rule text (with its test) before re-running only the failed scenario.

- [ ] **Step 7: Record the result** — append a short table (scenario, host, expected, observed, pass/fail, elapsed) to this plan file under `## Live check result`, with no transcript text. Commit:

```bash
git add docs/history/plans/2026-09-24-pre-sdd-review-5.1.0.md
git commit -m "docs(pre-sdd-review): record the 5.1.0 live behavior check"
```

## Live check result

Run on 2026-09-24, macOS, Claude Code 2.1.280 (child model claude-opus-5-5), throwaway fixture repository with an isolated evidence home. No transcript text is recorded here.

| Scenario | Host | Expected | Observed | Result | Elapsed |
|---|---|---|---|---|---|
| L1 discovery baseline (`review-only`) | Claude Code | 1 discovery reviewer, `REVISE`, review 1 / repair 0, findings `unresolved`, `Anomalies: none` | 1 discovery dispatch; `REVISE`; `execution=full`, review 1 / repair 0; 4 findings all `unresolved` (seeded defects a and b, and defect c split into a missing `build` script finding and a missing behavior test finding); `Anomalies: none` | pass | 140 s |
| L2 continuation (default) | Claude Code | first reviewer is a closure dispatch with the prior IDs and diff; IDs kept; review > repair; no `repair_after_last_review`; every `repaired` traceable to a closure reply | 2 dispatches, both closure (prior IDs PSDR-001..004 plus the plan diff since the L1 head); IDs kept; `READY`, review 2 / repair 1; no anomalies; PSDR-002 closed by closure 1, PSDR-001/003/004 by closure 2 | pass | 236 s |
| L2 continuation (default) | Codex | same as above | not run: Codex account usage limit (resets 2026-09-27) | not run (environment) | — |
| L3 code changed (default) | Claude Code | fresh discovery, because `git diff --name-only` lists `src/app.ts` | first dispatch is discovery with no prior findings; then repair and closure; `READY`, review 2 / repair 1; no anomalies | pass | 181 s |
| L4a unanswered decision (default) | Claude Code | `BLOCKED` with a checkpoint | discovery, 1 repair, closure; `BLOCKED`, `execution=blocked`, `block_reason` names the product-owner `n = 1` decision; one consolidated decision checkpoint; PSDR-001 BLOCKER open | pass | 173 s |
| L4b typo only (default) | Claude Code | no reviewer dispatched; same checkpoint | 0 dispatches, no repair, no new run; `BLOCKED` with the same `n = 1` decision (PSDR-001) | pass | 32 s |

Every run read `SKILL.md` from this worktree. No run used the Skill tool for pre-sdd-review or read an installed copy.
