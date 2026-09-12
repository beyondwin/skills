# korean-writing-editor Output Stickiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship korean-writing-editor 2.0.4 so default replies are the work product, already-correct local forms stay put in polish, and excluded near-misses are not fulfilled in the same turn.

**Architecture:** Replace the Output Contract prohibitions with a positive recipe in `SKILL.md`, extend the synonym-preservation gate from `correct` to `polish`, and close the near-miss hole that still performs the excluded task. Lock those rules with one new diagnose fixture, four mutation checks, and skill-tree terms, then retarget the locked 33-case public count to 34.

**Tech Stack:** Markdown skill payload, JSON fixtures, Python 3.11+ stdlib, `unittest`.

**Spec:** `docs/history/specs/2026-09-12-korean-writing-editor-output-stickiness-design.md`

## Global Constraints

- Product is `skills/korean-writing-editor`. Target version is `2.0.4`. This is a PATCH.
- Python 3.11+ standard library only. No third-party imports in tests or scripts.
- Verification command, run from the repository root: `python3 scripts/verify.py --skill korean-writing-editor`. After shared user-doc or release-contract edits, also run `python3 scripts/verify.py`.
- Do NOT modify `products.toml`. `supported_hosts` stays `["codex"]`. `verify_stages` stay as registered.
- Do NOT modify `tests/products/korean-writing-editor/live/` or run live `--execute`.
- Do NOT add Cursor or any new host to compatibility claims. Keep the registered support sentence `korean-writing-editor: Codex supported; Agent Skills contract portable; other hosts only supported after a recorded smoke.`
- Do NOT put provider model names in `SKILL.md`.
- Do NOT copy user Korean, provider transcripts, or credentials into fixtures. New fixture text is the synthetic sentences already in this spec.
- Do NOT add a mode, a morphological analyzer, or an unofficial spelling API.
- Maintainer docs under `docs/maintainers/products/korean-writing-editor/` are Korean prose. Payload README repository links stay absolute GitHub URLs; links to files shipped in the payload stay relative.
- Offline success does not prove live model quality. Do not write changelog or testing notes that treat fixture pass as live evidence.

---

### Task 1: Fail the skill tree and the 34-case summary before editing the payload

The current runner prints `33 cases: … trigger=5` and does not require the output-recipe phrases. Change those locks first so the rest of the work has a red test.

**Files:**
- Modify: `tests/products/korean-writing-editor/offline/run.py`
- Modify: `tests/products/korean-writing-editor/test_package.py`
- Test: `tests/products/korean-writing-editor/test_package.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `EXPECTED_CATEGORY_COUNTS["trigger"] == 6`, summary string `34 cases: normative=10 preservation=8 noop=6 voice=4 trigger=6`, and skill-tree terms `first non-whitespace`, `excluded task`, and `correct` or `polish`. Task 2 supplies the diagnose fixture. Task 3 supplies the SKILL.md phrases.

- [ ] **Step 1: Point the package summary at 34 cases**

In `tests/products/korean-writing-editor/test_package.py` replace:

```python
EXPECTED_SUMMARY = (
    "33 cases: normative=10 preservation=8 noop=6 voice=4 trigger=5"
)
```

with:

```python
EXPECTED_SUMMARY = (
    "34 cases: normative=10 preservation=8 noop=6 voice=4 trigger=6"
)
```

In the same file, in `test_korean_offline_runner_accepts_explicit_skill_root`, replace the assertion `"33 cases:"` with `"34 cases:"`.

- [ ] **Step 2: Run the package test to verify it fails**

Run: `python3 tests/products/korean-writing-editor/test_package.py KoreanPackageTests.test_korean_offline_runner_accepts_explicit_skill_root -v`

Expected: FAIL. The runner still prints `33 cases:` and `trigger=5`. Do not use `python3 -m unittest tests.products.korean-writing-editor...`; the product directory name contains hyphens and is not an importable package. The file has `unittest.main()`.

- [ ] **Step 3: Raise the runner's trigger count and summary**

In `tests/products/korean-writing-editor/offline/run.py` set:

```python
EXPECTED_CATEGORY_COUNTS = {
    "normative": 10,
    "preservation": 8,
    "noop": 6,
    "voice": 4,
    "trigger": 6,
}
```

Replace the summary print:

```python
        "33 cases: "
```

with:

```python
        "34 cases: "
```

- [ ] **Step 4: Require the output-recipe phrases in SKILL.md**

In `tests/products/korean-writing-editor/offline/run.py`, immediately after `TIER_TERMS = ("fast", "balanced", "frontier")`, add:

```python
OUTPUT_RECIPE_TERMS = ("first non-whitespace", "excluded task", "correct` or `polish")
```

In `validate_skill_tree`, inside the existing `if skill_text is not None:` block that already checks `name`, `license`, and `description` (the first assignment of `skill_text = present.get("SKILL.md")`), append:

```python
        for term in OUTPUT_RECIPE_TERMS:
            if not _contains_term(skill_text, term):
                errors.append(
                    f"skill tree: SKILL.md missing output-recipe term {term!r}"
                )
```

Do not add a second `skill_text = present.get("SKILL.md")`. `_contains_term` already exists in this file.

- [ ] **Step 5: Run the package test to verify it still fails, now for two reasons**

Run: `python3 tests/products/korean-writing-editor/offline/run.py --scope full`

Expected: non-zero exit. stderr contains `fixtures: expected 6 trigger cases, found 5` and `skill tree: SKILL.md missing output-recipe term 'first non-whitespace'`. Missing `correct` or `polish` is also a skill-tree error; the first missing term is enough to fail this step.

- [ ] **Step 6: Commit**

```bash
git add tests/products/korean-writing-editor/offline/run.py tests/products/korean-writing-editor/test_package.py
git commit -m "test: require 34 korean fixtures and output-recipe skill terms"
```

---

### Task 2: Add the diagnose fixture and the four mutations

**Files:**
- Modify: `tests/products/korean-writing-editor/offline/cases.json`
- Modify: `tests/products/korean-writing-editor/offline/run.py` (`run_mutation_checks`)
- Modify: `tests/products/korean-writing-editor/test_package.py` (`len(payload["cases"])`)
- Test: `tests/products/korean-writing-editor/offline/run.py --scope fixtures` then `--scope full`

**Interfaces:**
- Consumes: `EXPECTED_CATEGORY_COUNTS["trigger"] == 6` from Task 1.
- Produces: case id `trigger-diagnose-06` and mutation failures for English preamble, Korean preamble, `수 있다` → `수도 있다`, and translation-after-refusal. Task 3 does not depend on the fixture text remaining editable.

- [ ] **Step 1: Append the diagnose case**

Add a comma after the last object in `tests/products/korean-writing-editor/offline/cases.json` (`trigger-legacy-kws-05`) and append:

```json
    {
      "id": "trigger-diagnose-06",
      "category": "trigger",
      "request": "고치지 말고 어색한 부분만 알려줘: 지금 상태에선 배포할수 있다.",
      "source": "지금 상태에선 배포할수 있다.",
      "candidate": "- 배포할수: 의존명사 수 앞 띄어쓰기가 필요합니다 (normative-rule).",
      "candidate_trigger": true,
      "candidate_mode": "diagnose",
      "candidate_tier": "fast",
      "expected_trigger": true,
      "expected_mode": "diagnose",
      "expected_tier": "fast",
      "expected_noop": false,
      "must_preserve": ["배포할수"],
      "required_substrings": ["배포할수"],
      "forbidden_substrings": [
        "지금 상태에선 배포할 수 있다.",
        "Using the",
        "Using korean-writing-editor",
        "한국어 교정 스킬"
      ],
      "rationale": "Diagnose names the spacing issue without a rewritten draft or process preamble."
    }
```

Keep `expected_noop` false. A true value would require `candidate == source` and reject every diagnose finding.

In `tests/products/korean-writing-editor/test_package.py`, in `test_cases_live_beside_the_runner`, replace `self.assertEqual(len(payload["cases"]), 33)` with `self.assertEqual(len(payload["cases"]), 34)`.

- [ ] **Step 2: Add forbidden preamble fragments to the spacing case**

In `norm-spacing-can-01`, replace:

```json
      "forbidden_substrings": ["사용할수", "켜야 할 필요는", "요청은 오탈자"],
```

with:

```json
      "forbidden_substrings": [
        "사용할수",
        "켜야 할 필요는",
        "요청은 오탈자",
        "Using the",
        "한국어 교정 스킬"
      ],
```

- [ ] **Step 3: Add the four mutations to `run_mutation_checks`**

Insert these blocks in `run_mutation_checks` after the existing `요청은 오탈자` preamble mutation and before the grammar-particle loop:

```python
        english_preamble = dict(spacing)
        english_preamble["candidate"] = (
            "Using the Korean writing editor skill to correct typos."
            + str(spacing["candidate"])
        )
        if not evaluate_candidate(english_preamble):
            errors.append(
                "mutation: adding English skill-usage preamble produced no error"
            )

        korean_preamble = dict(spacing)
        korean_preamble["candidate"] = (
            "한국어 교정 스킬을 확인한 뒤 오탈자만 고치겠습니다."
            + str(spacing["candidate"])
        )
        if not evaluate_candidate(korean_preamble):
            errors.append(
                "mutation: adding Korean skill-usage preamble produced no error"
            )
```

After the existing `meaning-negation-01` negation-flip mutation, add:

```python
        hedge = dict(negation)
        hedge["candidate"] = (
            str(negation["candidate"]).replace(
                "출시하지 않을 수 있다", "출시하지 않을 수도 있다"
            )
        )
        if not evaluate_candidate(hedge):
            errors.append(
                "mutation: replacing 수 있다 with 수도 있다 produced no error"
            )
```

After the existing `trigger` handling is not present; add this new lookup before `return errors`:

```python
    translation = by_id.get("trigger-translation-03")
    if translation is None:
        errors.append("mutation: missing trigger-translation-03")
    else:
        mutated = dict(translation)
        mutated["candidate"] = (
            str(translation["candidate"])
            + " There is a meeting tomorrow morning."
        )
        if not evaluate_candidate(mutated):
            errors.append(
                "mutation: fulfilling a translation near-miss produced no error"
            )
```

- [ ] **Step 4: Run fixtures-only to verify the new case and mutations pass**

Run: `python3 tests/products/korean-writing-editor/offline/run.py --scope fixtures`

Expected: exit 0 and stdout contains `34 cases: normative=10 preservation=8 noop=6 voice=4 trigger=6` and `mutation checks: PASS`. `--scope fixtures` skips the skill tree, so missing `first non-whitespace` must not fail here.

- [ ] **Step 5: Run full scope to verify it still fails on SKILL.md**

Run: `python3 tests/products/korean-writing-editor/offline/run.py --scope full`

Expected: non-zero exit. stderr contains `skill tree: SKILL.md missing output-recipe term 'first non-whitespace'`. Fixtures must not be the failing reason.

- [ ] **Step 6: Commit**

```bash
git add tests/products/korean-writing-editor/offline/cases.json tests/products/korean-writing-editor/offline/run.py tests/products/korean-writing-editor/test_package.py
git commit -m "test: lock diagnose fixture and output-preamble mutations"
```

---

### Task 3: Replace the SKILL.md recipe, synonym gate, and near-miss hole

**Files:**
- Modify: `skills/korean-writing-editor/SKILL.md`

**Interfaces:**
- Consumes: `OUTPUT_RECIPE_TERMS` from Task 1.
- Produces: the phrases `first non-whitespace`, `excluded task`, and `correct` or `polish` in `SKILL.md`. Task 4 quotes the same rules in the editorial guide and READMEs.

- [ ] **Step 1: Shorten Default Interaction so it defers to the recipe**

Replace the paragraph that begins `In \`correct\` and \`polish\`, the default reply is the edited text only.` with:

```markdown
Default replies follow ## Output Contract. Do not describe the work
instead of returning it.
```

Keep the genre-question paragraph and the do-not-persist paragraph.

- [ ] **Step 2: Apply the synonym gate to polish as well as correct**

In `## Preservation Gate`, replace:

```markdown
- replace an already standard, grammatical local expression with a synonym
  in `correct`
```

with:

```markdown
- replace an already standard, grammatical local expression with a synonym
  in `correct` or `polish`
```

Leave the next bullet (`rewrite obligation, permission, possibility, or
negation wording when that wording is already grammatical`) unchanged. It
already covers `수 있다` versus `수도 있다`.

- [ ] **Step 3: Close the near-miss consolation hole**

In `## Activation Gate`, immediately after `return a no-op handoff and do not start an editing workflow.`, add:

```markdown
A no-op handoff may say the editor does not apply. It must not perform the
excluded task in the same turn.
```

In `## Refuse Or Hold`, replace the Excluded near miss row:

```markdown
| Excluded near miss | No-op; do not edit, translate, draft, detect, or imitate a named author |
```

with:

```markdown
| Excluded near miss | No-op; do not edit, and do not perform the excluded task in the same turn |
```

- [ ] **Step 4: Replace Output Contract with the positive recipe**

Replace the entire `## Output Contract` section, keeping the heading, with:

```markdown
## Output Contract

The default reply is the work product, not a description of the work.

In `correct` and `polish`, the reply is exactly the edited Korean text
(or the unchanged original). The first non-whitespace character belongs
to that text. Do not put a skill name, a mode name, or process narration
before or after it.

In `diagnose`, the reply is the findings. The first line names an issue,
decision class, or hold. Do not restate the mode. Do not attach a
rewritten draft.

Do not print a rubric, change log, score, or routing receipt.
Add a short `확인 필요` note only for a material hold. Do not attach the
explanation list to that note. Explain class and source only when the user
asks why. A why-request may include:

1. the edited text (or the unchanged original)
2. material changes
3. held alternatives or ambiguity
4. the relevant normative source when a normative claim is made
```

The phrase `excluded task` must appear in the Activation Gate or Refuse table
text from Step 3. The Preservation Gate bullet from Step 2 must contain
`correct` or `polish` so `_contains_term` matches `correct` or `polish`.
If a later edit removes either phrase, the skill-tree check fails.

- [ ] **Step 5: Run the offline full scope**

Run: `python3 tests/products/korean-writing-editor/offline/run.py --scope full`

Expected: exit 0. stdout contains `34 cases:`, `mutation checks: PASS`, and `skill tree (full): PASS`.

- [ ] **Step 6: Commit**

```bash
git add skills/korean-writing-editor/SKILL.md
git commit -m "fix: make korean editor replies the work product"
```

---

### Task 4: Update the editorial guide and standalone READMEs

**Files:**
- Modify: `skills/korean-writing-editor/references/editorial-guide.md`
- Modify: `skills/korean-writing-editor/README.md`
- Modify: `skills/korean-writing-editor/README.en.md`

**Interfaces:**
- Consumes: the Output Contract recipe and near-miss rule from Task 3.
- Produces: shipped user-facing first-call examples whose default is `polish`.

- [ ] **Step 1: Add three compact examples**

Append these bullets under `## Compact Examples` in `skills/korean-writing-editor/references/editorial-guide.md`, after the high-stakes claim example:

```markdown
- **Reply shape.** For `correct` or `polish`, the reply starts with the
  edited sentence, not `Using korean-writing-editor`. For `diagnose`, the
  first line names the issue. Class: output recipe, not a style rule.
- **Already-correct possibility.** `현재 계획으로는 출시하지 않을 수 있다.`
  stays `수 있다`. Do not write `수도 있다`. Valid in `correct` and
  `polish`. Class: already-correct local form.
- **Excluded translation.** `이 문장을 영어로 번역해줘: 내일 오전에 회의가
  있습니다.` is a near-miss. Do not translate it in the same turn. Class:
  excluded task.
```

- [ ] **Step 2: Replace the Korean first-call example**

In `skills/korean-writing-editor/README.md`, replace the `## 첫 호출` section with:

```markdown
## 첫 호출

설치 다음 대화에서 이렇게 부릅니다. 기본은 윤문입니다. 이식 가능한 접두는
`$korean-writing-editor`와 `/korean-writing-editor`입니다. 측정된 호스트는
Codex입니다.

```text
$korean-writing-editor 자연스럽게 다듬어줘: (한국어 원문)
```

오탈자만 고치려면:

```text
$korean-writing-editor 오탈자만 고쳐줘: (한국어 원문)
```
```

Do not say Cursor is supported.

- [ ] **Step 3: Replace the English first-call example**

In `skills/korean-writing-editor/README.en.md`, replace the `## First call` section with:

```markdown
## First call

After install, invoke it on the next turn. The default is polish. Portable
prefixes are `$korean-writing-editor` and `/korean-writing-editor`. Codex
is the measured host.

```text
$korean-writing-editor Polish this naturally: (Korean source)
```

For typos only:

```text
$korean-writing-editor Fix typos only: (Korean source)
```
```

- [ ] **Step 4: Verify payload links and the skill tree**

Run: `python3 tests/products/korean-writing-editor/offline/run.py --scope full --skill-root skills/korean-writing-editor`

Expected: exit 0. Then:

Run: `python3 tests/products/korean-writing-editor/test_package.py KoreanPackageTests.test_standalone_readme_relative_links_stay_inside_payload -v`

Expected: OK. The new GitHub links in the READMEs were already absolute; do not introduce a relative link to `docs/`.

- [ ] **Step 5: Commit**

```bash
git add skills/korean-writing-editor/references/editorial-guide.md skills/korean-writing-editor/README.md skills/korean-writing-editor/README.en.md
git commit -m "docs: show polish as the default first korean editor call"
```

---

### Task 5: Retarget 2.0.4 and the public 34-case locks

**Files:**
- Modify: `skills/korean-writing-editor/release.toml`
- Modify: `skills/korean-writing-editor/SKILL.md` (frontmatter `metadata.version` and `updated_at`)
- Modify: `skills/korean-writing-editor/CHANGELOG.md`
- Modify: `tests/repository/test_release_contract.py` (`EXPECTED["korean-writing-editor"]`)
- Modify: `tests/products/korean-writing-editor/test_package.py` (version assertions)
- Modify: `docs/maintainers/products/korean-writing-editor/contract.md`
- Modify: `docs/maintainers/products/korean-writing-editor/testing.md`
- Modify: `docs/maintainers/products/korean-writing-editor/release.md`
- Modify: `docs/users/ko/verification.md`
- Modify: `docs/users/en/verification.md`
- Modify: `tests/repository/test_public_docs.py` (`"33"` → `"34"` in the evidence-dimension tuple)

**Interfaces:**
- Consumes: 34-case summary from Task 1 and the SKILL.md recipe from Task 3.
- Produces: the shipped 2.0.4 release metadata.

- [ ] **Step 1: Find leftover 2.0.3 and 33-case locks**

```bash
rg -n "2\\.0\\.3|33 cases|서른세|trigger=5" skills/korean-writing-editor tests/products/korean-writing-editor tests/repository/test_release_contract.py tests/repository/test_public_docs.py docs/maintainers/products/korean-writing-editor docs/users
```

Expected hits to change: `release.toml`, `SKILL.md` metadata, `CHANGELOG.md`, `test_release_contract.py`, `test_package.py` version methods, maintainer testing/release/contract, both user `verification.md` files, and `test_public_docs.py` only if it still expects the literal `33` from `verification.md`. Do not change live-harness `33` if none exists. Do not change image-workbench counts.

- [ ] **Step 2: Set the version to 2.0.4**

`skills/korean-writing-editor/release.toml`: `version = "2.0.4"`.

`skills/korean-writing-editor/SKILL.md` frontmatter:

```yaml
metadata:
  version: "2.0.4"
  updated_at: "2026-09-12"
```

`tests/repository/test_release_contract.py`: `"korean-writing-editor": "2.0.4"`.

In `tests/products/korean-writing-editor/test_package.py`, rename `test_release_target_and_skill_version_are_203` to `test_release_target_and_skill_version_are_204` and replace every `2.0.3` in that method and in `test_payload_declares_canonical_name_license_and_version` with `2.0.4`. The changelog regex becomes `(?m)^## 2\.0\.4 - \d{4}-\d{2}-\d{2}$`.

- [ ] **Step 3: Write the changelog entry**

Replace the empty `## Unreleased` body so the file begins:

```markdown
# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 2.0.4 - 2026-09-12

### Changed

- Default `correct` and `polish` replies are the edited text; `diagnose`
  replies start with the finding. Process narration is a failed shape, not
  an extra prohibition.
- Already-correct local forms stay unchanged in `polish` as well as
  `correct`. Near-miss handoffs do not perform the excluded task in the
  same turn.
- The first-call README example is conservative `polish`. Typo-only
  `correct` is the second example.

### Notes

- Offline fixtures are now 34 cases (`trigger=6`). Fixture pass still does
  not prove live model quality. This release does not add a recorded host
  smoke or a runner 18 live execute.

## 2.0.3 - 2026-09-11
```

Keep the existing 2.0.3 and older sections after that heading.

- [ ] **Step 4: Update maintainer contract, testing, and release prose**

In `docs/maintainers/products/korean-writing-editor/contract.md` `## 출력`, replace the first paragraph with:

```markdown
`correct`와 `polish`의 기본 출력은 편집된 글만이다. 첫 비공백 문자가 그
본문에 속한다. `diagnose`의 기본 출력은 소견이며 첫 줄이 문제·등급·hold를
가리킨다. 다시 쓴 초안, 루브릭, 변경 로그, 점수, 라우팅 영수증, 과정 서술을
붙이지 않는다. 실질 hold에만 짧은 `확인 필요` 주를 단다.

제외 near-miss의 no-op는 그 제외 과제를 같은 턴에 수행하지 않는다. 이미
맞는 국소 표현의 동의어 치환은 `correct`와 `polish` 모두에서 되돌린다.
```

In `docs/maintainers/products/korean-writing-editor/testing.md` opening paragraph, replace `서른세 개 속성 케이스` with `서른네 개 속성 케이스(\`normative=10 preservation=8 noop=6 voice=4 trigger=6\`)`. Do not search testing.md for `trigger=5`; that string is not there today. Add this bullet under 결정적 픽스처:

```markdown
- `trigger-diagnose-06`은 diagnose 소견이며 다시 쓴 초안과 과정 서문이
  있으면 실패한다. `norm-spacing-can-01`의 영문·한글 스킬 사용 서문,
  `meaning-negation-01`의 `수도 있다` 치환, `trigger-translation-03`의
  거절 후 번역 변이는 각각 실패해야 한다.
```

In `docs/maintainers/products/korean-writing-editor/release.md`, replace `서른세 개` with `서른네 개` and `trigger=5` with `trigger=6`. The category string already lives in release.md.

- [ ] **Step 5: Update shared user verification counts**

In `docs/users/ko/verification.md` replace `현재 Korean 오프라인은 33개` with `현재 Korean 오프라인은 34개`.

In `docs/users/en/verification.md` replace `Current Korean offline coverage is 33 cases` with `Current Korean offline coverage is 34 cases`.

Leave `normative=10` unchanged. `tests/repository/test_public_docs.py` asserts the literal `33` appears in those files; change that tuple entry from `"33"` to `"34"` in `test_shared_guides_name_current_evidence_dimensions`.

- [ ] **Step 6: Verify the product, then the repository**

```bash
python3 scripts/verify.py --skill korean-writing-editor
echo "SKILL_EXIT=$?"
python3 scripts/verify.py
echo "REPO_EXIT=$?"
```

Expected: `SKILL_EXIT=0` and `REPO_EXIT=0`. The full suite is required because this task changes `tests/repository/test_release_contract.py` and `docs/users/*/verification.md`.

- [ ] **Step 7: Commit**

```bash
git add skills/korean-writing-editor/release.toml skills/korean-writing-editor/SKILL.md skills/korean-writing-editor/CHANGELOG.md tests/repository/test_release_contract.py tests/products/korean-writing-editor/test_package.py tests/repository/test_public_docs.py docs/maintainers/products/korean-writing-editor/contract.md docs/maintainers/products/korean-writing-editor/testing.md docs/maintainers/products/korean-writing-editor/release.md docs/users/ko/verification.md docs/users/en/verification.md
git commit -m "docs: release korean-writing-editor 2.0.4 with 34 offline cases"
```
