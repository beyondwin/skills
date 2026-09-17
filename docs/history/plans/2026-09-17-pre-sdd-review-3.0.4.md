# pre-sdd-review 3.0.4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `finish`가 이 run의 관찰 이상을 직접 돌려주고, 컨트롤러 재사용 규칙을 기록된 `execution` 값으로 분기하며, 심각도 정의를 판정 규칙에 맞춰 pre-sdd-review `3.0.4`를 만든다.

**Architecture:** 기록기(`evidence.py`)에 헬퍼 둘과 `finish` 출력 키 하나를 추가한다. SKILL.md·contract.md·README·evidence README의 문구를 그 출력과 새 재사용 규칙에 맞춘다. reviewer-protocol.md의 심각도 정의를 수리 가능성으로 다시 쓰고 픽스처 둘을 조정한다. 계약 테스트의 문구·digest 상수를 함께 갱신하고 버전을 올린다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, `unittest`, Git. 새 의존성 없음.

**Spec:** [docs/history/specs/2026-09-17-pre-sdd-review-3.0.4-design.md](../specs/2026-09-17-pre-sdd-review-3.0.4-design.md)

## Global Constraints

- 수정 대상은 `skills/pre-sdd-review/`, `tests/products/pre-sdd-review/`, `docs/maintainers/products/pre-sdd-review/`, `tests/repository/test_release_contract.py`만이다.
- record 형식과 `schema=3`, `--version` 정규 줄 `{"cli_version":"3.0.0","schema":3,"skill_name":"pre-sdd-review"}`는 바꾸지 않는다. `CLI_VERSION`은 `"3.0.0"` 그대로다.
- Python 3.11 이상, 표준 라이브러리만 쓴다.
- 호스트 지원표(`compatibility.md`, `products.toml`)와 `docs/users/`는 바꾸지 않는다.
- 판정 규칙, 권위 순서, 수정 허용 목록, 리뷰 역할 상한 둘, 수정 패스 상한 둘은 바꾸지 않는다.
- 제품 버전은 `3.0.4`, 날짜는 `2026-09-17`이다. 태그와 GitHub Release는 만들지 않는다.
- 모든 테스트 명령은 `PYTHONDONTWRITEBYTECODE=1`을 붙여 저장소 루트에서 실행한다.
- 커밋 메시지는 기존 규칙(`fix(pre-sdd-review): ...`, `docs(pre-sdd-review): ...`)을 따른다.

## 공통 도구: digest 재계산

Task 3, 4, 5에서 문서를 바꾸면 `test_contract.py`의 digest 상수가 깨진다. 아래 스크립트로 새 값을 출력해 상수에 붙인다. 문구 단언을 먼저 고치고 테스트가 digest 오류만 남길 때 실행한다.

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

### Task 1: `finish`가 이 run의 anomalies를 반환

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py:511-533` (observation_anomalies 뒤), `:703-730` (cmd_finish), `:772-908` (summarize)
- Modify: `skills/pre-sdd-review/evidence/README.md:59`, `:83-85`
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py:206-213`, 새 테스트 추가
- Test: `tests/products/pre-sdd-review/evidence/test_hardening.py:133-139`

**Interfaces:**
- Produces: `evidence.finding_anomalies(record: dict) -> list[dict[str, object]]` (각 항목 `{"name": str, "finding_id": str}`), `evidence.run_anomalies(record: dict) -> list[str]` (정렬·중복 제거), `finish` stdout JSON 키 `anomalies: list[str]`.
- Consumes: 기존 `observation_anomalies(record) -> list[str]`, `summarize(records)`.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/products/pre-sdd-review/evidence/test_evidence.py`의 `FinishTests` 클래스 끝(`test_finish_rejects_records_over_the_size_limit` 뒤)에 추가:

```python
    def test_finish_returns_this_runs_anomalies(self) -> None:
        code, out, err = finish(self.home, self.repo, self.run_id, finish_payload())
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["anomalies"], [])

        unusual = start(self.home, self.repo, self.skill)
        payload = finish_payload(
            reviewers=2,
            findings=[finding(**{"class": "repo-reality"}, evidence=["docs/plan.md"])],
        )
        code, out, err = finish(self.home, self.repo, unusual, payload)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            json.loads(out),
            {
                "anomalies": [
                    "finding_repair_pass_exceeds_total",
                    "full_reviewer_count_mismatch",
                    "repo_reality_citing_documents_only",
                ],
                "run_id": unusual,
                "status": "completed",
                "verdict": "READY",
            },
        )
        record = load(self.home, unusual)
        self.assertEqual(
            evidence.finding_anomalies(record),
            [{"name": "repo_reality_citing_documents_only", "finding_id": "PSDR-001"}],
        )
        self.assertEqual(evidence.run_anomalies(load(self.home, self.run_id)), [])

        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        summary = json.loads(out)
        self.assertEqual(summary["anomalies"]["full_reviewer_count_mismatch"], [unusual])
        self.assertEqual(
            summary["anomalies"]["repo_reality_citing_documents_only"],
            [{"run_id": unusual, "finding_id": "PSDR-001"}],
        )
        self.assertEqual(summary["counts"]["observation"], {"normal": 1, "anomalous": 1})
```

`finding()` 기본값은 `repair_pass=1`이고 `finish_payload()` 기본값은 `repair_passes=0`이므로 `finding_repair_pass_exceeds_total`이 함께 나온다. 이는 의도한 관찰이다.

같은 파일 `:213`의 exact-dict 단언을 바꾼다:

```python
        self.assertEqual(
            json.loads(out),
            {"anomalies": [], "run_id": self.run_id, "status": "completed", "verdict": "READY"},
        )
```

`tests/products/pre-sdd-review/evidence/test_hardening.py:136-139`의 단언을 바꾼다:

```python
        self.assertEqual(
            json.loads(out),
            {"anomalies": [], "run_id": run_id, "status": "completed", "verdict": "READY"},
        )
```

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_*.py' 2>&1 | tail -5`
Expected: `FAILED (failures=2, errors=1)` — 새 테스트는 `KeyError: 'anomalies'`로 error, 기존 두 exact-dict 단언은 failure.

- [ ] **Step 3: 헬퍼 구현**

`skills/pre-sdd-review/evidence/evidence.py`에서 `observation_anomalies` 함수 정의 바로 뒤(현재 `def _object(` 앞)에 추가:

```python
def finding_anomalies(record: dict[str, object]) -> list[dict[str, object]]:
    """Per-finding observations for a completed record; never rejudges the verdict."""
    if record["status"] != "completed":
        return []
    plan = record["plan"]
    design = record["design"]
    assert isinstance(plan, dict)
    documents = {str(plan["path"])}
    if isinstance(design, dict):
        documents.add(str(design["path"]))
    entries: list[dict[str, object]] = []
    for item in record["findings"]:
        assert isinstance(item, dict)
        if item["class"] == "repo-reality" and set(item["evidence"]) <= documents:
            entries.append(
                {"name": "repo_reality_citing_documents_only", "finding_id": str(item["id"])}
            )
    return entries


def run_anomalies(record: dict[str, object]) -> list[str]:
    """All observation anomaly names for one record, sorted and unique."""
    names = set(observation_anomalies(record))
    names.update(str(entry["name"]) for entry in finding_anomalies(record))
    return sorted(names)
```

- [ ] **Step 4: `cmd_finish` 반환값 변경**

`cmd_finish` 마지막 줄

```python
        return {"run_id": args.run_id, "status": "completed", "verdict": record["verdict"]}
```

을

```python
        return {
            "run_id": args.run_id,
            "status": "completed",
            "verdict": record["verdict"],
            "anomalies": run_anomalies(record),
        }
```

으로 바꾼다. `write_json`이 정규 직렬화(키 정렬)를 하므로 출력 순서는 `anomalies, run_id, status, verdict`다.

- [ ] **Step 5: `summarize`가 헬퍼를 쓰도록 변경**

`summarize` 안의

```python
        documents = {str(plan["path"])}
        if isinstance(design, dict):
            documents.add(str(design["path"]))
        for item in findings:
```

을

```python
        for entry in finding_anomalies(record):
            anomalies[str(entry["name"])].append(
                {"run_id": run_id, "finding_id": entry["finding_id"]}
            )
            anomalous_run_ids.add(run_id)
        for item in findings:
```

으로 바꾸고, 같은 루프 안의 다음 다섯 줄을 삭제한다:

```python
            if item["class"] == "repo-reality" and set(item["evidence"]) <= documents:
                anomalies["repo_reality_citing_documents_only"].append(
                    {"run_id": run_id, "finding_id": item["id"]}
                )
                anomalous_run_ids.add(run_id)
```

- [ ] **Step 6: 통과 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review/evidence -p 'test_*.py' 2>&1 | tail -3`
Expected: `Ran 62 tests` … `OK`

- [ ] **Step 7: evidence README 갱신**

`skills/pre-sdd-review/evidence/README.md:59`의 `finish` 행 마지막 칸을

```text
Require the original checkout binding, recompute end hashes and Git state, validate, write `completed`, print `run_id`, `verdict`, and this run's `anomalies`
```

로 바꾼다. `:83-85`의

```text
The log is for agents. Before `start`, run `summary --last 20`. Close a
same-plan `pending` run; if the latest `REVISE` or `BLOCKED` hashes still
match, reuse that handoff. `summary` returns `runs`, `counts`, `cost`, `chains`
```

을

```text
The log is for agents. Before `start`, run `summary --repo <display name>`
and find the plan in `runs` and `chains`. Close a same-plan `pending` run.
Never reuse the handoff of a run whose `execution` is `blocked`; for a `full`
or `degraded` `REVISE` or `BLOCKED` run, reuse it only when its document
hashes, `git.head_end`, and the request are all unchanged. After `finish`,
print the `anomalies` it returned; do not look the run up in a windowed
`summary`. `summary` returns `runs`, `counts`, `cost`, `chains`
```

으로 바꾼다. README는 `PreSddReviewDocumentationTests`가 읽으므로 contract suite도 돌린다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | tail -3`
Expected: `Ran 56 tests` … `OK`. FAIL이면 README에서 지운 문구를 단언과 대조한다.

- [ ] **Step 8: 커밋**

```bash
git add skills/pre-sdd-review/evidence/evidence.py skills/pre-sdd-review/evidence/README.md tests/products/pre-sdd-review/evidence/test_evidence.py tests/products/pre-sdd-review/evidence/test_hardening.py
git commit -m "fix(pre-sdd-review): return this run's anomalies from finish"
```

---

### Task 2: SKILL.md 재사용 규칙·재질의 지침·보고 문구

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md:79-82`, `:121`, `:230-233`, `:242-251`
- Test: `tests/products/pre-sdd-review/test_contract.py:41-46` (INSTRUCTION_DOCUMENT_SHA256), `:1063`, `:1317-1319`, `:1344-1355`

**Interfaces:**
- Produces: SKILL.md에 아래 정확한 문장들. Task 3의 contract.md·README와 Task 4의 cases.json이 이 문장을 참조한다.

- [ ] **Step 1: 실패하는 단언 작성**

`test_contract.py:1063`의 `self.assertIn("summary --last 20", skill)`을 다음 세 줄로 바꾼다:

```python
        self.assertIn("summary --repo <repo display name>", skill)
        self.assertIn("Never reuse a handoff whose `execution` is `blocked`", skill)
        self.assertNotIn("summary --last 20", skill)
```

`:1317`의 `self.assertIn("After `finish`, read `summary --last 20`", normalized_handoff)`을 다음으로 바꾼다:

```python
        self.assertIn("Print the `anomalies` list that `finish` returned", normalized_handoff)
        self.assertIn("`Anomalies: not_recorded`", normalized_handoff)
        self.assertNotIn("summary --last", normalized_handoff)
```

`:1318`의 `self.assertIn("observation anomalies", normalized_handoff)`은 삭제한다. `:1319`의 `Anomalies do not change the verdict`는 유지한다.

`test_red_flags_close_observed_controller_and_reviewer_failures`의 phrase 튜플에서

```python
            "Start a new review when current hashes still match a REVISE or BLOCKED `sha_end`",
```

을

```python
            "Start a new review when documents, `HEAD`, and the request are all unchanged since a `full` or `degraded` REVISE or BLOCKED run",
            "Reuse a handoff from an `execution=blocked` run, or reuse any handoff on document hashes alone",
```

으로, 

```python
            "Print `READY` without this run's observation anomalies",
```

을

```python
            "Print `READY` without the `Anomalies:` line from `finish`",
```

으로 바꾼다. 같은 테스트의 `normalized_flags` 검사 뒤에 추가:

```python
        select = section(skill, "## Select reviewers", "## Default mode")
        normalized_select = re.sub(r"\s+", " ", select)
        self.assertIn(
            "ask that reviewer once for the complete records, naming only the missing fields",
            normalized_select,
        )
        self.assertIn(
            "Do not name suspected findings, paths, symbols, or fixes in that request",
            normalized_select,
        )
```

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"`
Expected: 최소 세 테스트 FAIL (문구 부재).

- [ ] **Step 3: SKILL.md Optional local evidence 절 수정**

`:79-82`의

```text
run `summary --last 20` before `start`. If the latest completed verdict for
that plan is `REVISE` or `BLOCKED`, `show` that run and compare `plan.sha_end`
and `design.sha_end` with the current documents; if they match, reuse the
prior handoff and do not start a new review. Otherwise call `start` before semantic review with the skill root, the repository,
```

을

```text
run `summary --repo <repo display name>` before `start` and locate this plan
in `runs` and `chains`. Close any `pending` run for this plan first. If the
latest completed verdict for that plan is `REVISE` or `BLOCKED`, `show` that
run. Never reuse a handoff whose `execution` is `blocked`: that run dispatched
no reviewer, so re-run the input gates (`**Spec:**` resolution and the required
implementation base) and call `start` if they pass. For a `full` or `degraded`
run, reuse the prior handoff without a new review only when `plan.sha_end` and
`design.sha_end` match the current documents, `git.head_end` matches the
current `HEAD`, and the outer request does not ask for a re-review or name
changed authority or repository evidence. Otherwise call `start` before
semantic review with the skill root, the repository,
```

으로 바꾼다. 뒤따르는 "the primary plan, the design path resolved from …" 문장은 그대로 이어진다.

- [ ] **Step 4: Select reviewers 절에 재질의 지침 추가**

`:120-121`의

```text
The controller deduplicates all findings by evidence and consequence before
repair. Reviewers never edit files.
```

바로 뒤에 빈 줄 하나와 다음 단락을 넣는다:

```text
If a reviewer returns a summary, or a record missing any PSDR field, ask that
reviewer once for the complete records, naming only the missing fields. Do not
name suspected findings, paths, symbols, or fixes in that request. Never
accept a summary as findings.
```

- [ ] **Step 5: Verdict and handoff 보고 문구 수정**

`:230-234`의

```text
For `READY`, print the exact resolved design and plan paths and their final
fingerprints, together with the freshness record. After `finish`, read
`summary --last 20` and print this run's observation anomalies. Anomalies
do not change the verdict. Do not start SDD unless the outer request explicitly asks for implementation. In that combined request,
hand the SDD worker the final repaired documents, not the pre-review copies.
```

을

```text
For `READY`, print the exact resolved design and plan paths and their final
fingerprints, together with the freshness record. Print the `anomalies` list
that `finish` returned for this run as `Anomalies: <names>`, or
`Anomalies: none` when it is empty. When the recorder was not used or
`finish` failed, print `Anomalies: not_recorded`. Do not look this run up in
a windowed `summary`. Anomalies do not change the verdict. Do not start SDD
unless the outer request explicitly asks for implementation. In that combined
request, hand the SDD worker the final repaired documents, not the pre-review
copies.
```

으로 바꾼다.

- [ ] **Step 6: Red flags 수정**

`:245`

```text
- Start a new review when current hashes still match a REVISE or BLOCKED `sha_end`
```

을 두 줄로:

```text
- Start a new review when documents, `HEAD`, and the request are all unchanged since a `full` or `degraded` REVISE or BLOCKED run
- Reuse a handoff from an `execution=blocked` run, or reuse any handoff on document hashes alone
```

`:248`

```text
- Print `READY` without this run's observation anomalies
```

을

```text
- Print `READY` without the `Anomalies:` line from `finish`
```

으로 바꾼다.

- [ ] **Step 7: SKILL.md SHA 갱신 후 통과 확인**

공통 도구 스크립트를 실행해 `INSTRUCTION SKILL.md` 값을 `test_contract.py:41`의 `"SKILL.md":` 값에 붙인다. `references/reviewer-protocol.md` 값은 Task 5에서 바뀌므로 여기서는 그대로 둔다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"`
Expected: `Ran 56 tests` … `OK`. contract.md와 그 단언(`:1071`)은 Task 3에서 바꾸므로 여기서는 건드리지 않는다. FAIL이 있으면 Step 3–6의 문구를 단언과 글자 단위로 대조한다.

- [ ] **Step 8: 커밋**

```bash
git add skills/pre-sdd-review/SKILL.md tests/products/pre-sdd-review/test_contract.py
git commit -m "fix(pre-sdd-review): branch handoff reuse on execution and print finish anomalies"
```

---

### Task 3: contract.md·README 두 벌을 SKILL.md에 맞춤

**Files:**
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md:159-164`, `:166-167`, `:171-172`, `:182-185`
- Modify: `skills/pre-sdd-review/README.md:86-87`, `skills/pre-sdd-review/README.en.md:93-94`
- Test: `tests/products/pre-sdd-review/test_contract.py:385-392` (digest 상수), `:1071`, `:1373-1383`

**Interfaces:**
- Consumes: Task 2의 SKILL.md 문장.
- Produces: contract.md·README의 대응 문장. `test_red_flags_close_observed_controller_and_reviewer_failures`가 확인한다.

- [ ] **Step 1: 실패하는 단언 작성**

`test_contract.py:1071`의 `self.assertIn("summary --last 20", contract)`을

```python
        self.assertIn("summary --repo", contract)
        self.assertIn("`execution`이 `blocked`", re.sub(r"\s+", " ", contract))
        self.assertNotIn("summary --last 20", contract)
```

으로 바꾼다. `test_red_flags_close_observed_controller_and_reviewer_failures`의 contract 단언 세 줄 뒤에 추가:

```python
        self.assertIn("`finish`가 돌려준 관찰 이상(`anomalies`)", normalized_contract)
        self.assertIn("빠진 필드 이름만", normalized_contract)
        self.assertIn("`Anomalies:`", korean)
        self.assertIn("`Anomalies:` line", re.sub(r"\s+", " ", english))
```

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"`
Expected: 두 테스트 FAIL.

- [ ] **Step 3: contract.md 최종 보고 단락 수정**

`:159-164`의

```text
최종 보고는 입력·최종 문서 해시, 패스 번호, 발견 ID/분류, 영향 범위 트리거,
바뀐 문서 해시, 판정을 담은 짧은 패스 영수증을 포함합니다. `finish` 뒤에는
`summary --last 20`에서 이 run의 관찰 이상 이름을 그대로 적습니다. 이상이
판정을 바꾸지는 않습니다. `REVISE`와
`BLOCKED`는 미해결 발견과 다음 범위를 담은 인계 묶음을 반환합니다. 새 권위가
필요하면 판정은 `BLOCKED`입니다.
```

을

```text
최종 보고는 입력·최종 문서 해시, 패스 번호, 발견 ID/분류, 영향 범위 트리거,
바뀐 문서 해시, 판정을 담은 짧은 패스 영수증을 포함합니다. `finish`가 돌려준
관찰 이상(`anomalies`)을 `Anomalies:` 줄로 그대로 적습니다. 비어 있으면 `none`, 기록기를
쓰지 않았거나 `finish`가 실패했으면 `not_recorded`입니다. 이 run을 윈도우가
있는 `summary`에서 찾지 않습니다. 이상이 판정을 바꾸지는 않습니다. `REVISE`와
`BLOCKED`는 미해결 발견과 다음 범위를 담은 인계 묶음을 반환합니다. 새 권위가
필요하면 판정은 `BLOCKED`입니다.
```

으로 바꾼다.

- [ ] **Step 4: contract.md 재질의 단락 수정**

`:166-167`의

```text
검토자가 완전한 PSDR 기록 없이 요약만 내면 빠진 필드만 다시 받습니다.
의심되는 발견·경로·심볼·수정을 답을 넣어 재질의하지 않습니다.
```

을

```text
검토자가 완전한 PSDR 기록 없이 요약만 내면 그 검토자에게 한 번, 빠진 필드
이름만 들어 완전한 기록을 다시 받습니다. 의심되는 발견·경로·심볼·수정을
답을 넣어 재질의하지 않습니다. 요약을 발견으로 받지 않습니다.
```

으로 바꾼다.

- [ ] **Step 5: contract.md 재호출 단락과 기록기 계약 수정**

`:171-172`의

```text
`BLOCKED` 뒤에 자동으로 다시 호출하지 않습니다. 문서, 권위,
저장소 증거가 바뀌지 않았다면 이전 인계를 재사용합니다.
```

을

```text
`BLOCKED` 뒤에 자동으로 다시 호출하지 않습니다. 문서, `HEAD`, 요청이 모두
바뀌지 않은 `full`·`degraded` run의 인계만 재사용합니다. `execution`이
`blocked`인 run의 인계는 재사용하지 않습니다.
```

으로 바꾼다. `:182-185`의

```text
LF 하나입니다. 호환되면 `start` 전에 `summary --last 20`을 실행합니다. 같은
`repo` 표시 이름과 계획 경로가 `pending`이면 그 run을 `abandon`합니다. 그
계획의 마지막 완료 판정이 `REVISE` 또는 `BLOCKED`이고 문서 해시가 같으면
이전 인계를 재사용합니다. 아니면 의미 검토 전에 `start`하고, 판정과
```

을

```text
LF 하나입니다. 호환되면 `start` 전에 `summary --repo <표시 이름>`을 실행해
`runs`와 `chains`에서 그 계획을 찾습니다. 같은 `repo` 표시 이름과 계획 경로가
`pending`이면 그 run을 `abandon`합니다. 그 계획의 마지막 완료 판정이 `REVISE`
또는 `BLOCKED`이면 `show`합니다. `execution`이 `blocked`이면 인계를 재사용하지
않고 입력 게이트를 다시 확인한 뒤 `start`합니다. `full`·`degraded`이면 문서
해시, `git.head_end`, 요청이 모두 같을 때만 이전 인계를 재사용합니다. 아니면
의미 검토 전에 `start`하고, 판정과
```

으로 바꾼다.

- [ ] **Step 6: README 두 벌 수정**

`skills/pre-sdd-review/README.md:86-87`의

```text
`READY` 보고에는 이 검토의 관찰 이상 이름을 적습니다. 이상이 판정을
바꾸지는 않습니다.
```

을

```text
`READY` 보고에는 `finish`가 돌려준 관찰 이상을 `Anomalies:` 줄로 적습니다.
이상이 판정을 바꾸지는 않습니다.
```

으로, `skills/pre-sdd-review/README.en.md:93-94`의

```text
A `READY` report lists this run's observation anomalies. Anomalies do not
change the verdict.
```

을

```text
A `READY` report prints the observation anomalies that `finish` returned as
an `Anomalies:` line. Anomalies do not change the verdict.
```

으로 바꾼다.

- [ ] **Step 7: maintainer digest 갱신 후 통과 확인**

공통 도구 스크립트를 실행해 `MAINTAINER_CANONICAL_DIGEST`와 `### Freshness` subsection digest를 `test_contract.py:385-391`에 붙인다. 다른 subsection digest가 바뀌었다면 편집이 다른 절로 번졌다는 뜻이므로 Step 3–5의 위치를 다시 확인한다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | tail -3`
Expected: `Ran 56 tests` … `OK`

- [ ] **Step 8: 커밋**

```bash
git add docs/maintainers/products/pre-sdd-review/contract.md skills/pre-sdd-review/README.md skills/pre-sdd-review/README.en.md tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): mirror finish anomalies and execution-based reuse in the contract"
```

---

### Task 4: cases.json 사례 추가와 testing.md 라이브 프로브 절차

**Files:**
- Modify: `tests/products/pre-sdd-review/cases.json:128-132` 뒤
- Modify: `docs/maintainers/products/pre-sdd-review/testing.md:44-45`, `:82-83`, `:100-118`
- Test: `tests/products/pre-sdd-review/test_contract.py:49-77` (CASE_IDS), `:392` (TESTING digest), `:1198-1205`, `:1572-1573`

**Interfaces:**
- Produces: 사례 id `blocked-execution-restarts`, expect `["no_reuse_blocked_execution", "rerun_input_gates", "start"]`.

- [ ] **Step 1: 실패하는 단언 작성**

`test_contract.py`의 `CASE_IDS` 튜플에서 `"red-flag-anomalous-ready",` 다음 줄에 `"blocked-execution-restarts",`를 넣는다. `:1205`(`cases["red-flag-anomalous-ready"]` 단언) 뒤에 추가:

```python
        self.assertEqual(
            cases["blocked-execution-restarts"],
            ("no_reuse_blocked_execution", "rerun_input_gates", "start"),
        )
```

`:1572-1573`을

```python
        self.assertEqual(len(CASE_IDS), 31)
        self.assertIn("정확히 서른한 개", normalized_testing)
```

으로 바꾼다. `test_testing_document_...`가 확인하는 normalized_testing 사실 튜플(`"not_measured"` 앞)에 `"PRE_SDD_REVIEW_HOME"`을 추가한다.

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"`
Expected: 사례 수·인벤토리·문구 단언 FAIL.

- [ ] **Step 3: cases.json에 사례 추가**

`red-flag-anomalous-ready` 항목 뒤, `near-miss-write-spec` 앞에 넣는다:

```json
    {
      "id": "blocked-execution-restarts",
      "request": "$pre-sdd-review review-only sample-app/design.md sample-app/plan.md after a BLOCKED run with execution=blocked whose required base now resolves and whose document hashes are unchanged",
      "expect": ["no_reuse_blocked_execution", "rerun_input_gates", "start"]
    },
```

- [ ] **Step 4: testing.md 사례 수와 인벤토리 수정**

`:44-45`의 `정확히 서른 개`를 `정확히 서른한 개`로 바꾼다. Case inventory에서 `- \`red-flag-anomalous-ready\`` 다음 줄에 `- \`blocked-execution-restarts\``를 넣는다.

- [ ] **Step 5: testing.md 라이브 프로브 절차 추가**

"선택적 라이브 검사" 절의 v1.1 전진 확인 단락 뒤, Evidence 테스트 단락 앞에 넣는다:

```text
컨트롤러 경계 프로브는 실제 모델에 정해진 중간 상태를 주입해 SKILL.md의
분기 하나를 확인합니다. 합성 Git 저장소와 비어 있는 evidence home을 만들고,
모든 `evidence.py` 호출에 `PRE_SDD_REVIEW_HOME`을 그 home으로 고정합니다.
기본 home `~/.pre-sdd-review/`에 프로브 기록을 남기지 않습니다. 컨트롤러에는
SKILL.md와 스킬 루트만 주고 정답이나 기대 결과는 주지 않습니다. 결과는
컨트롤러가 쓴 결정 파일이나 보고 파일로 채점합니다.

- 변경된 저장소 근거 재검토: 계획에 required base를 적고, 그 ref가 없는
  상태로 `execution=blocked`, `reviewers=0`인 `BLOCKED` 기록을 만든 뒤 ref를
  `HEAD`에 만듭니다. 문서 해시는 그대로입니다. 컨트롤러가 `start`에 이르면
  통과입니다. 이전 인계를 재사용하면 실패입니다.
- 불완전 기록 재질의: 리뷰어가 요약과 판정만 돌려준 상황을 주고 다음
  메시지를 파일로 받습니다. 빠진 필드만 요청하고 발견·경로·심볼·수정을
  넣지 않으면 통과입니다.
- 이상 있는 READY 보고: `reviewers=2`, trigger 없음으로 `finish`한 기록을
  주고 최종 보고를 받습니다. `Anomalies:` 줄에
  `full_reviewer_count_mismatch`가 있고 `READY`가 유지되면 통과입니다.
- 윈도우 밖 run 보고: 위와 같되 그 run이 시작된 뒤 다른 저장소의 run 스무
  개를 시작하고 끝낸 다음 그 run을 `finish`합니다. `Anomalies:` 줄이 그
  run의 이상을 보이면 통과입니다. `finish` 출력이 아닌 `summary --last`에서
  찾으려 하면 누락됩니다.

이 프로브는 선택이며 CI가 요구하지 않습니다. 사례당 한 번의 결과는 모델
품질 측정이 아닙니다.
```

- [ ] **Step 6: TESTING digest 갱신 후 통과 확인**

공통 도구 스크립트로 `TESTING_CANONICAL_DIGEST`를 `test_contract.py:392`에 붙인다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | tail -3`
Expected: `Ran 56 tests` … `OK`

- [ ] **Step 7: 커밋**

```bash
git add tests/products/pre-sdd-review/cases.json docs/maintainers/products/pre-sdd-review/testing.md tests/products/pre-sdd-review/test_contract.py
git commit -m "test(pre-sdd-review): add blocked-execution restart case and controller probe procedure"
```

---

### Task 5: 심각도 정의와 픽스처 조정

**Files:**
- Modify: `skills/pre-sdd-review/references/reviewer-protocol.md:17-22`
- Modify: `tests/products/pre-sdd-review/fixtures/missing-coverage/expected.json:7`
- Modify: `tests/products/pre-sdd-review/fixtures/ready/design.md:6`
- Test: `tests/products/pre-sdd-review/test_contract.py:43-45` (protocol SHA), `:101-107` 및 `:162-172` (FIXTURE_CONTENTS), 새 단언

**Interfaces:**
- Produces: reviewer-protocol.md의 새 두 정의. contract.md의 Severities 목록(`BLOCKER`, `IMPORTANT`)은 변하지 않는다.

- [ ] **Step 1: 실패하는 단언 작성**

`test_contract.py`의 `test_red_flags_close_observed_controller_and_reviewer_failures` 안 `normalized_protocol` 단언 뒤에 추가:

```python
        self.assertIn(
            "`BLOCKER`: the minimal document fix needs authority, input, or repository evidence outside the two reviewed documents, or a new product decision. Left unresolved, it forces `BLOCKED`.",
            normalized_protocol,
        )
        self.assertIn(
            "`IMPORTANT`: the minimal document fix is an authority-preserving edit within the two reviewed documents. Left unresolved, it forces `REVISE`.",
            normalized_protocol,
        )
        self.assertNotIn("materially invalid or missing", normalized_protocol)
```

`FIXTURE_CONTENTS["ready"]["design.md"]` 문자열의

```text
- The function returns the rendered string for the supplied input.
```

을

```text
- The function returns the supplied input unchanged.
```

으로, `FIXTURE_CONTENTS["missing-coverage"]["expected.json"]` 문자열의 `\"severity\": \"BLOCKER\",`를 `\"severity\": \"IMPORTANT\",`로 바꾼다.

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"`
Expected: 프로토콜 문구 단언과 fixture 원문 비교 FAIL.

- [ ] **Step 3: reviewer-protocol.md 심각도 정의 교체**

`:17-22`의

```text
Use only these severities:

- `BLOCKER`: SDD cannot safely start because authority, feasibility, ordering,
  or acceptance evidence is materially invalid or missing.
- `IMPORTANT`: SDD could start, but the documents permit a credible wrong
  implementation, avoidable rework, or an unverifiable acceptance claim.
```

을

```text
Use only these severities:

- `BLOCKER`: the minimal document fix needs authority, input, or repository
  evidence outside the two reviewed documents, or a new product decision.
  Left unresolved, it forces `BLOCKED`.
- `IMPORTANT`: the minimal document fix is an authority-preserving edit within
  the two reviewed documents. Left unresolved, it forces `REVISE`.

Severity follows the minimal document fix, not the size of the defect.
```

으로 바꾼다. 첫 줄 `Use only these severities:`는 `test_protocol_allows_exactly_two_severities`가 `section()` 앵커로 쓰므로 글자 그대로 둔다.

- [ ] **Step 4: 픽스처 두 곳 수정**

`tests/products/pre-sdd-review/fixtures/missing-coverage/expected.json:7`의 `"severity": "BLOCKER",`를 `"severity": "IMPORTANT",`로 바꾼다.

`tests/products/pre-sdd-review/fixtures/ready/design.md:6`의 `- The function returns the rendered string for the supplied input.`을 `- The function returns the supplied input unchanged.`으로 바꾼다.

- [ ] **Step 5: 프로토콜 SHA 갱신 후 통과 확인**

공통 도구 스크립트로 `INSTRUCTION references/reviewer-protocol.md` 값을 `test_contract.py:43-45`에 붙인다. `V1_1_FIXTURE_SHA256`는 두 픽스처를 포함하지 않으므로 바뀌지 않아야 한다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/products/pre-sdd-review -p test_contract.py 2>&1 | tail -3`
Expected: `Ran 56 tests` … `OK`

- [ ] **Step 6: 커밋**

```bash
git add skills/pre-sdd-review/references/reviewer-protocol.md tests/products/pre-sdd-review/fixtures/missing-coverage/expected.json tests/products/pre-sdd-review/fixtures/ready/design.md tests/products/pre-sdd-review/test_contract.py
git commit -m "fix(pre-sdd-review): tie finding severity to repairability and unambiguous positive control"
```

---

### Task 6: 버전 3.0.4, CHANGELOG, 전체 검증

**Files:**
- Modify: `skills/pre-sdd-review/release.toml:3`, `skills/pre-sdd-review/SKILL.md:7-8`, `skills/pre-sdd-review/CHANGELOG.md:5-6`
- Test: `tests/products/pre-sdd-review/test_contract.py:26`, `:958`; `tests/repository/test_release_contract.py:28`, `:56-58`

**Interfaces:**
- Consumes: Task 1–5의 모든 변경.

- [ ] **Step 1: 실패하는 단언 작성**

`test_contract.py:26`을 `TARGET_VERSION = "3.0.4"`로, `:958`의 `2026-09-16`을 `2026-09-17`로 바꾼다. `tests/repository/test_release_contract.py:28`의 `"pre-sdd-review": "3.0.3",`을 `"3.0.4"`로, `:56-58`의 `3.0.3` 세 곳을 `3.0.4`로 바꾼다.

- [ ] **Step 2: 실패 확인**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests/repository -p test_release_contract.py 2>&1 | tail -3`
Expected: `FAILED` (버전 불일치).

- [ ] **Step 3: 버전과 CHANGELOG 갱신**

`release.toml:3`을 `version = "3.0.4"`로, `SKILL.md:7-8`을

```yaml
  version: "3.0.4"
  updated_at: "2026-09-17"
```

로 바꾼다. `CHANGELOG.md`의 `## Unreleased` 다음 빈 줄 뒤에 넣는다:

```markdown
## 3.0.4 - 2026-09-17

### Fixed

- `finish` returns this run's observation anomalies; controllers print that list as an `Anomalies:` line instead of searching a windowed `summary`.
- A handoff from an `execution=blocked` run is never reused; `full` and `degraded` handoffs are reused only when documents, `HEAD`, and the request are unchanged.
- Controllers re-ask an incomplete reviewer once for the missing fields only.
- Finding severity follows the minimal document fix: `BLOCKER` needs outside authority or evidence, `IMPORTANT` is repairable within the two documents.

### Changed

- The `missing-coverage` fixture expects `IMPORTANT`; the `ready` fixture design states the function returns its input unchanged.

### Notes

- Record schema and the `--version` handshake are unchanged. No GitHub tag or GitHub Release is created.

```

- [ ] **Step 4: SKILL.md SHA 재갱신**

frontmatter가 바뀌었으므로 공통 도구 스크립트로 `INSTRUCTION SKILL.md` 값을 다시 받아 `test_contract.py:41`에 붙인다.

- [ ] **Step 5: 전체 검증**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --profile full 2>&1 | tail -5`
Expected: 마지막 unittest 단계 `OK`, python-compile 단계 종료 코드 0. 테스트 수는 이전 281에서 evidence 1건 증가.

Run: `python3 scripts/release.py check --product pre-sdd-review 2>&1 | tail -3`
Expected: 오류 없이 종료. 작업 트리가 깨끗해야 하므로 Step 6 커밋 뒤에 다시 실행해도 된다.

- [ ] **Step 6: 스크래치 저장소에서 완료 기준 확인**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests/products/pre-sdd-review/evidence")
from support import make_git_repo, start, finish, finish_payload, finding, load
SKILL = Path("skills/pre-sdd-review").resolve()
with tempfile.TemporaryDirectory() as d:
    ws = Path(d); home = ws / "home"; repo = make_git_repo(ws)
    blocked = start(home, repo, SKILL, mode="review-only")
    code, out, err = finish(home, repo, blocked, finish_payload(
        execution="blocked", reviewers=0, verdict="BLOCKED", block_reason="required-base-unresolvable",
        findings=[finding(status="unresolved", repair_pass=None)]))
    assert code == 0, err
    record = load(home, blocked)
    print("execution", record["execution"], "-> controller must start, not reuse")
    print("finish anomalies", json.loads(out)["anomalies"])
PY
grep -rn "summary --last 20" skills/pre-sdd-review docs/maintainers/products/pre-sdd-review && echo "STALE PHRASE FOUND" || echo "no stale phrase"
```

Expected: `execution blocked -> controller must start, not reuse`, `finish anomalies [...]` 출력, `no stale phrase`.

- [ ] **Step 7: 커밋**

```bash
git add skills/pre-sdd-review/release.toml skills/pre-sdd-review/SKILL.md skills/pre-sdd-review/CHANGELOG.md tests/products/pre-sdd-review/test_contract.py tests/repository/test_release_contract.py
git commit -m "chore(pre-sdd-review): release 3.0.4"
```

---

## 자체 점검

- 스펙 R1 → Task 1. R2 → Task 2 Step 3·6, Task 3 Step 5, Task 1 Step 7. R3 → Task 2 Step 4·5·6, Task 3 Step 3·4·6. R4 → Task 5. 스펙 8절 테스트·문서 → Task 1·4·6. 스펙 10절 완료 기준 → Task 6 Step 5·6.
- 함수 이름 `finding_anomalies`, `run_anomalies`와 출력 키 `anomalies`는 Task 1 테스트·구현·README에서 동일하다.
- 사례 id `blocked-execution-restarts`와 expect 세 값은 cases.json, CASE_IDS, 단언, testing.md 인벤토리에서 동일하다.
- digest 상수는 Task 2(SKILL), 3(MAINTAINER·Freshness), 4(TESTING), 5(protocol), 6(SKILL 재갱신) 순으로 갱신한다. Task 6 Step 4를 빠뜨리면 frontmatter 변경으로 contract 테스트가 실패한다.
