# pre-sdd-review 4.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 판정을 내지 않는 선행 원장 패스를 계획별 게이트 앞에 두고, 기록기를 schema 4 로 올려 baseline·원장·수리 회계·degraded 관찰을 기록하게 해 pre-sdd-review `4.0.0` 을 만든다.

**Architecture:** 기록기(`evidence.py`)에 record 필드 둘(`baseline`, `ledger`), git 사실 하나, finding 필드 하나(`source`)를 더하고 `repair_pass` 하한을 0 으로 내리며 `degraded_reasons` 를 열거로 조인다. 관찰 이상 둘과 집계 하나를 더한다. 그다음 `SKILL.md` 와 `references/reviewer-protocol.md` 에 선행 패스·원장·baseline·기계 점검·지시 계약을 넣고, `contract.md` 가 그 계약을 소유하게 한다. 문서를 고칠 때마다 계약 테스트의 고정 digest 가 깨지므로 같은 Task 안에서 재계산한다.

**Tech Stack:** Python 3.11+ 표준 라이브러리, `unittest`, Git. 새 의존성 없음. 새 실행 파일 없음.

**Spec:** [docs/history/specs/2026-09-18-pre-sdd-review-4.0.0-design.md](../specs/2026-09-18-pre-sdd-review-4.0.0-design.md)

## Global Constraints

- 수정 대상은 `skills/pre-sdd-review/`, `tests/products/pre-sdd-review/`, `docs/maintainers/products/pre-sdd-review/`, `tests/repository/test_release_contract.py` 만이다.
- 제품 버전은 `4.0.0`, 날짜는 `2026-09-18` 이다. 태그와 GitHub Release 는 만들지 않는다.
- `--version` 정규 줄은 `{"cli_version":"4.0.0","schema":4,"skill_name":"pre-sdd-review"}` 뒤에 LF 하나다.
- Python 3.11 이상, 표준 라이브러리만 쓴다. 새 런타임 의존성과 새 실행 파일은 없다.
- 호스트 지원을 넓히지 않는다. `products.toml`, `docs/maintainers/products/pre-sdd-review/compatibility.md`, `docs/users/` 는 바꾸지 않는다.
- 권위 순서는 다섯 항목을 유지한다. 원장은 유도된 증거이며 권위가 아니다.
- 판정 어휘(`READY`/`REVISE`/`BLOCKED`), 리뷰 역할 상한 둘, 수정 패스 상한 둘은 바꾸지 않는다.
- 사용자 문서 원문, 모델 응답 원문, 자격 증명은 픽스처·테스트·기록에 넣지 않는다.
- 모든 테스트 명령은 `PYTHONDONTWRITEBYTECODE=1` 을 붙여 저장소 루트에서 실행한다.
- 커밋 메시지는 기존 규칙(`feat(pre-sdd-review): ...`, `fix(...)`, `docs(...)`, `test(...)`)을 따른다.

## 공통 도구: digest 재계산

Task 5 부터 9 까지는 문서를 바꾸므로 `tests/products/pre-sdd-review/test_contract.py` 의 고정 digest 상수가 깨진다. 각 Task 안에서 문구 단언을 먼저 고치고, 남은 실패가 digest 오류뿐일 때 아래를 실행해 새 값을 상수에 붙인다.

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
print("RELEASE_CANONICAL_DIGEST", m.whole_document_digest((m.MAINTAINERS / "release.md").read_text(encoding="utf-8")))
for name in ("SKILL.md", "references/reviewer-protocol.md"):
    print("INSTRUCTION", name, hashlib.sha256((m.SKILL / name).read_bytes()).hexdigest())
PY
```

## 전체 검증

각 Task 는 자기 테스트를 돌린다. 머지 전에 한 번:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py
```

---

### Task 1: 버전을 4.0.0 으로 올린다

버전 식별자를 먼저 한 번에 올려, 이후 문서 Task 들이 digest 를 한 번씩만 재계산하게 한다.

**Files:**
- Modify: `skills/pre-sdd-review/release.toml`
- Modify: `skills/pre-sdd-review/SKILL.md` (frontmatter `version`, `updated_at`)
- Modify: `skills/pre-sdd-review/CHANGELOG.md`
- Modify: `tests/products/pre-sdd-review/test_contract.py` (`TARGET_VERSION`, `INSTRUCTION_DOCUMENT_SHA256`, CHANGELOG 날짜 단언)
- Modify: `tests/repository/test_release_contract.py:28,57,58`

**Interfaces:**
- Produces: 제품 버전 문자열 `4.0.0`, 날짜 `2026-09-18`, 태그 `pre-sdd-review-v4.0.0`.
- Consumes: 없음.

- [ ] **Step 1: 테스트 상수를 먼저 4.0.0 으로 바꿔 실패시킨다**

`tests/products/pre-sdd-review/test_contract.py:26`:

```python
TARGET_VERSION = "4.0.0"
```

같은 파일 `:959` 의 CHANGELOG 단언:

```python
        self.assertIn(f"## {TARGET_VERSION} - 2026-09-18", changelog)
```

`tests/repository/test_release_contract.py:28`:

```python
    "pre-sdd-review": "4.0.0",
```

같은 파일 `:57-58`:

```python
        self.assertEqual(product.tag, "pre-sdd-review-v4.0.0")
        self.assertEqual(product.artifact_name, "pre-sdd-review-v4.0.0.zip")
```

- [ ] **Step 2: 실패를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.test_contract tests.repository.test_release_contract -v 2>&1 | tail -20`
Expected: FAIL. 버전 불일치와 CHANGELOG 절 없음.

- [ ] **Step 3: 제품 파일의 버전을 올린다**

`skills/pre-sdd-review/release.toml`:

```toml
version = "4.0.0"
```

`skills/pre-sdd-review/SKILL.md` frontmatter:

```yaml
metadata:
  version: "4.0.0"
  updated_at: "2026-09-18"
```

`skills/pre-sdd-review/CHANGELOG.md` 의 `## Unreleased` 바로 아래에 절을 만든다. 내용은 Task 11 에서 채운다.

```markdown
## Unreleased

## 4.0.0 - 2026-09-18

### Added

- 판정을 내지 않는 선행 원장 패스.

### Notes

- Record schema 와 `--version` handshake 가 `4` 로 바뀐다. GitHub 태그와 Release 는 만들지 않는다.
```

- [ ] **Step 4: digest 를 재계산해 붙인다**

공통 도구 스크립트를 실행하고 `INSTRUCTION_DOCUMENT_SHA256["SKILL.md"]` 를 새 값으로 바꾼다. frontmatter 만 바뀌었으므로 `reviewer-protocol.md` 값은 그대로다.

- [ ] **Step 5: 테스트가 통과하는지 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.test_contract tests.repository.test_release_contract 2>&1 | tail -5`
Expected: OK

- [ ] **Step 6: 커밋**

```bash
git add skills/pre-sdd-review/release.toml skills/pre-sdd-review/SKILL.md skills/pre-sdd-review/CHANGELOG.md tests/products/pre-sdd-review/test_contract.py tests/repository/test_release_contract.py
git commit -m "chore(pre-sdd-review): bump the product version to 4.0.0"
```

---

### Task 2: record schema 4 — `baseline`, `ledger`, git 조상 사실

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py:23-24` (`CLI_VERSION`, `SCHEMA`), `:57-64` (record 키), `:337-341` (`require_current_schema` 의 하드코딩된 3), `:361-367` (`git_state` 뒤 헬퍼), `:590-640` (`validate_record`), `:672-716` (`cmd_start`), `:723-758` (`cmd_finish`), `:965-975` (`start` 인자)
- Modify: `tests/products/pre-sdd-review/evidence/support.py` (`start` 헬퍼)
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`

**Interfaces:**
- Produces: record 키 `baseline` (`{"head": str, "prior_plans": list[str]}`) 와 `ledger` (`{"path": str, "sha": str}` 또는 `None`); `git.head_start_is_ancestor_of_head_end` (`bool` 또는 `None`); `start --ledger PATH` 와 반복 가능한 `start --prior-plan PATH`; 모듈 상수 `RECORD_KEYS_V4`.
- Consumes: 기존 `repository_relative(root, argument, cwd)`, `document_hash(root, relative)`, `git(root, *args)`, `git_state(root)`.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/products/pre-sdd-review/evidence/test_evidence.py` 의 `StartTests` 끝에 추가:

```python
    def test_start_records_baseline_and_ledger(self) -> None:
        write(self.repo / "docs/ledger.md", "| path | plans |\n")
        run_id = start(
            self.home,
            self.repo,
            self.skill,
            ledger="docs/ledger.md",
            prior_plans=["docs/plan-a.md", "docs/plan-b.md"],
        )
        record = load(self.home, run_id)
        self.assertEqual(record["schema"], 4)
        self.assertEqual(
            record["baseline"],
            {"head": record["git"]["head_start"], "prior_plans": ["docs/plan-a.md", "docs/plan-b.md"]},
        )
        self.assertEqual(record["ledger"]["path"], "docs/ledger.md")
        self.assertEqual(len(record["ledger"]["sha"]), 64)
        self.assertIsNone(record["git"]["head_start_is_ancestor_of_head_end"])

    def test_start_without_ledger_or_prior_plans_uses_empty_defaults(self) -> None:
        record = load(self.home, start(self.home, self.repo, self.skill))
        self.assertIsNone(record["ledger"])
        self.assertEqual(record["baseline"]["prior_plans"], [])
```

`FinishTests` 끝에 추가:

```python
    def test_finish_records_whether_head_start_is_an_ancestor(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        write(self.repo / "src/app.ts", "export const app = 2;\n")
        commit_all(self.repo, "forward")
        code, _, err = finish(self.home, self.repo, run_id, finish_payload())
        self.assertEqual((code, err), (0, ""))
        self.assertIs(load(self.home, run_id)["git"]["head_start_is_ancestor_of_head_end"], True)

    def test_finish_flags_a_head_that_is_not_a_descendant(self) -> None:
        run_git(self.repo, "checkout", "--quiet", "-b", "side")
        write(self.repo / "src/app.ts", "export const app = 3;\n")
        commit_all(self.repo, "side")
        run_id = start(self.home, self.repo, self.skill)
        run_git(self.repo, "checkout", "--quiet", "-")
        code, _, err = finish(self.home, self.repo, run_id, finish_payload())
        self.assertEqual((code, err), (0, ""))
        self.assertIs(load(self.home, run_id)["git"]["head_start_is_ancestor_of_head_end"], False)
```

파일 위쪽 import 에 `commit_all`, `run_git`, `write` 가 없으면 `from .support import ...` 에 더한다.

`tests/products/pre-sdd-review/evidence/support.py` 의 `start` 를 고친다:

```python
def start(
    home: Path,
    repo: Path,
    skill_root: Path,
    *,
    design: bool = True,
    client: str = "codex",
    model: str = "gpt-test",
    mode: str = "default",
    ledger: str | None = None,
    prior_plans: list[str] | None = None,
) -> str:
    argv = [
        "start",
        "--skill-root", str(skill_root),
        "--repo", str(repo),
        "--plan", str(repo / "docs/plan.md"),
        "--client", client,
        "--model", model,
        "--mode", mode,
    ]
    if design:
        argv += ["--design", str(repo / "docs/design.md")]
    if ledger is not None:
        argv += ["--ledger", str(repo / ledger)]
    for prior in prior_plans or []:
        argv += ["--prior-plan", prior]
    code, out, err = run(argv, home=home, cwd=repo)
    if code != 0:
        raise AssertionError(err)
    return json.loads(out)["run_id"]
```

- [ ] **Step 2: 실패를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.evidence.test_evidence -v 2>&1 | tail -20`
Expected: FAIL. `--ledger` 는 알 수 없는 인자이고 `record["schema"]` 는 3 이다.

- [ ] **Step 3: 상수와 record 키를 고친다**

`skills/pre-sdd-review/evidence/evidence.py:23-24`:

```python
CLI_VERSION = "4.0.0"
SCHEMA = 4
```

`require_current_schema` 는 지금 `record["schema"] != 3` 이면 실패한다. `SCHEMA` 를 4 로 올리면 새 record 가 곧바로 그 검사에 걸려 `finish` 가 죽는다. 상수로 바꾼다:

```python
def require_current_schema(record: dict[str, object]) -> None:
    if record["schema"] != SCHEMA:
        fail(
            "legacy-record-read-only",
            "schema 2 is historical-unbound; preserve it and start a new run",
        )
```

Task 4 가 이것을 `require_mutable_schema` 로 다시 쓰며 schema 3 의 `abandon` 예외를 더한다.

`RECORD_KEYS_V2` 정의 바로 뒤에 더한다:

```python
RECORD_KEYS_V3 = RECORD_KEYS_V2 | {"repo_key"}
RECORD_KEYS_V4 = RECORD_KEYS_V3 | {"baseline", "ledger"}
GIT_KEYS_V3 = {"head_start", "head_end", "dirty_start", "dirty_end"}
GIT_KEYS_V4 = GIT_KEYS_V3 | {"head_start_is_ancestor_of_head_end"}
MAX_PRIOR_PLANS = 40
```

- [ ] **Step 4: `validate_record` 가 schema 4 를 받게 한다**

`validate_record` 의 schema 분기를 바꾼다:

```python
    schema = record["schema"]
    if schema not in (2, 3, 4):
        fail("schema-invalid", "record must use schema 2, 3, or 4")
    keys = {2: RECORD_KEYS_V2, 3: RECORD_KEYS_V3, 4: RECORD_KEYS_V4}[schema]
    value = _object(record, "record", keys)
```

`if schema == 3:` 로 `repo_key` 를 검사하던 줄을 `if schema >= 3:` 으로 바꾼다.

git 사실 검사를 바꾼다:

```python
    git_facts = _object(value["git"], "git", GIT_KEYS_V4 if schema == 4 else GIT_KEYS_V3)
```

`for suffix in ("start", "end"):` 루프 뒤에 더한다:

```python
    if schema == 4:
        ancestry = git_facts["head_start_is_ancestor_of_head_end"]
        if status != "completed":
            if ancestry is not None:
                fail("schema-invalid", "unfinished review cannot have ancestry facts")
        elif ancestry is not None:
            _boolean(ancestry, "git.head_start_is_ancestor_of_head_end")
```

`outcome` 검사 바로 앞에 `baseline` 과 `ledger` 검사를 더한다:

```python
    if schema == 4:
        baseline = _object(value["baseline"], "baseline", {"head", "prior_plans"})
        if baseline["head"] != git_facts["head_start"]:
            fail("schema-invalid", "baseline.head must equal git.head_start")
        if not isinstance(baseline["prior_plans"], list):
            fail("schema-invalid", "baseline.prior_plans must be a list")
        if len(baseline["prior_plans"]) > MAX_PRIOR_PLANS:
            fail("schema-invalid", f"baseline.prior_plans exceeds {MAX_PRIOR_PLANS} entries")
        for prior in baseline["prior_plans"]:
            _relative(prior, "baseline.prior_plans[]")
        if value["ledger"] is not None:
            ledger = _object(value["ledger"], "ledger", {"path", "sha"})
            _relative(ledger["path"], "ledger.path")
            _digest(ledger["sha"], "ledger.sha")
```

- [ ] **Step 5: `cmd_start` 가 새 필드를 쓰게 한다**

`cmd_start` 안, `head, dirty = git_state(root)` 뒤에 더한다:

```python
    ledger_path = None if args.ledger is None else repository_relative(root, args.ledger, cwd)
    prior_plans: list[str] = []
    for prior in args.prior_plan or []:
        value = _relative(prior, "prior-plan")
        if value not in prior_plans:
            prior_plans.append(value)
    if len(prior_plans) > MAX_PRIOR_PLANS:
        fail("invalid-arguments", f"--prior-plan exceeds {MAX_PRIOR_PLANS} entries")
```

record 리터럴의 `"design"` 항목 뒤에 더한다:

```python
        "baseline": {"head": head, "prior_plans": prior_plans},
        "ledger": None if ledger_path is None else {
            "path": ledger_path,
            "sha": document_hash(root, ledger_path),
        },
```

같은 리터럴의 `"git"` 을 바꾼다:

```python
        "git": {
            "head_start": head,
            "head_end": None,
            "dirty_start": dirty,
            "dirty_end": None,
            "head_start_is_ancestor_of_head_end": None,
        },
```

`--prior-plan` 은 저장소 상대 경로를 그대로 받는다. `--ledger` 만 `repository_relative` 로 정규화한다. 원장은 실제 파일이라 해시를 계산해야 하고, 선행 계획은 이 checkout 에 아직 없을 수도 있기 때문이다.

- [ ] **Step 6: `cmd_finish` 가 조상 관계를 기록하게 한다**

`git_state` 정의 뒤에 헬퍼를 더한다:

```python
def head_ancestry(root: Path, head_start: str, head_end: str) -> bool | None:
    """True when head_start is an ancestor of head_end; None when the question is moot."""
    if head_start == head_end or "unborn" in (head_start, head_end):
        return None
    return git(root, "merge-base", "--is-ancestor", head_start, head_end).returncode == 0
```

`cmd_finish` 의 `git_facts["dirty_end"] = dirty` 뒤에 더한다:

```python
        git_facts["head_start_is_ancestor_of_head_end"] = head_ancestry(
            root, str(git_facts["head_start"]), head
        )
```

- [ ] **Step 7: `start` 인자를 더한다**

`build_parser` 의 `start.add_argument("--mode", ...)` 뒤:

```python
    start.add_argument("--ledger")
    start.add_argument("--prior-plan", action="append", default=[])
```

- [ ] **Step 8: 테스트가 통과하는지 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.evidence.test_evidence tests.products.pre-sdd-review.evidence.test_hardening 2>&1 | tail -10`
Expected: OK. `--version` handshake 를 단언하는 기존 테스트가 실패하면 `4.0.0`/`4` 로 함께 고친다.

- [ ] **Step 9: 커밋**

```bash
git add skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence/
git commit -m "feat(pre-sdd-review): record the plan-turn baseline, the ledger, and head ancestry in schema 4"
```

---

### Task 3: finding 계약 — `source`, `repair_pass` 0, `partially-closed`

수리 회계를 한 결함 단위로 옮긴다. `repair_pass: 0` 은 "패스를 먹지 않고 고쳐졌다" 이고, `source` 가 그 이유를 말한다.

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py:43-45` (열거), `:66-78` (`FINDING_KEYS`), `:439-470` (`validate_finding`)
- Modify: `tests/products/pre-sdd-review/evidence/support.py` (`finding` 기본값)
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`, `tests/products/pre-sdd-review/evidence/test_hardening.py`

**Interfaces:**
- Produces: `FINDING_SOURCES = ("reviewer", "ledger-pass", "machine-check")`; finding 키 `source`; `finding.repair_pass` 범위 0..2; `finding.status` 에 `partially-closed` 추가.
- Consumes: Task 2 의 `RECORD_KEYS_V4`.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/products/pre-sdd-review/evidence/test_evidence.py` 의 `FinishTests` 끝에 추가:

```python
    def test_finish_accepts_a_costless_repair_and_a_partial_closure(self) -> None:
        payload = finish_payload(
            verdict="REVISE",
            repair_passes=1,
            findings=[
                finding(
                    id="PSDR-001",
                    status="repaired",
                    repair_pass=0,
                    source="ledger-pass",
                ),
                finding(
                    id="PSDR-002",
                    status="partially-closed",
                    repair_pass=1,
                    source="reviewer",
                ),
            ],
        )
        code, out, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["verdict"], "REVISE")
        statuses = [item["status"] for item in load(self.home, self.run_id)["findings"]]
        self.assertEqual(statuses, ["repaired", "partially-closed"])

    def test_finish_rejects_an_unknown_finding_source(self) -> None:
        payload = finish_payload(findings=[finding(source="controller")])
        code, _, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual(code, 1)
        self.assertEqual(error_code(err), "schema-invalid")

    def test_finish_rejects_a_negative_repair_pass(self) -> None:
        payload = finish_payload(findings=[finding(repair_pass=-1)])
        code, _, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual(code, 1)
        self.assertEqual(error_code(err), "schema-invalid")
```

`tests/products/pre-sdd-review/evidence/support.py` 의 `finding` 기본값에 `source` 를 더한다. `repair_pass` 기본값 `1` 은 그대로 둔다.

```python
        "repair_pass": 1,
        "source": "reviewer",
```

- [ ] **Step 2: 실패를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.evidence.test_evidence -v 2>&1 | tail -20`
Expected: FAIL. `finding must contain exactly the finding keys` — `source` 가 아직 없다.

- [ ] **Step 3: 열거와 키를 더한다**

`skills/pre-sdd-review/evidence/evidence.py:45` 근처:

```python
FINDING_STATUSES = ("repaired", "partially-closed", "unresolved", "blocked-by-authority", "accepted-as-is")
FINDING_SOURCES = ("reviewer", "ledger-pass", "machine-check")
```

`FINDING_KEYS` 에 `"source"` 를 더한다.

- [ ] **Step 4: `validate_finding` 을 고친다**

`_enum(item["status"], ...)` 뒤에 더한다:

```python
    _enum(item["source"], "finding.source", FINDING_SOURCES)
```

`repair_pass` 하한을 0 으로 내린다:

```python
        _integer(repair_pass, "finding.repair_pass", 0, 2)
```

`repair_pass > repair_passes` 검사는 그대로 둔다. `validate_finish_shape` 이 `validate_finding(item, 2)` 로 상수 2 를 넘기므로 실제 초과는 `finding_repair_pass_exceeds_total` 관찰이 잡는다. 0 은 어떤 `repair_passes` 값에서도 초과가 아니다.

- [ ] **Step 5: 테스트가 통과하는지 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.evidence.test_evidence tests.products.pre-sdd-review.evidence.test_hardening 2>&1 | tail -10`
Expected: OK

- [ ] **Step 6: 커밋**

```bash
git add skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence/
git commit -m "feat(pre-sdd-review): let a finding carry its source, a partial closure, and a costless repair"
```

---

### Task 4: 관찰 — degraded 사유 열거, 이상 둘, 무비용 수리 집계, schema 3 abandon

**Files:**
- Modify: `skills/pre-sdd-review/evidence/evidence.py:41` (열거), `:337-341` (`require_current_schema`), `:475-500` (`validate_finish_shape`), `:511-540` (`observation_anomalies`), `:700-730` (`cmd_abandon` 경로), `:800-930` (`summarize`)
- Test: `tests/products/pre-sdd-review/evidence/test_evidence.py`, `tests/products/pre-sdd-review/evidence/test_hardening.py`

**Interfaces:**
- Produces: `DEGRADED_REASONS = ("primary-role-not-obtained", "focused-role-not-obtained", "agent-reused-within-invocation", "agent-reused-across-plans", "other")`; 이상 `head_start_not_ancestor_of_head_end` 와 `document_changed_without_repair_pass`; `summary` 의 `counts["costless_repairs"]`; `require_mutable_schema(record, *, abandon: bool)`.
- Consumes: Task 2 의 `git.head_start_is_ancestor_of_head_end`, Task 3 의 `finding.repair_pass`, `finding.source`.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/products/pre-sdd-review/evidence/test_evidence.py` 의 `FinishTests` 끝에 추가:

```python
    def test_finish_rejects_a_free_text_degraded_reason(self) -> None:
        payload = finish_payload(execution="degraded", degraded_reasons=["thread limit"])
        code, _, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual(code, 1)
        self.assertEqual(error_code(err), "schema-invalid")

    def test_finish_accepts_an_enumerated_degraded_reason(self) -> None:
        payload = finish_payload(execution="degraded", degraded_reasons=["focused-role-not-obtained"])
        code, _, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual((code, err), (0, ""))

    def test_finish_flags_a_document_change_with_no_repair(self) -> None:
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n\nchanged\n")
        code, out, err = finish(self.home, self.repo, self.run_id, finish_payload())
        self.assertEqual((code, err), (0, ""))
        self.assertIn("document_changed_without_repair_pass", json.loads(out)["anomalies"])

    def test_a_costless_repair_clears_the_document_change_anomaly(self) -> None:
        write(self.repo / "docs/plan.md", "# Plan\n\n**Spec:** docs/design.md\n\nchanged\n")
        payload = finish_payload(
            findings=[finding(status="repaired", repair_pass=0, source="machine-check")]
        )
        code, out, err = finish(self.home, self.repo, self.run_id, payload)
        self.assertEqual((code, err), (0, ""))
        self.assertNotIn("document_changed_without_repair_pass", json.loads(out)["anomalies"])
```

`SummaryTests` 에 추가:

```python
    def test_summary_counts_costless_repairs(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        payload = finish_payload(
            findings=[
                finding(id="PSDR-001", status="repaired", repair_pass=0, source="ledger-pass"),
                finding(id="PSDR-002", status="repaired", repair_pass=1, source="reviewer"),
            ],
            repair_passes=1,
        )
        self.assertEqual(finish(self.home, self.repo, run_id, payload)[0], 0)
        code, out, err = run(["summary"], home=self.home, cwd=self.repo)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["counts"]["costless_repairs"], 1)
```

`test_hardening.py` 에 추가:

```python
    def test_a_schema_three_pending_run_can_only_be_abandoned(self) -> None:
        run_id = start(self.home, self.repo, self.skill)
        path = self.home / "runs" / f"{run_id}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["schema"] = 3
        del record["baseline"], record["ledger"]
        del record["git"]["head_start_is_ancestor_of_head_end"]
        path.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")

        code, _, err = finish(self.home, self.repo, run_id, finish_payload())
        self.assertEqual(code, 1)
        self.assertEqual(error_code(err), "legacy-record-read-only")

        code, out, err = run(
            ["abandon", "--run-id", run_id, "--reason", "input-format-fixed"],
            home=self.home,
            cwd=self.repo,
        )
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["status"], "abandoned")
```

- [ ] **Step 2: 실패를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.evidence.test_evidence tests.products.pre-sdd-review.evidence.test_hardening -v 2>&1 | tail -25`
Expected: FAIL. 자유 문자열 사유가 통과하고, 새 이상 이름과 `costless_repairs` 가 없다.

- [ ] **Step 3: degraded 사유를 열거로 조인다**

`ABANDON_REASONS` 옆에 더한다:

```python
DEGRADED_REASONS = (
    "primary-role-not-obtained",
    "focused-role-not-obtained",
    "agent-reused-within-invocation",
    "agent-reused-across-plans",
    "other",
)
```

`validate_finish_shape` 의 사유 처리 줄을 바꾼다:

```python
    reasons = [str(_enum(item, "degraded_reasons[]", DEGRADED_REASONS)) for item in payload["degraded_reasons"]]
```

- [ ] **Step 4: 관찰 이상 둘을 더한다**

`observation_anomalies` 의 `checks` 딕셔너리에 더한다:

```python
        "head_start_not_ancestor_of_head_end": record["git"].get("head_start_is_ancestor_of_head_end") is False,
        "document_changed_without_repair_pass": _documents_changed(record)
        and record["repair_passes"] == 0
        and not any(item["repair_pass"] == 0 for item in findings),
```

`observation_anomalies` 바로 앞에 헬퍼를 더한다:

```python
def _documents_changed(record: dict[str, object]) -> bool:
    for name in ("plan", "design"):
        document = record[name]
        if isinstance(document, dict) and document["sha_start"] != document["sha_end"]:
            return True
    return False
```

`head_changed_during_review` 는 그대로 둔다. 로그에서 참 양성이므로 좁히지 않는다. 새 이상은 그 신호를 **분해**하는 것이지 대체하는 것이 아니다.

`summarize` 의 `anomalies` 딕셔너리 리터럴에 두 이름의 빈 목록을 더한다. 키 순서는 기존 리터럴 순서를 따른다.

- [ ] **Step 5: `costless_repairs` 집계를 더한다**

`summarize` 안 finding 루프에서 세고 `counts` 에 넣는다. `severities.append(...)` 옆에 더한다:

```python
            if item["repair_pass"] == 0 and item["status"] == "repaired":
                costless_repairs += 1
```

루프 앞에 `costless_repairs = 0` 을 초기화하고, `counts` 리터럴에 `"costless_repairs": costless_repairs,` 를 더한다.

같은 함수에서 결속 판정을 schema 3 이상으로 넓힌다. `record["schema"] == 3` 인 곳 셋을 `record["schema"] >= 3` 으로 바꾼다: `runs_index` 의 `repo_key` 와 `binding`, `chain_key` 분기, `counts["binding"]` 의 표현식.

- [ ] **Step 6: schema 3 pending 을 abandon 만 허용한다**

`require_current_schema` 를 바꾼다:

```python
def require_mutable_schema(record: dict[str, object], *, abandon: bool = False) -> None:
    schema = record["schema"]
    if schema == SCHEMA:
        return
    if abandon and schema == 3:
        return
    fail(
        "legacy-record-read-only",
        "only a schema 4 run is mutable; a schema 3 pending run may be abandoned",
    )
```

`_require_pending` 에 그 인자를 통과시킨다:

```python
def _require_pending(home: Path, run_id: str, *, abandon: bool = False) -> dict[str, object]:
    record = load_record(home, run_id)
    require_mutable_schema(record, abandon=abandon)
    if record["status"] != "pending":
        fail("already-finished", "run is already finished")
    return record
```

`cmd_abandon` 의 호출을 `_require_pending(home, args.run_id, abandon=True)` 로 바꾼다. `cmd_finish` 와 `cmd_outcome` 의 호출은 그대로 두어 schema 4 만 받는다. `cmd_outcome` 의 `require_current_schema(record)` 도 `require_mutable_schema(record)` 로 바꾼다.

- [ ] **Step 7: 테스트가 통과하는지 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.evidence.test_evidence tests.products.pre-sdd-review.evidence.test_hardening 2>&1 | tail -10`
Expected: OK

- [ ] **Step 8: 커밋**

```bash
git add skills/pre-sdd-review/evidence/evidence.py tests/products/pre-sdd-review/evidence/
git commit -m "feat(pre-sdd-review): enumerate degraded reasons and observe ancestry, unrepaired edits, and costless repairs"
```

---

### Task 5: `evidence/README.md` 를 schema 4 에 맞춘다

**Files:**
- Modify: `skills/pre-sdd-review/evidence/README.md`
- Test: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: Task 2·3·4 의 최종 명령 표면.
- Produces: 없음. 문서만 바꾼다.

- [ ] **Step 1: handshake 와 명령 표를 고친다**

`--version` 정규 줄 예시를 바꾼다:

```json
{"cli_version":"4.0.0","schema":4,"skill_name":"pre-sdd-review"}
```

"The compatibility handshake is exactly `skill_name=pre-sdd-review` and `schema=3`" 를 `schema=4` 로 바꾼다.

명령 표의 `start` 행 인자를 바꾼다:

```text
`--skill-root --repo --plan [--design] [--ledger] [--prior-plan ...] --client --model --mode`
```

"Readers validate both schema 2 and schema 3 files" 를 바꾼다:

```text
Readers validate schema 2, 3, and 4 files in `runs/*.json`; `finish` and
`outcome` accept only schema 4. A schema 3 pending run may be `abandon`ed so an
in-flight run survives the upgrade; a schema 2 record stays fully read-only.
```

`finish reads exactly these keys` 문단의 finding 키 목록에 `source` 를 더하고 `repair_pass` 범위를 적는다:

```text
Each finding has `id` (`PSDR-001`), `severity`, `class`, `pattern`, `status`,
`source` (`reviewer`, `ledger-pass`, `machine-check`), `repair_pass` (0-2, where
`0` means the repair consumed no pass), `location` (`path`, `locator`),
`evidence` (relative paths), `consequence`, and `fix`.
```

`degraded_reasons` 를 열거로 적고, record 의 `baseline` 과 `ledger` 를 한 문단으로 적는다:

```text
A schema 4 record adds `baseline` (`head` plus the ordered `prior_plans` this
plan's turn assumes) and `ledger` (the shared-file ledger's `path` and `sha`, or
null). `git` adds `head_start_is_ancestor_of_head_end`: true when the checkout
moved forward, false when it did not, null when the question is moot.
```

- [ ] **Step 2: 계약 테스트를 돌린다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.test_contract 2>&1 | tail -20`
Expected: 이 파일에 대한 문구 단언이 있으면 실패한다. 실패한 단언의 기대 문구를 새 문구로 고친다. `evidence/README.md` 는 `INSTRUCTION_DOCUMENT_SHA256` 에 없으므로 digest 재계산은 필요 없다.

- [ ] **Step 3: 통과를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review 2>&1 | tail -10`
Expected: OK

- [ ] **Step 4: 커밋**

```bash
git add skills/pre-sdd-review/evidence/README.md tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): document the schema 4 recorder surface"
```

---

### Task 6: `SKILL.md` — 선행 원장 패스, 원장, baseline

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md` (`Resolve authoritative inputs`, 충돌 우선순위, `Capture freshness`)
- Test: `tests/products/pre-sdd-review/test_contract.py` (`INSTRUCTION_DOCUMENT_SHA256["SKILL.md"]`)

**Interfaces:**
- Produces: 문구 `Pre-pass: shared-file ledger`, `Repository reality at this plan's turn`, freshness 항목 `baseline` 과 `ledger`.
- Consumes: Task 2 의 `start --ledger` 와 `--prior-plan`.

- [ ] **Step 1: `Resolve authoritative inputs` 의 계획 단수 문장을 판정 기준으로 한정한다**

현재 첫 문장:

```text
One invocation reviews exactly one implementation plan.
```

바꾼다:

```text
One verdict-bearing invocation reviews exactly one implementation plan.
```

같은 절의 다중 계획 문단을 바꾼다. 현재:

```text
A request naming several plans may be split into separate
invocations, but each verdict remains plan-local.
```

바꾼다:

```text
A request naming several plans is split into separate verdict-bearing
invocations, but each verdict remains plan-local. Before the first of those
invocations, run the pre-pass below once. Do not emit an aggregate `READY`.
```

- [ ] **Step 2: 선행 패스 절을 더한다**

`Resolve authoritative inputs` 절의 끝, 필수 구현 베이스 문단 뒤에 새 절을 넣는다.

```markdown
## Pre-pass: shared-file ledger

Run this once, before the first verdict-bearing invocation, when the outer
request names two or more plans or asks for it explicitly. It emits no verdict.

1. Fix the execution order. Take it from the user or derive it from the plans'
   stated prerequisites. If it cannot be fixed, stop and ask: without an order
   there is no baseline.
2. Build the ledger. Scrape each plan's `Files:` backticked paths and invert
   them into one row per path. If a plan has no `Files:` section, stop and ask;
   never derive the paths from task edit surfaces.
3. Sweep the rows that two or more plans touch.
4. Run the machine checks over every plan at once.
5. Steps 3 and 4 emit candidates, not findings. A candidate becomes a defect
   only when the repository confirms it.

The controlling agent does all of this. Dispatch no reviewer: a reviewer here
would be a third review role outside any plan's invocation. The next
invocation's fresh discovery review is the independent check on these repairs.

Hand the confirmed candidates to the controller, never to a reviewer. Repair
them before dispatching any reviewer, so the reviewer still arrives told
nothing. Those repairs precede review, so they consume no repair pass; record
them with `repair_pass: 0` and `source` `ledger-pass` or `machine-check`.

The ledger is derived evidence, never authority. When it disagrees with a
plan's `Files:`, the plan wins and the ledger is rebuilt. Its default path is
`docs/superpowers/ledgers/YYYY-MM-DD-<campaign>.md`; a user preference wins.

Under `review-only`, keep the ledger controller-local, write no file, and make
no intake repair. Report confirmed candidates as findings only.

This pre-pass is not a recorded run. The recorder binds one run to one plan and
to a verdict, and this pass has neither. The ledger reaches evidence through
each plan's own `start`.
```

- [ ] **Step 3: 충돌 우선순위 5번과 수정 허용 목록을 고친다**

우선순위 목록의 5번을 바꾼다:

```text
5. Repository reality at this plan's turn.
```

그 목록 바로 뒤에 한 문단을 더한다:

```text
A plan's turn is the repository plus every preceding plan in the fixed order,
not whatever `HEAD` happens to be. When preceding plans exist, that baseline
exists nowhere on disk and must be reconstructed from them.
```

`Repair rules` 의 첫 문장을 바꾼다. 현재:

```text
The controlling agent may edit only the resolved design specification and the
resolved implementation plan.
```

바꾼다:

```text
The controlling agent may edit only the resolved design specification, the
resolved implementation plan, and the resolved shared-file ledger.
```

- [ ] **Step 4: `Capture freshness` 에 baseline 과 ledger 를 더한다**

첫 문단 끝에 더한다:

```text
Also record the baseline: `HEAD` alone when no plan precedes this one, or
`HEAD` with the ordered list of preceding plans when they do. Record the
ledger's repository-relative path and SHA-256 when a ledger exists.
```

그 절 끝에 더한다:

```text
When preceding plans exist, carry that list and their paths in the reviewer
instruction and require a baseline-reconstruction statement on the response's
first line. That statement is the reviewer's own report and is not machine
checked. Its value is making the baseline explicit so the reviewer does not
quietly fall back to `HEAD`; it does not prove the reconstruction happened.
```

- [ ] **Step 5: digest 를 재계산해 붙인다**

공통 도구 스크립트를 돌려 `INSTRUCTION_DOCUMENT_SHA256["SKILL.md"]` 를 새 값으로 바꾼다. 문구 단언이 먼저 실패하면 그것부터 고친 뒤 다시 돌린다.

- [ ] **Step 6: 통과를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review 2>&1 | tail -10`
Expected: OK

- [ ] **Step 7: 커밋**

```bash
git add skills/pre-sdd-review/SKILL.md tests/products/pre-sdd-review/test_contract.py
git commit -m "feat(pre-sdd-review): add the verdict-less ledger pre-pass and the plan-turn baseline"
```

---

### Task 7: `SKILL.md` — 기계 점검, 수리 회계, degraded, BLOCKED, red flags

**Files:**
- Modify: `skills/pre-sdd-review/SKILL.md` (`Select reviewers`, `Default mode`, `Repair rules`, `Verdict and handoff`, `Optional local evidence`, `Red flags`)
- Test: `tests/products/pre-sdd-review/test_contract.py` (`INSTRUCTION_DOCUMENT_SHA256["SKILL.md"]`)

**Interfaces:**
- Consumes: Task 3 의 `partially-closed` 와 `repair_pass: 0`, Task 4 의 `DEGRADED_REASONS`.
- Produces: 문구 `Machine checks`, red flag 두 줄.

- [ ] **Step 1: `Repair rules` 에 기계 점검 절을 더한다**

`Repair rules` 절 끝에 더한다.

```markdown
### Machine checks

Run these over the repaired documents before dispatching the closure reviewer
and attach the results to the `repair-impact map`.

1. A declared count against the counted one: a task's stated passing count
   against its actual tests, a closed list's stated membership against its
   members.
2. The argument count and order at every site that builds the same constructor.
3. A literal against the constraint that receives it: length, range, enum.
4. An identifier embedded in a number or a name, at every site that carries it:
   a migration file's number against the number in the test that checks it.
5. Every face of a closed list, updated together: schema enums, exact-match key
   arrays, tests that count members.

These emit candidates. A candidate is not a defect until the repository
confirms it. Raising an unconfirmed candidate makes the gate spend a round trip
on a defect that is not there.
```

- [ ] **Step 2: `Default mode` 의 수리 회계를 고친다**

`repair_passes counts only passes that produced at least one repaired finding.` 뒤에 더한다:

```text
A repair consumes no pass when both hold: the `repair-impact map` is empty
because no structural trigger fired, and the closure reviewer confirmed the
repair has no consumer. The controller's own confirmation does not count.
Because the second condition is the closure reviewer's, pass accounting settles
after that round's closure review, never at the moment of repair. Record such a
repair with `repair_pass: 0`. Group them into one pass.

Closure disposition is `closed`, `partially-closed`, or `open`. Record the
remainder of a partial closure as the original record's remaining sites, never
as a new ID, so repair passes track defects rather than the sites a defect is
scattered across. A finding still `partially-closed` at the end counts as
unresolved for the verdict and forces `REVISE`. A record's `repair_pass` is the
pass that last changed its status.
```

- [ ] **Step 3: unmapped 문단에 같은 갈래 예외를 더한다**

현재 문단:

```text
Keep an unmapped material finding visible, but do not widen the current repair.
```

그 문장 뒤에 더한다:

```text
A finding whose `class` and pattern match an original record is not unmapped,
even at a different location. It shows the original record's Location was
incomplete: widen that Location and repair it inside the same pass. Only a new
defect shape is unmapped.
```

- [ ] **Step 4: `Select reviewers` 의 degraded 규칙을 고친다**

`If a fresh independent reviewer cannot be obtained, do not use the controlling agent as a substitute independent primary.` 를 바꾼다:

```text
If a fresh independent primary reviewer cannot be obtained, return `BLOCKED`.
Do not use the controlling agent as a substitute independent primary and do not
run a short degraded round in its place. When only the focused risk role cannot
be obtained, the run is `execution=degraded`; its handoff is never reusable.
Never reuse one agent across invocations that review different plans: that is
not reuse, it is loss of independence.
```

- [ ] **Step 5: `Verdict and handoff` 의 `BLOCKED` 정의를 넓힌다**

현재:

```text
Return `BLOCKED` when required authority, input, or
repository evidence is unavailable, unresolvable, or would require a new
product decision.
```

바꾼다:

```text
Return `BLOCKED` when required authority, input, or repository evidence is
unavailable, unresolvable, or would require a new product decision, or when an
independent primary reviewer cannot be obtained. Record that run as
`execution=blocked` and name the cause in `block_reason`; a `BLOCKED` run with
a null `block_reason` is an anomaly.
```

재사용 규칙 문장에서 `degraded` 를 뺀다. 현재:

```text
for a `full` or `degraded` run only when the documents, `HEAD`, and the request are all unchanged.
```

바꾼다:

```text
for a `full` run only when the documents, `HEAD`, and the request are all unchanged.
```

`Optional local evidence` 절과 `Red flags` 에 있는 같은 표현 두 곳도 함께 고친다.

- [ ] **Step 6: `Optional local evidence` 에 finding 모양과 pending 을 앞세운다**

`run summary --repo <repo display name> before start and locate this plan in runs and chains.` 뒤 문장을 바꾼다. 현재:

```text
Close any `pending` run for this plan first.
```

바꾼다:

```text
Close any `pending` run for this plan before anything else: a pending run can
outlive the invocation that opened it and be mistaken for a new round.
```

그 절 끝에 한 문단을 더한다:

```text
A finding record carries `id`, `severity`, `class`, `pattern`, `status`,
`source`, `repair_pass`, `location` (`path`, `locator`), `evidence`,
`consequence`, and `fix`. `evidence` is a list of repository-relative paths,
not prose. Pass the ledger path with `--ledger` and each preceding plan with a
repeated `--prior-plan` on `start`.
```

- [ ] **Step 7: `Optional local evidence` 의 schema 게이트를 4 로 올린다**

두 문장을 고친다. 현재:

```text
record only when `skill_name=pre-sdd-review` and `schema=3`
```

바꾼다:

```text
record only when `skill_name=pre-sdd-review` and `schema=4`
```

그리고 현재:

```text
A schema 2 pending run is `historical-unbound` and read-only. Preserve it and
start a new run if recording is still wanted; never infer a checkout identity
for a historical record.
```

바꾼다:

```text
A schema 2 pending run is `historical-unbound` and read-only. Preserve it and
start a new run if recording is still wanted; never infer a checkout identity
for a historical record. A schema 3 pending run is not writable either, but it
accepts `abandon` so an in-flight run survives the upgrade.
```

- [ ] **Step 8: `Red flags` 에 네 줄을 더한다**

```text
- Claim that a test covers something without locating that test
- Apply a textual repair without asserting the match is unique
- Reuse one reviewer across invocations that review different plans
- Reuse a handoff from a `degraded` run
```

- [ ] **Step 9: digest 를 재계산하고 통과를 확인한다**

문구 단언을 먼저 고치고, 남은 실패가 digest 뿐일 때 공통 도구 스크립트로 `INSTRUCTION_DOCUMENT_SHA256["SKILL.md"]` 를 갱신한다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review 2>&1 | tail -10`
Expected: OK

- [ ] **Step 10: 커밋**

```bash
git add skills/pre-sdd-review/SKILL.md tests/products/pre-sdd-review/test_contract.py
git commit -m "feat(pre-sdd-review): name the machine checks, partial closure, costless repairs, and the degraded limits"
```

---

### Task 8: `references/reviewer-protocol.md` — 지시 계약, 결함 갈래 넷, 증명 표

**Files:**
- Modify: `skills/pre-sdd-review/references/reviewer-protocol.md`
- Test: `tests/products/pre-sdd-review/test_contract.py` (`INSTRUCTION_DOCUMENT_SHA256["references/reviewer-protocol.md"]`)

**Interfaces:**
- Produces: 제목 `Dispatch contract`, `Discovery dispatch`, `Closure dispatch`; Pass 3 의 이름 붙은 검사 넷; Pass 4 의 증명 표.
- Consumes: Task 6 의 baseline 과 원장 문구.

- [ ] **Step 1: `Finding vocabulary` 앞에 지시 계약 절을 넣는다**

```markdown
## Dispatch contract

The controlling agent writes the instruction. These items are not optional, and
the two instructions differ: a discovery reviewer must arrive told nothing.

### Discovery dispatch

- The baseline: the ordered preceding plans and their paths, with a required
  reconstruction statement on the response's first line.
- The shared-file ledger's path and SHA-256, when one exists.
- An instruction to read a large plan task by task rather than whole.
- The four recurring defect shapes named in Pass 3.
- The output format.

Never carry an earlier round's findings into a discovery instruction.

### Closure dispatch

Everything above, plus:

- The earlier round's PSDR records verbatim. A controller summary is not
  accepted: closure is checked by matching the original Location and Evidence,
  which a summary cannot carry.
- The `repair-impact map`.
- The machine-check results.
- An explicit slot listing the tasks that no record yet points at.

The rule against naming findings, paths, symbols, or fixes when resuming a
reviewer applies only to re-asking an incomplete record for its missing fields.
It does not restrict the closure dispatch above.
```

- [ ] **Step 2: Pass 3 에 이름 붙은 검사 넷을 더한다**

`Pass 3: cross-artifact consistency` 의 조건부 검사 목록 앞에 더한다.

```markdown
Check these four by name. They recur across plans and languages.

- **An addendum folded into the tasks only halfway.** A revisions or
  final-checks section states a requirement while the task's code block keeps
  the old shape. Two tasks then build the same record with different arity and
  neither reconciliation compiles.
- **Verification that exists in prose but not in code.** "That test covers
  this" where the test is absent or does not look at it. A concurrency
  requirement with no stated method passes with sequential calls.
- **A line number used as a location.** A preceding plan inserting above shifts
  every number below. When the symbol name is already given, the number carries
  only misinformation.
- **A closed list updated on one side only.** Schema enums, exact-match key
  arrays, zod enums, tests that count members. Each plan adds its own entry and
  one omission leaves the published document rejecting its own schema.
```

- [ ] **Step 3: Pass 4 에 증명 표를 더한다**

`Pass 4: verification falsification` 끝에 더한다.

```markdown
When a plan asserts a constraint built from several conjuncts, require a table,
not prose: one variant per conjunct removed, each rejection case checked
against each variant. A prose judgement caught three of six conjuncts where the
table caught all six.
```

- [ ] **Step 4: digest 를 재계산하고 통과를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review 2>&1 | tail -10`
Expected: 문구 단언 실패를 먼저 고치고, 남은 digest 실패를 공통 도구 스크립트 값으로 갱신하면 OK

- [ ] **Step 5: 커밋**

```bash
git add skills/pre-sdd-review/references/reviewer-protocol.md tests/products/pre-sdd-review/test_contract.py
git commit -m "feat(pre-sdd-review): give the reviewer dispatch a contract and name the four recurring defects"
```

---

### Task 9: `contract.md` — 계약 소유

**Files:**
- Modify: `docs/maintainers/products/pre-sdd-review/contract.md`
- Test: `tests/products/pre-sdd-review/test_contract.py` (`MAINTAINER_CANONICAL_DIGEST`, `MAINTAINER_CANONICAL_SUBSECTION_DIGESTS`)

**Interfaces:**
- Produces: `### Editable paths` 세 항목, `### Ledger shape`, `### Degraded reasons`, 갱신된 `### Contract` 목록.
- Consumes: Task 6·7·8 의 최종 문구.

- [ ] **Step 1: `Editable paths` 를 셋으로 늘린다**

```markdown
### Editable paths

1. resolved design specification.
2. resolved implementation plan.
3. resolved shared-file ledger.
```

그 목록 뒤에 한 문단을 더한다:

```text
원장은 유도된 증거이지 권위가 아닙니다. 권위 순서 다섯은 그대로입니다. 원장이
계획의 `Files:` 와 어긋나면 계획이 이기고 원장을 다시 만듭니다.
```

- [ ] **Step 2: 원장 모양 절을 더한다**

`## 검토 패스와 발견` 앞에 넣는다.

```markdown
## 선행 원장 패스

외부 요청이 계획을 둘 이상 이름 대면, 판정을 내는 첫 호출 앞에 한 번 돕니다.
이 패스는 판정을 내지 않습니다. 출력은 원장, 확정된 실행 순서, 저장소로 확인된
결함 후보입니다. 컨트롤러가 전부 하고 검토자를 부르지 않습니다. 확인된 후보는
검토자 파견 전에 고칩니다. 그 수리는 검토 이전이므로 수리 패스를 먹지 않고
`repair_pass: 0` 으로 기록합니다. `review-only` 에서는 원장을 파일로 쓰지 않고
반입 수리도 하지 않습니다. 이 패스는 run 으로 기록하지 않습니다.

계획에 `Files:` 절이 없으면 멈추고 묻습니다. Task 의 edit surface 에서 유도하지
않습니다.

### Ledger shape

- 머리: 생성 시각, 대상 계획 목록과 각 계획의 SHA-256, 확정된 실행 순서
- 본문: 한 행이 한 경로. `| path | 이 경로를 만지는 계획 (실행 순서대로) |`
- 만지는 계획이 하나인 경로도 전부 적습니다. 스윕 대상은 둘 이상인 행입니다.
- 기본 위치는 `docs/superpowers/ledgers/YYYY-MM-DD-<campaign>.md` 이고 사용자
  선호가 우선합니다.
```

- [ ] **Step 3: degraded 와 BLOCKED 를 고친다**

`## 검토자 격리와 수정 허용 목록` 의 재검토 문단 뒤에 더한다.

```markdown
### Degraded reasons

- `primary-role-not-obtained`
- `focused-role-not-obtained`
- `agent-reused-within-invocation`
- `agent-reused-across-plans`
- `other`

독립 1차 검토자를 구할 수 없으면 `BLOCKED` 입니다. 짧은 degraded 회차로 대신하지
않습니다. 집중 위험 역할만 못 구하면 `degraded` 이고 그 인계는 재사용하지
않습니다. 한 에이전트를 계획이 다른 호출에 돌려 쓰지 않습니다.
```

`### Verdicts` 의 `BLOCKED` 줄을 바꾼다:

```text
- `BLOCKED`: 필요한 입력·권위·저장소 증거가 없거나, 새 제품 결정이 필요하거나,
  독립 1차 검토자를 구할 수 없습니다.
```

`## 기본 흐름, 판정, freshness` 의 재사용 문장에서 `degraded` 를 뺀다:

```text
문서, `HEAD`, 요청이 모두 바뀌지 않은 `full` run 의 인계만 재사용합니다.
`execution` 이 `degraded` 또는 `blocked` 인 run 의 인계는 재사용하지 않습니다.
```

`### Freshness` 목록에 두 줄을 더한다:

```text
- baseline: `HEAD`, 또는 `HEAD` 와 선행 계획 목록
- ledger: 저장소 상대 경로와 SHA-256 (없으면 생략)
```

- [ ] **Step 4: 기록기 절을 schema 4 로 고친다**

`## 선택 기록기 계약` 의 handshake 문장과 정규 줄을 바꾼다:

```text
handshake 가 정확히 `skill_name=pre-sdd-review` 와 `schema=4` 일 때만 기록합니다.
정규 한 줄은 `{"cli_version":"4.0.0","schema":4,"skill_name":"pre-sdd-review"}`
뒤에 LF 하나입니다.
```

같은 절의 schema 2 문단을 바꾼다:

```text
schema 2 와 schema 3 record 는 계속 읽습니다. 변경은 schema 4 만 받습니다.
예외로 schema 3 pending 은 `abandon` 만 허용해 업그레이드 시점의 진행 중 run 을
닫을 수 있게 합니다. schema 2 는 `historical-unbound` 이며 읽기 전용입니다.
`start` 는 schema 4 checkout 결속 run 을 만듭니다.
```

finding 필드 문장에 `source` 와 `repair_pass` 범위를 더한다:

```text
finding 에는 `source` (`reviewer`, `ledger-pass`, `machine-check`) 와
`repair_pass` (0..2, `0` 은 패스를 먹지 않은 수리) 가 들어갑니다.
`finding.evidence` 는 산문이 아니라 저장소 상대 경로의 목록입니다.
```

- [ ] **Step 5: `하지 않는 것` 에서 `program ledger` 를 뺀다**

```markdown
- closure-only input schema
- shared-design invalidation map
- evidence probe cache
```

- [ ] **Step 6: `### Contract` 목록을 갱신한다**

아래 줄들을 고치고 더한다:

```text
- `plan-cardinality`: `one-plan-per-verdict-bearing-invocation`, `no-aggregate-ready`
- `editable-surfaces`: `resolved-design-specification`, `resolved-implementation-plan`, `resolved-shared-file-ledger`
- `ledger`: `pre-pass-no-verdict`, `derived-not-authority`
- `baseline`: `plan-turn-reality`
- `repair-passes`: `at-most-two`, `costless-repairs-uncounted`
- `second-reviewer`: `conditional-only`, `no-cross-plan-reuse`
- `handoff`: `unresolved-packet`, `full-execution-only`
```

- [ ] **Step 7: digest 를 재계산하고 통과를 확인한다**

먼저 기존 튜플을 그대로 출력해 무엇을 고정하고 있는지 본다.

```bash
sed -n '/^MAINTAINER_CANONICAL_SUBSECTION_DIGESTS/,/^)/p' tests/products/pre-sdd-review/test_contract.py
```

그 목록이 `Editable paths` 처럼 계약 토큰을 담은 제목만 고정한다면, 같은 성격인 `Ledger shape` 와 `Degraded reasons` 를 더한다. 공통 도구 스크립트가 각 제목의 값을 출력하므로 그 값을 그대로 붙인다.

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review 2>&1 | tail -20`
Expected: OK

- [ ] **Step 8: 커밋**

```bash
git add docs/maintainers/products/pre-sdd-review/contract.md tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): let the contract own the ledger, the baseline, and the degraded limits"
```

---

### Task 10: 제품 README 둘

**Files:**
- Modify: `skills/pre-sdd-review/README.md`
- Modify: `skills/pre-sdd-review/README.en.md`
- Test: `tests/products/pre-sdd-review/test_contract.py`

**Interfaces:**
- Consumes: Task 6~9 의 최종 계약.
- Produces: 없음. 사용자 안내만 바꾼다.

- [ ] **Step 1: 현재 문구를 읽고 무엇이 어긋나는지 적는다**

Run: `sed -n 1,200p skills/pre-sdd-review/README.md`

계획 단수, 재사용 규칙, handshake 버전, 수정 허용 목록을 적은 문장을 찾는다.

- [ ] **Step 2: 두 README 를 고친다**

각각에서 고칠 것은 넷이다. 두 파일의 대응 문장을 같은 뜻으로 바꾼다.

1. 계획 단수: "한 호출은 계획 하나" → "판정을 내는 한 호출은 계획 하나". 계획이 둘 이상이면 선행 원장 패스를 먼저 돈다는 한 문장을 더한다.
2. 수정 허용 목록: 설계와 계획 둘 → 원장을 더해 셋.
3. 재사용: `full` run 의 인계만 재사용한다.
4. handshake: `schema=3` → `schema=4`, `cli_version` `3.0.0` → `4.0.0`.

- [ ] **Step 3: 통과를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py --skill pre-sdd-review 2>&1 | tail -10`
Expected: OK

- [ ] **Step 4: 커밋**

```bash
git add skills/pre-sdd-review/README.md skills/pre-sdd-review/README.en.md tests/products/pre-sdd-review/test_contract.py
git commit -m "docs(pre-sdd-review): describe the ledger pre-pass and the schema 4 handshake in both READMEs"
```

---

### Task 11: `cases.json` 다섯 케이스와 CHANGELOG 마무리

**Files:**
- Modify: `tests/products/pre-sdd-review/cases.json`
- Modify: `tests/products/pre-sdd-review/test_contract.py` (`CASE_IDS`)
- Modify: `skills/pre-sdd-review/CHANGELOG.md`

**Interfaces:**
- Consumes: Task 1~10 전부.
- Produces: 없음. 마지막 Task 다.

- [ ] **Step 1: 실패하는 `CASE_IDS` 를 먼저 쓴다**

`tests/products/pre-sdd-review/test_contract.py` 의 `CASE_IDS` 튜플 끝에 더한다:

```python
    "ledger-required-for-multiple-plans",
    "baseline-reconstruction-required",
    "partial-closure-not-a-new-finding",
    "costless-repair-consumes-no-pass",
    "degraded-handoff-not-reused",
```

- [ ] **Step 2: 실패를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.test_contract -v 2>&1 | tail -15`
Expected: FAIL. `cases.json` 에 그 id 가 없다.

- [ ] **Step 3: `cases.json` 에 다섯 케이스를 더한다**

`cases` 배열 끝에 더한다.

```json
  {
    "id": "ledger-required-for-multiple-plans",
    "request": "$pre-sdd-review sample-app/plan-a.md sample-app/plan-b.md that both edit sample-app/src/app.ts",
    "expect": ["ledger", "no_aggregate_verdict", "execution_order"]
  },
  {
    "id": "baseline-reconstruction-required",
    "request": "$pre-sdd-review sample-app/design.md sample-app/plan-b.md that runs after sample-app/plan-a.md",
    "expect": ["baseline", "prior_plans", "reconstruction_statement"]
  },
  {
    "id": "partial-closure-not-a-new-finding",
    "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md whose repair closed two of three sites",
    "expect": ["partially-closed", "same_finding_id", "REVISE"]
  },
  {
    "id": "costless-repair-consumes-no-pass",
    "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md needing only a rename with no consumer",
    "expect": ["repair_pass_0", "empty_impact_map", "closure_confirmed"]
  },
  {
    "id": "degraded-handoff-not-reused",
    "request": "$pre-sdd-review sample-app/design.md sample-app/plan.md after a degraded REVISE run",
    "expect": ["no_reuse", "fresh_review"]
  }
```

- [ ] **Step 4: 통과를 확인한다**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.products.pre-sdd-review.test_contract 2>&1 | tail -5`
Expected: OK

- [ ] **Step 5: CHANGELOG 의 4.0.0 절을 채운다**

Task 1 이 만든 뼈대를 아래로 바꾼다.

```markdown
## 4.0.0 - 2026-09-18

### Added

- 판정을 내지 않는 선행 원장 패스. 계획을 둘 이상 이름 댄 요청은 판정을 내는 첫
  호출 앞에 공유 파일 원장과 실행 순서를 만들고 기계 점검을 한 번에 돌린다.
- `Repository reality at this plan's turn`. freshness 에 baseline 과 ledger 가
  들어가고, 선행 계획이 있으면 리뷰어가 기준선 재구성을 진술한다.
- 리뷰어 지시 계약. 발견 지시와 종결 지시를 나누고, 종결 지시는 앞 회차 기록
  원문과 아직 아무 기록도 가리키지 않은 Task 목록을 싣는다.
- 되풀이된 결함 갈래 넷과 복합 제약의 증명 표.

### Changed

- 수정 허용 목록이 설계·계획·원장 셋이다. 원장은 유도된 증거이지 권위가 아니다.
- 부분 닫힘이 일급이다. 잔여는 새 ID 가 아니라 같은 기록의 남은 자리다.
- 영향 표가 비어 있고 종결 리뷰어가 소비자 없음을 확인한 수리는 패스를 먹지
  않는다.
- 원 기록과 `class` 및 갈래가 같은 발견은 위치가 달라도 unmapped 가 아니다.
- 인계 재사용은 `full` run 만이다. 독립 1차 검토자를 구할 수 없으면 `BLOCKED`
  이고, 한 에이전트를 계획이 다른 호출에 돌려 쓰지 않는다.

### Breaking

- Record schema 와 handshake 가 `4` 다. 정규 줄은
  `{"cli_version":"4.0.0","schema":4,"skill_name":"pre-sdd-review"}` 다.
- record 에 `baseline` 과 `ledger` 가, `git` 에
  `head_start_is_ancestor_of_head_end` 가, finding 에 `source` 가 들어간다.
- `finding.repair_pass` 범위가 0..2 이고, `finding.status` 에 `partially-closed`
  가 들어가며, `degraded_reasons` 는 열거다.
- schema 2·3 은 계속 읽는다. 변경은 schema 4 만 받고, schema 3 pending 은
  `abandon` 만 허용한다.

### Notes

- GitHub 태그와 Release 는 만들지 않는다.
```

- [ ] **Step 6: 전체 검증**

Run: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify.py 2>&1 | tail -20`
Expected: OK

- [ ] **Step 7: 커밋**

```bash
git add tests/products/pre-sdd-review/cases.json tests/products/pre-sdd-review/test_contract.py skills/pre-sdd-review/CHANGELOG.md
git commit -m "test(pre-sdd-review): pin the ledger, baseline, closure, and degraded contracts as cases"
```

---

## 완료 뒤

스펙 15절에 따라 구현이 끝나면 이 계획, 스펙, 현장 기록 셋을 함께 지운다. Git
이력에서 볼 수 있다. 현장 기록이 아직 커밋되지 않았다면 지울 것이 없으므로,
지우기 전에 커밋 여부를 사용자에게 확인한다.
