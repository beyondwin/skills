# pre-sdd-review 5.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 발견은 겹치고 수리는 직렬이며, 종결은 수리 diff만 보고, dirty가 아니면 0건 발견은 종결을 건너뛰는 pre-sdd-review `5.0.0` 컨트롤러 계약을 만든다.

**Architecture:** 새 런타임은 없다. 스케줄 규칙은 SKILL.md가 소유하고, 합성 그래프 테스트가 그 규칙을 고정한다. 프로토콜·계약·README·cases·handshake `cli_version`을 같은 뜻으로 맞춘다. record schema는 4로 둔다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, `unittest`, Git. 새 의존성 없음.

**Spec:** [docs/history/specs/2026-09-19-pre-sdd-review-5.0.0-design.md](../specs/2026-09-19-pre-sdd-review-5.0.0-design.md)

## Global Constraints

- 수정 대상은 `skills/pre-sdd-review/`, `tests/products/pre-sdd-review/`, `docs/maintainers/products/pre-sdd-review/`, `tests/repository/test_release_contract.py`만이다.
- 제품 버전은 `5.0.0`, 날짜는 `2026-09-19`다. schema는 `4`. handshake는 `{"cli_version":"5.0.0","schema":4,"skill_name":"pre-sdd-review"}`다.
- 새 실행 파일·원장 파서·dirty record 키를 만들지 않는다. 스케줄 함수는 `test_campaign_schedule.py`에만 둔다.
- 호스트 지원표와 `docs/users/`는 바꾸지 않는다.
- 권위 순서, 수정 허용 목록, 판정 어휘, 역할 상한 둘, 수리 패스 상한 둘, `no-aggregate-ready`는 유지한다.
- 태그와 GitHub Release는 만들지 않는다.
- 테스트는 저장소 루트에서 `PYTHONDONTWRITEBYTECODE=1`을 붙인다.

## Review Focus

- 공유 설계만 겹치고 `Files:`는 거의 다른 두 계획: A 수리가 B를 dirty로 만든다.
- 호스트 `k=1`: 발견도 직렬이며 합법, 재사용 0.
- 캠페인 중 `HEAD`가 움직이면 그 freeze에 대해 READY를 내지 않는다.
- `review-only`는 발견만 겹치고 수리·종결이 없다.
- 같은 계획 `pending`은 여전히 새 `start` 전에 닫는다. 다른 계획 `pending`은 닫지 않는다.

## 공통 도구: digest 재계산

문서를 바꾼 뒤 `test_contract.py` digest가 깨지면:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import hashlib, importlib.util
spec = importlib.util.spec_from_file_location("tc", "tests/products/pre-sdd-review/test_contract.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
contract = (m.MAINTAINERS / "contract.md").read_text(encoding="utf-8")
print("MAINTAINER_CANONICAL_DIGEST", m.canonical_digest(contract))
for heading, _ in m.MAINTAINER_CANONICAL_SUBSECTION_DIGESTS:
    print(heading, m.canonical_digest(m.subsection(contract, heading)))
print("TESTING_CANONICAL_DIGEST", m.whole_document_digest((m.MAINTAINERS / "testing.md").read_text(encoding="utf-8")))
for name in ("SKILL.md", "references/reviewer-protocol.md"):
    print("INSTRUCTION", name, hashlib.sha256((m.SKILL / name).read_bytes()).hexdigest())
PY
```

---

### Task 1: 합성 캠페인 스케줄 테스트

**Files:**
- Create: `tests/products/pre-sdd-review/test_campaign_schedule.py`
- Test: 같은 파일

**Interfaces:**
- Produces: 테스트 파일 로컬 함수 `waves(order, files) -> list[list[str]]`, `dirty_after(repaired, files, designs, evidence) -> set[str]`, `assign_discovery(plans, k) -> list[tuple[str, int]]` (plan, agent_id). 제품 모듈 없음.
- Consumes: 없음.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/products/pre-sdd-review/test_campaign_schedule.py`:

```python
from __future__ import annotations

import unittest
from collections import defaultdict


def waves(order: list[str], files: dict[str, set[str]]) -> list[list[str]]:
    preds: dict[str, set[str]] = defaultdict(set)
    for i, a in enumerate(order):
        for b in order[i + 1 :]:
            if files[a] & files[b]:
                preds[b].add(a)
    remaining = set(order)
    out: list[list[str]] = []
    while remaining:
        wave = [t for t in order if t in remaining and not (preds[t] & remaining)]
        if not wave:
            raise AssertionError(f"stuck {remaining}")
        out.append(wave)
        remaining -= set(wave)
    return out


def dirty_after(
    repaired: str,
    order: list[str],
    files: dict[str, set[str]],
    designs: dict[str, str],
    delta_paths: set[str],
    delta_design: str | None,
) -> set[str]:
    dirty: set[str] = set()
    i = order.index(repaired)
    for later in order[i + 1 :]:
        read = set(files[later]) | {designs[later]}
        if delta_paths & read or (delta_design and designs[later] == delta_design):
            dirty.add(later)
    return dirty


def assign_discovery(plans: list[str], k: int) -> list[tuple[str, int]]:
    if k < 1:
        raise ValueError("k")
    assigned: list[tuple[str, int]] = []
    used: set[int] = set()
    slot = 0
    for plan in plans:
        if len(used) == k:
            used.clear()
        while slot in used:
            slot += 1
        assigned.append((plan, slot))
        used.add(slot)
        slot += 1
    agents = [agent for _, agent in assigned]
    if len(agents) != len(set(agents)):
        raise AssertionError("reused agent across plans")
    return assigned


class CampaignScheduleTests(unittest.TestCase):
    order = ["A", "B", "C", "D"]
    files = {
        "A": {"ui.ts", "spec.md"},
        "B": {"api.java", "spec.md"},
        "C": {"ui.ts"},
        "D": {"other.ts"},
    }
    designs = {"A": "spec.md", "B": "spec.md", "C": "c.md", "D": "d.md"}

    def test_waves_serialize_on_shared_files(self) -> None:
        self.assertEqual(waves(self.order, self.files), [["A", "D"], ["B", "C"]])

    def test_repairs_are_serial_in_order(self) -> None:
        seen: list[str] = []
        for plan in self.order:
            self.assertNotIn(plan, seen)
            seen.append(plan)
        self.assertEqual(seen, self.order)

    def test_shared_design_dirties_later_plan(self) -> None:
        self.assertEqual(
            dirty_after("A", self.order, self.files, self.designs, set(), "spec.md"),
            {"B"},
        )

    def test_file_delta_dirties_consumer(self) -> None:
        self.assertEqual(
            dirty_after("A", self.order, self.files, self.designs, {"ui.ts"}, None),
            {"C"},
        )

    def test_zero_findings_skip_closure_unless_dirty(self) -> None:
        dirty = dirty_after("A", self.order, self.files, self.designs, {"ui.ts"}, None)
        skip = {p for p in self.order if p not in dirty and p != "A"}
        self.assertIn("B", skip)
        self.assertIn("D", skip)
        self.assertNotIn("C", skip)

    def test_jobserver_k2_never_reuses_agent(self) -> None:
        assigned = assign_discovery(self.order, 2)
        self.assertEqual(len({agent for _, agent in assigned}), 4)
        self.assertLessEqual(max(agent for _, agent in assigned), 3)

    def test_k1_is_serial_and_legal(self) -> None:
        assigned = assign_discovery(self.order, 1)
        self.assertEqual([p for p, _ in assigned], self.order)
        self.assertEqual(len({agent for _, agent in assigned}), 4)
```

- [ ] **Step 2: 테스트 실행**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.test_campaign_schedule -v`
Expected: `Ran 7 tests` … `OK` (함수가 테스트 파일에 있으므로 이 Task는 구현과 테스트가 같다. 실패하면 함수를 고친다. 제품 코드를 만들지 않는다.)

- [ ] **Step 3: 커밋**

```bash
git add tests/products/pre-sdd-review/test_campaign_schedule.py
git commit -m "test(pre-sdd-review): pin campaign wave, dirty, and jobserver rules"
```

---

### Task 2: SKILL.md와 종결 지시

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md` (Resolve authoritative inputs, Capture freshness, Default mode, Machine checks, Select reviewers, Review-only, Red flags)
- Modify: `skills/pre-sdd-review/references/reviewer-protocol.md` (Discovery dispatch 동결, Closure dispatch에 수리 diff)
- Test: `tests/products/pre-sdd-review/test_contract.py` 해당 단언

**Interfaces:**
- Produces: 스펙 R1–R5의 SKILL·프로토콜 문장. Task 3가 계약·README에서 같은 뜻을 따른다.

- [ ] **Step 1: 실패하는 단언**

`test_unreleased_convergence_contract_has_one_bounded_terminal_loop`에서 `self.assertIn("do not overlap them", skill)`을 다음으로 바꾼다:

```python
        self.assertIn("Discoveries of different plans may overlap", skill)
        self.assertIn("Repairs do not overlap", skill)
        self.assertNotIn("do not overlap them", skill)
```

`test_controller_sections_and_transitions_are_ordered`의 상태기계 정규식은 캠페인 기계를 허용하도록, 워크플로 절에 아래 조각이 있는지로 바꾼다 (기존 한 줄 화살표 전체를 삭제하지 말고 **추가** 단언):

```python
        self.assertIn("Discoveries of different plans may overlap", workflow)
        self.assertIn("skip repair and closure", workflow)
        self.assertIn("unless that plan is dirty", workflow)
        self.assertIn("repair diff", workflow)
```

`test_protocol_dispatch`류가 없으면 `test_reviewer_is_read_only_and_controller_owns_repairs` 뒤에:

```python
    def test_closure_dispatch_requires_repair_diff(self) -> None:
        protocol = (SKILL / "references/reviewer-protocol.md").read_text(encoding="utf-8")
        self.assertIn("The repair diff of the resolved design, plan, and ledger", protocol)
        self.assertIn("H0", protocol)
```

Red flags 튜플에 추가:

```python
            "Overlap repairs of two plans on one host",
            "Reuse a reviewer to fill a discovery wave",
            "Print READY after HEAD moved from the freeze",
            "Skip closure for a dirty plan with zero discovery findings",
```

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"`
Expected: 위 문구 부재로 FAIL.

- [ ] **Step 3: SKILL.md Resolve 절**

`:43-46`의

```text
first of those invocations, run the pre-pass below once. On one host, run
those invocations one after another; do not overlap them. Do not emit an
aggregate `READY`. If a later invocation changes a shared design, rerun every
earlier plan whose evidence depended on the previous design fingerprint.
```

을

```text
first of those invocations, run the pre-pass below once. That pre-pass freezes
document hashes as H0 and Git HEAD as H_git0. Discoveries of different plans
may overlap. Repairs do not overlap. Do not emit an aggregate `READY`. A later
repair that changes a shared design marks every dependent plan dirty in this
campaign; do not open a new campaign for that invalidation.
```

으로 바꾼다.

- [ ] **Step 4: Default mode 0건 발견과 종결 diff**

`:225-227`의 “If the first review has zero findings, skip repair and closure and return `READY`.”를

```text
If the first review has zero findings and the plan is not dirty, skip repair
and closure and return `READY`. A dirty plan still takes scoped closure.
```

으로 바꾼다.

`:255-258` “Give a fresh reviewer the final repaired documents, original findings, and any repair-impact map.” 앞에 한 문장을 넣는다:

```text
The closure instruction must include the repair diff of the resolved design,
plan, and ledger, even when the repair-impact map is empty.
```

캠페인 안쪽 순서를 Default mode 상태기계 블록 **아래**에 짧은 목록으로 추가한다. 기존 한 호출 화살표는 `n=1`용으로 남긴다:

```text
When the outer request names two or more plans, after the pre-pass:

1. Discovery in host-sized waves of fresh agents. No verdict.
2. Serial repair in execution order. Update dirty from each delta.
3. Closure only for repaired or dirty plans, in parallel up to the host cap.
4. At most one more serial repair + closure per plan. Then plan-local verdicts.
```

- [ ] **Step 5: freshness HEAD, 기계점검 6, jobserver, review-only, red flags**

Capture freshness에 한 문단:

```text
The pre-pass records H_git0 with H0. If HEAD moves off H_git0 before verdicts,
do not return READY against that freeze. Abandon in-flight runs with
`input-changed`. A new freeze needs an outer request. Do not narrow
`head_changed_during_review` to files the plan named.
```

Select reviewers, “If a fresh independent primary reviewer cannot be obtained, return `BLOCKED`.” 뒤에:

```text
If the host can supply only k fresh agents, run discovery in waves of k.
Do not reuse an agent across plans to fill a wave.
```

Machine checks 목록 5번 뒤에:

```text
6. Every backticked repository path in the plan exists at that plan's turn.
   Exclude paths any plan in the chain lists under `Create:`. Excluding only
   the current plan's `Create:` yields false positives.
```

Review-only 절 끝에:

```text
Named multi-plan `review-only` may overlap discoveries. It still makes no
file changes and returns each plan's first-review verdict. There is no
repair epoch and no dirty set.
```

Red flags에 Step 1의 네 줄을 추가한다. “Do not automatically start another invocation after `REVISE` or `BLOCKED`.”는 그대로 둔다.

Discovery dispatch에 “Documents are the H0 bytes, not a live unsaved buffer.”를 한 줄 넣는다. Closure dispatch 목록 맨 위에:

```text
- The repair diff of the resolved design, plan, and ledger. Required even
  when the repair-impact map is empty.
```

- [ ] **Step 6: digest 후 통과**

공통 도구로 SKILL.md·protocol SHA를 `INSTRUCTION_DOCUMENT_SHA256`에 붙인다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | tail -5`
Expected: digest·계약 단언 외 FAIL는 Task 3 몫. Task 2가 넣은 문구 단언은 통과.

- [ ] **Step 7: 커밋**

```bash
git add skills/pre-sdd-review/SKILL.md skills/pre-sdd-review/references/reviewer-protocol.md tests/products/pre-sdd-review/test_contract.py
git commit -m "fix(pre-sdd-review): overlap discoveries, serialize repairs, require closure diffs"
```

---

### Task 3: 계약, cases, README, testing.md

**Files:**
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md`
- Modify: `docs/maintainers/products/pre-sdd-review/testing.md`
- Modify: `skills/pre-sdd-review/README.md`, `README.en.md`
- Modify: `tests/products/pre-sdd-review/cases.json`
- Test: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: Task 2 문장.
- Produces: cases id 다섯, expect 태그, 계약 토큰.

- [ ] **Step 1: 실패하는 단언**

`CASE_IDS`에서 `"degraded-handoff-not-reused",` 뒤에 추가:

```python
    "zero-findings-but-dirty",
    "closure-requires-repair-diff",
    "host-limit-waves-not-reuse",
    "head-break-no-ready",
    "no-automatic-second-campaign",
```

`len(CASE_IDS)`를 41로, testing.md 단언의 사례 수를 마흔하나로.

```python
        self.assertEqual(
            cases["serialize-split-plans"],
            (
                "discoveries_may_overlap",
                "repairs_do_not_overlap",
                "no_aggregate_ready",
                "reviewers_are_distinct_agents",
            ),
        )
        self.assertEqual(
            cases["zero-findings-but-dirty"],
            ("dirty_requires_closure", "zero_findings_skip_only_when_not_dirty"),
        )
        self.assertEqual(
            cases["closure-requires-repair-diff"],
            ("repair_diff_required",),
        )
        self.assertEqual(
            cases["host-limit-waves-not-reuse"],
            ("wave_by_host_cap", "no_reuse_to_fill"),
        )
        self.assertEqual(
            cases["head-break-no-ready"],
            ("no_ready_after_head_moves", "abandon_input_changed"),
        )
        self.assertEqual(
            cases["no-automatic-second-campaign"],
            ("no_automatic_reinvoke",),
        )
```

`test_maintainer_testing_compatibility_and_release_stay_role_specific`의 “하지 않는 것”에서 `"shared-design invalidation map"`을 빼고, 계약에 `"컨트롤러 로컬 dirty"`가 있음을 단언한다. `"closure-only input schema"`와 `"evidence probe cache"`는 남긴다.

계약 본문에 `겹치지 않고`가 있으면 발견/수리 분리 문구로 단언을 바꾼다.

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"`
Expected: cases 수·expect·하지 않는 것 FAIL.

- [ ] **Step 3: cases.json**

`serialize-split-plans` expect를 Step 1 네 태그로 바꾼다. `degraded-handoff-not-reused` 뒤에 다섯 사례를 넣는다. request는 `$pre-sdd-review`와 계획 두 개를 이름 대는 한 줄이면 충분하다.

- [ ] **Step 4: contract.md**

활성화 절 “같은 호스트에서는 나눈 호출을 겹치지 않고 하나씩 실행합니다.”를 “발견은 겹칠 수 있고 수리는 겹치지 않습니다.”로 바꾼다. 기본 흐름에 dirty면 0건이어도 종결, 종결에 수리 diff 필수, HEAD 동결 깨지면 READY 금지를 한 문단으로 넣는다. `## 하지 않는 것`에서 `shared-design invalidation map`을 지우고 `컨트롤러 로컬 dirty 집합`이 이번 판의 무효화라고 적는다. Contract 토큰에 `campaign-scheduler`: `discoveries-may-overlap`, `repairs-do-not-overlap`를 더한다.

- [ ] **Step 5: README 두 벌과 testing.md**

README.en.md “Split plans on one host run one after another.”를 “Discoveries of split plans may overlap; repairs do not. Closure requires the repair diff.”로. 한국어 README 대응 문장도 같은 뜻. testing.md 사례 수를 마흔하나, Case inventory에 다섯 id.

- [ ] **Step 6: digest 후 통과**

공통 도구로 MAINTAINER·TESTING digest를 붙인다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | tail -3`
Expected: `OK`. handshake `cli_version` 단언은 Task 4.

- [ ] **Step 7: 커밋**

```bash
git add docs/maintainers/products/pre-sdd-review/contract.md docs/maintainers/products/pre-sdd-review/testing.md skills/pre-sdd-review/README.md skills/pre-sdd-review/README.en.md tests/products/pre-sdd-review/cases.json tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): state overlapping discovery and dirty closure in the contract"
```

---

### Task 4: 버전 5.0.0과 handshake

**Files:**
- Modify: `skills/pre-sdd-review/release.toml`, `SKILL.md` frontmatter, `CHANGELOG.md`, `evidence/evidence.py` `CLI_VERSION`, `evidence/README.md`
- Modify: `tests/products/pre-sdd-review/evidence/test_evidence.py` `VERSION_LINE`
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md` handshake 줄
- Test: `tests/products/pre-sdd-review/test_contract.py` `TARGET_VERSION`, changelog 날짜; `tests/repository/test_release_contract.py`

**Interfaces:**
- Consumes: Task 1–3.
- Produces: 설치 버전 `5.0.0`, schema `4`.

- [ ] **Step 1: 실패하는 단언**

`TARGET_VERSION = "5.0.0"`. changelog 날짜 단언을 `## 5.0.0 - 2026-09-19`. `test_release_contract.py`의 `"pre-sdd-review": "4.0.0"`과 tag/artifact `pre-sdd-review-v4.0.0`을 `5.0.0`으로. `VERSION_LINE`을 `b'{"cli_version":"5.0.0","schema":4,"skill_name":"pre-sdd-review"}\n'`.

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p test_release_contract.py 2>&1 | tail -3`
Expected: FAILED.

- [ ] **Step 3: 버전 값**

`release.toml` `version = "5.0.0"`. SKILL.md `version: "5.0.0"`, `updated_at: "2026-09-19"`. `evidence.py` `CLI_VERSION = "5.0.0"`. SCHEMA는 4. contract.md·evidence README의 정규 줄을 새 handshake로. CHANGELOG `## Unreleased` 아래에:

```markdown
## 5.0.0 - 2026-09-19

### Changed

- Multi-plan discovery may overlap. Repairs stay serial. Closure requires a repair diff.
- A dirty plan with zero discovery findings still takes scoped closure.
- Host agent limits wave discoveries; they do not reuse a reviewer across plans.
- HEAD moving off the freeze blocks READY on that freeze.

### Notes

- Record schema stays 4. Handshake `cli_version` is 5.0.0. No GitHub tag or GitHub Release is created.
```

- [ ] **Step 4: SKILL SHA 재갱신 후 검증**

frontmatter가 바뀌었으므로 SKILL.md SHA를 다시 붙인다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review`
Expected: exit 0.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py`
Expected: exit 0. 라이브 `--execute`는 돌리지 않는다.

- [ ] **Step 5: 커밋**

```bash
git add skills/pre-sdd-review/release.toml skills/pre-sdd-review/SKILL.md skills/pre-sdd-review/CHANGELOG.md skills/pre-sdd-review/evidence/evidence.py skills/pre-sdd-review/evidence/README.md docs/maintainers/products/pre-sdd-review/contract.md tests/products/pre-sdd-review/test_contract.py tests/products/pre-sdd-review/evidence/test_evidence.py tests/repository/test_release_contract.py
git commit -m "chore(pre-sdd-review): release 5.0.0"
```

커밋 뒤 `python3 scripts/release.py check --product pre-sdd-review`.

---

## 자체 점검

- 스펙 R1 → Task 2 Step 3·4. R2 → Task 2 Step 5, Task 1 jobserver. R3 → Task 1 dirty, Task 2 0건+dirty. R4 → Task 2 closure diff. R5 → Task 2 HEAD·review-only. R6 → Task 1·3. 완료 기준 handshake → Task 4.
- 스펙이 빼라고 한 `ledger-pass` run, dirty record 키, 원장 파서, 라이브 execute는 어떤 Task에도 없다.
- Review Focus 다섯은 Task 1(설계 dirty, k=1)과 Task 2(HEAD, review-only, same-plan pending은 기존 문구 유지)에 있다.
