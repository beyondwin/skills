# how-it-works First Picture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship how-it-works 3.0.0 so a named mechanism explains at 그림 in one turn, without a depth question, while `/eli5` stays a near-miss and the six chat deliverables stay required.

**Architecture:** Stop blocking on a missing rung. Fill rung by `explicit rung > explicit depth alias > existing jargon default > default 그림`, announce it, and explain in the same turn. Keep civilization 자르기 and high-stakes pause. At 그림 only, put numbered hops before Mermaid in Map and stop restating hops in Body.

**Tech Stack:** Markdown skill payload, JSON fixtures, Python 3.11+ stdlib, `unittest`.

**Spec:** `docs/history/specs/2026-09-12-how-it-works-first-picture-design.md`

## File map

| File | Responsibility |
| --- | --- |
| `tests/products/how-it-works/cases.json` | Synthetic activation fixtures |
| `tests/products/how-it-works/test_contract.py` | Locks fixtures, chrome order, precedence strings, version |
| `skills/how-it-works/SKILL.md` | Gate, paths, rung precedence, dump table |
| `skills/how-it-works/references/output.md` | Chrome order, 그림 body recipe, type recipes |
| `skills/how-it-works/references/visuals.md` | 그림 map = hops then Mermaid |
| `skills/how-it-works/references/korean.md` | Positive 해요체 and 그림 target |
| `skills/how-it-works/README.md`, `README.en.md` | First-call example and skeleton |
| `skills/how-it-works/release.toml`, `CHANGELOG.md` | 3.0.0 identity |
| `docs/maintainers/products/how-it-works/{contract,testing,release}.md` | Maintainer contract |
| `tests/repository/test_release_contract.py` | Shared version pin |
| `tests/repository/test_public_docs.py` | Fixture id list in testing.md |

Do not split the skill. Do not add a renderer, a host, or a live record.

## Global Constraints

- Product is `skills/how-it-works`. Target version is `3.0.0`. This is MAJOR.
- Python 3.11+ standard library only.
- Verify from the repository root: `python3 scripts/verify.py --skill how-it-works`. After repository test or maintainer-doc edits, also run `python3 scripts/verify.py`.
- Do NOT modify `products.toml`. Hosts stay `codex` and `claude-code`.
- Do NOT modify `tests/products/how-it-works/live/smoke-record.json` or `live/cases.json`. Do NOT run live model calls.
- Do NOT activate on `/eli5`. Description must contain `ELI5` and must not contain `/eli5`.
- Do NOT commit user prompts, transcripts, receipts, or generated media.
- Do NOT stage unrelated dirty files (other products, other history specs/plans).
- Do NOT touch the README Python install fence after `<!-- how-it-works-local-links -->`.
- Do NOT change `stakes.md` banner bytes.
- Offline pass is not live quality. CHANGELOG Notes must say live quality stays `not_measured`.
- Product tests: `python3 tests/products/how-it-works/test_contract.py -v`. Do not use `python3 -m unittest tests.products.how-it-works...`; the directory name has hyphens.

---

### Task 1: Fail the fixture lock for default 그림

The current `missing-rung` row forbids a silent rung and requires a closed question. Flip that lock and add `/how-it-works DNS` before editing the skill.

**Files:**
- Modify: `tests/products/how-it-works/test_contract.py`
- Modify: `tests/repository/test_public_docs.py`
- Test: `tests/products/how-it-works/test_contract.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `CASE_IDS` includes `default-dns-picture` immediately after `missing-rung`. `missing-rung` must be a 그림 deliverable. Task 2 writes the matching `cases.json` rows.

- [ ] **Step 1: Insert the new case id**

In `tests/products/how-it-works/test_contract.py`, change `CASE_IDS` so the first three ids are:

```python
CASE_IDS = [
    "broad-slice",
    "missing-rung",
    "default-dns-picture",
    "explicit-dns-path",
```

Keep the remaining ids in the current order.

In `tests/repository/test_public_docs.py`, in `HOW_IT_WORKS_FIXTURE_IDS`, insert `"default-dns-picture",` immediately after `"missing-rung",`.

- [ ] **Step 2: Change the missing-rung lock and add the new lock**

In `test_cases_lock_synthetic_dns_and_rebase_behavior`, replace the `missing-rung` assertion with:

```python
        self.assertEqual(
            by_id["missing-rung"],
            {
                "id": "missing-rung",
                "prompt": "/how-it-works DNS 흐름",
                "must": [
                    "picture_default",
                    "claim",
                    "mermaid",
                    "numbered_hops",
                    "body",
                    "adjacent_slices",
                    "next_move",
                ],
                "forbidden": ["one_closed_question", "skeleton_default"],
            },
        )
        self.assertEqual(
            by_id["default-dns-picture"],
            {
                "id": "default-dns-picture",
                "prompt": "/how-it-works DNS",
                "must": [
                    "picture_default",
                    "claim",
                    "mermaid",
                    "numbered_hops",
                    "body",
                    "adjacent_slices",
                    "next_move",
                ],
                "forbidden": ["one_closed_question", "skeleton_default"],
            },
        )
```

Leave `broad-slice`, `explicit-dns-path`, `near-miss-eli5`, and `jargon-without-depth` assertions unchanged.

- [ ] **Step 3: Run the fixture tests to verify they fail**

Run:

```bash
python3 tests/products/how-it-works/test_contract.py HowItWorksPayloadTests.test_cases_file_parses HowItWorksPayloadTests.test_cases_lock_synthetic_dns_and_rebase_behavior -v
```

Expected: FAIL. `test_cases_file_parses` still sees 19 ids without `default-dns-picture`. `test_cases_lock_synthetic_dns_and_rebase_behavior` still sees `must: ["one_closed_question"]` and `forbidden: ["silent_rung"]`.

- [ ] **Step 4: Commit**

```bash
git add tests/products/how-it-works/test_contract.py tests/repository/test_public_docs.py
git commit -m "test: require how-it-works default picture without a depth question"
```

---

### Task 2: Write the new fixture rows

**Files:**
- Modify: `tests/products/how-it-works/cases.json`
- Modify: `docs/maintainers/products/how-it-works/testing.md`
- Test: `tests/products/how-it-works/test_contract.py`

**Interfaces:**
- Consumes: Task 1 `CASE_IDS` and the two `assertEqual` payloads.
- Produces: `cases.json` ids equal `CASE_IDS`. Task 3 does not depend on fixture text remaining editable.

- [ ] **Step 1: Edit `missing-rung` and insert `default-dns-picture`**

In `tests/products/how-it-works/cases.json`, replace the `missing-rung` object and insert the new object immediately after it:

```json
    {
      "id": "missing-rung",
      "prompt": "/how-it-works DNS 흐름",
      "must": [
        "picture_default",
        "claim",
        "mermaid",
        "numbered_hops",
        "body",
        "adjacent_slices",
        "next_move"
      ],
      "forbidden": ["one_closed_question", "skeleton_default"]
    },
    {
      "id": "default-dns-picture",
      "prompt": "/how-it-works DNS",
      "must": [
        "picture_default",
        "claim",
        "mermaid",
        "numbered_hops",
        "body",
        "adjacent_slices",
        "next_move"
      ],
      "forbidden": ["one_closed_question", "skeleton_default"]
    },
```

Keep a comma after the new object so `explicit-dns-path` still parses.

- [ ] **Step 2: Update testing.md**

In `docs/maintainers/products/how-it-works/testing.md`, replace:

```markdown
- `missing-rung`은 닫힌 깊이 질문 하나이며 칸을 조용히 채우지 않습니다.
```

with:

```markdown
- `missing-rung`은 `/how-it-works DNS 흐름`이며 유형만 채우고 기본 그림으로
  같은 턴에 설명합니다. 닫힌 깊이 질문이 아닙니다.
- `default-dns-picture`는 `/how-it-works DNS`이며 기본 그림 설명입니다.
```

Keep the `near-miss-eli5` bullet unchanged.

- [ ] **Step 3: Run the fixture tests to verify they pass**

Run:

```bash
python3 tests/products/how-it-works/test_contract.py HowItWorksPayloadTests.test_cases_file_parses HowItWorksPayloadTests.test_cases_lock_synthetic_dns_and_rebase_behavior -v
```

Expected: OK. Then:

```bash
python3 tests/repository/test_public_docs.py MaintainerProtocolTests.test_how_it_works_protocol_maps_contract_testing_compatibility_and_release -v
```

Expected: `default-dns-picture` is in `testing.md`, so the `HOW_IT_WORKS_FIXTURE_IDS` loop passes. Other public-doc failures from later tasks are out of this task.

- [ ] **Step 4: Commit**

```bash
git add tests/products/how-it-works/cases.json docs/maintainers/products/how-it-works/testing.md
git commit -m "test: lock DNS default-picture fixtures for how-it-works"
```

---

### Task 3: Fail the SKILL.md precedence and chrome locks

**Files:**
- Modify: `tests/products/how-it-works/test_contract.py`
- Test: `tests/products/how-it-works/test_contract.py`

**Interfaces:**
- Consumes: nothing from Task 2 beyond leaving historical 2.0.0 changelog text alone.
- Produces: SKILL.md must contain `default 그림`, `Announce the rung in the intent line`, `Do not explain until \`slice\` is a cut mechanism`, `Explain in the same turn`, `Missing rung takes default 그림`, picker `**그림** — 한 장 (default)`, and must not contain `Do not silently pick a depth`, the old four-slot gate sentence, or `**길** — 누가 무엇을 넘기는지 (default)`. `OUTPUT_CHROME` requires hops before the mermaid fence. Keep existing exact locks `Do not use the rung picker` and `Explicit 쉽게/한눈에/한 장 selects 그림 even with jargon`. Task 4 supplies the payload strings.

- [ ] **Step 1: Point precedence, type-word, and gate tests at default 그림**

Replace `test_type_word_does_not_silently_fill_rung` with:

```python
    def test_type_word_does_not_silently_fill_rung(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`흐름` → 흐름", text)
        self.assertIn("Type inference does not fill `rung`", text)
        self.assertIn("Never replace a filled rung", text)
        self.assertIn("default 그림", text)
        self.assertNotIn("Do not silently pick a depth", text)
        aliases = section(text, "Silent aliases", "If the prompt already uses domain words")
        self.assertNotIn("흐름", aliases)
        self.assertIn("감이 안 와", aliases)
```

Replace the precedence string in `test_v2_explicit_depth_precedence_contract` with:

```python
            "explicit rung > explicit depth alias > existing jargon default > default 그림",
```

Keep the numeric-alias and `jargon wins` assertions in that method. Keep `test_debug_and_eli5_do_not_enter_the_gate` and `test_explicit_easy_alias_precedes_jargon` byte-for-byte. Do not edit those two methods.

After `test_type_word_does_not_silently_fill_rung`, add:

```python
    def test_missing_depth_explains_at_default_picture(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Do not explain until `slice` is a cut mechanism", text)
        self.assertIn("Explain in the same turn", text)
        self.assertIn("Announce the rung in the intent line", text)
        self.assertIn("Missing rung takes default 그림", text)
        self.assertIn("| 바로 | slice is a cut mechanism |", text)
        self.assertIn("- **그림** — 한 장 (default)", text)
        self.assertNotIn(
            "Do not explain until `slice`, `type`, `rung`, and `language` are filled",
            text,
        )
        self.assertNotIn("- **길** — 누가 무엇을 넘기는지 (default)", text)
```

- [ ] **Step 2: Reorder OUTPUT_CHROME**

Replace the `OUTPUT_CHROME` tuple with:

```python
OUTPUT_CHROME = (
    "# {slice} · {그림|길|뼈대|허점}",
    "{high-stakes banner or omit}",
    "## 한 줄 / One sentence",
    "## 지도 / Map",
    "1. **H1** — {what moves or changes}",
    "2. **H2** — {what moves or changes}",
    "```mermaid",
    "{diagram source}",
    "## 본문 / Body",
    "## 지금 다루지 않은 것 / Adjacent slices",
    "다음 / Next: {exactly one move}",
)
```

Keep `RUNTIME_FLOW` unchanged.

- [ ] **Step 3: Require 그림 body and Korean target phrases**

Add these methods on `HowItWorksPayloadTests` after `test_explicit_easy_alias_precedes_jargon`:

```python
    def test_picture_body_does_not_restate_hops(self) -> None:
        output = _reference("output.md")
        self.assertIn("그림 hops are the map; Body does not walk the hops again", output)
        self.assertIn("Analogy, if used, comes after the hops", output)
        self.assertIn(
            "그림: Map hops only; Body is identity and use. 길 walks the hops on a sequence diagram",
            output,
        )
        self.assertNotIn(
            "Walk the hops. 길 gets the sequence diagram. 그림 gets boxes only",
            output,
        )

    def test_korean_picture_target_keeps_cache_in_the_same_movie(self) -> None:
        korean = _reference("korean.md")
        self.assertIn("묻다, 맡기다, 적어 두다, 만료되다", korean)
        self.assertIn("가까운 기억", korean)
        self.assertNotIn("컴퓨터는 숫자 주소를 본다", korean)
        self.assertIn("여러분이", korean)
        self.assertIn("답니다", korean)
```

- [ ] **Step 4: Run the new locks to verify they fail**

Run:

```bash
python3 tests/products/how-it-works/test_contract.py HowItWorksPayloadTests.test_type_word_does_not_silently_fill_rung HowItWorksPayloadTests.test_missing_depth_explains_at_default_picture HowItWorksPayloadTests.test_v2_explicit_depth_precedence_contract HowItWorksPayloadTests.test_output_chrome_is_common_markdown HowItWorksPayloadTests.test_picture_body_does_not_restate_hops HowItWorksPayloadTests.test_korean_picture_target_keeps_cache_in_the_same_movie HowItWorksPayloadTests.test_debug_and_eli5_do_not_enter_the_gate HowItWorksPayloadTests.test_explicit_easy_alias_precedes_jargon -v
```

Expected: FAIL on missing `default 그림`, remaining `Do not silently pick a depth`, remaining four-slot HARD-GATE, remaining picker `**길** (default)`, mermaid-before-hops order in `output.md`, missing 흐름 recipe, and missing Korean target phrases. `test_debug_and_eli5_do_not_enter_the_gate` and `test_explicit_easy_alias_precedes_jargon` still PASS on the current payload.

- [ ] **Step 5: Commit**

```bash
git add tests/products/how-it-works/test_contract.py
git commit -m "test: lock how-it-works default 그림 and hop-first chrome"
```

---

### Task 4: Implement the gate, chrome, and Korean recipe

**Files:**
- Modify: `skills/how-it-works/SKILL.md`
- Modify: `skills/how-it-works/references/output.md`
- Modify: `skills/how-it-works/references/visuals.md`
- Modify: `skills/how-it-works/references/korean.md`
- Test: `tests/products/how-it-works/test_contract.py`

**Interfaces:**
- Consumes: Task 3 string locks.
- Produces: payload phrases `default 그림`, `Never replace a filled rung`, `Do not use the rung picker`, `Explicit 쉽게/한눈에/한 장 selects 그림 even with jargon`, hop-first chrome, `그림 hops are the map; Body does not walk the hops again`, and `그림: Map hops only; Body is identity and use`. Task 5 copies the same rules into maintainer docs.

- [ ] **Step 1: Replace HARD-GATE through Slots in `SKILL.md`**

Replace from `<HARD-GATE>` through the sentence `Never replace a filled rung. If the rung remains unresolved, ask one closed depth question.` with:

```markdown
<HARD-GATE>
Do not explain until `slice` is a cut mechanism.
Fill `type` and `language` by inference. Fill `rung` by precedence, including
default 그림. Announce the rung in the intent line. Explain in the same turn.
If the noun is a civilization (인터넷, AI, 자본주의), do not explain — cut a slice first.
Do not activate on eli5, /eli5, or “explain like I’m 5”. That is a different skill.
Do not use the rung picker, or this explanation flow, on debugging, implementation, review, translation, one-line lookup, or eli5 requests.
</HARD-GATE>

Prefer explicit invocation: `$how-it-works` on Codex and `/how-it-works` on Claude Code.

## Classify

Say one line before any question so the user can override. Use only the selected
language. In Korean, use this intent line:

> {slice}를 **{rung}** 깊이로 설명할게요. {particle}가 이동하는 순서를 따라가요.

In English, state the same intent in English without repeating the Korean line.

Paths:

| Path | When | Do |
| --- | --- | --- |
| 바로 | slice is a cut mechanism | Fill rung by precedence. One-line plan. Explain same turn if unsurprising. |
| 하나 | slice missing, conflicting rungs, or mixed KO/EN that would change the output | Ask one closed question. |
| 자르기 | blob noun | Three slices + Other. No essay. |

Do not stack two questions. Do not re-ask a filled slot. Do not survey genre, audience, or tone.

## Slots

Required before EXPLAIN: `slice`, `type`, `rung`, and `language`. Infer `type`
and `language`. Fill `rung` by precedence. Do not wait for a user token for
`rung`.

Infer `type` when the verb is obvious (`vs` → 비교, `어떻게 고치냐` → 절차, `왜/원리` → 개념, `흐름` → 흐름). Ask type only if the guess would change the output. Type inference does not fill `rung`.

Missing-slot order: slice, then a language question only if KO/EN mix would change the reply.

Rung picker (recommendation first):

- **그림** — 한 장 (default)
- **길** — 누가 무엇을 넘기는지
- **뼈대** — 갈림길과 실패
- **허점** — 이 그림이 금 가는 곳

Depth precedence: explicit rung > explicit depth alias > existing jargon default > default 그림
An explicitly selected 그림/길/뼈대/허점 (picture/path/skeleton/fracture) wins.
Explicit 쉽게/한눈에/한 장 selects 그림 even with jargon such as rebase, TTL, or Raft.
Use the existing jargon default only when neither a rung nor a depth alias was supplied.
Interpret numeric aliases only when explicitly selecting depth; numbers in the topic are not depth choices.
Never replace a filled rung.

Silent aliases (never print numbers or ages): 쉽게/한눈에/한 장/감이 안 와 → 그림; 따라가 → 길; 내부/실무/속 → 뼈대; 한계/깊게/예외/반례 → 허점. Explicit numeric depth selections use `5` → 그림, `10` → 길, `15` → 뼈대, and `20` → 허점. `Raft term 20`, `HTTP/2`, and `5개 노드` contain topic data, not depth choices.
```

Keep the jargon-default paragraph that begins `If the prompt already uses domain words` unchanged, including `default **뼈대**`.

Keep `Do not wait for a nod when they already chose the rung.` Change it to:

```markdown
Do not wait for a nod when the rung is filled by precedence. Pause when the slice is surprising or the topic is medical, legal, or financial — then read `references/stakes.md`.
```

Keep the Runtime block that contains every `RUNTIME_FLOW` phrase. After `fill slice, type, rung, language` you may add a comment line `missing rung → default 그림`, but the five existing phrases must still appear verbatim.

- [ ] **Step 2: Fix After EXPLAIN, dump gate, and red flags**

In `## After EXPLAIN`, after the four next-move bullets, add:

```markdown
그림's default next move is 길, naming a hop ID.
```

In the dump gate table, replace:

```markdown
| They asked 설명해줘 so answer now | Wrong type/rung wastes the answer. One question. |
| Topic is obvious | Announce type+rung. If they specified both, 바로. |
```

with:

```markdown
| They asked 설명해줘 so answer now | Missing slice still waits. Missing rung takes default 그림, announces, explains. |
| Topic is obvious | Announce type+rung. Explain same turn. |
```

Keep the remaining dump-gate rows, including `I'll explain the whole internet then zoom`.

In red flags, replace:

```markdown
- Essay in the same turn as the first classification when a slot is missing
```

with:

```markdown
- Essay in the same turn as the first classification when slice is missing
```

Keep `/eli5` handled as this skill, animals, omitted Mermaid, and 허점 that cannot collapse.

- [ ] **Step 3: Reorder chrome and 그림 recipes in `output.md`**

In the existing 4-backtick markdown template in `output.md`, move the two hop lines so they sit **above** the mermaid fence and **below** `## 지도 / Map`. After the edit the template body, inside the same fence style as today, must contain this exact order:

```text
## 지도 / Map

1. **H1** — {what moves or changes}
2. **H2** — {what moves or changes}

```
then a mermaid fence with `{diagram source}`, then `## 본문 / Body`. Do not change the heading strings. `test_output_chrome_is_common_markdown` checks this order with `str.index`.

Replace the 지도 bullet:

```markdown
- 지도: mermaid source, then the numbered hop list; caption is the diagram’s claim
```

with:

```markdown
- 지도: numbered hop list, then mermaid source; caption is the diagram’s claim
```

In `## Rung overlay`, replace the **그림** row:

```markdown
| **그림** | Happy-path pipeline, 5–7 boxes | Identity, use, ≤2-joint backbone. Optional one analogy plus one break line. | Baby talk, second metaphor, formulas, `여러분`, `답니다` |
```

with:

```markdown
| **그림** | Numbered hops first, then a happy-path pipeline, 5–7 boxes | Identity, use, ≤2-joint backbone. 그림 hops are the map; Body does not walk the hops again. Analogy, if used, comes after the hops, then the break line. | Baby talk, second metaphor, formulas, `여러분`, `답니다`, hop restatement |
```

In type recipes, replace the **흐름** row:

```markdown
| **흐름** | Walk the hops. 길 gets the sequence diagram. 그림 gets boxes only |
```

with:

```markdown
| **흐름** | 그림: Map hops only; Body is identity and use. 길 walks the hops on a sequence diagram |
```

- [ ] **Step 4: Update `visuals.md`**

After `Default: a fenced Mermaid block in the chat Markdown, plus a numbered hop list that still reads when the diagram is shown as source.`, add:

```markdown
At 그림, the numbered hops are the human map. Put them before the mermaid fence in Map. Mermaid stays required as interchange.
```

Replace:

```markdown
- 그림: ≤7 boxes (hard cap 12; over 12 means recut the slice)
```

with:

```markdown
- 그림: hops first, then ≤7 boxes (hard cap 12; over 12 means recut the slice)
```

- [ ] **Step 5: Update `korean.md`**

After `Gloss once: 리베이스(rebase), then one form.`, add:

```markdown
- Causal verbs: 묻다, 맡기다, 적어 두다, 만료되다.
- Open with a lived snag, then the joint. Do not open with a definition.
```

Replace the 그림 target block with:

```markdown
그림 target:

> 사이트 이름을 쳤는데, 패킷이 나갈 곳은 숫자 주소예요. DNS는 가까운 기억부터 보고, 없으면 이름 나무의 권한 있는 서버까지 물어 가는 조회예요.
```

Keep the forbidden 그림 example that contains `여러분이` and `답니다`. Do not write `컴퓨터는 숫자 주소를 본다`.

- [ ] **Step 6: Run the payload tests**

Run:

```bash
python3 tests/products/how-it-works/test_contract.py -v
```

Expected: `HowItWorksPayloadTests` PASS, including version `2.0.1` pins, `test_debug_and_eli5_do_not_enter_the_gate`, `test_explicit_easy_alias_precedes_jargon`, `test_missing_depth_explains_at_default_picture`, and `test_picture_body_does_not_restate_hops`. Do not bump version in this task. If a dump-gate or red-flag `assertIn` fails, restore that exact substring or update the assertion in this same task only when the spec replaced that substring.

- [ ] **Step 7: Commit**

```bash
git add skills/how-it-works/SKILL.md skills/how-it-works/references/output.md skills/how-it-works/references/visuals.md skills/how-it-works/references/korean.md
git commit -m "feat: default how-it-works explanations to 그림 in one turn"
```

---

### Task 5: Retarget 3.0.0 and the public first-call examples

**Files:**
- Modify: `skills/how-it-works/release.toml`
- Modify: `skills/how-it-works/SKILL.md` (frontmatter `metadata.version` and `updated_at` only)
- Modify: `skills/how-it-works/CHANGELOG.md`
- Modify: `skills/how-it-works/README.md`
- Modify: `skills/how-it-works/README.en.md`
- Modify: `docs/maintainers/products/how-it-works/contract.md`
- Modify: `docs/maintainers/products/how-it-works/release.md`
- Modify: `tests/products/how-it-works/test_contract.py` (version assertions)
- Modify: `tests/repository/test_release_contract.py`
- Test: `python3 scripts/verify.py --skill how-it-works` then `python3 scripts/verify.py`

**Interfaces:**
- Consumes: Task 4 payload behavior.
- Produces: shipped 3.0.0 metadata. Live quality remains `not_measured`.

- [ ] **Step 1: Find leftover 2.0.1 and old-gate strings**

```bash
rg -n "2\\.0\\.1|one necessary question|Do not silently pick a depth|추천 첫 칸은 길|DNS 길" skills/how-it-works tests/products/how-it-works tests/repository/test_release_contract.py docs/maintainers/products/how-it-works
```

Expected hits to change: `release.toml`, `SKILL.md` metadata, `test_contract.py` version methods, `test_release_contract.py` `EXPECTED` and the how-it-works archive/mutation tests, `contract.md` default 칸 and version, README first-call examples. Leave CHANGELOG `## 2.0.0` historical `one necessary question` alone. Leave live prompts that say `길을 보여줘`.

- [ ] **Step 2: Set the version to 3.0.0**

`skills/how-it-works/release.toml`: `version = "3.0.0"`.

`skills/how-it-works/SKILL.md` frontmatter:

```yaml
metadata:
  version: "3.0.0"
  updated_at: "2026-09-12"
```

Use the implementation-commit date if it is not 2026-09-12.

In `tests/products/how-it-works/test_contract.py` replace both `"2.0.1"` version assertions with `"3.0.0"`.

In `tests/repository/test_release_contract.py`:

- `"how-it-works": "3.0.0"`
- `test_how_it_works_current_archive_identity`: version `3.0.0`, tag `how-it-works-v3.0.0`, artifact `how-it-works-v3.0.0.zip`
- `test_one_product_version_can_change_without_changing_neighbors`: replace `2.0.1` with `3.0.0` and `2.0.2` with `3.0.1` in both the mutate string and the expected error `release.toml version 3.0.1 != SKILL.md version 3.0.0`

- [ ] **Step 3: Write the changelog entry**

Replace the empty `## Unreleased` body so the file begins:

```markdown
# Changelog

All notable changes to this product are documented in this file.

## Unreleased

## 3.0.0 - 2026-09-12

### Breaking

- Default rung is 그림. A missing depth is filled by precedence, announced
  in the intent line, and explained in the same turn. The old last step
  `one necessary question` is removed.
- Picture Map prints numbered hops before Mermaid source. Body at 그림
  does not walk the hops again.

### Changed

- `감이 안 와` is a silent 그림 alias. Type word `흐름` still does not fill
  rung. Jargon without a depth alias remains 뼈대.
- First-call README examples use `$how-it-works DNS` / `/how-it-works DNS`.
  Explicit `DNS 길` remains a path example.

### Notes

- Live model quality stays `not_measured`. Fixture pass is not host
  execution evidence. No GitHub tag or GitHub Release is created.

## 2.0.1 - 2026-09-11
```

Keep 2.0.1 and older sections after that heading. Keep the 2.0.0 historical `one necessary question` sentence.

- [ ] **Step 4: Update READMEs without touching the install fence**

In `skills/how-it-works/README.md` `## 첫 호출`, replace the fenced examples with:

```text
$how-it-works DNS
/how-it-works DNS
```

Immediately after that fence, add:

```markdown
명시 길은 그대로입니다.

```text
$how-it-works DNS 길
/how-it-works DNS 길
```
```

In the expected-result skeleton, put the numbered hop list above the mermaid fence, matching `OUTPUT_CHROME`.

In `skills/how-it-works/README.en.md` `## First call`, replace the fenced examples with:

```text
$how-it-works DNS
/how-it-works DNS
```

Then add the explicit path example:

```text
$how-it-works Explain DNS as a path.
/how-it-works Explain DNS as a path.
```

Reorder the English skeleton the same way: hops, then mermaid.

Do not edit bytes inside the `<!-- how-it-works-local-links -->` Python fence.

- [ ] **Step 5: Update maintainer contract and release prose**

In `docs/maintainers/products/how-it-works/contract.md` `## 트리거와 기본값`, replace the paragraph that names picker default 길 and `one necessary question` with:

```markdown
설명 전에 `slice`, `type`, `rung`, `language`를 채웁니다. type과 language는
추론합니다. 칸은 그림, 길, 뼈대, 허점이며 picker의 추천 첫 칸은 그림입니다.
깊이 우선순위는 `explicit rung > explicit depth alias > existing jargon default
> default 그림`입니다. 명시한 그림/길/뼈대/허점 또는
picture/path/skeleton/fracture가 가장 먼저 적용됩니다.
`쉽게`/`한눈에`/`한 장`/`감이 안 와`는 jargon(`rebase`, `TTL`, `Raft`)이
있어도 그림입니다. jargon 기본 뼈대는 명시한 rung이나 깊이 별칭이 없을 때만
적용합니다. 숫자 별칭 `5→그림`, `10→길`, `15→뼈대`, `20→허점`은 깊이를
명시적으로 고른 경우에만 해석합니다. `Raft term 20`, `HTTP/2`, `5개 노드`의
숫자는 주제 데이터입니다. 채워진 칸은 바꾸지 않습니다. 깊이가 비면 기본
그림을 intent에 알리고 같은 턴에서 설명합니다.
```

In `## 출력`, after the six-item list, add:

```markdown
그림의 지도 절은 번호 홉이 머메이드 소스보다 앞입니다. 그림 본문은 홉을
다시 걷지 않습니다.
```

In `## 버전과 설치`, replace `현재 제품 계약 버전은 \`2.0.0\`입니다` with `현재 제품 계약 버전은 \`3.0.0\`입니다`. Replace the `2026-09-08` implementation-date sentence with the same date used in `metadata.updated_at`.

In `docs/maintainers/products/how-it-works/release.md`, keep the MAJOR example that already names 기본 칸. After the SemVer list, add:

```markdown
3.0.0은 기본 칸을 그림으로 바꾸고 깊이 질문을 제거한 MAJOR입니다.
```

- [ ] **Step 6: Verify the product, then the repository**

```bash
python3 tests/products/how-it-works/test_contract.py -v
echo "CONTRACT_EXIT=$?"
python3 scripts/verify.py --skill how-it-works
echo "SKILL_EXIT=$?"
python3 scripts/verify.py
echo "REPO_EXIT=$?"
git diff --check
git diff -- catalog
```

Expected: all exits 0. `catalog/` diff empty. `test_contract.py` does not fail on live `LIVE_CASES_PAYLOAD`; that blob stays the three historical prompts.

- [ ] **Step 7: Commit**

```bash
git add skills/how-it-works/release.toml skills/how-it-works/SKILL.md skills/how-it-works/CHANGELOG.md skills/how-it-works/README.md skills/how-it-works/README.en.md docs/maintainers/products/how-it-works/contract.md docs/maintainers/products/how-it-works/release.md tests/products/how-it-works/test_contract.py tests/repository/test_release_contract.py
git commit -m "release: how-it-works 3.0.0 defaults to 그림"
```

---

## Self-review

**Spec coverage**

| Spec decision | Task |
| --- | --- |
| Default 그림, no depth question | 1–4 |
| Precedence explicit > alias > jargon 뼈대 > default 그림 | 3–4 |
| `감이 안 와` alias | 3–4 |
| 자르기 / `/eli5` / high-stakes unchanged | 4 (kept rows) + 2 (`broad-slice` untouched) |
| Hop-first Map, Body does not restate | 3–4 |
| Six deliverables required | 1 fixtures still list all six |
| 3.0.0 MAJOR | 5 |
| Live out of scope, `not_measured` | Global + Task 5 Notes |
| Together-files | 2, 4, 5 |
| README first call `$how-it-works DNS` | 5 |
| Install Python fence untouched | Task 5 Step 4 |

**Placeholder scan:** none. **Type consistency:** `default-dns-picture`, `default 그림`, `OUTPUT_CHROME` hop-then-mermaid, version `3.0.0` are the same names in every task.
